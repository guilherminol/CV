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

Follow-up semantics are DATA-INFERRED (Pattern 4b, pin A3): pending means a
followup event dated after hoje; vencido means one dated before hoje; no
`executada` flag column exists anywhere. executar/adiar select the earliest
followup with data_evento >= hoje — a followup dated TODAY is not past, so it
stays executable/postponable on the day it comes due (the UI flags themselves
stay strict: pendente only future, vencido only past).

SQL posture (T-07-01): every statement is a static string with `?`
placeholders — values NEVER interpolated into statement text. The one place
an identifier is composed (the edit SET clause) draws only from a
compile-time constant field tuple; every VALUE rides a `?` parameter.
"""

import csv
import io
import json
import sqlite3
from datetime import date
from typing import get_args

from app.config import TRACKER_FOLLOWUP_SUGGEST_DAYS
from app.tracker.models import (
    CandidaturaCriacaoRequest,
    CandidaturaEdicaoRequest,
    EstagioCriacaoRequest,
    EstagioEdicaoRequest,
    EventoRegistroRequest,
    FollowupAdiamentoRequest,
    FollowupExecucaoRequest,
    TipoEvento,
)

# Single source of truth for the event-type vocabulary: the DTO Literal
# (07-01 drift lock). No literal duplicated here.
TIPOS_EVENTO = frozenset(get_args(TipoEvento))


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


def _exigir_candidatura(conn: sqlite3.Connection, candidatura_id: int) -> None:
    """Loud not-found gate for every candidatura-scoped mutation — unknown
    ids flow through TrackerErro to the erro envelope, NEVER a bare 404."""
    existe = conn.execute(
        "SELECT id FROM candidaturas WHERE id = ?",
        (candidatura_id,),
    ).fetchone()
    if existe is None:
        raise TrackerErro(
            f"Candidatura {candidatura_id} não encontrada.",
            f"candidaturas row miss for id={candidatura_id}",
        )


def _exigir_estagio(conn: sqlite3.Connection, estagio_id: int) -> None:
    existe = conn.execute(
        "SELECT id FROM estagios WHERE id = ?",
        (estagio_id,),
    ).fetchone()
    if existe is None:
        raise TrackerErro(
            f"Estágio {estagio_id} não encontrado.",
            f"estagios row miss for id={estagio_id}",
        )


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


# Editable candidatura columns — compile-time constants ONLY. The edit SET
# clause below composes identifiers from this tuple; every VALUE rides a `?`.
_CAMPOS_EDICAO = (
    "empresa",
    "cargo",
    "fonte",
    "link_vaga",
    "faixa_salarial",
    "contato_recrutador",
    "estagio_id",
    "data_aplicacao",
    "prazo_retorno",
    "notas",
    "jd_texto",
    "modalidade",
)


def editar_candidatura(
    conn: sqlite3.Connection,
    candidatura_id: int,
    dados: CandidaturaEdicaoRequest,
    *,
    hoje: date | None = None,
) -> dict:
    """Update ONLY the provided optional fields (None = untouched).

    Archive semantics (A2 pin): arquivada=True stamps arquivada_em with
    today's ISO date; arquivada=False clears it — the flag survives
    user-edited stage vocabularies (D-05). Unknown id raises TrackerErro
    (erro envelope, never a bare 404). Returns the refreshed wire projection.
    """
    hoje = hoje or date.today()
    _exigir_candidatura(conn, candidatura_id)
    if dados.estagio_id is not None:
        _resolver_estagio(conn, dados.estagio_id)

    atribuicoes: list[str] = []
    valores: list[object] = []
    for campo in _CAMPOS_EDICAO:  # identifiers from the constant tuple only
        valor = getattr(dados, campo)
        if valor is not None:
            atribuicoes.append(f"{campo} = ?")
            valores.append(valor)
    if dados.arquivada is True:
        atribuicoes.append("arquivada = 1")
        atribuicoes.append("arquivada_em = ?")
        valores.append(hoje.isoformat())
    elif dados.arquivada is False:
        atribuicoes.append("arquivada = 0")
        atribuicoes.append("arquivada_em = NULL")
    if not atribuicoes:
        raise TrackerErro(
            "Informe ao menos um campo para editar.",
            f"empty CandidaturaEdicaoRequest for candidatura_id={candidatura_id}",
        )
    conn.execute(
        # Identifiers come ONLY from _CAMPOS_EDICAO + the fixed archive
        # literals above — never user data; every value is a bound parameter.
        f"UPDATE candidaturas SET {', '.join(atribuicoes)} WHERE id = ?",
        (*valores, candidatura_id),
    )
    return _candidatura_por_id(conn, candidatura_id, hoje=hoje)


def mover_estagio(
    conn: sqlite3.Connection,
    candidatura_id: int,
    novo_estagio_id: int,
    *,
    hoje: date | None = None,
) -> dict:
    """Move one candidatura to another stage — loud TrackerErro on an unknown
    stage (D-05) or unknown candidatura."""
    hoje = hoje or date.today()
    _exigir_candidatura(conn, candidatura_id)
    estagio_id = _resolver_estagio(conn, novo_estagio_id)
    conn.execute(
        "UPDATE candidaturas SET estagio_id = ? WHERE id = ?",
        (estagio_id, candidatura_id),
    )
    return _candidatura_por_id(conn, candidatura_id, hoje=hoje)


def adicionar_evento(
    conn: sqlite3.Connection,
    candidatura_id: int,
    dados: EventoRegistroRequest,
) -> dict:
    """Register one metadata-only event (D-08): exactly the five columns
    (candidatura_id, tipo, data_evento, idioma, observacao) — the schema has
    NO content column by design (resume text stays ephemeral). The tipo
    literal is re-checked loudly even though the DTO constrains it."""
    _exigir_candidatura(conn, candidatura_id)
    if dados.tipo not in TIPOS_EVENTO:
        raise TrackerErro(
            "Tipo de evento desconhecido.",
            f"tipo literal miss: {dados.tipo!r}",
        )
    cursor = conn.execute(
        """
        INSERT INTO eventos (candidatura_id, tipo, data_evento, idioma, observacao)
        VALUES (?, ?, ?, ?, ?)
        """,
        (candidatura_id, dados.tipo, dados.data_evento, dados.idioma, dados.observacao),
    )
    row = conn.execute(
        "SELECT * FROM eventos WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)


def _followup_nao_passado(
    conn: sqlite3.Connection, candidatura_id: int, hoje: date
) -> sqlite3.Row | None:
    """Earliest followup of the candidatura with data_evento >= hoje (ISO
    date-only strings compare lexicographically == chronologically). Includes
    TODAY so a followup executed today can still be postponed today (Pattern
    4b comment on this module) — the derived pendente/vencido flags stay
    strict (future-only / past-only)."""
    return conn.execute(
        """
        SELECT * FROM eventos
        WHERE candidatura_id = ? AND tipo = ? AND data_evento >= ?
        ORDER BY data_evento, id
        LIMIT 1
        """,
        (candidatura_id, "followup", hoje.isoformat()),
    ).fetchone()


def executar_followup(
    conn: sqlite3.Connection,
    candidatura_id: int,
    dados: FollowupExecucaoRequest,
    *,
    hoje: date | None = None,
) -> dict:
    """Register that the pending follow-up was executed (D-10): re-date the
    row to hoje and append the note — it becomes a normal dated event. NO
    `executada` flag column exists (A3): data-inference cannot drift from
    reality. Raises TrackerErro when no pending follow-up exists."""
    hoje = hoje or date.today()
    _exigir_candidatura(conn, candidatura_id)
    pendente = _followup_nao_passado(conn, candidatura_id, hoje)
    if pendente is None:
        raise TrackerErro(
            "Nenhum follow-up pendente para registrar.",
            f"no pending (future) followup for candidatura_id={candidatura_id} "
            f"at hoje={hoje.isoformat()}",
        )
    observacao = pendente["observacao"]
    if dados.observacao:
        observacao = (
            f"{observacao}\n{dados.observacao}" if observacao else dados.observacao
        )
    conn.execute(
        "UPDATE eventos SET data_evento = ?, observacao = ? WHERE id = ?",
        (hoje.isoformat(), observacao, pendente["id"]),
    )
    return _candidatura_por_id(conn, candidatura_id, hoje=hoje)


def adiar_followup(
    conn: sqlite3.Connection,
    candidatura_id: int,
    dados: FollowupAdiamentoRequest,
    *,
    hoje: date | None = None,
) -> dict:
    """Postpone the pending follow-up to nova_data (D-11) — nova_data must
    remain STRICTLY after hoje; past/today targets raise TrackerErro."""
    hoje = hoje or date.today()
    _exigir_candidatura(conn, candidatura_id)
    pendente = _followup_nao_passado(conn, candidatura_id, hoje)
    if pendente is None:
        raise TrackerErro(
            "Nenhum follow-up pendente para adiar.",
            f"no pending followup to postpone for candidatura_id={candidatura_id} "
            f"at hoje={hoje.isoformat()}",
        )
    if date.fromisoformat(dados.nova_data) <= hoje:
        raise TrackerErro(
            "A nova data do follow-up deve ser futura (depois de hoje).",
            f"adiar target not future: nova_data={dados.nova_data} "
            f"hoje={hoje.isoformat()}",
        )
    conn.execute(
        "UPDATE eventos SET data_evento = ? WHERE id = ?",
        (dados.nova_data, pendente["id"]),
    )
    return _candidatura_por_id(conn, candidatura_id, hoje=hoje)


# --- Stage vocabulary management (D-05) -------------------------------------


def listar_estagios(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(row)
        for row in conn.execute(
            "SELECT id, nome, ordem FROM estagios ORDER BY ordem"
        ).fetchall()
    ]


def criar_estagio(conn: sqlite3.Connection, dados: EstagioCriacaoRequest) -> dict:
    """Append one stage at the end of the board (ordem = max + 1)."""
    maior = conn.execute("SELECT COALESCE(MAX(ordem), 0) FROM estagios").fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO estagios (nome, ordem) VALUES (?, ?)",
        (dados.nome, int(maior) + 1),
    )
    row = conn.execute(
        "SELECT id, nome, ordem FROM estagios WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row)


def renomear_estagio(
    conn: sqlite3.Connection, estagio_id: int, dados: EstagioEdicaoRequest
) -> dict:
    """Rename one stage — the personal vocabulary stays editable (D-05)."""
    _exigir_estagio(conn, estagio_id)
    if dados.nome is None:
        raise TrackerErro(
            "Informe o novo nome do estágio.",
            f"rename without nome for estagio_id={estagio_id}",
        )
    conn.execute(
        "UPDATE estagios SET nome = ? WHERE id = ?",
        (dados.nome, estagio_id),
    )
    row = conn.execute(
        "SELECT id, nome, ordem FROM estagios WHERE id = ?",
        (estagio_id,),
    ).fetchone()
    return dict(row)


def reordenar_estagios(conn: sqlite3.Connection, ordens: list[int]) -> list[dict]:
    """Reorder the whole board: the id list assigns ordem 1..n in the given
    order, inside ONE transaction. The list must cover exactly the existing
    stages (contiguity by construction). A temporary negative-ordem pass
    sidesteps the UNIQUE(ordem) constraint while positions swap."""
    ids_existentes = {
        int(row["id"]) for row in conn.execute("SELECT id FROM estagios").fetchall()
    }
    if len(ordens) != len(ids_existentes) or set(ordens) != ids_existentes:
        raise TrackerErro(
            "A reordenação deve incluir exatamente todos os estágios, sem repetir.",
            f"reorder list mismatch: ordens={ordens} "
            f"existentes={sorted(ids_existentes)}",
        )
    with conn:
        conn.execute("UPDATE estagios SET ordem = -ordem")
        for posicao, estagio_id in enumerate(ordens, start=1):
            conn.execute(
                "UPDATE estagios SET ordem = ? WHERE id = ?",
                (posicao, estagio_id),
            )
    return listar_estagios(conn)


def remover_estagio(conn: sqlite3.Connection, estagio_id: int) -> dict:
    """Remove one stage — REFUSED while any candidatura references it.

    Pitfall-2 posture: the FK pragma alone would only raise IntegrityError;
    the explicit reference COUNT is what produces the friendly PT-BR erro
    envelope, and NO cascade ever touches candidaturas (D-05 + the no-
    destructive spirit of D-04). Removing a free stage succeeds and the
    remaining ordem values are renumbered contiguously 1..n."""
    _exigir_estagio(conn, estagio_id)
    referencias = conn.execute(
        "SELECT COUNT(*) FROM candidaturas WHERE estagio_id = ?",
        (estagio_id,),
    ).fetchone()[0]
    if referencias:
        raise TrackerErro(
            "Não é possível remover: há candidaturas neste estágio.",
            f"estagio_id={estagio_id} referenced by {referencias} candidatura(s) "
            "— removal blocked (D-04/D-05)",
        )
    with conn:
        conn.execute("DELETE FROM estagios WHERE id = ?", (estagio_id,))
        # Remaining order is read BEFORE the negation pass — after the flip the
        # temporary ordem values are negative and would sort reversed.
        restantes = conn.execute(
            "SELECT id FROM estagios ORDER BY ordem"
        ).fetchall()
        conn.execute("UPDATE estagios SET ordem = -ordem")
        for posicao, row in enumerate(restantes, start=1):
            conn.execute(
                "UPDATE estagios SET ordem = ? WHERE id = ?",
                (posicao, row["id"]),
            )
    return {"removido": estagio_id, "estagios": listar_estagios(conn)}


# --- Export builders (D-03) --------------------------------------------------


def exportar_json(conn: sqlite3.Connection, *, hoje: date | None = None) -> bytes:
    """Full dump of the three tables, utf-8 bytes (D-03). Restores/import
    stay deferred — the payload carries the rows exactly as stored, eventos
    attached per candidatura."""
    hoje = hoje or date.today()
    candidaturas = []
    for row in conn.execute(
        "SELECT * FROM candidaturas ORDER BY id"
    ).fetchall():
        cand = dict(row)
        cand["eventos"] = [
            dict(evento)
            for evento in conn.execute(
                "SELECT * FROM eventos WHERE candidatura_id = ? ORDER BY data_evento, id",
                (cand["id"],),
            ).fetchall()
        ]
        candidaturas.append(cand)
    carga = {
        "estagios": listar_estagios(conn),
        "candidaturas": candidaturas,
        "exportado_em": hoje.isoformat(),
    }
    return json.dumps(carga, ensure_ascii=False).encode("utf-8")


_CSV_COLUNAS = (
    "empresa",
    "cargo",
    "fonte",
    "link_vaga",
    "estagio",
    "data_aplicacao",
    "prazo_retorno",
    "modalidade",
    "faixa_salarial",
    "contato_recrutador",
    "arquivada",
    "envios",
    "entrevistas",
)


def _sanitizar_celula(valor: object) -> str:
    """CSV formula-injection mitigation (T-07-02): cells whose FIRST char is
    one of = + - @ get an apostrophe prefix BEFORE csv.writer serialization —
    the export's consumers open it in Excel."""
    texto = "" if valor is None else str(valor)
    if texto[:1] in ("=", "+", "-", "@"):
        return "'" + texto
    return texto


def exportar_csv(conn: sqlite3.Connection) -> bytes:
    """One row per candidatura for the PT-BR spreadsheet (A6 pin): ';'
    delimiter, utf-8-sig so the EF BB BF BOM leads the bytes and Excel
    detects UTF-8, every data cell formula-sanitized (T-07-02). Ordered by
    prazo proximity with NULL-prazo last (the D-09 overview order)."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(_CSV_COLUNAS)
    nomes = _nomes_estagios(conn)
    rows = conn.execute(
        """
        SELECT * FROM candidaturas
        ORDER BY CASE WHEN prazo_retorno IS NULL THEN 1 ELSE 0 END, prazo_retorno
        """
    ).fetchall()
    for row in rows:
        cand = dict(row)
        contagens = {"envio_curriculo": 0, "entrevista": 0}
        for evento in conn.execute(
            "SELECT tipo FROM eventos WHERE candidatura_id = ?",
            (cand["id"],),
        ).fetchall():
            if evento["tipo"] in contagens:
                contagens[evento["tipo"]] += 1
        linha = {
            "empresa": cand["empresa"],
            "cargo": cand["cargo"],
            "fonte": cand["fonte"],
            "link_vaga": cand["link_vaga"],
            "estagio": nomes.get(cand["estagio_id"]),
            "data_aplicacao": cand["data_aplicacao"],
            "prazo_retorno": cand["prazo_retorno"],
            "modalidade": cand["modalidade"],
            "faixa_salarial": cand["faixa_salarial"],
            "contato_recrutador": cand["contato_recrutador"],
            "arquivada": "sim" if cand["arquivada"] else "não",
            "envios": contagens["envio_curriculo"],
            "entrevistas": contagens["entrevista"],
        }
        writer.writerow([_sanitizar_celula(linha[coluna]) for coluna in _CSV_COLUNAS])
    return buffer.getvalue().encode("utf-8-sig")


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


def _candidatura_por_id(
    conn: sqlite3.Connection,
    candidatura_id: int,
    *,
    hoje: date,
    limiar_followup: int = TRACKER_FOLLOWUP_SUGGEST_DAYS,
) -> dict:
    """One candidatura as the SAME wire projection as the resumo rows —
    one wire contract for every candidatura-carrying response."""
    row = conn.execute(
        "SELECT * FROM candidaturas WHERE id = ?",
        (candidatura_id,),
    ).fetchone()
    eventos = [
        dict(evento)
        for evento in conn.execute(
            "SELECT * FROM eventos WHERE candidatura_id = ? ORDER BY data_evento, id",
            (candidatura_id,),
        ).fetchall()
    ]
    return _derivados(
        dict(row), eventos, _nomes_estagios(conn), hoje, limiar_followup
    )


def obter_resumo(
    conn: sqlite3.Connection,
    *,
    hoje: date | None = None,
    limiar_followup: int = TRACKER_FOLLOWUP_SUGGEST_DAYS,
) -> dict:
    """Pure projection for GET /api/tracker/resumo (D-07/D-09).

    Returns {"contadores": {enviados, entrevistas, ativas}, "candidaturas":
    [...], "estagios": [...]}. Contadores derive from PERSISTED events only —
    enviados/entrevistas count ALL such events across candidaturas regardless
    of archive status (history feeds the counts, D-04); ativas counts
    arquivada=0. Overview ordered by prazo proximity ascending with NULL-prazo
    last (D-09, server-side).
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

    estagios = listar_estagios(conn)
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


def derivar_campos(
    cand: dict, eventos: list[dict], *, hoje: date, limiar_followup: int
) -> dict:
    """PURE derived-field projection (RESEARCH Patterns 6 + 4b) — no conn,
    no mutation: returns the server-computed fields the UI never recomputes
    (D-09/D-11/D-12; date-only arithmetic, Pitfall 7).

    - dias_para_prazo: (prazo - hoje).days, None without a prazo (negative =
      vencido).
    - atrasado_prazo: dias_para_prazo < 0.
    - sugerir_followup: >= limiar days since the anchor — the latest event
      dated <= hoje, falling back to data_aplicacao then criada_em when no
      past event exists (future events are PENDING followups, not activity).
    - followup_pendente: a followup dated AFTER hoje.
    - followup_vencido: a followup dated BEFORE hoje.
    - followup_pendente_data: the next due followup's date (earliest strictly
      after hoje) — the {data} slot of the panel's pendente line; the client
      renders it verbatim and NEVER derives it (Pitfall 7: all date math
      stays server-side).
    - followup_vencido_dias: days since the most recent lapse (latest followup
      strictly before hoje) — the {X} slot of the panel's vencido line;
      server-computed like dias_para_prazo (07-03: the pinned string needs the
      delta and the client has no honest way to source "hoje").
    """
    prazo = date.fromisoformat(cand["prazo_retorno"]) if cand["prazo_retorno"] else None
    dias_para_prazo = (prazo - hoje).days if prazo else None  # negativo = vencido

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

    datas_followup_futuras = [
        date.fromisoformat(evento["data_evento"])
        for evento in eventos
        if evento["tipo"] == "followup"
        and date.fromisoformat(evento["data_evento"]) > hoje
    ]
    datas_followup_passadas = [
        date.fromisoformat(evento["data_evento"])
        for evento in eventos
        if evento["tipo"] == "followup"
        and date.fromisoformat(evento["data_evento"]) < hoje
    ]

    return {
        "dias_para_prazo": dias_para_prazo,
        "atrasado_prazo": dias_para_prazo is not None and dias_para_prazo < 0,
        "sugerir_followup": (hoje - ultimo_evento).days >= limiar_followup,
        "followup_pendente": any(
            evento["tipo"] == "followup"
            and date.fromisoformat(evento["data_evento"]) > hoje
            for evento in eventos
        ),
        "followup_vencido": any(
            evento["tipo"] == "followup"
            and date.fromisoformat(evento["data_evento"]) < hoje
            for evento in eventos
        ),
        "followup_pendente_data": (
            min(datas_followup_futuras).isoformat() if datas_followup_futuras else None
        ),
        "followup_vencido_dias": (
            (hoje - max(datas_followup_passadas)).days
            if datas_followup_passadas
            else None
        ),
    }


def _derivados(
    cand: dict,
    eventos: list[dict],
    nome_por_estagio: dict[int, str],
    hoje: date,
    limiar_followup: int,
) -> dict:
    """Wire projection: the pure derivar_campos result merged into the row,
    plus the joined stage name."""
    cand = _para_wire(cand, eventos=eventos)
    cand["estagio_nome"] = nome_por_estagio.get(cand["estagio_id"])
    cand.update(
        derivar_campos(cand, eventos, hoje=hoje, limiar_followup=limiar_followup)
    )
    return cand
