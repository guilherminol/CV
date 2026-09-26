---
status: testing
phase: 01-foundation-scaffold-master-profile
source: [01-VERIFICATION.md]
started: 2026-09-25T22:10:00-03:00
updated: 2026-09-25T22:10:00-03:00
---

## Current Test

number: 1
name: SC1/SC3 browser smoke (prod mode)
expected: |
  PT-BR shell with header/nav, 'Perfil carregado' status, amber 'Dados de exemplo' banner,
  7-section completeness grid, resume-style preview of Ana Exemplo (3 experiences, skills, projects).
awaiting: user response

## Tests

### 1. SC1/SC3 browser smoke (prod mode; steps scripted in README 'Phase 1 smoke check')
expected: |
  PT-BR shell with header/nav, 'Perfil carregado' status, amber 'Dados de exemplo' banner,
  7-section completeness grid, resume-style preview of Ana Exemplo (3 experiences, skills, projects).
  Steps: npm run build, cd backend && uv run uvicorn app.main:app, open http://127.0.0.1:8000.
  Optionally repeat via the dev flow (two terminals) at http://127.0.0.1:5173.
result: [pending]

### 2. Broken-profile UI round-trip
expected: |
  Red ErrorPanel names the exact file and key in PT-BR; app stays up (no crash/500 screen);
  terminal shows the raw technical detail; restore returns the healthy home without restart.
  Steps: rename a key in content/profile.md, refresh http://127.0.0.1:8000; check the uvicorn
  terminal; restore the file and refresh again.
result: [pending]

### 3. Edit-refresh freshness (D-15)
expected: |
  New value appears after browser refresh with no server restart.
  Steps: change a visible value in content/profile.md while the server runs, refresh, then restore.
result: [pending]

### 4. Preview base-language check (D-04)
expected: |
  No English-only rendering of localized fields, no raw language-map JSON in the page —
  every localized field in the preview shows the pt-BR value.
result: [pending]

### 5. Flagged prohibition review (3 judgment-tier prohibitions)
expected: |
  Confirmations match the code evidence: (a) config.py reads OPENROUTER_API_KEY tolerantly with
  empty default and no other reference exists (app starts without it, never calls it);
  (b) zero write/open calls to content/ in backend/app; (c) PlaceholderBanner and App.tsx contain
  no onClick/button/dismiss and the client only GETs (no UI control over the example flag).
  Confirm or reject the LLM-judge PASS verdicts.
result: [pending]

### 6. Package legitimacy spot-check (plan-01 T-01-SC end-of-phase human-check)
expected: |
  Maintainers/repos match the 01-RESEARCH.md Package Legitimacy Audit Source Repo column; no
  package gained install scripts. Spot-check npmjs.com / pypi.org for the pinned versions:
  react 19.3.0, vite 8.3.1, @tanstack/react-query 5.103.2, tailwindcss 4.3.3, fastapi 0.141.1,
  uvicorn 0.54.0, pydantic 2.13.5, python-frontmatter 1.3.0, python-dotenv 1.2.3, pytest 9.1.1,
  httpx 0.28.1.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
