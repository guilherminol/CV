"""Deterministic QA vectors — glossário + English bleed (plan 06-04, SC4,
D-12/D-13/D-14), OFFLINE (test_coverage.py vector style; the loader-failure
ladder mirrors tests/test_prompt_loader.py).

Pinned here, all pure-function:

- Glossary substitution (apply_glossario): exact replacement in all three
  case shapes (lower / Capitalized / ALL-CAPS), lookaround boundaries
  ("machine learning" never matches inside a larger word or a plural), UTF-8
  accent intactness (the surrounding text survives byte-for-byte), correct
  occurrence counts, zero-match pair → no row AND no text change, multi-pair
  file order, and the non-word-char trailing boundary (e-commerce vs
  e-commerces — the \\b lesson);
- load_glossario: the strict fail-fast ladder (missing file / broken YAML /
  unexpected extra key / empty pair → PromptError with a PT-BR message naming
  file and field) + the fresh-read seam (a mutated file between two calls
  changes the result — D-12 edit-and-next-run);
- English bleed (detect_english_bleed): one positive vector per shipped
  EN_BLEED_TERMS term, case/fold variants, accented PT-BR negative controls
  (the fold machinery + list curation proven — including the "for" PT-verb
  collision that kept the token out), and the consolidated-tech-noun
  exclusion;
- run_linkedin_qa orchestration: glossary BEFORE bleed on the post-glossary
  text (the report describes the copied text — research constraint #4),
  habilidades flagged but NEVER rewritten, experiência rows labeled by
  company, the en language gate (None + zero mutation + no file read), and
  the loud-empty payload shape for a clean run.
"""

from pathlib import Path

import pytest
import yaml

from app.linkedin.qa import (
    EN_BLEED_TERMS,
    GlossarioSpec,
    ParGlossario,
    apply_glossario,
    detect_english_bleed,
    load_glossario,
    run_linkedin_qa,
)
from app.llm.errors import PromptError

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Helpers — tmp glossário writer + spec builders (hermetic; the real shipped
# file gets its own soft happy-path test so user edits never break vectors)
# ---------------------------------------------------------------------------


def _write_glossario(directory: Path, meta: dict, body: str = "Documentação.") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + body
        + "\n"
    )
    path = directory / f"{meta['id']}.md"
    path.write_text(text, encoding="utf-8")
    return path


def _valid_meta() -> dict:
    return {
        "id": "glossario",
        "pares": [{"de": "machine learning", "para": "aprendizado de máquina"}],
    }


def _spec(pares: list[tuple[str, str]]) -> GlossarioSpec:
    return GlossarioSpec(
        id="glossario",
        pares=[ParGlossario(de=de, para=para) for de, para in pares],
    )


ML = ("machine learning", "aprendizado de máquina")


# ---------------------------------------------------------------------------
# Glossary substitution — deterministic, case-preserving, reported (D-13)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("found", "expected"),
    [
        # lower — the para as written
        ("machine learning", "aprendizado de máquina"),
        # Capitalized — the para's first letter follows the match
        ("Machine Learning", "Aprendizado de máquina"),
        # ALL-CAPS — the whole para uppercased
        ("MACHINE LEARNING", "APRENDIZADO DE MÁQUINA"),
    ],
)
def test_substitution_preserves_the_match_case_shape(found: str, expected: str) -> None:
    texto, rows = apply_glossario(f"Hoje: {found}.", _spec([ML]))
    assert texto == f"Hoje: {expected}."
    assert rows == [{"de": ML[0], "para": ML[1], "ocorrencias": 1}]


def test_substitution_counts_every_occurrence_and_keeps_each_case() -> None:
    texto = "machine learning, MACHINE LEARNING e Machine Learning mudam tudo."
    novo, rows = apply_glossario(texto, _spec([ML]))
    assert novo == (
        "aprendizado de máquina, APRENDIZADO DE MÁQUINA e Aprendizado de máquina mudam tudo."
    )
    assert rows == [{"de": ML[0], "para": ML[1], "ocorrencias": 3}]


def test_lookaround_blocks_matches_inside_larger_words() -> None:
    # The plan's boundary vector: "machine learning" must not fire inside a
    # plural/larger construct — the trailing (?!\w) blocks "machine learnings".
    texto = "cursos de machine learnings e machinelearnings existem."
    novo, rows = apply_glossario(texto, _spec([ML]))
    assert novo == texto  # untouched — no whole-term match
    assert rows == []


def test_lookaround_blocks_non_word_char_trailing_boundary() -> None:
    # Pitfall 7: a term ending in a non-word char has NO \b transition — the
    # lookarounds must match "e-commerce" standalone and skip "e-commerces".
    par = ("e-commerce", "comércio eletrônico")
    novo, rows = apply_glossario("minha loja e-commerce cresceu", _spec([par]))
    assert novo == "minha loja comércio eletrônico cresceu"
    assert rows == [{"de": par[0], "para": par[1], "ocorrencias": 1}]
    novo, rows = apply_glossario("lojas e-commerces crescem", _spec([par]))
    assert novo == "lojas e-commerces crescem"
    assert rows == []


def test_utf8_accents_around_the_substitution_survive_byte_for_byte() -> None:
    texto = "Visão de machine learning com coração, ação, café e pé no chão."
    novo, _ = apply_glossario(texto, _spec([ML]))
    assert novo == "Visão de aprendizado de máquina com coração, ação, café e pé no chão."
    # Byte-for-byte: the accented neighbors are the ORIGINAL code points.
    assert "coração".encode("utf-8") in novo.encode("utf-8")
    assert "café".encode("utf-8") in novo.encode("utf-8")


def test_zero_match_pair_yields_no_row_and_no_text_change() -> None:
    texto = "Nada a substituir aqui."
    novo, rows = apply_glossario(texto, _spec([("blockchain", "cadeia de blocos")]))
    assert novo == texto
    assert rows == []


def test_pairs_apply_in_file_order_and_each_hit_is_reported() -> None:
    spec = _spec([ML, ("data governance", "governança de dados")])
    novo, rows = apply_glossario(
        "machine learning e data governance — machine learning de novo.", spec
    )
    assert novo == (
        "aprendizado de máquina e governança de dados — aprendizado de máquina de novo."
    )
    assert rows == [
        {"de": ML[0], "para": ML[1], "ocorrencias": 2},
        {"de": "data governance", "para": "governança de dados", "ocorrencias": 1},
    ]


def test_regex_injection_in_pair_content_is_escaped_literal() -> None:
    # T-06-11: pair content is DATA — re.escape keeps ".*" literal.
    par = (".*", "tudo")
    novo, rows = apply_glossario("preço: .* por unidade", _spec([par]))
    assert novo == "preço: tudo por unidade"
    assert rows == [{"de": par[0], "para": par[1], "ocorrencias": 1}]


# ---------------------------------------------------------------------------
# load_glossario — the strict fail-fast ladder + fresh-read seam (D-12)
# ---------------------------------------------------------------------------


def test_load_real_shipped_glossario() -> None:
    spec = load_glossario()  # the real repo-root prompts/ dir
    assert spec.id == "glossario"
    assert len(spec.pares) >= 1  # seeded with real conservative pairs
    assert all(par.de.strip() and par.para.strip() for par in spec.pares)


def test_missing_glossario_names_path(tmp_path: Path) -> None:
    with pytest.raises(PromptError) as excinfo:
        load_glossario(prompts_dir=tmp_path)
    msg = excinfo.value.message_ptbr
    assert "não encontrado" in msg
    assert str(tmp_path / "glossario.md") in msg
    assert excinfo.value.raw


def test_invalid_yaml_names_file(tmp_path: Path) -> None:
    text = "---\nid: [unclosed\n  bad: {mixed\n---\n\nCorpo.\n"
    path = tmp_path / "glossario.md"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PromptError) as excinfo:
        load_glossario(prompts_dir=tmp_path)
    msg = excinfo.value.message_ptbr
    assert "YAML" in msg
    assert str(path) in msg
    assert excinfo.value.raw


def test_unexpected_extra_frontmatter_key_names_key_and_file(tmp_path: Path) -> None:
    meta = _valid_meta()
    meta["temperatura"] = 0.2  # a prompt-file key is NOT a glossário key
    path = _write_glossario(tmp_path, meta)
    with pytest.raises(PromptError) as excinfo:
        load_glossario(prompts_dir=tmp_path)
    msg = excinfo.value.message_ptbr
    assert "temperatura" in msg
    assert str(path) in msg
    assert excinfo.value.raw
    assert "Extra inputs are not permitted" not in msg  # no English prose in the UI path


def test_malformed_empty_pair_fails_before_the_substitution_engine(
    tmp_path: Path,
) -> None:
    # T-06-10: an empty `de` would match at every word boundary and corrupt
    # the whole text — the strict spec keeps the pair from ever loading.
    meta = {"id": "glossario", "pares": [{"de": "", "para": "qualquer"}]}
    _write_glossario(tmp_path, meta)
    with pytest.raises(PromptError) as excinfo:
        load_glossario(prompts_dir=tmp_path)
    assert str(tmp_path / "glossario.md") in excinfo.value.message_ptbr


def test_glossario_is_read_fresh_between_calls(tmp_path: Path) -> None:
    _write_glossario(tmp_path, _valid_meta())
    first = load_glossario(prompts_dir=tmp_path)
    assert first.pares[0].para == "aprendizado de máquina"

    mutated = _valid_meta()
    mutated["pares"][0]["para"] = "ML"  # the user edited the pair
    _write_glossario(tmp_path, mutated)

    second = load_glossario(prompts_dir=tmp_path)
    assert second.pares[0].para == "ML"  # fresh read, no cache (D-12)


def test_non_utf8_glossario_names_file(tmp_path: Path) -> None:
    path = tmp_path / "glossario.md"
    path.write_bytes(b"---\nid: glossario\n---\n\n\xe9 corrompido\n")
    with pytest.raises(PromptError) as excinfo:
        load_glossario(prompts_dir=tmp_path)
    assert "UTF-8" in excinfo.value.message_ptbr
    assert str(path) in excinfo.value.message_ptbr


# ---------------------------------------------------------------------------
# English-bleed detection — curated static list, one matcher (D-14)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("termo", EN_BLEED_TERMS)
def test_every_shipped_bleed_term_flags(termo: str) -> None:
    rows = detect_english_bleed(f"Ponto forte: {termo} — resultados medidos.", "sobre")
    assert {"termo": termo, "secao": "sobre"} in rows


@pytest.mark.parametrize("termo", ["track record", "team player", "i am"])
def test_bleed_matching_is_case_and_fold_insensitive(termo: str) -> None:
    assert {"termo": termo, "secao": "headline"} in detect_english_bleed(
        termo.upper() + " aqui", "headline"
    )
    assert {"termo": termo, "secao": "headline"} in detect_english_bleed(
        termo.title() + " aqui", "headline"
    )


def test_negative_ptbr_controls_do_not_flag() -> None:
    texto = (
        "Gerenciei times e liderei iniciativas com comunicação clara — se for "
        "necessário, ajusto o processo. Tenho experiência com ação, coração e "
        "avanço contínuo, e trabalho com método."
    )
    assert detect_english_bleed(texto, "sobre") == []
    # The curation proof: "for" is a real PT-BR verb ("se for necessário") —
    # shipping it would false-positive on every such sentence (dropped).
    assert "for" not in EN_BLEED_TERMS


def test_consolidated_tech_proper_nouns_do_not_flag() -> None:
    # Deliberate exclusion (D-14): consolidated tech terms are legitimate in
    # PT-BR tech writing — never bleed findings.
    texto = (
        "Automatizei pipelines de machine learning com Python, Kubernetes, "
        "Docker e SQL no dia a dia."
    )
    assert detect_english_bleed(texto, "headline") == []


def test_bleed_rows_carry_only_termo_and_secao() -> None:
    rows = detect_english_bleed("managed com sucesso", "sobre")
    assert rows and all(set(row) == {"termo", "secao"} for row in rows)


# ---------------------------------------------------------------------------
# run_linkedin_qa — the orchestration seam (order contract + language gate)
# ---------------------------------------------------------------------------


def _secoes(
    headline: str = "Engenheira de Dados — Python e SQL",
    sobre: str = "Sobre em português, dentro do limite.",
    descricao: str = "Liderei pipelines com impacto medido.",
    company: str = "Exemplo IA",
    habilidades: list[str] | None = None,
) -> dict:
    return {
        "headline": headline,
        "sobre": sobre,
        "experiencias": [
            {"company": company, "title": "Engenheira Sênior", "descricao": descricao}
        ],
        "habilidades": list(habilidades or ["Python", "SQL"]),
    }


def _tmp_prompts_dir(tmp_path: Path, pares: list[tuple[str, str]]) -> Path:
    _write_glossario(
        tmp_path,
        {"id": "glossario", "pares": [{"de": de, "para": para} for de, para in pares]},
    )
    return tmp_path


def test_ptbr_applies_glossary_to_prose_surfaces_and_reports(tmp_path: Path) -> None:
    prompts_dir = _tmp_prompts_dir(tmp_path, [ML])
    secoes = _secoes(sobre="Especialista em machine learning.", descricao="machine learning aplicado.")
    qa = run_linkedin_qa(secoes, "pt-BR", prompts_dir=prompts_dir)

    assert qa is not None
    # The report has one row per applied surface hit...
    assert [row["ocorrencias"] for row in qa["glossario"]] == [1, 1]
    assert {row["de"] for row in qa["glossario"]} == {ML[0]}
    # ...and the MUTATED secoes ARE the post-glossary text the user copies.
    assert secoes["sobre"] == "Especialista em aprendizado de máquina."
    assert secoes["experiencias"][0]["descricao"] == "aprendizado de máquina aplicado."
    assert qa["bleed"] == []


def test_bleed_runs_on_the_post_glossary_text(tmp_path: Path) -> None:
    # Research constraint #4: the glossário replaces the ONLY occurrence of a
    # bleed term — the report must stay empty, proving bleed detection ran
    # AFTER the substitution (had it run first/pre, it would flag "track record").
    prompts_dir = _tmp_prompts_dir(tmp_path, [("track record", "histórico comprovado")])
    secoes = _secoes(sobre="Tenho track record em dados.")
    qa = run_linkedin_qa(secoes, "pt-BR", prompts_dir=prompts_dir)

    assert qa is not None
    assert qa["glossario"] == [
        {"de": "track record", "para": "histórico comprovado", "ocorrencias": 1}
    ]
    assert secoes["sobre"] == "Tenho histórico comprovado em dados."
    assert qa["bleed"] == []


def test_surviving_bleed_terms_flag_with_their_surface(tmp_path: Path) -> None:
    prompts_dir = _tmp_prompts_dir(tmp_path, [ML])
    secoes = _secoes(
        sobre="machine learning com track record comprovado.",
        descricao="entreguei and otimizei pipelines.",
    )
    qa = run_linkedin_qa(secoes, "pt-BR", prompts_dir=prompts_dir)

    assert qa is not None
    # sobre row: labeled by the surface name...
    assert {"termo": "track record", "secao": "sobre"} in qa["bleed"]
    # ...experiência row: labeled by the entry's company (the fixed
    # profile-fact anchor the frontend renders as the sub-block header).
    assert {"termo": "and", "secao": "Exemplo IA"} in qa["bleed"]


def test_habilidades_flag_but_are_never_rewritten(tmp_path: Path) -> None:
    # Substituting inside a skill name would silently alter the deliverable
    # list — habilidades get bleed detection ONLY (the glossary pair matches
    # the skill text and still must NOT be applied).
    prompts_dir = _tmp_prompts_dir(tmp_path, [("track record", "histórico comprovado")])
    secoes = _secoes(habilidades=["track record em dados", "Python"])
    qa = run_linkedin_qa(secoes, "pt-BR", prompts_dir=prompts_dir)

    assert qa is not None
    assert secoes["habilidades"] == ["track record em dados", "Python"]  # untouched
    assert qa["glossario"] == []  # the pair never reached the skills list
    assert {"termo": "track record", "secao": "track record em dados"} in qa["bleed"]


def test_en_language_gate_returns_none_without_touching_anything(tmp_path: Path) -> None:
    # An EN run has NO glossário file at all — returning None proves the gate
    # short-circuits BEFORE the read (EN runs never touch the file).
    secoes = _secoes(sobre="Expert in machine learning.")
    qa = run_linkedin_qa(secoes, "en", prompts_dir=tmp_path)  # empty dir

    assert qa is None
    assert secoes["sobre"] == "Expert in machine learning."  # zero substitutions
    assert secoes["experiencias"][0]["descricao"] == "Liderei pipelines com impacto medido."


def test_clean_ptbr_run_is_a_loud_empty_payload(tmp_path: Path) -> None:
    # Zero substitutions + zero findings still carry BOTH keys — the frontend
    # renders loud zero lines; QA blocks are never silently absent (UI-SPEC).
    prompts_dir = _tmp_prompts_dir(tmp_path, [ML])
    qa = run_linkedin_qa(_secoes(), "pt-BR", prompts_dir=prompts_dir)
    assert qa == {"glossario": [], "bleed": []}


def test_real_shipped_glossario_flows_through_the_default_seam() -> None:
    # The default prompts_dir resolves at CALL time — the production path
    # reads the real git-versioned file fresh (soft assertions: user edits to
    # the shipped pairs must not break this vector).
    secoes = _secoes()
    qa = run_linkedin_qa(secoes, "pt-BR")
    assert qa is not None
    assert set(qa) == {"glossario", "bleed"}
    assert isinstance(qa["glossario"], list) and isinstance(qa["bleed"], list)
    assert secoes["headline"] and secoes["sobre"]  # valid post-QA text


def test_package_reexports_the_qa_surface() -> None:
    import app.linkedin as linkedin_pkg
    import app.linkedin.qa as qa_module

    assert linkedin_pkg.run_linkedin_qa is qa_module.run_linkedin_qa
    assert linkedin_pkg.EN_BLEED_TERMS is qa_module.EN_BLEED_TERMS
    assert linkedin_pkg.load_glossario is qa_module.load_glossario
    assert linkedin_pkg.apply_glossario is qa_module.apply_glossario
    assert linkedin_pkg.detect_english_bleed is qa_module.detect_english_bleed
