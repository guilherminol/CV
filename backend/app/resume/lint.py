"""JD-tied completeness lint (PROFILE-02, D-04) — pure functions.

Sibling to — NOT a replacement of — app.profile.completeness.compute_completude
(presence/counts for the Perfil home, D-12): THIS lint ties profile gaps to
what the vaga asks. Output is a plain list of PT-BR aviso strings in D-04
order — (a) keyword gaps, (b) experiences without impacts, (c) empty summary —
and is NON-BLOCKING (D-03): avisos never gate the generate CTA, and the lint
never raises on data gaps.

The (a) check matches ANY keyword rendering (canonical, aliases, pt, en)
against the profile inventory — SkillGroup.items + Project.technologies +
the languages section (name and level, BOTH renderings) — reusing the SAME
lookaround/fold matcher primitives as app.resume.coverage (one matcher, two
inputs). Skills/technologies are single language-neutral strings; languages
carry both renderings, so a vaga citing "English" fold-matches the Inglês
entry instead of false-flagging a language the profile speaks.

Template strings are the UI-SPEC Copywriting Contract rows, owned here
verbatim — the frontend renders them without re-mapping (D-13 discipline).
"""

from app.llm.schemas import Keyword
from app.profile.models import Profile
from app.resume.coverage import _fold, _term_pattern


def _profile_inventory(profile: Profile) -> str:
    """One string joining every skill item, project technology AND language
    (name + level in both renderings) — D-04a: a vaga citing a language the
    profile speaks is not a gap ("English" fold-matches Inglês/English)."""
    items = [item for group in profile.skills for item in group.items]
    items.extend(
        technology for project in profile.projects for technology in project.technologies
    )
    items.extend(
        text
        for entry in profile.languages
        for text in (*entry.name.values(), *entry.level.values())
        if text
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


def _gap_aviso(canonical: str) -> str:
    """The (a) template row — owned HERE verbatim (UI-SPEC Copywriting Contract)."""
    return f'A vaga cita "{canonical}", ausente do seu perfil.'


def lint_gaps(profile: Profile, keywords: list[Keyword]) -> list[dict]:
    """The (a) check as STRUCTURED rows — the vaga → perfil acceptance supply.

    Each row carries the keyword's acceptance payload (canonical/pt/en/
    categoria — the POST /api/profile/adicionar body shape) PLUS the verbatim
    aviso line, so the UI renders the backend-owned string next to its add
    button without ever parsing avisos (D-13). Only competencias/ferramentas
    are inventory-bound (titles and certifications have no profile inventory).
    """
    inventory = _profile_inventory(profile)
    gaps: list[dict] = []
    for keyword in keywords:
        if keyword.category not in ("competencias", "ferramentas"):
            continue
        if not _matches_inventory(keyword, inventory):
            gaps.append(
                {
                    "canonical": keyword.canonical,
                    "pt": keyword.pt,
                    "en": keyword.en,
                    "categoria": keyword.category,
                    "aviso": _gap_aviso(keyword.canonical),
                }
            )
    return gaps


def lint_jd_tied(profile: Profile, keywords: list[Keyword]) -> list[str]:
    """D-04 checks in (a) → (b) → (c) order; non-blocking PT-BR avisos (D-03)."""
    avisos: list[str] = []

    # (a) JD keyword gaps — derived from the SAME structured rows the
    # acceptance UI consumes (one matcher, one template, two consumers).
    avisos.extend(gap["aviso"] for gap in lint_gaps(profile, keywords))

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
