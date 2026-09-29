---
phase: "06"
plan: "02"
subsystem: linkedin-module
tags: [linkedin, llm-gateway, pipeline, fastapi, regen, lint]
requires:
  - 06-01 tracer slice (linkedin-headline stage, wire schemas, gerar route, config constants)
  - Phase 2 gateway run_stage + _STAGE_SCHEMAS (untouched mechanics)
  - Phase 5 regen semantics (one stage, merge over submitted state, compose dica framing)
provides:
  - linkedin-sobre / linkedin-experiencias / linkedin-skills gateway stages + PT-BR prompt files (D-09 quartet complete)
  - run_linkedin_pipeline full quartet: D-09 order, loud-empty guards, profile-order experiências alignment (fold-match + all-entries fallback), skills dedupe (no sort), full limites block
  - run_linkedin_section_regen + SECTION_STAGE_BY_ID (one stage per regen, byte-identical siblings)
  - app/linkedin/models.py LinkedinSecoes (submitted displayed-state model, route+pipeline shared)
  - facts.append_dica_block — the input-agnostic dica framing shared by resume + LinkedIn regen composes
  - POST /api/linkedin/lint (verbatim run_lint_only reuse) + POST /api/linkedin/regenerar
affects:
  - 06-03 (frontend quartet blocks + lint avisos build against the complete test-pinned envelope)
  - 06-04/06-05 (QA panel payload joins the same envelope additively; bilingual DoD harness drives the quartet)
tech-stack:
  added: []
  patterns:
    - stage registration = one _STAGE_SCHEMAS entry (gateway untouched, D-09)
    - loud-empty per block; empty habilidades fails only when the profile HAS skills
    - profile-order alignment via coverage _fold first-unused-match + wholesale returned-order fallback
    - dedupe fold-match first-occurrence-wins — no sort anywhere (returned order IS priority)
    - merge over SUBMITTED state, siblings by reference (Phase 5 SC1 semantics)
key-files:
  created:
    - prompts/linkedin-sobre.md
    - prompts/linkedin-experiencias.md
    - prompts/linkedin-skills.md
    - backend/app/linkedin/models.py
    - backend/tests/test_linkedin_regen_pipeline.py
  modified:
    - backend/app/llm/gateway.py
    - backend/app/linkedin/pipeline.py
    - backend/app/routes/linkedin.py
    - backend/app/resume/facts.py
    - backend/tests/test_linkedin_pipeline.py
    - backend/tests/test_linkedin_schema.py
    - backend/tests/test_linkedin_api.py
decisions:
  - Experiências alignment = fold-match each profile company to the first UNUSED returned entry (same-company entries each consume one distinct entry, never collide); ANY failed pairing flips the WHOLE alignment to returned-order positional fallback (UI-SPEC all-entries note) — pinned by same-company + partial-match vectors.
  - Skills dedupe removes fold-match duplicates first-occurrence-wins and NEVER sorts — the LLM's returned order is the priority order (LI-05), pinned by a deliberately unsorted scripted list.
  - Empty habilidades fails loud ONLY when the profile has skills to draw from; a skills-less profile is a frontend lint aviso surface, not a run failure (probe edge LI-05/empty backend half).
  - "[Rule 3] The plan's verbatim compose_regen_stage_input reuse would have mislabeled the LinkedIn base (DESCRIÇÃO DA VAGA) — the input-agnostic part is the dica framing, extracted as facts.append_dica_block; compose_linkedin_regen_stage_input keeps the OBJETIVO DE CARREIRA base."
  - LinkedinSecoes lives in app/linkedin/models.py (NOT routes/linkedin.py — would be a circular import with the pipeline); empty experiencias/habilidades lists are legitimate display states (zero-experience/skills-less profiles), headline/sobre keep min_length=1 floors.
  - limites.habilidades carries {contagem, limite:100} as a sanity record only — no per-list character limit exists (D-05 forbids inventing one; the UI count line uses contagem).
metrics:
  duration: 20 min
  completed: 2026-09-29
actuals:
  tokens: 26170 # chars/4 over the realized diff (104680 diff chars)
  tasks: 2
  commits: 2 # measured: git rev-list --count aadf515..HEAD
plan_head_before: aadf51596c95781a7946274a356f31bf8ba04f09
status: complete
---

# Phase 6 Plan 2: Full LinkedIn Generation Backend Summary

**One-liner:** one gerar call now produces all four LinkedIn blocks (headline → sobre → experiências per profile entry in profile order → prioritized skills) with loud-empty guards, fold-match alignment + dedupe, and the full `limites` block — plus `/api/linkedin/lint` as a verbatim `run_lint_only` reuse and per-section regen with exact Phase 5 semantics (one stage, wholesale merge, byte-identical siblings, dica-as-DATA).

## What Was Built

- **Stage quartet complete (Task 1):** `linkedin-sobre`, `linkedin-experiencias`, `linkedin-skills` registered in `_STAGE_SCHEMAS` with their prompt files (registration pin test flipped to the full quartet, wired to the 06-01 drift-locked pairs). Three PT-BR prompt files copy the resume-summary structure — injection-rule line, never-invent hard rule anchored to FATOS DO PERFIL, strict JSON output blocks; experiências carries the verbatim company/title hard rule and `max_tokens: 6000` (inside the research-mandated 4000-8000 band, asserted by a loader test); skills states returned order = priority order.
- **Full pipeline (Task 1):** `run_linkedin_pipeline` runs all four stages sequentially in D-09 order on the SAME composed input (a bad About never re-rolls the headline), returning `{idioma, secoes, limites}` with the full secoes shape. Loud-empty: blank headline/sobre, zero-entry experiências, or any blank descricao raises `LLMError`; empty habilidades fails only on skills-bearing profiles. Experiências align to PROFILE order via company `_fold` matching (first unused match wins) with the returned-order all-entries fallback; skills dedupe fold-match first-occurrence-wins with no sort anywhere. `limites` covers headline/sobre `{limite,tamanho,excesso}` (code-unit len), experiências index-aligned, habilidades `{contagem, limite}` sanity record. Over-limit text is never truncated (flagged via excesso).
- **Lint + regen (Task 2):** `POST /api/linkedin/lint` calls `run_lint_only(objetivo)` verbatim (D-03: input-agnostic engine, avisos non-blocking). `run_linkedin_section_regen` + `SECTION_STAGE_BY_ID`: exactly ONE stage per regen for each of the four secao ids, merge over the SUBMITTED `LinkedinSecoes` (siblings by reference — byte-identity pinned with `is` assertions), experiências group swap re-aligned to profile order, `limites` recomputed over the FULL merged state, loud-empty re-run on the regenerated block only. `POST /api/linkedin/regenerar`: strict request (secao Literal, dica ≤500 defaulting None), plain def, house 200-envelope. The dica framing is shared: `facts.append_dica_block` extracted so resume and LinkedIn regen composes use ONE input-agnostic framing string.

## Tasks Completed

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | Three remaining stages + full 4-block pipeline (limites, alignment, dedupe) | 51e5c72 |
| 2 | Lint route + per-section regen pipeline and route (Phase 5 semantics) | a15afd2 |

## Verification

- `cd backend && uv run pytest tests/test_linkedin_pipeline.py tests/test_linkedin_regen_pipeline.py tests/test_linkedin_api.py -q` → **60 passed**
- `cd backend && uv run pytest -q` (full offline suite) → **350 passed, 7 deselected** (309 post-06-01 baseline + 41 new; suite stays 100% offline — ScriptedClient/fakes only)
- runs.jsonl offline assertion: a scripted quartet run logs exactly the four linkedin stage strings, metadata-only (D-10) — pinned in test (b)
- Probe edges pinned: LI-03/empty, LI-03/encoding, LI-04/empty, LI-04/adjacency (same-company distinct consumption + partial-match fallback), LI-04/ordering, LI-05/adjacency, LI-05/ordering (no-sort vector), LI-05/empty (skills-less profile ok)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Verbatim `compose_regen_stage_input` reuse would mislabel the LinkedIn base**
- **Found during:** Task 2 (first regen test run)
- **Issue:** `app.resume.facts.compose_regen_stage_input` builds its base via `compose_stage_input`, hard-coding the "DESCRIÇÃO DA VAGA" label — the plan's as-is reuse would have sent LinkedIn objectives under the resume's JD label, breaking the 06-01-pinned "OBJETIVO DE CARREIRA" user-message contract (T-06-01).
- **Fix:** Extracted the genuinely input-agnostic part — the dica framing + blank normalization — as `append_dica_block(base, dica)` in facts.py (compose_regen_stage_input delegates; resume behavior byte-identical); added `compose_linkedin_regen_stage_input` keeping the LinkedIn base. One framing string, many bases.
- **Files modified:** backend/app/resume/facts.py, backend/app/linkedin/pipeline.py, backend/tests/test_linkedin_regen_pipeline.py
- **Commit:** a15afd2

**2. [Rule 3 - Blocking] Submitted-state model needed a non-route home**
- **Found during:** Task 2 (design)
- **Issue:** The plan said to mirror Phase 5's "reuse the exported secoes shape — import, never duplicate", but LinkedIn has no export module, and hosting the model in routes/linkedin.py would create a circular import (routes ↔ pipeline both need it).
- **Fix:** `app/linkedin/models.py` with `LinkedinSecoes` (strict, reuses `ExperienciaLinkedin` from app.llm.schemas; min_length=1 floors on headline/sobre; empty experiencias/habilidades lists legitimate for zero-experience/skills-less profiles) — one definition imported by both the route and the pipeline, mirroring ExportarSecoes' role.
- **Files modified:** backend/app/linkedin/models.py (new)
- **Commit:** a15afd2

**3. [Test-authoring fixes during Task 1 — no behavior change]**
- The same-company alignment expectation was corrected to the plan's own "first unused match wins" semantics (the implementation was right; my first expectation consumed returned entries in the wrong order), and the skills-less-profile vector now scripts the empty habilidades list it exists to prove. Also updated the 06-01 API test stubs to serve the quartet (mechanical consequence of the 1→4 stage expansion).
- **Files modified:** backend/tests/test_linkedin_pipeline.py, backend/tests/test_linkedin_api.py
- **Commit:** 51e5c72

The `test_linkedin_schema.py` registration pin flipped from "only the tracer stage" to "all four registered" — the pin's own 06-01 comment anticipated this exact 06-02 flip; not a deviation.

## Auth Gates

None — fully offline execution, no credentials touched.

## Known Stubs

None created by this plan. (Carried forward from 06-01: the LinkedInHome result card still renders only the Headline block — a frontend-scope stub that 06-03 resolves against this plan's now-complete backend envelope; the backend surface itself has no placeholder paths.)

## Notes for 06-03 / 06-04 / 06-05

- The gerar envelope keys are final: `{status, idioma, secoes{headline,sobre,experiencias[entries],habilidades}, limites{headline,sobre,experiencias[index-aligned],habilidades{contagem,limite}}}`; regen returns the same shape with `status` included (route returns the pipeline result directly). Frontend types mirror these additively.
- Experiências entries carry LLM company/title strings as display anchors only — render sub-block headers from PROFILE FACTS (UI-SPEC); per-entry Copiar copies `descricao` only.
- The QA payload (`qa`) is NOT in the envelope yet — 06-04/06-05 add it; the regen pipeline is where per-block post-gen hooks join.
- `SECTION_STAGE_BY_ID` accepts exactly the four LinkedIn ids; the route Literal rejects resume ids ("resumo") with a 422 (pinned).
- Any `prompts/linkedin-*.md` edit is "not done" until `uv run pytest -m llm` is green (D-15 DoD — the bilingual harness tests land in 06-05).

## Self-Check: PASSED

- Created files verified on disk (5 created, 7 modified — all in the task file lists + the two Rule 3 files).
- Commits verified in git log: 51e5c72, a15afd2.
- `git rev-list --count aadf515..HEAD` = 2 (matches the commits ledger; no uncommitted code changes).
