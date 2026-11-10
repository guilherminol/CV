"""Tracker routes — the complete deterministic /api/tracker surface.

House posture (routes/linkedin.py precedent): every handler a plain
synchronous `def` (Starlette threadpool dispatch — the sqlite3 connection is
opened on the serving thread by the yield dependency below, RESEARCH
Pattern 1, never module-global and never shared across threads); every
failure answers HTTP 200 {"status": "erro", "erros": [PT-BR lines]} with the
raw detail logged via logger.error ONLY (terminal); validation failures stay
FastAPI 422s (extra=forbid DTOs); unknown ids flow through the erro envelope,
NEVER a bare 404. Archive is the ONLY closure path (D-04 — no route removes
candidaturas; estagios removal is the sole DELETE in the surface and it is
blocked while referenced).

Route shape pins (plan 07-02 Task 2):
- PUT /api/tracker/estagios/reordenar is registered BEFORE
  PUT /api/tracker/estagios/{estagio_id} so the literal path wins the match.
- POST /api/tracker/exportar answers the S8 house transport: backend-generated
  filename + base64 bytes in the ok envelope — never raw bytes, never a
  client-recomposed filename.

mirrors: frontend/src/api/client.ts tracker section — change BOTH together;
tsc -b is the drift gate.
"""

import base64
import logging
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.config import TRACKER_FOLLOWUP_SUGGEST_DAYS
from app.tracker.db import aplicar_migracoes, conectar
from app.tracker.models import (
    CandidaturaCriacaoRequest,
    CandidaturaEdicaoRequest,
    EstagioCriacaoRequest,
    EstagioEdicaoRequest,
    EventoRegistroRequest,
    ExportRequest,
    FollowupAdiamentoRequest,
    FollowupExecucaoRequest,
)
from app.tracker.service import (
    TrackerErro,
    adiar_followup,
    adicionar_evento,
    criar_candidatura,
    criar_estagio,
    editar_candidatura,
    executar_followup,
    exportar_csv,
    exportar_json,
    listar_estagios,
    mover_estagio,
    obter_resumo,
    remover_estagio,
    renomear_estagio,
    reordenar_estagios,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_FALHA_GENERICA = (
    "Falha na operação do rastreador — o detalhe técnico completo aparece no "
    "terminal onde o servidor está rodando."
)


def get_tracker_db():
    """Connection per request (RESEARCH Pattern 1 — the FastAPI-docs yield
    dependency): opened on THIS request's thread, committed after the handler
    succeeds, closed in finally. A fresh TRACKER_DB auto-migrates here."""
    conn = conectar()
    try:
        aplicar_migracoes(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


class MoverEstagioRequest(BaseModel):
    """Body for POST /api/tracker/candidaturas/{id}/mover — small strict
    inline model per plan 07-02 Task 2 (the service takes the plain int)."""

    model_config = ConfigDict(extra="forbid")

    estagio_id: int


class EstagioReordemRequest(BaseModel):
    """Body for PUT /api/tracker/estagios/reordenar — ALL stage ids in the
    new order (the service assigns ordem 1..n and rejects partial lists)."""

    model_config = ConfigDict(extra="forbid")

    ordens: list[int] = Field(min_length=1)


@router.get("/api/tracker/resumo")
def resumo_tracker(conn: sqlite3.Connection = Depends(get_tracker_db)) -> dict:
    """Contadores + candidaturas + estagios in one payload — sync def."""
    try:
        resultado = obter_resumo(
            conn,
            hoje=date.today(),
            limiar_followup=TRACKER_FOLLOWUP_SUGGEST_DAYS,
        )
    except sqlite3.Error as exc:
        logger.error("Falha ao obter o resumo do rastreador:\n%s", exc)  # raw → terminal
        return {"status": "erro", "erros": [_FALHA_GENERICA]}
    return {"status": "ok", **resultado}


@router.post("/api/tracker/candidaturas")
def registrar_candidatura(
    payload: CandidaturaCriacaoRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Create one candidatura (D-06 essential fields) — sync def."""
    try:
        candidatura = criar_candidatura(conn, payload)
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao registrar a candidatura:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "candidatura": candidatura}


@router.put("/api/tracker/candidaturas/{candidatura_id}")
def editar_candidatura_rota(
    candidatura_id: int,
    payload: CandidaturaEdicaoRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Edit fields / toggle the arquivada flag — archive is NOT destructive
    (D-04), so no ConfirmStrip anywhere (05-CONTEXT D-14 stays dormant)."""
    try:
        candidatura = editar_candidatura(
            conn, candidatura_id, payload, hoje=date.today()
        )
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao editar a candidatura:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "candidatura": candidatura}


@router.post("/api/tracker/candidaturas/{candidatura_id}/mover")
def mover_candidatura_rota(
    candidatura_id: int,
    payload: MoverEstagioRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Move one candidatura to another stage (kanban drop, D-14/D-05)."""
    try:
        candidatura = mover_estagio(
            conn, candidatura_id, payload.estagio_id, hoje=date.today()
        )
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao mover a candidatura:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "candidatura": candidatura}


@router.post("/api/tracker/candidaturas/{candidatura_id}/eventos")
def registrar_evento_rota(
    candidatura_id: int,
    payload: EventoRegistroRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Register one metadata-only event (D-08 — content never stored)."""
    try:
        evento = adicionar_evento(conn, candidatura_id, payload)
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao registrar o evento:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "evento": evento}


@router.post("/api/tracker/candidaturas/{candidatura_id}/followups/executar")
def executar_followup_rota(
    candidatura_id: int,
    payload: FollowupExecucaoRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Register that the pending follow-up was executed (D-10) — the response
    carries the recomputed candidatura projection (followup_pendente False)."""
    try:
        candidatura = executar_followup(
            conn, candidatura_id, payload, hoje=date.today()
        )
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao registrar o follow-up:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "candidatura": candidatura}


@router.post("/api/tracker/candidaturas/{candidatura_id}/followups/adiar")
def adiar_followup_rota(
    candidatura_id: int,
    payload: FollowupAdiamentoRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Postpone the pending follow-up to a strictly future date (D-11)."""
    try:
        candidatura = adiar_followup(conn, candidatura_id, payload, hoje=date.today())
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao adiar o follow-up:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "candidatura": candidatura}


@router.get("/api/tracker/estagios")
def listar_estagios_rota(
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """The stage vocabulary in board order (D-05)."""
    try:
        return {"status": "ok", "estagios": listar_estagios(conn)}
    except sqlite3.Error as exc:
        logger.error("Falha ao listar os estágios:\n%s", exc)  # raw → terminal
        return {"status": "erro", "erros": [_FALHA_GENERICA]}


@router.post("/api/tracker/estagios")
def criar_estagio_rota(
    payload: EstagioCriacaoRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Append one stage at the end of the board (ordem = max + 1, D-05)."""
    try:
        estagio = criar_estagio(conn, payload)
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao criar o estágio:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "estagio": estagio}


# Literal path FIRST: PUT /estagios/reordenar must win before /{estagio_id}.
@router.put("/api/tracker/estagios/reordenar")
def reordenar_estagios_rota(
    payload: EstagioReordemRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Reorder the whole board — ordens assigns ordem 1..n in the given
    order (partial lists rejected loudly, D-05)."""
    try:
        estagios = reordenar_estagios(conn, payload.ordens)
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao reordenar os estágios:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "estagios": estagios}


@router.put("/api/tracker/estagios/{estagio_id}")
def renomear_estagio_rota(
    estagio_id: int,
    payload: EstagioEdicaoRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Rename one stage — the personal vocabulary stays editable (D-05)."""
    try:
        estagio = renomear_estagio(conn, estagio_id, payload)
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao renomear o estágio:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", "estagio": estagio}


@router.delete("/api/tracker/estagios/{estagio_id}")
def remover_estagio_rota(
    estagio_id: int,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Remove one stage — the ONLY DELETE in the tracker surface, refused
    with the PT-BR erro envelope while any candidatura references it (D-05;
    the no-destructive spirit of D-04)."""
    try:
        resultado = remover_estagio(conn, estagio_id)
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao remover o estágio:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {"status": "ok", **resultado}


@router.post("/api/tracker/exportar")
def exportar_tracker_rota(
    payload: ExportRequest,
    conn: sqlite3.Connection = Depends(get_tracker_db),
) -> dict:
    """Export everything (D-03) — the S8 house transport: backend-generated
    filename + base64 bytes inside the ok envelope (routes/export.py
    precedent). Never raw bytes in the body, never a client-recomposed
    filename."""
    try:
        hoje_iso = date.today().isoformat()
        if payload.formato == "csv":
            conteudo_base64 = base64.b64encode(exportar_csv(conn)).decode("ascii")
            filename = f"tracker-{hoje_iso}.csv"
            arquivo = "csv"
        else:
            conteudo_base64 = base64.b64encode(
                exportar_json(conn, hoje=date.today())
            ).decode("ascii")
            filename = f"tracker-{hoje_iso}.json"
            arquivo = "json"
    except (TrackerErro, sqlite3.Error) as exc:
        raw = getattr(exc, "raw", str(exc))
        logger.error("Falha ao exportar o rastreador:\n%s", raw)  # raw → terminal only
        mensagem = getattr(exc, "message_ptbr", None) or _FALHA_GENERICA
        return {"status": "erro", "erros": [mensagem]}
    return {
        "status": "ok",
        "arquivo": arquivo,
        "filename": filename,
        "conteudo_base64": conteudo_base64,
    }
