"""Deterministic keyword coverage matcher (RESUME-04, D-02) — pure functions.

D-02: covered/absent classification by deterministic matching in code — NO
LLM judge, no network, no I/O. The honest checklist is auditable mechanics:
every "coberto" mark carries the exact term string that matched (termo).

STUB (TDD RED): signatures only — bodies raise/return sentinels so the
behavior table in tests/test_coverage.py fails on assertions, not on
collection errors. The GREEN commit replaces these bodies.
"""

import re

from app.llm.schemas import Keyword


def _fold(text: str) -> str:
    """Casefold + NFKD accent-fold both sides once, at the boundary."""
    raise NotImplementedError


def _term_pattern(term: str) -> re.Pattern:
    """Lookaround-bounded pattern over the folded term — never \\b."""
    raise NotImplementedError


def keyword_in_text(keyword: Keyword, text: str, language: str) -> str | None:
    """Return the FIRST matching candidate term string, else None."""
    return "__STUB__"


def classify_coverage(
    keywords: list[Keyword], generated_text: str, language: str
) -> list[dict]:
    """Per-keyword {"canonical", "category", "termo", "status"} in extraction order."""
    return []


def summarize_coverage(cobertura: list[dict]) -> dict:
    """Exact integer tally {"cobertos", "total"}."""
    return {}
