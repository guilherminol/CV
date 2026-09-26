"""JD-tied completeness lint (PROFILE-02, D-04) — pure functions.

STUB (TDD RED): signature only — the behavior table in
tests/test_resume_lint.py must fail on assertions, not collection errors.
The GREEN commit replaces this body.
"""

from app.llm.schemas import Keyword
from app.profile.models import Profile


def lint_jd_tied(profile: Profile, keywords: list[Keyword]) -> list[str]:
    """D-04 checks in (a) → (b) → (c) order; non-blocking PT-BR avisos (D-03)."""
    return ["__STUB__"]
