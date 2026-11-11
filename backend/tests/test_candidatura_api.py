"""Route tests for POST /api/candidatura/responder — the 200-envelope
contract of the vaga → perfil follow-on module, OFFLINE: the pipeline's
run_stage is stubbed with a canned CandidaturaResposta and the profile loader
is retargeted to the conftest fixture (D-15/D-16 seams; mirrors
tests/test_linkedin_api.py).

Pinned here: the ok envelope ({"status", "resposta"}); the composed stage
input carries the three DATA blocks (facts + optional vaga + question) with
the run language pinned by the gateway's user-message template; the vaga is
omitted from the blob when absent; the erro envelope on a scripted LLMError
(200, no "resposta" key, raw detail terminal-only via caplog — the house
pattern, T-06-04); the erro envelope on a broken profile; 422 on a short
question, an oversized question, an unknown body key (extra=forbid) and an
unknown language; sync (non-coroutine) handler; the candidatura router
registered BEFORE the SPA mount (Pitfall 5/8).
"""

import inspect
import json
import logging

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.llm.errors import LLMError
from app.llm.schemas import CandidaturaResposta
from app.main import app

client = TestClient(app)

PERGUNTA = "Descreva sua última experiência e o principal resultado que você entregou."
RESPOSTA = (
    "Na minha última posição liderei a plataforma de IA generativa da empresa, "
    "entregando uma solução que reduziu em até 90% o tempo de análise de antecedentes."
)


def _stub_run_stage(monkeypatch: pytest.MonkeyPatch, outcome: object) -> dict:
    """Swap pipeline.run_stage for a canned outcome — model, exception, or
    raw-string sentinel to capture the composed input_text."""
    import app.candidatura.pipeline as pipeline_module

    captured: dict = {}

    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        captured["stage"] = stage
        captured["input_text"] = input_text
        captured["language"] = language
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(pipeline_module, "run_stage", fake_run_stage)
    return captured


@pytest.fixture()
def perfil_valido(monkeypatch, tmp_path):
    """The conftest minimal profile retargets the loader (never the real file)."""
    import app.profile.loader as loader_module
    import yaml
    from conftest import minimal_profile

    path = tmp_path / "profile.md"
    meta = minimal_profile()
    path.write_text(
        "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n\nPerfil de teste.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(loader_module, "PROFILE_PATH", path)
    return path


def _iter_api_routes():
    """(path, endpoint_or_None, position) in registration order — handles the
    FastAPI >= 0.141 nested-_IncludedRouter layout (test_linkedin_api precedent)."""
    for position, entry in enumerate(app.routes):
        if isinstance(entry, APIRoute):
            yield entry.path, entry.endpoint, position
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    yield sub.path, sub.endpoint, position
        elif type(entry).__name__ == "Mount":
            yield entry.path, None, position


def test_router_registered_before_spa_mount() -> None:
    routes = list(_iter_api_routes())
    paths = [path for path, _, _ in routes]
    assert "/api/candidatura/responder" in paths
    # The SPA mount (StaticFiles) is registered LAST — the candidatura route
    # must precede it in app.router order (Pitfall 5/8). The Mount entry is
    # the only yielded item with endpoint None (its path renders "" on this
    # FastAPI version, never "/" — match by the None endpoint alone).
    pos_rota = next(pos for path, _, pos in routes if path == "/api/candidatura/responder")
    pos_mount = next(pos for path, endpoint, pos in routes if endpoint is None)
    assert pos_rota < pos_mount


def test_handler_is_sync() -> None:
    endpoints = [
        endpoint
        for path, endpoint, _ in _iter_api_routes()
        if path == "/api/candidatura/responder"
    ]
    assert endpoints, "rota não registrada"
    for endpoint in endpoints:
        assert not inspect.iscoroutinefunction(endpoint)


def test_responder_ok_envelope(perfil_valido, monkeypatch) -> None:
    captured = _stub_run_stage(monkeypatch, CandidaturaResposta.model_validate({"resposta": RESPOSTA}))
    resp = client.post(
        "/api/candidatura/responder",
        json={"pergunta": PERGUNTA, "language": "pt-BR"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok", "resposta": RESPOSTA}
    # Stage id flows to runs.jsonl via the real gateway contract (D-10).
    assert captured["stage"] == "candidatura-resposta"
    assert captured["language"] == "pt-BR"
    # Three DATA blocks, question LAST (T-02-01): facts, no vaga, question.
    assert captured["input_text"].startswith("FATOS DO PERFIL:\n")
    assert "DESCRIÇÃO DA VAGA:" not in captured["input_text"]
    assert "PERGUNTA DO RECRUTADOR:\n" + PERGUNTA in captured["input_text"]


def test_responder_com_vaga_inclui_bloco(perfil_valido, monkeypatch) -> None:
    captured = _stub_run_stage(monkeypatch, CandidaturaResposta.model_validate({"resposta": RESPOSTA}))
    resp = client.post(
        "/api/candidatura/responder",
        json={"pergunta": PERGUNTA, "vaga_texto": "Vaga sênior de IA generativa com LangGraph."},
    )
    assert resp.status_code == 200
    assert "DESCRIÇÃO DA VAGA:\nVaga sênior de IA generativa" in captured["input_text"]
    # Ordering: facts → vaga → question.
    assert captured["input_text"].index("DESCRIÇÃO DA VAGA:") < captured["input_text"].index(
        "PERGUNTA DO RECRUTADOR:"
    )


def test_responder_erro_envelope_llm_error(perfil_valido, monkeypatch, caplog) -> None:
    exc = LLMError("Falha na chamada ao modelo", "raw: boom")
    _stub_run_stage(monkeypatch, exc)
    with caplog.at_level(logging.ERROR):
        resp = client.post("/api/candidatura/responder", json={"pergunta": PERGUNTA})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == ["Falha na chamada ao modelo"]
    assert "resposta" not in body
    assert "raw: boom" in caplog.text  # raw detail → terminal ONLY


def test_responder_erro_envelope_perfil_quebrado(monkeypatch, tmp_path) -> None:
    import app.profile.loader as loader_module

    broken = tmp_path / "profile.md"
    broken.write_text("---\nname: \"Ana\"\n---\n\ncorpo\n", encoding="utf-8")
    monkeypatch.setattr(loader_module, "PROFILE_PATH", broken)
    resp = client.post("/api/candidatura/responder", json={"pergunta": PERGUNTA})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"]


def test_resposta_vazia_venv_vira_erro(perfil_valido, monkeypatch) -> None:
    """Loud-empty (LinkedIn D-09): a blank generated answer is never delivered."""
    _stub_run_stage(monkeypatch, CandidaturaResposta.model_validate({"resposta": "   "}))
    resp = client.post("/api/candidatura/responder", json={"pergunta": PERGUNTA})
    assert resp.status_code == 200
    assert resp.json()["status"] == "erro"


def test_422_pergunta_curta(perfil_valido) -> None:
    resp = client.post("/api/candidatura/responder", json={"pergunta": "abc"})
    assert resp.status_code == 422


def test_422_pergunta_longa(perfil_valido) -> None:
    resp = client.post("/api/candidatura/responder", json={"pergunta": "x" * 2001})
    assert resp.status_code == 422


def test_422_chave_desconhecida(perfil_valido) -> None:
    resp = client.post(
        "/api/candidatura/responder",
        json={"pergunta": PERGUNTA, "idioma": "pt-BR"},  # unknown key (field is `language`)
    )
    assert resp.status_code == 422


def test_422_idioma_desconhecido(perfil_valido) -> None:
    resp = client.post(
        "/api/candidatura/responder",
        json={"pergunta": PERGUNTA, "language": "es"},
    )
    assert resp.status_code == 422


def test_stage_registration_is_consistent() -> None:
    """The gateway knows the stage, and the wire schema names derive from it —
    the runs.jsonl contract stays intact (D-10)."""
    from app.llm.gateway import _STAGE_SCHEMAS

    assert "candidatura-resposta" in _STAGE_SCHEMAS
    output_model, wire_schema = _STAGE_SCHEMAS["candidatura-resposta"]
    assert output_model is CandidaturaResposta
    assert json.dumps(wire_schema)  # serializable strict schema
