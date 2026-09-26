"""Route tests for POST /api/resume/lint + POST /api/resume/gerar — the
normative 200-envelope contract of plan 03-03, OFFLINE: the pipeline's
run_stage is stubbed with canned models per stage and the profile loader is
retargeted to the conftest fixture (D-15/D-16 seams).

Pinned here: ok envelopes for both endpoints in both languages; the erro
envelope on a scripted LLMError (200, NO secoes key, raw detail terminal-only
via caplog — the house pattern from test_api.py); the erro envelope on a
broken profile; 422 on short jd_text and unknown body keys (extra=forbid);
sync (non-coroutine) handlers; router registration BEFORE the SPA mount.
"""

import inspect
import json
import logging

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.llm.errors import LLMError
from app.llm.schemas import (
    KeywordExtraction,
    ResumeExperiencias,
    ResumeSkills,
    ResumeSummary,
)
from app.main import app

client = TestClient(app)

# ≥80 chars — passes the strict request validation (V5).
JD_PT = (
    "Vaga: engenheiro(a) de dados sênior. Requisitos: experiência com Python, "
    "Docker e pipelines de dados em produção. Diferencial: certificação AWS."
)
JD_EN = (
    "Job opening: senior data engineer. Requirements: hands-on experience with "
    "Python, Docker and production data pipelines. Nice to have: AWS certification."
)

# Canned payloads per stage — same content as tests/test_resume_pipeline.py.
KEYWORDS_CONTENT = json.dumps(
    {
        "keywords": [
            {
                "canonical": "Python",
                "aliases": [],
                "pt": "Python",
                "en": "Python",
                "category": "competencias",
            },
            {
                "canonical": "Docker",
                "aliases": [],
                "pt": "Docker",
                "en": "Docker",
                "category": "ferramentas",
            },
        ]
    },
    ensure_ascii=False,
)
RESUMO_CONTENT = json.dumps(
    {"resumo": "Engenheira de dados sênior com pipeline RAG e avaliação automática."},
    ensure_ascii=False,
)
EXPERIENCIAS_CONTENT = json.dumps(
    {
        "experiencias": [
            {
                "company": "Exemplo IA",
                "title": "Engenheira de Software Sênior",
                "bullets": ["Implementou um pipeline RAG com avaliação automática"],
            }
        ]
    },
    ensure_ascii=False,
)
SKILLS_CONTENT = json.dumps(
    {"habilidades": ["Python", "Docker"]},
    ensure_ascii=False,
)

_STAGE_CONTENT = {
    "keyword-extraction": KEYWORDS_CONTENT,
    "resume-summary": RESUMO_CONTENT,
    "resume-experiencias": EXPERIENCIAS_CONTENT,
    "resume-skills": SKILLS_CONTENT,
}
_STAGE_MODELS = {
    "keyword-extraction": KeywordExtraction,
    "resume-summary": ResumeSummary,
    "resume-experiencias": ResumeExperiencias,
    "resume-skills": ResumeSkills,
}


def _canned_model(stage: str):
    return _STAGE_MODELS[stage].model_validate(json.loads(_STAGE_CONTENT[stage]))


@pytest.fixture
def _profile_file(monkeypatch: pytest.MonkeyPatch, valid_profile_path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", valid_profile_path)


def _stub_stages(monkeypatch: pytest.MonkeyPatch, script: list | None = None) -> None:
    """Stub app.resume.pipeline.run_stage: canned model per requested stage
    (or the next scripted item — content str or exception)."""
    import app.resume.pipeline as pipeline_module

    items = list(script) if script is not None else list(_STAGE_CONTENT.values())

    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        item = items.pop(0)
        if isinstance(item, Exception):
            raise item
        if item is None:  # canned model for the requested stage
            return _canned_model(stage)
        return _STAGE_MODELS[stage].model_validate(json.loads(item))

    monkeypatch.setattr(pipeline_module, "run_stage", fake_run_stage)


@pytest.fixture
def _canned_pipeline(monkeypatch: pytest.MonkeyPatch, _profile_file: None) -> None:
    _stub_stages(monkeypatch)


# ---------------------------------------------------------------------------
# (a) Lint endpoint — pre-generate extraction + lint (SC5)
# ---------------------------------------------------------------------------


def test_lint_returns_ok_envelope_with_canned_keywords(_canned_pipeline: None) -> None:
    resp = client.post("/api/resume/lint", json={"jd_text": JD_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["keywords"] == json.loads(KEYWORDS_CONTENT)["keywords"]  # verbatim
    assert isinstance(body["avisos"], list)


# ---------------------------------------------------------------------------
# (b) Gerar endpoint — the FULL ok envelope, both languages
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("jd", [JD_PT, JD_EN])
@pytest.mark.parametrize("language", ["pt-BR", "en"])
def test_gerar_returns_full_ok_envelope_both_languages(
    jd: str, language: str, _canned_pipeline: None
) -> None:
    resp = client.post("/api/resume/gerar", json={"jd_text": jd, "language": language})
    assert resp.status_code == 200
    body = resp.json()
    # EVERY contract key — the interface of record for plan 03-04's client.
    assert set(body) == {
        "status",
        "idioma",
        "keywords",
        "avisos",
        "secoes",
        "cobertura",
        "cobertura_resumo",
    }
    assert body["status"] == "ok"
    assert body["idioma"] == language
    assert body["keywords"] == json.loads(KEYWORDS_CONTENT)["keywords"]
    secoes = body["secoes"]
    assert set(secoes) == {"resumo", "experiencias", "habilidades"}
    assert secoes["resumo"] == json.loads(RESUMO_CONTENT)["resumo"]
    assert secoes["experiencias"] == json.loads(EXPERIENCIAS_CONTENT)["experiencias"]
    assert secoes["habilidades"] == json.loads(SKILLS_CONTENT)["habilidades"]
    assert len(body["cobertura"]) == len(body["keywords"])
    for entry in body["cobertura"]:
        assert set(entry) == {"canonical", "category", "termo", "status"}
        assert entry["status"] in ("coberto", "ausente")
    resumo_cov = body["cobertura_resumo"]
    assert set(resumo_cov) == {"cobertos", "total"}  # no score anywhere
    assert resumo_cov["total"] == len(body["cobertura"])
    assert 0 <= resumo_cov["cobertos"] <= resumo_cov["total"]


def test_gerar_defaults_language_to_ptbr(_canned_pipeline: None) -> None:
    body = client.post("/api/resume/gerar", json={"jd_text": JD_PT}).json()
    assert body["idioma"] == "pt-BR"


# ---------------------------------------------------------------------------
# (c) Erro envelope on a scripted LLMError — 200, no secoes, raw terminal-only
# ---------------------------------------------------------------------------


def test_gerar_erro_envelope_on_llm_error(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _stub_stages(monkeypatch, script=[LLMError("Falha na geração", "RAW-DETAIL-secreto")])
    with caplog.at_level(logging.ERROR, logger="app.routes.resume"):
        resp = client.post(
            "/api/resume/gerar", json={"jd_text": JD_PT, "language": "pt-BR"}
        )
    assert resp.status_code == 200  # never an HTTP 500 (house envelope rule)
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body  # all-or-nothing: no partial section set (T-03-07)
    assert "cobertura" not in body
    assert body["erros"] == ["Falha na geração"]  # PT-BR lines only
    # Raw detail reached the terminal log...
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-DETAIL-secreto" in terminal_text
    # ...but NEVER the API envelope (T-03-02).
    assert "RAW-DETAIL-secreto" not in " ".join(body["erros"])


def test_lint_erro_envelope_on_llm_error(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _stub_stages(monkeypatch, script=[LLMError("Falha na análise", "RAW-LINT-DETAIL")])
    with caplog.at_level(logging.ERROR, logger="app.routes.resume"):
        resp = client.post("/api/resume/lint", json={"jd_text": JD_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == ["Falha na análise"]
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-LINT-DETAIL" in terminal_text
    assert "RAW-LINT-DETAIL" not in " ".join(body["erros"])


# ---------------------------------------------------------------------------
# (d) Erro envelope on a broken profile — the exact file is named
# ---------------------------------------------------------------------------


def test_gerar_erro_envelope_on_broken_profile(
    monkeypatch: pytest.MonkeyPatch, typo_profile_path
) -> None:
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", typo_profile_path)
    resp = client.post("/api/resume/gerar", json={"jd_text": JD_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert any(str(typo_profile_path) in line for line in body["erros"])


# ---------------------------------------------------------------------------
# (e) Strict request validation → FastAPI's default 422 (planner decision)
# ---------------------------------------------------------------------------


def test_lint_rejects_short_jd_text() -> None:
    resp = client.post("/api/resume/lint", json={"jd_text": "curto demais"})
    assert resp.status_code == 422


def test_lint_rejects_unknown_extra_key() -> None:
    resp = client.post("/api/resume/lint", json={"jd_text": JD_PT, "hack": True})
    assert resp.status_code == 422  # extra=forbid


def test_gerar_rejects_unknown_language() -> None:
    resp = client.post(
        "/api/resume/gerar", json={"jd_text": JD_PT, "language": "es"}
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# (f) Structural pins: sync handlers + router BEFORE the SPA mount
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
    for path in ("/api/resume/lint", "/api/resume/gerar"):
        endpoint = endpoints[path]  # KeyError would mean the route is missing
        # Pitfall 2: plain def → Starlette threadpool; async would freeze the
        # event loop during the ~60s synchronous SDK run.
        assert inspect.iscoroutinefunction(endpoint) is False, path


def test_resume_router_registered_before_spa_mount() -> None:
    entries = list(_iter_api_routes())
    mount_positions = [
        pos for path, endpoint, pos in entries if endpoint is None and path in ("", "/")
    ]
    assert mount_positions, "SPA mount expected at / (frontend/dist guard, Pitfall 5)"
    for path in ("/api/resume/lint", "/api/resume/gerar"):
        positions = [pos for p, _, pos in entries if p == path]
        assert positions, f"route missing: {path}"
        assert max(positions) < mount_positions[0], path  # Pitfall 3/5
