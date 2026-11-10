"""Tracker routes — GET /api/tracker/resumo + POST /api/tracker/candidaturas.

House posture (routes/linkedin.py precedent): every handler a plain
synchronous `def` (Starlette threadpool dispatch — the sqlite3 connection is
opened on the serving thread by the yield dependency below, RESEARCH
Pattern 1, never module-global and never shared across threads); every
failure answers HTTP 200 {"status": "erro", "erros": [PT-BR lines]} with the
raw detail logged via logger.error ONLY (terminal); validation failures stay
FastAPI 422s (extra=forbid DTOs); no destructive path ships here (D-04 —
the only mutation is create).

mirrors: frontend/src/api/client.ts tracker section — change BOTH together;
tsc -b is the drift gate.
"""

import logging
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends

from app.config import TRACKER_FOLLOWUP_SUGGEST_DAYS
from app.tracker.db import aplicar_migracoes, conectar
from app.tracker.models import CandidaturaCriacaoRequest
from app.tracker.service import TrackerErro, criar_candidatura, obter_resumo

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
