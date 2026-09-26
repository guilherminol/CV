---
phase: 02-llm-generation-core
plan: 04
subsystem: testing
tags: [pytest, openrouter, llm, json-schema, pydantic, pt-br, fixture-harness]

# Dependency graph
requires:
  - phase: 02-llm-generation-core (plans 01-03)
    provides: gateway.run_stage (strict json_schema + Pydantic re-validation + retry + runs.jsonl audit), pytest llm marker with offline-by-default addopts, config-only LLM_MODEL slug
provides:
  - backend/tests/test_llm_harness.py — the -m llm real-API harness (slug probe + 4 parametrized bilingual runs through the gateway)
  - backend/tests/llm_fixtures.py — realistic bilingual fixture texts JD_EN/JD_PT/OBJECTIVE_EN/OBJECTIVE_PT (re-exported via conftest)
  - SC2 live proof: 5/5 -m llm tests passed against real OpenRouter with anthropic/claude-sonnet-4.5; runs.jsonl audit lines per attempt
affects: [03-generation-api, 04-pdf-export, 05-profile-integration, phase-06-ptbr-hardening]

# Actuals (#2632)
actuals:
  tokens: 3684
  tasks: 3
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "tmp-retargeted runs_log per harness run — audit assertions never depend on shared log state"
    - "D-11 bilingual spot-check via explicit proper-noun set (technology names pt==en; job titles translatable)"

key-files:
  created:
    - backend/tests/llm_fixtures.py
    - backend/tests/test_llm_harness.py
  modified:
    - backend/tests/conftest.py

key-decisions:
  - "Harness asserts the pinned 02-03 JSONL contract (cost field present, numeric tokens) instead of numeric USD — pricing stays deferred to the Phase 5/6 run store; no production code touched"
  - "Fixture texts live in tests/llm_fixtures.py imported by conftest (convention preserved, harness file stays readable)"
  - "OPENROUTER_API_KEY/LLM_MODEL relocated from backend/.env to repo-root .env — that is the only path app/config.py loads (Phase 1 convention pinned by test_secrets.py)"

patterns-established:
  - "Pattern: real-API harness = marker-gated + skipif-guarded + gateway-only call path + per-run tmp audit log"
  - "Pattern: PT-BR fixtures double as UTF-8 probes (accented chars asserted in output renderings)"

requirements-completed: [PROFILE-03]

coverage:
  - id: D1
    description: "Bilingual fixture texts (JD + career objective, EN + PT-BR) shape-tested offline in the default suite"
    requirement: PROFILE-03
    verification:
      - kind: unit
        ref: "backend/tests/test_llm_harness.py#test_fixture_is_realistic_text"
        status: pass
      - kind: unit
        ref: "backend/tests/test_llm_harness.py#test_fixtures_are_pure_data"
        status: pass
    human_judgment: false
  - id: D2
    description: "-m llm real-API harness green: slug probe + 4 bilingual gateway runs against live OpenRouter, per-attempt audit lines in runs.jsonl"
    requirement: PROFILE-03
    verification:
      - kind: integration
        ref: "uv run pytest -m llm -q (5 passed, 0 skipped, live OpenRouter, 2026-09-26)"
        status: pass
    human_judgment: false
  - id: D3
    description: "PT-BR prose quality of generated KeywordExtraction acceptable to the user (manual-only verification per 02-VALIDATION.md)"
    requirement: PROFILE-03
    verification: []
    human_judgment: true
    rationale: "Translation/terminology quality of live LLM output (PT-BR accents, natural renderings, correct categorization) is a human judgment call that automation cannot certify"

# Metrics
duration: 14min
completed: 2026-09-26
status: complete
---

# Phase 2 Plan 04: Real-API Fixture Harness Summary

**Pytest -m llm harness green on live OpenRouter — 5/5 real tests passed (slug probe + EN/PT-BR JD and objective runs) with per-attempt runs.jsonl audit and anthropic/claude-sonnet-4.5 validated as the pinned default slug**

## Performance

- **Duration:** 14 min (03:20–03:34 UTC span incl. checkpoint pause; live runs ~2 min)
- **Started:** 2026-09-26T03:20:17Z
- **Completed:** 2026-09-26T03:34:00Z (acceptance run 12:29 UTC — see Issues)
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 3

## Accomplishments
- Real-API harness: slug-probe test (bad slug fails loudly naming LLM_MODEL) + parametrized 4-case real-run test, every call through gateway.run_stage (no direct SDK)
- Realistic bilingual fixtures (JD_EN/JD_PT/OBJECTIVE_EN/OBJECTIVE_PT) — 4-category coverage, PT variants accented, offline shape tests in the default suite
- SC2 proven live: bilingual generation in both languages, per-attempt audit lines (stage/model/language/tokens/latency) in runs.jsonl, strict json_schema + Pydantic re-validation held on the wire
- STATE.md blocker resolved: anthropic/claude-sonnet-4.5 validated against the live API (A1 closed)

## Task Commits

1. **Task 1: Fixture texts — realistic JD and career objective, EN + PT-BR** - `93dfd6b` (test)
2. **Task 2: -m llm harness tests — slug probe + 4 real runs through the gateway** - `93dfd6b` (test; same file/commit — harness tests were written with the fixtures, TDD RED/GREEN ran per-layer)
3. **Task 3: Real harness run — SC2 acceptance** - `9ffc62a` (test fix: D-11 spot-check) + live run evidence (no code)

**Plan metadata:** pending (docs commit follows)

## Files Created/Modified
- `backend/tests/llm_fixtures.py` — four realistic bilingual fixture texts (UTF-8 probes)
- `backend/tests/test_llm_harness.py` — offline shape tests + -m llm slug probe + parametrized real-run test
- `backend/tests/conftest.py` — re-exports the four fixture constants

## Decisions Made
- Harness asserts the 02-03 pinned JSONL contract (cost field present, numeric total_tokens > 0) rather than numeric USD — cost is deliberately null until the Phase 5/6 run store; kept the plan's "no production code changes" scope intact
- Fixture texts live in a dedicated `tests/llm_fixtures.py` imported by conftest.py (keeps conftest convention and imports clean)
- Per-run tmp-retargeted runs_log in tests (discretion granted by plan); the acceptance presentation run used the real logs/runs.jsonl so the live evidence is auditable

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] D-11 spot-check wrongly treated job titles as proper nouns**
- **Found during:** Task 3 (live run)
- **Issue:** The pt==en identity assertion keyed on capitalized canonicals, so "Data Engineer" (correctly localized as pt="Engenheiro de Dados") failed the test — the gateway output was right, the test heuristic was wrong
- **Fix:** Restricted the identity check to an explicit technology proper-noun set (Kubernetes, Terraform, AWS, Kafka, ...); job titles excluded per D-11
- **Files modified:** backend/tests/test_llm_harness.py
- **Verification:** uv run pytest -m llm -q → 5 passed, 0 skipped (live)
- **Committed in:** 9ffc62a

**2. [Rule 3 - Blocking] OPENROUTER_API_KEY placed in backend/.env but config loads repo-root .env**
- **Found during:** Task 3 (post-key-setup run skipped all tests)
- **Issue:** The human set the key in backend/.env; app/config.py loads REPO_ROOT/.env (Phase 1 convention pinned by test_secrets.py), so OPENROUTER_API_KEY stayed empty and -m llm tests skipped
- **Fix:** Relocated OPENROUTER_API_KEY and LLM_MODEL lines from backend/.env to the repo-root .env (mechanical move, secret value never printed). backend/.env left untouched for the user to clean up at will
- **Files modified:** none tracked (.env files are gitignored)
- **Verification:** grep counts (values not printed); subsequent -m llm run went from 5 skipped to 5 passed
- **Committed in:** n/a (gitignored files)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes required for the live acceptance to run truthfully. No scope creep; no production code touched.

## Issues Encountered
- First -m llm run (pre-key) legitimately skipped per design; after key setup the skip surfaced the .env location mismatch above
- One real run failed on the over-broad D-11 assertion (bounded spend, ~20s) — fixed and re-run green

## User Setup Required
- OPENROUTER_API_KEY: now set in repo-root .env (relocated by the executor). If you edit keys later, edit the repo-root .env — backend/.env is NOT read by the app.

## Known Stubs
- None. (runs.jsonl `cost: null` is the deliberate 02-03 contract, not a stub — USD pricing lands with the Phase 5/6 run store.)

## Next Phase Readiness
- SC2/SC4 live evidence on disk: logs/runs.jsonl (10 audit lines) + validated KeywordExtraction outputs in both languages
- Model swap is config-only and proven: LLM_MODEL pinned default anthropic/claude-sonnet-4.5, env-overridable
- Phase 3 (generation API) can build directly on run_stage + KeywordExtraction; PT-BR QA-gate hardening (Phase 6) inherits the harness as its regression instrument

## Self-Check: PASSED

- Files verified on disk: backend/tests/llm_fixtures.py, backend/tests/test_llm_harness.py, backend/tests/conftest.py, this SUMMARY
- Commits verified in history: 93dfd6b, 9ffc62a
- Live evidence: `uv run pytest -m llm -q` → 5 passed / 0 skipped; logs/runs.jsonl → 10 audit lines

---
*Phase: 02-llm-generation-core*
*Completed: 2026-09-26*
