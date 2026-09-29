"""LinkedIn orchestration — run_linkedin_pipeline (plan 06-02, LI-01/D-04/D-09).

One gerar execution generates ALL FOUR sections sequentially in D-09 order
(linkedin-headline → linkedin-sobre → linkedin-experiencias →
linkedin-skills), one run_stage call each with the SAME composed stage_input:
a bad About never re-rolls the headline (per-block stages, localized retry).

House disciplines carried from app.resume.pipeline (D-09 wholesale reuse):
- ALL-OR-NOTHING: exceptions propagate UNTOUCHED — the ROUTE owns the erro
  envelope. A raised LLMError aborts before any envelope dict is built.
- No caching: load_profile() runs fresh ONCE per invocation (D-15) and the
  facts are passed down — no memoization anywhere.
- `runs_log` and `client` thread through to EVERY run_stage call: the
  injection seam that keeps the default pytest suite 100% offline (D-16).
- runs.jsonl contract intact (D-10): the stage strings flow through the
  existing mechanism; no new fields.

Post-generation contracts (D-07, probe edges LI-03/LI-04/LI-05):
- LOUD-EMPTY: a blank headline or sobre, zero experiência entries, or any
  entry with a blank descricao raises LLMError — an empty block is never
  rendered or swapped into a displayed state. Empty habilidades fails ONLY
  when the profile HAS skills to draw from — a skills-less profile is a lint
  aviso surface (frontend), not a run failure.
- ALIGNMENT (LI-04/adjacency + LI-04/ordering): returned experiência entries
  are reordered into PROFILE order by fold-matching company values (coverage
  `_fold` — first unused match wins, so same-company entries each consume one
  distinct returned entry and never collide); a failed pairing falls back to
  positional pairing over ALL returned entries in returned order (UI-SPEC
  all-entries fallback) rather than crashing. The generated company/title
  strings are display anchors only — the frontend renders headers from
  PROFILE FACTS.
- DEDUPE (LI-05/adjacency): duplicate skills fold-match away deterministically,
  first occurrence wins, order otherwise preserved — NO sorting anywhere: the
  LLM's returned order IS the priority order (LI-05).
- LIMITES (D-05/D-07): code-unit counts (Python `len` on the same string the
  client counts with JS `.length`) — never bytes or graphemes. Over-limit text
  is NEVER truncated or rejected: `limites` records {limite, tamanho, excesso}
  and the UI flags it in place. `habilidades` carries {"contagem", "limite"}
  as a sanity record — no per-list character limit exists (D-05 forbids
  inventing one; the UI count line uses contagem only).
"""

from pathlib import Path

from app.config import (
    LINKEDIN_EXPERIENCIA_MAX_CHARS,
    LINKEDIN_HEADLINE_MAX_CHARS,
    LINKEDIN_SKILLS_MAX_COUNT,
    LINKEDIN_SOBRE_MAX_CHARS,
)
from app.llm.errors import LLMError
from app.llm.gateway import run_stage
from app.profile.loader import load_profile
from app.resume.coverage import _fold
from app.resume.facts import serialize_profile_facts

LINKEDIN_HEADLINE_STAGE = "linkedin-headline"
LINKEDIN_SOBRE_STAGE = "linkedin-sobre"
LINKEDIN_EXPERIENCIAS_STAGE = "linkedin-experiencias"
LINKEDIN_SKILLS_STAGE = "linkedin-skills"

# D-09 order: one gerar execution runs ALL FOUR stages sequentially — the
# stage string order IS the generation order (pinned by the stage-order test).
LINKEDIN_SECTION_STAGES = (
    LINKEDIN_HEADLINE_STAGE,
    LINKEDIN_SOBRE_STAGE,
    LINKEDIN_EXPERIENCIAS_STAGE,
    LINKEDIN_SKILLS_STAGE,
)


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


def _require_non_empty(value: str, block_label: str, stage: str) -> str:
    """Loud-empty contract (probe edges LI-03/empty, LI-04/empty): a blank
    generated block raises LLMError — an empty block is never rendered or
    swapped into a displayed state downstream (D-07 mechanics)."""
    if not value or not value.strip():
        raise LLMError(
            f"O modelo devolveu um bloco {block_label} vazio — regenere as "
            "seções (detalhes no terminal)",
            f"empty {block_label} content from the '{stage}' stage",
        )
    return value


def _align_experiencias(profile_experiences: list, returned: list) -> list[dict]:
    """Reorder returned entries into PROFILE order (LI-04/adjacency+ordering).

    Fold-match each profile experience's company against the returned
    `company` values via coverage `_fold` — first UNUSED match wins, so
    same-company profile entries each consume one distinct returned entry and
    never collide or merge. If ANY profile entry fails to pair, fall back to
    positional pairing over ALL returned entries in RETURNED order (UI-SPEC
    all-entries fallback) rather than crashing. Output entries are model
    dumps: the generated company/title strings ride along as display anchors
    only — the frontend renders headers from PROFILE FACTS (06-03).
    """
    used: set[int] = set()
    matched: list = []
    for experience in profile_experiences:
        found = None
        for idx, entry in enumerate(returned):
            if idx in used:
                continue
            if _fold(entry.company) == _fold(experience.company):
                found = idx
                break
        if found is None:
            # All-entries fallback: returned order IS the pairing.
            return [entry.model_dump() for entry in returned]
        matched.append(returned[found])
        used.add(found)
    return [entry.model_dump() for entry in matched]


def _process_experiencias(returned: list, profile_experiences: list) -> list[dict]:
    """Loud-empty + alignment for the experiências stage output (LI-04)."""
    if not returned:
        raise LLMError(
            "O modelo devolveu uma lista de experiências vazia — regenere as "
            "seções (detalhes no terminal)",
            f"empty experiencias list from the '{LINKEDIN_EXPERIENCIAS_STAGE}' stage",
        )
    for idx, entry in enumerate(returned):
        if not entry.descricao or not entry.descricao.strip():
            raise LLMError(
                "O modelo devolveu uma descrição de experiência vazia — "
                "regenere as seções (detalhes no terminal)",
                f"blank descricao on returned experiencias[{idx}] from the "
                f"'{LINKEDIN_EXPERIENCIAS_STAGE}' stage",
            )
    return _align_experiencias(profile_experiences, returned)


def _dedupe_habilidades(habilidades: list[str]) -> list[str]:
    """Fold-match dedupe (LI-05/adjacency): duplicates removed
    deterministically, FIRST occurrence wins, returned order otherwise
    preserved. Deliberately NO sort call anywhere — the LLM's returned order
    IS the priority order (LI-05/ordering)."""
    seen: set[str] = set()
    deduped: list[str] = []
    for skill in habilidades:
        key = _fold(skill)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(skill)
    return deduped


def _process_habilidades(habilidades: list[str], profile) -> list[str]:
    """Dedupe + the skills-only loud-empty rule (LI-05/empty backend half):
    an empty list fails ONLY when the profile HAS skills to draw from — a
    skills-less profile is a lint aviso surface (frontend), not a run
    failure."""
    deduped = _dedupe_habilidades(list(habilidades))
    profile_has_skills = any(group.items for group in profile.skills)
    if not deduped and profile_has_skills:
        raise LLMError(
            "O modelo devolveu uma lista de habilidades vazia — regenere as "
            "seções (detalhes no terminal)",
            f"empty habilidades list from the '{LINKEDIN_SKILLS_STAGE}' stage "
            "(profile has skills to draw from)",
        )
    return deduped


def _limite_entry(text: str, limite: int) -> dict:
    """{limite, tamanho, excesso} with CODE-UNIT counts (probe edges
    LI-03/encoding, LI-04/encoding): Python `len` on the SAME string the
    client counts with JS `.length` — never bytes, never graphemes."""
    tamanho = len(text)
    return {"limite": limite, "tamanho": tamanho, "excesso": max(0, tamanho - limite)}


def _build_limites(secoes: dict) -> dict:
    """The full limites block (D-05/D-07) over a secoes dict: per-text
    {limite, tamanho, excesso} for headline/sobre and per-entry (index-aligned
    with secoes["experiencias"]) for experiências; habilidades carries
    {"contagem", "limite"} as a sanity record — the UI count line uses
    contagem only (no per-list character limit exists; D-05 forbids
    inventing one)."""
    return {
        "headline": _limite_entry(secoes["headline"], LINKEDIN_HEADLINE_MAX_CHARS),
        "sobre": _limite_entry(secoes["sobre"], LINKEDIN_SOBRE_MAX_CHARS),
        "experiencias": [
            _limite_entry(entry["descricao"], LINKEDIN_EXPERIENCIA_MAX_CHARS)
            for entry in secoes["experiencias"]
        ],
        "habilidades": {
            "contagem": len(secoes["habilidades"]),
            "limite": LINKEDIN_SKILLS_MAX_COUNT,
        },
    }


def run_linkedin_pipeline(
    objetivo: str,
    language: str,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
    """Generate the LinkedIn sections for one career objective (LI-01/D-04).

    All four stages run sequentially in D-09 order with the SAME composed
    input. Returns the ok envelope of the plan-06-01 contract: {"idioma",
    "secoes", "limites"} with `secoes` = {"headline": str, "sobre": str,
    "experiencias": [entries in PROFILE order], "habilidades": [str]}. Raises
    on any stage failure (ProfileError from the loader, PromptError from a
    prompt file, LLMError from the gateway or a loud-empty guard); the route
    converts to the erro envelope (all-or-nothing — a partial section set is
    unreachable).
    """
    profile = load_profile()  # fresh, once per invocation (D-15)
    facts = serialize_profile_facts(profile, language)
    stage_input = compose_linkedin_stage_input(facts, objetivo)

    headline_output = run_stage(
        LINKEDIN_SECTION_STAGES[0], stage_input, language, runs_log=runs_log, client=client
    )
    headline = _require_non_empty(
        headline_output.headline, "headline", LINKEDIN_HEADLINE_STAGE
    )

    sobre_output = run_stage(
        LINKEDIN_SECTION_STAGES[1], stage_input, language, runs_log=runs_log, client=client
    )
    sobre = _require_non_empty(sobre_output.sobre, "sobre", LINKEDIN_SOBRE_STAGE)

    experiencias_output = run_stage(
        LINKEDIN_SECTION_STAGES[2], stage_input, language, runs_log=runs_log, client=client
    )
    experiencias = _process_experiencias(
        experiencias_output.experiencias, profile.experiences
    )

    skills_output = run_stage(
        LINKEDIN_SECTION_STAGES[3], stage_input, language, runs_log=runs_log, client=client
    )
    habilidades = _process_habilidades(list(skills_output.habilidades), profile)

    secoes = {
        "headline": headline,
        "sobre": sobre,
        "experiencias": experiencias,
        "habilidades": habilidades,
    }
    return {"idioma": language, "secoes": secoes, "limites": _build_limites(secoes)}


# --- Per-section regeneration (plan 06-02 Task 2, D-04) is added on top of
# this quartet in the next task commit: SECTION_STAGE_BY_ID +
# run_linkedin_section_regen reuse these same helpers over the SUBMITTED
# state with Phase 5 merge semantics. --------------------------------------
