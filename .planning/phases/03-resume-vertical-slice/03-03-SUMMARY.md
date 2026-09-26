---
phase: 03-resume-vertical-slice
plan: 03
subsystem: api
tags: [fastapi, pydantic, orchestration, llm-gateway, envelope-api, pytest, offline-tests]

# Dependency graph
requires:
  - phase: 02-llm-generation-core
    provides: run_stage gateway with injectable client + per-attempt runs.jsonl audit (D-13/D-16); strict Pydantic models + hand-maintained wire schemas
  - phase: 03-resume-vertical-slice (plans 03-01, 03-02)
    provides: 3 resume section stages registered in the gateway (D-01); serialize_profile_facts + compose_stage_input; classify_coverage/summarize_coverage + lint_jd_tied pure functions
provides:
  - POST /api/resume/lint — pre-generate keyword extraction + JD-tied lint, 200 ok/erro envelope (SC5)
  - POST /api/resume/gerar — one-shot extraction → lint → 3 sequential section stages → generated-text-only coverage; the NORMATIVE response contract plan 03-04's typed client mirrors
  - app.resume.pipeline.run_lint_only / run_resume_pipeline with runs_log + client injection seams (offline testable)
  - all-or-nothing failure semantics: exceptions propagate out of the pipeline, the route owns the erro envelope; partial section sets structurally unreachable
affects: [03-04 frontend typed client, 03-05 grounding harness, Phase 5 review flow, Phase 6 LinkedIn reuse]

# Actuals (#2632)
actuals:
  tokens: 7216        # chars/4 over the realized diff (28,865 chars, 5 files)
  tasks: 2
  commits: 2          # MEASURED: git rev-list --count 896cf34..HEAD

# Tech tracking
tech-stack:
  added: []           # no new dependencies — contract held
  patterns: [sync-def envelope routes (threadpool dispatch), pipeline-all-or-nothing, raw-detail-terminal-only logging, strict extra=forbid request models]

key-files:
  created:
    - backend/app/resume/pipeline.py
    - backend/app/routes/resume.py
    - backend/tests/test_resume_api.py
  modified:
    - backend/app/main.py
    - backend/tests/test_resume_pipeline.py

key-decisions:
  - "Keyword-extraction language fixed to pt-BR in BOTH paths (lint + gerar); run-language selection happens at matching time — gerar echoes ITS OWN extraction verbatim (never trusts a prior lint call)"
  - "cobertura_resumo tallied server-side as {cobertos, total} — no score field anywhere in either response; no JS test runner introduced (no-new-frontend-deps contract)"
  - "Validation failures surface as FastAPI's default 422 (extra=forbid, jd_text 80..20000, Literal language) — app-level failures use the 200 envelope, malformed bodies are a client bug"
  - "Structural route pins (sync handlers, router-before-mount) written against FastAPI 0.141's _IncludedRouter layout with a dual-layout traversal"

patterns-established:
  - "Route envelope pattern extended: catch (ProfileError, PromptError, LLMError) → 200 + PT-BR erros lines; exc.raw to logger.error only (caplog-pinned split)"
  - "Pipeline seam discipline: runs_log + client thread into EVERY run_stage call; load_profile() fresh once per invocation, facts passed down (no memoization)"

requirements-completed: [RESUME-01, RESUME-02, RESUME-04, PROFILE-02]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "POST /api/resume/lint returns the ok envelope — keywords echoed verbatim from the extraction stage, avisos list present (SC5)"
    requirement: RESUME-02
    verification:
      - kind: integration
        ref: "tests/test_resume_api.py#test_lint_returns_ok_envelope_with_canned_keywords"
        status: pass
    human_judgment: false
  - id: D2
    description: "POST /api/resume/gerar returns the FULL ok envelope in both languages — idioma echo, keywords, avisos, secoes (resumo/experiencias/habilidades), cobertura entries, cobertura_resumo exact tally with no score field"
    requirement: RESUME-01
    verification:
      - kind: integration
        ref: "tests/test_resume_api.py#test_gerar_returns_full_ok_envelope_both_languages"
        status: pass
    human_judgment: false
  - id: D3
    description: "All-or-nothing + information-disclosure failure semantics: a scripted LLMError answers 200 + status erro with NO secoes key; PT-BR lines in the envelope, raw detail terminal-only (caplog split)"
    requirement: RESUME-01
    verification:
      - kind: integration
        ref: "tests/test_resume_api.py#test_gerar_erro_envelope_on_llm_error"
        status: pass
      - kind: integration
        ref: "tests/test_resume_api.py#test_lint_erro_envelope_on_llm_error"
        status: pass
    human_judgment: false
  - id: D4
    description: "Strict request validation: 422 on jd_text under 80 chars, on unknown extra keys (extra=forbid), and on language outside {pt-BR, en}"
    requirement: PROFILE-02
    verification:
      - kind: integration
        ref: "tests/test_resume_api.py#test_lint_rejects_short_jd_text"
        status: pass
      - kind: integration
        ref: "tests/test_resume_api.py#test_lint_rejects_unknown_extra_key"
        status: pass
      - kind: integration
        ref: "tests/test_resume_api.py#test_gerar_rejects_unknown_language"
        status: pass
    human_judgment: false
  - id: D5
    description: "Structural pins: both handlers are plain def (threadpool dispatch, never coroutines) and the resume router registers BEFORE the SPA mount"
    requirement: RESUME-01
    verification:
      - kind: integration
        ref: "tests/test_resume_api.py#test_handlers_are_sync_def_never_coroutines"
        status: pass
      - kind: integration
        ref: "tests/test_resume_api.py#test_resume_router_registered_before_spa_mount"
        status: pass
    human_judgment: false
  - id: D6
    description: "Pipeline orchestration: D-01 stage order (extraction → resume-summary → resume-experiencias → resume-skills), coverage computed over GENERATED text only (Docker profile-only keyword stays ausente), cobertura_resumo consistency both languages, LLMError propagates out of run_resume_pipeline untouched"
    requirement: RESUME-04
    verification:
      - kind: integration
        ref: "tests/test_resume_pipeline.py#test_run_resume_pipeline_returns_contract_envelope"
        status: pass
      - kind: integration
        ref: "tests/test_resume_pipeline.py#test_run_lint_only_returns_keywords_verbatim_and_avisos"
        status: pass
      - kind: integration
        ref: "tests/test_resume_pipeline.py#test_run_resume_pipeline_raises_llm_error_on_scripted_failure"
        status: pass
    human_judgment: false
  - id: D7
    description: "Live end-to-end generate against the real OpenRouter (~60s run, real PT-BR/EN content quality, ok envelope with 3 grounded sections)"
    requirement: RESUME-01
    verification: []
    human_judgment: true
    rationale: "The offline suite stubs the LLM client by design (D-16); the live smoke is exactly what plan 03-05's real-API bilingual harness + end-of-phase verification exist to prove."

# Metrics
duration: 9 min
completed: 2026-09-26
status: complete
---

# Phase 3 Plan 03: Orchestration + Routes Summary

**One-call resume pipeline (extraction → lint → 3 section stages → honest coverage) exposed as two sync 200-envelope routes — POST /api/resume/lint + /api/resume/gerar — the backend contract of record plan 03-04's typed client mirrors.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-26T21:56:42Z
- **Completed:** 2026-09-26T22:06:11Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- `backend/app/resume/pipeline.py`: `run_lint_only` + `run_resume_pipeline` orchestrate the full flow through the Phase 2 gateway — `runs_log`/`client` threaded into every `run_stage` call (offline D-16 seam), `load_profile()` fresh once per invocation (D-15), sections sequential in D-01 order, coverage over generated text ONLY (Pitfall 7), exceptions propagate untouched (all-or-nothing, T-03-07)
- `backend/app/routes/resume.py`: both endpoints as plain `def` (threadpool dispatch — the synchronous SDK client never blocks the event loop, Pitfall 2/T-03-06), strict `extra=forbid` request models (jd_text 80..20000, Literal language defaulting pt-BR — T-03-01), house erro envelope with raw detail terminal-only (T-03-02)
- `backend/app/main.py`: resume router registered beside the profile router BEFORE the SPA mount (Pitfall 3/5)
- Contract pinned by 25 new offline tests (route + pipeline suites); full offline suite green: 169 passed, 5 deselected (`-m llm`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline orchestration (run_lint_only, run_resume_pipeline)** - `2106c3e` (feat)
2. **Task 2: Routes + registration (lint/gerar, sync def, envelope, router-before-mount)** - `b439509` (feat)

**Plan metadata:** docs commit together with STATE.md/ROADMAP.md updates (this commit).

## Files Created/Modified

- `backend/app/resume/pipeline.py` — pipeline orchestration: lint-only + full generate, injection seams, generated-text-only coverage
- `backend/app/routes/resume.py` — LintRequest/GerarRequest strict models + lint_vaga/gerar_curriculo sync envelope handlers
- `backend/app/main.py` — resume router registration before the SPA mount
- `backend/tests/test_resume_api.py` — offline route tests: ok envelopes both languages, LLMError/broken-profile erro paths with caplog split, 422 validation, sync-handler + mount-order pins
- `backend/tests/test_resume_pipeline.py` — appended orchestration tests: ScriptedClient 4-stage runs, D-01 order, Docker profile-only keyword stays ausente, LLMError propagation

## Decisions Made

- Extraction language fixed to "pt-BR" in both paths — the extraction stage always emits the bilingual {pt, en} map (D-09/D-11); run-language selection happens at matching time. `gerar` re-runs extraction server-side and treats ITS OWN keywords as authoritative (the lint endpoint's keywords are display-only pre-generate)
- Server-side coverage tally `{cobertos, total}` — no score anywhere; frontend copy function only picks singular/plural wording later
- Route structural pins traverse FastAPI 0.141's `_IncludedRouter` layout with a fallback for flattened layouts — version-robust rather than relying on `app.routes` flattening

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] FastAPI 0.141 nests included routers — plan's "locate the route object by path" check didn't work as written**
- **Found during:** Task 2 (structural pins)
- **Issue:** `app.routes` on FastAPI 0.141.1 holds `_IncludedRouter` wrappers (path=None) plus a Mount with path `''`, not flattened `APIRoute`s — `routes[path]` KeyError'd
- **Fix:** rewrote both structural tests over a dual-layout traversal (`_iter_api_routes`): yields flattened `APIRoute`s OR recurses into `original_router.routes`, Mount position included
- **Files modified:** backend/tests/test_resume_api.py
- **Verification:** `test_handlers_are_sync_def_never_coroutines` + `test_resume_router_registered_before_spa_mount` pass
- **Committed in:** b439509 (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test-infrastructure adaptation only — the asserted invariants (sync handlers, mount ordering) are exactly the plan's; no production-code or contract change.

## Issues Encountered

- Task 2's first test run failed 8 tests due to a bug in my own stub helper (`list(_STAGE_CONTENT)` iterated dict keys, so the stub `json.loads`-ed a stage name). Fixed to `list(_STAGE_CONTENT.values())` within the task's red-green loop, before the Task 2 commit. All other failures were the same root cause.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The backend contract of record is real and curl-able: plan 03-04 mirrors these exact envelope shapes into `frontend/src/api/client.ts` (normative comment block in 03-03-PLAN.md is the interface of record)
- Requirement checkbox marking (RESUME-01/02/04, PROFILE-02) is deferred by the shared-ID gate (#2388): plan 03-04 declares the same IDs and has no SUMMARY yet; the gate re-evaluates when 03-04 finishes
- Open: optional live smoke against real OpenRouter (spend) — deliberately owned by plan 03-05's bilingual harness + end-of-phase verification (see coverage D7)

---
*Phase: 03-resume-vertical-slice*
*Completed: 2026-09-26*

## Self-Check: PASSED

- All 5 key-files verified on disk (`backend/app/resume/pipeline.py`, `backend/app/routes/resume.py`, `backend/app/main.py`, `backend/tests/test_resume_pipeline.py`, `backend/tests/test_resume_api.py`)
- Task commits verified in history: `2106c3e` (Task 1), `b439509` (Task 2)
- Full verification re-run: `uv run pytest tests/test_resume_api.py tests/test_resume_pipeline.py tests/test_api.py -q` → 41 passed; `uv run pytest -q` → 169 passed, 5 deselected (offline `-m llm` deselection by config — expected)
