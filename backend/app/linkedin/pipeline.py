"""LinkedIn orchestration — run_linkedin_pipeline (plan 06-01, LI-01/D-09).

Tracer scope (plan 06-01): ONLY the linkedin-headline stage runs. Wave 2
(06-02) expands this to the full D-09 quartet (linkedin-sobre,
linkedin-experiencias, linkedin-skills) — the function signature and the
envelope shape ({idioma, secoes, limites}) are final from day one; later
waves extend ADDITIVELY (new sections never rename existing keys).

House disciplines carried from app.resume.pipeline (D-09 wholesale reuse):
- ALL-OR-NOTHING: exceptions propagate UNTOUCHED — the ROUTE owns the erro
  envelope. A raised LLMError aborts before any envelope dict is built.
- No caching: load_profile() runs fresh ONCE per invocation (D-15) and the
  facts are passed down — no memoization anywhere.
- `runs_log` and `client` thread through to EVERY run_stage call: the
  injection seam that keeps the default pytest suite 100% offline (D-16).
- runs.jsonl contract intact (D-10): the stage string "linkedin-headline"
  flows through the existing mechanism; no new fields.

Post-generation limit mechanics (D-07, probe edges LI-02/empty + LI-02/
encoding): an empty/blank generated headline raises LLMError LOUD — an empty
block is never rendered; over-limit text is never truncated or rejected —
`limites` records {limite, tamanho, excesso} and the UI flags it in place.
Counts are CODE-UNIT counts (Python `len` on the same string the client
counts with JS `.length`) — never bytes or grapheme clusters.
"""

from pathlib import Path

from app.config import LINKEDIN_HEADLINE_MAX_CHARS
from app.llm.errors import LLMError
from app.llm.gateway import run_stage
from app.profile.loader import load_profile
from app.resume.facts import serialize_profile_facts

LINKEDIN_HEADLINE_STAGE = "linkedin-headline"


def compose_linkedin_stage_input(facts: str, objetivo: str) -> str:
    """The single input blob a LinkedIn run passes as run_stage input_text
    (research Pattern 2 — mirrors compose_stage_input): the profile-fact
    section plus the career objective — both DATA inside the gateway's
    existing user-message template (T-02-01/T-06-01: the objetivo is
    user-message data, NEVER a system-prompt instruction and never parsed
    for instructions anywhere in this pipeline)."""
    return (
        "FATOS DO PERFIL:\n"
        f"{facts}\n"
        "\n"
        "OBJETIVO DE CARREIRA:\n"
        f"{objetivo}"
    )


def run_linkedin_pipeline(
    objetivo: str,
    language: str,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
    """Generate the LinkedIn sections for one career objective (LI-01/D-04).

    Returns the ok envelope of the plan-06-01 contract: {"idioma", "secoes",
    "limites"} — the ROUTE adds "status": "ok". Raises on any stage failure
    (ProfileError from the loader, PromptError from the prompt file, LLMError
    from the gateway or the empty-headline guard); the route converts to the
    erro envelope (all-or-nothing — a partial section set is unreachable).
    """
    profile = load_profile()  # fresh, once per invocation (D-15)
    facts = serialize_profile_facts(profile, language)
    stage_input = compose_linkedin_stage_input(facts, objetivo)

    headline_output = run_stage(
        LINKEDIN_HEADLINE_STAGE, stage_input, language, runs_log=runs_log, client=client
    )
    headline = headline_output.headline
    if not headline or not headline.strip():
        # Probe edge LI-02/empty: an empty/blank headline fails the run LOUD
        # (SC3 posture) — an empty block is never rendered or swapped into a
        # displayed state downstream (D-07 mechanics).
        raise LLMError(
            "O modelo devolveu um headline vazio — regenere as seções "
            "(detalhes no terminal)",
            f"empty headline content from the '{LINKEDIN_HEADLINE_STAGE}' stage",
        )

    # Probe edge LI-02/encoding: CODE-UNIT count — Python `len` on the same
    # string the client's `.length` counts. Never bytes, never graphemes.
    tamanho = len(headline)
    limite = LINKEDIN_HEADLINE_MAX_CHARS
    return {
        "idioma": language,
        "secoes": {"headline": headline},
        "limites": {
            "headline": {
                "limite": limite,
                "tamanho": tamanho,
                "excesso": max(0, tamanho - limite),
            }
        },
    }
