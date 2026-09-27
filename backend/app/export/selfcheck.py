"""Self-check payload builder (REVIEW-03, D-14/D-15) — pure functions.

build_selfcheck composes the export response's "selfcheck" block from ONE
GateResult — the SAME pass the delivery decision used (no second extraction,
no divergent verdicts):

- "ordem": gate.ordem_rows verbatim — {"id": ..., "ok": bool} rows, contato
  first, then one row per exported section in render order; ids come from
  the route's ExpectedDoc (render.rendered_section_keys — one row per
  RENDERED section; an empty passthrough section is template-hidden and
  never listed — CR-01, D-03 single source). The frontend maps ids to
  labels and renders UNKNOWN ids raw — never silently dropped (D-14; the
  normative id set is "contato" + the rendered sections).
- "sobrevivencia": classify_coverage(keywords, pdf_text, idioma) VERBATIM —
  the SAME deterministic Phase 3 matcher (canonical OR alias, case/
  punctuation-insensitive, run-language candidate order — D-15 locked reuse,
  zero new matching logic here). INPUT DIFFERENCE vs Phase 3, documented in
  coverage.py's module docstring: Phase 3 classifies over the 3 GENERATED
  sections only, while HERE the input is the FULL extracted PDF text
  including passthrough sections — D-15 audits the PDF, the sendable
  artifact, so a certification keyword that only survives via a passthrough
  section is honestly "coberto" on the export.
- "gate": {"coocorrencia": bool, "acentos": bool} — the two D-06 checks the
  ordem block does not show, surfaced as the panel's footer guarantee; the
  booleans are read from the PASSED-IN GateResult.

Honesty rule (REQUIREMENTS Out of Scope, D-15): counts only. Consumers
derive survived/total from the sobrevivencia list itself (status "coberto"
vs "ausente"); the payload carries NO aggregate ratio, numeric ATS score,
percentage, or meter — and no LLM judge enters any verdict.
"""

from app.export.gate import GateResult
from app.llm.schemas import Keyword
from app.resume.coverage import classify_coverage


def build_selfcheck(
    pdf_text: str, keywords: list[Keyword], idioma: str, gate: GateResult
) -> dict:
    """Compose {ordem, sobrevivencia, gate} — pure, no browser, no LLM.

    pdf_text: the gate's flat_text (whitespace-normalized extraction).
    keywords: the run's extracted keywords — an EMPTY list is legitimate and
    yields sobrevivencia == [] (the loud-zero line the frontend consumes).
    idioma: the run language — drives the matcher's candidate order (kw.pt
    for pt-BR, kw.en otherwise).
    gate: the SAME GateResult the delivery decision used.
    """
    return {
        "ordem": gate.ordem_rows,
        "sobrevivencia": classify_coverage(keywords, pdf_text, idioma),
        "gate": {"coocorrencia": gate.coocorrencia, "acentos": gate.acentos},
    }
