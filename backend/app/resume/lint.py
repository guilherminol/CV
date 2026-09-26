"""JD-tied completeness lint (PROFILE-02, D-04) — pure functions.

Sibling to — NOT a replacement of — app.profile.completeness.compute_completude
(presence/counts for the Perfil home, D-12): THIS lint ties profile gaps to
what the vaga asks. Output is a plain list of PT-BR aviso strings in D-04
order — (a) keyword gaps, (b) experiences without impacts, (c) empty summary —
and is NON-BLOCKING (D-03): avisos never gate the generate CTA, and the lint
never raises on data gaps.

The (a) check matches ANY keyword rendering (canonical, aliases, pt, en)
against the profile inventory — SkillGroup.items + Project.technologies (the
two surfaces named by D-04a) — reusing the SAME lookaround/fold matcher
primitives as app.resume.coverage (one matcher, two inputs). The profile's
skills/technologies are single language-neutral strings, so the check is
language-agnostic by construction.

Template strings are the UI-SPEC Copywriting Contract rows, owned here
verbatim — the frontend renders them without re-mapping (D-13 discipline).
"""

from app.llm.schemas import Keyword
from app.profile.models import Profile
from app.resume.coverage import _fold, _term_pattern


def _profile_inventory(profile: Profile) -> str:
    """One string joining every skill item and project technology (D-04a)."""
    items = [item for group in profile.skills for item in group.items]
    items.extend(
        technology for project in profile.projects for technology in project.technologies
    )
    return " ".join(items)


def _matches_inventory(keyword: Keyword, inventory: str) -> bool:
    """True when ANY rendering (pt, en, canonical, aliases) hits the inventory."""
    folded_inventory = _fold(inventory)
    candidates = [keyword.pt, keyword.en, keyword.canonical, *keyword.aliases]
    return any(
        term and _term_pattern(term).search(folded_inventory) for term in candidates
    )


def _summary_is_empty(profile: Profile) -> bool:
    """True when the summary map is absent or resolves to blank text."""
    return not any(
        (value or "").strip() for value in (profile.summary or {}).values()
    )


def lint_jd_tied(profile: Profile, keywords: list[Keyword]) -> list[str]:
    """D-04 checks in (a) → (b) → (c) order; non-blocking PT-BR avisos (D-03)."""
    avisos: list[str] = []

    # (a) JD keyword gaps — only competencias/ferramentas are inventory-bound
    # (titles and certifications have no profile inventory to compare against).
    inventory = _profile_inventory(profile)
    for keyword in keywords:
        if keyword.category not in ("competencias", "ferramentas"):
            continue
        if not _matches_inventory(keyword, inventory):
            avisos.append(f'A vaga cita "{keyword.canonical}", ausente do seu perfil.')

    # (b) experiences without impacts/metrics.
    for experience in profile.experiences:
        if not experience.impacts:
            avisos.append(
                f'"{experience.company}" não tem impactos com métricas no perfil.'
            )

    # (c) summary absent or resolving empty.
    if _summary_is_empty(profile):
        avisos.append("O resumo do perfil está vazio.")

    return avisos
