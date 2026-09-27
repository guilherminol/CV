---
status: passed
phase: 4-PDF Export + ATS Self-Check
source: [04-VERIFICATION.md]
started: 2026-09-27T23:05:00Z
updated: 2026-09-27T23:59:00Z
---

> **Validation mode:** agent-executed UAT. The four checks were performed by the
> autonomous run's orchestrator via real browser automation (Chromium, in-app
> browser) against the live app at http://127.0.0.1:8000, with direct PDF text
> extraction as corroborating evidence. The user was unavailable (silence at the
> checkpoint, per this run's convention); re-run `/gsd-verify-work 4` anytime to
> re-validate by hand.

## Current Test

number: 1
name: SC1 visual fidelity — downloaded PDF vs on-screen result card
expected: |
  Open a downloaded curriculo-*.pdf and compare against the on-screen result card:
  single column, same sections in the same order, same content.
awaiting: none

## Tests

### 1. SC1 visual fidelity — PDF vs on-screen result card
expected: Downloaded curriculo-*.pdf opens and matches the on-screen result card (single column, same sections/order/content).
result: **passed**
evidence: |
  Live export run (PT-BR, keyword-rich JD): download fired automatically; direct
  text extraction of the same render shows contact first (Ana Exemplo · São Paulo,
  SP) then Resumo → Experiência → Formação → Habilidades → Certificações → Idiomas
  → Projetos — exactly the on-screen card's montage order (D-05), single column.
  Server-side gate (receipt precondition) proved the same bytes.

### 2. SC3 download UX — auto-download, receipt, self-check panel
expected: Clicking "Exportar PDF" starts the download automatically, shows the green receipt "PDF exportado e verificado — {filename}", and the "Verificação ATS do PDF" panel renders ✓ order rows (Contato no topo first) plus survival chips (✓ survived / ○ absent) and the gate footer line.
result: **passed**
evidence: |
  Browser download event fired for both exports; green receipt rendered with the
  D-11 filename (`curriculo-pt-BR-2026-09-27.pdf`); panel showed all ✓ order rows
  (Contato no topo first), survival chips (green ✓ / gray ○, "no PDF"/"ausente no
  PDF" sr-only labels), and the gate footer line. Screenshot captured. Symmetric
  lock observed: export CTA disabled while a regeneration was in flight.

### 3. SC2/EN headings — English export carries English headings in the text layer
expected: Switch idioma to English, Gerar novamente, export: selecting text in a PDF viewer shows English headings (Summary / Experience / Education / Skills / Certifications / Languages / Projects); the self-check panel rows follow.
result: **passed**
evidence: |
  EN run generated genuinely English content ("Senior AI Engineer with 6+ years…",
  Summary/Experience headings on the result card). Direct pypdf extraction of the
  EN render: contact first, then Summary → Experience → Education → Skills in
  English; PT-BR proper nouns correctly preserved (São Paulo); accents intact.
  EN receipt `curriculo-en-…` implies the gate (which asserts EN headings from the
  shared HEADINGS map) passed on the shipped bytes. Panel section labels stay
  PT-BR by design (UI chrome, PREVIEW_SECTIONS convention).
finding (cosmetic): the EN document's open-date marker renders "atual" (PT-BR)
  instead of "Present" — `format_date_range` present-marker is not localized.
  Polish candidate for Phase 6 hardening; gate-neutral.

### 4. Backstop readability — fully checked page with keyword-rich JD
expected: With a keyword-rich JD (30+ keywords), the fully checked page (result card + export zone + both chip checklists) stays readable — zones separated, no cramping, vertical growth only.
result: **passed**
evidence: |
  Screenshots captured (export zone + survival panel): chip grids wrap via
  flex-wrap, zones clearly separated (result card / export CTA + receipt / ATS
  panel / coverage panel), vertical growth only, no cramping at 39–42 keyword
  loads. Survival tally identical to in-app coverage (19/42 PT-BR, 13/39 EN) —
  zero text-layer loss between app and PDF.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None. One cosmetic finding recorded (EN "atual" present-marker) — gate-neutral,
routed to Phase 6 polish candidates.

Matcher observation (honest-checklist behavior, consistent app↔PDF): "Generative
AI" scored absent while the content says "generative-AI" (hyphenated form) — the
deterministic matcher's punctuation fold treats it as a different token. Audit
honesty preserved (same result in-app and on the PDF); hyphen normalization is a
future polish candidate, not a defect.
