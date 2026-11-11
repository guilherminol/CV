"""Service-layer vector suite for the tracker (plan 07-02, Task 1) — 100% OFFLINE.

Pins, with `hoje` injected explicitly in EVERY call (date.today() is never
used directly — Pitfall 7 determinism):
- contadores derived from persisted events only (D-07): archived candidaturas
  still feed the event counts but leave `ativas` (D-04 history honesty);
- the D-12 suggestion boundary at exactly TRACKER_FOLLOWUP_SUGGEST_DAYS=7 —
  True at 7 days since the last non-future event, False at 6; a future-dated
  followup never moves the anchor;
- dias_para_prazo boundaries: prazo == hoje → 0, prazo == hoje-1 → -1 with
  atrasado_prazo True (D-09), no prazo → None;
- overview ordering by prazo proximity with NULL-prazo last (D-09);
- follow-up lifecycle transitions WITHOUT any executada flag (Pattern 4b):
  pendente (future) → executar re-dates to hoje → adiar re-dates forward;
  past-dated → vencido; execute/postpone without a pending follow-up raise
  TrackerErro; postpone targets must stay strictly future;
- stage vocabulary management (D-05): removal BLOCKED while referenced with
  the PT-BR envelope line (no cascade ever runs), free removal keeps ordem
  contiguous 1..n, reorder persists 1..n in the given order;
- export builders (D-03/T-07-02): CSV bytes start with the UTF-8 BOM, use
  the ';' delimiter, and prefix an apostrophe on formula-leading cells;
  JSON round-trips back into the three table shapes.

Isolation seam: the fixture monkeypatches the app.tracker.db module constant
TRACKER_DB at tmp_path — per-test fresh file, NEVER the real data/ directory.
"""

import json
from datetime import date, timedelta

import pytest

import app.tracker.db as tracker_db
from app.tracker.db import aplicar_migracoes, conectar
from app.tracker.models import (
    CandidaturaCriacaoRequest,
    CandidaturaEdicaoRequest,
    EstagioCriacaoRequest,
    EstagioEdicaoRequest,
    EventoRegistroRequest,
    FollowupAdiamentoRequest,
    FollowupExecucaoRequest,
)
from app.tracker.service import (
    TrackerErro,
    adicionar_evento,
    adiar_followup,
    criar_candidatura,
    criar_estagio,
    derivar_campos,
    editar_candidatura,
    executar_followup,
    exportar_csv,
    exportar_json,
    listar_estagios,
    mover_estagio,
    obter_resumo,
    reordenar_estagios,
    remover_estagio,
    renomear_estagio,
)

HOJE = date(2026, 11, 10)
LIMIAR = 7  # TRACKER_FOLLOWUP_SUGGEST_DAYS pin (D-12) — passed EXPLICITLY


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    """Fresh migrated tracker DB per test at tmp_path — never the real data/."""
    monkeypatch.setattr(tracker_db, "TRACKER_DB", tmp_path / "tracker.db")
    c = conectar()
    aplicar_migracoes(c)
    yield c
    c.close()


def _criar(conn, **overrides) -> int:
    """Create one candidatura and return its id (first create → id 1)."""
    payload = {"empresa": "Acme", "cargo": "Dev", **overrides}
    dados = CandidaturaCriacaoRequest(**payload)
    candidatura = criar_candidatura(conn, dados)
    return int(candidatura["id"])


def _criar_evento(conn, candidatura_id: int, tipo: str, data_evento: str, **extra) -> None:
    adicionar_evento(
        conn,
        candidatura_id,
        EventoRegistroRequest(tipo=tipo, data_evento=data_evento, **extra),
    )


def _resumo(conn):
    return obter_resumo(conn, hoje=HOJE, limiar_followup=LIMIAR)


# ---------------------------------------------------------------------------
# (a) Contadores derive from persisted events only (D-07/D-04)
# ---------------------------------------------------------------------------


def test_contadores_derivam_somente_de_eventos(conn):
    candidatura_id = _criar(conn)  # no events yet
    resumo = _resumo(conn)
    assert resumo["contadores"] == {"enviados": 0, "entrevistas": 0, "ativas": 1}

    _criar_evento(
        conn,
        candidatura_id,
        "envio_curriculo",
        (HOJE - timedelta(days=2)).isoformat(),
        idioma="pt-BR",
    )
    resumo = _resumo(conn)
    assert resumo["contadores"]["enviados"] == 1
    assert resumo["contadores"]["entrevistas"] == 0
    assert resumo["candidaturas"][0]["eventos"][0]["tipo"] == "envio_curriculo"


def test_arquivada_conta_eventos_mas_nao_ativas(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "entrevista",
        (HOJE - timedelta(days=1)).isoformat(),
    )
    editar_candidatura(
        conn, candidatura_id, CandidaturaEdicaoRequest(arquivada=True), hoje=HOJE
    )
    resumo = _resumo(conn)
    # History feeds the counts regardless of archive status (D-04/D-07).
    assert resumo["contadores"]["entrevistas"] == 1
    assert resumo["contadores"]["ativas"] == 0


# ---------------------------------------------------------------------------
# (b) D-12 suggestion boundary — exactly 7 days (injected hoje)
# ---------------------------------------------------------------------------


def test_sugestao_followup_no_limiar_exato_de_7_dias(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "envio_curriculo",
        (HOJE - timedelta(days=7)).isoformat(),
    )
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["sugerir_followup"] is True  # exactly TRACKER_FOLLOWUP_SUGGEST_DAYS


def test_sugestao_followup_abaixo_do_limiar_6_dias(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "envio_curriculo",
        (HOJE - timedelta(days=6)).isoformat(),
    )
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["sugerir_followup"] is False  # one day short of the pin


def test_evento_futuro_nao_muda_ancora_da_sugestao(conn):
    candidatura_id = _criar(conn, data_aplicacao=(HOJE - timedelta(days=20)).isoformat())
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["sugerir_followup"] is True  # anchored on data_aplicacao (20 days)

    # A future-dated followup is PENDING, not activity — the anchor is intact.
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE + timedelta(days=10)).isoformat(),
        observacao="cobrar retorno",
    )
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["sugerir_followup"] is True
    assert cand["followup_pendente"] is True
    assert cand["followup_vencido"] is False


def test_derivar_campos_puro_e_limites():
    """The pure projection (no conn): fallback anchor + the 7/6-day flip."""
    cand = {"prazo_retorno": None, "data_aplicacao": None, "criada_em": "2026-11-01"}
    campos = derivar_campos(cand, [], hoje=date(2026, 11, 8), limiar_followup=7)
    assert campos["dias_para_prazo"] is None
    assert campos["atrasado_prazo"] is False
    assert campos["sugerir_followup"] is True  # 7 days since criada_em anchor
    campos = derivar_campos(cand, [], hoje=date(2026, 11, 7), limiar_followup=7)
    assert campos["sugerir_followup"] is False  # 6 days — below the pin


# ---------------------------------------------------------------------------
# (c) dias_para_prazo boundaries (D-09) + overview ordering
# ---------------------------------------------------------------------------


def test_dias_para_prazo_zero_no_dia_do_prazo(conn):
    _criar(conn, prazo_retorno=HOJE.isoformat())
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["dias_para_prazo"] == 0
    assert cand["atrasado_prazo"] is False


def test_dias_para_prazo_menos_um_e_vencido(conn):
    _criar(conn, prazo_retorno=(HOJE - timedelta(days=1)).isoformat())
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["dias_para_prazo"] == -1
    assert cand["atrasado_prazo"] is True  # vermelho highlight source (D-09)


def test_dias_para_prazo_none_sem_prazo(conn):
    _criar(conn)
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["dias_para_prazo"] is None
    assert cand["atrasado_prazo"] is False


def test_visao_geral_ordenada_por_proximidade_de_prazo(conn):
    _criar(conn, empresa="Sem Prazo")  # NULL prazo → last (D-09)
    _criar(conn, empresa="Vencida", prazo_retorno=(HOJE - timedelta(days=1)).isoformat())
    _criar(conn, empresa="Longe", prazo_retorno=(HOJE + timedelta(days=30)).isoformat())
    ordem = [c["empresa"] for c in _resumo(conn)["candidaturas"]]
    assert ordem == ["Vencida", "Longe", "Sem Prazo"]


# ---------------------------------------------------------------------------
# (d) Follow-up lifecycle — data-inferred, Pattern 4b, no executada flag
# ---------------------------------------------------------------------------


def test_followup_transicao_pendente_executar_adiar(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE + timedelta(days=3)).isoformat(),
        observacao="cobrar retorno",
    )
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["followup_pendente"] is True
    assert cand["followup_vencido"] is False

    # executar re-dates the row to hoje and appends the note (D-10).
    resultado = executar_followup(
        conn, candidatura_id, FollowupExecucaoRequest(observacao="ligado"), hoje=HOJE
    )
    assert resultado["followup_pendente"] is False
    evento = resultado["eventos"][-1]
    assert evento["tipo"] == "followup"
    assert evento["data_evento"] == HOJE.isoformat()
    assert "cobrar retorno" in evento["observacao"]
    assert "ligado" in evento["observacao"]

    # A candidatura com followup executed today is neither pendente nor vencido.
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["followup_vencido"] is False

    # adiar moves it forward again — pendente returns (D-11).
    resultado = adiar_followup(
        conn,
        candidatura_id,
        FollowupAdiamentoRequest(nova_data=(HOJE + timedelta(days=5)).isoformat()),
        hoje=HOJE,
    )
    assert resultado["followup_pendente"] is True
    assert resultado["eventos"][-1]["data_evento"] == (HOJE + timedelta(days=5)).isoformat()


def test_followup_vencido_apos_data_passada(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE - timedelta(days=2)).isoformat(),
    )
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["followup_vencido"] is True  # vermelho highlight source (D-11)
    assert cand["followup_pendente"] is False


def test_followup_pendente_data_e_vencido_dias_derivados(conn):
    """The EventosPanel strings' {data}/{X} slots come from SERVER-computed
    fields — the client renders them verbatim and never derives dates
    (Pitfall 7; 07-03: the pinned UI copy needs both slots in the payload)."""
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE - timedelta(days=3)).isoformat(),
    )
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE - timedelta(days=1)).isoformat(),
    )
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE + timedelta(days=2)).isoformat(),
    )
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["followup_pendente"] is True
    assert cand["followup_pendente_data"] == (HOJE + timedelta(days=2)).isoformat()
    assert cand["followup_vencido"] is True
    # The displayed lapse is the most recent one: 1 day since it went overdue.
    assert cand["followup_vencido_dias"] == 1


def test_followup_derivados_nulos_sem_followups(conn):
    candidatura_id = _criar(conn)
    cand = _resumo(conn)["candidaturas"][0]
    assert cand["followup_pendente_data"] is None
    assert cand["followup_vencido_dias"] is None


def test_executar_followup_sem_pendente_levanta_erro(conn):
    candidatura_id = _criar(conn)
    with pytest.raises(TrackerErro) as exc:
        executar_followup(conn, candidatura_id, FollowupExecucaoRequest(), hoje=HOJE)
    assert "Nenhum follow-up pendente" in exc.value.message_ptbr


def test_adiar_followup_para_data_passada_ou_hoje_rejeitado(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "followup",
        (HOJE + timedelta(days=3)).isoformat(),
    )
    with pytest.raises(TrackerErro) as exc:
        adiar_followup(
            conn,
            candidatura_id,
            FollowupAdiamentoRequest(nova_data=(HOJE - timedelta(days=1)).isoformat()),
            hoje=HOJE,
        )
    assert "futura" in exc.value.message_ptbr
    with pytest.raises(TrackerErro):  # hoje is NOT strictly future either
        adiar_followup(
            conn,
            candidatura_id,
            FollowupAdiamentoRequest(nova_data=HOJE.isoformat()),
            hoje=HOJE,
        )


# ---------------------------------------------------------------------------
# (e) Candidatura editing — field edits + the A2 archive flag semantics
# ---------------------------------------------------------------------------


def test_editar_candidatura_campos_e_arquivada(conn):
    candidatura_id = _criar(conn)
    resultado = editar_candidatura(
        conn,
        candidatura_id,
        CandidaturaEdicaoRequest(empresa="Globex", arquivada=True),
        hoje=HOJE,
    )
    assert resultado["empresa"] == "Globex"
    assert resultado["arquivada"] is True
    assert resultado["arquivada_em"] == HOJE.isoformat()  # A2 pin

    resultado = editar_candidatura(
        conn, candidatura_id, CandidaturaEdicaoRequest(arquivada=False), hoje=HOJE
    )
    assert resultado["arquivada"] is False
    assert resultado["arquivada_em"] is None  # unarchive clears the date


def test_editar_candidatura_none_nao_sobrescreve(conn):
    candidatura_id = _criar(conn, fonte="LinkedIn")
    resultado = editar_candidatura(
        conn, candidatura_id, CandidaturaEdicaoRequest(cargo="Data Engineer"), hoje=HOJE
    )
    assert resultado["cargo"] == "Data Engineer"
    assert resultado["fonte"] == "LinkedIn"  # None = untouched


def test_editar_candidatura_desconhecida_levanta_erro(conn):
    with pytest.raises(TrackerErro) as exc:
        editar_candidatura(conn, 999, CandidaturaEdicaoRequest(cargo="x"), hoje=HOJE)
    assert "Candidatura 999 não encontrada" in exc.value.message_ptbr


def test_editar_candidatura_vazia_levanta_erro(conn):
    candidatura_id = _criar(conn)
    with pytest.raises(TrackerErro):
        editar_candidatura(conn, candidatura_id, CandidaturaEdicaoRequest(), hoje=HOJE)


# ---------------------------------------------------------------------------
# (f) Stage moves + vocabulary management (D-05)
# ---------------------------------------------------------------------------


def test_mover_estagio(conn):
    candidatura_id = _criar(conn)
    resultado = mover_estagio(conn, candidatura_id, 3, hoje=HOJE)
    assert resultado["estagio_id"] == 3
    assert resultado["estagio_nome"] == "Entrevista"


def test_mover_estagio_desconhecido_levanta_erro(conn):
    candidatura_id = _criar(conn)
    with pytest.raises(TrackerErro) as exc:
        mover_estagio(conn, candidatura_id, 999, hoje=HOJE)
    assert "Estágio 999 não encontrado" in exc.value.message_ptbr


def test_mover_candidatura_desconhecida_levanta_erro(conn):
    with pytest.raises(TrackerErro) as exc:
        mover_estagio(conn, 999, 1, hoje=HOJE)
    assert "Candidatura 999 não encontrada" in exc.value.message_ptbr


def test_criar_estagio_ordem_max_mais_um(conn):
    novo = criar_estagio(conn, EstagioCriacaoRequest(nome="Negociação"))
    assert novo == {"id": 6, "nome": "Negociação", "ordem": 6}


def test_renomear_estagio(conn):
    atualizado = renomear_estagio(conn, 1, EstagioEdicaoRequest(nome="Explorando"))
    assert atualizado == {"id": 1, "nome": "Explorando", "ordem": 1}


def test_reordenar_estagios_persiste_ordem(conn):
    estagios = reordenar_estagios(conn, [3, 1, 2, 4, 5])
    assert [e["id"] for e in estagios] == [3, 1, 2, 4, 5]
    assert [e["ordem"] for e in estagios] == [1, 2, 3, 4, 5]  # contiguous 1..n


def test_reordenar_estagios_incompleto_levanta_erro(conn):
    with pytest.raises(TrackerErro):
        reordenar_estagios(conn, [2, 1])  # must cover ALL stages


def test_remover_estagio_referenciado_bloqueado(conn):
    _criar(conn, estagio_id=2)  # a candidatura sits in "Enviado"
    with pytest.raises(TrackerErro) as exc:
        remover_estagio(conn, 2)
    assert "Não é possível remover: há candidaturas neste estágio" in exc.value.message_ptbr
    # Nothing removed — no cascade ever touches candidaturas (D-05/D-04).
    assert len(listar_estagios(conn)) == 5


def test_remover_estagio_livre_mantem_ordem_contigua(conn):
    criar_estagio(conn, EstagioCriacaoRequest(nome="Negociação"))  # id 6, ordem 6
    resultado = remover_estagio(conn, 3)  # "Entrevista" — unreferenced
    estagios = resultado["estagios"]
    assert "Entrevista" not in [e["nome"] for e in estagios]
    assert [e["ordem"] for e in estagios] == [1, 2, 3, 4, 5]  # renumbered contiguously
    assert estagios[-1]["nome"] == "Negociação"


def test_remover_estagio_desconhecido_levanta_erro(conn):
    with pytest.raises(TrackerErro) as exc:
        remover_estagio(conn, 999)
    assert "Estágio 999 não encontrado" in exc.value.message_ptbr


# ---------------------------------------------------------------------------
# (g) Export builders (D-03 + T-07-02)
# ---------------------------------------------------------------------------


def test_exportar_csv_bom_delimitador_e_sanitizacao(conn):
    _criar(conn, empresa="=SOMA(A1)")  # formula-leading cell (T-07-02 vector)
    bytes_csv = exportar_csv(conn)
    assert bytes_csv.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM leads the bytes
    texto = bytes_csv.decode("utf-8-sig")
    assert ";" in texto  # A6 pin — PT-BR Excel double-click
    linhas = texto.splitlines()
    assert linhas[0].split(";")[0] == "empresa"  # header row
    assert linhas[1].startswith("'=SOMA(A1);")  # apostrophe prefix present


def test_exportar_json_roundtrip_tres_tabelas(conn):
    candidatura_id = _criar(conn)
    _criar_evento(
        conn,
        candidatura_id,
        "envio_curriculo",
        HOJE.isoformat(),
        idioma="pt-BR",
    )
    criar_estagio(conn, EstagioCriacaoRequest(nome="Negociação"))
    carga = json.loads(exportar_json(conn, hoje=HOJE).decode("utf-8"))
    assert set(carga) == {"estagios", "candidaturas", "exportado_em"}
    assert carga["exportado_em"] == HOJE.isoformat()
    assert len(carga["estagios"]) == 6
    assert len(carga["candidaturas"]) == 1
    cand = carga["candidaturas"][0]
    assert cand["empresa"] == "Acme"
    assert cand["eventos"][0]["tipo"] == "envio_curriculo"
    assert cand["eventos"][0]["idioma"] == "pt-BR"
