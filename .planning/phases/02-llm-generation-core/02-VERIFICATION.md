---
phase: 02-llm-generation-core
verified: 2026-09-26T12:55:57Z
status: gaps_found
score: 12/13 must-haves verified
covered_files:
  - .planning/phases/02-llm-generation-core/02-01-PLAN.md
  - .planning/phases/02-llm-generation-core/02-02-PLAN.md
  - .planning/phases/02-llm-generation-core/02-03-PLAN.md
  - .planning/phases/02-llm-generation-core/02-04-PLAN.md
  - .planning/phases/02-llm-generation-core/02-01-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-02-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-03-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-04-SUMMARY.md
  - .planning/REQUIREMENTS.md
  - .gitignore
  - backend/pyproject.toml
  - backend/app/config.py
  - backend/app/llm/__init__.py
  - backend/app/llm/errors.py
  - backend/app/llm/gateway.py
  - backend/app/llm/logging.py
  - backend/app/llm/prompts.py
  - backend/app/llm/schemas.py
  - prompts/keyword-extraction.md
  - backend/tests/conftest.py
  - backend/tests/llm_fixtures.py
  - backend/tests/test_gateway.py
  - backend/tests/test_keyword_schema.py
  - backend/tests/test_llm_harness.py
  - backend/tests/test_phase2_config.py
  - backend/tests/test_prompt_loader.py
  - backend/tests/test_run_log.py
covered_digest: "v1:sha256:bc015f8e9d7324e9c77b90ee57821b307becddba2086b20f219a160ecde4872c"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "A malformed structured response is caught by validation, retried with the validation error appended, and surfaces a clear failure — malformed content never reaches downstream stages (roadmap SC3; plan 02-03 truth 1)"
    status: partial
    reason: >
      Containment holds for the JSON/Pydantic malformation class (tested offline: recover with appended
      correction, bounded exhaustion, fatal-immediate API errors). But malformed-but-200 response SHAPES
      escape run_stage uncaught: backend/app/llm/gateway.py:154 `resp.choices[0].message.content` raises
      IndexError on empty choices, and gateway.py:156 `json.loads(content)` raises TypeError on None
      content (model refusal / content filter — realistic for the pinned anthropic/claude-sonnet-4.5) or
      non-str content. The except clause (gateway.py:158) catches only (JSONDecodeError, ValidationError).
      Reproduced deterministically with fake clients: all three shapes exit run_stage as raw
      IndexError/TypeError with ZERO runs.jsonl lines — no attempt line, no run_summary — violating the
      phase goal's "logged" property and the D-13/D-14 contract for that class, and surfacing a raw
      exception (not a PT-BR LLMError) to the Phase 3 caller that will catch LLMError. Matches Critical
      finding CR-01 in 02-REVIEW.md. Malformed content itself still never returns downstream (the crash
      prevents it) — one of SC3's four clauses holds, hence partial rather than total failure.
    artifacts:
      - path: backend/app/llm/gateway.py
        issue: "Lines 154-158: response-shape extraction + JSON parse only contain (JSONDecodeError, ValidationError); empty choices / None content / non-str content crash uncontained, with no audit line and no summary"
    missing:
      - "Guard response-shape extraction in run_stage: empty/missing choices and None or non-str content must route through the SAME containment path as invalid content (status 'invalid' attempt line, terminal run_summary, bounded retry with a correction message, LLMError at exhaustion) — fix specified in 02-REVIEW.md CR-01"
      - "An offline test pinning the three malformed shapes (choices=[], content=None, non-str content) proving attempt+summary lines are written, LLMError is raised, and no raw IndexError/TypeError escapes"
---

# Phase 2: LLM Generation Core — Verification Report

**Phase Goal:** Every LLM call flows through one gateway that is logged, schema-validated, bilingual by parameter, and driven by meta-prompts the user can edit as versioned files in git.
**Verified:** 2026-09-26T12:55:57Z
**Status:** gaps_found (1 partial gap — SC3 containment hole for malformed-but-200 response shapes)
**Re-verification:** No — initial verification

**MVP mode note:** ROADMAP.md marks this phase `mode: mvp`, but the phase goal is not a User Story sentence (the `user-story.validate` verb returns `valid: false`). Rather than fabricate a low-quality User Flow Coverage table, verification proceeded goal-backward against the roadmap Success Criteria (the non-negotiable contract) and all PLAN must_haves. No scope was reduced by this.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: User edits a meta-prompt file in git and the next generation run reflects the change with no code edits | ✓ VERIFIED | `prompts/keyword-extraction.md` is git-versioned (commit d1e4d93); `prompts.py:57` re-reads the file every call, no cache; `gateway.py:89` calls `load_prompt(stage)` per call; `test_prompt_file_edit_is_visible_on_next_call` proves the second call's system message carries the edit (passing in the 83-test offline run) |
| 2 | SC2: Fixture harness generates in EN and PT-BR; every call logged (stage, model, tokens/cost); model swap is config-only | ✓ VERIFIED | Live acceptance run 2026-09-26 12:25–12:29 UTC: `logs/runs.jsonl` holds 10 lines = 5 runs (slug probe + JD/OBJECTIVE × en/pt-BR), each with attempt line + `run_summary`, `model: anthropic/claude-sonnet-4.5`, numeric tokens (1048/2499/1891…); `cost` field present, null per the deliberate D-13 contract. Slug literal exists only in `config.py:34` (grep of `backend/app/`); harness asserts `line["model"] == LLM_MODEL`. Orchestrator-confirmed: `uv run pytest -m llm -q` → 5 passed, 0 skipped |
| 3 | SC3: Malformed structured response caught by validation, retried with error appended, clear failure; never downstream | ✗ FAILED (partial) | Validation-class chain fully proven offline (`test_invalid_then_valid_recovers_with_appended_correction`, `test_exhausted_retries_raise_llmerror_after_max_attempts`, `test_api_error_is_fatal_immediate_no_retry`). BUT malformed-but-200 shapes escape: verifier repro (fake clients) → empty `choices` = uncaught IndexError; `content=None` and non-str content = uncaught TypeError; **zero lines written to runs.jsonl** on all three. See Gaps Summary |
| 4 | SC4: Keyword extraction on JD or objective returns {en, pt}-mapped categorized keywords with hooks for later coverage checks | ✓ VERIFIED | `Keyword(canonical, aliases, pt, en, category)` + 4 pinned ASCII categories (`schemas.py`); live harness asserts all 4 categories non-empty per fixture, pt renderings with accents, technology proper nouns pt==en (D-11 spot-check). The covered/adjacent/absent classification itself is Phase 3's RESUME-04; the bilingual+categorized keyword set is the hook, matching the planner's documented SC4 interpretation in 02-04-PLAN |
| 5 | Offline-by-default pytest: llm marker registered, addopts deselect llm tests, zero network in default run (D-15/D-16) | ✓ VERIFIED | `pyproject.toml` markers + `addopts = "-m 'not llm'"`; verifier run: **83 passed, 5 deselected in 1.86s**, no unknown-marker warning; `pytest -m llm --collect-only` enumerates exactly 5; all gateway tests use injected fakes |
| 6 | logs/ gitignored before any run-log writer exists (Pitfall 8) | ✓ VERIFIED | `.gitignore` contains `logs/`; `git check-ignore logs/runs.jsonl` exit 0 |
| 7 | Phase 2 config constants importable: PROMPTS_DIR, LOGS_DIR, RUNS_LOG, LLM_MODEL (env-overridable, default anthropic/claude-sonnet-4.5), LLM_MAX_ATTEMPTS=3 | ✓ VERIFIED | Verifier import check passed: all constants import from `app.config`, `LLM_MAX_ATTEMPTS == 3`, `openai` importable, LLM_MODEL resolves to the pinned default |
| 8 | Prompt file loads/validates strictly; typo'd frontmatter key fails loudly naming key and file; fresh read (D-05..D-08, PROFILE-03) | ✓ VERIFIED | `PromptSpec(extra="forbid")`, try/except ladder mirrors profile loader with PT-BR messages naming path; `test_prompt_loader.py` (6 tests) green in the offline run |
| 9 | Tracer: mocked call flows load_prompt → compose → SDK call → Pydantic validation → typed KeywordExtraction → JSONL line, end-to-end offline | ✓ VERIFIED | `test_happy_path_returns_typed_extraction_and_logs_one_line`: typed result, exactly 1 attempt line + run_summary, all pinned fields, accent integrity, no prompt/response content in log |
| 10 | Retry loop: invalid retried with assistant output + PT-BR correction appended (never identical messages); exhaustion → LLMError after LLM_MAX_ATTEMPTS; API errors fatal-immediate (SC3/D-03/D-04, Pitfall 7) | ✓ VERIFIED | `ScriptedClient` tests assert: 2-call recovery with `["system","user","assistant","user"]` message roles and rendered error embedded; exactly LLM_MAX_ATTEMPTS calls then LLMError mentioning "tentativas"; RuntimeError → 1 attempt, status "error", no retry |
| 11 | Every attempt (ok/invalid/error) writes its own runs.jsonl line with attempt number; field set pinned; UTF-8 accents; append-only crash safety (D-13/D-14) | ✓ VERIFIED (scoped) | `test_run_log.py` pins the 12-field contract verbatim, 3-attempt ascending lines, accent round-trip, summary on ok and LLMError paths, pre-existing line survives (backstop evidence: `test_append_never_truncates_preexisting_lines`). Scope note: holds for attempts that resolve to a status; the CR-01 crash class resolves to none — captured in the SC3 gap, same root cause |
| 12 | Strict JSON Schema dict drift-locked to KeywordExtraction's Pydantic model by test (RESEARCH Pattern 2, T-02-08) | ✓ VERIFIED | `KEYWORD_STRICT_SCHEMA` hand-maintained (never `model_json_schema()` raw); bidirectional property-name tests at top and nested levels, enum equality, strict-shape invariants (`additionalProperties: false` + full `required` at every object level). Caveat (WR-07, warning): property TYPES are not compared — see Anti-Patterns |
| 13 | Harness: slug probe + 4 real runs through the gateway ONLY; no-key → PT-BR skipif; spend failures loud (D-15, A1) | ✓ VERIFIED | `test_llm_harness.py` has slug probe + parametrized 4-case test, all `@pytest.mark.llm` + PT-BR skipif guard; grep confirms no direct SDK import in tests — every real call goes through `gateway.run_stage`; slug probe converts LLMError to a loud `pytest.fail` naming the slug |

**Score:** 12/13 truths verified (0 present-but-behavior-unverified; 1 failed — SC3, partial containment)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/config.py` | Phase 2 constants, slug config-only | ✓ VERIFIED | All constants present, env-overridable model, cap 3; only slug literal in `backend/app/` |
| `backend/app/llm/__init__.py` | Package marker | ✓ VERIFIED | Exists |
| `backend/app/llm/errors.py` | PromptError/LLMError with message_ptbr + raw | ✓ VERIFIED | Exact ProfileError shape; `render_prompt_errors_ptbr` variant (sanctioned deviation, 02-02-SUMMARY) |
| `backend/app/llm/prompts.py` | Strict fresh-read loader, call-time default dir | ✓ VERIFIED | `PromptSpec` extra=forbid; default dir resolved at call time (monkeypatchable, used by tests) |
| `backend/app/llm/schemas.py` | Keyword/KeywordExtraction + strict wire dict | ✓ VERIFIED | 4-token Literal categories, extra=forbid, hand-maintained `KEYWORD_STRICT_SCHEMA` |
| `backend/app/llm/logging.py` | Append-only UTF-8 JSONL writer + run summary | ✓ VERIFIED | `write_run_line` + `write_run_summary`, ensure_ascii=False, mkdir on first write, metadata only |
| `backend/app/llm/gateway.py` | Single choke point: fresh prompt → strict schema call → re-validation → per-attempt log → typed return | ✓ VERIFIED (contains the SC3 gap) | All contracted behaviors present and tested; CR-01 shape hole at lines 154-158 |
| `prompts/keyword-extraction.md` | First versioned meta-prompt | ✓ VERIFIED | Git-versioned (d1e4d93); id/temperature/max_tokens frontmatter; facts-only, bilingual, 4-category body; no template variables |
| `backend/tests/test_prompt_loader.py` | Loader behaviors | ✓ VERIFIED | 6 tests, green |
| `backend/tests/test_gateway.py` | Offline full-path + retry tests | ✓ VERIFIED | 11 tests incl. scripted retry scenarios, green |
| `backend/tests/test_keyword_schema.py` | Drift-lock + strict rejection | ✓ VERIFIED | 9 tests, green (type comparison missing — WR-07) |
| `backend/tests/test_run_log.py` | Pinned JSONL contract | ✓ VERIFIED | 6 tests, green |
| `backend/tests/llm_fixtures.py` + `conftest.py` + `test_llm_harness.py` | Bilingual fixtures + -m llm harness | ✓ VERIFIED | 4 realistic fixtures (offline shape tests green), harness marker-gated, live-run audit lines on disk |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gateway.run_stage` | `prompts/<stage>.md` | `load_prompt` fresh per call (D-08/SC1) | ✓ WIRED | gateway.py:89 → prompts.py:47-57; edit-visibility test green |
| `gateway` | `llm/logging.py` → `config.RUNS_LOG` | `write_run_line`/`write_run_summary` per attempt | ✓ WIRED | gateway.py:31,76-77,111-116; real runs.jsonl lines on disk corroborate |
| `gateway` | `config.LLM_MODEL` (slug nowhere else) | import from config only | ✓ WIRED | grep: slug literal only in config.py:34; tests assert model field == LLM_MODEL |
| `KEYWORD_STRICT_SCHEMA` | `KeywordExtraction` | drift-lock test (T-02-08) | ✓ WIRED | test_keyword_schema.py bidirectional name/enum/shape locks; types not compared (WR-07) |
| retry loop | per-attempt logging | `_log` with attempt number + statuses | ✓ WIRED | test_gateway.py + test_run_log.py assert statuses/attempt ascending |
| `test_llm_harness.py` | `gateway.run_stage` | the ONLY call path (no direct SDK) | ✓ WIRED | grep: no OpenAI import in tests; 5/5 live tests through the gateway |
| harness run | `logs/runs.jsonl` audit | per-run tmp (or real) runs_log assertions | ✓ WIRED | harness asserts stage/model/language/cost-field/tokens per line; real acceptance log on disk |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `run_stage` return | KeywordExtraction | Live OpenRouter chat.completions via openai SDK → Pydantic re-validation | Yes — live run 2026-09-26 (33 keywords JD_PT, 21 keywords OBJECTIVE_PT per 02-04-SUMMARY) | ✓ FLOWING |
| `runs.jsonl` attempt lines | usage/tokens/latency/status | `resp.usage` + client timing per attempt | Yes — numeric token counts (1048/2499/1891) in the real log | ✓ FLOWING |
| `run_summary` line | totals/status_counts | accumulated per-attempt records | Yes — totals match attempt sums (test-pinned) | ✓ FLOWING |

No static returns, hardcoded literals, or mock data flow into production output. `cost: null` is the deliberate D-13 contract (pricing deferred to Phase 5/6 run store), documented in 02-04-SUMMARY — not a stub.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Offline suite green, llm tests deselected, no warnings | `cd backend && uv run pytest -q` | 83 passed, 5 deselected in 1.86s | ✓ PASS |
| logs/ gitignored | `git check-ignore logs/runs.jsonl` | exit 0 | ✓ PASS |
| Config constants importable, cap=3, SDK present | `uv run python -c "from app.config import …; assert LLM_MAX_ATTEMPTS == 3; import openai"` | CONFIG_OK, LLM_MODEL=anthropic/claude-sonnet-4.5 | ✓ PASS |
| 5 llm tests exist (enumeration, no spend) | `uv run pytest -m llm --collect-only -q` | 5 collected (slug probe + 4 fixtures) | ✓ PASS |
| Live harness acceptance (NOT re-run — spend; evidence inspected) | inspect `logs/runs.jsonl` | 10 lines, 5 runs en+pt-BR, model/tokens per attempt, 2026-09-26 12:25–12:29 UTC | ✓ PASS (disk evidence) |
| SC3 containment for malformed-but-200 shapes | verifier repro: fake clients returning `choices=[]`, `content=None`, non-str content | IndexError / TypeError / TypeError escape `run_stage` uncaught; runs.jsonl never created — zero audit lines | ✗ FAIL |

### Probe Execution

No probes declared in any plan and no `scripts/*/tests/probe-*.sh` exist in this repository — Step 7c SKIPPED (nothing to run). The offline/real suite commands above serve as the runnable checks.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PROFILE-03 | 02-01, 02-02, 02-03, 02-04 (all four) | User can edit meta-prompts as versioned files in git to tune generation behavior | ✓ SATISFIED | `prompts/keyword-extraction.md` versioned in git; strict fail-loud loader naming key+file; fresh-read edit reflection proven at gateway level and by design at loader level; live SC2 run proves tuned generation works. REQUIREMENTS.md maps only PROFILE-03 to Phase 2 (marked Complete) — no orphaned requirements |

### Decision Coverage

All 16 trackable CONTEXT.md decisions (D-01..D-16) are honored by shipped artifacts (`check.decision-coverage-verify`: honored 16/16, not_honored []). Gate is non-blocking; recorded for drift review.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| test_gateway.py | PROFILE-03 | 11 | 0 | none | behavioral (message-role sequences, statuses, attempt bounds) | OK |
| test_run_log.py | PROFILE-03 | 6 | 0 | none | value (verbatim field-set pin) | OK |
| test_keyword_schema.py | PROFILE-03 | 9 | 0 | none | value (bidirectional sets, enums, strict shape) | OK (WR-07: no type comparison) |
| test_prompt_loader.py | PROFILE-03 | 6 | 0 | none | value/behavioral | OK |
| test_phase2_config.py | PROFILE-03 | 3 | 0 | none | value | OK (WR-06: env-sensitive default assertion — passes in this env) |
| test_llm_harness.py | PROFILE-03 | 7 (5 llm + 2 offline shape) | 0 disabled — the skipif is the by-design D-15 key guard, not a silenced requirement test; live proof exists (5 passed + disk log) | none | behavioral (live, post-conditions on typed output + audit lines) | OK |

**Disabled tests on requirements:** 0 → no blocker. **Circular patterns:** 0. **Insufficient assertions:** 0.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| backend/app/llm/gateway.py | 154-158 | Unguarded `resp.choices[0].message.content` + narrow except — malformed-but-200 shapes crash uncontained, unlogged (CR-01, deterministically reproduced by verifier) | 🛑 Blocker | Drives gaps_found: SC3 containment + D-13/D-14 audit contract broken for refusal/empty-choices/non-str-content shapes |
| backend/app/llm/gateway.py | 144 | Raw SDK exception text written verbatim into the metadata-only log `error` field (WR-01) | ⚠️ Warning | Metadata-only guarantee rests on provider error bodies never echoing request content; no length bound |
| backend/app/config.py + gateway.py | 18 / 29 | API key bound at import time while docstring claims call-time (WR-02) | ⚠️ Warning | Long-running process started before .env is populated keeps erroring until restart |
| backend/app/llm/prompts.py | 70-74 | `PromptSpec.id` never cross-checked against requested `stage` (WR-03) | ⚠️ Warning | Renamed/copied prompt files pass silently; runs.jsonl can misattribute which prompt produced a run |
| backend/app/llm/prompts.py | 74 | Prompt body never validated non-empty (WR-04) | ⚠️ Warning | Empty body = system message sent empty; wasted spend |
| backend/tests/test_gateway.py | 174-175 | Test pins the shipped prompt's temperature/max_tokens values (WR-05) | ⚠️ Warning | Legitimate prompt tuning (SC1 workflow) breaks CI; should assert pass-through, not file values |
| backend/tests/test_phase2_config.py | 13 | Asserts live env-dependent LLM_MODEL default (WR-06) | ⚠️ Warning | Fails in legitimately configured environments; passes in this one |
| backend/tests/test_keyword_schema.py | 19-65 | Drift-lock compares names/enums/shape but not property types (WR-07) | ⚠️ Warning | T-02-08 guarantee weaker than documented; type drift surfaces only as burned retries |
| backend/app/llm/errors.py | 15,20 | Unused re-export of profile-header renderer (IN-01); prompts.py path traversal gated only by gateway allowlist (IN-02); harness docstring says "numeric cost" but asserts presence (IN-03); prompt promises in-progress marker the schema can't express (IN-04); model-swap schema acceptance proven for pinned slug only (IN-05) | ℹ️ Info | Hygiene/documentation items |

Debt-marker gate: no TBD/FIXME/XXX/HACK markers in any phase file (the single grep hit is a test's own marker blacklist asserting fixtures are pure data). No stubs or empty implementations in production code.

### Human Verification Required

None outstanding. The single manual-only verification from 02-VALIDATION.md (real EN + PT-BR generation quality) was **satisfied**: the user supplied OPENROUTER_API_KEY (repo-root .env), the real harness run completed 5/5 with 0 skipped (2026-09-26), and PT-BR quality evidence is recorded in 02-04-SUMMARY.md. Beyond that, this is an infrastructure/foundation phase (backend gateway core) with no user-facing UI elements; no artificial manual steps are invented, and no ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths exist (the one behavioral gap — SC3 shapes — is FAILED with deterministic evidence, not routed to human).

## Gaps Summary

One gap, one root cause. The phase goal is substantially achieved: all four roadmap Success Criteria are proven — SC1 by test + git-versioned prompts, SC2 by the live bilingual OpenRouter run with per-attempt audit lines and config-only model swap, SC3 for the JSON/Pydantic malformation class by a scripted offline suite, SC4 by the live bilingual categorized extraction. The 83-test offline suite is green, PROFILE-03 is satisfied, all 16 context decisions are honored, and the Phase 5/6 JSONL contract is pinned by test.

The exception is the containment edge of SC3: `run_stage` assumes every 200 response has non-empty `choices` and string `content`. When OpenRouter surfaces a provider error inside HTTP 200 (empty choices) or the pinned Anthropic model refuses (content=None), the gateway dies with a raw IndexError/TypeError — no attempt line, no run summary, no PT-BR LLMError. For those calls the goal's own "logged" property fails, and the future Phase 3 route layer (which will catch LLMError) gets an unhandled exception instead. The defect was flagged Critical by 02-REVIEW.md (CR-01) and is deterministically reproduced by this verification. The fix is small, fully specified in the review, and confined to `backend/app/llm/gateway.py` plus one offline test — a natural `/gsd:plan-phase --gaps` closure.

This does not look like an intentional deviation, so no override is suggested.

---

_Verified: 2026-09-26T12:55:57Z_
_Verifier: Claude (gsd-verifier)_
