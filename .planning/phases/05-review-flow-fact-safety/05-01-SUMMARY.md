---
phase: 05-review-flow-fact-safety
plan: 01
subsystem: resume-regeneration
tags: [regen, review-flow, fastapi, react, tracer]
requires:
  - Phase 2 gateway run_stage + _STAGE_SCHEMAS (untouched)
  - Phase 3 SECTION_STAGES pipeline + coverage matcher
  - Phase 4 ExportarSecoes displayed-state contract
provides:
  - POST /api/resume/regenerar (one-stage section regen, full merged secoes + recomputed coverage)
  - pipeline.run_section_regen + SECTION_STAGE_BY_ID
  - facts.compose_regen_stage_input (hint-as-DATA compose variant)
  - frontend regenerarSecao() + regenerar mutation + per-section action rows (Regenerar seção / Adicionar dica)
affects:
  - 05-02 (editor + version stack expand around the section action rows)
  - 05-03 (comparison panel joins the same GeneratedSection shell)
tech-stack:
  added: [] # zero new dependencies (D-01/D-06 mandate reuse)
  patterns:
    - house 200-envelope + raw-terminal-only (extended to /regenerar)
    - strict Pydantic request models reusing ExportarSecoes
    - wholesale displayed-state swap from response (no client-side merge)
    - export-state reset triple before every displayed-content mutation
key-files:
  created:
    - backend/tests/test_resume_regen_pipeline.py
    - backend/tests/test_resume_regen_api.py
  modified:
    - backend/app/resume/facts.py
    - backend/app/resume/pipeline.py
    - backend/app/routes/resume.py
    - backend/tests/test_resume_api.py
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/pages/CurriculoHome.tsx
    - frontend/src/components/ResumeResult.tsx
decisions:
  - "run_section_regen merges server-side and returns the FULL secoes — sibling byte-identity is a response-level property pinned by identity assertions (is) in tests"
  - "dica normalization lives at the compose boundary (compose_regen_stage_input): blank/None returns the plain base composition; gateway stays untouched (D-06/D-15)"
  - "frontend drops the dica KEY from the request body when empty (not dica: '') — extra=forbid hygiene (Pitfall 5)"
  - "regen success replaces resultado.secoes/cobertura/cobertura_resumo wholesale from the response; keywords/avisos/idioma keep the gerar-run values"
  - "full-gerar success resets per-section dica/dicaAberta/regenErros (UI-SPEC hint lifecycle: persists until cleared or the result is replaced)"
metrics:
  duration: 15 min
  completed: 2026-09-29
status: complete
actuals:
  tokens: 13400 # chars/4 over the realized diff (1194 line-changes)
  tasks: 3
  commits: 4 # MEASURED: git rev-list --count 2b96e0d..HEAD
plan_head_before: 2b96e0d8c4c056169a466decdbfb488a45cf5e1d
---

# Phase 5 Plan 01: Review Flow Tracer — One Section Regenerable End-to-End Summary

**One-liner:** POST /api/resume/regenerar reruns exactly ONE gateway stage per section and returns the full merged secoes + recomputed coverage, wired end-to-end to per-section "Regenerar seção" + on-demand "Adicionar dica" controls in the result card.

## What Was Built

Tracer slice for REVIEW-01's SC1 spine — the whole regeneration architecture proven on the phase's best early tokens:

- **Backend route** (`backend/app/routes/resume.py`): `RegenerarRequest` (extra=forbid; jd_text 80..20000, Literal language/secao, dica ≤500 defaulting to None, `secoes: ExportarSecoes` imported from routes/export, `keywords: list[Keyword] = []`) + `POST /api/resume/regenerar` as a PLAIN `def` handler with the house 200-envelope (`logger.error(raw)` terminal-only; `erros[]` = `message_ptbr.splitlines()`).
- **Pipeline** (`backend/app/resume/pipeline.py`): `SECTION_STAGE_BY_ID` built from `SECTION_STAGES` order + `run_section_regen()` — fresh `load_profile()` → `serialize_profile_facts` → `compose_regen_stage_input` → exactly one `run_stage(...)` → server-side merge over the SUBMITTED `ExportarSecoes` (siblings pass through by reference) → coverage recomputed over the FULL merged generated text → ok envelope `{status, idioma, secoes, cobertura, cobertura_resumo}`.
- **Compose variant** (`backend/app/resume/facts.py`): `compose_regen_stage_input(facts, jd_text, dica)` — blank/None returns the base composition unchanged; otherwise appends the `DICA DE DIRECIONAMENTO` block framed as user DATA bounded by the prompt's existing rules. Gateway, prompt files, and runs.jsonl untouched (D-05/D-06/D-15).
- **Offline test family** (Wave-0 RED seeds): `test_resume_regen_pipeline.py` (ScriptedClient recording create() kwargs — one-stage-per-regen for all 3 targets, hint in messages[1] only with messages[0] == `load_prompt(stage).body`, unchanged create() field set, hint absent from runs.jsonl, sibling identity `is`-asserted, merged-text coverage proof with cross-section keywords, blank-dica boundary) and `test_resume_regen_api.py` (ok envelope key set, erro envelope on scripted LLMError with caplog raw-terminal-only, broken-profile envelope, 7×422 strict validation, route presence). `test_resume_api.py` structural pins (sync-def, router-before-mount) learned `/api/resume/regenerar`.
- **Frontend** (`client.ts`, `constants/ui.ts`, `CurriculoHome.tsx`, `ResumeResult.tsx`): typed `RegenerarRequest`/`RegenerarResponse` + `regenerarSecao()` (dica key omitted from the body when empty); `regenerar` mutation whose ok branch runs the THREE export-state clears BEFORE swapping `secoes`/`cobertura`/`cobertura_resumo` wholesale from the response (no client-side merge); per-section dica/toggle/error state; `GeneratedSection` action rows on the 3 generated sections only (quiet "Adicionar dica" toggle revealing the labeled hint input, compact secondary "Regenerar seção" with in-flight label swap, sibling-reassurance in-flight line inside the shared aria-live region, section-scoped red error panel with backend `erros[]` verbatim); passthrough "Do perfil" sections untouched; symmetric locks extended (form CTA, Exportar CTA, header button) to the regen flight.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Wave-0 test seeds — offline regen test family (RED) | 0d2c8a1 | backend/tests/test_resume_regen_pipeline.py (new), backend/tests/test_resume_regen_api.py (new), backend/tests/test_resume_api.py |
| 2 | Backend tracer — compose_regen_stage_input + run_section_regen + POST /api/resume/regenerar (GREEN) | 16cd728 | backend/app/resume/facts.py, backend/app/resume/pipeline.py, backend/app/routes/resume.py |
| 3 | Frontend tracer — regenerarSecao client + mutation + per-section wiring | be0966c | frontend/src/api/client.ts, frontend/src/constants/ui.ts, frontend/src/pages/CurriculoHome.tsx, frontend/src/components/ResumeResult.tsx |
| — | Rule-1 test fix (Task 2 verify follow-up) | 9965a0e | backend/tests/test_resume_regen_pipeline.py |

## Verification Results

- `cd backend && uv run pytest tests/test_resume_regen_pipeline.py tests/test_resume_regen_api.py tests/test_resume_api.py -q` → **41 passed** (RED state first confirmed: every pre-implementation failure was an ImportError on the missing symbols or the missing route)
- `cd backend && uv run pytest -q` (full offline suite) → **259 passed, 7 deselected** (232 baseline + 27 new; zero regressions)
- `cd frontend && npm run build` (tsc -b drift gate) → **green in 1.14s**
- D-15 grep: routes/resume.py logging additions = the single raw-detail `logger.error` line only — no hint/section text anywhere in logs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test-side model_dump call on JSON-parsed dicts**
- **Found during:** Task 2 (verify run)
- **Issue:** In `test_siblings_byte_identical_only_target_replaced[experiencias]`, the expected value called `.model_dump()` on plain dicts parsed from the canned JSON (AttributeError) — a test authoring bug, not an implementation gap.
- **Fix:** Expected value is now the plain parsed list (`json.loads(NEW_EXPERIENCIAS_CONTENT)["experiencias"]`).
- **Files modified:** backend/tests/test_resume_regen_pipeline.py
- **Commit:** 9965a0e

No other deviations — plan executed as written.

## Auth Gates

None — fully offline execution, no credentials touched.

## Known Stubs

None — every control is wired to the real endpoint; no placeholder data paths.

## Notes for 05-02 / 05-03

- `GeneratedSection` (ResumeResult.tsx) is the shell to extend: the UI-SPEC anatomy slots (editor textarea, comparison panel, versions panel, amber confirm strips) hang between the action row and the section content.
- The per-section UI state atoms (dicas/dicaAberta/regenErros) and the mutate/dispatch pattern in CurriculoHome are the template for editor + versions state; `regenErros` uses key-absence = no-error.
- The version-stack helper (D-08/SC4, stack-before-mutate) does NOT exist yet — regen success currently replaces the displayed section without stacking (per this plan's scope); 05-02 must add `empilharVersaoAtual` to every destructive path INCLUDING regen success.

## Self-Check: PASSED

- Files exist: all 9 key-files verified present on disk (3 created/6 modified per the commit manifests)
- Commits exist: 0d2c8a1, 16cd728, be0966c, 9965a0e in `git log` (4 measured from ledger 2b96e0d..HEAD)
- Clean tree: no uncommitted source changes remain (only pre-existing .planning/ orchestrator state, committed separately below)
