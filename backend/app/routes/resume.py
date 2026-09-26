"""POST /api/resume/lint + POST /api/resume/gerar — 200-envelope contract.

Both handlers are PLAIN `def` (NEVER async def): run_stage blocks on the
synchronous OpenAI SDK client for up to ~60s per generate, and Starlette
dispatches sync endpoints to its threadpool so the event loop stays
responsive during the run (RESEARCH Pitfall 2, threat T-03-06).

House envelope rule (same as routes/profile.py): EVERY failure (ProfileError,
PromptError, LLMError) answers HTTP 200 with {"status": "erro", "erros":
[PT-BR lines]}; the raw exception detail goes to the uvicorn terminal log
ONLY — never an HTTP 500, never raw detail in the envelope (D-13/D-14,
threat T-03-02). All-or-nothing (T-03-07): the pipeline raises before any
envelope is built, so a partial section set is unreachable.

Request validation is strict (extra=forbid, threat T-03-01): jd_text bounded
80..20000 chars, language pinned by Literal defaulting to pt-BR. Validation
failures surface as FastAPI's default 422 — malformed requests are a client
bug, not a UI state. The pasted JD flows only into run_stage's user-message
input as DATA, never interpolated into the system prompt (T-02-01).
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from app.llm.errors import LLMError, PromptError
from app.profile.loader import ProfileError
from app.resume.pipeline import run_lint_only, run_resume_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# T-03-01: sane max-length guard — token cost is the real bound at personal
# scale; 80 chars is the same floor the UI's CTA gate enforces.
JD_MIN_LENGTH = 80
JD_MAX_LENGTH = 20000


class LintRequest(BaseModel):
    """Strict body for POST /api/resume/lint."""

    model_config = ConfigDict(extra="forbid")

    jd_text: str = Field(min_length=JD_MIN_LENGTH, max_length=JD_MAX_LENGTH)


class GerarRequest(LintRequest):
    """Strict body for POST /api/resume/gerar — language defaults to pt-BR."""

    language: Literal["pt-BR", "en"] = "pt-BR"


@router.post("/api/resume/lint")
def lint_vaga(payload: LintRequest) -> dict:
    """Pre-generate keyword extraction + JD-tied lint (SC5) — sync def."""
    try:
        return {"status": "ok", **run_lint_only(payload.jd_text)}
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na análise da vaga:\n%s", exc.raw)  # raw → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}


@router.post("/api/resume/gerar")
def gerar_curriculo(payload: GerarRequest) -> dict:
    """One-shot generate: extraction → lint → 3 sections → coverage — sync def."""
    try:
        result = run_resume_pipeline(payload.jd_text, payload.language)
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na geração do currículo:\n%s", exc.raw)  # raw → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return result
