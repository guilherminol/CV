---
phase: "06"
plan: "01"
subsystem: linkedin-module
tags: [linkedin, llm-gateway, wire-schema, fastapi, react, tracer]
requires:
  - Phase 2 LLM gateway (run_stage, _STAGE_SCHEMAS, runs.jsonl contract D-10/D-13)
  - Phase 3 resume pipeline pattern (facts serialization, all-or-nothing, injectable client)
  - Phase 5 frontend page pattern (CurriculoHome: profile gate, wholesale swap)
provides:
  - linkedin-headline stage end-to-end (gateway → prompt → pipeline → route → page)
  - backend LINKEDIN_* config constants (220/2600/2000/100, objetivo 80..2000)
  - 4 drift-locked LinkedIn wire schemas + models (headline, sobre, experiencias, skills)
  - app/linkedin/ package (run_linkedin_pipeline, compose_linkedin_stage_input)
  - POST /api/linkedin/gerar (200-envelope, strict request)
  - frontend LinkedIn page skeleton + CharacterCounter component + gerarLinkedin client
affects:
  - 06-02 (registers the 3 remaining stages with their prompt files; expands the pipeline quartet)
  - 06-03..06-05 (QA panel, regen, remaining result blocks extend the pinned envelope additively)
tech-stack:
  added: []
  patterns:
    - stage registration = one _STAGE_SCHEMAS entry (gateway untouched, D-09)
    - asymmetric bounds — Field bounds on inputs, NONE on LLM-layer outputs (D-07)
    - 200-envelope fail-loud with raw detail terminal-only (T-06-04)
    - wholesale result swap + verbatim erro lines (D-11)
key-files:
  created:
    - backend/app/linkedin/__init__.py
    - backend/app/linkedin/pipeline.py
    - backend/app/routes/linkedin.py
    - prompts/linkedin-headline.md
    - backend/tests/test_linkedin_schema.py
    - backend/tests/test_linkedin_pipeline.py
    - backend/tests/test_linkedin_api.py
    - frontend/src/pages/LinkedInHome.tsx
    - frontend/src/components/CharacterCounter.tsx
  modified:
    - backend/app/config.py
    - backend/app/llm/schemas.py
    - backend/app/llm/gateway.py
    - backend/app/main.py
    - frontend/src/constants/ui.ts
    - frontend/src/App.tsx
    - frontend/src/api/client.ts
decisions:
  - Empty/blank generated headline raises LLMError in the pipeline (loud contract) — an empty block can never render or swap into displayed state.
  - Only linkedin-headline is registered in _STAGE_SCHEMAS (tracer minimal surface); the other 3 wire schemas/models are drift-locked now but register with their prompt files in 06-02.
  - CharacterCounter takes pure numeric props and exports pure formatter/class functions (house no-JS-test-runner policy keeps them offline-testable).
  - Objetivo hint copy keeps {min}/{max}/{excesso} interpolation slots with plain template replace (house pattern).
  - Gerar error hint/retry and the ephemeral notice reuse the Currículo constants verbatim (UI-SPEC "reused" rows) instead of LINKEDIN_ duplicates.
metrics:
  duration: 16 min
  completed: 2026-09-29
actuals:
  tokens: 18346 # chars/4 over the realized diff (73382 diff chars)
  tasks: 3
  commits: 3 # measured: git rev-list --count 703d367..HEAD
plan_head_before: 703d3670f21ecc5bdb81b459cf45b99c6fa77a17
status: complete
---

# Phase 6 Plan 1: LinkedIn Tracer Slice Summary

**One-liner:** linkedin-headline generated end-to-end offline — gateway stage + strict wire schema (no length bounds, D-07) + PT-BR prompt + `app/linkedin/` pipeline with loud empty-guard and `{limite,tamanho,excesso}` envelope + `POST /api/linkedin/gerar` + LinkedIn page skeleton with live counter and Copiar — with all four LinkedIn wire schemas drift-locked and oversize-safe before any expansion wave.

## What Was Built

- **Wave-0 contract (Tasks 1-2):** the four LinkedIn LLM-layer models (`LinkedinHeadline`, `LinkedinSobre`, `ExperienciaLinkedin`/`LinkedinExperiencias`, `LinkedinSkills`) with plain `str` fields — NO per-field length bounds — each hand-maintained strict wire schema drift-locked to its model in `test_linkedin_schema.py` (23 tests), including oversize guards (500-char headline, 3000-char sobre, 2500-char descricao, 150-item habilidades all validate cleanly). Only `linkedin-headline` is registered in `_STAGE_SCHEMAS`; a pin test keeps the registration surface minimal until 06-02.
- **Backend tracer (Task 1):** Phase 6 config constants with recorded confidence notes (220/2600/2000 MEDIUM cross-source consensus — official silence documented; skills=100 HIGH official; objetivo 80..2000). `run_linkedin_pipeline` composes FATOS DO PERFIL + OBJETIVO DE CARREIRA as user-message DATA (T-06-01), raises `LLMError` on empty/blank headline, and returns the final envelope `{idioma, secoes, limites}` with code-unit counts. `POST /api/linkedin/gerar`: sync def, strict request (`extra="forbid"`), 200-envelope, raw detail terminal-only, router before the SPA mount.
- **Frontend tracer (Task 3):** LinkedIn nav enabled; `LinkedInHome` mirrors the CurriculoHome pattern (profile gate verbatim, objetivo textarea with WR-01 mirrors, idioma segmented control reused verbatim, gated CTA); gerar mutation swaps the result wholesale; headline block with `Copiar` first (`navigator.clipboard.writeText` of the exact displayed text, `Copiado!` ~2 s with `aria-live="polite"`, failure line persisting until the next successful copy), `CharacterCounter` (gray / amber ≥90% / red over), and the red over-limit flag — nothing ever truncated (D-07).

## Tasks Completed

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | Tracer — linkedin-headline end-to-end (constants, stage, pipeline, route) | 3816e68 |
| 2 | Wave-0 contract — remaining 3 stage models + wire schemas + drift lock | 6fa14cf |
| 3 | Tracer frontend — LinkedIn page skeleton rendering the headline block | 9a83092 |

## Verification

- `cd backend && uv run pytest -q` → **309 passed, 7 deselected** (267 baseline + 42 new; suite stays 100% offline — ScriptedClient/fakes only)
- `cd frontend && npm run build` → **green** (tsc -b drift gate)
- Tracer feedback gate re-run after Task 1 commit: 27 tracer tests green end-to-end; `git grep "linkedin-headline" backend/app/llm/gateway.py` returns exactly one registration line → `⚡ Tracer verified end-to-end — expanding`
- Manual smoke (dev servers: LinkedIn nav → objetivo ≥80 → Gerar → headline + counter; sub-80 keeps CTA disabled) is deferred to the phase's end-of-phase human verification per `human_verify_mode: end-of-phase`

## Deviations from Plan

None — plan executed exactly as written. (Two mechanical test-authoring fixes during Task 2 — a pytest parametrize arity mismatch and an assertion branch for the flat `ExperienciaLinkedin` dump shape — were fixed before commit; no behavior change.)

## Known Stubs

| Stub | File | Reason | Resolved by |
| ---- | ---- | ------ | ----------- |
| The result card renders ONLY the Headline block while the in-flight hint (UI-SPEC-pinned final copy) says "Quatro blocos são gerados em sequência" | frontend/src/pages/LinkedInHome.tsx | Intentional tracer scope — the plan's objective is the ONE-block proven slice; the pipeline/route envelope keys are already final so later waves extend additively | 06-02 (full quartet), 06-03..06-05 (remaining blocks, QA panel, regen) |

## Self-Check: PASSED

- Created files verified on disk (9 created, 7 modified — all in the task file lists).
- Commits verified in git log: 3816e68, 6fa14cf, 9a83092.
- `git rev-list --count 703d367..HEAD` = 3 (matches the commits ledger; no uncommitted code changes).
