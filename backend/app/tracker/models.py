"""Tracker request DTOs — the wire contract for /api/tracker/* routes.

Docstring discipline copied from app/linkedin/models.py: ONE definition per
DTO, imported by BOTH the route layer (request body) and the service, so the
wire shape can never drift between the two. Every request model is strict
(extra="forbid") with Field bounds mirroring the house conventions (JD 20000
like the resume/lint bounds; notas 5000; observacao 2000 — the T-07-05 DoS
posture).

Wave-0 drift lock (06-01 precedent): ALL tracker request DTOs are pinned
here in 07-01, before the route stages that consume them exist (07-02/07-04).

D-06 field set; `modalidade` constrained to the D-06 trio; event `tipo` to
the five pinned literals ('resposta' is the D-13 Respostas-association type).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TrackerModalidade = Literal["remoto", "hibrido", "presencial"]

TipoEvento = Literal[
    "envio_curriculo",
    "entrevista",
    "retorno",
    "followup",
    "resposta",
]

TrackerIdioma = Literal["pt-BR", "en"]

# Date-only ISO 'YYYY-MM-DD' — no timezone-bearing timestamps (Pitfall 7).
_PADRAO_DATA = r"^\d{4}-\d{2}-\d{2}$"


class CandidaturaCriacaoRequest(BaseModel):
    """Body for POST /api/tracker/candidaturas.

    empresa/cargo are the only required fields — the minimal create path.
    estagio_id is optional: None resolves server-side to the first stage by
    ordem (D-05-safe default — never hardcode a seed id at the call site).
    """

    model_config = ConfigDict(extra="forbid")

    empresa: str = Field(min_length=1, max_length=200)
    cargo: str = Field(min_length=1, max_length=200)
    estagio_id: int | None = None
    fonte: str | None = Field(default=None, max_length=200)
    link_vaga: str | None = Field(default=None, max_length=2000)
    faixa_salarial: str | None = Field(default=None, max_length=100)
    contato_recrutador: str | None = Field(default=None, max_length=200)
    data_aplicacao: str | None = Field(default=None, pattern=_PADRAO_DATA)
    prazo_retorno: str | None = Field(default=None, pattern=_PADRAO_DATA)
    notas: str | None = Field(default=None, max_length=5000)
    jd_texto: str | None = Field(default=None, max_length=20000)
    modalidade: TrackerModalidade | None = None


class CandidaturaEdicaoRequest(BaseModel):
    """Body for the candidatura edit/archive route (07-02)."""

    model_config = ConfigDict(extra="forbid")

    empresa: str | None = Field(default=None, min_length=1, max_length=200)
    cargo: str | None = Field(default=None, min_length=1, max_length=200)
    fonte: str | None = Field(default=None, max_length=200)
    link_vaga: str | None = Field(default=None, max_length=2000)
    faixa_salarial: str | None = Field(default=None, max_length=100)
    contato_recrutador: str | None = Field(default=None, max_length=200)
    estagio_id: int | None = None
    data_aplicacao: str | None = Field(default=None, pattern=_PADRAO_DATA)
    prazo_retorno: str | None = Field(default=None, pattern=_PADRAO_DATA)
    notas: str | None = Field(default=None, max_length=5000)
    jd_texto: str | None = Field(default=None, max_length=20000)
    modalidade: TrackerModalidade | None = None
    arquivada: bool | None = None


class EventoRegistroRequest(BaseModel):
    """Body for the event-registration route (07-02) — metadata only (D-08)."""

    model_config = ConfigDict(extra="forbid")

    tipo: TipoEvento
    data_evento: str = Field(pattern=_PADRAO_DATA)
    idioma: TrackerIdioma | None = None
    observacao: str | None = Field(default=None, max_length=2000)


class FollowupExecucaoRequest(BaseModel):
    """Body for "execute follow-up" — re-dates the pending event to today (D-10)."""

    model_config = ConfigDict(extra="forbid")

    observacao: str | None = Field(default=None, max_length=2000)


class FollowupAdiamentoRequest(BaseModel):
    """Body for "adiar follow-up" — re-dates the pending event to a new future date (D-11)."""

    model_config = ConfigDict(extra="forbid")

    nova_data: str = Field(pattern=_PADRAO_DATA)


class EstagioCriacaoRequest(BaseModel):
    """Body for POST /api/tracker/estagios (D-05 — personal stage vocabulary)."""

    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=1, max_length=80)


class EstagioEdicaoRequest(BaseModel):
    """Body for the stage edit route — rename and/or reorder (D-05)."""

    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=1, max_length=80)
    ordem: int | None = None

    @model_validator(mode="after")
    def _pelo_menos_um_campo(self) -> "EstagioEdicaoRequest":
        if self.nome is None and self.ordem is None:
            raise ValueError("Informe ao menos um campo: nome ou ordem")
        return self


class ExportRequest(BaseModel):
    """Body for the export route (D-03 — JSON completo ou CSV para planilha)."""

    model_config = ConfigDict(extra="forbid")

    formato: Literal["json", "csv"]
