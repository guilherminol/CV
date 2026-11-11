"""Candidatura orchestration — run_candidatura_resposta (vaga → perfil module).

One stage ("candidatura-resposta") per POST: the recruiter's open-form
question ("Descreva sua última experiência…") answered from the profile
facts. The composed stage input follows the T-02-01 discipline shared by the
resume and LinkedIn modules: profile facts + optional job description + the
question ALL travel as USER-message DATA blocks — the question is never part
of the system prompt and never an instruction source (a question asking the
model to invent binds only within the prompt's never-invent rules).

House disciplines carried from app.linkedin.pipeline:
- ALL-OR-NOTHING: exceptions propagate UNTOUCHED — the ROUTE owns the erro
  envelope; a raised LLMError aborts before any envelope dict is built.
- No caching: load_profile() runs fresh ONCE per invocation (D-15).
- `runs_log` and `client` thread through to run_stage: the injection seam
  that keeps the default pytest suite 100% offline (D-16).
- LOUD-EMPTY: a blank answer raises LLMError — an empty block is never
  rendered (LinkedIn D-09 convention).

The runs.jsonl contract stays intact (D-10): the stage string
"candidatura-resposta" flows through the existing mechanism, no new fields.
"""

from pathlib import Path

from app.llm.errors import LLMError
from app.llm.gateway import run_stage
from app.profile.loader import load_profile
from app.resume.facts import serialize_profile_facts

PERGUNTA_HEADER = "PERGUNTA DO RECRUTADOR"
VAGA_HEADER = "DESCRIÇÃO DA VAGA"


def compose_resposta_input(fatos: str, pergunta: str, vaga_texto: str | None) -> str:
    """The single input blob one candidatura run passes as run_stage input_text.

    Facts first (the grounding supply line), then the optional job description,
    then the question — each a labeled DATA block, mirroring the
    compose_stage_input convention (T-02-01). The vaga is omitted entirely when
    blank/None: no empty-label noise for the model to misread.
    """
    blocks = [
        "FATOS DO PERFIL:\n" + fatos,
    ]
    if vaga_texto and vaga_texto.strip():
        blocks.append(VAGA_HEADER + ":\n" + vaga_texto.strip())
    blocks.append(PERGUNTA_HEADER + ":\n" + pergunta.strip())
    return "\n\n".join(blocks)


def run_candidatura_resposta(
    pergunta: str,
    language: str,
    vaga_texto: str | None = None,
    *,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
    """Answer ONE application-form question from the profile facts.

    Returns the pipeline envelope fragment {"resposta": str}; raises
    (ProfileError/PromptError/LLMError) untouched — the route owns the erro
    envelope and the raw-detail terminal line.
    """
    profile = load_profile()
    fatos = serialize_profile_facts(profile, language)
    input_text = compose_resposta_input(fatos, pergunta, vaga_texto)
    result = run_stage(
        "candidatura-resposta",
        input_text,
        language,
        runs_log=runs_log,
        client=client,
    )
    resposta = result.resposta.strip()
    if not resposta:  # loud-empty (LinkedIn D-09): never render a blank block
        raise LLMError(
            "A resposta gerada veio vazia — tente novamente",
            "candidatura-resposta returned an empty resposta string",
        )
    return {"resposta": resposta}
