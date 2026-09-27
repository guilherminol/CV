"""POST /api/resume/exportar — one-shot export envelope (D-07..D-12, T-04-02).

The handler renders the SUBMITTED displayed state (D-10: perfil + generated
secoes travel verbatim from the screen — regenerating server-side from the
profile is rejected; the generation pipeline is NEVER called here), then
render → PDF → parse-back gate → self-check in ONE request:

    join_experience_dates → build_resume_html → html_to_pdf →
    parse_back_check → build_selfcheck

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
from datetime import date
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

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


class ExportarRequest(BaseModel):
    """Strict body for POST /api/resume/exportar — the displayed state,
    verbatim (D-10). Reuses app.profile.models.Profile and
    app.llm.schemas.ExperienciaGerada/Keyword directly: the exact objects the
    screen holds are what travel (validated strictly on the way in)."""

    model_config = ConfigDict(extra="forbid")

    perfil: Profile
    secoes: ExportarSecoes
    keywords: list[Keyword] = []  # zero-keyword runs are legitimate (loud-zero UI)
    idioma: Literal["pt-BR", "en"]


def _expected_doc(
    payload: ExportarRequest, datas: dict[str, tuple[str, str | None]]
) -> ExpectedDoc:
    """ExpectedDoc from render.py outputs — template and gate can never
    drift (ExpectedDoc contract in gate.py). Dateless entries (no profile
    join match) carry dates=None — the gate skips ONLY the date sub-check."""
    labels = HEADINGS[payload.idioma]
    return ExpectedDoc(
        contact_tokens=(payload.perfil.contact.email,),
        # CR-01: the template is the truth — expected headings derive from the
        # SAME rendered-section traversal build_resume_html renders from, so a
        # hidden empty passthrough section (Profile defaults: education,
        # certifications, languages, projects all default to []) is never
        # demanded of the PDF. Order checks stay intact: the keys come back in
        # render order.
        headings=tuple(
            (key, labels[key])
            for key in rendered_section_keys(
                payload.perfil, payload.secoes, datas, payload.idioma
            )
        ),
        experiences=tuple(
            ExpectedExperience(
                company=exp.company,
                title=exp.title,
                # WR-01: datas is the per-entry join output — element i carries
                # secoes.experiencias[i]'s own range (None = dateless entry).
                dates=(
                    format_date_range(*datas[idx])
                    if idx < len(datas) and datas[idx] is not None
                    else None
                ),
            )
            for idx, exp in enumerate(payload.secoes.experiencias)
        ),
        accent_strings=tuple(
            iter_rendered_strings(payload.perfil, payload.secoes, datas, payload.idioma)
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
        datas = join_experience_dates(payload.perfil, payload.secoes)
        html_doc = build_resume_html(payload.perfil, payload.secoes, datas, payload.idioma)
        pdf_bytes = html_to_pdf(html_doc)
        gate = parse_back_check(pdf_bytes, _expected_doc(payload, datas))
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
