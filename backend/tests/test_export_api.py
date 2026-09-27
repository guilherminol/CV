"""Route tests for POST /api/resume/exportar (plan 04-02) — the full envelope
family, OFFLINE: html_to_pdf and parse_back_check are stubbed at the module
under test (app.routes.export) exactly the way test_resume_api.py stubs
run_stage — the render+gate seam. One case runs the REAL chain end-to-end
(local Chromium, offline, session-rendered once) as the D-07 route-layer
proof.

Pinned here: the ok envelope {status, filename, pdf_base64, selfcheck} — THE
cross-tier contract plan 04-03's client.ts mirrors; the gate-failure erro
envelope with NO PDF payload key (T-04-04) and raw detail terminal-only via
caplog (T-04-03); the chromium-missing erro envelope carrying the install
hint; the strict 422 set (extra key, empty resumo/experiencias/habilidades,
unknown idioma — REVIEW-02/empty edge); sync handlers + export router
registered BEFORE the SPA mount; and the D-15 no-LLM-machinery structural
pin scoped to the export modules.
"""

import ast
import base64
import inspect
import logging
import re
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.config import RUNS_LOG
from app.export.gate import GateResult, MSG_ACENTOS_CORROMPIDOS
from app.export.errors import ExportError
from app.export.pdf import _BROWSER_MISSING_PTBR
from app.export.render import section_keys
from app.main import app
from test_export_gate import _persona  # the same session persona as 04-01

client = TestClient(app)

EXPORT_APP_DIR = Path(__file__).resolve().parents[1] / "app"
EXPORT_MODULES = sorted((EXPORT_APP_DIR / "export").glob("*.py")) + [
    EXPORT_APP_DIR / "routes" / "export.py"
]

# Fixed engine output for the stubbed ok-path tests (never written to disk).
STUB_PDF_BYTES = b"%PDF-1.7 stub-bytes-for-tests"

# Stub gates: ONE GateResult feeds both the delivery decision and the
# selfcheck payload — the stubs mirror exactly what a real pass/fail carries.
_PASSING_GATE = GateResult(
    ok=True,
    erros_ptbr=[],
    raw="stub-flat-text",
    contato_primeiro=True,
    ordem_titulos=True,
    coocorrencia=True,
    acentos=True,
    flat_text="Resumo Python vive nas habilidades Docker tambem",
    ordem_rows=[
        {"id": "contato", "ok": True},
        {"id": "resumo", "ok": True},
        {"id": "experiencias", "ok": True},
        {"id": "formacao", "ok": True},
        {"id": "habilidades", "ok": True},
        {"id": "certificacoes", "ok": True},
        {"id": "idiomas", "ok": True},
        {"id": "projetos", "ok": True},
    ],
)
_FAILING_GATE = GateResult(
    ok=False,
    erros_ptbr=[MSG_ACENTOS_CORROMPIDOS],
    raw="RAW-GATE-DETAIL-secreto",
    contato_primeiro=True,
    ordem_titulos=True,
    coocorrencia=False,
    acentos=False,
    flat_text="Resumo com acentos corrompidos",
    ordem_rows=[
        {"id": "contato", "ok": True},
        {"id": "resumo", "ok": True},
    ],
)

KEYWORD_PYTHON = {
    "canonical": "Python",
    "aliases": [],
    "pt": "Python",
    "en": "Python",
    "category": "competencias",
}


def _export_payload(idioma: str) -> dict:
    """The displayed state as the frontend would send it (D-10): perfil +
    generated secoes + keywords + run language."""
    profile, secoes = _persona(idioma)
    return {
        "perfil": profile.model_dump(mode="json"),
        "secoes": {
            "resumo": secoes.resumo,
            "experiencias": [exp.model_dump(mode="json") for exp in secoes.experiencias],
            "habilidades": secoes.habilidades,
        },
        "keywords": [KEYWORD_PYTHON],
        "idioma": idioma,
    }


# ---------------------------------------------------------------------------
# (a) Stub seams — render + gate, at the module under test
# ---------------------------------------------------------------------------


@pytest.fixture
def _stub_ok_export(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixed bytes + a PASSING GateResult: the whole pure chain (join →
    html build → ExpectedDoc assembly → selfcheck) still runs for real."""
    import app.routes.export as export_module

    monkeypatch.setattr(export_module, "html_to_pdf", lambda html: STUB_PDF_BYTES)
    monkeypatch.setattr(
        export_module, "parse_back_check", lambda pdf_bytes, expected: _PASSING_GATE
    )


@pytest.fixture
def _stub_failing_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.routes.export as export_module

    monkeypatch.setattr(export_module, "html_to_pdf", lambda html: STUB_PDF_BYTES)
    monkeypatch.setattr(
        export_module, "parse_back_check", lambda pdf_bytes, expected: _FAILING_GATE
    )


@pytest.fixture
def _stub_browser_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """html_to_pdf raising the 04-01 ExportError (install hint + raw detail)."""

    def raise_browser_missing(html: str) -> bytes:
        raise ExportError(_BROWSER_MISSING_PTBR, "RAW-BROWSER-DETAIL-secreto")

    import app.routes.export as export_module

    monkeypatch.setattr(export_module, "html_to_pdf", raise_browser_missing)


# ---------------------------------------------------------------------------
# (b) Ok envelope — {status, filename, pdf_base64, selfcheck} (the 04-03 contract)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("idioma", ["pt-BR", "en"])
def test_exportar_ok_envelope(idioma: str, _stub_ok_export: None) -> None:
    resp = client.post("/api/resume/exportar", json=_export_payload(idioma))
    assert resp.status_code == 200
    body = resp.json()
    # EVERY contract key — the interface of record for plan 04-03's client.
    assert set(body) == {"status", "filename", "pdf_base64", "selfcheck"}
    assert body["status"] == "ok"
    assert re.fullmatch(rf"curriculo-{idioma}-\d{{4}}-\d{{2}}-\d{{2}}\.pdf", body["filename"])
    assert base64.b64decode(body["pdf_base64"]) == STUB_PDF_BYTES
    selfcheck = body["selfcheck"]
    assert set(selfcheck) == {"ordem", "sobrevivencia", "gate"}
    assert selfcheck["ordem"] == _PASSING_GATE.ordem_rows
    assert selfcheck["gate"] == {"coocorrencia": True, "acentos": True}
    assert selfcheck["sobrevivencia"] == [
        {
            "canonical": "Python",
            "category": "competencias",
            "termo": "Python",
            "status": "coberto",
        }
    ]


# ---------------------------------------------------------------------------
# (c) Gate-failure erro envelope — NO PDF key, raw detail terminal-only
# ---------------------------------------------------------------------------


def test_exportar_gate_failure_erro_envelope(
    _stub_failing_gate: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="app.routes.export"):
        resp = client.post("/api/resume/exportar", json=_export_payload("pt-BR"))
    assert resp.status_code == 200  # never an HTTP 500 (house envelope rule)
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == _FAILING_GATE.erros_ptbr  # PT-BR lines naming the check
    # T-04-04: a gate-failing export NEVER carries PDF bytes under any key —
    # no partial delivery, no "download anyway" path (D-08).
    assert "pdf_base64" not in body
    assert "filename" not in body
    assert "selfcheck" not in body
    # T-04-03 split: the raw extracted text reached the terminal log...
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert _FAILING_GATE.raw in terminal_text
    # ...but NEVER the API envelope.
    assert _FAILING_GATE.raw not in " ".join(body["erros"])


def test_exportar_browser_missing_erro_envelope(
    _stub_browser_missing: None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR, logger="app.routes.export"):
        resp = client.post("/api/resume/exportar", json=_export_payload("pt-BR"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == _BROWSER_MISSING_PTBR.splitlines()  # the install hint
    assert "pdf_base64" not in body
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-BROWSER-DETAIL-secreto" in terminal_text
    assert "RAW-BROWSER-DETAIL-secreto" not in " ".join(body["erros"])


# ---------------------------------------------------------------------------
# (d) Strict request validation → FastAPI's default 422 (REVIEW-02/empty edge)
# ---------------------------------------------------------------------------


def test_exportar_rejects_unknown_extra_key() -> None:
    payload = _export_payload("pt-BR")
    payload["hack"] = True
    assert client.post("/api/resume/exportar", json=payload).status_code == 422


def test_exportar_rejects_empty_resumo() -> None:
    payload = _export_payload("pt-BR")
    payload["secoes"]["resumo"] = ""
    assert client.post("/api/resume/exportar", json=payload).status_code == 422


def test_exportar_rejects_empty_experiencias() -> None:
    payload = _export_payload("pt-BR")
    payload["secoes"]["experiencias"] = []
    assert client.post("/api/resume/exportar", json=payload).status_code == 422


def test_exportar_rejects_empty_habilidades() -> None:
    payload = _export_payload("pt-BR")
    payload["secoes"]["habilidades"] = []
    assert client.post("/api/resume/exportar", json=payload).status_code == 422


def test_exportar_rejects_unknown_idioma() -> None:
    payload = _export_payload("pt-BR")
    payload["idioma"] = "es"
    assert client.post("/api/resume/exportar", json=payload).status_code == 422


# ---------------------------------------------------------------------------
# (e) Structural pins: sync handlers, router BEFORE the SPA mount, no LLM
# ---------------------------------------------------------------------------


def _iter_api_routes():
    """(path, endpoint_or_None, position) for every route in registration
    order — same helper as test_resume_api.py (handles the FastAPI >= 0.141
    _IncludedRouter nesting; the Mount entry carries endpoint=None)."""
    for position, entry in enumerate(app.routes):
        if isinstance(entry, APIRoute):
            yield entry.path, entry.endpoint, position
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    yield sub.path, sub.endpoint, position
        elif type(entry).__name__ == "Mount":
            yield entry.path, None, position


def test_exportar_handler_is_sync_def_never_coroutine() -> None:
    endpoints = {
        path: endpoint for path, endpoint, _ in _iter_api_routes() if endpoint is not None
    }
    endpoint = endpoints["/api/resume/exportar"]  # KeyError would mean missing route
    # Pitfall 1: sync Playwright RAISES inside a running asyncio loop; plain
    # def → Starlette threadpool keeps the event loop responsive.
    assert inspect.iscoroutinefunction(endpoint) is False


def test_all_api_handlers_are_sync_def() -> None:
    for path, endpoint, _ in _iter_api_routes():
        if endpoint is not None:
            assert inspect.iscoroutinefunction(endpoint) is False, path


def test_export_router_registered_before_spa_mount() -> None:
    entries = list(_iter_api_routes())
    mount_positions = [
        pos for path, endpoint, pos in entries if endpoint is None and path in ("", "/")
    ]
    assert mount_positions, "SPA mount expected at / (frontend/dist guard, Pitfall 5)"
    positions = [pos for p, _, pos in entries if p == "/api/resume/exportar"]
    assert positions, "route missing: /api/resume/exportar"
    assert max(positions) < mount_positions[0]  # Pitfall 3/5/6


# D-15 prohibition: no LLM judge in the export path. app.llm.schemas (pure
# Pydantic DTOs the displayed state travels in) is allowed — the ban is the
# CALL machinery (gateway/prompts/logging/client) plus the generation
# pipeline (D-10: the route renders the submitted state only).
_LLM_MACHINERY = ("gateway", "prompts", "logging", "client")


def _imports_llm_machinery(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module:
            names.extend(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        for full in names:
            parts = full.split(".")
            if parts[:3] == ["app", "resume", "pipeline"]:
                return True
            if parts[:2] == ["app", "llm"] and len(parts) >= 3 and parts[2] in _LLM_MACHINERY:
                return True
    return False


def test_export_path_never_imports_llm_machinery() -> None:
    """Scoped to the export modules (the whole app legitimately imports
    app.llm elsewhere) — export stays offline and deterministic (D-15)."""
    for path in EXPORT_MODULES:
        source = path.read_text(encoding="utf-8")
        assert not _imports_llm_machinery(source), f"{path.name} must not import LLM machinery"


# ---------------------------------------------------------------------------
# (f) REAL render end-to-end — the D-07 proof at the route layer (no stubs)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_ok_envelope() -> dict:
    """The persona export through the REAL chain: pure builder → local
    Chromium (~1-3s, offline) → pypdf gate → selfcheck. Fail-loud: a missing
    Chromium surfaces as ExportError, never skip-silent. Also proves export
    adds NO line to runs.jsonl (LLM-call-only logging contract)."""
    before = RUNS_LOG.read_text(encoding="utf-8").count("\n") if RUNS_LOG.exists() else 0
    resp = client.post("/api/resume/exportar", json=_export_payload("pt-BR"))
    assert resp.status_code == 200
    after = RUNS_LOG.read_text(encoding="utf-8").count("\n") if RUNS_LOG.exists() else 0
    assert after == before, "export must not write a runs.jsonl line"
    return resp.json()


def test_exportar_real_render_ok_envelope(real_ok_envelope: dict) -> None:
    body = real_ok_envelope
    assert body["status"] == "ok"
    assert re.fullmatch(r"curriculo-pt-BR-\d{4}-\d{2}-\d{2}\.pdf", body["filename"])
    pdf_bytes = base64.b64decode(body["pdf_base64"])
    assert pdf_bytes[:5] == b"%PDF-"  # PDF magic header — plausible bytes
    selfcheck = body["selfcheck"]
    assert set(selfcheck) == {"ordem", "sobrevivencia", "gate"}
    assert selfcheck["ordem"][0] == {"id": "contato", "ok": True}
    assert [row["id"] for row in selfcheck["ordem"][1:]] == list(section_keys)
    assert all(row["ok"] for row in selfcheck["ordem"]), selfcheck["ordem"]
    assert selfcheck["gate"] == {"coocorrencia": True, "acentos": True}
    # the travelled keyword survived on the REAL PDF text (full-text input —
    # Python renders in Habilidades)
    assert selfcheck["sobrevivencia"] == [
        {
            "canonical": "Python",
            "category": "competencias",
            "termo": "Python",
            "status": "coberto",
        }
    ]
