"""Coverage matcher tests — the honest-checklist mechanics (RESUME-04, D-02).

Exhaustive offline table mirroring the RESEARCH Pattern 3 empirical probe
(verified on this project's Python 3.12 runtime) plus language-selection and
accent-fold rows. The matcher is a pure function over typed inputs — no
network, no LLM (D-02: a semantic judge would reintroduce false precision).

The special-character rows (C++, C#, .NET, CI/CD) are load-bearing: a `\b`
pattern verifiably false-negatives on exactly these (Pitfall 1), so these
rows pin the lookaround boundary mechanics `(?<!\\w)…(?!\\w)`.
"""

import pytest

from app.llm.schemas import Keyword
from app.resume.coverage import classify_coverage, keyword_in_text, summarize_coverage


def _kw(
    canonical: str,
    category: str = "competencias",
    aliases: list[str] | None = None,
    pt: str | None = None,
    en: str | None = None,
) -> Keyword:
    return Keyword.model_validate(
        {
            "canonical": canonical,
            "aliases": aliases or [],
            "pt": pt,
            "en": en,
            "category": category,
        }
    )


# ---------------------------------------------------------------------------
# RESEARCH Pattern 3 — special-character keywords (the \b false-negative trap)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("canonical", "text", "expected_term"),
    [
        ("C++", "sei C++ e C", "C++"),
        ("C#", "programo em C# hoje", "C#"),
        (".NET", "usa .NET no trabalho", ".NET"),
        ("CI/CD", "experiência com CI/CD no dia a dia", "CI/CD"),
    ],
)
def test_special_char_keywords_match_via_lookaround(
    canonical: str, text: str, expected_term: str
) -> None:
    # \b variants fail every row here (RESEARCH probe table) — the lookaround
    # matcher must return the exact term string that matched (D-02 auditability).
    kw = _kw(canonical, category="ferramentas")
    assert keyword_in_text(kw, text, "en") == expected_term


# ---------------------------------------------------------------------------
# Inside-word and glued-token blocking (lookaround, not \b — still strict)
# ---------------------------------------------------------------------------


def test_inside_word_match_is_blocked() -> None:
    java = _kw("Java")
    javascript = _kw("JavaScript")
    # "JavaScript" contains "Java" only INSIDE the word — the lookarounds must
    # block it, so keyword "Java" does not match a text about JavaScript alone.
    only_js_text = "o JavaScript domina o frontend"
    assert keyword_in_text(java, only_js_text, "en") is None
    assert keyword_in_text(javascript, only_js_text, "en") == "JavaScript"
    # A standalone "Java" occurrence elsewhere still matches — no false
    # negatives on the honest checklist (RESEARCH probe row 11's example text
    # "o JavaScript e Java" ends with a standalone "Java"; pinning None there
    # would demand a broken matcher).
    assert keyword_in_text(java, "sei Java e também JavaScript", "en") == "Java"


def test_glued_token_is_blocked() -> None:
    kw = _kw("C++", category="ferramentas")
    assert keyword_in_text(kw, "o stack ABC++x", "en") is None


# ---------------------------------------------------------------------------
# Aliases — the matched alias string is what gets returned
# ---------------------------------------------------------------------------


def test_alias_hit_returns_the_alias_string() -> None:
    kw = _kw("Kubernetes", category="ferramentas", aliases=["k8s"])
    assert keyword_in_text(kw, "orquestração com k8s no cluster", "en") == "k8s"


def test_alias_alone_does_not_make_an_inside_word_match() -> None:
    kw = _kw("Kubernetes", category="ferramentas", aliases=["k8s"])
    assert keyword_in_text(kw, "o tak8s interno", "en") is None


# ---------------------------------------------------------------------------
# Accents — case-insensitive and accent-folded on BOTH sides
# ---------------------------------------------------------------------------


def test_accented_keyword_matches_case_insensitively() -> None:
    kw = _kw("Comunicação", pt="Comunicação", en="Communication")
    assert keyword_in_text(kw, "boa comunicação com o time", "pt-BR") == "Comunicação"


def test_accent_fold_matches_unfolded_keyword_against_accented_text() -> None:
    kw = _kw("comunicacao", pt="comunicacao", en="communication")
    assert keyword_in_text(kw, "boa comunicação com o time", "pt-BR") == "comunicacao"


# ---------------------------------------------------------------------------
# Run-language selection (D-11 Fase 2): pt-BR → kw.pt, en → kw.en,
# canonical fallback when the run-language rendering is null, aliases always.
# ---------------------------------------------------------------------------


def test_pt_br_run_matches_the_pt_rendering() -> None:
    kw = _kw("Pipeline de dados", pt="Pipeline de dados", en="Data pipeline")
    assert (
        keyword_in_text(kw, "montamos um pipeline de dados sólido", "pt-BR")
        == "Pipeline de dados"
    )


def test_en_run_matches_the_en_rendering() -> None:
    kw = _kw("Pipeline de dados", pt="Pipeline de dados", en="Data pipeline")
    assert keyword_in_text(kw, "we own the data pipeline end to end", "en") == (
        "Data pipeline"
    )


def test_run_language_rendering_beats_canonical_in_candidate_order() -> None:
    # Both renderings would match their own text; only the run-language one is tried first.
    kw = _kw("Containerização", pt="Containerização", en="Containerization")
    assert (
        keyword_in_text(kw, "containerização de serviços", "pt-BR") == "Containerização"
    )
    assert (
        keyword_in_text(kw, "containerization of services", "en") == "Containerization"
    )


def test_pt_run_with_null_pt_falls_back_to_canonical() -> None:
    kw = _kw("Kafka", category="ferramentas", pt=None, en="Apache Kafka")
    assert keyword_in_text(kw, "consumimos do Kafka diariamente", "pt-BR") == "Kafka"


def test_en_run_with_null_en_falls_back_to_canonical() -> None:
    kw = _kw("Kafka", category="ferramentas", pt="Kafka", en=None)
    assert keyword_in_text(kw, "streaming with Kafka", "en") == "Kafka"


def test_aliases_are_always_tried_regardless_of_language() -> None:
    kw = _kw("Kubernetes", category="ferramentas", aliases=["k8s"], en="Kubernetes")
    assert keyword_in_text(kw, "o k8s roda o cluster", "pt-BR") == "k8s"


# ---------------------------------------------------------------------------
# classify_coverage — extraction order, auditable termo, coberto/ausente
# ---------------------------------------------------------------------------


def test_classify_coverage_preserves_extraction_order_and_reports_misses() -> None:
    keywords = [
        _kw("Python", pt="Python", en="Python"),
        _kw("Snowflake", category="ferramentas", pt="Snowflake", en="Snowflake"),
        _kw("Kubernetes", category="ferramentas", aliases=["k8s"]),
    ]
    text = "automatizei pipelines com Python e orquestração com k8s"
    resultado = classify_coverage(keywords, text, "pt-BR")
    assert [entry["canonical"] for entry in resultado] == [
        "Python",
        "Snowflake",
        "Kubernetes",
    ]
    assert resultado[0] == {
        "canonical": "Python",
        "category": "competencias",
        "termo": "Python",
        "status": "coberto",
    }
    assert resultado[1] == {
        "canonical": "Snowflake",
        "category": "ferramentas",
        "termo": None,
        "status": "ausente",
    }
    assert resultado[2] == {
        "canonical": "Kubernetes",
        "category": "ferramentas",
        "termo": "k8s",
        "status": "coberto",
    }


def test_classify_coverage_empty_keywords_yield_empty_cobertura() -> None:
    # The loud empty state is the UI's job (plan 03-04) — never a silent default.
    assert classify_coverage([], "texto qualquer", "pt-BR") == []


# ---------------------------------------------------------------------------
# summarize_coverage — exact integer counts, nothing derived beyond len/count
# ---------------------------------------------------------------------------


def test_summarize_counts_exactly() -> None:
    cobertura = [
        {"status": "coberto"},
        {"status": "ausente"},
        {"status": "coberto"},
    ]
    assert summarize_coverage(cobertura) == {"cobertos": 2, "total": 3}


def test_summarize_empty_list_is_zero_totals() -> None:
    assert summarize_coverage([]) == {"cobertos": 0, "total": 0}


def test_summarize_never_invents_a_score_or_percentage() -> None:
    cobertura = [{"status": "coberto"}] * 4 + [{"status": "ausente"}] * 1
    tally = summarize_coverage(cobertura)
    assert set(tally) == {"cobertos", "total"}  # no score/percent fields, ever
    assert tally == {"cobertos": 4, "total": 5}
