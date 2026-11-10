"""Route tests for GET /api/tracker/resumo + POST /api/tracker/candidaturas —
the 200-envelope contract of plan 07-01, 100% OFFLINE (D-15 — the tracker has
no LLM; the suite needs no marker opt-out).

Pinned here: the tracker router registered BEFORE the SPA mount (research
Pitfall 5); both handlers plain sync `def` (threadpool dispatch contract);
the resumo ZERO state on a fresh DB (auto-migration via the yield dependency:
contadores all zero + the 5 seeded stages); the create roundtrip (POST → GET
resumo shows ativas=1 and the row with empresa echoed + derived fields
present); 422 vectors (unknown key — extra=forbid; oversized empresa; bad
date pattern); the erro-envelope shape for an unknown estagio_id (200 +
status erro + PT-BR line, raw detail terminal-only via caplog); and the
D-04 posture — no row-removal route among the shipped tracker routes.

Isolation seam (RESEARCH Wave-0): the fixture monkeypatches the
app.tracker.db module constant TRACKER_DB at tmp_path — per-test fresh file,
NEVER the real data/ directory.
"""

import inspect
import logging

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import app.tracker.db as tracker_db
from app.main import app

client = TestClient(app)

CRIACAO_MINIMA = {"empresa": "Acme", "cargo": "Engenheira de Dados"}


@pytest.fixture(autouse=True)
def db_tmp(tmp_path, monkeypatch):
    """Fresh tracker DB per test at tmp_path — never the real data/."""
    alvo = tmp_path / "tracker.db"
    monkeypatch.setattr(tracker_db, "TRACKER_DB", alvo)
    return alvo


def _iter_api_routes():
    """(path, endpoint_or_None, position) for every route in registration
    order. FastAPI >= 0.141 nests included routers as _IncludedRouter
    objects (original_router) instead of flattening APIRoutes onto
    app.routes — handle both layouts (test_linkedin_api precedent). The
    Mount entry carries path + endpoint=None (its position = SPA mount)."""
    for position, entry in enumerate(app.routes):
        if isinstance(entry, APIRoute):
            yield entry.path, entry.endpoint, position
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    yield sub.path, sub.endpoint, position
        elif type(entry).__name__ == "Mount":
            yield entry.path, None, position


def _rotas_api():
    """APIRoute objects in registration order (same nested layout handling
    as _iter_api_routes — needed for route-level attributes like .methods)."""
    for entry in app.routes:
        if isinstance(entry, APIRoute):
            yield entry
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    yield sub


# ---------------------------------------------------------------------------
# (a) Structural pins: sync handlers + router BEFORE the SPA mount
# ---------------------------------------------------------------------------


def test_handlers_are_sync_def_never_coroutines() -> None:
    endpoints = {
        path: endpoint
        for path, endpoint, _ in _iter_api_routes()
        if endpoint is not None
    }
    for path in ("/api/tracker/resumo", "/api/tracker/candidaturas"):
        endpoint = endpoints[path]  # KeyError would mean the route is missing
        # Plain def → Starlette threadpool; the sqlite3 connection is opened
        # on the serving thread (RESEARCH Pattern 1).
        assert inspect.iscoroutinefunction(endpoint) is False, path


def test_router_registered_before_spa_mount() -> None:
    entries = list(_iter_api_routes())
    mount_positions = [
        pos for path, endpoint, pos in entries if endpoint is None and path in ("", "/")
    ]
    assert mount_positions, "SPA mount expected at / (frontend/dist guard, Pitfall 5)"
    for path in ("/api/tracker/resumo", "/api/tracker/candidaturas"):
        pos_rota = next(pos for p, _, pos in entries if p == path)
        assert pos_rota < min(mount_positions), (
            f"{path} registrada depois do mount SPA — inalcançável (Pitfall 5)"
        )


# ---------------------------------------------------------------------------
# (b) Resumo zero state on a fresh DB (auto-migration via the dependency)
# ---------------------------------------------------------------------------


def test_resumo_zero_state_fresh_db() -> None:
    resp = client.get("/api/tracker/resumo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # D-07 zero state: no events persisted → enviados/entrevistas zero.
    assert body["contadores"] == {"enviados": 0, "entrevistas": 0, "ativas": 0}
    assert len(body["estagios"]) == 5  # v1 seed set, ordem 1..5
    assert [e["nome"] for e in body["estagios"]] == [
        "Pesquisando",
        "Enviado",
        "Entrevista",
        "Oferta",
        "Encerrado",
    ]
    assert body["candidaturas"] == []


# ---------------------------------------------------------------------------
# (c) Create roundtrip — the tracer path POST → SQLite → resumo
# ---------------------------------------------------------------------------


def test_criar_candidatura_roundtrip() -> None:
    resp = client.post("/api/tracker/candidaturas", json=CRIACAO_MINIMA)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    candidatura = body["candidatura"]
    assert candidatura["empresa"] == CRIACAO_MINIMA["empresa"]
    assert candidatura["cargo"] == CRIACAO_MINIMA["cargo"]
    # Default stage resolves server-side to the FIRST stage by ordem (D-05).
    assert candidatura["estagio_nome"] == "Pesquisando"
    assert candidatura["arquivada"] is False  # JSON boolean on the wire
    assert candidatura["criada_em"]  # date-only ISO stamped server-side
    # Derived fields present, computed server-side (the UI never recomputes).
    assert candidatura["dias_para_prazo"] is None
    assert candidatura["sugerir_followup"] is False
    assert candidatura["atrasado_prazo"] is False
    assert candidatura["followup_pendente"] is False
    assert candidatura["followup_vencido"] is False
    assert candidatura["eventos"] == []

    resumo = client.get("/api/tracker/resumo").json()
    assert resumo["status"] == "ok"
    # D-07: a candidatura without events counts in ativas, in none of the
    # event-derived counters.
    assert resumo["contadores"] == {"enviados": 0, "entrevistas": 0, "ativas": 1}
    assert resumo["candidaturas"][0]["empresa"] == CRIACAO_MINIMA["empresa"]


# ---------------------------------------------------------------------------
# (d) Validation failures stay FastAPI 422 (extra=forbid + bounds + patterns)
# ---------------------------------------------------------------------------


def test_422_chave_desconhecida_no_body() -> None:
    resp = client.post(
        "/api/tracker/candidaturas",
        json={**CRIACAO_MINIMA, "campo_inexistente": "x"},
    )
    assert resp.status_code == 422


def test_422_empresa_acima_do_limite() -> None:
    resp = client.post(
        "/api/tracker/candidaturas",
        json={"empresa": "A" * 201, "cargo": "Dev"},
    )
    assert resp.status_code == 422


def test_422_data_fora_do_padrao_iso() -> None:
    resp = client.post(
        "/api/tracker/candidaturas",
        json={**CRIACAO_MINIMA, "data_aplicacao": "2026/01/01"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# (e) Erro envelope: unknown estagio_id — 200 + status erro + PT-BR line,
# raw detail terminal-only (caplog, house pattern)
# ---------------------------------------------------------------------------


def test_erro_envelope_estagio_desconhecido(caplog) -> None:
    with caplog.at_level(logging.ERROR):
        resp = client.post(
            "/api/tracker/candidaturas",
            json={**CRIACAO_MINIMA, "estagio_id": 999},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == ["Estágio 999 não encontrado."]
    assert "estagios row miss for id=999" in caplog.text  # raw → terminal ONLY
    # No partial row: nothing persisted for the failed create.
    resumo = client.get("/api/tracker/resumo").json()
    assert resumo["contadores"]["ativas"] == 0


# ---------------------------------------------------------------------------
# (f) D-04 posture: no destructive path ships in the tracker routes
# ---------------------------------------------------------------------------


def test_rotas_tracker_nao_tem_caminho_destrutivo() -> None:
    metodos_por_rota: dict[str, set[str]] = {}
    for rota in _rotas_api():
        if rota.path.startswith("/api/tracker"):
            metodos_por_rota.setdefault(rota.path, set()).update(rota.methods)
    assert metodos_por_rota, "rotas do tracker esperadas"
    for path, metodos in metodos_por_rota.items():
        assert "DELETE" not in metodos, path  # D-04: só arquivar, nunca apagar
