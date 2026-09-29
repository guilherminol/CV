"""POST /api/linkedin/gerar — 200-envelope contract (plan 06-01, LI-01/D-02).

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
failures surface as FastAPI's default 422. The objetivo flows only into
run_stage's user-message input as DATA, never the system prompt (T-06-01).
"""

import logging

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.config import LINKEDIN_OBJETIVO_MAX_LENGTH, LINKEDIN_OBJETIVO_MIN_LENGTH
from app.linkedin.pipeline import run_linkedin_pipeline
from app.llm.errors import LLMError, PromptError
from app.profile.loader import ProfileError

logger = logging.getLogger(__name__)

router = APIRouter()


class LinkedinGerarRequest(BaseModel):
    """Strict body for POST /api/linkedin/gerar (T-03-01 discipline)."""

    model_config = ConfigDict(extra="forbid")

    objetivo: str = Field(
        min_length=LINKEDIN_OBJETIVO_MIN_LENGTH,
        max_length=LINKEDIN_OBJETIVO_MAX_LENGTH,
    )
    language: Literal["pt-BR", "en"] = "pt-BR"


@router.post("/api/linkedin/gerar")
def gerar_linkedin(payload: LinkedinGerarRequest) -> dict:
    """Generate the LinkedIn sections for one career objective — sync def."""
    try:
        result = run_linkedin_pipeline(payload.objetivo, payload.language)
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na geração do LinkedIn:\n%s", exc.raw)  # raw → terminal (T-06-04)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {"status": "ok", **result}
