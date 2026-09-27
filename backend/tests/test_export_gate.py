"""Export gate + render tests (REVIEW-02/REVIEW-03, D-01/D-02/D-05/D-06) — offline.

Fixture strategy (04-RESEARCH Validation Architecture): session-scoped REAL
renders — the persona HTML goes through the actual engine (local Chromium,
~3s each, zero network) ONCE per language into module-level bytes; every gate
test consumes those bytes. If Chromium is missing the fixture FAILS LOUD with
the PT-BR setup hint inside the raised ExportError — never skip-silent.
Synthetic-text tests (via the pure check_extracted_text core) cover the
failure branches with zero browser involvement (test_coverage.py table style).

Assertion discipline: LOGICAL properties only (order, presence, co-occurrence)
— NEVER byte equality against a fixture (Chromium embeds timestamps).
Every D-08 PT-BR gate line is imported from gate.py — the message set lives
in exactly one place.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

from conftest import full_profile, minimal_profile
from app.export.errors import ExportError
from app.export.gate import (
    MSG_ACENTOS_CORROMPIDOS,
    MSG_CONTATO_FORA_DO_TOPO,
    ExpectedDoc,
    ExpectedExperience,
    check_extracted_text,
    msg_coocorrencia,
    msg_secao_fora_de_ordem,
    parse_back_check,
)
from app.export.pdf import _BROWSER_MISSING_PTBR, html_to_pdf
from app.export.render import (
    HEADINGS,
    build_resume_html,
    format_date_range,
    iter_rendered_strings,
    join_experience_dates,
    rendered_section_keys,
    section_keys,
)
from app.export.selfcheck import build_selfcheck
from app.llm.schemas import ExperienciaGerada, Keyword
from app.profile.models import Profile

EXPORT_DIR = Path(__file__).resolve().parents[1] / "app" / "export"
EMAIL = "ana.exemplo@example.com"

# --- Persona (conftest-shaped; deliberate PT-BR accents: São Paulo,
# Engenheira de Software Sênior, março de 2020) -------------------------------

PT_SUMMARY = (
    "Engenheira de Software Sênior com dez anos de atuação em sistemas "
    "distribuídos, base em São Paulo e foco em liderança técnica."
)
EN_SUMMARY = (
    "Senior Software Engineer with ten years building distributed systems, "
    "based in São Paulo and focused on technical leadership."
)
HABILIDADES = ["Python", "TypeScript", "FastAPI", "React", "Docker"]


@dataclass
class _Secoes:
    """The generated-sections payload shape (strict request model: plan 04-02)."""

    resumo: str
    experiencias: list[ExperienciaGerada]
    habilidades: list[str]


def _persona(idioma: str) -> tuple[Profile, _Secoes]:
    profile = Profile.model_validate(full_profile())
    if idioma == "pt-BR":
        secoes = _Secoes(
            resumo=PT_SUMMARY,
            experiencias=[
                ExperienciaGerada.model_validate(
                    {
                        "company": "Exemplo IA",
                        "title": "Engenheira de Software Sênior",
                        "bullets": [
                            "Implementou um pipeline RAG com avaliação automática.",
                            "Liderou a adoção de práticas de observabilidade desde março de 2020.",
                        ],
                    }
                )
            ],
            habilidades=HABILIDADES,
        )
    else:
        secoes = _Secoes(
            resumo=EN_SUMMARY,
            experiencias=[
                ExperienciaGerada.model_validate(
                    {
                        "company": "Exemplo IA",
                        "title": "Senior Software Engineer",
                        "bullets": [
                            "Implemented a RAG pipeline with automated evaluation.",
                            "Led observability practices since March 2020.",
                        ],
                    }
                )
            ],
            habilidades=HABILIDADES,
        )
    return profile, secoes


def _render_persona(idioma: str, persona: tuple[Profile, _Secoes] | None = None) -> bytes:
    profile, secoes = persona or _persona(idioma)
    datas = join_experience_dates(profile, secoes)
    html_doc = build_resume_html(profile, secoes, datas, idioma)
    return html_to_pdf(html_doc)


@pytest.fixture(scope="session")
def rendered_pdfs() -> dict[str, bytes]:
    """Both run languages rendered ONCE through the real engine (~6s total).

    Missing Chromium surfaces as ExportError here — the PT-BR install hint is
    the failure message (fail loud, never skip-silent).
    """
    return {idioma: _render_persona(idioma) for idioma in ("pt-BR", "en")}


def _full_expected_doc(
    idioma: str, persona: tuple[Profile, _Secoes] | None = None
) -> ExpectedDoc:
    """ExpectedDoc built from render.py outputs exactly as the route will in
    plan 04-02 — headings from THE shared HEADINGS map, dates from
    join_experience_dates, accent universe from iter_rendered_strings."""
    profile, secoes = persona or _persona(idioma)
    datas = join_experience_dates(profile, secoes)
    labels = HEADINGS[idioma]
    entry = secoes.experiencias[0]
    return ExpectedDoc(
        contact_tokens=(EMAIL,),
        headings=tuple(
            (key, labels[key])
            for key in rendered_section_keys(profile, secoes, datas, idioma)
        ),
        experiences=(
            ExpectedExperience(
                company=entry.company,
                title=entry.title,
                dates=format_date_range(*datas[0]),  # WR-01: per-entry join output
            ),
        ),
        accent_strings=tuple(iter_rendered_strings(profile, secoes, datas, idioma)),
    )


# --- Structural pins (engine seam, fold reuse, no-bytes-to-disk) -------------


def _export_sources() -> dict[Path, str]:
    return {
        path: path.read_text(encoding="utf-8")
        for path in sorted(EXPORT_DIR.glob("*.py"))
    }


def _imports_playwright(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "playwright" or alias.name.startswith("playwright.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and (
                node.module == "playwright" or node.module.startswith("playwright.")
            ):
                return True
    return False


def test_engine_seam_pdf_is_the_only_playwright_import() -> None:
    """D-01: every export module is browser-free except the one-function seam
    (join_experience_dates stays importable with zero browser machinery)."""
    for path, source in _export_sources().items():
        if path.name == "pdf.py":
            assert _imports_playwright(source), f"{path.name} must carry the engine seam"
        else:
            assert not _imports_playwright(source), f"{path.name} must not import playwright"


def test_gate_reuses_coverage_fold() -> None:
    """D-15 family: fold + lookaround pattern imported from app.resume.coverage,
    never re-implemented."""
    source = (EXPORT_DIR / "gate.py").read_text(encoding="utf-8")
    assert "from app.resume.coverage import _fold, _term_pattern" in source


def test_pdf_bytes_never_written_to_disk() -> None:
    """PDF bytes stay in memory: no open(..., \"wb\") anywhere in app/export/."""
    for path, source in _export_sources().items():
        assert '"wb"' not in source, f"{path.name} must never write bytes to disk"


# --- Template unit (pure — no browser) ---------------------------------------


def test_headings_map_covers_all_sections_in_render_order() -> None:
    """D-03/A2: HEADINGS is the single source — every section key, both
    languages, keys listed exactly in D-05 render order."""
    assert len(section_keys) == 7
    for lang in ("pt-BR", "en"):
        assert tuple(HEADINGS[lang].keys()) == section_keys
        assert all(HEADINGS[lang][key] for key in section_keys)


def test_render_html_escapes_hostile_strings() -> None:
    """V5.3/T-04-01: removing any escaping call site fails this test — the
    hostile payload can never reach the HTML as markup."""
    profile, secoes = _persona("pt-BR")
    secoes.experiencias[0].company = '<script>alert("x")</script> & cia <b>negrito</b>'
    html_doc = build_resume_html(profile, secoes, [], "pt-BR")
    assert "<script>" not in html_doc
    assert "<b>negrito</b>" not in html_doc
    assert "&lt;script&gt;" in html_doc
    assert "&amp; cia" in html_doc
    assert "&quot;" in html_doc  # quote=True


def test_render_html_full_montage_in_preview_order() -> None:
    """D-05: all 7 headings render in PREVIEW order for the full persona;
    the company join renders RAW stored strings ("2022-03 – atual" — Open
    Question 3); dateless-montage convention holds for the minimal persona."""
    profile, secoes = _persona("pt-BR")
    datas = join_experience_dates(profile, secoes)
    html_doc = build_resume_html(profile, secoes, datas, "pt-BR")
    positions = [html_doc.index(HEADINGS["pt-BR"][key]) for key in section_keys]
    assert positions == sorted(positions)
    assert "2022-03 – atual" in html_doc

    minimal = Profile.model_validate(minimal_profile())
    minimal_doc = build_resume_html(
        minimal,
        _Secoes(resumo="Resumo.", experiencias=[], habilidades=["Python"]),
        [],
        "pt-BR",
    )
    assert HEADINGS["pt-BR"]["formacao"] not in minimal_doc  # empty passthrough hidden
    assert HEADINGS["pt-BR"]["projetos"] not in minimal_doc


def test_rendered_section_keys_matches_template_hidden_sections() -> None:
    """CR-01: rendered_section_keys is THE single source the gate's heading
    expectations derive from — the full persona renders all 7 keys; a persona
    with EMPTY passthrough sections renders only the three generated ones,
    and build_resume_html confirms the hidden headings are truly absent from
    the HTML (template = truth, one traversal)."""
    profile, secoes = _persona("pt-BR")
    datas = join_experience_dates(profile, secoes)
    assert rendered_section_keys(profile, secoes, datas, "pt-BR") == section_keys

    for field in ("education", "certifications", "languages", "projects"):
        setattr(profile, field, [])
    datas = join_experience_dates(profile, secoes)
    assert rendered_section_keys(profile, secoes, datas, "pt-BR") == (
        "resumo",
        "experiencias",
        "habilidades",
    )
    html_doc = build_resume_html(profile, secoes, datas, "pt-BR")
    for key in ("formacao", "certificacoes", "idiomas", "projetos"):
        assert HEADINGS["pt-BR"][key] not in html_doc


def test_join_experience_dates_pure_and_accent_tolerant() -> None:
    """Open Question 1: strip+fold company join; unmatched entries are None
    (dateless render — no invented dates); one result element PER generated
    entry, in order. Pure: direct call, no browser."""
    profile, secoes = _persona("pt-BR")
    datas = join_experience_dates(profile, secoes)
    assert datas == [("2022-03", None)]

    secoes.experiencias[0].company = "exemplo ia "  # case/whitespace drift still joins
    assert join_experience_dates(profile, secoes) == [("2022-03", None)]

    secoes.experiencias[0].company = "Outra Empresa"  # unmatched → dateless
    assert join_experience_dates(profile, secoes) == [None]


def test_join_experience_dates_same_company_stints_map_positionally() -> None:
    """WR-01 regression: two profile stints at ONE company (career
    progression) map to the generated entries IN ORDER — each generated entry
    carries its OWN dates. The previous dict-by-company shape collapsed both
    entries onto the last stored range, silently printing the later stint's
    dates on the earlier entry (factually wrong, on a sendable document)."""
    raw = full_profile()
    raw["experiences"].append(
        {
            "company": "Exemplo IA",
            "title": {"pt-BR": "Analista de Software", "en": "Software Analyst"},
            "start_date": "2018-02",
            "end_date": "2022-02",
            "description": {"pt-BR": "Descrição de exemplo.", "en": "Example description."},
            "impacts": [],
        }
    )
    profile = Profile.model_validate(raw)
    secoes = _Secoes(
        resumo=PT_SUMMARY,
        experiencias=[
            ExperienciaGerada.model_validate(
                {
                    "company": "Exemplo IA",
                    "title": "Engenheira de Software Sênior",
                    "bullets": ["Implementou um pipeline RAG."],
                }
            ),
            ExperienciaGerada.model_validate(
                {
                    "company": "Exemplo IA",
                    "title": "Analista de Software",
                    "bullets": ["Automatizou relatórios."],
                }
            ),
        ],
        habilidades=HABILIDADES,
    )
    datas = join_experience_dates(profile, secoes)
    assert datas == [("2022-03", None), ("2018-02", "2022-02")]

    html_doc = build_resume_html(profile, secoes, datas, "pt-BR")
    assert "2022-03 – atual" in html_doc  # the senior stint's own range
    assert "2018-02 – 2022-02" in html_doc  # the analyst stint's own range


# --- Order-check failure branches (synthetic text — NO browser) ---------------

_ORDER_DOC = ExpectedDoc(
    contact_tokens=("ana@exemplo.com",),
    headings=(
        ("resumo", "Resumo"),
        ("experiencias", "Experiência"),
        ("habilidades", "Habilidades"),
    ),
)


@pytest.mark.parametrize(
    ("scenario", "text", "expected_erros"),
    [
        (
            "contato depois do primeiro título",
            "Resumo alfa Experiência beta Habilidades gama ana@exemplo.com",
            [MSG_CONTATO_FORA_DO_TOPO],
        ),
        (
            "títulos fora de ordem",
            "ana@exemplo.com Resumo alfa Habilidades gama Experiência beta",
            [msg_secao_fora_de_ordem("habilidades")],
        ),
        (
            "título ausente do PDF",
            "ana@exemplo.com Resumo alfa Experiência beta",
            [msg_secao_fora_de_ordem("habilidades")],
        ),
    ],
)
def test_order_failures(scenario: str, text: str, expected_erros: list[str]) -> None:
    """Each corruption shape fails LOUD with its exact D-08 PT-BR line."""
    result = check_extracted_text(text, _ORDER_DOC)
    assert result.ok is False, scenario
    assert result.erros_ptbr == expected_erros, scenario


# --- Co-occurrence + accent failure branches (synthetic text — NO browser) ----

_COOC_DOC = ExpectedDoc(
    contact_tokens=("ana@exemplo.com",),
    headings=(
        ("resumo", "Resumo"),
        ("experiencias", "Experiência"),
        ("habilidades", "Habilidades"),
    ),
    experiences=(
        ExpectedExperience(
            company="Exemplo IA",
            title="Engenheira de Software Sênior",
            dates="2022-03 – atual",
        ),
    ),
    accent_strings=("São Paulo, SP", "Engenheira de Software Sênior"),
)
_GOOD_TEXT = (
    "Ana Exemplo ana@exemplo.com · São Paulo, SP "
    "Resumo atuação da Ana em São Paulo. "
    "Experiência Exemplo IA · Engenheira de Software Sênior 2022-03 – atual "
    "Implementou um pipeline RAG. Habilidades Python, Docker"
)


@pytest.mark.parametrize(
    ("scenario", "text", "doc", "expected_ok", "expected_erros"),
    [
        (
            "empresa sem o cargo na janela",
            (
                "ana@exemplo.com Resumo alfa. Experiência Exemplo IA "
                "2022-03 – atual Habilidades Python"
            ),
            _COOC_DOC,
            False,
            [msg_coocorrencia("Exemplo IA")],
        ),
        (
            "entrada sem datas passa (graceful skip)",
            _GOOD_TEXT,
            ExpectedDoc(
                contact_tokens=_COOC_DOC.contact_tokens,
                headings=_COOC_DOC.headings,
                experiences=(
                    ExpectedExperience(
                        company="Exemplo IA",
                        title="Engenheira de Software Sênior",
                        dates=None,
                    ),
                ),
                accent_strings=_COOC_DOC.accent_strings,
            ),
            True,
            [],
        ),
        (
            "acento perdido reprova (espaço casefold-ONLY)",
            _GOOD_TEXT.replace("Sênior", "Senior"),
            _COOC_DOC,
            False,
            [MSG_ACENTOS_CORROMPIDOS],
        ),
        (
            "mojibake Ã+não-ASCII reprova (assinatura real: 'ão' → 'Ã£o')",
            _GOOD_TEXT.replace("São Paulo", "S\u00c3\u00a3o Paulo"),
            _COOC_DOC,
            False,
            [MSG_ACENTOS_CORROMPIDOS],
        ),
        (
            "Ã maiúsculo legítimo passa (SÃO PAULO no contato)",
            _GOOD_TEXT.replace("São Paulo", "SÃO PAULO"),
            _COOC_DOC,
            True,
            [],
        ),
        (
            "Ã final de palavra legítimo passa (MANHÃ)",
            f"{_GOOD_TEXT} Alinhamento marcado para a MANHÃ.",
            _COOC_DOC,
            True,
            [],
        ),
        (
            "U+FFFD reprova",
            f"{_GOOD_TEXT} \ufffd",
            _COOC_DOC,
            False,
            [MSG_ACENTOS_CORROMPIDOS],
        ),
        (
            "texto limpo passa (todas as checagens)",
            _GOOD_TEXT,
            _COOC_DOC,
            True,
            [],
        ),
    ],
)
def test_cooccurrence_and_accents(
    scenario: str,
    text: str,
    doc: ExpectedDoc,
    expected_ok: bool,
    expected_erros: list[str],
) -> None:
    result = check_extracted_text(text, doc)
    assert result.ok is expected_ok, f"{scenario}: {result.erros_ptbr}"
    assert result.erros_ptbr == expected_erros, scenario
    if expected_ok:
        assert result.coocorrencia and result.acentos, scenario


# --- Real-render gate (integration — local Chromium, offline) -----------------


@pytest.mark.parametrize("idioma", ["pt-BR", "en"])
def test_gate_passes_real_pdf(rendered_pdfs: dict[str, bytes], idioma: str) -> None:
    """SC2 complete (all four checks) on REAL Chromium exports in both run
    languages — the empirical D-02 verdict that embeds Playwright."""
    pdf_bytes = rendered_pdfs[idioma]
    assert pdf_bytes.startswith(b"%PDF")  # real PDF, in memory only
    result = parse_back_check(pdf_bytes, _full_expected_doc(idioma))
    assert result.contato_primeiro, result.raw
    assert result.ordem_titulos, result.raw
    assert result.coocorrencia, result.raw
    assert result.acentos, result.raw
    assert result.ok, result.raw


def test_gate_passes_real_pdf_with_uppercase_accented_contact() -> None:
    """CR-02 end-to-end (real Chromium): a profile storing its contact
    location in caps ("SÃO PAULO, SP" — common in Brazilian addresses)
    renders clean and PASSES all four checks — a legit uppercase Ã is never
    mojibake; the byte-perfect accent check still holds every rendered word
    (casefold-only space, accents REQUIRED)."""
    profile, secoes = _persona("pt-BR")
    profile.contact.location = "SÃO PAULO, SP"
    pdf_bytes = _render_persona("pt-BR", persona=(profile, secoes))
    result = parse_back_check(
        pdf_bytes, _full_expected_doc("pt-BR", persona=(profile, secoes))
    )
    assert result.acentos, result.raw
    assert result.ok, result.raw


def test_gate_short_circuits_on_shuffled_headings(rendered_pdfs: dict[str, bytes]) -> None:
    """A shuffled ExpectedDoc against a good PDF yields EXACTLY one heading
    line naming the out-of-order section (first-failure short-circuit, D-08)."""
    labels = HEADINGS["pt-BR"]
    shuffled = (
        ("habilidades", labels["habilidades"]),
        ("experiencias", labels["experiencias"]),
        ("resumo", labels["resumo"]),
    )
    expected = ExpectedDoc(contact_tokens=(EMAIL,), headings=shuffled)
    result = parse_back_check(rendered_pdfs["pt-BR"], expected)
    assert result.ok is False
    assert result.erros_ptbr == [msg_secao_fora_de_ordem("experiencias")]
    assert MSG_CONTATO_FORA_DO_TOPO not in result.erros_ptbr  # contact check passed


# --- Self-check payload over REAL extracted PDF text (plan 04-02) -------------


def _kw(canonical: str, **overrides) -> Keyword:
    """Keyword factory — schema defaults for pt/en/aliases unless overridden."""
    base: dict = {
        "canonical": canonical,
        "aliases": [],
        "pt": None,
        "en": None,
        "category": "competencias",
    }
    base.update(overrides)
    return Keyword.model_validate(base)


@pytest.mark.parametrize("idioma", ["pt-BR", "en"])
def test_survival_on_pdf_text(rendered_pdfs: dict[str, bytes], idioma: str) -> None:
    """Pinned Wave-0 seed: keyword survival over the REAL extracted PDF text,
    per language — the SAME Phase 3 matcher (zero new matching logic). The pt
    rendering survives on a pt-BR run, the en rendering wins on an en run
    (candidate order); an absent keyword carries termo None + status ausente;
    alias-only presence survives via the alias string; a zero-keyword list
    yields sobrevivencia == [] (the loud-zero line 04-03 consumes)."""
    gate = parse_back_check(rendered_pdfs[idioma], _full_expected_doc(idioma))
    assert gate.ok, gate.raw  # the 04-01 verdict — fixture sanity for this test
    assert gate.flat_text  # the normalized extraction rode the same GateResult

    titulo = _kw(
        "Engenheira de Software Sênior",
        pt="Engenheira de Software Sênior",
        en="Senior Software Engineer",
        category="titulos_de_vaga",
    )
    ausente = _kw("Kubernetes", pt="Kubernetes", en="Kubernetes", category="ferramentas")
    alias_only = _kw(
        "Contêineres",
        pt="Contêineres",  # absent from the PDF either way
        en="Containers",
        aliases=["Docker"],  # Docker renders in Habilidades — alias-only presence
        category="ferramentas",
    )

    zero = build_selfcheck(gate.flat_text, [], idioma, gate)
    assert zero["sobrevivencia"] == []

    selfcheck = build_selfcheck(gate.flat_text, [titulo, ausente, alias_only], idioma, gate)
    assert set(selfcheck) == {"ordem", "sobrevivencia", "gate"}
    sobrevivencia = selfcheck["sobrevivencia"]
    assert len(sobrevivencia) == 3
    for entry in sobrevivencia:  # structural honesty pin: NO aggregate field
        assert set(entry) == {"canonical", "category", "termo", "status"}
    assert sobrevivencia[0]["status"] == "coberto"
    assert sobrevivencia[0]["termo"] == (
        "Engenheira de Software Sênior" if idioma == "pt-BR" else "Senior Software Engineer"
    )
    assert sobrevivencia[1] == {
        "canonical": "Kubernetes",
        "category": "ferramentas",
        "termo": None,
        "status": "ausente",
    }
    assert sobrevivencia[2]["status"] == "coberto"
    assert sobrevivencia[2]["termo"] == "Docker"  # survived via the alias string


@pytest.mark.parametrize("idioma", ["pt-BR", "en"])
def test_ordem_rows_on_real_pdf(rendered_pdfs: dict[str, bytes], idioma: str) -> None:
    """Ordem rows (D-14): a leading contato row, then one row per exported
    section — ids from render.py's section_keys (the 04-03 label-mapping
    contract) — all ok=True on the real renders, in render order."""
    gate = parse_back_check(rendered_pdfs[idioma], _full_expected_doc(idioma))
    rows = gate.ordem_rows
    assert rows[0] == {"id": "contato", "ok": True}
    assert [row["id"] for row in rows[1:]] == list(section_keys)
    assert all(row["ok"] for row in rows), rows


def test_ordem_rows_record_partial_order_on_failure() -> None:
    """A FAILING gate still records what was found: rows before the failed
    key were found at monotonic positions (ok), the failed key and everything
    after it were not (ok=False) — honest partial order despite rejection."""
    labels = HEADINGS["pt-BR"]
    expected = ExpectedDoc(
        contact_tokens=(EMAIL,),
        headings=(
            ("resumo", labels["resumo"]),
            ("habilidades", labels["habilidades"]),  # asked BEFORE experiencias
            ("experiencias", labels["experiencias"]),
        ),
    )
    result = check_extracted_text(
        f"{EMAIL} Resumo alfa Experiência beta Habilidades gama", expected
    )
    assert result.ok is False
    assert result.erros_ptbr == [msg_secao_fora_de_ordem("experiencias")]
    assert result.ordem_rows == [
        {"id": "contato", "ok": True},
        {"id": "resumo", "ok": True},  # found at its monotonic position
        {"id": "habilidades", "ok": True},  # found (after resumo) — honest
        {"id": "experiencias", "ok": False},  # never found after habilidades
    ]


def test_ordem_rows_contato_row_false_on_contact_failure() -> None:
    """Contact-first failure: the contato row records ok=False while the
    section rows still record what the heading walk found."""
    result = check_extracted_text(
        "Resumo alfa ana@exemplo.com Experiência beta Habilidades gama", _ORDER_DOC
    )
    assert result.ok is False
    assert result.erros_ptbr == [MSG_CONTATO_FORA_DO_TOPO]
    assert result.ordem_rows[0] == {"id": "contato", "ok": False}
    assert [row["ok"] for row in result.ordem_rows[1:]] == [True, True, True]


def test_selfcheck_gate_footer_from_same_gate_result() -> None:
    """The footer booleans come from the PASSED-IN GateResult — a failing
    gate yields False footers; ordem passes through verbatim; the payload
    carries no score/ratio anywhere (counts-only honesty, D-15)."""
    failing = check_extracted_text("sem contato", _ORDER_DOC)
    assert failing.ok is False
    payload = build_selfcheck("texto qualquer", [], "pt-BR", failing)
    assert set(payload) == {"ordem", "sobrevivencia", "gate"}
    assert payload["gate"] == {"coocorrencia": False, "acentos": False}
    assert payload["ordem"] == failing.ordem_rows


# --- IN-01: html_to_pdf failure STAGE picks the PT-BR line (offline fakes) ----


class _FakeBrowser:
    """Launch succeeded; the render stage raises the stored error."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def new_page(self):
        raise self._error

    def close(self) -> None:
        pass


class _FakePlaywright:
    """sync_playwright() stand-in: configurable launch/render failures."""

    def __init__(self, launch_error: Exception | None = None, render_error: Exception | None = None):
        self._launch_error = launch_error
        self._render_error = render_error

    @property
    def chromium(self):
        return self

    def launch(self, headless: bool):
        if self._launch_error is not None:
            raise self._launch_error
        return _FakeBrowser(self._render_error)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_html_to_pdf_launch_failure_carries_install_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """IN-01 branch 1: a launch/executable-lookup failure (Chromium missing)
    keeps the actionable install hint as the envelope line; raw detail is
    terminal-only."""
    import app.export.pdf as pdf_module

    monkeypatch.setattr(
        pdf_module,
        "sync_playwright",
        lambda: _FakePlaywright(launch_error=RuntimeError("Executable doesn't exist")),
    )
    with pytest.raises(ExportError) as excinfo:
        pdf_module.html_to_pdf("<html></html>")
    assert excinfo.value.message_ptbr == _BROWSER_MISSING_PTBR
    assert "Executable doesn't exist" in excinfo.value.raw


def test_html_to_pdf_render_failure_gets_generic_retry_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """IN-01 branch 2: a RENDER-stage failure (set_content / page.pdf) no
    longer blames the browser install — the generic retry hint is the
    envelope line; the raw detail stays terminal-only."""
    import app.export.pdf as pdf_module

    monkeypatch.setattr(
        pdf_module,
        "sync_playwright",
        lambda: _FakePlaywright(render_error=RuntimeError("page crashed")),
    )
    with pytest.raises(ExportError) as excinfo:
        pdf_module.html_to_pdf("<html></html>")
    assert excinfo.value.message_ptbr != _BROWSER_MISSING_PTBR
    assert "install" not in excinfo.value.message_ptbr.lower()
    assert "page crashed" in excinfo.value.raw
