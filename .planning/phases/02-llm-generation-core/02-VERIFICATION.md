---
phase: 02-llm-generation-core
verified: 2026-09-26T23:37:51Z
status: passed
score: 13/13 must-haves verified
covered_files:
  - .gitignore
  - .planning/REQUIREMENTS.md
  - .planning/phases/02-llm-generation-core/02-01-PLAN.md
  - .planning/phases/02-llm-generation-core/02-01-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-02-PLAN.md
  - .planning/phases/02-llm-generation-core/02-02-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-03-PLAN.md
  - .planning/phases/02-llm-generation-core/02-03-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-04-PLAN.md
  - .planning/phases/02-llm-generation-core/02-04-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-05-PLAN.md
  - .planning/phases/02-llm-generation-core/02-05-SUMMARY.md
  - backend/app/config.py
  - backend/app/llm/__init__.py
  - backend/app/llm/errors.py
  - backend/app/llm/gateway.py
  - backend/app/llm/logging.py
  - backend/app/llm/prompts.py
  - backend/app/llm/schemas.py
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/llm_fixtures.py
  - backend/tests/test_gateway.py
  - backend/tests/test_keyword_schema.py
  - backend/tests/test_llm_harness.py
  - backend/tests/test_phase2_config.py
  - backend/tests/test_prompt_loader.py
  - backend/tests/test_run_log.py
  - prompts/keyword-extraction.md
covered_digest: "v1:sha256:911c946d6d36724e741c8958fff5d4f9a5e7f7cf3e4dd100fb7ffd1169999c98"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 13/13
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "Guarded extraction still dereferences choices[0].message unguarded (gateway.py:174) — a non-empty choices list whose first choice lacks .message would raise a raw AttributeError (02-REVIEW.md IN-06)"
    category: architectural
    reason: "Carried from the previous verification, unchanged by phase 3 (the diff region is byte-identical). Unreachable through the real OpenAI SDK: response payload parsing happens inside create(), so a missing .message raises there and is contained by the except Exception branch (status 'error' attempt line + immediate LLMError). Reachable only by injecting a client that violates the documented 'OpenAI SDK-compatible chat client' contract (gateway.py:80). No failing test, no reproducible defect on any real call path — including the post-phase-3 live run at 2026-09-26T22:38 UTC. Fix is a two-line getattr extension if ever desired."
    evidence_status: "none provided"
---

# Phase 2: LLM Generation Core — Verification Report (Staleness Re-verification)

**Phase Goal:** Every LLM call flows through one gateway that is logged, schema-validated, bilingual by parameter, and driven by meta-prompts the user can edit as versioned files in git.
**Verified:** 2026-09-26T23:37:51Z
**Status:** passed
**Re-verification:** Yes — staleness check after Phase 3 modified shared LLM files

## Why Re-verified

The previous VERIFICATION.md (2026-09-26T18:18:26Z, passed 13/13) predated Phase 3's commits. Git shows Phase 3 touched the shared LLM surface in exactly two production commits plus one test commit:

| Commit | File(s) | Nature of change |
|--------|---------|------------------|
| `bc64fd7` (03-01) | `backend/app/llm/schemas.py` | +79 lines, PURELY ADDITIVE — `Keyword`, `KeywordExtraction`, `KEYWORD_STRICT_SCHEMA` byte-untouched; resume section models/wire schemas appended after |
| `0613c1f` (03-01) | `backend/app/llm/gateway.py` | Additive: 3 resume stages registered in `_STAGE_SCHEMAS`, imports widened, return annotation `KeywordExtraction` → `BaseModel`. Diff confirms ZERO changes to message plumbing, the CR-01 shape guard, the retry loop, logging calls, or exhaustion path |
| `7e5ada9` (3-5) | `backend/tests/test_llm_harness.py` | Additive: 2 new llm-marked pipeline tests appended; all Phase 2 keyword-harness tests untouched |

`git diff 3f1297e..HEAD` across every other Phase-2-owned file (`prompts.py`, `logging.py`, `errors.py`, `config.py`, `__init__.py`, `prompts/keyword-extraction.md`, `test_prompt_loader.py`, `test_keyword_schema.py`, `test_run_log.py`, `conftest.py`, `llm_fixtures.py`, `test_phase2_config.py`) is EMPTY — none were touched after the gap closure. The annotation loosening does not weaken the typed-return contract: the concrete model still comes from `_STAGE_SCHEMAS` and strict `model_validate` is unchanged; tests still assert `isinstance(result, KeywordExtraction)` for the keyword stage.

All 13 truths were re-assessed against the CURRENT codebase: full-depth re-read of the two modified shared files, fresh test execution, fresh greps — none taken from the prior report.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence (fresh, this verification) |
|---|-------|--------|--------------------------------------|
| 1 | SC1: User edits a meta-prompt file in git and the next generation run reflects the change with no code edits | ✓ VERIFIED | `prompts/keyword-extraction.md` still git-versioned (d1e4d93, `git ls-files` re-run; 3 resume prompts added alongside by Phase 3, also versioned); `grep cache prompts.py` clean (file untouched since gap closure); current gateway.py:105 `load_prompt(stage)` fresh per call; `test_prompt_file_edit_is_visible_on_next_call` green in this run's suite |
| 2 | SC2: Fixture harness generates in EN and PT-BR; every call logged (stage, model, tokens/cost); model swap is config-only | ✓ VERIFIED | Live evidence on disk re-inspected: `logs/runs.jsonl` now 12 lines / 6 run_summaries — including a NEW live run at **2026-09-26T22:38 UTC, AFTER Phase 3's gateway commits (21:22–21:26 UTC)**: stage keyword-extraction, status "ok", outcome "ok", numeric tokens 982/71/1053, model anthropic/claude-sonnet-4.5 — a real successful call through the CURRENT refactored gateway. Both languages (en, pt-BR) present across the log. 7 llm tests collect (`-m llm --collect-only`: 7/190), deselected by default |
| 3 | SC3: Malformed structured response caught by validation, retried with error appended, clear failure; never downstream | ✓ VERIFIED | Current gateway.py:170-205 CR-01 guard intact and byte-identical to the verified fix (`getattr(resp, "choices", None) or []`, `choices[0].message.content if choices else None`, `isinstance/strip` branch → shared containment path: status "invalid" lines with metadata-only descriptors, PT-BR correction, `_summarize("invalid")` at exhaustion, LLMError). All shape/recovery pins present in current test_gateway.py (lines 319-392, incl. the +29 the diff range attributes past the guard commit) and green in this run's suite (183 passed) |
| 4 | SC4: Keyword extraction on JD or objective returns {en, pt}-mapped categorized keywords with hooks for later coverage checks | ✓ VERIFIED | Current schemas.py lines 1-37: `Keyword(canonical, aliases, pt, en, category)` + 4 pinned ASCII categories + `KeywordExtraction` — byte-untouched by `bc64fd7` (additions start at line 38); `KEYWORD_STRICT_SCHEMA` intact (gateway still references it twice: import + `_STAGE_SCHEMAS["keyword-extraction"]` at gateway.py:50); `test_keyword_schema.py` (9 tests) green in this run |
| 5 | Offline-by-default pytest: llm marker registered, addopts deselect llm tests, zero network in default run (D-15/D-16) | ✓ VERIFIED | This verification's run: **183 passed, 7 deselected in 1.63s**, no warnings (deselected grew 5→7 — Phase 3 added 2 pipeline llm tests; default suite still fully offline) |
| 6 | logs/ gitignored before any run-log writer exists (Pitfall 8) | ✓ VERIFIED | `git check-ignore logs/runs.jsonl` exit 0 (re-run this pass) |
| 7 | Phase 2 config constants importable: PROMPTS_DIR, LOGS_DIR, RUNS_LOG, LLM_MODEL (env-overridable, default anthropic/claude-sonnet-4.5), LLM_MAX_ATTEMPTS=3 | ✓ VERIFIED | Import check re-run: CONFIG_OK, LLM_MAX_ATTEMPTS == 3, openai importable, pinned default resolves; slug literal only in `config.py` (grep re-run: zero hits elsewhere in backend/app) |
| 8 | Prompt file loads/validates strictly; typo'd frontmatter key fails loudly naming key and file; fresh read (D-05..D-08, PROFILE-03) | ✓ VERIFIED | `prompts.py` untouched since gap closure (`PromptSpec(extra="forbid")` intact); `test_prompt_loader.py` (6 tests) green in this run |
| 9 | Tracer: mocked call flows load_prompt → compose → SDK call → Pydantic validation → typed KeywordExtraction → JSONL line, end-to-end offline | ✓ VERIFIED | `test_happy_path_returns_typed_extraction_and_logs_one_line` green in this run against the current gateway (unchanged machinery) |
| 10 | Retry loop: invalid retried with assistant output + PT-BR correction appended (never identical messages); exhaustion → LLMError after LLM_MAX_ATTEMPTS; API errors fatal-immediate (SC3/D-03/D-04, Pitfall 7) | ✓ VERIFIED | Current gateway.py:134-262: retry loop, message-append branches (validation path appends assistant+user, malformed path appends user-only), fatal `except Exception` → 1 attempt + status "error" + immediate LLMError — all present, all scripted tests green in this run's suite |
| 11 | Every attempt (ok/invalid/error) writes its own runs.jsonl line with attempt number; field set pinned; UTF-8 accents; append-only crash safety (D-13/D-14) | ✓ VERIFIED | `logging.py` untouched since gap closure; `test_run_log.py` (6 tests) green in this run; the live log's real lines carry the pinned field set (re-inspected) |
| 12 | Strict JSON Schema dict drift-locked to KeywordExtraction's Pydantic model by test (RESEARCH Pattern 2, T-02-08) | ✓ VERIFIED | `KEYWORD_STRICT_SCHEMA` + `KeywordExtraction` both byte-untouched; `test_keyword_schema.py` (9 tests) green in this run; Phase 3 added a generalized drift-lock harness (`test_resume_schema.py`) for its own schemas — keyword lock unchanged (WR-07 caveat remains, unchanged) |
| 13 | Harness: slug probe + 4 real runs through the gateway ONLY; no-key → PT-BR skipif; spend failures loud (D-15, A1) | ✓ VERIFIED | Current test_llm_harness.py: Phase 2's keyword tests byte-untouched (`7e5ada9` appended only); the docstring's call-path contract now reads "run_stage or run_resume_pipeline — the ONLY call paths" (still gateway-only for the keyword stage, satisfying the no-bespoke-SDK prohibition); 7 llm tests collect; live 5/5 evidence on disk PLUS the post-phase-3 live ok run at 22:38 UTC |

**Score:** 13/13 truths verified (0 present-but-behavior-unverified)

**Verdict changes vs previous report: NONE.** All 13 truths remain VERIFIED against the current codebase; the shared-file refactors were verified additive and non-regressive.

### Advisory (New Scope, Unevidenced)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | gateway.py:174 dereferences `choices[0].message` unguarded — raw AttributeError if an injected choice lacks `.message` (IN-06, 02-REVIEW.md) | architectural | carried, unchanged by Phase 3 — unreachable through the real OpenAI SDK (payload parsing inside `create()` is contained by the `except Exception` branch → "error" line + LLMError); reachable only via a client violating the documented SDK-compatible contract; the post-phase-3 live run confirms no defect on the real path |

Carried warnings (unchanged — all their host files are untouched since the gap closure): WR-01 (raw SDK exception text into the log `error` field, gateway.py:160), WR-02 (API key bound at import time, config.py), WR-03/WR-04 (`PromptSpec.id` not cross-checked vs stage; body not validated non-empty, prompts.py), WR-05 (test pins shipped prompt's temperature/max_tokens, test_gateway.py), WR-06 (env-dependent default assertion, test_phase2_config.py), WR-07 (drift-lock compares names/enums/shape but not types, test_keyword_schema.py).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/config.py` | Phase 2 constants, slug config-only | ✓ VERIFIED | Untouched since gap closure; import check re-run green |
| `backend/app/llm/__init__.py` | Package marker | ✓ VERIFIED | Untouched |
| `backend/app/llm/errors.py` | PromptError/LLMError with message_ptbr + raw | ✓ VERIFIED | Untouched |
| `backend/app/llm/prompts.py` | Strict fresh-read loader, call-time default dir | ✓ VERIFIED | Untouched; no cache (grep re-run) |
| `backend/app/llm/schemas.py` | Keyword/KeywordExtraction + strict wire dict | ✓ VERIFIED | Keyword block byte-untouched; Phase 3 additions purely appended |
| `backend/app/llm/logging.py` | Append-only UTF-8 JSONL writer + run summary | ✓ VERIFIED | Untouched |
| `backend/app/llm/gateway.py` | Single choke point: fresh prompt → strict schema call → re-validation → per-attempt log → typed return | ✓ VERIFIED | All Phase 2 machinery intact in current file; Phase 3 added 3 `_STAGE_SCHEMAS` entries + annotation only |
| `prompts/keyword-extraction.md` | First versioned meta-prompt | ✓ VERIFIED | Git-versioned (d1e4d93, re-confirmed) |
| `backend/tests/test_prompt_loader.py` | Loader behaviors | ✓ VERIFIED | 6 tests green in this run |
| `backend/tests/test_gateway.py` | Offline full-path + retry + malformed-shape tests | ✓ VERIFIED | All 15 tests green in this run's suite; shape/recovery pins present in current file |
| `backend/tests/test_keyword_schema.py` | Drift-lock + strict rejection | ✓ VERIFIED | 9 tests green (WR-07 caveat unchanged) |
| `backend/tests/test_run_log.py` | Pinned JSONL contract | ✓ VERIFIED | 6 tests green |
| `backend/tests/llm_fixtures.py` + `conftest.py` + `test_llm_harness.py` | Bilingual fixtures + -m llm harness | ✓ VERIFIED | Fixtures/conftest untouched; harness file additive-only; 7 llm tests collect; live evidence on disk |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gateway.run_stage` | `prompts/<stage>.md` | `load_prompt` fresh per call (D-08/SC1) | ✓ WIRED | gateway.py:105; edit-visibility test green in this run |
| `gateway` | `llm/logging.py` → `config.RUNS_LOG` | `write_run_line`/`write_run_summary` per attempt | ✓ WIRED | Covers ALL shapes incl. malformed-but-200; live log lines on disk confirm |
| `gateway` | `config.LLM_MODEL` (slug nowhere else) | import from config only | ✓ WIRED | grep re-run: slug literal only in config.py |
| `KEYWORD_STRICT_SCHEMA` | `KeywordExtraction` | drift-lock test (T-02-08) | ✓ WIRED | Both representations byte-untouched; test_keyword_schema.py green (WR-07 caveat) |
| retry loop | per-attempt logging | `_log` with attempt number + statuses | ✓ WIRED | Current gateway.py:127-132/182-192/212-222/244-252; asserted by green tests |
| `test_llm_harness.py` | `gateway.run_stage` | the ONLY call path for keyword runs (no direct SDK) | ✓ WIRED | Phase 2 keyword tests unchanged; Phase 3's pipeline tests also route through run_stage via run_resume_pipeline |
| harness run | `logs/runs.jsonl` audit | per-run tmp (or real) runs_log assertions | ✓ WIRED | Real log on disk re-inspected, incl. the post-phase-3 22:38 UTC run |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `run_stage` return | KeywordExtraction | Live OpenRouter chat.completions via openai SDK → Pydantic re-validation | Yes — live runs on disk incl. one THROUGH the current post-phase-3 gateway (22:38 UTC, status ok) | ✓ FLOWING |
| `runs.jsonl` attempt lines | usage/tokens/latency/status | `resp.usage` + client timing per attempt | Yes — numeric token counts in the real log (982/71/1053 on the newest run) | ✓ FLOWING |
| `run_summary` line | totals/status_counts | accumulated per-attempt records | Yes — 6 summary lines on disk, all outcome "ok" | ✓ FLOWING |

No static returns, hardcoded literals, or mock data flow into production output. `cost: null` remains the deliberate D-13 contract (pricing deferred to Phase 5/6 run store) — not a stub.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full offline suite green, llm tests deselected | `cd backend && uv run pytest -q` (single full run) | **183 passed, 7 deselected in 1.63s**, no warnings | ✓ PASS |
| logs/ gitignored | `git check-ignore logs/runs.jsonl` | exit 0 | ✓ PASS |
| Config constants importable, cap=3, SDK present | `uv run python -c "from app.config import …; assert LLM_MAX_ATTEMPTS == 3; import openai"` | CONFIG_OK, pinned slug `anthropic/claude-sonnet-4.5` | ✓ PASS |
| llm tests exist (enumeration, no spend) | `uv run pytest -m llm --collect-only -q` | 7/190 collected | ✓ PASS |
| Slug literal confined to config | `grep -rn "anthropic/claude-sonnet" backend/app/` (excl. config.py) | zero hits | ✓ PASS |
| No prompt cache | `grep -n "lru_cache\|cache" backend/app/llm/prompts.py` | zero hits | ✓ PASS |
| Live harness acceptance (NOT re-run — spend; disk evidence re-inspected) | inspect `logs/runs.jsonl` | 12 lines, 6 runs, both languages, per-attempt + summary, newest run 2026-09-26T22:38 UTC through the CURRENT gateway | ✓ PASS (disk evidence) |

### Probe Execution

No probes declared in any Phase 2 plan and no `scripts/*/tests/probe-*.sh` exist in this repository — Step 7c SKIPPED (nothing to run). The pytest commands above serve as the runnable checks.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PROFILE-03 | 02-01, 02-02, 02-03, 02-04, 02-05 (all five) | User can edit meta-prompts as versioned files in git to tune generation behavior | ✓ SATISFIED | Prompt file versioned in git (plus 3 Phase-3 prompt files joining it); strict fail-loud loader; fresh-read edit reflection test-proven against the current gateway; live tuned generation on disk incl. a post-refactor run. Phase 3's additive refactors did not weaken the requirement — they extended the same prompt-file/gateway pattern. REQUIREMENTS.md maps only PROFILE-03 to Phase 2 (marked Complete) — no orphaned requirements |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| backend/app/llm/gateway.py | 174 | `choices[0].message` dereference unguarded (IN-06) | ℹ️ Info | Advisory only — unreachable through the real OpenAI SDK; confirmed live-safe by the post-phase-3 run |
| backend/app/llm/gateway.py | 160 | Raw SDK exception text in log `error` field (WR-01) | ⚠️ Warning | Carried, unchanged |
| backend/app/config.py | 18 | API key bound at import time (WR-02) | ⚠️ Warning | Carried |
| backend/app/llm/prompts.py | 70-74 | `PromptSpec.id` not cross-checked vs stage (WR-03); body not validated non-empty (WR-04) | ⚠️ Warning | Carried |
| backend/tests/test_gateway.py | ~190 | Test pins shipped prompt's temperature/max_tokens (WR-05) | ⚠️ Warning | Carried |
| backend/tests/test_phase2_config.py | 13 | Env-dependent default assertion (WR-06) | ⚠️ Warning | Carried |
| backend/tests/test_keyword_schema.py | 19-65 | Drift-lock compares names/enums/shape, not types (WR-07) | ⚠️ Warning | Carried |

Debt-marker gate: re-scanned all shared files modified since the gap closure (`gateway.py`, `schemas.py`, `test_gateway.py`, `test_llm_harness.py`) — zero real TBD/FIXME/XXX/HACK markers (the single grep hit is the harness's own anti-placeholder assertion string, which tests that fixtures contain no such markers), zero stub implementations, no empty handlers, no placeholder returns.

### Human Verification Required

None outstanding. Infrastructure/foundation phase — no user-facing UI. The single manual-only item (real EN + PT-BR generation quality) was satisfied by the 5/5 live run with user-confirmed PT-BR quality (02-04 checkpoint), and is now FURTHER supported by a live run at 2026-09-26T22:38 UTC executed through the current post-phase-3 gateway (status ok, numeric tokens). No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths — every behavior-dependent truth (containment, retry/exhaustion transitions, recovery, audit ordering) has a named passing test executed in this verification's suite run.

## Gaps Summary

None. This staleness re-verification confirms the Phase 3 refactors were strictly additive to the shared LLM surface:

1. `schemas.py` — Keyword contract and wire schema byte-untouched; resume models appended.
2. `gateway.py` — all Phase 2 machinery (shape guard, retry loop, containment, per-attempt logging, exhaustion, fatal-error path, fresh prompt load, config-only model, injectable client, call-time key check) byte-identical; three new stage registrations and a return-annotation widening only. The keyword-extraction stage's wiring is unchanged.
3. `test_llm_harness.py` — Phase 2 tests untouched; two llm-marked pipeline tests appended.

All four roadmap Success Criteria hold against the current code: SC1 (edit-visibility test + git-versioned prompts), SC2 (live bilingual runs with per-attempt audit + config-only model swap — now including a post-refactor live run), SC3 (validation-class and shape-class containment, offline-pinned), SC4 (bilingual categorized extraction). PROFILE-03 is satisfied with no orphaned requirements, and the phase goal — one logged, schema-validated, bilingual-by-parameter, meta-prompt-driven gateway — is achieved in the current codebase.

---

_Verified: 2026-09-26T23:37:51Z_
_Verifier: Claude (gsd-verifier)_
