"""Parse-back gate (REVIEW-02/REVIEW-03, D-05/D-06/D-08) — pure checks over pypdf extraction.

The gate proves, on the PDF's own text layer and in both run languages, the
properties SC2 names: (1) contact first, (2) headings in render order, (3)
per generated experience company+title+dates co-occurring inside the
Experiências→next-heading window (dates skipped per entry when the profile
join found no match — no invented dates, ever), (4) accent integrity —
exhaustive over resume-size content: every non-ASCII word of every rendered
string found in the casefold-ONLY space (accent-SENSITIVE: "EXPERIÊNCIA"
matches "experiência", mojibake does not) plus mojibake sentinels (no U+FFFD,
no "Ã"/"â€" sequences). D-02 sequencing: the gate EXISTS before the engine is
trusted — the passing real-Chromium tests in tests/test_export_gate.py ARE
the empirical verdict that embeds Playwright; WeasyPrint stays installable
against this same gate.

Mechanics: plain-mode pypdf extraction (NEVER extraction_mode="layout" —
slower and whitespace-quirky; plain mode follows content-stream order =
reading order for single-column output). Whitespace is normalized ONCE
(re.sub(r"\\s+", " ")) before ALL position math (Pitfall 5). Order/heading
and window/co-occurrence comparisons run on the coverage fold — casefold +
NFKD — because the print pipeline can bake text-transform into the extracted
layer (the template ships none, but the fold keeps the checks robust). The
fold AND the lookaround term pattern are IMPORTED from app.resume.coverage,
never re-implemented (D-15 family determinism).

Fail behavior (D-08): the FIRST failing check short-circuits; its PT-BR line
lands in GateResult.erros_ptbr, the extracted text + which-word detail in
GateResult.raw (terminal-only — never an envelope field; the route side of
that split is plan 04-02). The D-08 message set lives EXACTLY in this module
— tests import the constants/functions, never restate the lines.
"""

import io
import re
from dataclasses import dataclass, field

from pypdf import PdfReader

from app.export.errors import ExportError
from app.resume.coverage import _fold, _term_pattern

# --- D-08 message set: each PT-BR gate line exists EXACTLY here. ------------
MSG_CONTATO_FORA_DO_TOPO = "Contato não encontrado no topo do PDF."
MSG_ACENTOS_CORROMPIDOS = "Acentos corrompidos na camada de texto do PDF."
MSG_EXTRACAO_FALHOU = "Não foi possível extrair o texto do PDF para verificação."


def msg_secao_fora_de_ordem(secao: str) -> str:
    """Check-2 line; names the section key (language-neutral identifier)."""
    return f"Seção {secao} fora de ordem no PDF."


def msg_coocorrencia(company: str) -> str:
    """Check-3 line; names the failing entry's company."""
    return f"Empresa, cargo ou datas não extraídos juntos para {company}."


# Mojibake sentinels (check 4b): U+FFFD replacement char, and the UTF-8→Latin-1
# byte-mangling leads "Ã" (e.g. "ão" → "Ã£o") / "â€" (e.g. "…" → "â€œ").
_MOJIBAKE_SENTINELS = ("\ufffd", "Ã", "â€")


@dataclass(frozen=True)
class ExpectedExperience:
    """Check-3 expectation for one generated experience entry.

    `dates` is the RENDERED range string (render.format_date_range) when the
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
    accent_strings: tuple[str, ...] = ()  # every rendered string (render.iter_rendered_strings)


@dataclass(frozen=True)
class GateResult:
    """D-08 split: envelope-safe PT-BR lines + terminal-only raw detail.

    The per-check booleans feed the selfcheck footer in the plan-04-02 export
    payload (research Pattern 4 "gate" block — checks the ordem panel does
    not show). A check not yet run is False; ok=True implies all True.

    Plan-04-02 additions — ONE gate pass feeds the WHOLE self-check payload
    (no second extraction, no divergent verdicts):
    - flat_text: the whitespace-normalized extraction — the exact text the
      survival matcher classifies (selfcheck.build_selfcheck input).
    - ordem_rows: {"id": "contato" | section key, "ok": bool} in render
      order, recorded during the heading walk. On a FAILING gate the rows
      still record what was found — a future UI could show partial order
      even though export rejects. Ids come from ExpectedDoc.headings keys,
      which the route builds from render.rendered_section_keys — one row per
      RENDERED section (CR-01: the template hides empty passthrough sections;
      D-03 single source).
    """

    ok: bool
    erros_ptbr: list[str]
    raw: str
    contato_primeiro: bool = False
    ordem_titulos: bool = False
    coocorrencia: bool = False
    acentos: bool = False
    flat_text: str = ""
    ordem_rows: list[dict] = field(default_factory=list)


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


def _ordem_rows(
    contato_ok: bool,
    positions: dict[str, int] | None,
    failed_key: str | None,
    headings: tuple[tuple[str, str], ...],
) -> list[dict]:
    """Ordem rows (plan 04-02): contato first, then one row per RENDERED
    section in order — ok=True when the heading was found at its monotonic
    position, False otherwise. When the scan failed at failed_key, every row
    BEFORE it was found monotonically; failed_key and the rows after it were
    not, and record ok=False — honest partial order, even on a rejected
    export. Pure: derived from the SAME walk as the check-2 verdict."""
    rows: list[dict] = [{"id": "contato", "ok": contato_ok}]
    if positions is None:
        seen_failure = False
        for key, _label in headings:
            if key == failed_key:
                seen_failure = True
            rows.append({"id": key, "ok": not seen_failure})
        return rows
    rows.extend({"id": key, "ok": True} for key, _label in headings)
    return rows


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
    # Heading positions are walked ONCE for BOTH the check-2 verdict and the
    # plan-04-02 ordem rows — one gate pass feeds the whole self-check
    # payload (no second extraction, no divergent verdicts).
    positions, failed_key = _scan_headings(folded, expected.headings)
    ordem_rows = _ordem_rows(contato_primeiro, positions, failed_key, expected.headings)

    if not contato_primeiro:
        return GateResult(
            ok=False,
            erros_ptbr=[MSG_CONTATO_FORA_DO_TOPO],
            raw=raw,
            contato_primeiro=False,
            flat_text=flat,
            ordem_rows=ordem_rows,
        )

    # --- Check 2: headings in render order ----------------------------------
    ordem_titulos = failed_key is None
    if not ordem_titulos:
        return GateResult(
            ok=False,
            erros_ptbr=[msg_secao_fora_de_ordem(failed_key)],
            raw=raw,
            contato_primeiro=True,
            ordem_titulos=False,
            flat_text=flat,
            ordem_rows=ordem_rows,
        )

    # --- Check 3: company+title+dates co-occurrence per experience ----------
    coocorrencia = True
    failing_company: str | None = None
    if expected.experiences and positions and "experiencias" in positions:
        window_start = positions["experiencias"]
        later = [pos for pos in positions.values() if pos > window_start]
        window_end = min(later) if later else len(folded)
        window = folded[window_start:window_end]
        for entry in expected.experiences:
            company_found = _term_pattern(entry.company).search(window)
            title_found = _term_pattern(entry.title).search(window)
            # Graceful skip: a dateless entry asserts company+title only.
            dates_found = entry.dates is None or _term_pattern(entry.dates).search(window)
            if not (company_found and title_found and dates_found):
                coocorrencia = False
                failing_company = entry.company
                break
    if not coocorrencia:
        return GateResult(
            ok=False,
            erros_ptbr=[msg_coocorrencia(failing_company or "")],
            raw=raw,
            contato_primeiro=True,
            ordem_titulos=True,
            coocorrencia=False,
            flat_text=flat,
            ordem_rows=ordem_rows,
        )

    # --- Check 4: accent integrity (casefold-ONLY space + mojibake sentinels)
    acentos, accent_detail = _check_accents(flat, expected.accent_strings)
    if not acentos:
        return GateResult(
            ok=False,
            erros_ptbr=[MSG_ACENTOS_CORROMPIDOS],
            raw=f"{raw}\n\n{accent_detail}",
            contato_primeiro=True,
            ordem_titulos=True,
            coocorrencia=True,
            acentos=False,
            flat_text=flat,
            ordem_rows=ordem_rows,
        )

    return GateResult(
        ok=True,
        erros_ptbr=[],
        raw=raw,
        contato_primeiro=True,
        ordem_titulos=True,
        coocorrencia=True,
        acentos=True,
        flat_text=flat,
        ordem_rows=ordem_rows,
    )


def _check_accents(flat: str, accent_strings: tuple[str, ...]) -> tuple[bool, str]:
    """(ok, raw_detail): every non-ASCII word of every rendered string must
    appear in the casefold-only space — accent-SENSITIVE, so one lost accent
    fails the gate — plus the mojibake sentinels. Exhaustive, never sampled;
    the failing word/string detail goes to GateResult.raw ONLY (D-08)."""
    casefolded = flat.casefold()
    for sentinel in _MOJIBAKE_SENTINELS:
        if sentinel in flat:
            return False, f"sentinela de mojibake encontrada no texto extraído: {sentinel!r}"
    for string in accent_strings:
        for word in string.split():
            if all(char.isascii() for char in word):
                continue
            if word.casefold() not in casefolded:
                return False, f"palavra acentuada ausente da camada de texto: {word!r} (string renderizada: {string!r})"
    return True, ""


def parse_back_check(pdf_bytes: bytes, expected: ExpectedDoc) -> GateResult:
    """Extract the PDF's text layer (pypdf plain mode) and run the SC2 checks."""
    return check_extracted_text(_extract_flat_text(pdf_bytes), expected)
