---
phase: 02-llm-generation-core
plan: "02"
subsystem: llm
tags: [openrouter, openai-sdk, pydantic, prompts, jsonl, tracer]

requires:
  - phase: 02-llm-generation-core
    provides: config constants (PROMPTS_DIR/RUNS_LOG/LLM_MODEL/LLM_MAX_ATTEMPTS), openai dep, llm pytest marker, logs/ gitignore
provides:
  - app.llm package — errors (PromptError/LLMError, ProfileError shape), prompts.load_prompt (strict, fresh-read), schemas (Keyword/KeywordExtraction + strict wire JSON Schema), logging.write_run_line, gateway.run_stage (injectable client)
  - prompts/keyword-extraction.md — the first real, git-versioned meta-prompt
  - Offline test suites for the loader (6 tests) and the gateway (6 tests)
affects: [02-llm-generation-core (02-03 retry/expansion, 02-04 real-API harness), 03-tailoring (keyword extraction entry point)]

actuals:
  tokens: 14900   # chars/4 over realized diff (~59.6k chars across 9 files)
  tasks: 2
  commits: 3      # measured: git rev-list --count f0277ecd..7977a9f7
plan_head_before: f0277ecdf07d9c7dd04a1e8d56369a5643c4c497

tech-stack:
  added: []   # openai SDK already added in 02-01
  patterns:
    - "Prompt loader mirrors profile loader try/except ladder — PT-BR loud, names file+key"
    - "Gateway user input is DATA in the user message, never system (T-02-01); wire strict:true never trusted, always re-validated (T-02-03)"
    - "Injectable SDK client — offline-by-default suite (D-16), no mocking dependency"

key-files:
  created:
    - backend/app/llm/__init__.py
    - backend/app/llm/errors.py
    - backend/app/llm/prompts.py
    - backend/app/llm/schemas.py
    - backend/app/llm/gateway.py
    - backend/app/llm/logging.py
    - prompts/keyword-extraction.md
    - backend/tests/test_prompt_loader.py
    - backend/tests/test_gateway.py
  modified: []

key-decisions:
  - "Body IS the system prompt (D-07): load_prompt returns LoadedPrompt(spec, body); runtime inputs compose the user message"
  - "render_prompt_errors_ptbr — profile D-14 renderer with 'Erro no prompt' header (PATTERNS-sanctioned variant)"
  - "Single-entry stage→schema map in gateway; full drift-locked schema dict deferred to 02-03 as planned"
  - "Gateway logs 'error'/'invalid' status lines on failures too (loud + audited, D-03/SC3) even before the retry loop exists"

patterns-established:
  - "Every LLM-layer failure raises LLMError(message_ptbr, raw) — no silent model fallback"
  - "One runs.jsonl append per attempt is the atomicity unit; metadata only, never key/prompt/response"

requirements-completed: [PROFILE-03]

coverage:
  - id: D1
    description: "Tracer: prompt file → strict loader → gateway (mocked) → Pydantic KeywordExtraction → one JSONL line"
    requirement: PROFILE-03
    verification:
      - kind: unit
        ref: backend/tests/test_prompt_loader.py (6 tests)
        status: pass
      - kind: unit
        ref: backend/tests/test_gateway.py (6 tests, fake client — full offline path)
        status: pass
      - kind: other
        ref: "cd backend && uv run pytest -q → 58 passed, offline"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-26
status: complete
---

# Phase 02 Plan 02: LLM Tracer Summary

**Thinnest end-to-end path through every Phase-2 layer: prompts/keyword-extraction.md → strict loader → gateway (OpenRouter via openai SDK, mocked in tests) → Pydantic-validated KeywordExtraction → one metadata-only JSONL line in logs/runs.jsonl**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-26T03:08:48Z
- **Completed:** 2026-09-26T03:20:5xZ
- **Tasks:** 2 (Task 1 TDD RED→GREEN; Task 2 tracer)
- **Files created:** 9

## Accomplishments
- `app/llm/prompts.py` mirrors the profile loader exactly (FileNotFoundError/YAML/UTF-8/ValidationError ladder, PT-BR messages naming file and key); strict `PromptSpec` frontmatter (id/temperature/max_tokens, extra="forbid"); default dir resolves at call time; fresh read per call (D-08/SC1)
- `prompts/keyword-extraction.md` — input-agnostic PT-BR system prompt: facts-only, canonical+aliases, pt/en renderings with identical proper nouns, fixed 4-category set
- `app/llm/schemas.py` — KeywordCategory (4 ASCII tokens per A6), Keyword, KeywordExtraction (all extra="forbid") + hand-maintained minimal strict wire JSON Schema (never model_json_schema() raw — Pitfall 1)
- `app/llm/logging.py` — `write_run_line`: one UTF-8 JSON append per attempt (ensure_ascii=False, mkdir on first write), metadata only (T-02-02)
- `app/llm/gateway.py` — `run_stage`: fresh prompt load → system=prompt body / user=runtime inputs (T-02-01) → SDK call (model from config only, json_schema strict, provider.require_parameters in extra_body — Pitfall 2, temperature/max_tokens from PromptSpec) → Pydantic re-validation (SC3/T-02-03) → one log line → typed return; injectable client (offline suite, D-16); missing key / unknown stage / API error / invalid content all raise loud LLMError with the failure logged
- Gateway tests prove the FULL path offline with a fake client: typed result, exactly one JSON line with correct fields, SDK call shape, failure containment, accent integrity

## Task Commits

Each task was committed atomically:

1. **Task 1: Meta-prompt loader + errors + first prompt** - `e684960` (test — RED: ModuleNotFoundError, no app.llm)
2. **Task 1: Meta-prompt loader + errors + first prompt** - `d1e4d93` (feat — GREEN: 6/6 loader tests, full suite 52)
3. **Task 2: End-to-end tracer** - `7977a9f` (feat — schemas + logging + gateway + offline gateway tests; 58/58 full suite)

## TDD Gate Compliance (Task 1)

- RED: `backend/tests/test_prompt_loader.py` — collection error `ModuleNotFoundError: No module named 'app.llm'` (exit 2) before any implementation existed
- GREEN: implementation passes; full offline suite 52/52 at that point
- REFACTOR: not needed — the loader mirrors an already-clean analog

## Files Created
- `backend/app/llm/__init__.py` - package marker
- `backend/app/llm/errors.py` - PromptError/LLMError (message_ptbr + raw) + render_prompt_errors_ptbr
- `backend/app/llm/prompts.py` - PromptSpec, LoadedPrompt, load_prompt (strict, fresh-read)
- `backend/app/llm/schemas.py` - KeywordCategory/Keyword/KeywordExtraction + KEYWORD_EXTRACTION_JSON_SCHEMA
- `backend/app/llm/logging.py` - write_run_line (UTF-8 JSONL append)
- `backend/app/llm/gateway.py` - run_stage (injectable client, loud failures)
- `prompts/keyword-extraction.md` - first real meta-prompt (versioned)
- `backend/tests/test_prompt_loader.py` - 6 tests (happy, typo key, missing, YAML, fresh-read)
- `backend/tests/test_gateway.py` - 6 tests (full offline path, call shape, failures, UTF-8)

## Decisions Made
- `render_prompt_errors_ptbr` reuses the profile `_ptbr_message`/`render_loc` machinery with an "Erro no prompt" header (PATTERNS explicitly sanctions the header variant over duplicating the map)
- Gateway also logs `error`/`invalid` attempts (status field) before the 02-03 retry loop exists — the audit trail is complete from day one
- Test-side autouse fake-key fixture satisfies the call-time guard; the missing-key behavior is separately pinned by overriding it with ""

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Call-time OPENROUTER_API_KEY guard fired in offline tests**
- **Found during:** Task 2 verification
- **Issue:** This environment has no OPENROUTER_API_KEY, so the (correct, planned) call-time guard rejected every gateway test before the fake client mattered
- **Fix:** Autouse fixture monkeypatching `app.llm.gateway.OPENROUTER_API_KEY` to a fake value; the missing-key test overrides it with "" and asserts the loud LLMError
- **Files modified:** backend/tests/test_gateway.py
- **Commit:** 7977a9f

**2. [Rule 2 - Correctness] PT-BR renderer header said "Erro no perfil" for prompt files**
- **Found during:** Task 1 GREEN
- **Issue:** Reusing `render_errors_ptbr` verbatim would emit a misleading profile header on prompt-validation failures
- **Fix:** Added `render_prompt_errors_ptbr` (same map/loc rendering, "Erro no prompt:" header) — PATTERNS-sanctioned option
- **Files modified:** backend/app/llm/errors.py, backend/app/llm/prompts.py
- **Commit:** d1e4d93

## Issues Encountered
None beyond the deviations above.

## User Setup Required
None — for real API calls (Plan 02-04), set `OPENROUTER_API_KEY` in the repo-root `.env`.

## Next Phase Readiness
- 02-03 (retry loop + drift-locked schema) can wrap `run_stage`'s single-attempt core; log-line shape and attempt field already match D-14
- 02-04 (real-API harness) marks its tests `-m llm` and consumes config.LLM_MODEL; blocker in STATE (model not yet validated for strict json_schema) still open

## Self-Check: PASSED

- FOUND: backend/app/llm/prompts.py, gateway.py, logging.py, schemas.py, errors.py
- FOUND: prompts/keyword-extraction.md
- FOUND: backend/tests/test_prompt_loader.py, test_gateway.py
- FOUND: commits e684960, d1e4d93, 7977a9f (git log)

---
*Phase: 02-llm-generation-core*
*Completed: 2026-09-26*
