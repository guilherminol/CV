---
phase: 02-llm-generation-core
plan: "01"
subsystem: infra
tags: [openai, openrouter, pytest, config, gitignore]

requires:
  - phase: 01-foundation-scaffold-master-profile
    provides: backend skeleton (FastAPI app, config.py, pytest suite), .gitignore
provides:
  - openai SDK dependency in backend environment (OpenRouter client, Pattern 1)
  - llm pytest marker registered + offline-by-default addopts (-m 'not llm')
  - logs/ gitignored before any run-log writer exists
  - Phase 2 config constants: PROMPTS_DIR, LOGS_DIR, RUNS_LOG, LLM_MODEL (env-overridable), LLM_MAX_ATTEMPTS=3
affects: [02-llm-generation-core (02-02 tracer, 02-03 expansion, 02-04 harness)]

actuals:
  tokens: 9764   # chars/4 over realized diff (39,056 chars incl. uv.lock)
  tasks: 1
  commits: 2      # measured: git rev-list --count 49cf32e..HEAD
plan_head_before: 49cf32e9e0e3e34440fc54def45f920c5b881b75

tech-stack:
  added: ["openai>=3.19.2 (PyPI)"]
  patterns:
    - "Model slug lives only in config (env-overridable) — model swaps are config-only"
    - "Spend-bearing tests marked llm; default pytest run is offline by construction"

key-files:
  created:
    - backend/tests/test_phase2_config.py
  modified:
    - backend/pyproject.toml
    - backend/app/config.py
    - .gitignore
    - backend/uv.lock

key-decisions:
  - "LLM_MODEL default anthropic/claude-sonnet-4.5, env-overridable (D-01/D-02)"
  - "LLM_MAX_ATTEMPTS=3 pinned in config before any call site exists (D-04)"
  - "addopts = -m 'not llm' + registered marker — CLI -m llm wins when explicitly requested (D-15/D-16)"

patterns-established:
  - "Offline-by-default pytest: new network-touching tests must carry the llm marker"
  - "All Phase 2 paths/constants hang off app.config — no slug or path literals at call sites"

requirements-completed: [PROFILE-03]

coverage:
  - id: D1
    description: "Phase 2 wave-0 config: openai dep, llm marker + offline addopts, logs/ gitignore, config constants"
    requirement: PROFILE-03
    verification:
      - kind: unit
        ref: backend/tests/test_phase2_config.py (3 tests)
        status: pass
      - kind: other
        ref: "cd backend && uv run pytest -q → 46 passed, no unknown-marker warning"
        status: pass
      - kind: other
        ref: "git check-ignore logs/runs.jsonl → exit 0"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-09-26
status: complete
---

# Phase 02 Plan 01: Wave-0 LLM Config Summary

**openai SDK installed, `llm` pytest marker with offline-by-default addopts, logs/ gitignored, and all Phase 2 constants (LLM_MODEL, LLM_MAX_ATTEMPTS, PROMPTS_DIR/LOGS_DIR/RUNS_LOG) pinned in app.config**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-26T03:03:14Z
- **Completed:** 2026-09-26T03:06:32Z
- **Tasks:** 1 (TDD: RED → GREEN)
- **Files modified:** 5

## Accomplishments
- openai>=3.19.2 added via `uv add` (supply-chain audited in 02-RESEARCH: official openai/openai-python) and importable
- `llm` marker registered with `addopts = "-m 'not llm'"` — default suite runs offline (46 passed, zero deselected-network tests, no unknown-marker warning); `-m llm` on the CLI still selects explicitly
- `logs/` in .gitignore BEFORE any run-log writer exists (T-02-13); `git check-ignore logs/runs.jsonl` exits 0
- config.py extended: PROMPTS_DIR, LOGS_DIR, RUNS_LOG, LLM_MODEL (default `anthropic/claude-sonnet-4.5`, env-overridable), LLM_MAX_ATTEMPTS=3; tolerant OPENROUTER_API_KEY read untouched

## Task Commits

Each task was committed atomically (TDD cycle):

1. **Task 1: Wave-0 config** - `4a7a0a9` (test — RED: 3 failing tests for constants/marker/dependency)
2. **Task 1: Wave-0 config** - `35dbaa4` (feat — GREEN: implementation passes)

**Plan metadata:** (see final docs commit)

## TDD Gate Compliance

- RED: `backend/tests/test_phase2_config.py` — all 3 target tests failed on assertions (exit 1); evidence verified via `check tdd-red-evidence` → `RED_EVIDENCE_OK`
- GREEN: implementation passes; full offline suite 46/46 green
- REFACTOR: not needed (minimal config-only change)

## Files Created/Modified
- `backend/tests/test_phase2_config.py` - asserts constants, marker/addopts, openai dependency
- `backend/pyproject.toml` - openai dep; pytest markers + addopts
- `backend/app/config.py` - Phase 2 constants in existing REPO_ROOT style
- `.gitignore` - logs/ entry
- `backend/uv.lock` - lockfile for openai

## Decisions Made
None beyond plan - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 02-02 (tracer) can consume PROMPTS_DIR/RUNS_LOG/LLM_MODEL from app.config and mark its live-API test with `@pytest.mark.llm`
- Blocker noted in STATE: no OpenRouter model pinned yet — 02-04 harness validates json_schema compliance; slugs stay in config

## Self-Check: PASSED

- FOUND: backend/tests/test_phase2_config.py
- FOUND: backend/app/config.py (extended)
- FOUND: commits 4a7a0a9, 35dbaa4 (git log)

---
*Phase: 02-llm-generation-core*
*Completed: 2026-09-26*
