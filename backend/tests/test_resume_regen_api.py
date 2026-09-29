"""Route tests for POST /api/resume/regenerar — the 200-envelope contract of
plan 05-01, OFFLINE: the pipeline's run_stage is stubbed with canned models
per requested stage and the profile loader is retargeted to the conftest
fixture (D-15/D-16 seams — the REAL run_section_regen runs underneath).

Pinned here: the ok envelope shape (full merged secoes + recomputed
cobertura, no keywords/avisos keys); the erro envelope on a scripted LLMError
(200, NO secoes/cobertura keys, raw detail terminal-only via caplog — the
house pattern from test_resume_api.py); 422 strict validation (extra=forbid,
Literal secao/language, Field bounds: short jd_text, dica > 500, empty
submitted secoes); route presence. The sync-def + router-before-mount
structural pins live in tests/test_resume_api.py (extended there).
"""

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

# Canned payloads per stage — same content as tests/test_resume_api.py.
KEYWORDS_CONTENT = '{"keywords": [{"canonical": "Python", "aliases": [], "pt": "Python", "en": "Python", "category": "competencias"}]}'
RESUMO_CONTENT = '{"resumo": "Resumo em exibição com Python."}'
EXPERIENCIAS_CONTENT = (
    '{"experiencias": [{"company": "Exemplo IA", "title": "Engenheira de Software Sênior", '
    '"bullets": ["Implementou um pipeline RAG com avaliação automática"]}]}'
)
SKILLS_CONTENT = '{"habilidades": ["Python", "Docker"]}'

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


def _submitted_secoes() -> dict:
    """The displayed state the screen re-posts (ExportarSecoes shape)."""
    return {
        "resumo": "Resumo em exibição com Python.",
        "experiencias": [
            {
                "company": "Exemplo IA",
                "title": "Engenheira de Software Sênior",
                "bullets": ["Implementou pipelines de dados"],
            }
        ],
        "habilidades": ["Habilidade antiga"],
    }


def _regen_body(**overrides) -> dict:
    body = {
        "jd_text": JD_PT,
        "language": "pt-BR",
        "secao": "habilidades",
        "secoes": _submitted_secoes(),
        "keywords": [
            {"canonical": "Python", "aliases": [], "pt": "Python", "en": "Python", "category": "competencias"}
        ],
    }
    body.update(overrides)
    return body


@pytest.fixture
def _profile_file(monkeypatch: pytest.MonkeyPatch, valid_profile_path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", valid_profile_path)


def _stub_stages(monkeypatch: pytest.MonkeyPatch, script: list | None = None) -> None:
    """Stub app.resume.pipeline.run_stage: canned model per REQUESTED stage
    (or the next scripted item — content str or exception)."""
    import app.resume.pipeline as pipeline_module

    items = list(script) if script is not None else [None]

    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        item = items.pop(0)
        if isinstance(item, Exception):
            raise item
        if item is None:  # canned model for the requested stage
            return _canned_model(stage)
        return _STAGE_MODELS[stage].model_validate(json.loads(item))

    monkeypatch.setattr(pipeline_module, "run_stage", fake_run_stage)


@pytest.fixture
def _canned_regen(monkeypatch: pytest.MonkeyPatch, _profile_file: None) -> None:
    _stub_stages(monkeypatch)


def _api_paths() -> set[str]:
    """Every APIRoute path — handles FastAPI ≥0.141's nested _IncludedRouter
    layout AND the flattened layout (same walker as test_resume_api.py)."""
    paths = set()
    for entry in app.routes:
        if isinstance(entry, APIRoute):
            paths.add(entry.path)
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    paths.add(sub.path)
    return paths


# ---------------------------------------------------------------------------
# (a) Ok envelope — full merged secoes + recomputed coverage, NOTHING more
# ---------------------------------------------------------------------------


def test_regen_returns_full_merged_ok_envelope(_canned_regen: None) -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body())
    assert resp.status_code == 200
    body = resp.json()
    # EVERY contract key — the interface of record for the 05-01 client.
    assert set(body) == {"status", "idioma", "secoes", "cobertura", "cobertura_resumo"}
    assert body["status"] == "ok"
    assert body["idioma"] == "pt-BR"
    secoes = body["secoes"]
    assert set(secoes) == {"resumo", "experiencias", "habilidades"}
    assert secoes["habilidades"] == ["Python", "Docker"]  # target replaced by the stage output
    assert secoes["resumo"] == "Resumo em exibição com Python."  # sibling byte-identical
    assert secoes["experiencias"] == _submitted_secoes()["experiencias"]
    for entry in body["cobertura"]:
        assert set(entry) == {"canonical", "category", "termo", "status"}
        assert entry["status"] in ("coberto", "ausente")
    resumo_cov = body["cobertura_resumo"]
    assert set(resumo_cov) == {"cobertos", "total"}  # no score anywhere
    assert resumo_cov["total"] == len(body["cobertura"])


def test_regen_accepts_optional_dica(_canned_regen: None) -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body(dica="destacar métricas"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# (b) Erro envelope on a scripted LLMError — 200, no secoes, raw terminal-only
# ---------------------------------------------------------------------------


def test_regen_erro_envelope_on_llm_error(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _stub_stages(monkeypatch, script=[LLMError("Falha na regeneração", "RAW-REGEN-DETAIL")])
    with caplog.at_level(logging.ERROR, logger="app.routes.resume"):
        resp = client.post("/api/resume/regenerar", json=_regen_body())
    assert resp.status_code == 200  # never an HTTP 500 (house envelope rule)
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body  # all-or-nothing: no partial section set (T-03-07)
    assert "cobertura" not in body
    assert body["erros"] == ["Falha na regeneração"]  # PT-BR lines only
    # Raw detail reached the terminal log...
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-REGEN-DETAIL" in terminal_text
    # ...but NEVER the API envelope (T-03-02/T-05-03).
    assert "RAW-REGEN-DETAIL" not in " ".join(body["erros"])


def test_regen_erro_envelope_on_broken_profile(
    monkeypatch: pytest.MonkeyPatch, typo_profile_path
) -> None:
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", typo_profile_path)
    resp = client.post("/api/resume/regenerar", json=_regen_body())
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert any(str(typo_profile_path) in line for line in body["erros"])


# ---------------------------------------------------------------------------
# (c) Strict request validation → FastAPI's default 422 (T-05-02/T-05-05)
# ---------------------------------------------------------------------------


def test_regen_rejects_unknown_extra_key() -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body(hack=True))
    assert resp.status_code == 422  # extra=forbid


def test_regen_rejects_short_jd_text() -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body(jd_text="curto demais"))
    assert resp.status_code == 422


def test_regen_rejects_unknown_secao() -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body(secao="formacao"))
    assert resp.status_code == 422  # Literal["resumo", "experiencias", "habilidades"]


def test_regen_rejects_unknown_language() -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body(language="es"))
    assert resp.status_code == 422


def test_regen_rejects_dica_over_500() -> None:
    resp = client.post("/api/resume/regenerar", json=_regen_body(dica="x" * 501))
    assert resp.status_code == 422  # dica: str | None = Field(max_length=500)


def test_regen_rejects_empty_submitted_habilidades() -> None:
    secoes = _submitted_secoes()
    secoes["habilidades"] = []  # ExportarSecoes min_length=1 (empty-section edge)
    resp = client.post("/api/resume/regenerar", json=_regen_body(secoes=secoes))
    assert resp.status_code == 422


def test_regen_rejects_missing_required_secoes() -> None:
    body = _regen_body()
    del body["secoes"]
    resp = client.post("/api/resume/regenerar", json=body)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# (d) Route presence (structural sync-def/mount pins live in test_resume_api)
# ---------------------------------------------------------------------------


def test_regenerar_route_is_registered() -> None:
    assert "/api/resume/regenerar" in _api_paths()
