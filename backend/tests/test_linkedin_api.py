"""Route tests for POST /api/linkedin/lint + /gerar + /regenerar — the
200-envelope contract of plans 06-01/06-02, OFFLINE: the pipelines' run_stage
is stubbed with canned models per stage and the profile loader is retargeted
to the conftest fixture (D-15/D-16 seams; mirrors tests/test_resume_api.py).

Pinned here: the gerar ok envelope in both languages (full quartet); the lint
ok/erro envelopes (run_lint_only reuse, D-03); the regen ok envelope carrying
the FULL merged secoes + recomputed limites (D-04 Phase 5 semantics); the
erro envelope on a scripted LLMError (200, no secoes/limites keys, raw detail
terminal-only via caplog — the house pattern, T-06-04); the erro envelope on
a broken profile; 422 on a sub-80-char objetivo, unknown body keys
(extra=forbid), an unknown language, an unknown secao value and an empty
submitted headline; sync (non-coroutine) handlers; the linkedin router
registered BEFORE the SPA mount (research Pitfall 8); and the plan-06-04 QA
envelope contract — pt-BR ok envelopes carry the qa dict (keys
glossario/bleed), EN ok envelopes carry qa null, and a glossário load
failure during gerar surfaces as the erro envelope (PromptError → PT-BR
lines, raw detail terminal-only — the fail-fast ladder end-to-end).
"""

import inspect
import json
import logging

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.llm.errors import LLMError, PromptError
from app.llm.schemas import (
    LinkedinExperiencias,
    LinkedinHeadline,
    LinkedinSkills,
    LinkedinSobre,
)
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
SOBRE_CONTENT = json.dumps(
    {"sobre": "Sobre gerado com foco em dados: engenheira sênior em plataformas de nuvem."},
    ensure_ascii=False,
)
EXPERIENCIAS_CONTENT = json.dumps(
    {
        "experiencias": [
            {
                "company": "Exemplo IA",
                "title": "Engenheira de Software Sênior",
                "descricao": "Liderei pipelines de dados em produção com impacto medido.",
            }
        ]
    },
    ensure_ascii=False,
)
SKILLS_CONTENT = json.dumps({"habilidades": ["Python", "SQL", "Docker"]}, ensure_ascii=False)

_CONTENT_BY_STAGE = {
    "linkedin-headline": HEADLINE_CONTENT,
    "linkedin-sobre": SOBRE_CONTENT,
    "linkedin-experiencias": EXPERIENCIAS_CONTENT,
    "linkedin-skills": SKILLS_CONTENT,
}

_MODEL_BY_STAGE = {
    "linkedin-headline": LinkedinHeadline,
    "linkedin-sobre": LinkedinSobre,
    "linkedin-experiencias": LinkedinExperiencias,
    "linkedin-skills": LinkedinSkills,
}


def _canned_model(stage: str):
    return _MODEL_BY_STAGE[stage].model_validate(json.loads(_CONTENT_BY_STAGE[stage]))


@pytest.fixture
def _profile_file(monkeypatch: pytest.MonkeyPatch, valid_profile_path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", valid_profile_path)


def _stub_stages(monkeypatch: pytest.MonkeyPatch, script: list | None = None) -> None:
    """Stub app.linkedin.pipeline.run_stage: a canned model per requested
    stage (or the next scripted item — content str or exception). With no
    script, EVERY call gets its stage's canned model (the quartet runs four
    calls per gerar)."""
    import app.linkedin.pipeline as pipeline_module

    items = list(script) if script is not None else None

    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        if items is None:  # canned model for the requested stage, every call
            return _canned_model(stage)
        item = items.pop(0)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, str):
            return _canned_model(stage).model_validate(json.loads(item))
        return item  # a pre-built model (regen helpers pass models directly)

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
    assert set(body) == {"status", "idioma", "secoes", "limites", "qa"}
    assert body["status"] == "ok"
    assert body["idioma"] == language
    assert body["secoes"]["headline"] == json.loads(HEADLINE_CONTENT)["headline"]
    limites = body["limites"]["headline"]
    assert set(limites) == {"limite", "tamanho", "excesso"}
    assert limites["limite"] == 220
    assert limites["tamanho"] == len(body["secoes"]["headline"])
    assert limites["excesso"] == 0
    # The QA language contract (plan 06-04, D-14): pt-BR ok envelopes ALWAYS
    # carry the report dict, EN ok envelopes ALWAYS carry null — never a
    # silently absent verdict.
    if language == "pt-BR":
        assert set(body["qa"]) == {"glossario", "bleed"}
    else:
        assert body["qa"] is None


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


def test_gerar_erro_envelope_on_glossary_load_failure(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The fail-fast ladder end-to-end (plan 06-04, T-06-10): a malformed
    user-edited glossário raises PromptError AFTER the four stages ran — the
    route converts it to the erro envelope (never an HTTP 500, raw detail
    terminal-only)."""
    import app.linkedin.qa as qa_module

    def broken_load_glossario(prompts_dir=None):
        raise PromptError("Glossário inválido: par malformado", "RAW-GLOSSARIO-secreto")

    monkeypatch.setattr(qa_module, "load_glossario", broken_load_glossario)
    _stub_stages(monkeypatch)  # the four stages succeed; the QA read fails
    with caplog.at_level(logging.ERROR, logger="app.routes.linkedin"):
        resp = client.post("/api/linkedin/gerar", json={"objetivo": OBJETIVO_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body and "limites" not in body  # all-or-nothing
    assert body["erros"] == ["Glossário inválido: par malformado"]  # PT-BR lines
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-GLOSSARIO-secreto" in terminal_text  # raw → terminal only
    assert "RAW-GLOSSARIO-secreto" not in " ".join(body["erros"])


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
# (d) Lint endpoint — the verbatim run_lint_only reuse (D-03)
# ---------------------------------------------------------------------------


def _stub_lint(monkeypatch: pytest.MonkeyPatch, result_or_exc) -> None:
    import app.routes.linkedin as routes_module

    def fake_run_lint_only(objetivo, runs_log=None, client=None):
        if isinstance(result_or_exc, Exception):
            raise result_or_exc
        return result_or_exc

    monkeypatch.setattr(routes_module, "run_lint_only", fake_run_lint_only)


def test_lint_returns_ok_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    canned = {
        "keywords": [
            {
                "canonical": "Python",
                "aliases": [],
                "pt": "Python",
                "en": "Python",
                "category": "competencias",
            }
        ],
        "avisos": ["Nenhuma palavra-chave crítica ausente."],
    }
    _stub_lint(monkeypatch, canned)
    resp = client.post("/api/linkedin/lint", json={"objetivo": OBJETIVO_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"status", "keywords", "avisos"}
    assert body["status"] == "ok"
    assert body["keywords"] == canned["keywords"]
    assert body["avisos"] == canned["avisos"]


def test_lint_erro_envelope_on_llm_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _stub_lint(monkeypatch, LLMError("Falha na análise do objetivo", "RAW-LINT-secreto"))
    with caplog.at_level(logging.ERROR, logger="app.routes.linkedin"):
        resp = client.post("/api/linkedin/lint", json={"objetivo": OBJETIVO_PT})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert "keywords" not in body and "avisos" not in body
    assert body["erros"] == ["Falha na análise do objetivo"]
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-LINT-secreto" in terminal_text
    assert "RAW-LINT-secreto" not in " ".join(body["erros"])


def test_lint_rejects_sub_min_objetivo_and_extra_keys() -> None:
    assert client.post("/api/linkedin/lint", json={"objetivo": "curto"}).status_code == 422
    assert (
        client.post(
            "/api/linkedin/lint", json={"objetivo": OBJETIVO_PT, "hack": True}
        ).status_code
        == 422
    )


# ---------------------------------------------------------------------------
# (e) Regen endpoint — full merged secoes + recomputed limites (D-04)
# ---------------------------------------------------------------------------


def _regen_body(secao: str = "headline", **overrides) -> dict:
    body = {
        "objetivo": OBJETIVO_PT,
        "language": "pt-BR",
        "secao": secao,
        "secoes": {
            "headline": "Headline em exibição — Python e dados",
            "sobre": "Sobre em exibição " + "x" * 2600,  # over the 2600 limit
            "experiencias": [
                {
                    "company": "Exemplo IA",
                    "title": "Engenheira de Software Sênior",
                    "descricao": "Descrição de experiência em exibição.",
                }
            ],
            "habilidades": ["Habilidade antiga"],
        },
    }
    body.update(overrides)
    return body


def test_regen_returns_full_merged_secoes_and_recomputed_limites(
    monkeypatch: pytest.MonkeyPatch, _profile_file: None
) -> None:
    _stub_stages(monkeypatch)
    resp = client.post("/api/linkedin/regenerar", json=_regen_body("headline"))
    assert resp.status_code == 200
    body = resp.json()
    # The route returns the pipeline result directly — the full ok envelope.
    assert set(body) == {"status", "idioma", "secoes", "limites", "qa"}
    assert body["status"] == "ok"
    assert set(body["secoes"]) == {"headline", "sobre", "experiencias", "habilidades"}
    assert body["secoes"]["headline"] == json.loads(HEADLINE_CONTENT)["headline"]
    # The regen recomputed QA over the FULL merged state (plan 06-04).
    assert set(body["qa"]) == {"glossario", "bleed"}
    # Siblings pass through from the SUBMITTED state...
    assert body["secoes"]["sobre"] == _regen_body()["secoes"]["sobre"]
    assert body["secoes"]["habilidades"] == ["Habilidade antiga"]
    # ...and limites are RECOMPUTED over the full merged state — the
    # submitted over-limit sibling sobre still surfaces (D-04/D-07).
    assert set(body["limites"]) == {"headline", "sobre", "experiencias", "habilidades"}
    assert body["limites"]["sobre"]["excesso"] > 0
    assert body["limites"]["headline"]["tamanho"] == len(body["secoes"]["headline"])


def test_regen_erro_envelope_on_llm_error(
    monkeypatch: pytest.MonkeyPatch,
    _profile_file: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _stub_stages(
        monkeypatch,
        script=[LLMError("Falha na regeneração da seção", "RAW-REGEN-secreto")],
    )
    with caplog.at_level(logging.ERROR, logger="app.routes.linkedin"):
        resp = client.post("/api/linkedin/regenerar", json=_regen_body("sobre"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body and "limites" not in body
    assert body["erros"] == ["Falha na regeneração da seção"]
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-REGEN-secreto" in terminal_text
    assert "RAW-REGEN-secreto" not in " ".join(body["erros"])


def test_regen_rejects_unknown_secao_value(_profile_file: None) -> None:
    # "resumo" is the RESUME section id — never a LinkedIn one (Literal pin).
    resp = client.post("/api/linkedin/regenerar", json=_regen_body("resumo"))
    assert resp.status_code == 422


def test_regen_rejects_extra_keys_and_empty_submitted_headline() -> None:
    resp = client.post("/api/linkedin/regenerar", json=_regen_body(hack=True))
    assert resp.status_code == 422  # extra=forbid
    body = _regen_body()
    body["secoes"]["headline"] = ""  # an empty block can never be displayed
    resp = client.post("/api/linkedin/regenerar", json=body)
    assert resp.status_code == 422  # min_length=1 floor (loud-empty mirror)


def test_regen_defaults_dica_to_none(
    monkeypatch: pytest.MonkeyPatch, _profile_file: None
) -> None:
    """The frontend omits the empty dica KEY (extra=forbid discipline) — the
    body without a dica key must pass validation and reach the pipeline."""
    _stub_stages(monkeypatch)
    resp = client.post("/api/linkedin/regenerar", json=_regen_body())
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


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
    for path in (
        "/api/linkedin/lint",
        "/api/linkedin/gerar",
        "/api/linkedin/regenerar",
    ):
        endpoint = endpoints[path]  # KeyError would mean the route is missing
        # Pitfall 2: plain def → Starlette threadpool; async would freeze the
        # event loop during the synchronous SDK run.
        assert inspect.iscoroutinefunction(endpoint) is False, path


def test_linkedin_router_registered_before_spa_mount() -> None:
    entries = list(_iter_api_routes())
    mount_positions = [
        pos for path, endpoint, pos in entries if endpoint is None and path in ("", "/")
    ]
    assert mount_positions, "SPA mount expected at / (frontend/dist guard, Pitfall 5)"
    for path in (
        "/api/linkedin/lint",
        "/api/linkedin/gerar",
        "/api/linkedin/regenerar",
    ):
        positions = [pos for p, _, pos in entries if p == path]
        assert positions, f"route missing: {path}"
        assert max(positions) < mount_positions[0]  # research Pitfall 8
