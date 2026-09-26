---
phase: 03-resume-vertical-slice
plan: 01
subsystem: llm
tags: [pydantic, json-schema, llm-gateway, meta-prompts, openrouter, fastapi, grounding]

# Dependency graph
requires:
  - phase: 02-llm-generation-core
    provides: gateway run_stage + _STAGE_SCHEMAS, hand-maintained strict wire-schema pattern with drift-lock, PromptSpec prompt loader (fresh read), runs.jsonl per-attempt audit, bounded retry with PT-BR correction
  - phase: 01-foundation-scaffold-master-profile
    provides: Profile schema with LocalizedText (pt-BR base) and impacts embedded per experience/project, content/profile.md
provides:
  - Three strict resume section models (ResumeSummary, ExperienciaGerada, ResumeExperiencias, ResumeSkills) + three hand-maintained strict wire schemas, drift-locked by a generalized harness over all four wire schemas
  - Gateway stages resume-summary / resume-experiencias / resume-skills — typed output, per-attempt runs.jsonl lines carrying the stage name, bounded retry, loud LLMError exhaustion (all inherited Phase 2 machinery, zero new call paths)
  - Three git-versioned PT-BR meta-prompts with the D-07 grounding hard rule as rule 1 and the injection clause
  - backend/app/resume/facts.py — resolve_loc (run language, pt-BR fallback), serialize_profile_facts (profile-derived-only labeled blob), compose_stage_input (FATOS DO PERFIL + DESCRIÇÃO DA VAGA in one input blob)
affects: [03-02 (lint/coverage), 03-03 (route orchestration), 03-04 (result screen), 03-05 (grounding harness)]

# Actuals (#2632) — pairs with the plan's estimate (85000 tokens) to calibrate.
actuals:
  tokens: 9205
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []  # T-03-SC by design: no new packages — stdlib-only plan
  patterns:
    - "Hand-maintained strict wire schema per stage + generalized drift-lock harness (all four wire schemas walked recursively)"
    - "Facts-blob-in-user-message: composed input_text through the UNCHANGED gateway user-message template — zero message-plumbing changes"
    - "Per-stage prompt frontmatter params (temperature/max_tokens) drive the SDK call shape"
    - "Lazy-symbol RED tests: planned symbols resolved inside test bodies so RED fails on assertions, not collection ImportErrors (#3770 RED_EVIDENCE_OK)"

key-files:
  created:
    - backend/app/resume/__init__.py
    - backend/app/resume/facts.py
    - backend/tests/test_resume_schema.py
    - backend/tests/test_resume_pipeline.py
    - prompts/resume-summary.md
    - prompts/resume-experiencias.md
    - prompts/resume-skills.md
  modified:
    - backend/app/llm/schemas.py
    - backend/app/llm/gateway.py

key-decisions:
  - "RED tests resolve planned symbols lazily inside test bodies — RED fails on assertions about planned behavior, not collection ImportErrors (verified RED_EVIDENCE_OK via check tdd-red-evidence)"
  - "Profile facts enter the model as ONE composed blob through the unchanged gateway user-message template (planner decision: no facts parameter on run_stage)"
  - "resume-experiencias max_tokens 4000 — deliberate ceiling (PT-BR encodes ~1.5-2x EN; the old 2000 budget was sized for keyword lists)"
  - "requirements RESUME-01/RESUME-03 claimed by this plan but NOT yet marked complete in REQUIREMENTS.md — shared with plans 03-03/03-04/03-05, deferred by the #2388 shared-ID gate"

patterns-established:
  - "Strict section models inherit _Strict (extra=forbid); every field required, no defaults"
  - "Wire-schema rule: every property in required, additionalProperties false at EVERY object level, never derived from model_json_schema() at runtime"
  - "facts.py discipline: pure functions, imports only app.profile.models; fixed uppercase section labels are the only non-profile strings in the blob"

requirements-completed: [RESUME-03, RESUME-01]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Three strict resume section models + three hand-maintained wire schemas, drift-locked over all four wire schemas"
    requirement: RESUME-03
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_schema.py (16 tests: strict-shape walk, property-set equality, nested item equality, strict rejection)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Three resume stages registered end-to-end through the gateway: typed output, runs.jsonl attempt+run_summary lines carrying the stage name, invalid-then-valid bounded retry, loud LLMError on unknown stage / exhaustion"
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_pipeline.py#test_happy_path_returns_typed_section_and_logs_stage (3 stages x 2 languages) + retry/unknown-stage tests, and tests/test_gateway.py regression suite"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each stage's own prompt-file frontmatter (temperature/max_tokens/wire schema name) drives the SDK call shape; composed input flows through the user message as data"
    requirement: RESUME-01
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_pipeline.py#test_sdk_call_shape_carries_stage_frontmatter"
        status: pass
    human_judgment: false
  - id: D4
    description: "Grounding supply line: facts.py emits a profile-derived, run-language-resolved blob (pt-BR fallback) composed with the pasted JD into one input blob; absent tokens (Snowflake probe) can never appear"
    requirement: RESUME-03
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_pipeline.py#test_serialize_full_profile_contains_known_profile_strings_ptbr + fallback/Snowflake/compose tests (6)"
        status: pass
    human_judgment: false
  - id: D5
    description: "The D-07 grounding bar holds in LIVE generation: no invented numbers/technologies/dates in actual LLM output, bilingual section quality"
    requirement: RESUME-03
    verification: []
    human_judgment: true
    rationale: "Offline fixture-based invention detection lands in plan 03-05; live bilingual proof requires pytest -m llm spend and human review of generated sections (end-of-phase verify) — automation cannot judge grounding quality at authoring time"
  - id: D6
    description: "Meta-prompts are git-versioned and editable — the next call reflects an edit with no code change (SC1 extended to resume stages)"
    verification:
      - kind: unit
        ref: "backend/tests/test_gateway.py#test_prompt_file_edit_is_visible_on_next_call (same loader path) + SDK shape tests loading the real resume prompt files"
        status: pass
    human_judgment: false

# Metrics
duration: 13min
completed: 2026-09-26
status: complete
---

# Phase 3 Plan 01: Resume Generation Engine Summary

**Three strict bilingual grounded resume stages (ResumeSummary / ResumeExperiencias / ResumeSkills) registered in the Phase 2 gateway with drift-locked wire schemas, plus a profile-fact serializer that grounds them in profile facts only**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-26T21:17:06Z
- **Completed:** 2026-09-26T21:30:01Z
- **Tasks:** 3
- **Files modified:** 9 (828 insertions, 5 deletions)

## Accomplishments

- The resume generation ENGINE is complete: `run_stage("resume-summary"|"resume-experiencias"|"resume-skills", input_text, language)` returns typed, schema-validated sections offline (injected client) — orchestration (03-03) and display (03-04) can build on it immediately
- Three hand-maintained strict wire schemas with a generalized drift-lock harness covering all four wire schemas (keyword + 3 resume) — wire dict and Pydantic model can no longer diverge silently
- The grounding supply line exists: `serialize_profile_facts` emits ONLY profile-derived content, resolved to the run language with pt-BR fallback; `compose_stage_input` delivers facts + pasted JD through the unchanged gateway user-message template (zero gateway plumbing changes)
- Three git-versioned PT-BR meta-prompts carrying the D-07 hard rule as rule 1 (never add numbers/technologies/dates absent from FATOS DO PERFIL) and the injection clause — the user can edit them and the next call reflects it with no code change

## Task Commits

Each task was committed atomically (TDD task produced its RED + GREEN pair):

1. **Task 1: Three strict section models + wire schemas + drift-lock tests** — `92f91e3` (test, RED) + `bc64fd7` (feat, GREEN)
2. **Task 2: Tracer — register the three resume stages end-to-end through the gateway** — `0613c1f` (feat)
3. **Task 3: Profile-fact serialization (facts.py)** — `255a763` (feat)

**Plan metadata:** this commit (docs(03-01): complete resume generation engine plan)

## Files Created/Modified

- `backend/app/llm/schemas.py` — +ResumeSummary, ExperienciaGerada, ResumeExperiencias, ResumeSkills (all _Strict) + 3 RESUME_*_STRICT_SCHEMA wire dicts
- `backend/app/llm/gateway.py` — 3 new _STAGE_SCHEMAS entries; run_stage return annotation loosened to BaseModel (signature/messages template untouched)
- `backend/app/resume/__init__.py` — package marker
- `backend/app/resume/facts.py` — resolve_loc, serialize_profile_facts, compose_stage_input (pure functions)
- `prompts/resume-summary.md` / `prompts/resume-experiencias.md` / `prompts/resume-skills.md` — meta-prompts (0.3/2000, 0.3/4000, 0.2/2000)
- `backend/tests/test_resume_schema.py` — generalized drift-lock harness (16 tests)
- `backend/tests/test_resume_pipeline.py` — offline pipeline + facts tests (17 tests)

## Decisions Made

- RED tests resolve planned symbols lazily inside test bodies so RED fails on assertions about planned behavior, not collection ImportErrors — validated `RED_EVIDENCE_OK` via `gsd_run check tdd-red-evidence`
- Facts flow as one composed blob through the unchanged user-message template (planner decision honored; Phase 2 message-shape tests untouched)
- resume-experiencias sized at max_tokens 4000 (research Pitfall 5); summary/skills keep 2000
- RESUME-01/RESUME-03 marking deferred: shared with plans 03-03/03-04/03-05 per the #2388 shared-ID gate — re-evaluated when the last declaring plan finishes

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Verification Results

- `uv run pytest tests/test_resume_schema.py tests/test_resume_pipeline.py tests/test_keyword_schema.py tests/test_gateway.py -q` → **57 passed**
- `uv run pytest -q` (full offline suite) → **120 passed, 5 deselected** (87 baseline + 33 new; llm-marked real-API tests deselected by design)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for 03-02 (wave 2). The engine contract for the rest of the phase: facts via `compose_stage_input(serialize_profile_facts(profile, language), jd_text)` → `run_stage(stage, blob, language)` → typed section models
- Live grounding proof (D5) is deliberately deferred to plan 03-05's fixture harness + `pytest -m llm` + end-of-phase human verify — not a blocker for 03-02/03-03

---
*Phase: 03-resume-vertical-slice*
*Completed: 2026-09-26*

## Self-Check: PASSED

All 9 created/modified key files verified on disk; all 4 task commit hashes (92f91e3, bc64fd7, 0613c1f, 255a763) verified in git log; full offline suite 120 passed.
