---
phase: 02-llm-generation-core
reviewed: 2026-09-26T12:41:25Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - .gitignore
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
findings:
  critical: 1
  warning: 7
  info: 5
  total: 13
status: findings
---

# Phase 02: Code Review Report

**Reviewed:** 2026-09-26T12:41:25Z
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

Reviewed the Phase 2 LLM generation core: OpenRouter gateway, prompt loader, run-log writer, keyword schema, config, pytest suite, and the shipped meta-prompt, at standard depth with cross-module tracing into `app/profile/errors.py` (imported by `app/llm/errors.py`) and `app/profile/loader.py` (claimed mirror).

Overall the architecture is sound and the security posture is mostly strong: `.env` and `logs/` are correctly gitignored (verified via `git check-ignore`), `.env.example` carries no real secret, no hardcoded credentials exist, LLM output is strictly re-validated (`extra="forbid"` + `Literal` categories + wire-never-trusted), and the happy-path attempt lines carry metadata only (confirmed by test assertions and code reading).

The one critical defect: the gateway's response-extraction step (`resp.choices[0].message.content`) is not guarded against malformed-but-200 response shapes (empty `choices`, `content=None` on refusal/content-filter, non-str content). `IndexError`/`TypeError` then escape `run_stage` uncaught — no attempt line, no run summary, no `LLMError` — silently breaking the phase's core containment contract (D-13/SC3) that the run-log tests pin.

Warnings cluster around: untruncated exception text flowing into the metadata-only log, import-time (not call-time) API-key binding contradicting the module docstring, two unenforced prompt-file validations (`id` cross-check, non-empty body), and two environment-sensitive tests that fail in legitimately configured developer setups. The drift-lock test compares names and enums but not types, so its "fails CI if the dict and model diverge" guarantee (T-02-08) is weaker than documented.

## Critical Issues

### CR-01: Malformed LLM response shape crashes outside the containment contract — no log line, no summary, no LLMError

**File:** `backend/app/llm/gateway.py:154-158`

**Issue:** After `client.chat.completions.create(...)` returns a 200-style response, line 154 does `content = resp.choices[0].message.content` and line 156 does `json.loads(content)`. The `try` on lines 155-158 only catches `(json.JSONDecodeError, ValidationError)`. Three realistic response shapes therefore raise *uncaught* exceptions that propagate out of `run_stage`:

1. `resp.choices == []` (provider error surfaced with HTTP 200, OpenRouter "no provider could serve" shapes) → `IndexError` at line 154.
2. `content is None` (model refusal, content filter, or provider returning `message.refusal` instead of content) → `json.loads(None)` → `TypeError` at line 156.
3. Non-string `content` (some providers return content block lists) → `TypeError` at line 156.

Consequences, all violating the module's own contract: (a) the attempt is never logged to `runs.jsonl` (no attempt line, D-14), (b) no `run_summary` line is written (D-13 promises it "on BOTH success and LLMError paths" — this path is neither), (c) the caller receives a raw `IndexError`/`TypeError` instead of `LLMError`, so any UI/route layer catching `LLMError` for the PT-BR message path gets an unhandled 500 instead (SC3: invalid content must never escape uncontained).

**Fix:**
```python
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        choices = getattr(resp, "choices", None) or []
        content = choices[0].message.content if choices else None
        if not isinstance(content, str) or not content.strip():
            # Malformed shape (empty choices / refusal / non-str content):
            # route through the SAME containment path as invalid JSON.
            raw = f"malformed response: choices={len(choices)}, content={type(content).__name__}"
            accumulated_raw.append(f"[tentativa {attempt}] {raw}")
            _log(
                {
                    **base_record,
                    **_usage_fields(resp),
                    "attempt": attempt,
                    "status": "invalid",
                    "latency_ms": latency_ms,
                    "error": f"conteúdo ausente ou não-textual ({type(content).__name__}) — "
                    "nunca retornado downstream, SC3",
                }
            )
            if attempt < LLM_MAX_ATTEMPTS:
                messages.append(
                    {"role": "user", "content": "Sua resposta anterior chegou vazia. "
                    "Reenvie o objeto JSON completo."}
                )
            continue
        try:
            parsed = json.loads(content)
            result = output_model.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            ...
```
(The exhaustion path after the loop already emits `_summarize("invalid")` + `LLMError`, so routing these shapes into the same flow restores both D-13 and SC3.)

## Warnings

### WR-01: Raw SDK/API exception text written verbatim into the metadata-only runs.jsonl

**File:** `backend/app/llm/gateway.py:144`

**Issue:** On SDK/API failure the attempt line's `error` field is `f"{type(exc).__name__}: {exc}"`. For OpenAI-SDK status errors, `str(exc)` embeds the provider's full response body, and for request-construction errors it can embed kwargs. The runs.jsonl metadata-only guarantee (T-02-02: no prompt/response content, no secrets) currently rests on the unverified assumption that provider error bodies never echo request content or credentials. There is also no length bound on the field.

**Fix:** Keep the full detail in `LLMError.raw` (terminal only) but log a bounded, low-context form:
```python
"error": f"{type(exc).__name__}: {str(exc)[:200]}",
```

### WR-02: OPENROUTER_API_KEY is bound at import time, not call time — docstring and behavior disagree

**File:** `backend/app/config.py:18` (with `backend/app/llm/gateway.py:29`)

**Issue:** `config.py:18` captures `os.environ.get("OPENROUTER_API_KEY", "")` at import time, and `gateway.py:29` imports that value by name. The gateway docstring (lines 16-17) promises "Missing/empty OPENROUTER_API_KEY at CALL time raises LLMError", but the *check* is at call time while the *value* is frozen at import. A long-running uvicorn process started before `.env` is populated will keep raising the "key ausente" error after the user adds the key, until the process is restarted. (Tests only work around this by monkeypatching `app.llm.gateway.OPENROUTER_API_KEY`.)

**Fix:** Read through the config module at call time:
```python
from app import config
...
    if not config.OPENROUTER_API_KEY:
```
Same treatment for `LLM_MODEL` if mid-process env changes are meant to be honored.

### WR-03: PromptSpec.id is validated but never cross-checked against the requested stage

**File:** `backend/app/llm/prompts.py:70-74` (field at line 34)

**Issue:** `PromptSpec.id` is required by the strict schema but never used by the gateway and never compared with the `stage` argument. A prompt file copied from another stage (or a manually renamed file) keeps its stale `id` and passes validation silently. Meanwhile `runs.jsonl` records the *caller's* stage (gateway.py:99), so the audit trail can misattribute which meta-prompt actually produced a run — precisely the silent divergence D-06's fail-loud discipline exists to prevent.

**Fix:**
```python
    if spec.id != stage:
        raise PromptError(
            f"Erro no prompt: {path} — id do frontmatter ('{spec.id}') não "
            f"corresponde ao estágio solicitado ('{stage}')",
            f"frontmatter id mismatch: {spec.id!r} != {stage!r}",
        )
```

### WR-04: Prompt body (the system payload) is never validated non-empty

**File:** `backend/app/llm/prompts.py:74`

**Issue:** The loader validates frontmatter strictly but returns `body=post.content` unchecked. A prompt file with an empty or whitespace-only body (the actual system prompt per D-07) loads successfully and the gateway silently sends an empty system message — the LLM then generates against no instructions, wasting spend and producing likely-invalid output. `test_prompt_loader.py:50` asserts non-empty body only for the one shipped file, not as a loader invariant.

**Fix:**
```python
    if not post.content.strip():
        raise PromptError(
            f"Erro no prompt: {path} — corpo do prompt está vazio (o corpo é o "
            "system prompt e não pode ser vazio)",
            "empty prompt body",
        )
```

### WR-05: Gateway test pins the shipped prompt file's parameter values — prompt tuning breaks CI

**File:** `backend/tests/test_gateway.py:174-175`

**Issue:** `test_sdk_call_shape_strict_schema_and_extra_body` asserts `kwargs["temperature"] == 0.2` and `kwargs["max_tokens"] == 2000` sourced from the *real* `prompts/keyword-extraction.md` (comment: "from the real prompt file"). Editing prompt parameters is an explicitly supported, no-code-change workflow (D-08/SC1 is tested by `test_prompt_file_edit_is_visible_on_next_call`), yet any legitimate tuning of the shipped file breaks this test. The test should verify pass-through, not the file's current values.

**Fix:** Write a temp prompt file with known values and retarget via `monkeypatch.setattr("app.llm.prompts.PROMPTS_DIR", ...)` (same technique as `test_prompt_file_edit_is_visible_on_next_call`, lines 302-322), then assert the kwargs equal the values just written.

### WR-06: Config test asserts env-overridable default — fails in legitimately configured environments

**File:** `backend/tests/test_phase2_config.py:13`

**Issue:** `assert cfg.LLM_MODEL == "anthropic/claude-sonnet-4.5"` compares the *live* value of `config.LLM_MODEL`, which `config.py:34` documents as env-overridable via `LLM_MODEL` (loaded from repo-root `.env` per the 02-04 summary). A developer who pins a test model in `.env` — the documented workflow — gets a failing config test unrelated to their change. The assertion tests the environment, not the code.

**Fix:** Isolate the env for this test, e.g. `monkeypatch.delenv("LLM_MODEL", raising=False)` with config reload, or assert only `isinstance(cfg.LLM_MODEL, str) and cfg.LLM_MODEL` and pin the default in an env-independent way.

### WR-07: Drift-lock test does not compare property types — T-02-08 guarantee weaker than documented

**File:** `backend/tests/test_keyword_schema.py:24-27` and `61-65` (with claim at `backend/app/llm/schemas.py:45-46`)

**Issue:** `schemas.py:45-46` states the drift-lock test "fails CI if this dict and the Pydantic model diverge". What the tests actually pin: top-level and nested property *name sets* (lines 19-27), category *enum values* (lines 30-46), and the strict shape invariants (lines 61-65). They do NOT compare property *types* (`canonical: str` vs `"type": "string"`, `aliases` item types) or required/optionality semantics. If someone changes a Pydantic field type or a wire type, CI stays green and the divergence only surfaces as runtime validation failures burning LLM retries — the exact silent-divergence threat T-02-08 names.

**Fix:** Extend the drift-lock to compare per-property types — build an expected map from `KeywordExtraction.model_json_schema()["$defs"]["Keyword"]["properties"]` and assert each wire property's `type`/`enum` against it, or round-trip `KEYWORD_STRICT_SCHEMA` through a pydantic-generated schema and assert equivalence on names + types.

## Info

### IN-01: Unused re-export of `render_errors_ptbr` exposes a profile-header renderer in the LLM namespace

**File:** `backend/app/llm/errors.py:15,20`

**Issue:** `render_errors_ptbr` is imported (with `noqa: F401`) and listed in `__all__`, but no module imports it from `app.llm.errors` (verified by grep — its only consumer is `app/profile/loader.py`, importing from `app.profile.errors`). Anyone importing it from the LLM module gets a renderer emitting the "Erro no perfil:" header — wrong prefix for LLM-layer errors.

**Fix:** Remove `render_errors_ptbr` from the import and from `__all__` (keep `_ptbr_message`/`render_loc`, which `render_prompt_errors_ptbr` uses).

### IN-02: Public `load_prompt` performs no stage sanitization; traversal only gated by the gateway allowlist

**File:** `backend/app/llm/prompts.py:55`

**Issue:** `path = prompts_dir / f"{stage}.md"` accepts any string, so `load_prompt("../../secrets")` reads outside `prompts/`. Today this is unreachable through `run_stage` (gateway.py:69 allowlists `stage` against `_STAGE_SCHEMAS` first), but the loader is a public module API that future call sites may use directly.

**Fix:** Reject stages containing path separators (`"/" in stage or "\\" in stage or stage in (".", "..")`), or document the caller-must-allowlist invariant in the docstring.

### IN-03: Harness docstring promises "numeric cost" but asserts only field presence (cost is locked to null)

**File:** `backend/tests/test_llm_harness.py:120` (vs assertion at line 176)

**Issue:** The docstring says ">=1 runs.jsonl line per attempt with numeric cost (D-13)", but the assertion at line 176 only checks `"cost" in line`, and D-13 locks `cost: null` until Phase 5/6. The stale docstring misstates the contract the test enforces.

**Fix:** Reword the docstring to "with the cost field present (null until Phase 5/6)".

### IN-04: Prompt promises an "in progress" marker the output schema cannot express

**File:** `prompts/keyword-extraction.md:20`

**Issue:** Rule 4 says certifications include "as em andamento, marcadas como tal no texto", but the `Keyword` schema (canonical/aliases/pt/en/category) has no field to carry an in-progress marker. The ambiguity invites the model to either invent an extra key (→ `extra_forbidden` → wasted retry) or silently ignore the instruction.

**Fix:** Reword to remove the marker implication, e.g. "certificações (incluindo as em andamento — extraia normalmente)", or defer marker support to a schema change.

### IN-05: Model swap is only live-validated by the opt-in harness; wire schema acceptance is proven for the pinned slug only

**File:** `backend/app/llm/schemas.py:57-58` (with `backend/app/config.py:34`)

**Issue:** The wire schema expresses nullable fields as `"type": ["string", "null"]` (lines 57-58). Live acceptance was proven for `anthropic/claude-sonnet-4.5` (02-04-SUMMARY: 5/5 `-m llm` tests passed), but the offline suite never sends the schema, and D-01/D-02 allow swapping `LLM_MODEL` via env with no code change. A swapped model/provider that rejects the type-array form would fail loudly (immediate 400 `LLMError`, no retry per D-03) — correct, but spend-wasting and discovered only at first real use.

**Fix:** No code change required; document that swapping `LLM_MODEL` must be followed by a `uv run pytest -m llm` harness pass (the slug probe exists for exactly this).

---

_Reviewed: 2026-09-26T12:41:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
