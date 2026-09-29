"""Route tests for POST /api/linkedin/gerar — the 200-envelope contract of
plan 06-01, OFFLINE: the pipeline's run_stage is stubbed with canned models
per stage and the profile loader is retargeted to the conftest fixture
(D-15/D-16 seams; mirrors tests/test_resume_api.py).

Pinned here: the ok envelope in both languages; the erro envelope on a
scripted LLMError (200, NO secoes key, raw detail terminal-only via caplog —
the house pattern, T-06-04); the erro envelope on a broken profile; 422 on a
sub-80-char objetivo, unknown body keys (extra=forbid) and an unknown
language; sync (non-coroutine) handlers; the linkedin router registered
BEFORE the SPA mount (research Pitfall 8).
"""

import inspect
import json
import logging

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.llm.errors import LLMError
from app.llm.schemas import LinkedinHeadline
from app.main import app

client = TestClient(app)

# ≥80 chars — passes the strict request validation (V5); mirrors the UI-SPEC
# placeholder objective.
OBJETIVO_PT = (
    "Crescer como engenheiro de dados sênior com foco em Python, SQL e "
    "plataformas de dados em nuvem, liderando iniciativas que impactem o negócio."
)
OBJETIVO_EN = (
    "Grow into a senior data engineer role focused on Python, SQL and cloud "
    "data platforms, leading data initiatives that impact the business."
)

HEADLINE_CONTENT = json.dumps(
    {"headline": "Engenheira de Dados Sênior — Python, SQL e plataformas de dados em nuvem"},
    ensure_ascii=False,
)


def _canned_model(stage: str):
    assert stage == "linkedin-headline"
    return LinkedinHeadline.model_validate(json.loads(HEADLINE_CONTENT))


@pytest.fixture
def _profile_file(monkeypatch: pytest.MonkeyPatch, valid_profile_path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", valid_profile_path)


def _stub_stages(monkeypatch: pytest.MonkeyPatch, script: list | None = None) -> None:
    """Stub app.linkedin.pipeline.run_stage: a canned model per requested
    stage (or the next scripted item — content str or exception)."""
    import app.linkedin.pipeline as pipeline_module

    items = list(script) if script is not None else [None]

    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        item = items.pop(0)
        if isinstance(item, Exception):
            raise item
        if item is None:  # canned model for the requested stage
            return _canned_model(stage)
        return LinkedinHeadline.model_validate(json.loads(item))

    monkeypatch.setattr(pipeline_module, "run_stage", fake_run_stage)


@pytest.fixture
def _canned_pipeline(monkeypatch: pytest.MonkeyPatch, _profile_file: None) -> None:
    _stub_stages(monkeypatch)


# ---------------------------------------------------------------------------
# (a) Gerar endpoint — the ok envelope, both languages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("language", ["pt-BR", "en"])
def test_gerar_returns_ok_envelope_both_languages(
    language: str, _canned_pipeline: None
) -> None:
    resp = client.post(
        "/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT, "language": language}
    )
    assert resp.status_code == 200
    body = resp.json()
    # EVERY contract key — the interface of record for the plan's client.
    assert set(body) == {"status", "idioma", "secoes", "limites"}
    assert body["status"] == "ok"
    assert body["idioma"] == language
    assert body["secoes"]["headline"] == json.loads(HEADLINE_CONTENT)["headline"]
    limites = body["limites"]["headline"]
    assert set(limites) == {"limite", "tamanho", "excesso"}
    assert limites["limite"] == 220
    assert limites["tamanho"] == len(body["secoes"]["headline"])
    assert limites["excesso"] == 0


def test_gerar_defaults_language_to_ptbr(_canned_pipeline: None) -> None:
    body = client.post("/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT}).json()
    assert body["idioma"] == "pt-BR"


# ---------------------------------------------------------------------------
# (b) Erro envelope on a scripted LLMError — 200, no secoes, raw terminal-only
# ---------------------------------------------------------------------------


def test_gerar_erro_envelope_on_llm_error(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _stub_stages(
        monkeypatch, script=[LLMError("Falha na geração do LinkedIn", "RAW-DETAIL-secreto")]
    )
    with caplog.at_level(logging.ERROR, logger="app.routes.linkedin"):
        resp = client.post(
            "/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT, "language": "pt-BR"}
        )
    assert resp.status_code == 200  # never an HTTP 500 (house envelope rule)
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body  # all-or-nothing: no partial section set (T-03-07)
    assert "limites" not in body
    assert body["erros"] == ["Falha na geração do LinkedIn"]  # PT-BR lines only
    # Raw detail reached the terminal log...
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-DETAIL-secreto" in terminal_text
    # ...but NEVER the API envelope (T-06-04).
    assert "RAW-DETAIL-secreto" not in " ".join(body["erros"])


def test_gerar_erro_envelope_on_empty_headline_llm_error(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Probe edge LI-02/empty end-to-end: a scripted empty headline raises the
    # pipeline's loud LLMError — the route converts it to the erro envelope.
    _stub_stages(monkeypatch, script=[json.dumps({"headline": "   "}, ensure_ascii=False)])
    with caplog.at_level(logging.ERROR, logger="app.routes.linkedin"):
        resp = client.post("/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body
    assert any("headline vazio" in line for line in body["erros"])
    assert "empty headline content" in " ".join(rec.getMessage() for rec in caplog.records)


def test_gerar_erro_envelope_on_broken_profile(
    monkeypatch: pytest.MonkeyPatch, typo_profile_path
) -> None:
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", typo_profile_path)
    resp = client.post("/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert any(str(typo_profile_path) in line for line in body["erros"])


# ---------------------------------------------------------------------------
# (c) Strict request validation → FastAPI's default 422 (planner decision)
# ---------------------------------------------------------------------------


def test_gerar_rejects_sub_min_objetivo() -> None:
    resp = client.post("/api/linkedin/gerar", json={"objetivo": "curto demais"})
    assert resp.status_code == 422  # the client gate mirrors this bound (D-02)


def test_gerar_rejects_unknown_extra_key() -> None:
    resp = client.post(
        "/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT, "hack": True}
    )
    assert resp.status_code == 422  # extra=forbid


def test_gerar_rejects_unknown_language() -> None:
    resp = client.post(
        "/api/linkedin/gerar", json={"objetivo": OBJETIVO_EN, "language": "es"}
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# (d) Structural pins: sync handlers + router BEFORE the SPA mount
# ---------------------------------------------------------------------------


def _iter_api_routes():
    """(path, endpoint_or_None, position) for every route in registration
    order. FastAPI >= 0.141 nests included routers as _IncludedRouter
    objects (original_router) instead of flattening APIRoutes onto
    app.routes — handle both layouts. The Mount entry carries path +
    endpoint=None (its position = SPA mount position)."""
    for position, entry in enumerate(app.routes):
        if isinstance(entry, APIRoute):
            yield entry.path, entry.endpoint, position
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    yield sub.path, sub.endpoint, position
        elif type(entry).__name__ == "Mount":
            yield entry.path, None, position


def test_handlers_are_sync_def_never_coroutines() -> None:
    endpoints = {
        path: endpoint for path, endpoint, _ in _iter_api_routes() if endpoint is not None
    }
    endpoint = endpoints["/api/linkedin/gerar"]  # KeyError would mean the route is missing
    # Pitfall 2: plain def → Starlette threadpool; async would freeze the
    # event loop during the synchronous SDK run.
    assert inspect.iscoroutinefunction(endpoint) is False


def test_linkedin_router_registered_before_spa_mount() -> None:
    entries = list(_iter_api_routes())
    mount_positions = [
        pos for path, endpoint, pos in entries if endpoint is None and path in ("", "/")
    ]
    assert mount_positions, "SPA mount expected at / (frontend/dist guard, Pitfall 5)"
    positions = [pos for p, _, pos in entries if p == "/api/linkedin/gerar"]
    assert positions, "route missing: /api/linkedin/gerar"
    assert max(positions) < mount_positions[0]  # research Pitfall 8
