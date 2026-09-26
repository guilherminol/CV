---
phase: 02-llm-generation-core
plan: 05
subsystem: api
tags: [llm, openrouter, gateway, error-containment, tdd, gap-closure]

# Dependency graph
requires:
  - phase: 02-llm-generation-core (plans 02-01..02-04)
    provides: gateway run_stage with injectable client, retry loop + containment flow (invalid attempt lines, run_summary, LLMError), offline fake-client test harness
provides:
  - Shape-guarded response extraction in run_stage: empty/missing choices and None/non-str content route through the SAME containment path as invalid JSON (CR-01/SC3)
  - Offline test pins for all three malformed-but-200 shapes (choices=[], content=None, non-str list) proving invalid attempt lines + terminal run_summary + bounded retry + LLMError at exhaustion
  - Recovery-on-retry proof for the malformed path with user-only correction (roles [system, user, user], no assistant turn)
affects: [phase-03 route layer (catches LLMError for the PT-BR message path), PROFILE-03 prompt-editing loop]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 2125        # chars/4 over the realized diff (8498 diff chars, 2 files)
  tasks: 2
  commits: 3          # MEASURED: git rev-list --count 46bc3e8..HEAD
commits: 3
plan_head_before: 46bc3e84d58712f11bac4e6bb255d556011559d2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shape-guard containment: getattr-based choices extraction + isinstance(content, str)/strip gate before json.loads, feeding the existing invalid-content containment flow unchanged"
    - "Metadata-only descriptors on new log paths: choice count + content type NAME only, never the content value"

key-files:
  created: []
  modified:
    - backend/app/llm/gateway.py
    - backend/tests/test_gateway.py

key-decisions:
  - "Malformed shapes reuse the invalid-JSON containment path verbatim (status 'invalid', _summarize('invalid') at exhaustion) — no new exception type, per CR-01 fix spec"
  - "Malformed-path retry appends ONLY a user correction (no assistant echo — content may be None/non-str); Pitfall 7 still satisfied because the correction differs from anything previously sent"
  - "Metadata-only discipline on the new path: descriptors only (choices count, content type NAME); test pins that input text and payload values never reach runs.jsonl"

patterns-established:
  - "Malformed-but-200 containment: any non-str/blank content is contained, never a raw IndexError/TypeError escape"
  - "ScriptedClient verbatim mode: prebuilt response objects (anything with .choices) pass through unwrapped — the offline harness can now simulate hostile response shapes"

requirements-completed: [PROFILE-03]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "All three malformed-but-200 shapes (choices=[], content=None, non-str list) are contained: LLMError after exactly LLM_MAX_ATTEMPTS calls, invalid attempt lines with 'conteúdo ausente ou não-textual' + correct type NAME, terminal run_summary outcome 'invalid', no raw IndexError/TypeError escape"
    requirement: PROFILE-03
    verification:
      - kind: unit
        ref: "tests/test_gateway.py#test_malformed_response_shapes_contained_like_invalid_content[empty-choices]"
        status: pass
      - kind: unit
        ref: "tests/test_gateway.py#test_malformed_response_shapes_contained_like_invalid_content[content-none]"
        status: pass
      - kind: unit
        ref: "tests/test_gateway.py#test_malformed_response_shapes_contained_like_invalid_content[content-non-str]"
        status: pass
    human_judgment: false
  - id: D2
    description: "A malformed shape on an early attempt recovers when a later attempt returns valid JSON: typed KeywordExtraction returned, statuses ['invalid','ok'], run_summary outcome 'ok' attempts=2, retry messages roles exactly [system, user, user] with the PT-BR correction 'Reenvie o objeto JSON completo'"
    requirement: PROFILE-03
    verification:
      - kind: unit
        ref: "tests/test_gateway.py#test_malformed_shape_then_valid_recovers_with_correction"
        status: pass
    human_judgment: false
  - id: D3
    description: "Offline-by-default contract intact: the three shapes are pinned with injected fake clients (zero network) and the default pytest run deselects the 5 llm-marked tests; full offline suite green"
    requirement: PROFILE-03
    verification:
      - kind: other
        ref: "command: cd backend && uv run pytest -q  →  87 passed, 5 deselected"
        status: pass
    human_judgment: false

# Metrics
duration: 8min
completed: 2026-09-26
status: complete
---

# Phase 2 Plan 5: SC3 Malformed-Shape Containment Gap Closure Summary

**SC3 gap closed: malformed-but-200 LLM response shapes (empty `choices`, `content=None`, non-str content) now route through the same containment path as invalid content — logged per attempt, bounded-retried with a PT-BR correction, typed `LLMError` at exhaustion, raw IndexError/TypeError never escapes (02-REVIEW.md CR-01)**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-26T17:48:11Z
- **Completed:** 2026-09-26T17:56:21Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- CR-01 guard in `gateway.run_stage`: `getattr`-based choices extraction + `isinstance(content, str)`/strip check before `json.loads` routes every malformed-but-200 shape into the existing containment flow (invalid attempt line with metadata-only PT-BR descriptors, `_summarize("invalid")` at exhaustion, loud `LLMError`)
- Three-shape offline pin (parametrized): `choices=[]`, `content=None` (refusal/content-filter), `content=["bloco"]` (content-block list) — each exhausts to LLMError after exactly `LLM_MAX_ATTEMPTS` calls with ascending invalid attempt lines whose `error` carries the correct type NAME ("NoneType"/"list") and a terminal run_summary with outcome "invalid"
- Recovery proven: malformed shape on attempt 1 + valid JSON on attempt 2 returns a typed `KeywordExtraction` with statuses ["invalid","ok"], run_summary outcome "ok" attempts=2, and retry messages roles exactly ["system","user","user"] — the malformed path appends ONLY the user correction, no assistant turn
- 02-VERIFICATION.md gap closed: the verifier's failed Behavioral Spot-Check is reversed — fake clients returning each malformed shape produce attempt+summary lines in runs.jsonl and raise LLMError (pinned offline by the new tests)

## Task Commits

Each task was committed atomically (TDD discipline — Task 1 ran RED → GREEN):

1. **Task 1 (tracer): empty `choices` shape — RED test, then the CR-01 guard** - `b225f57` (test: failing malformed-shape test, RED_EVIDENCE_OK recorded) + `3f1297e` (feat: shape-guard containment)
2. **Task 2: remaining shapes + recovery-on-retry + full-suite regression** - `1678e31` (test: parametrize extension + recovery test)

**Plan metadata:** committed with the docs commit (see Task Commits note below).

## Files Created/Modified
- `backend/app/llm/gateway.py` — guarded response-shape extraction inside `run_stage`; malformed shapes feed the existing invalid-content containment flow (no new functions, exceptions, or files)
- `backend/tests/test_gateway.py` — `_shape_response` helper, `ScriptedClient` verbatim mode for prebuilt response objects, parametrized three-shape containment test, recovery test

## Decisions Made
- Reused the invalid-JSON containment path verbatim (status "invalid", same exhaustion code) instead of a parallel branch — the identical path JSONDecodeError/ValidationError already take, per the CR-01 spec
- No assistant message on the malformed-path retry: the content may be None/non-str, there is nothing valid to echo back; the appended user correction keeps Pitfall 7 (never resend identical messages)
- Metadata-only discipline on the new log lines: only choice count + content type NAME, never the content value, prompt text, or provider bodies (T-02-05-02 mitigated and test-pinned)

## Deviations from Plan

None - plan executed exactly as written. Scope held to exactly the two `files_modified` entries; no new files, dependencies, or schema/config/logging changes.

## Issues Encountered
- Minor tooling note: the `tdd-red-evidence` checker parses node-TAP summaries; the pytest RED run was validated via a mechanical 1:1 projection of its result (1 ran / 0 passed / 1 failed, target test named) — verdict `RED_EVIDENCE_OK`. The RED itself was genuine: `IndexError: list index out of range` escaping `run_stage` at gateway.py:154, with zero log lines written.

## User Setup Required

None - no external service configuration required. No live-API spend performed; all tests offline with injected fakes.

## Next Phase Readiness
- Phase 2's SC3 containment gap is closed; the gateway now guarantees every response shape terminates as a typed result or a typed `LLMError` with a full runs.jsonl audit trail — the contract the Phase 3 route layer (catching `LLMError` for the PT-BR message path) depends on
- All 5 plans of Phase 2 now have summaries; ready for `/gsd:verify-work 2`

---
*Phase: 02-llm-generation-core*
*Completed: 2026-09-26*

## Self-Check: PASSED

- Files exist on disk: `backend/app/llm/gateway.py`, `backend/tests/test_gateway.py`, this SUMMARY
- All 3 task commits found in git history: `b225f57`, `3f1297e`, `1678e31`
- Measured commits from `plan_head_before` (46bc3e8): 3
- Source assertions hold: `getattr(resp, "choices", None)` guard (gateway.py:157) + `isinstance(content, str)` check (gateway.py:159) before `json.loads`
- Plan-level verification: `uv run pytest tests/test_gateway.py -q` → 15 passed; `uv run pytest -q` → 87 passed, 5 deselected
