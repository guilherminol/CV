"""Deterministic keyword coverage matcher (RESUME-04, D-02) — pure functions.

D-02: covered/absent classification by deterministic matching in code — NO
LLM judge, no network, no I/O. The honest checklist is auditable mechanics:
every "coberto" mark carries the exact term string that matched (termo), so
the UI can show the string that marked the match.

Input discipline (locked reading of D-02, "sobre o texto gerado"): the caller
(plan 03-03) passes ONLY the 3 generated sections' text. Recorded consequence
(plan 03-02, research Open Question 1 / A4): a certification keyword present
only in a passthrough section (e.g. Certificações) reads "ausente" — flipping
later is a one-line input change in the caller.

Boundary mechanics (RESEARCH Pattern 3, empirically verified on this
project's Python 3.12 runtime — 15-row probe table): per-term patterns are
lookaround-bounded `(?<!\\w)term(?!\\w)` — NEVER `\\b`, which verifiably
false-negatives on the special-character keywords ATS users care most about
(C++, C#, .NET, CI/CD): a keyword ending in a non-word character has no `\b`
transition against a following space. Both sides are casefolded + NFKD
accent-folded before matching (D-02 "case/pontuação-insensitive" without an
unidecode dependency).

`adjacente` stays empty this phase (D-02 option B) — no stemming, no NLP
machinery; additive later if wanted.
"""

import re
import unicodedata

from app.llm.schemas import Keyword


def _fold(text: str) -> str:
    """Casefold + NFKD accent-fold (drop combining marks) — both sides, once."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _term_pattern(term: str) -> re.Pattern:
    """Lookaround-bounded pattern over the FOLDED term — never \\b (Pitfall 1)."""
    return re.compile(r"(?<!\w)" + re.escape(_fold(term)) + r"(?!\w)", re.IGNORECASE)


def keyword_in_text(keyword: Keyword, text: str, language: str) -> str | None:
    """Return the FIRST matching candidate term string (D-02 auditability) or None.

    Candidate order (D-11 Fase 2): the run-language rendering (kw.pt for a
    pt-BR run, kw.en otherwise), then canonical, then aliases.
    """
    folded_text = _fold(text)
    primary = keyword.pt if language == "pt-BR" else keyword.en
    for term in [primary, keyword.canonical, *keyword.aliases]:
        if term and _term_pattern(term).search(folded_text):
            return term
    return None


def classify_coverage(
    keywords: list[Keyword], generated_text: str, language: str
) -> list[dict]:
    """Per-keyword coverage entry, in extraction order.

    Each entry: {"canonical", "category", "termo", "status"} where termo is
    the matched term string (None on a miss) and status is "coberto" |
    "ausente". The input must be the 3 GENERATED sections' text ONLY — see
    the module docstring for the recorded passthrough consequence.
    """
    cobertura: list[dict] = []
    for keyword in keywords:
        termo = keyword_in_text(keyword, generated_text, language)
        cobertura.append(
            {
                "canonical": keyword.canonical,
                "category": keyword.category,
                "termo": termo,
                "status": "coberto" if termo is not None else "ausente",
            }
        )
    return cobertura


def summarize_coverage(cobertura: list[dict]) -> dict:
    """Exact integer tally {"cobertos", "total"} — no score, no percentage."""
    return {
        "cobertos": sum(1 for entry in cobertura if entry["status"] == "coberto"),
        "total": len(cobertura),
    }
