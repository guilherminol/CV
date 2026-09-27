"""Parse-back gate (REVIEW-02/REVIEW-03, D-05/D-06/D-08) — pure checks over pypdf extraction.

The gate proves, on the PDF's own text layer and in both run languages, the
properties SC2 names: (1) contact first, (2) headings in render order, (3)
per generated experience company+title+dates co-occurring (Task 2 of this
plan), (4) accent integrity (Task 2). D-02 sequencing: the gate EXISTS before
the engine is trusted — the passing real-Chromium tests in
tests/test_export_gate.py ARE the empirical verdict that embeds Playwright;
WeasyPrint stays installable against this same gate.

Mechanics: plain-mode pypdf extraction (NEVER extraction_mode="layout" —
slower and whitespace-quirky; plain mode follows content-stream order =
reading order for single-column output). Whitespace is normalized ONCE
(re.sub(r"\\s+", " ")) before ALL position math (Pitfall 5). Order/heading
comparisons run on the coverage fold — casefold + NFKD — because the print
pipeline can bake text-transform into the extracted layer (the template ships
none, but the fold keeps the check robust). The fold is IMPORTED from
app.resume.coverage, never re-implemented (D-15 family determinism).

Fail behavior (D-08): the FIRST failing check short-circuits; its PT-BR line
lands in GateResult.erros_ptbr, the extracted text + which-word detail in
GateResult.raw (terminal-only — never an envelope field; the route side of
that split is plan 04-02). The D-08 message set lives EXACTLY in this module
— tests import the constants/functions, never restate the lines.
"""

import io
import re
from dataclasses import dataclass

from pypdf import PdfReader

from app.export.errors import ExportError
from app.resume.coverage import _fold

# --- D-08 message set: each PT-BR gate line exists EXACTLY here. ------------
MSG_CONTATO_FORA_DO_TOPO = "Contato não encontrado no topo do PDF."
MSG_EXTRACAO_FALHOU = "Não foi possível extrair o texto do PDF para verificação."


def msg_secao_fora_de_ordem(secao: str) -> str:
    """Check-2 line; names the section key (language-neutral identifier)."""
    return f"Seção {secao} fora de ordem no PDF."


@dataclass(frozen=True)
class ExpectedExperience:
    """Check-3 expectation for one generated experience entry (Task 2).

    `dates` is the RENDERED range string (format_date_range) when the
    profile join matched, or None for a dateless entry — the gate then skips
    ONLY the date sub-check (company+title still asserted; no invented dates,
    ever — research Open Question 1 resolution).
    """

    company: str
    title: str
    dates: str | None = None


@dataclass(frozen=True)
class ExpectedDoc:
    """What the PDF must contain — built by the route (plan 04-02) from
    render.py outputs so template and gate can never drift apart."""

    contact_tokens: tuple[str, ...]  # email at minimum
    headings: tuple[tuple[str, str], ...]  # (section key, label) in render order
    experiences: tuple[ExpectedExperience, ...] = ()
    accent_strings: tuple[str, ...] = ()  # Task 2: every rendered string


@dataclass(frozen=True)
class GateResult:
    """D-08 split: envelope-safe PT-BR lines + terminal-only raw detail.

    The per-check booleans feed the selfcheck footer in the plan-04-02 export
    payload (research Pattern 4 "gate" block — checks the ordem panel does
    not show). A check not yet run is False; ok=True implies all True.
    """

    ok: bool
    erros_ptbr: list[str]
    raw: str
    contato_primeiro: bool = False
    ordem_titulos: bool = False
    coocorrencia: bool = False
    acentos: bool = False


def _extract_flat_text(pdf_bytes: bytes) -> str:
    """Plain-mode pypdf extraction over every page, whitespace-normalized ONCE.

    Extraction crashes (unreadable/corrupt PDF) raise ExportError — never a
    bare pypdf exception (D-08: PT-BR line + raw detail).
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ExportError(MSG_EXTRACAO_FALHOU, f"{type(exc).__name__}: {exc}") from exc
    return re.sub(r"\s+", " ", text)


def _scan_headings(
    folded: str, headings: tuple[tuple[str, str], ...]
) -> tuple[dict[str, int] | None, str | None]:
    """Sequential find: each heading at a monotonically increasing position.

    Returns ({key: position}, None) on success or (None, failing_key) on the
    first heading that is missing or appears out of order.
    """
    positions: dict[str, int] = {}
    cursor = 0
    for key, label in headings:
        pos = folded.find(_fold(label), cursor)
        if pos < 0:
            return None, key
        positions[key] = pos
        cursor = pos + len(_fold(label))
    return positions, None


def check_extracted_text(text: str, expected: ExpectedDoc) -> GateResult:
    """The SC2 checks over ALREADY-extracted text — pure, no pypdf, no browser.

    Split from parse_back_check so the failure-branch tests exercise every
    branch on synthetic text with zero browser involvement (fixture strategy,
    04-RESEARCH Validation Architecture).
    """
    flat = re.sub(r"\s+", " ", text)
    folded = _fold(flat)
    raw = flat  # terminal-only detail (D-08)

    # --- Check 1: contact first ---------------------------------------------
    tokens = [token for token in expected.contact_tokens if token]
    contato_primeiro = True
    if tokens:
        contact_positions = [folded.find(_fold(token)) for token in tokens]
        found = all(pos >= 0 for pos in contact_positions)
        if expected.headings:
            first_heading_pos = folded.find(_fold(expected.headings[0][1]))
            contato_primeiro = (
                found and first_heading_pos >= 0 and min(contact_positions) < first_heading_pos
            )
        else:
            contato_primeiro = found
    if not contato_primeiro:
        return GateResult(
            ok=False,
            erros_ptbr=[MSG_CONTATO_FORA_DO_TOPO],
            raw=raw,
            contato_primeiro=False,
        )

    # --- Check 2: headings in render order ----------------------------------
    positions, failed_key = _scan_headings(folded, expected.headings)
    ordem_titulos = failed_key is None
    if not ordem_titulos:
        return GateResult(
            ok=False,
            erros_ptbr=[msg_secao_fora_de_ordem(failed_key)],
            raw=raw,
            contato_primeiro=True,
            ordem_titulos=False,
        )

    # Checks 3 (co-occurrence) and 4 (accent integrity) land with Task 2.
    return GateResult(
        ok=True,
        erros_ptbr=[],
        raw=raw,
        contato_primeiro=True,
        ordem_titulos=True,
    )


def parse_back_check(pdf_bytes: bytes, expected: ExpectedDoc) -> GateResult:
    """Extract the PDF's text layer (pypdf plain mode) and run the SC2 checks."""
    return check_extracted_text(_extract_flat_text(pdf_bytes), expected)
