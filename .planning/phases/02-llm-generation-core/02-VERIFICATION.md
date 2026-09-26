---
phase: 02-llm-generation-core
verified: 2026-09-26T18:18:26Z
status: passed
score: 13/13 must-haves verified
covered_files:
  - .planning/phases/02-llm-generation-core/02-01-PLAN.md
  - .planning/phases/02-llm-generation-core/02-02-PLAN.md
  - .planning/phases/02-llm-generation-core/02-03-PLAN.md
  - .planning/phases/02-llm-generation-core/02-04-PLAN.md
  - .planning/phases/02-llm-generation-core/02-05-PLAN.md
  - .planning/phases/02-llm-generation-core/02-01-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-02-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-03-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-04-SUMMARY.md
  - .planning/phases/02-llm-generation-core/02-05-SUMMARY.md
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
covered_digest: "v1:sha256:5b6c14458d3c864ee0ddac03ab6211c063a99f294c093e54ea16678c43b64220"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 12/13
  gaps_closed:
    - "SC3 malformed-but-200 response-shape containment: empty choices / content=None / non-str content now route through the SAME containment path as invalid content (invalid attempt lines, terminal run_summary, bounded retry with PT-BR correction, LLMError at exhaustion) — CR-01 fixed in gateway.py and pinned offline by test_gateway.py"
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "Guarded extraction still dereferences choices[0].message unguarded (gateway.py:158) — a non-empty choices list whose first choice lacks .message would raise a raw AttributeError (02-REVIEW.md IN-06)"
    category: architectural
    reason: "New-scope residue of the CR-01 fix, surfaced by the re-review. Unreachable through the real OpenAI SDK: response payload parsing happens inside create(), so a missing .message raises there and is contained by the except Exception branch (status 'error' attempt line + immediate LLMError). Reachable only by injecting a client that violates the documented 'OpenAI SDK-compatible chat client' contract (gateway.py:66). No failing test, no reproducible defect on any real call path. Fix is a two-line getattr extension if ever desired."
    evidence_status: "none provided"
---

# Phase 2: LLM Generation Core — Verification Report (Re-verification)

**Phase Goal:** Every LLM call flows through one gateway that is logged, schema-validated, bilingual by parameter, and driven by meta-prompts the user can edit as versioned files in git.
**Verified:** 2026-09-26T18:18:26Z
**Status:** passed
**Re-verification:** Yes — after gap closure (02-05, commits b225f57 RED → 3f1297e guard → 1678e31 pins+recovery → ba41bb6 docs)

**MVP mode note:** unchanged from the initial verification — ROADMAP.md marks this phase `mode: mvp`, but the goal is not a User Story sentence (`user-story.validate` → `valid: false`). Verification proceeded goal-backward against the roadmap Success Criteria and all PLAN must_haves; no scope was reduced.

## Goal Achievement

### Observable Truths

All 13 truths from the initial verification's must-have contract were re-assessed: the one gap truth at full depth (exists / substantive / wired / behavior), the other 12 by regression spot-check (existence + the automated evidence re-run).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: User edits a meta-prompt file in git and the next generation run reflects the change with no code edits | ✓ VERIFIED | `prompts/keyword-extraction.md` git-versioned (d1e4d93, re-confirmed); `prompts.py` has no cache (grep clean); `gateway.py:89` calls `load_prompt(stage)` per call; `test_prompt_file_edit_is_visible_on_next_call` PASSED in this verification's gateway run (15/15) |
| 2 | SC2: Fixture harness generates in EN and PT-BR; every call logged (stage, model, tokens/cost); model swap is config-only | ✓ VERIFIED | Live acceptance run on disk: `logs/runs.jsonl` 10 lines, timestamps 2026-09-26T12:25–12:29 UTC, model anthropic/claude-sonnet-4.5, numeric tokens (982/66/1048…), both languages, per-attempt + run_summary lines — re-inspected this pass. The gap-closure guard (17:48+ UTC) does not touch the valid-content path: for non-empty str content the new `isinstance/strip` branch is False and flow is identical to the pre-fix code (verified by reading the diff region); the full offline suite exercising run_stage end-to-end is green post-change, and `test_llm_harness.py` is byte-identical (only gateway.py + test_gateway.py changed — git-verified). 5 llm tests still collect (`--collect-only`: 5/92) |
| 3 | SC3: Malformed structured response caught by validation, retried with error appended, clear failure; never downstream — **THE GAP, now closed** | ✓ VERIFIED | CR-01 guard present (gateway.py:157-159: `getattr(resp, "choices", None) or []`, `choices[0].message.content if choices else None`, `isinstance(content, str)/strip` branch) and routed into the SAME containment flow as invalid JSON (status "invalid" line with metadata-only descriptors, `_summarize("invalid")` at the shared exhaustion path, LLMError). Behavior proven by tests executed in THIS verification: `test_malformed_response_shapes_contained_like_invalid_content[empty-choices|content-none|content-non-str]` + `test_malformed_shape_then_valid_recovers_with_correction` all PASSED (verbose run: 4/4) — `pytest.raises(LLMError)` (no raw IndexError/TypeError), exactly LLM_MAX_ATTEMPTS calls, ascending invalid attempt lines carrying "conteúdo ausente ou não-textual" + correct type NAME, terminal run_summary outcome "invalid", metadata-only (`TEXTO-SECRETO-DO-USUARIO`/`bloco` absent from log); recovery returns typed KeywordExtraction with statuses ["invalid","ok"], roles ["system","user","user"]. TDD held: b225f57 (test-only RED) → 3f1297e (guard, production-only) |
| 4 | SC4: Keyword extraction on JD or objective returns {en, pt}-mapped categorized keywords with hooks for later coverage checks | ✓ VERIFIED | Unchanged since initial verification (schemas.py + prompt untouched by gap commits): `Keyword(canonical, aliases, pt, en, category)` + 4 pinned ASCII categories; live categorized bilingual extraction on disk; `test_keyword_schema.py` green in this run |
| 5 | Offline-by-default pytest: llm marker registered, addopts deselect llm tests, zero network in default run (D-15/D-16) | ✓ VERIFIED | This verification's run: **87 passed, 5 deselected in 1.17s**, no warnings; `pytest -m llm --collect-only` enumerates exactly 5; the three malformed shapes are pinned with injected fakes (zero network) |
| 6 | logs/ gitignored before any run-log writer exists (Pitfall 8) | ✓ VERIFIED | `git check-ignore logs/runs.jsonl` exit 0 (re-run this pass) |
| 7 | Phase 2 config constants importable: PROMPTS_DIR, LOGS_DIR, RUNS_LOG, LLM_MODEL (env-overridable, default anthropic/claude-sonnet-4.5), LLM_MAX_ATTEMPTS=3 | ✓ VERIFIED | Import check re-run: CONFIG_OK, LLM_MAX_ATTEMPTS == 3, openai importable, pinned default resolves; slug literal only in `config.py:34` (grep re-run) |
| 8 | Prompt file loads/validates strictly; typo'd frontmatter key fails loudly naming key and file; fresh read (D-05..D-08, PROFILE-03) | ✓ VERIFIED | `PromptSpec(extra="forbid")` unchanged; `test_prompt_loader.py` (6 tests) green in this run |
| 9 | Tracer: mocked call flows load_prompt → compose → SDK call → Pydantic validation → typed KeywordExtraction → JSONL line, end-to-end offline | ✓ VERIFIED | `test_happy_path_returns_typed_extraction_and_logs_one_line` green in this run |
| 10 | Retry loop: invalid retried with assistant output + PT-BR correction appended (never identical messages); exhaustion → LLMError after LLM_MAX_ATTEMPTS; API errors fatal-immediate (SC3/D-03/D-04, Pitfall 7) | ✓ VERIFIED | All three scripted tests green in this run (validation-path recovery roles ["system","user","assistant","user"], bounded exhaustion with "tentativas", RuntimeError → 1 attempt status "error") |
| 11 | Every attempt (ok/invalid/error) writes its own runs.jsonl line with attempt number; field set pinned; UTF-8 accents; append-only crash safety (D-13/D-14) | ✓ VERIFIED | `test_run_log.py` green; the initial verification's scope note (crash-class resolves to no status) is now moot — every malformed shape also resolves to status "invalid" lines + summary (truth 3) |
| 12 | Strict JSON Schema dict drift-locked to KeywordExtraction's Pydantic model by test (RESEARCH Pattern 2, T-02-08) | ✓ VERIFIED | `test_keyword_schema.py` (9 tests) green in this run; WR-07 caveat (types not compared) remains a carried warning, unchanged |
| 13 | Harness: slug probe + 4 real runs through the gateway ONLY; no-key → PT-BR skipif; spend failures loud (D-15, A1) | ✓ VERIFIED | `test_llm_harness.py` byte-identical through the gap round; offline shape tests green; 5 llm tests enumerate; live 5/5 evidence on disk + orchestrator-confirmed 2026-09-26 |

**Score:** 13/13 truths verified (0 present-but-behavior-unverified)

### Advisory (New Scope, Unevidenced)

New-scope findings from Step 7 with no deterministic evidence — reported, not blocking. Included because re-verification ran.

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | gateway.py:158 dereferences `choices[0].message` unguarded — raw AttributeError if an injected choice lacks `.message` (IN-06, 02-REVIEW.md) | architectural | new-scope, no deterministic evidence — unreachable through the real OpenAI SDK (payload parsing inside `create()` is contained by the `except Exception` branch → "error" line + LLMError); reachable only via a client violating the documented SDK-compatible contract |

Carried from the initial verification (unchanged, non-blocking, none addressed or worsened by the gap round): WR-01 (raw SDK exception text into the log `error` field), WR-02 (API key bound at import time), WR-03 (`PromptSpec.id` not cross-checked against stage), WR-04 (prompt body not validated non-empty), WR-05 (test pins shipped prompt's temperature/max_tokens), WR-06 (config test asserts live env default), WR-07 (drift-lock compares names/enums/shape but not types). All predate the gap-closure round, were treated as warnings then, and remain warnings.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/config.py` | Phase 2 constants, slug config-only | ✓ VERIFIED | Re-checked: constants present, env-overridable model, cap 3 |
| `backend/app/llm/__init__.py` | Package marker | ✓ VERIFIED | Exists (untouched by gap round) |
| `backend/app/llm/errors.py` | PromptError/LLMError with message_ptbr + raw | ✓ VERIFIED | Unchanged |
| `backend/app/llm/prompts.py` | Strict fresh-read loader, call-time default dir | ✓ VERIFIED | Unchanged; no cache (grep) |
| `backend/app/llm/schemas.py` | Keyword/KeywordExtraction + strict wire dict | ✓ VERIFIED | Unchanged |
| `backend/app/llm/logging.py` | Append-only UTF-8 JSONL writer + run summary | ✓ VERIFIED | Unchanged; the new containment path feeds it unchanged |
| `backend/app/llm/gateway.py` | Single choke point: fresh prompt → strict schema call → re-validation → per-attempt log → typed return | ✓ VERIFIED | CR-01 guard in place (lines 154-189); all behaviors present and test-pinned |
| `prompts/keyword-extraction.md` | First versioned meta-prompt | ✓ VERIFIED | Git-versioned (d1e4d93, re-confirmed) |
| `backend/tests/test_prompt_loader.py` | Loader behaviors | ✓ VERIFIED | 6 tests green |
| `backend/tests/test_gateway.py` | Offline full-path + retry + malformed-shape tests | ✓ VERIFIED | **15 tests green in this run** — 11 prior + 3 shape params + 1 recovery |
| `backend/tests/test_keyword_schema.py` | Drift-lock + strict rejection | ✓ VERIFIED | 9 tests green (WR-07 caveat unchanged) |
| `backend/tests/test_run_log.py` | Pinned JSONL contract | ✓ VERIFIED | 6 tests green |
| `backend/tests/llm_fixtures.py` + `conftest.py` + `test_llm_harness.py` | Bilingual fixtures + -m llm harness | ✓ VERIFIED | Byte-identical through the gap round; offline shape tests green; live evidence on disk |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `gateway.run_stage` | `prompts/<stage>.md` | `load_prompt` fresh per call (D-08/SC1) | ✓ WIRED | gateway.py:89; edit-visibility test green in this run |
| `gateway` | `llm/logging.py` → `config.RUNS_LOG` | `write_run_line`/`write_run_summary` per attempt | ✓ WIRED | Now covers ALL shapes including malformed-but-200 (the closed gap's core) |
| `gateway` | `config.LLM_MODEL` (slug nowhere else) | import from config only | ✓ WIRED | grep re-run: slug literal only in config.py:34 |
| `KEYWORD_STRICT_SCHEMA` | `KeywordExtraction` | drift-lock test (T-02-08) | ✓ WIRED | test_keyword_schema.py green (types-not-compared caveat = WR-07, warning) |
| retry loop | per-attempt logging | `_log` with attempt number + statuses | ✓ WIRED | Ascending attempts + statuses asserted by tests run in this pass, including on the malformed-shape path |
| `test_llm_harness.py` | `gateway.run_stage` | the ONLY call path (no direct SDK) | ✓ WIRED | Unchanged; 5 llm tests collect |
| harness run | `logs/runs.jsonl` audit | per-run tmp (or real) runs_log assertions | ✓ WIRED | Real acceptance log on disk re-inspected |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `run_stage` return | KeywordExtraction | Live OpenRouter chat.completions via openai SDK → Pydantic re-validation | Yes — live run 2026-09-26 on disk (unchanged path post-guard for valid content) | ✓ FLOWING |
| `runs.jsonl` attempt lines | usage/tokens/latency/status | `resp.usage` + client timing per attempt | Yes — numeric token counts in the real log | ✓ FLOWING |
| `run_summary` line | totals/status_counts | accumulated per-attempt records | Yes — test-pinned, now including the malformed-shape class | ✓ FLOWING |

No static returns, hardcoded literals, or mock data flow into production output. `cost: null` remains the deliberate D-13 contract (pricing deferred to Phase 5/6 run store) — not a stub.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full offline suite green, llm tests deselected | `cd backend && uv run pytest -q` | **87 passed, 5 deselected in 1.17s** | ✓ PASS |
| Gateway file incl. all new pins | `cd backend && uv run pytest tests/test_gateway.py -q` | **15 passed in 0.36s** | ✓ PASS |
| Malformed-shape containment + recovery (the gap) | `cd backend && uv run pytest tests/test_gateway.py -k malformed -v` | 4 passed — empty-choices, content-none, content-non-str, recovery | ✓ PASS |
| logs/ gitignored | `git check-ignore logs/runs.jsonl` | exit 0 | ✓ PASS |
| Config constants importable, cap=3, SDK present | `uv run python -c "from app.config import …; assert LLM_MAX_ATTEMPTS == 3; import openai"` | CONFIG_OK, pinned slug, key set | ✓ PASS |
| 5 llm tests exist (enumeration, no spend) | `uv run pytest -m llm --collect-only -q` | 5/92 collected | ✓ PASS |
| Live harness acceptance (NOT re-run — spend; disk evidence re-inspected) | inspect `logs/runs.jsonl` | 10 lines, 5 runs en+pt-BR, model/tokens per attempt, 2026-09-26 12:25–12:29 UTC | ✓ PASS (disk evidence) |

### Probe Execution

No probes declared in any plan (including 02-05) and no `scripts/*/tests/probe-*.sh` exist in this repository — Step 7c SKIPPED (nothing to run). The pytest commands above serve as the runnable checks.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PROFILE-03 | 02-01, 02-02, 02-03, 02-04, 02-05 (all five) | User can edit meta-prompts as versioned files in git to tune generation behavior | ✓ SATISFIED | `prompts/keyword-extraction.md` versioned in git; strict fail-loud loader; fresh-read edit reflection test-proven; live SC2 run proves tuned generation; the gap closure STRENGTHENED the requirement's reliability (every response shape now terminates as typed result or typed LLMError with a full audit trail). REQUIREMENTS.md maps only PROFILE-03 to Phase 2 (marked Complete) — no orphaned requirements |

### Decision Coverage

All 16 trackable CONTEXT.md decisions (D-01..D-16) are honored by shipped artifacts (`check.decision-coverage-verify` re-run this pass: honored 16/16, not_honored []). Gate is non-blocking; recorded for drift review.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| test_gateway.py | PROFILE-03 | 15 | 0 | none | behavioral (shape containment, message-role sequences, statuses, attempt bounds, metadata-only negative assertions) | OK |
| test_run_log.py | PROFILE-03 | 6 | 0 | none | value (verbatim field-set pin) | OK |
| test_keyword_schema.py | PROFILE-03 | 9 | 0 | none | value (bidirectional sets, enums, strict shape) | OK (WR-07: no type comparison) |
| test_prompt_loader.py | PROFILE-03 | 6 | 0 | none | value/behavioral | OK |
| test_phase2_config.py | PROFILE-03 | 3 | 0 | none | value | OK (WR-06 caveat) |
| test_llm_harness.py | PROFILE-03 | 7 (5 llm + 2 offline shape) | 0 disabled — the skipif is the by-design D-15 key guard; live proof exists (5/5 + disk log) | none | behavioral (live post-conditions) | OK |

**Disabled tests on requirements:** 0 → no blocker. **Circular patterns:** 0. **Insufficient assertions:** 0. The new malformed-shape tests use value/behavioral-level assertions (exact statuses, type-name descriptors, role sequences, metadata-absence negatives) — they prove the containment invariant, not mere existence.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| backend/app/llm/gateway.py | 158 | `choices[0].message` dereference unguarded — raw AttributeError if an injected choice lacks `.message` (IN-06) | ℹ️ Info | Advisory only — unreachable through the real OpenAI SDK (see Advisory section); the prior CR-01 blocker on lines 154-158 is RESOLVED |
| backend/app/llm/gateway.py | 144 | Raw SDK exception text in log `error` field (WR-01) | ⚠️ Warning | Carried, unchanged, non-blocking |
| backend/app/config.py + gateway.py | 18 / 29 | API key bound at import time (WR-02) | ⚠️ Warning | Carried |
| backend/app/llm/prompts.py | 70-74 | `PromptSpec.id` not cross-checked vs stage (WR-03); body not validated non-empty (WR-04) | ⚠️ Warning | Carried |
| backend/tests/test_gateway.py | 190-191 | Test pins shipped prompt's temperature/max_tokens (WR-05) | ⚠️ Warning | Carried — legitimate prompt tuning breaks CI |
| backend/tests/test_phase2_config.py | 13 | Env-dependent default assertion (WR-06) | ⚠️ Warning | Carried — passes in this env |
| backend/tests/test_keyword_schema.py | 19-65 | Drift-lock compares names/enums/shape, not types (WR-07) | ⚠️ Warning | Carried |
| (prior Info items IN-01..IN-05) | — | Unused re-export; loader traversal gated only by allowlist; stale "numeric cost" docstring; in-progress-marker wording; model-swap live-validation doc gap | ℹ️ Info | Carried, unchanged |

Debt-marker gate: re-scanned both files modified this round (`gateway.py`, `test_gateway.py`) — zero TBD/FIXME/XXX/HACK markers, zero placeholders, zero empty implementations. The prior blocker entry (CR-01) is resolved and removed from the blocker set.

### Human Verification Required

None outstanding. This is an infrastructure/foundation phase (backend LLM gateway core) with no user-facing UI elements. The single manual-only item from 02-VALIDATION.md (real EN + PT-BR generation quality) was satisfied at the initial verification (user-supplied key, 5/5 live run 2026-09-26, user-confirmed PT-BR quality per 02-04 checkpoint) and is not invalidated by the gap round: the guard only adds a branch for non-str/blank content; the valid-content path is code-identical (verified by reading the diff region), and the full offline suite exercising that path end-to-end is green post-change. No ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths exist — every behavior-dependent truth (containment, retry/exhaustion transitions, recovery, audit ordering) has a named passing test executed in this verification.

## Gaps Summary

None. The single gap from the initial verification is closed and verified:

**SC3 malformed-shape containment (CR-01)** — the fix implements exactly the gap contract's two missing items. (1) The guard: `getattr(resp, "choices", None) or []` + `choices[0].message.content if choices else None` + the `not isinstance(content, str) or not content.strip()` branch route empty choices, `content=None` (refusal/content filter), and non-str content into the identical containment flow as invalid JSON — status "invalid" attempt line with metadata-only descriptors (choice count + type NAME), PT-BR correction appended on retry (user-only turn, deliberately no assistant echo), `_summarize("invalid")` + LLMError ("tentativas" / "malformed response" channels) at the shared exhaustion path. (2) The pins: a parametrized offline test covers all three shapes (asserting `pytest.raises(LLMError)` — so no raw IndexError/TypeError can pass unnoticed — plus call count, ascending invalid lines, type-name descriptors, terminal run_summary, and metadata-only discipline), and a recovery test proves attempt-2 valid JSON returns the typed result with statuses ["invalid","ok"] and retry roles ["system","user","user"]. TDD discipline is verifiable in git: the RED commit b225f57 touched only the test file, the GREEN commit 3f1297e only the gateway. All evidence was re-measured in this verification, not taken from SUMMARY claims: 87 passed / 5 deselected (full suite), 15/15 (gateway file), 4/4 verbose on the malformed tests.

With that, all four roadmap Success Criteria hold: SC1 (edit-visibility test + git-versioned prompts), SC2 (live bilingual run with per-attempt audit + config-only model swap), SC3 (validation-class and now shape-class containment, both offline-pinned), SC4 (bilingual categorized extraction). The 16 context decisions are honored, PROFILE-03 is satisfied, and the phase goal — one logged, schema-validated, bilingual-by-parameter, meta-prompt-driven gateway — is achieved. The only residual finding is IN-06 (advisory, unreachable through the real SDK), recorded in the advisory frontmatter.

---

_Verified: 2026-09-26T18:18:26Z_
_Verifier: Claude (gsd-verifier)_
