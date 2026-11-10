"""Tracker service layer — deterministic CRUD + derived projections (D-07).

All-or-nothing discipline (candidatura/pipeline.py precedent): the service
RAISES untouched on failure — the ROUTE owns the erro envelope (raw detail
to the logger only, PT-BR lines to the user; see routes/tracker.py).

Pure projection posture (profile/completeness.py precedent): obter_resumo
computes contadores/deadline deltas/badges FRESH per call from the persisted
rows — nothing cached, nothing stored (D-07 mechanical honesty:
enviados/entrevistas come from eventos rows only; ativas from the arquivada
flag). `hoje` is injectable (never datetime.now — Pitfall 7) so pytest pins
boundary vectors fully offline; all dates are date-only ISO 'YYYY-MM-DD'
strings.

SQL posture (T-07-01): every statement is a static string with `?`
placeholders — values NEVER interpolated into statement text.
"""

import sqlite3
from datetime import date

from app.config import TRACKER_FOLLOWUP_SUGGEST_DAYS
from app.tracker.models import CandidaturaCriacaoRequest


class TrackerErro(Exception):
    """Tracker domain failure — the route turns this into the erro envelope.

    raw carries the technical detail (terminal only, via logger.error);
    message_ptbr carries the single user-facing line (envelope erros list).
    """

    def __init__(self, message_ptbr: str, raw: str) -> None:
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw


def _resolver_estagio(conn: sqlite3.Connection, estagio_id: int | None) -> int:
    """Resolve the target stage loudly (D-05): explicit id must exist; None
    falls back to the FIRST stage by ordem — never a hardcoded seed id."""
    if estagio_id is None:
        row = conn.execute(
            "SELECT id FROM estagios ORDER BY ordem LIMIT 1"
        ).fetchone()
        if row is None:
            raise TrackerErro(
                "Nenhum estágio cadastrado — crie um estágio antes de registrar a candidatura.",
                "estagios table empty — no default stage to resolve",
            )
        return int(row["id"])
    existe = conn.execute(
        "SELECT id FROM estagios WHERE id = ?",
        (estagio_id,),
    ).fetchone()
    if existe is None:
        raise TrackerErro(
            f"Estágio {estagio_id} não encontrado.",
            f"estagios row miss for id={estagio_id}",
        )
    return estagio_id


def criar_candidatura(
    conn: sqlite3.Connection, dados: CandidaturaCriacaoRequest
) -> dict:
    """Insert one candidatura and return the row as a wire dict.

    Parameterized `?` placeholders ONLY (T-07-01). criada_em is date-only ISO
    from date.today() (Pitfall 7). estagio_id resolves loudly (TrackerErro on
    row miss / empty stage table).
    """
    estagio_id = _resolver_estagio(conn, dados.estagio_id)
    cursor = conn.execute(
        """
        INSERT INTO candidaturas (
            empresa, cargo, fonte, link_vaga, estagio_id, data_aplicacao,
            prazo_retorno, notas, jd_texto, faixa_salarial,
            contato_recrutador, modalidade, arquivada, arquivada_em, criada_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
        """,
        (
            dados.empresa,
            dados.cargo,
            dados.fonte,
            dados.link_vaga,
            estagio_id,
            dados.data_aplicacao,
            dados.prazo_retorno,
            dados.notas,
            dados.jd_texto,
            dados.faixa_salarial,
            dados.contato_recrutador,
            dados.modalidade,
            date.today().isoformat(),
        ),
    )
    row = conn.execute(
        "SELECT * FROM candidaturas WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    # The POST response carries the SAME projected shape as the resumo rows —
    # one wire contract (the typed client mirror types it as CandidaturaDTO).
    return _derivados(
        dict(row),
        [],
        _nomes_estagios(conn),
        date.today(),
        TRACKER_FOLLOWUP_SUGGEST_DAYS,
    )


def _para_wire(cand: dict, *, eventos: list[dict] | None = None) -> dict:
    """Row dict → wire dict: the archive flag becomes a JSON boolean."""
    cand["arquivada"] = bool(cand["arquivada"])
    if eventos is not None:
        cand["eventos"] = eventos
    return cand


def _nomes_estagios(conn: sqlite3.Connection) -> dict[int, str]:
    """estagio_id → nome lookup for the derived projection (render support)."""
    return {
        int(row["id"]): row["nome"]
        for row in conn.execute("SELECT id, nome FROM estagios").fetchall()
    }


def obter_resumo(
    conn: sqlite3.Connection,
    *,
    hoje: date | None = None,
    limiar_followup: int = TRACKER_FOLLOWUP_SUGGEST_DAYS,
) -> dict:
    """Pure projection for GET /api/tracker/resumo (D-07/D-09).

    Returns {"contadores": {enviados, entrevistas, ativas}, "candidaturas":
    [...], "estagios": [...]}. Contadores derive from PERSISTED events only —
    a candidatura created without events counts in ativas and in none of
    enviados/entrevistas. Overview ordered by prazo proximity ascending with
    NULL-prazo last (D-09, server-side).
    """
    hoje = hoje or date.today()

    enviados = conn.execute(
        "SELECT COUNT(*) FROM eventos WHERE tipo = ?",
        ("envio_curriculo",),
    ).fetchone()[0]
    entrevistas = conn.execute(
        "SELECT COUNT(*) FROM eventos WHERE tipo = ?",
        ("entrevista",),
    ).fetchone()[0]
    ativas = conn.execute(
        "SELECT COUNT(*) FROM candidaturas WHERE arquivada = 0"
    ).fetchone()[0]

    estagios = [
        dict(row)
        for row in conn.execute(
            "SELECT id, nome, ordem FROM estagios ORDER BY ordem"
        ).fetchall()
    ]
    nome_por_estagio = {estagio["id"]: estagio["nome"] for estagio in estagios}

    candidaturas = []
    rows = conn.execute(
        """
        SELECT * FROM candidaturas
        ORDER BY CASE WHEN prazo_retorno IS NULL THEN 1 ELSE 0 END, prazo_retorno
        """
    ).fetchall()
    for row in rows:
        cand = dict(row)
        eventos = [
            dict(evento)
            for evento in conn.execute(
                "SELECT * FROM eventos WHERE candidatura_id = ? ORDER BY data_evento, id",
                (cand["id"],),
            ).fetchall()
        ]
        candidaturas.append(
            _derivados(cand, eventos, nome_por_estagio, hoje, limiar_followup)
        )

    return {
        "contadores": {
            "enviados": enviados,
            "entrevistas": entrevistas,
            "ativas": ativas,
        },
        "candidaturas": candidaturas,
        "estagios": estagios,
    }


def _derivados(
    cand: dict,
    eventos: list[dict],
    nome_por_estagio: dict[int, str],
    hoje: date,
    limiar_followup: int,
) -> dict:
    """Server-computed derived fields (RESEARCH Pattern 6) — the UI never
    recomputes these (D-09/D-11/D-12; date-only arithmetic, Pitfall 7)."""
    prazo = date.fromisoformat(cand["prazo_retorno"]) if cand["prazo_retorno"] else None
    dias_para_prazo = (prazo - hoje).days if prazo else None  # negativo = vencido

    # Only NON-FUTURE events count as activity — pending followups are not
    # activity (A3 data-inferred pending; future events excluded from the anchor).
    datas_passadas = [
        date.fromisoformat(evento["data_evento"])
        for evento in eventos
        if date.fromisoformat(evento["data_evento"]) <= hoje
    ]
    if datas_passadas:
        ultimo_evento = max(datas_passadas)
    else:
        # Fallback anchor: data_aplicacao when present, else criada_em.
        ancora_iso = cand["data_aplicacao"] or cand["criada_em"]
        ultimo_evento = date.fromisoformat(ancora_iso)
    sugerir_followup = (hoje - ultimo_evento).days >= limiar_followup

    followup_pendente = any(
        evento["tipo"] == "followup"
        and date.fromisoformat(evento["data_evento"]) > hoje
        for evento in eventos
    )
    followup_vencido = any(
        evento["tipo"] == "followup"
        and date.fromisoformat(evento["data_evento"]) < hoje
        for evento in eventos
    )

    cand = _para_wire(cand, eventos=eventos)
    cand["estagio_nome"] = nome_por_estagio.get(cand["estagio_id"])
    cand["dias_para_prazo"] = dias_para_prazo
    cand["sugerir_followup"] = sugerir_followup
    cand["atrasado_prazo"] = dias_para_prazo is not None and dias_para_prazo < 0
    cand["followup_pendente"] = followup_pendente
    cand["followup_vencido"] = followup_vencido
    return cand
