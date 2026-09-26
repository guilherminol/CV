---
phase: 02-llm-generation-core
plan: "03"
subsystem: llm
tags: [openrouter, retry-loop, json-schema, jsonl, pydantic, tdd]

requires:
  - phase: 02-llm-generation-core
    provides: tracer gateway/prompts/logging (02-02), config constants (02-01)
provides:
  - "KEYWORD_STRICT_SCHEMA — hand-maintained strict wire dict, drift-locked to KeywordExtraction by test (T-02-08)"
  - "gateway retry loop — validation errors retried with appended assistant output + PT-BR correction (SC3/D-04, Pitfall 7); API errors fatal on attempt 1 (D-03)"
  - "logging.write_run_summary — terminal event=run_summary line per run on ok/invalid/error outcomes (D-13)"
  - "Pinned JSONL attempt-line field contract (ts..error) for Phase 5/6's run store (D-13 costly)"
affects: [02-llm-generation-core (02-04 real-API harness), 05-run-store (parses runs.jsonl)]

actuals:
  tokens: 13550   # chars/4 over realized diff (~54.2k chars incl. test churn)
  tasks: 3
  commits: 6      # measured: git rev-list --count 5275022..HEAD
plan_head_before: 5275022be1d5590b24717f86595e219796e86ca3

tech-stack:
  added: []
  patterns:
    - "Wire schema and Pydantic model are two hand-maintained representations locked by a bidirectional drift-lock test — never derived at runtime (Pitfall 1)"
    - "Retry sends ONLY evolved messages: assistant bad output + PT-BR correction embedding rendered validation errors (Pitfall 7)"
    - "One runs.jsonl append per attempt is the audit unit; one run_summary line per invocation closes the run"

key-files:
  created:
    - backend/tests/test_keyword_schema.py
    - backend/tests/test_run_log.py
  modified:
    - backend/app/llm/schemas.py
    - backend/app/llm/gateway.py
    - backend/app/llm/logging.py
    - backend/tests/test_gateway.py

key-decisions:
  - "KEYWORD_EXTRACTION_JSON_SCHEMA renamed KEYWORD_STRICT_SCHEMA (Plan-02-03 canonical name) — gateway references it via _STAGE_SCHEMAS, no inline literal"
  - "run_summary line carries event=run_summary + outcome(ok|invalid|error), attempts, status_counts, token totals — format discretion per D-13, pinned by test"
  - "Invalid JSON (JSONDecodeError) retried like ValidationError; plain re-send-JSON correction text in that branch"
  - "02-02 happy-path line-count assertion evolved to 1 attempt line + 1 summary line (planned contract evolution, not drift)"

patterns-established:
  - "Every LLM-layer failure raises LLMError(message_ptbr, raw) with a terminal run summary already written — the log alone reconstructs the run"
  - "Exhaustion message follows 'Falha na geração após N tentativas' so callers/tests can match on 'tentativas'"

requirements-completed: [PROFILE-03]

coverage:
  - id: D1
    description: "Retry loop + drift-locked schema + per-attempt logging, all offline"
    requirement: PROFILE-03
    verification:
      - kind: unit
        ref: backend/tests/test_keyword_schema.py (9 tests)
        status: pass
      - kind: unit
        ref: backend/tests/test_gateway.py (11 tests, scripted fake clients)
        status: pass
      - kind: unit
        ref: backend/tests/test_run_log.py (6 tests — pinned JSONL contract)
        status: pass
      - kind: other
        ref: "cd backend && uv run pytest -q → 78 passed, offline (all clients faked)"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-09-26
status: complete
---

# Phase 02 Plan 03: Gateway Expansion Summary

**Validation-error retry loop with appended PT-BR correction, per-attempt JSONL audit with terminal run-summary line, and the drift-locked strict JSON Schema dict — the full gateway contract, 78/78 offline**

## Performance

- **Duration:** 4 min
- **Tasks:** 3 (all TDD RED → GREEN)
- **Files modified:** 6 (2 created, 4 modified)

## Accomplishments
- `KEYWORD_STRICT_SCHEMA` (renamed from the 02-02 minimal dict): OpenAI strict-mode shape — additionalProperties:false + ALL properties in required at every object level (verified recursively by test), 4-token ASCII category enum (A6); gateway sends it via `_STAGE_SCHEMAS` (grep-able, no inline literal)
- Drift-lock (T-02-08): bidirectional property tests at top level AND keyword-item nesting between the wire dict and `KeywordExtraction.model_json_schema()` — the two representations cannot diverge silently
- Retry loop (Pattern 3, SC3): invalid JSON/ValidationError retried up to `LLM_MAX_ATTEMPTS`; each retry appends the assistant's bad output verbatim + a PT-BR correction request embedding the rendered Pydantic errors (Pitfall 7 — identical messages never resent); exhaustion raises `LLMError("Falha na geração após N tentativas…", accumulated_raw)`
- D-03 fail-loud: SDK/API/network exceptions are NOT retried — logged as status "error", LLMError on attempt 1, no model fallback
- SC1 at gateway level: prompt file edited between calls → second call's system message reflects the edit (monkeypatched PROMPTS_DIR, no cache)
- `write_run_summary`: terminal `event: "run_summary"` line (outcome, attempts, status_counts, token totals, summed latency) emitted on success, exhaustion, AND fatal-error paths
- `test_run_log.py` pins the attempt-line field set verbatim (ts, stage, model, language, attempt, status, prompt_tokens, completion_tokens, total_tokens, cost, latency_ms, error) — the Phase 5/6 run-store contract (D-13)

## Task Commits

Each task was committed atomically (TDD RED → GREEN):

1. **Task 1: Strict JSON Schema dict + drift-lock test** - `e9452cc` (test — RED: ImportError, no KEYWORD_STRICT_SCHEMA)
2. **Task 1: Strict JSON Schema dict + drift-lock test** - `e7fd1bf` (feat — GREEN: renamed dict, gateway wired)
3. **Task 2: Validation-error retry loop** - `6ec270e` (test — RED: recover + exhaust tests fail on single-attempt gateway)
4. **Task 2: Validation-error retry loop** - `ff505b5` (feat — GREEN: Pattern 3 loop)
5. **Task 3: JSONL contract + run summary** - `69d6ef3` (test — RED: 3 summary-contract tests fail)
6. **Task 3: JSONL contract + run summary** - `ecfa0b1` (feat — GREEN: write_run_summary + gateway _summarize)

## TDD Gate Compliance

- Task 1 RED: collection ImportError (`KEYWORD_STRICT_SCHEMA` absent) → exit 2; GREEN: 15/15 (schema + gateway suites)
- Task 2 RED: 2 new tests failed on assertions against the single-attempt gateway; GREEN: 11/11 gateway tests
- Task 3 RED: 3 summary-contract tests failed (no run_summary line); GREEN: full offline suite 78/78
- REFACTOR: inline conditional in the correction-message branch extracted to named `correction`/`rendered` locals before GREEN commit

## Files Created/Modified
- `backend/app/llm/schemas.py` - KEYWORD_STRICT_SCHEMA (renamed + documented)
- `backend/app/llm/gateway.py` - retry loop, _log/_summarize helpers, fatal-immediate error path
- `backend/app/llm/logging.py` - write_run_summary (UTF-8, ensure_ascii=False, append-only)
- `backend/tests/test_gateway.py` - ScriptedClient fake + 5 retry/fresh-read/key-guard tests
- `backend/tests/test_keyword_schema.py` - 9 drift-lock/strict/acceptance tests
- `backend/tests/test_run_log.py` - 6 contract tests (pinned field set)

## Decisions Made
- run_summary line shape (event/outcome/attempts/status_counts/totals) — format discretion granted by D-13, now pinned by test
- JSONDecodeError treated as retryable invalid with a simpler correction message ("reenvie o objeto JSON completo")
- Accumulated raw detail joined as `[tentativa N] …` lines — terminal-only (T-02-07: validation raw detail never enters JSONL lines)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two retry tests read raw JSONL lines including the new run_summary line**
- **Found during:** Task 3 GREEN
- **Issue:** Task 2's tests asserted statuses over ALL lines; the summary line (no `status` key) broke them
- **Fix:** Filter to attempt lines (`event != "run_summary"`) — same discipline as test_run_log.py
- **Files modified:** backend/tests/test_gateway.py
- **Commit:** ecfa0b1

**2. [Rule 1 - Bug] 02-02 happy-path test asserted exactly ONE log line**
- **Found during:** Task 3 GREEN
- **Issue:** The planned terminal summary line makes a successful run write 2 lines
- **Fix:** Assertion evolved to 1 attempt line + 1 run_summary line with outcome "ok" — planned contract evolution, documented here for traceability
- **Files modified:** backend/tests/test_gateway.py
- **Commit:** ecfa0b1

## Issues Encountered
None beyond the deviations above.

## User Setup Required
None — offline plan. For 02-04 (real-API harness), set `OPENROUTER_API_KEY` in the repo-root `.env`.

## Next Phase Readiness
- 02-04 harness can run `-m llm` tests against the full contract: bounded retries, per-attempt audit, terminal summary — the blocker "no model pinned/validated for strict json_schema" is exactly what it resolves
- Phase 5/6 run store parses runs.jsonl against the field set pinned in test_run_log.py

## Threat Mitigations Applied
- T-02-05: retry loop bounded by config; appended assistant content is schema-constrained data
- T-02-06: hard cap LLM_MAX_ATTEMPTS; every attempt cost-logged (run_summary totals)
- T-02-07: JSONL lines carry metadata only; validation raw detail goes to exc.raw (terminal), never the log
- T-02-08: drift-lock test fails CI on any wire/model property mismatch

## Self-Check: PASSED

- FOUND: backend/tests/test_keyword_schema.py, backend/tests/test_run_log.py
- FOUND: backend/app/llm/schemas.py, gateway.py, logging.py (modified)
- FOUND: commits e9452cc, e7fd1bf, 6ec270e, ff505b5, 69d6ef3, ecfa0b1 (git log)

---
*Phase: 02-llm-generation-core*
*Completed: 2026-09-26*
