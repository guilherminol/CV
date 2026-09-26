---
phase: 02-llm-generation-core
reviewed: 2026-09-26T18:08:16Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/app/config.py
  - backend/app/llm/__init__.py
  - backend/app/llm/errors.py
  - backend/app/llm/gateway.py
  - backend/app/llm/logging.py
  - backend/app/llm/prompts.py
  - backend/app/llm/schemas.py
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
  critical: 0
  warning: 7
  info: 6
  total: 13
status: issues_found
---

# Phase 02: Code Review Report (RE-REVIEW)

**Reviewed:** 2026-09-26T18:08:16Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Re-review of Phase 2 (LLM Generation Core) after the gap-closure fix. The delta since the prior review (76ea7a8..HEAD) is confined to `backend/app/llm/gateway.py` (guarded response-shape extraction) and `backend/tests/test_gateway.py` (malformed-shape pins), plus planning docs; all other listed files are byte-identical to what the prior review covered, so carried findings were re-verified against current line numbers rather than re-derived.

**CR-01 is RESOLVED** (see "Resolved since prior review" below — verified against commits 3f1297e / b225f57 / 1678e31 and by execution). No new critical or warning findings were introduced by the fix itself; one new Info (IN-06) notes a residual gap in the guard's absolute claim, unreachable through the real OpenAI SDK.

Evidence run during this review: `uv run pytest -q` → **87 passed, 5 deselected** (the `-m llm` real-API tests correctly deselected by addopts offline-by-default). Cross-module facts re-verified: `app/profile/errors.py` does export `_ptbr_message` (line 41), `render_loc` (line 50), `render_errors_ptbr` (line 69) — the imports in `app/llm/errors.py:15` are valid; `.gitignore` covers `.env` (line 2) and `logs/` (line 14); `pyproject.toml` registers the `llm` marker and `addopts = "-m 'not llm'"` consistent with `test_phase2_config.py`'s assertions.

All 7 warnings and 5 info findings from the prior review remain open (none were addressed by the gap-closure commits, which were scoped to CR-01) and are carried forward below with their original IDs.

## Resolved since prior review

### CR-01 (RESOLVED): Malformed LLM response shape crashes outside the containment contract

**File:** `backend/app/llm/gateway.py:154-189`

Verified fixed. The previously unguarded `content = resp.choices[0].message.content` is now:

```python
choices = getattr(resp, "choices", None) or []
content = choices[0].message.content if choices else None
if not isinstance(content, str) or not content.strip():
```

All three shapes named in the original finding are routed into the SAME containment flow as invalid JSON:

- **empty `choices`** (`getattr ... or []` → `choices == []` → `content = None`), covered by `test_gateway.py::test_malformed_response_shapes_contained_like_invalid_content[empty-choices]`;
- **`content is None`** (refusal/content filter), covered by the `content-none` param;
- **non-str `content`**, covered by the `content-non-str` param (`["bloco"]`).

Each shape produces: an `invalid` attempt line in `runs.jsonl` (D-14, metadata-only descriptors — choice count and type NAME, verified by the `"TEXTO-SECRETO-DO-USUARIO" not in raw_log` / `"bloco" not in raw_log` assertions), a bounded retry with a PT-BR correction (deliberately no assistant turn on this path — nothing valid to echo; roles pinned to `["system", "user", "user"]` by `test_malformed_shape_then_valid_recovers_with_correction`), and on exhaustion `_summarize("invalid")` + loud `LLMError` (D-13/SC3). Whitespace-only string content is also caught by the `.strip()` gate. Recovery-on-retry is pinned (attempt 2 valid → `outcome: "ok"`). Offline suite green including all new pins. One residual sliver of the class survives at Info level (IN-06).

## Warnings

### WR-01: Raw SDK/API exception text written verbatim into the metadata-only runs.jsonl

**File:** `backend/app/llm/gateway.py:144`

**Issue:** Still open — unchanged since the prior review. On SDK/API failure the attempt line's `error` field is `f"{type(exc).__name__}: {exc}"`. For OpenAI-SDK status errors, `str(exc)` embeds the provider's full response body, and for request-construction errors it can embed kwargs. The runs.jsonl metadata-only guarantee (T-02-02: no prompt/response content, no secrets) rests on the unverified assumption that provider error bodies never echo request content or credentials. No length bound on the field either. (The new malformed-shape path at lines 164-175 correctly logs descriptors only — the leak surface is specifically the `except Exception` branch.)

**Fix:** Keep the full detail in `LLMError.raw` (terminal only) but log a bounded, low-context form:
```python
"error": f"{type(exc).__name__}: {str(exc)[:200]}",
```

### WR-02: OPENROUTER_API_KEY is bound at import time, not call time — docstring and behavior disagree

**File:** `backend/app/config.py:18` (with `backend/app/llm/gateway.py:29`)

**Issue:** Still open. `config.py:18` captures `os.environ.get("OPENROUTER_API_KEY", "")` at import time and `gateway.py:29` imports the value by name. The gateway check IS at call time (line 78) but the value is frozen at import: a long-running uvicorn process started before `.env` is populated keeps raising "key ausente" after the user adds the key, until restart. The same import-time freeze propagates to `test_llm_harness.py:80`'s `skipif(not OPENROUTER_API_KEY, ...)` (evaluated at collection). Tests work around this only via `monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", ...)`.

**Fix:** Read through the config module at call time:
```python
from app import config
...
    if not config.OPENROUTER_API_KEY:
```
Same treatment for `LLM_MODEL` if mid-process env changes are meant to be honored.

### WR-03: PromptSpec.id is validated but never cross-checked against the requested stage

**File:** `backend/app/llm/prompts.py:68-74`

**Issue:** Still open. `PromptSpec.id` is required by the strict schema but never compared with the `stage` argument. A prompt file copied from another stage (or manually renamed) keeps its stale `id` and passes validation silently, while `runs.jsonl` records the *caller's* stage (`gateway.py:99`) — the audit trail can misattribute which meta-prompt produced a run, the exact silent divergence D-06's fail-loud discipline exists to prevent.

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

**Issue:** Still open. The loader validates frontmatter strictly but returns `body=post.content` unchecked. A prompt file with an empty or whitespace-only body (the actual system prompt per D-07) loads successfully and the gateway silently sends an empty system message — the LLM generates against no instructions, wasting spend and producing likely-invalid output. `test_prompt_loader.py:50` asserts non-empty body only for the one shipped file, not as a loader invariant.

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

**File:** `backend/tests/test_gateway.py:190-191`

**Issue:** Still open. `test_sdk_call_shape_strict_schema_and_extra_body` asserts `kwargs["temperature"] == 0.2` and `kwargs["max_tokens"] == 2000` sourced from the *real* `prompts/keyword-extraction.md` (comment: "from the real prompt file"). Editing prompt parameters is an explicitly supported, no-code-change workflow (D-08/SC1 is itself tested by `test_prompt_file_edit_is_visible_on_next_call`, lines 396-421, using exactly the technique this test needs), yet any legitimate tuning of the shipped file breaks CI.

**Fix:** Write a temp prompt file with known values and retarget via `monkeypatch.setattr("app.llm.prompts.PROMPTS_DIR", ...)`, then assert the kwargs equal the values just written.

### WR-06: Config test asserts env-overridable default — fails in legitimately configured environments

**File:** `backend/tests/test_phase2_config.py:13`

**Issue:** Still open. `assert cfg.LLM_MODEL == "anthropic/claude-sonnet-4.5"` compares the *live* value of `config.LLM_MODEL`, which `config.py:34` documents as env-overridable via `LLM_MODEL` (loaded from repo-root `.env`). A developer who pins a test model in `.env` — the documented workflow — gets a failing config test unrelated to their change. The assertion tests the environment, not the code.

**Fix:** Isolate the env for this test (`monkeypatch.delenv("LLM_MODEL", raising=False)` + config reload), or assert only `isinstance(cfg.LLM_MODEL, str) and cfg.LLM_MODEL` and pin the default in an env-independent way.

### WR-07: Drift-lock test does not compare property types — T-02-08 guarantee weaker than documented

**File:** `backend/tests/test_keyword_schema.py:19-46, 61-65` (with claim at `backend/app/llm/schemas.py:45-46`)

**Issue:** Still open. `schemas.py:45-46` states the drift-lock test "fails CI if this dict and the Pydantic model diverge". What the tests actually pin: top-level and nested property *name sets* (lines 19-27), category *enum values* (lines 30-46), and strict-shape invariants (lines 61-65). They do NOT compare property *types* (`canonical: str` vs `"type": "string"`, `aliases` item types) or required/optionality semantics. A Pydantic field type change or a wire type change stays green in CI and only surfaces as runtime validation failures burning LLM retries — the exact silent-divergence threat T-02-08 names.

**Fix:** Extend the drift-lock to compare per-property types — build an expected map from `KeywordExtraction.model_json_schema()["$defs"]["Keyword"]["properties"]` and assert each wire property's `type`/`enum` against it, or round-trip `KEYWORD_STRICT_SCHEMA` through a pydantic-generated schema and assert equivalence on names + types.

## Info

### IN-01: Unused re-export of `render_errors_ptbr` exposes a profile-header renderer in the LLM namespace

**File:** `backend/app/llm/errors.py:15,20`

**Issue:** Still open. `render_errors_ptbr` is imported (with `noqa: F401`) and listed in `__all__`, but no module imports it from `app.llm.errors` (its only consumer is `app/profile/loader.py`, importing from `app.profile.errors`). Anyone importing it from the LLM module gets a renderer emitting the "Erro no perfil:" header — wrong prefix for LLM-layer errors.

**Fix:** Remove `render_errors_ptbr` from the import and from `__all__` (keep `_ptbr_message`/`render_loc`, which `render_prompt_errors_ptbr` uses).

### IN-02: Public `load_prompt` performs no stage sanitization; traversal only gated by the gateway allowlist

**File:** `backend/app/llm/prompts.py:55`

**Issue:** Still open. `path = prompts_dir / f"{stage}.md"` accepts any string, so `load_prompt("../../secrets")` reads outside `prompts/`. Today this is unreachable through `run_stage` (`gateway.py:69` allowlists `stage` against `_STAGE_SCHEMAS` first), but the loader is a public module API that future call sites may use directly.

**Fix:** Reject stages containing path separators (`"/" in stage or "\\" in stage or stage in (".", "..")`), or document the caller-must-allowlist invariant in the docstring.

### IN-03: Harness docstring promises "numeric cost" but asserts only field presence (cost is locked to null)

**File:** `backend/tests/test_llm_harness.py:120` (vs assertion at line 176)

**Issue:** Still open. The docstring says ">=1 runs.jsonl line per attempt with numeric cost (D-13)", but the assertion at line 176 only checks `"cost" in line`, and D-13 locks `cost: null` until Phase 5/6. The stale docstring misstates the contract the test enforces.

**Fix:** Reword the docstring to "with the cost field present (null until Phase 5/6)".

### IN-04: Prompt promises an "in progress" marker the output schema cannot express

**File:** `prompts/keyword-extraction.md:20`

**Issue:** Still open. Rule 4 says certifications include "as em andamento, marcadas como tal no texto", but the `Keyword` schema (canonical/aliases/pt/en/category) has no field to carry an in-progress marker. The ambiguity invites the model to either invent an extra key (→ `extra_forbidden` → wasted retry) or silently ignore the instruction.

**Fix:** Reword to remove the marker implication, e.g. "certificações (incluindo as em andamento — extraia normalmente)", or defer marker support to a schema change.

### IN-05: Model swap is only live-validated by the opt-in harness; wire schema acceptance is proven for the pinned slug only

**File:** `backend/app/llm/schemas.py:57-58` (with `backend/app/config.py:34`)

**Issue:** Still open (documentation gap). The wire schema expresses nullable fields as `"type": ["string", "null"]`. Live acceptance was proven for `anthropic/claude-sonnet-4.5`, but the offline suite never sends the schema, and D-01/D-02 allow swapping `LLM_MODEL` via env with no code change. A swapped model/provider that rejects the type-array form fails loudly (immediate 400 `LLMError`, no retry per D-03) — correct, but spend-wasting and discovered only at first real use.

**Fix:** No code change required; document that swapping `LLM_MODEL` must be followed by a `uv run pytest -m llm` harness pass (the slug probe exists for exactly this).

### IN-06 (new): Guarded extraction still assumes `choices[0].message` exists — an AttributeError can escape the containment the comment claims is absolute

**File:** `backend/app/llm/gateway.py:158`

**Issue:** The CR-01 fix guards `resp.choices` (missing/None/empty) and `content` (None/non-str/whitespace), but line 158 dereferences `choices[0].message.content` unguarded. A non-empty `choices` whose first element lacks a `.message` attribute (or whose `message` is `None`) raises a raw `AttributeError` out of `run_stage` — the exact uncontained-crash class CR-01 closed, contra the comment at lines 154-156 ("must NEVER escape"). This is unreachable through the real OpenAI SDK (the SDK parses the payload into typed models *inside* `create()`, so a missing `message` surfaces there and is contained by the `except Exception` at line 137) — but `client` is a documented injectable surface (`gateway.py:62-63`), and a looser "SDK-compatible" client can trigger it.

**Fix:** Complete the guard with the same getattr discipline used one line up:
```python
choice = choices[0] if choices else None
message = getattr(choice, "message", None) if choice is not None else None
content = getattr(message, "content", None)
```
Optionally pin it with a `choices=[object()]`-style param in `test_malformed_response_shapes_contained_like_invalid_content`.

---

_Reviewed: 2026-09-26T18:08:16Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
