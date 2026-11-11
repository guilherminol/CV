"""Route tests for the complete /api/tracker surface — the 200-envelope
contract of plans 07-01 + 07-02, 100% OFFLINE (D-15 — the tracker has no LLM;
the suite needs no marker opt-out).

Pinned here: the tracker router registered BEFORE the SPA mount (research
Pitfall 5) with PUT /estagios/reordenar BEFORE the {estagio_id} route; every
handler a plain sync `def` (threadpool dispatch contract) across the WHOLE
surface; the resumo ZERO state on a fresh DB (auto-migration via the yield
dependency); the create roundtrip; 422 vectors (unknown key — extra=forbid;
literal misses; bounds; bad date patterns; calendar-invalid dates — CR-02); not-found envelopes for the
edit/move/events/followups paths (200 + status erro + PT-BR line, raw detail
terminal-only via caplog — NEVER a bare 404); the stage-removal blocking
envelope; reorder persistence; the export pins (base64 transport,
backend-generated filename, UTF-8 BOM, formula sanitization end-to-end);
and the D-04 closure pins — no candidatura path with the removal method;
estagios removal is the ONLY DELETE in the surface.

Isolation seam (RESEARCH Wave-0): the fixture monkeypatches the
app.tracker.db module constant TRACKER_DB at tmp_path — per-test fresh file,
NEVER the real data/ directory.
"""

import base64
import inspect
import json
import logging
from datetime import date

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
    """Sync-handler pin extended over ALL tracker routes (07-02): plain def →
    Starlette threadpool; the sqlite3 connection is opened on the serving
    thread (RESEARCH Pattern 1)."""
    rotas = [rota for rota in _rotas_api() if rota.path.startswith("/api/tracker")]
    assert len(rotas) >= 11, "the complete 07-02 surface expected"
    for rota in rotas:
        assert inspect.iscoroutinefunction(rota.endpoint) is False, rota.path


def test_reordenar_registrada_antes_da_rota_parametrizada() -> None:
    """Route-matching order pin: the literal PUT /estagios/reordenar path is
    registered BEFORE PUT /estagios/{estagio_id}."""
    caminhos = [rota.path for rota in _rotas_api()]
    assert (
        caminhos.index("/api/tracker/estagios/reordenar")
        < caminhos.index("/api/tracker/estagios/{estagio_id}")
    )


def test_router_registered_before_spa_mount() -> None:
    entries = list(_iter_api_routes())
    mount_positions = [
        pos for path, endpoint, pos in entries if endpoint is None and path in ("", "/")
    ]
    assert mount_positions, "SPA mount expected at / (frontend/dist guard, Pitfall 5)"
    caminhos_tracker = (
        "/api/tracker/resumo",
        "/api/tracker/candidaturas",
        "/api/tracker/candidaturas/{candidatura_id}",
        "/api/tracker/candidaturas/{candidatura_id}/mover",
        "/api/tracker/candidaturas/{candidatura_id}/eventos",
        "/api/tracker/candidaturas/{candidatura_id}/followups/executar",
        "/api/tracker/candidaturas/{candidatura_id}/followups/adiar",
        "/api/tracker/estagios",
        "/api/tracker/estagios/reordenar",
        "/api/tracker/estagios/{estagio_id}",
        "/api/tracker/exportar",
    )
    for path in caminhos_tracker:
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
# (f) D-04 posture: archive-only — the ONLY DELETE in the surface is estagios
# ---------------------------------------------------------------------------


def test_rotas_tracker_nao_tem_caminho_destrutivo() -> None:
    """D-04 refined (07-02): the ONLY DELETE in the tracker surface is
    estagios removal (service-blocked while referenced). Pinned together
    with test_no_candidatura_removal_route below."""
    deletes = [
        rota.path
        for rota in _rotas_api()
        if rota.path.startswith("/api/tracker") and "DELETE" in (rota.methods or set())
    ]
    assert deletes == ["/api/tracker/estagios/{estagio_id}"]


def test_no_candidatura_removal_route() -> None:
    """D-04 closure pin (plan 07-02): iterate app.routes and assert NO
    APIRoute combines a candidatura path with the removal method —
    archive-only is the closure policy; exclusion is deferred."""
    for rota in _rotas_api():
        if "/candidaturas" in rota.path:
            assert "DELETE" not in (rota.methods or set()), rota.path


# ---------------------------------------------------------------------------
# (g) 422 vectors — validation happens before any SQL runs (T-07-07)
# ---------------------------------------------------------------------------


def test_422_chave_desconhecida_na_edicao() -> None:
    resp = client.put(
        "/api/tracker/candidaturas/1", json={"cargo": "Dev", "extra": 1}
    )
    assert resp.status_code == 422


def test_422_modalidade_fora_do_literal() -> None:
    resp = client.put(
        "/api/tracker/candidaturas/1", json={"modalidade": "presencial_remoto"}
    )
    assert resp.status_code == 422


def test_422_jd_texto_acima_do_limite() -> None:
    resp = client.put("/api/tracker/candidaturas/1", json={"jd_texto": "x" * 20001})
    assert resp.status_code == 422


def test_422_tipo_fora_do_literal_evento() -> None:
    resp = client.post(
        "/api/tracker/candidaturas/1/eventos",
        json={"tipo": "ligacao", "data_evento": "2026-01-05"},
    )
    assert resp.status_code == 422


def test_422_data_evento_fora_do_padrao_iso() -> None:
    resp = client.post(
        "/api/tracker/candidaturas/1/eventos",
        json={"tipo": "retorno", "data_evento": "05/01/2026"},
    )
    assert resp.status_code == 422


def test_422_mover_sem_estagio_id() -> None:
    resp = client.post("/api/tracker/candidaturas/1/mover", json={})
    assert resp.status_code == 422  # estagio_id required in the strict body


def test_422_reordenar_lista_vazia() -> None:
    resp = client.put("/api/tracker/estagios/reordenar", json={"ordens": []})
    assert resp.status_code == 422


def test_422_formato_fora_do_literal_exportar() -> None:
    resp = client.post("/api/tracker/exportar", json={"formato": "xml"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# (g2) CR-02 vectors: calendar-INVALID dates (regex-VALID) are rejected 422 —
# never an unhandled ValueError (HTTP 500) in derivar_campos/adiar_followup
# and never a poisoned persisted row breaking GET /resumo permanently
# ---------------------------------------------------------------------------


def test_422_prazo_retorno_calendario_invalido_na_criacao() -> None:
    """CR-02: '2026-02-30' matches _PADRAO_DATA but is not a real date —
    rejected at the DTO boundary as 422, NOT an HTTP 500 from the unguarded
    date.fromisoformat projection."""
    resp = client.post(
        "/api/tracker/candidaturas",
        json={**CRIACAO_MINIMA, "prazo_retorno": "2026-02-30"},
    )
    assert resp.status_code == 422
    # Nothing persisted for the rejected create.
    resumo = client.get("/api/tracker/resumo").json()
    assert resumo["status"] == "ok"
    assert resumo["contadores"]["ativas"] == 0


def test_422_data_evento_calendario_invalido_no_registro() -> None:
    """CR-02: '2026-13-05' is regex-valid and month-impossible — rejected
    422. Before the fix it was accepted (200 ok), poisoning the eventos table
    and breaking GET /resumo with HTTP 500 on every later call."""
    resp = client.post("/api/tracker/candidaturas", json=CRIACAO_MINIMA)
    assert resp.status_code == 200
    resp = client.post(
        "/api/tracker/candidaturas/1/eventos",
        json={"tipo": "retorno", "data_evento": "2026-13-05"},
    )
    assert resp.status_code == 422
    # The poisoned row never reached storage — resumo stays healthy.
    resumo = client.get("/api/tracker/resumo")
    assert resumo.status_code == 200
    assert resumo.json()["status"] == "ok"


def test_422_nova_data_calendario_invalida_no_adiar() -> None:
    """CR-02: the adiar target '2027-02-30' is day-impossible — rejected 422
    at the DTO boundary, not a ValueError/HTTP 500 inside adiar_followup."""
    resp = client.post("/api/tracker/candidaturas", json=CRIACAO_MINIMA)
    assert resp.status_code == 200
    resp = client.post(
        "/api/tracker/candidaturas/1/followups/adiar",
        json={"nova_data": "2027-02-30"},
    )
    assert resp.status_code == 422


def test_422_datas_calendario_invalidas_na_edicao() -> None:
    """CR-02: the edit DTO's date fields carry the same calendar-validity
    gate as the create DTO (one wire contract, both request models)."""
    resp = client.put(
        "/api/tracker/candidaturas/1",
        json={"data_aplicacao": "2026-02-30"},
    )
    assert resp.status_code == 422
    resp = client.put(
        "/api/tracker/candidaturas/1",
        json={"prazo_retorno": "2027-04-31"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# (h) Not-found flows answer the erro envelope — NEVER a bare 404
# ---------------------------------------------------------------------------


def test_nao_encontrado_envelope_mover(caplog) -> None:
    with caplog.at_level(logging.ERROR):
        resp = client.post(
            "/api/tracker/candidaturas/999/mover", json={"estagio_id": 1}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == ["Candidatura 999 não encontrada."]
    assert "candidaturas row miss for id=999" in caplog.text  # raw → terminal ONLY


def test_nao_encontrado_envelope_edicao() -> None:
    resp = client.put("/api/tracker/candidaturas/999", json={"cargo": "x"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "erro", "erros": ["Candidatura 999 não encontrada."]}


def test_nao_encontrado_envelope_eventos() -> None:
    resp = client.post(
        "/api/tracker/candidaturas/999/eventos",
        json={"tipo": "retorno", "data_evento": "2026-01-05"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "erro", "erros": ["Candidatura 999 não encontrada."]}


def test_nao_encontrado_envelope_followups() -> None:
    resp = client.post("/api/tracker/candidaturas/999/followups/executar", json={})
    assert resp.status_code == 200
    assert resp.json()["erros"] == ["Candidatura 999 não encontrada."]


def test_nao_encontrado_envelope_remover_estagio() -> None:
    resp = client.delete("/api/tracker/estagios/999")
    assert resp.status_code == 200
    assert resp.json() == {"status": "erro", "erros": ["Estágio 999 não encontrado."]}


# ---------------------------------------------------------------------------
# (i) Stage vocabulary management via the API (D-05)
# ---------------------------------------------------------------------------


def test_estagio_delete_bloqueado_quando_referenciado(caplog) -> None:
    resp = client.post("/api/tracker/estagios", json={"nome": "Triagem"})
    estagio_id = resp.json()["estagio"]["id"]
    client.post("/api/tracker/candidaturas", json=CRIACAO_MINIMA)  # default stage 1
    client.post("/api/tracker/candidaturas/1/mover", json={"estagio_id": estagio_id})
    with caplog.at_level(logging.ERROR):
        resp = client.delete(f"/api/tracker/estagios/{estagio_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == ["Não é possível remover: há candidaturas neste estágio."]
    # The referenced stage survives (no cascade ever runs — D-05/D-04).
    nomes = [e["nome"] for e in client.get("/api/tracker/estagios").json()["estagios"]]
    assert "Triagem" in nomes
    assert "referenced by 1 candidatura" in caplog.text  # raw → terminal ONLY


def test_estagio_delete_livre_ok() -> None:
    resp = client.post("/api/tracker/estagios", json={"nome": "Triagem"})
    estagio_id = resp.json()["estagio"]["id"]
    resp = client.delete(f"/api/tracker/estagios/{estagio_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["removido"] == estagio_id
    nomes = [e["nome"] for e in client.get("/api/tracker/estagios").json()["estagios"]]
    assert "Triagem" not in nomes


def test_renomear_estagio_via_api() -> None:
    resp = client.put("/api/tracker/estagios/1", json={"nome": "Explorando"})
    assert resp.status_code == 200
    assert resp.json()["estagio"]["nome"] == "Explorando"


def test_reordenar_estagios_persiste_ordem() -> None:
    resp = client.put(
        "/api/tracker/estagios/reordenar", json={"ordens": [3, 1, 2, 4, 5]}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert [e["id"] for e in body["estagios"]] == [3, 1, 2, 4, 5]
    assert [e["ordem"] for e in body["estagios"]] == [1, 2, 3, 4, 5]
    # GET reflects the persisted order (React Query invalidate target).
    ordem = [e["id"] for e in client.get("/api/tracker/estagios").json()["estagios"]]
    assert ordem == [3, 1, 2, 4, 5]


def test_reordenar_incompleto_envelope_erro() -> None:
    resp = client.put("/api/tracker/estagios/reordenar", json={"ordens": [2, 1]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert "todos os estágios" in body["erros"][0]


# ---------------------------------------------------------------------------
# (j) Full lifecycle through the API (edit → move → events → follow-ups)
# ---------------------------------------------------------------------------


def test_ciclo_editar_mover_evento_followup_via_api() -> None:
    client.post("/api/tracker/candidaturas", json=CRIACAO_MINIMA)

    # Edit + archive toggle (A2 flag pin on the wire).
    resp = client.put(
        "/api/tracker/candidaturas/1",
        json={"cargo": "Data Engineer", "arquivada": True},
    )
    candidatura = resp.json()["candidatura"]
    assert candidatura["arquivada"] is True
    assert candidatura["arquivada_em"] == date.today().isoformat()
    resp = client.put("/api/tracker/candidaturas/1", json={"arquivada": False})
    assert resp.json()["candidatura"]["arquivada"] is False

    # Move to another stage — estagio_nome joins server-side (D-09).
    resp = client.post("/api/tracker/candidaturas/1/mover", json={"estagio_id": 3})
    assert resp.json()["candidatura"]["estagio_nome"] == "Entrevista"

    # Events: one envio (feeds the counter) + one future followup (pendente).
    resp = client.post(
        "/api/tracker/candidaturas/1/eventos",
        json={"tipo": "envio_curriculo", "data_evento": "2026-01-02", "idioma": "pt-BR"},
    )
    assert resp.json()["evento"]["tipo"] == "envio_curriculo"
    resp = client.post(
        "/api/tracker/candidaturas/1/eventos",
        json={"tipo": "followup", "data_evento": "2099-01-05", "observacao": "cobrar"},
    )
    assert resp.json()["status"] == "ok"
    resumo = client.get("/api/tracker/resumo").json()
    assert resumo["contadores"]["enviados"] == 1
    assert resumo["candidaturas"][0]["followup_pendente"] is True

    # Follow-up lifecycle: executar clears pendente; adiar restores it.
    resp = client.post(
        "/api/tracker/candidaturas/1/followups/executar", json={"observacao": "ligado"}
    )
    assert resp.json()["candidatura"]["followup_pendente"] is False
    resp = client.post(
        "/api/tracker/candidaturas/1/followups/adiar", json={"nova_data": "2099-02-01"}
    )
    assert resp.json()["candidatura"]["followup_pendente"] is True


# ---------------------------------------------------------------------------
# (k) Export transport — base64 + backend-generated filename (S8/D-03/T-07-02)
# ---------------------------------------------------------------------------


def test_exportar_json_base64_tres_tabelas() -> None:
    client.post("/api/tracker/candidaturas", json=CRIACAO_MINIMA)
    resp = client.post("/api/tracker/exportar", json={"formato": "json"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["arquivo"] == "json"
    assert body["filename"] == f"tracker-{date.today().isoformat()}.json"
    carga = json.loads(base64.b64decode(body["conteudo_base64"]).decode("utf-8"))
    assert set(carga) == {"estagios", "candidaturas", "exportado_em"}
    assert carga["candidaturas"][0]["empresa"] == CRIACAO_MINIMA["empresa"]
    assert len(carga["estagios"]) == 5  # v1 seed set


def test_exportar_csv_bom_filename_e_sanitizacao() -> None:
    client.post(
        "/api/tracker/candidaturas", json={"empresa": "=SOMA(A1)", "cargo": "Dev"}
    )
    resp = client.post("/api/tracker/exportar", json={"formato": "csv"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["arquivo"] == "csv"
    assert body["filename"] == f"tracker-{date.today().isoformat()}.csv"
    bytes_csv = base64.b64decode(body["conteudo_base64"])
    assert bytes_csv.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM leads the bytes
    texto = bytes_csv.decode("utf-8-sig")
    assert ";" in texto  # A6 delimiter pin
    assert "'=SOMA(A1)" in texto  # formula-leading cell sanitized end-to-end
