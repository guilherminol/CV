"""Export gate + render tests (REVIEW-02/REVIEW-03, D-01/D-02/D-05/D-06) — offline.

Fixture strategy (04-RESEARCH Validation Architecture): session-scoped REAL
renders — the persona HTML goes through the actual engine (local Chromium,
~3s each, zero network) ONCE per language into module-level bytes; every gate
test consumes those bytes. If Chromium is missing the fixture FAILS LOUD with
the PT-BR setup hint inside the raised ExportError — never skip-silent.
Synthetic-text tests (via the pure check_extracted_text core) cover the
failure branches with zero browser involvement.

Assertion discipline: LOGICAL properties only (order, presence, co-occurrence)
— NEVER byte equality against a fixture (Chromium embeds timestamps).
"""

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

from conftest import full_profile
from app.export.gate import (
    MSG_CONTATO_FORA_DO_TOPO,
    ExpectedDoc,
    msg_secao_fora_de_ordem,
    parse_back_check,
)
from app.export.pdf import html_to_pdf
from app.export.render import (
    HEADINGS,
    build_resume_html,
    section_keys,
)
from app.llm.schemas import ExperienciaGerada
from app.profile.models import Profile

EXPORT_DIR = Path(__file__).resolve().parents[1] / "app" / "export"
CORE_KEYS = ("resumo", "experiencias", "habilidades")  # tracer montage (Task 2 completes the rest)
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


def _render_persona(idioma: str) -> bytes:
    profile, secoes = _persona(idioma)
    html_doc = build_resume_html(profile, secoes, {}, idioma)
    return html_to_pdf(html_doc)


@pytest.fixture(scope="session")
def rendered_pdfs() -> dict[str, bytes]:
    """Both run languages rendered ONCE through the real engine (~6s total).

    Missing Chromium surfaces as ExportError here — the PT-BR install hint is
    the failure message (fail loud, never skip-silent).
    """
    return {idioma: _render_persona(idioma) for idioma in ("pt-BR", "en")}


def _core_expected_doc(idioma: str) -> ExpectedDoc:
    """Tracer ExpectedDoc: email + the 3 headings the tracer montage renders,
    labels taken from THE shared HEADINGS map (single source, D-03)."""
    labels = HEADINGS[idioma]
    return ExpectedDoc(
        contact_tokens=(EMAIL,),
        headings=tuple((key, labels[key]) for key in CORE_KEYS),
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
    """D-01: every export module is browser-free except the one-function seam."""
    for path, source in _export_sources().items():
        if path.name == "pdf.py":
            assert _imports_playwright(source), f"{path.name} must carry the engine seam"
        else:
            assert not _imports_playwright(source), f"{path.name} must not import playwright"


def test_gate_reuses_coverage_fold() -> None:
    """D-15 family: the fold is imported from app.resume.coverage, never re-implemented."""
    source = (EXPORT_DIR / "gate.py").read_text(encoding="utf-8")
    assert "from app.resume.coverage import _fold" in source


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
    html_doc = build_resume_html(profile, secoes, {}, "pt-BR")
    assert "<script>" not in html_doc
    assert "<b>negrito</b>" not in html_doc
    assert "&lt;script&gt;" in html_doc
    assert "&amp; cia" in html_doc
    assert "&quot;" in html_doc  # quote=True


def test_render_html_headings_follow_section_order() -> None:
    profile, secoes = _persona("pt-BR")
    html_doc = build_resume_html(profile, secoes, {}, "pt-BR")
    labels = HEADINGS["pt-BR"]
    assert (
        html_doc.index(labels["resumo"])
        < html_doc.index(labels["experiencias"])
        < html_doc.index(labels["habilidades"])
    )


# --- Real-render gate (integration — local Chromium, offline) -----------------


@pytest.mark.parametrize("idioma", ["pt-BR", "en"])
def test_gate_passes_real_pdf(rendered_pdfs: dict[str, bytes], idioma: str) -> None:
    """SC2 (partial — checks 1-2 this task) on a REAL Chromium export."""
    pdf_bytes = rendered_pdfs[idioma]
    assert pdf_bytes.startswith(b"%PDF")  # real PDF, in memory only
    result = parse_back_check(pdf_bytes, _core_expected_doc(idioma))
    assert result.contato_primeiro, result.raw
    assert result.ordem_titulos, result.raw
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
