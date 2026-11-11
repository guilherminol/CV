"""POST /api/candidatura/responder — 200-envelope contract (vaga → perfil module).

Plain `def` (NEVER async def): run_stage blocks on the synchronous OpenAI SDK
client, and Starlette dispatches sync endpoints to its threadpool so the
event loop stays responsive during the run (house pattern from
routes/resume.py / routes/linkedin.py, Pitfall 2).

House envelope rule: every failure (ProfileError, PromptError, LLMError)
answers HTTP 200 with {"status": "erro", "erros": [PT-BR lines]}; the raw
exception detail goes to the uvicorn terminal log ONLY — never an HTTP 500,
never raw detail in the envelope (T-06-04 posture).

Request validation is strict (extra=forbid): pergunta bounded 5..2000 chars
(a question shorter than 5 chars is a mis-paste; 2000 mirrors the dica-style
input bound), optional vaga_texto bounded like the resume JD (0..20000 —
unlike the resume flow the vaga is OPTIONAL here: many form questions need
no job description), language pinned by Literal defaulting to pt-BR.
Validation failures surface as FastAPI's default 422. The pergunta and vaga
flow only into run_stage's user-message input as DATA, never the system
prompt (T-02-01).
"""

import logging

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.candidatura.pipeline import run_candidatura_resposta
from app.llm.errors import LLMError, PromptError
from app.profile.loader import ProfileError

logger = logging.getLogger(__name__)

router = APIRouter()

PERGUNTA_MIN_LENGTH = 5
PERGUNTA_MAX_LENGTH = 2000
VAGA_MAX_LENGTH = 20000  # same bound as the resume JD — pasted JDs get long


class CandidaturaRespostaRequest(BaseModel):
    """Strict body for POST /api/candidatura/responder."""

    model_config = ConfigDict(extra="forbid")

    pergunta: str = Field(min_length=PERGUNTA_MIN_LENGTH, max_length=PERGUNTA_MAX_LENGTH)
    vaga_texto: str | None = Field(default=None, max_length=VAGA_MAX_LENGTH)
    language: Literal["pt-BR", "en"] = "pt-BR"


@router.post("/api/candidatura/responder")
def responder_candidatura(payload: CandidaturaRespostaRequest) -> dict:
    """Answer ONE application-form question from the profile facts — sync def
    (the blocking stage call must never stall the event loop)."""
    try:
        result = run_candidatura_resposta(
            payload.pergunta,
            payload.language,
            vaga_texto=payload.vaga_texto,
        )
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na resposta de candidatura:\n%s", exc.raw)  # raw → terminal
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {"status": "ok", **result}
