"""Real-API fixture harness (D-15) — SC2 acceptance tests.

Two layers:
- OFFLINE fixture-shape tests (default suite): the four bilingual fixture
  texts are realistic, pure data — no network, no markers.
- @pytest.mark.llm real-run tests (deselected by addopts `-m 'not llm'`;
  run explicitly with `uv run pytest -m llm`): the slug probe (A1), one
  real gateway run per fixture, each audited via runs.jsonl (D-13), and the
  bilingual resume-PIPELINE runs (plan 03-05) — the FULL pipeline
  (extraction → lint → 3 grounded section stages → coverage) per language
  over the shipped example profile, policed by assert_invention_free.

Every real test calls gateway.run_stage or resume.run_resume_pipeline — the
ONLY call paths (prohibition: no bespoke SDK clients in tests, client stays
None so the real OpenRouter path runs). A spend failure is loud: no
catch-and-pass, no xfail (D-03).
"""

import json

import pytest

from app.config import LLM_MODEL, OPENROUTER_API_KEY
from app.llm.errors import LLMError
from app.llm.gateway import run_stage
from llm_fixtures import JD_EN, JD_PT, OBJECTIVE_EN, OBJECTIVE_PT

# The four pinned categories (D-10) — each fixture must yield keywords in
# all of them (competências / ferramentas / títulos de vaga / certificações).
CATEGORIES = {"competencias", "ferramentas", "titulos_de_vaga", "certificacoes"}


# ---------------------------------------------------------------------------
# Offline fixture-shape tests (default suite — D-16: never touch the network)
# ---------------------------------------------------------------------------

ALL_FIXTURES = {
    "JD_EN": JD_EN,
    "JD_PT": JD_PT,
    "OBJECTIVE_EN": OBJECTIVE_EN,
    "OBJECTIVE_PT": OBJECTIVE_PT,
}

# Proper nouns intentionally embedded in the fixture texts — used both for
# the category-coverage shape check and the D-09/D-11 live spot-check.
CATEGORY_PROBES = {
    "competencias": ["Kubernetes", "arquitetura"],
    "ferramentas": ["Terraform", "Docker"],
    "titulos_de_vaga": ["Engenheiro de Dados", "Data Engineer"],
    "certificacoes": ["AWS", "PMP"],
}


@pytest.mark.parametrize("name", sorted(ALL_FIXTURES))
def test_fixture_is_realistic_text(name: str) -> None:
    """Each fixture is substantial and touches all four keyword categories."""
    text = ALL_FIXTURES[name]
    assert len(text) > 200, f"{name} deve ter mais de 200 caracteres"
    lowered = text.lower()
    for category, probes in CATEGORY_PROBES.items():
        assert any(
            probe.lower() in lowered for probe in probes
        ), f"{name} não menciona conteúdo da categoria '{category}'"
    if "_PT" in name:
        # Fixtures double as UTF-8 probes: PT-BR texts carry accents.
        assert any(ch in text for ch in "áéíóúãõçêâô"), (
            f"{name} deve conter caracteres acentuados (probe de UTF-8)"
        )


def test_fixtures_are_pure_data() -> None:
    """No test markers, no instructions — pure market text (injection-safe)."""
    for name, text in ALL_FIXTURES.items():
        for marker in ("TODO", "FIXME", "PLACEHOLDER", "lorem ipsum", "{{", "}}"):
            assert marker.lower() not in text.lower(), (
                f"{name} contém marcador '{marker}' — fixtures são dados reais"
            )


# ---------------------------------------------------------------------------
# Real-API harness tests (pytest -m llm — spend!)
# ---------------------------------------------------------------------------

_llm_guard = pytest.mark.skipif(
    not OPENROUTER_API_KEY,
    reason="OPENROUTER_API_KEY ausente — defina a chave no .env para rodar o harness real",
)


@_llm_guard
@pytest.mark.llm
def test_slug_probe_default_model_is_live() -> None:
    """A1/Pitfall 3: the pinned default slug must be accepted by OpenRouter.

    One minimal real call through the gateway; a 404/400 naming the model
    must fail HERE with the slug visible in the assertion output.
    """
    try:
        result = run_stage("keyword-extraction", "Vaga: Data Engineer com AWS.", "en")
    except LLMError as exc:
        pytest.fail(
            f"Slug de modelo inválido ou falha na chamada real — LLM_MODEL="
            f"'{LLM_MODEL}' (verifique openrouter.ai/models). Detalhe: {exc.raw}"
        )
    assert result.keywords, "probe mínimo deve retornar ao menos um keyword"


@_llm_guard
@pytest.mark.llm
@pytest.mark.parametrize(
    ("text", "language", "label"),
    [
        (JD_EN, "en", "JD_EN"),
        (JD_PT, "pt-BR", "JD_PT"),
        (OBJECTIVE_EN, "en", "OBJECTIVE_EN"),
        (OBJECTIVE_PT, "pt-BR", "OBJECTIVE_PT"),
    ],
)
def test_real_run_keyword_extraction(text: str, language: str, label: str, tmp_path) -> None:
    """One real gateway run per fixture — SC2/SC4 live proof.

    Asserts: valid KeywordExtraction, all 4 categories populated, PT-BR runs
    keep pt renderings, proper nouns render identically across languages
    (D-09/D-11 spot-check), and >=1 runs.jsonl line per attempt with numeric
    cost (D-13).
    """
    runs_log = tmp_path / "runs.jsonl"
    result = run_stage(
        "keyword-extraction", text, language, runs_log=runs_log
    )

    # Valid typed output with all four categories non-empty.
    assert result.keywords, f"{label}: nenhum keyword retornado"
    covered = {kw.category for kw in result.keywords}
    missing = CATEGORIES - covered
    assert not missing, f"{label}: categorias vazias: {sorted(missing)}"

    # PT-BR runs must return pt renderings with accents intact (UTF-8 end
    # to end); EN runs must return en renderings.
    renderings = [
        kw.pt if language == "pt-BR" else kw.en
        for kw in result.keywords
    ]
    non_null = [r for r in renderings if r]
    assert len(non_null) >= len(result.keywords) / 2, (
        f"{label}: menos da metade dos keywords com renderização '{language}'"
    )
    if language == "pt-BR":
        assert any(
            any(ch in r for ch in "áéíóúãõçêâô") for r in non_null
        ), f"{label}: nenhuma renderização pt-BR com acentos preservados"

    # D-09/D-11 spot-check: TECHNOLOGY proper nouns render identically across
    # languages (pt == en). Job titles ("Data Engineer" → "Engenheiro de
    # Dados") are translatable and deliberately excluded.
    proper_nouns = {
        "kubernetes", "terraform", "aws", "kafka", "spark", "docker",
        "dbt", "airflow", "snowflake", "redshift", "grafana",
        "opentelemetry", "great expectations", "iceberg", "eks",
    }
    for kw in result.keywords:
        if kw.pt and kw.en and kw.canonical.lower() in proper_nouns:
            assert kw.pt == kw.en, (
                f"{label}: próprio '{kw.canonical}' divergiu entre idiomas "
                f"(pt='{kw.pt}' != en='{kw.en}') — D-11"
            )

    # D-13: every attempt left an auditable runs.jsonl line.
    lines = [
        json.loads(line)
        for line in runs_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    run_lines = [line for line in lines if line.get("event") != "run_summary"]
    assert run_lines, f"{label}: nenhuma linha por tentativa em runs.jsonl"
    for line in run_lines:
        assert line["stage"] == "keyword-extraction"
        assert line["model"] == LLM_MODEL
        assert line["language"] == language
        assert "cost" in line, f"{label}: campo 'cost' ausente em runs.jsonl (D-13)"
        assert isinstance(line["total_tokens"], int) and line["total_tokens"] > 0, (
            f"{label}: total_tokens não numérico/positivo em runs.jsonl: "
            f"{line['total_tokens']!r}"
        )


# ---------------------------------------------------------------------------
# Real-API bilingual resume-PIPELINE harness (plan 03-05) — the FULL pipeline
# through the ONE real call path (run_resume_pipeline with client=None)
# ---------------------------------------------------------------------------

# All four stages the pipeline must audit in runs.jsonl (D-13 at pipeline
# scale): keyword-extraction + the 3 resume section stages (D-01 order).
PIPELINE_STAGES = {
    "keyword-extraction",
    "resume-summary",
    "resume-experiencias",
    "resume-skills",
}


@_llm_guard
@pytest.mark.llm
@pytest.mark.parametrize(
    ("jd", "language", "label"),
    [
        (JD_EN, "en", "pipeline-EN"),
        (JD_PT, "pt-BR", "pipeline-PT"),
    ],
)
def test_real_run_resume_pipeline_bilingual(
    jd: str, language: str, label: str, tmp_path, monkeypatch, shipped_profile_path
) -> None:
    """Full bilingual pipeline live: extraction → lint → 3 grounded stages →
    coverage, on the shipped example profile (invention is detectable there).

    Asserts the ok envelope (idioma/keywords/avisos/secoes/cobertura), the
    invention detector over the composed generated text, per-stage runs.jsonl
    audit lines, and the PT-BR UTF-8 probe (accents intact end to end).
    """
    from app.profile.loader import load_profile
    from app.resume.facts import serialize_profile_facts
    from app.resume.pipeline import run_resume_pipeline
    from test_resume_grounding import assert_invention_free

    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", shipped_profile_path)
    runs_log = tmp_path / "runs.jsonl"
    envelope = run_resume_pipeline(jd, language, runs_log=runs_log)  # client=None: real path

    # Ok envelope of the normative contract.
    assert envelope["status"] == "ok", f"{label}: status != ok"
    assert envelope["idioma"] == language, f"{label}: idioma divergente do pedido"
    keywords = envelope["keywords"]
    assert keywords, f"{label}: nenhum keyword retornado"
    assert isinstance(envelope["avisos"], list), f"{label}: avisos não é lista"

    # Non-empty generated sections (minimum substance bar).
    secoes = envelope["secoes"]
    assert set(secoes) == {"resumo", "experiencias", "habilidades"}
    assert len(secoes["resumo"]) >= 200, (
        f"{label}: resumo curto demais ({len(secoes['resumo'])} chars)"
    )
    total_bullets = sum(len(e["bullets"]) for e in secoes["experiencias"])
    assert total_bullets >= 3, f"{label}: menos de 3 bullets de experiência"
    assert len(secoes["habilidades"]) >= 3, f"{label}: menos de 3 habilidades"

    # Honest coverage tally: one entry per keyword, consistent summary —
    # no score anywhere (RESUME-04).
    cobertura = envelope["cobertura"]
    assert len(cobertura) == len(keywords), (
        f"{label}: cobertura != keywords ({len(cobertura)} vs {len(keywords)})"
    )
    resumo_cov = envelope["cobertura_resumo"]
    assert resumo_cov["total"] == len(cobertura)
    assert 0 <= resumo_cov["cobertos"] <= resumo_cov["total"]

    # SC3 mechanical check: every numeral in the GENERATED text exists in the
    # shipped profile's facts (the invented 87% or unknown date fails here).
    generated_text = "\n".join(
        [secoes["resumo"]]
        + [bullet for entry in secoes["experiencias"] for bullet in entry["bullets"]]
        + list(secoes["habilidades"])
    )
    facts_text = serialize_profile_facts(load_profile(), language)
    assert_invention_free(generated_text, facts_text)

    # D-13 at pipeline scale: attempt lines cover ALL FOUR stages, each with
    # model/language/attempt fields. Extraction is fixed pt-BR; the section
    # stages carry the run language.
    lines = [
        json.loads(line)
        for line in runs_log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    attempt_lines = [line for line in lines if line.get("event") != "run_summary"]
    assert attempt_lines, f"{label}: nenhuma linha por tentativa em runs.jsonl"
    stages_seen = {line["stage"] for line in attempt_lines}
    missing = PIPELINE_STAGES - stages_seen
    assert not missing, f"{label}: estágios ausentes do audit: {sorted(missing)}"
    for line in attempt_lines:
        assert line["model"] == LLM_MODEL
        assert line["language"] in {"pt-BR", language}, (
            f"{label}: language inesperado em runs.jsonl: {line['language']!r}"
        )
        assert isinstance(line["attempt"], int) and line["attempt"] >= 1

    # UTF-8 probe (Phase 2 fixture discipline): PT-BR output keeps accents.
    if language == "pt-BR":
        assert any(
            ch in secoes["resumo"] for ch in "áéíóúãõçêâô"
        ), f"{label}: resumo PT-BR sem caracteres acentuados (probe de UTF-8)"
