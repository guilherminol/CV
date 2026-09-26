---
status: testing
phase: 03-resume-vertical-slice
source: [.planning/phases/03-resume-vertical-slice/03-VERIFICATION.md]
started: 2026-09-26T23:10:00Z
updated: 2026-09-26T23:10:00Z
---

## Current Test

number: 1
name: Browser walkthrough of the Currículo screen (UI-SPEC zones, SC1–SC5 + backstop)
expected: |
  Start backend (cd backend && uv run uvicorn app.main:app --reload) + frontend; paste a real JD (>= 80 chars).
  Lint panel appears once the debounced JD reaches 80 chars (79 does not enable); avisos or green clear-line render verbatim;
  choose each language; generate — in-flight hint shows, then the result card with Gerado badges on
  resumo/experiência/habilidades and Do perfil badges on formação/certificações/idiomas/projetos + name/contact header;
  keywords grouped in the 4 fixed categories with green-✓/gray-○ chips and the plain tally line (NO numeric score);
  ephemeral notice above the card; Gerar novamente re-runs and replaces; a failed re-run keeps the prior result on screen;
  a 30+ keyword JD keeps the coverage panel readable (UI-SPEC backstop row).
awaiting: user response

## Tests

### 1. Browser walkthrough of the Currículo screen (UI-SPEC zones, SC1–SC5 + backstop)
expected: Lint panel gates at exactly 80 chars; both languages generate; Gerado/Do perfil badges on the right sections; keywords grouped in 4 fixed categories with ✓/○ chips and plain tally (no score); ephemeral notice; Gerar novamente re-runs; failed re-run keeps prior result; 30+ keyword JD stays readable.
result: [pending]

### 2. Live grounding + prose-quality read (`cd backend && uv run pytest -m llm -v`, spend)
expected: All 7 llm tests pass including both bilingual full-pipeline runs; generated PT-BR/EN sections read naturally, non-machine-translated; no invented numerals/technologies/dates (SC3, VALIDATION.md manual row).
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
