"""POST /api/linkedin/lint + POST /api/linkedin/gerar +
POST /api/linkedin/regenerar — 200-envelope contract (plans 06-01/06-02).

Plain `def` (NEVER async def): run_stage blocks on the synchronous OpenAI SDK
client, and Starlette dispatches sync endpoints to its threadpool so the
event loop stays responsive during the run (house pattern from
routes/resume.py, Pitfall 2).

House envelope rule (same as routes/resume.py): every failure (ProfileError,
PromptError, LLMError) answers HTTP 200 with {"status": "erro", "erros":
[PT-BR lines]}; the raw exception detail goes to the uvicorn terminal log
ONLY — never an HTTP 500, never raw detail in the envelope (T-06-04).
All-or-nothing (T-03-07): the pipeline raises before any envelope is built,
so a partial section set is unreachable.

Request validation is strict (extra=forbid, T-03-01): objetivo bounded
80..2000 chars — inputs DO get Field bounds (the LLM-layer OUTPUT models
never do, D-07); language pinned by Literal defaulting to pt-BR. Validation
failures surface as FastAPI's default 422. The objetivo and the optional
dica flow only into run_stage's user-message input as DATA, never the system
prompt (T-06-01); the dica is bounded (max_length 500) and normalized at the
compose boundary.

/lint (D-03) reuses run_lint_only VERBATIM — the keyword engine is
input-agnostic and already accepts objectives; zero new lint logic, avisos
non-blocking (view, not gate).

/regenerar (D-04) regenerates ONE section with Phase 5 semantics: the
submitted displayed state travels verbatim in `secoes` (LinkedinSecoes —
imported from app.linkedin.models, never duplicated; T-06-07: strict model,
secao Literal, the server treats it as display state to merge — never
executed or persisted, ephemeral D-11), and the response carries the FULL
merged secoes + recomputed limites so the client replaces its state
wholesale. The route adds NO logging beyond the house raw-detail line — no
hint or section text is ever logged (Phase 5 T-05-04 discipline).
"""

import logging

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.config import LINKEDIN_OBJETIVO_MAX_LENGTH, LINKEDIN_OBJETIVO_MIN_LENGTH
from app.linkedin.models import LinkedinSecoes
from app.linkedin.pipeline import run_linkedin_pipeline, run_linkedin_section_regen
from app.llm.errors import LLMError, PromptError
from app.profile.loader import ProfileError
from app.resume.pipeline import run_lint_only

logger = logging.getLogger(__name__)

router = APIRouter()


class LinkedinLintRequest(BaseModel):
    """Strict body for POST /api/linkedin/lint (T-03-01 discipline)."""

    model_config = ConfigDict(extra="forbid")

    objetivo: str = Field(
        min_length=LINKEDIN_OBJETIVO_MIN_LENGTH,
        max_length=LINKEDIN_OBJETIVO_MAX_LENGTH,
    )


class LinkedinGerarRequest(LinkedinLintRequest):
    """Strict body for POST /api/linkedin/gerar — language defaults to pt-BR."""

    language: Literal["pt-BR", "en"] = "pt-BR"


class LinkedinRegenerarRequest(LinkedinLintRequest):
    """Strict body for POST /api/linkedin/regenerar (plan 06-02, T-06-07).

    `secoes` REUSES LinkedinSecoes (imported from app.linkedin.models — never
    duplicated): the exact displayed-state shape the screen holds.
    `dica` is optional and bounded (strip-empty → base composition at the
    compose boundary); the frontend omits the empty dica KEY from the body
    (extra=forbid hygiene — the Phase 5 pattern).
    """

    language: Literal["pt-BR", "en"]
    secao: Literal["headline", "sobre", "experiencias", "habilidades"]
    secoes: LinkedinSecoes
    dica: str | None = Field(default=None, max_length=500)


@router.post("/api/linkedin/lint")
def lint_linkedin(payload: LinkedinLintRequest) -> dict:
    """Pre-generate keyword extraction + objective lint (D-03) — sync def.

    run_lint_only VERBATIM (the engine is input-agnostic and already accepts
    objectives); avisos are non-blocking — never a gate."""
    try:
        return {"status": "ok", **run_lint_only(payload.objetivo)}
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na análise do objetivo:\n%s", exc.raw)  # raw → terminal (T-06-04)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}


@router.post("/api/linkedin/gerar")
def gerar_linkedin(payload: LinkedinGerarRequest) -> dict:
    """Generate the LinkedIn sections for one career objective — sync def."""
    try:
        result = run_linkedin_pipeline(payload.objetivo, payload.language)
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na geração do LinkedIn:\n%s", exc.raw)  # raw → terminal (T-06-04)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {"status": "ok", **result}


@router.post("/api/linkedin/regenerar")
def regenerar_secao_linkedin(payload: LinkedinRegenerarRequest) -> dict:
    """Regenerate ONE LinkedIn section: one gateway stage → merged secoes +
    recomputed limites back — sync def (same threadpool rationale as gerar;
    the blocking stage call must never stall the event loop)."""
    try:
        return run_linkedin_section_regen(
            payload.objetivo,
            payload.language,
            payload.secao,
            payload.secoes,
            dica=payload.dica,
        )
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na regeneração da seção do LinkedIn:\n%s", exc.raw)  # raw → terminal
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
