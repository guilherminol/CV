"""POST /api/resume/exportar — one-shot export envelope (D-07..D-12, T-04-02).

The handler renders the SUBMITTED displayed state (D-10: perfil + generated
secoes travel verbatim from the screen — regenerating server-side from the
profile is rejected; the generation pipeline is NEVER called here), then
render → PDF → parse-back gate → self-check in ONE request:

    _aplicar_selecao → join_experience_dates → build_resume_html →
    html_to_pdf → parse_back_check → build_selfcheck

The optional selecao (quick task 261006-oy9, D-01/D-02) is a PRESENTATIONAL
filter applied after validation: it subsets what renders into the PDF, and
because the filter runs BEFORE the join/render/gate chain and _expected_doc
consumes the SAME filtered views, the parse-back gate can only verify the
document that actually renders (T-OY9-02 — never a render bypass).

The handler is a PLAIN `def` (NEVER async def): html_to_pdf blocks on sync
Playwright (~0.9s Chromium launch + render), and sync Playwright RAISES
under a running asyncio loop (RESEARCH Pitfall 1) — Starlette dispatches
sync endpoints to its threadpool so the event loop stays responsive (same
rationale as routes/resume.py, threat T-03-06).

House envelope rule (routes/resume.py): EVERY failure answers HTTP 200 with
{"status": "erro", "erros": [PT-BR lines]}; raw gate detail and exception
text go to the uvicorn terminal log ONLY — never an HTTP 500, never raw
detail in the envelope (D-08, threat T-04-03). A gate failure is not an
exception: the route logs the raw extraction and returns the erro envelope
WITHOUT any PDF payload key — the ordering IS the guarantee that bytes can
only ever cross to the client on the gate-ok path (D-07/D-08, T-04-04).

Request validation is strict (extra=forbid, threat T-04-02): min_length=1
floors on all three generated sections make an empty or partial section set
a loud FastAPI 422 (specless REVIEW-02/empty edge — the generation envelope
is all-or-nothing, T-03-07, so a real client always satisfies them);
idioma is pinned by Literal (D-12: the PDF follows the run language, no
extra selector). keywords may be empty — zero-keyword runs are legitimate.

Discipline: export adds NO line to logs/runs.jsonl (LLM-call-only contract);
PDF bytes and the base64 payload are never logged; the self-check matcher is
the deterministic Phase 3 classifier — no LLM machinery anywhere in the
export path (D-15; enforced by a structural test in tests/test_export_api.py).
"""

import base64
import logging
from dataclasses import dataclass
from datetime import date
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.export.errors import ExportError
from app.export.gate import ExpectedDoc, ExpectedExperience, parse_back_check
from app.export.pdf import html_to_pdf
from app.export.render import (
    HEADINGS,
    build_resume_html,
    format_date_range,
    iter_rendered_strings,
    join_experience_dates,
    rendered_section_keys,
)
from app.export.selfcheck import build_selfcheck
from app.llm.schemas import ExperienciaGerada, Keyword
from app.profile.models import Profile

logger = logging.getLogger(__name__)

router = APIRouter()

# T-04-02: resumo is the one free-form section string — bounded generously
# (~10x the longest realistic run-language summary paragraph; the JD_MAX_LENGTH
# precedent for wire-bound guards at personal scale).
RESUMO_MAX_LENGTH = 8000


class ExportarSecoes(BaseModel):
    """The three generated sections, verbatim from the displayed state.

    min_length=1 floors: an empty or partial section set is a loud 422
    (REVIEW-02/empty edge) — the route can never render an empty or partial
    document, mirroring the all-or-nothing generation envelope (T-03-07).
    """

    model_config = ConfigDict(extra="forbid")

    resumo: str = Field(min_length=1, max_length=RESUMO_MAX_LENGTH)
    experiencias: list[ExperienciaGerada] = Field(min_length=1)
    habilidades: list[str] = Field(min_length=1)


class SelecaoExportacao(BaseModel):
    """Presentational export selection (quick task 261006-oy9, D-01/D-02).

    Seven section flags — all defaulting True, so an absent/partial selecao
    exports everything (today's behavior, byte-identical) — plus optional
    item-level index lists for the two item-granular sections (experiencias,
    projetos). None = ALL items travel; the lists are used ONLY when their
    parent section flag is True (a False flag excludes the section wholesale
    and its indices are ignored). Strict (extra=forbid, T-04-02): an unknown
    key inside selecao is a loud 422.

    A selection that would render ZERO sections is rejected loudly by the
    model_validator (FastAPI 422), mirroring the existing min_length=1 house
    precedent — the route can never render a degenerate empty document.
    """

    model_config = ConfigDict(extra="forbid")

    resumo: bool = True
    experiencias: bool = True
    formacao: bool = True
    habilidades: bool = True
    certificacoes: bool = True
    idiomas: bool = True
    projetos: bool = True
    # Item granularity (D-01): None = all items; [] = none; out-of-range or
    # negative indices are silently ignored by the route's enumerate
    # membership filter — never indexed blindly, never a crash (T-OY9-01).
    experiencias_indices: list[int] | None = None
    projetos_indices: list[int] | None = None

    @model_validator(mode="after")
    def _pelo_menos_uma_secao(self) -> "SelecaoExportacao":
        if not any(
            (
                self.resumo,
                self.experiencias,
                self.formacao,
                self.habilidades,
                self.certificacoes,
                self.idiomas,
                self.projetos,
            )
        ):
            raise ValueError(
                "seleção vazia: ao menos uma seção deve permanecer selecionada"
            )
        return self


class ExportarRequest(BaseModel):
    """Strict body for POST /api/resume/exportar — the displayed state,
    verbatim (D-10). Reuses app.profile.models.Profile and
    app.llm.schemas.ExperienciaGerada/Keyword directly: the exact objects the
    screen holds are what travel (validated strictly on the way in).

    selecao (quick task 261006-oy9, D-02): optional presentational filter
    applied AFTER validation, INSIDE the route — the generation pipeline
    contract is untouched, and None (absent) means export everything, so
    today's payloads and tests are unchanged."""

    model_config = ConfigDict(extra="forbid")

    perfil: Profile
    secoes: ExportarSecoes
    keywords: list[Keyword] = []  # zero-keyword runs are legitimate (loud-zero UI)
    idioma: Literal["pt-BR", "en"]
    selecao: SelecaoExportacao | None = None


@dataclass
class _SecoesFiltradas:
    """The selection-filtered view of the three generated sections — the
    object handed to join_experience_dates/build_resume_html/_expected_doc.
    Duck-type-compatible with ExportarSecoes (same attribute names) so the
    render module needs no knowledge of the selection."""

    resumo: str
    experiencias: list[ExperienciaGerada]
    habilidades: list[str]


def _indices_filtrados(itens: list, indices: list[int] | None) -> list:
    """enumerate-membership filter (T-OY9-01): only non-negative in-range
    indices ever match — [99, -1] selects nothing, never crashes."""
    if indices is None:
        return list(itens)
    escolhidos = set(indices)
    return [item for pos, item in enumerate(itens) if pos in escolhidos]


def _aplicar_selecao(payload: ExportarRequest) -> tuple[Profile, _SecoesFiltradas]:
    """Apply the presentational selection (D-01/D-02) BEFORE any downstream
    call, producing the filtered views EVERY consumer shares — join, render,
    and gate see one identical filtered payload (T-OY9-02: the parse-back
    gate can only verify the document that actually renders).

    perfil.experiences is NEVER filtered — join_experience_dates matches
    generated entries to stored ranges by folded company, consumed
    positionally. Perfil section lists are swapped via model_copy(update=...),
    which skips validators — safe because every swapped value is [] or a
    subset of already-validated entries. keywords/idioma/filename come from
    the ORIGINAL payload (selection is presentational — D-02/D-03)."""
    selecao = payload.selecao
    if selecao is None:
        return payload.perfil, _SecoesFiltradas(
            resumo=payload.secoes.resumo,
            experiencias=list(payload.secoes.experiencias),
            habilidades=list(payload.secoes.habilidades),
        )

    perfil_updates: dict = {}
    if not selecao.formacao:
        perfil_updates["education"] = []
    if not selecao.certificacoes:
        perfil_updates["certifications"] = []
    if not selecao.idiomas:
        perfil_updates["languages"] = []
    if not selecao.projetos:
        perfil_updates["projects"] = []
    elif selecao.projetos_indices is not None:
        perfil_updates["projects"] = _indices_filtrados(
            payload.perfil.projects, selecao.projetos_indices
        )
    perfil = payload.perfil.model_copy(update=perfil_updates) if perfil_updates else payload.perfil

    secoes = _SecoesFiltradas(
        resumo=payload.secoes.resumo if selecao.resumo else "",
        experiencias=(
            _indices_filtrados(payload.secoes.experiencias, selecao.experiencias_indices)
            if selecao.experiencias
            else []
        ),
        habilidades=list(payload.secoes.habilidades) if selecao.habilidades else [],
    )
    return perfil, secoes


def _expected_doc(
    perfil: Profile,
    secoes: _SecoesFiltradas,
    datas: list[tuple[str, str | None] | None],
    idioma: str,
) -> ExpectedDoc:
    """ExpectedDoc from render.py outputs over the FILTERED views — template
    and gate can never drift (ExpectedDoc contract in gate.py; T-OY9-02).
    Dateless entries (no profile join match) carry dates=None — the gate
    skips ONLY the date sub-check."""
    labels = HEADINGS[idioma]
    return ExpectedDoc(
        contact_tokens=(perfil.contact.email,),
        # CR-01: the template is the truth — expected headings derive from the
        # SAME rendered-section traversal build_resume_html renders from, so a
        # hidden empty passthrough section (Profile defaults: education,
        # certifications, languages, projects all default to []) — or a
        # section emptied by the export selection — is never demanded of the
        # PDF. Order checks stay intact: the keys come back in render order.
        headings=tuple(
            (key, labels[key])
            for key in rendered_section_keys(perfil, secoes, datas, idioma)
        ),
        experiences=tuple(
            ExpectedExperience(
                company=exp.company,
                title=exp.title,
                # WR-01: datas is the per-entry join output — element i carries
                # secoes.experiencias[i]'s own range (None = dateless entry).
                dates=(
                    format_date_range(*datas[idx], idioma)
                    if idx < len(datas) and datas[idx] is not None
                    else None
                ),
            )
            for idx, exp in enumerate(secoes.experiencias)
        ),
        accent_strings=tuple(
            iter_rendered_strings(perfil, secoes, datas, idioma)
        ),
    )


@router.post("/api/resume/exportar")
def exportar_curriculo(payload: ExportarRequest) -> dict:
    """Render → PDF → gate → envelope in ONE sync-def request (D-07).

    Ordering IS the D-07/D-08 guarantee: pdf_base64 is placed in the response
    only AFTER gate.ok — a gate-failing export can never reach the user as if
    good (T-04-04; pinned by the gate-failure test). The self-check rides the
    same ok response (D-13), built from the SAME GateResult the delivery
    decision used. Filename convention curriculo-{idioma}-{data}.pdf (D-11)."""
    try:
        # Selection filter FIRST (T-OY9-02): join, template and gate consume
        # the SAME filtered views — the parse-back gate verifies exactly the
        # document that renders, never a bypass of it.
        perfil_filtrado, secoes_filtradas = _aplicar_selecao(payload)
        datas = join_experience_dates(perfil_filtrado, secoes_filtradas)
        html_doc = build_resume_html(perfil_filtrado, secoes_filtradas, datas, payload.idioma)
        pdf_bytes = html_to_pdf(html_doc)
        gate = parse_back_check(
            pdf_bytes,
            _expected_doc(perfil_filtrado, secoes_filtradas, datas, payload.idioma),
        )
        if not gate.ok:
            logger.error(
                "Falha no gate de parse-back do export:\n%s", gate.raw
            )  # raw extracted text → terminal ONLY (D-08/T-04-03)
            return {"status": "erro", "erros": gate.erros_ptbr}
        selfcheck = build_selfcheck(gate.flat_text, payload.keywords, payload.idioma, gate)
        return {
            "status": "ok",
            "filename": f"curriculo-{payload.idioma}-{date.today().isoformat()}.pdf",
            "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
            "selfcheck": selfcheck,
        }
    except ExportError as exc:
        logger.error("Falha na exportação do currículo:\n%s", exc.raw)  # raw → terminal (D-08)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
