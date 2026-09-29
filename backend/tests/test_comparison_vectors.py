"""Canonical fold/numeral vectors for the frontend comparison port (05-03).

frontend/src/lib/comparison.ts is a mechanical TS port of the project's
verified matching mechanics: coverage.py's _fold/_term_pattern (lines 33-41)
and the invention-detector numeral regex from tests/test_resume_grounding.py
(lines 146-157). The TS side intentionally has NO JS test runner (held house
contract) — its verification is `tsc -b` + the phase UAT against THIS table:
every vector below carries a comment stating the expected TS-side result
(fold()/termPattern()/extractNumerals()/foldContains() from comparison.ts),
so a divergent port fails review against the same pinned behavior.

These are the CANONICAL vectors: the port must reproduce them exactly —
lookarounds on both sides, never word-boundary anchors (Pitfall 1 of
05-RESEARCH: word-boundary transitions verifiably false-negative C++, C#,
.NET and CI/CD).
"""

import re

from app.resume.coverage import _fold, _term_pattern

# Re-declared EXACTLY as in tests/test_resume_grounding.py:146-157 (the
# invention-detector prior art): the AAAA-MM date shape first (never split
# into year+month), then percentages with the sign attached, then plain /
# decimal / thousand-grouped numbers; lookarounds both sides so identifier
# tails (utf8, v2) never leak phantom numerals. TS mirror: the NUMERAL_RE
# literal in frontend/src/lib/comparison.ts — same order, same structure.
_NUMERAL_RE = re.compile(
    r"""
    (?<!\w)                  # not the tail of a word/identifier
    (?:
        \d{4}-\d{2}          # AAAA-MM date shape, kept whole
      | \d+(?:[.,]\d+)*%     # percentage with the sign attached
      | \d+(?:[.,]\d+)*      # plain / decimal / thousand-grouped number
    )
    (?!\w)                   # no identifier tail either
    """,
    re.VERBOSE,
)


def extract_numerals(text: str) -> set[str]:
    """Every numeric token in the text (mirrors the grounding prior art)."""
    return set(_NUMERAL_RE.findall(text))


# ---------------------------------------------------------------------------
# Fold vectors (coverage.py _fold lines 33-41 ≡ comparison.ts fold())
# ---------------------------------------------------------------------------


def test_fold_vectors() -> None:
    # TS: fold('Résumé') === 'resume'
    assert _fold("Résumé") == "resume"
    # TS: fold('Currículo') === 'curriculo'
    assert _fold("Currículo") == "curriculo"
    # TS: fold('AWS Certified') === 'aws certified'
    assert _fold("AWS Certified") == "aws certified"
    # TS: fold('Integração') === 'integracao'
    assert _fold("Integração") == "integracao"


# ---------------------------------------------------------------------------
# Term-boundary vectors (coverage.py _term_pattern ≡ comparison.ts termPattern())
# ---------------------------------------------------------------------------


def test_term_pattern_matches_accent_and_case_insensitively() -> None:
    # TS: termPattern('Integração').test(fold('INTEGRACAO com o ERP')) === true
    assert _term_pattern("Integração").search(_fold("INTEGRACAO com o ERP"))
    # TS: termPattern('python').test(fold('Python no backend')) === true
    assert _term_pattern("python").search(_fold("Python no backend"))


def test_term_pattern_matches_tech_shapes() -> None:
    # TS: termPattern('C++').test(fold('domina C++ e C#')) === true
    assert _term_pattern("C++").search(_fold("domina C++ e C#"))
    # TS: termPattern('.NET').test(fold('experiência com .NET 8')) === true
    assert _term_pattern(".NET").search(_fold("experiência com .NET 8"))
    # TS: termPattern('CI/CD').test(fold('pipeline de CI/CD')) === true
    assert _term_pattern("CI/CD").search(_fold("pipeline de CI/CD"))


def test_term_pattern_rejects_identifier_tails() -> None:
    # No false tail matches — the lookarounds hold where word-boundary
    # anchors would either miss the match or fire inside an identifier.
    # TS: termPattern('C++').test(fold('xC++')) === false
    assert not _term_pattern("C++").search(_fold("xC++"))
    # TS: termPattern('.NET').test(fold('ASP.NET')) === false
    assert not _term_pattern(".NET").search(_fold("ASP.NET"))
    # TS: termPattern('CI/CD').test(fold('pipeline CI/CDv2')) === false
    assert not _term_pattern("CI/CD").search(_fold("pipeline CI/CDv2"))
    # TS: termPattern('v2').test(fold('v25')) === false
    assert not _term_pattern("v2").search(_fold("v25"))


# ---------------------------------------------------------------------------
# Numeral vectors (grounding prior art ≡ comparison.ts extractNumerals())
# ---------------------------------------------------------------------------


def test_extract_numerals_canonical_set() -> None:
    # TS: extractNumerals('Melhorou 40% em 2022-03 — custo de 1.234 e 7,5 dias')
    #     === Set({'40%', '2022-03', '1.234', '7,5'})
    assert extract_numerals("Melhorou 40% em 2022-03 — custo de 1.234 e 7,5 dias") == {
        "40%",
        "2022-03",
        "1.234",
        "7,5",
    }


def test_extract_numerals_identifier_guard() -> None:
    # utf8 / v2 never leak as numerals.
    # TS: extractNumerals('utf8 e v2 não vazam numerais') === Set()
    assert extract_numerals("utf8 e v2 não vazam numerais") == set()


# ---------------------------------------------------------------------------
# Folded-containment vectors (assert_invention_free ≡ comparison.ts foldContains())
# ---------------------------------------------------------------------------


def test_folded_substring_containment_vectors() -> None:
    # Substring semantics, not token equality: "2022" inside facts
    # "2022-03" is grounded.
    # TS: foldContains(fold('período: 2022-03 – atual'), '2022') === true
    facts = _fold("período: 2022-03 – atual")
    assert "2022" in facts
    # TS: foldContains(fold('-40% no tempo de resposta'), '87%') === false
    assert "87%" not in _fold("-40% no tempo de resposta")
    # Accent/case-folded containment both sides.
    # TS: foldContains(fold('INTEGRAÇÃO com o ERP'), 'integracao') === true
    assert "integracao" in _fold("INTEGRAÇÃO com o ERP")
