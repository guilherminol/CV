---
status: testing
phase: 4-PDF Export + ATS Self-Check
source: [04-VERIFICATION.md]
started: 2026-09-27T23:05:00Z
updated: 2026-09-27T23:05:00Z
---

## Current Test

number: 1
name: SC1 visual fidelity — downloaded PDF vs on-screen result card
expected: |
  Open a downloaded curriculo-*.pdf and compare against the on-screen result card:
  single column, same sections in the same order, same content.
awaiting: user response

## Tests

### 1. SC1 visual fidelity — PDF vs on-screen result card
expected: Downloaded curriculo-*.pdf opens and matches the on-screen result card (single column, same sections/order/content).
result: [pending]

### 2. SC3 download UX — auto-download, receipt, self-check panel
expected: Clicking "Exportar PDF" starts the download automatically, shows the green receipt "PDF exportado e verificado — {filename}", and the "Verificação ATS do PDF" panel renders ✓ order rows (Contato no topo first) plus survival chips (✓ survived / ○ absent) and the gate footer line.
result: [pending]

### 3. SC2/EN headings — English export carries English headings in the text layer
expected: Switch idioma to English, Gerar novamente, export: selecting text in a PDF viewer shows English headings (Summary / Experience / Education / Skills / Certifications / Languages / Projects); the self-check panel rows follow.
result: [pending]

### 4. Backstop readability — fully checked page with keyword-rich JD
expected: With a keyword-rich JD (30+ keywords), the fully checked page (result card + export zone + both chip checklists) stays readable — zones separated, no cramping, vertical growth only.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
