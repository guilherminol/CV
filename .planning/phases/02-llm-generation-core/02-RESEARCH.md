# Phase 2: LLM Generation Core - Research

**Researched:** 2026-09-25
**Domain:** OpenRouter LLM gateway (Python/FastAPI backend) — structured outputs, meta-prompt files, validation-retry loop, JSONL call logging, pytest marker-based real-API harness
**Confidence:** HIGH (codebase anchors read; OpenRouter behavior verified against official docs; environment probed)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Default model family: Claude Sonnet (`claude-*` on OpenRouter). Slug lives in config; swapping is a one-line change.
- **D-02:** Single global model, no per-stage override.
- **D-03:** Fail loud — no automatic model fallback. Clear error + full detail in log.
- **D-04:** Cost/size guardrails in config: `max_tokens` per stage + retry cap (e.g., 2 validation-error retries).
- **D-05:** One meta-prompt file per stage (e.g., `prompts/keyword-extraction.md`).
- **D-06:** Format: Markdown body + YAML frontmatter (id + stage params); strict Pydantic `extra="forbid"` validation.
- **D-07:** Prompt file = system prompt; runtime inputs in the user message. No `{{template}}` variables.
- **D-08:** `prompts/` at repo root, sibling of `content/`. Files read fresh on every call (no cache).
- **D-09:** LLM maps PT↔EN in the extraction call itself — structured output carries each keyword in both languages.
- **D-10:** Fixed categories: competências, ferramentas, títulos de vaga, certificações.
- **D-11:** Canonical form + aliases (canonical "Kubernetes", alias "k8s").
- **D-12:** One input-agnostic prompt for both JD and career objective.
- **D-13:** Call log is `logs/runs.jsonl` (gitignored), one JSON line per LLM call + terminal summary. Fields: stage, model, tokens, cost, latency, language.
- **D-14:** Granularity: per LLM call including retries (line carries attempt number).
- **D-15:** Fixture harness = `pytest -m llm` — real OpenRouter calls, on demand (`uv run pytest -m llm`). Fixtures cover EN and PT-BR.
- **D-16:** Regular test suite is 100% offline — real API spend only under `-m llm`.

### Claude's Discretion
- Exact `claude-*` slug pinned as default (fixture harness must validate strict `json_schema` compliance + PT-BR quality before locking; slug lives in config only).
- OpenRouter client mechanics: OpenAI-compatible SDK vs raw `httpx`; structured-outputs enforcement (`response_format: json_schema` vs prompt-side); retry/backoff mechanics; transient vs fatal classification.
- JSONL line field names, terminal summary format, log rotation policy.
- Prompt frontmatter exact key set + Pydantic model; `app/llm/` package layout; profile-facts serialization into user message.
- Mocking library/technique for offline tests; fixture input texts (realistic sample JD + career objective, both languages).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (PT↔EN glossary is Phase 6, recorded in D-09, not deferred here.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROFILE-03 | User can edit meta-prompts as versioned files in git to tune generation behavior (e.g., "more metrics", "more concise PT-BR") | Meta-prompt loader pattern (frontmatter + Pydantic strict, fresh read per call — D-05..D-08) mirroring Phase 1's profile loader; OpenRouter gateway calling prompt-as-system-message (D-07); `pytest -m llm` harness proving the edit→run loop (SC1/SC2) |
</phase_requirements>

## Summary

Phase 2 adds a single LLM gateway to the existing FastAPI backend: every call goes through one module that loads a meta-prompt file (`prompts/<stage>.md`, frontmatter + Markdown body), composes runtime inputs into the user message, calls OpenRouter via the OpenAI-compatible Python SDK with `response_format: json_schema`, re-validates the parsed content against a strict Pydantic model, retries up to 2 times with the validation error appended, and writes one JSONL line per attempt (stage, model, tokens, cost, latency, language, attempt) to `logs/runs.jsonl`. The keyword engine is the first consumer: one input-agnostic prompt extracting keywords with PT↔EN pairs, fixed categories, canonical+aliases, and covered/adjacent/absent classification hooks for Phase 3.

The codebase anchors are strong: `backend/app/config.py` (extend with model slug, `PROMPTS_DIR`, log path, retry cap), `app/profile/models.py` (`Language`, `LocalizedText`, `_Strict` — reuse verbatim for keyword output schema and frontmatter model), `app/profile/loader.py`/`errors.py` (the fail-fast template to mirror for prompt files), and the existing pytest suite (home for the `-m llm` marker). Environment probed: uv 0.12.5 + Python 3.12.10 present; `openai` package NOT yet installed; `OPENROUTER_API_KEY` currently unset/empty in `.env`; `logs/` and `prompts/` directories do not exist yet.

Two corrections/clarifications vs. STACK.md's pinned pattern, verified against current official OpenRouter docs: (1) `require_parameters` is a **provider-preference body field** (`extra_body={"provider": {"require_parameters": True}}` via the OpenAI SDK), not a header; (2) `usage.cost` is returned automatically in every non-streaming response (denominated in credits) — no `usage: {include: true}` needed (that param is deprecated/no-op).

**Primary recommendation:** Use the `openai` PyPI SDK with `base_url="https://openrouter.ai/api/v1"`, send a hand-maintained strict JSON Schema dict (kept test-locked to the Pydantic model) via `response_format={"type": "json_schema", ...}`, re-validate with Pydantic regardless (per-provider enforcement varies), and structure the phase as: config+schema → prompt loader → gateway+JSONL log → keyword engine → offline tests → `-m llm` harness.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Meta-prompt file loading/validation | API / Backend (Python) | — | Files are user-edited git content; backend reads fresh per call (D-08), fail-fast like the profile loader |
| LLM call orchestration (gateway) | API / Backend (Python) | — | Single choke point for logging, validation, retry, language param; no LLM logic in browser |
| Structured-output schema definition | API / Backend (Pydantic) | — | Backend owns the contract Phase 3 consumes; frontend never sees unvalidated LLM output |
| Call logging (JSONL) | API / Backend (filesystem) | — | `logs/runs.jsonl` local file, gitignored; seed of Phase 5/6 run store |
| Model/SLUG configuration | API / Backend (config.py + .env) | — | Model swap = config change (SC2); key stays in gitignored `.env` |
| Real-API validation harness | Test tier (pytest `-m llm`) | — | On-demand only; regular suite 100% offline (D-15/D-16) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai (PyPI) | latest (>=1.x line; latest release 2026-09-24) | OpenRouter client via `OpenAI(base_url="https://openrouter.ai/api/v1")` — chat completions, `response_format` passthrough, `extra_body` provider prefs | Official OpenAI SDK; the OpenAI-compatible endpoint is a first-class documented OpenRouter feature `[CITED: openrouter.ai/docs/quickstart via STACK.md]`; vastly more examples than the vendor SDK; vendor-portable |
| pydantic (installed 2.13.5) | 2.13.5 | Keyword output schema, prompt frontmatter model, response re-validation | Already a dependency; `_Strict` base reusable `[VERIFIED: backend/app/profile/models.py:29-32]`; OpenRouter docs warn schema enforcement varies by provider — always re-validate `[CITED: openrouter.ai/docs/guides/features/structured-outputs]` |
| python-frontmatter (installed 1.3.0) | 1.3.0 | Parse `prompts/*.md` (YAML frontmatter + Markdown body) | Already used by the profile loader — same pattern, same pitfalls solved (explicit UTF-8) `[VERIFIED: backend/app/profile/loader.py:38]` |
| pytest (installed 9.1.1) | 9.1.1 | Offline suite + `-m llm` real-API harness | Existing suite; markers registered in `pyproject.toml [tool.pytest.ini_options]` `[VERIFIED: backend/pyproject.toml:14-16]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx (dev dep, installed 0.28.1) | 0.28.1 | Mocking transport for offline gateway tests (or plain monkeypatch) | Offline tests that exercise the gateway without network |
| respx or pytest-httpx | — (optional) | Interceptor for httpx-based calls | Only if the gateway is raw-httpx; if using the `openai` SDK, monkeypatch the client instead — an extra dependency is not required `[ASSUMED]` |

**Installation:**
```bash
uv add --project backend openai
```
No other new dependencies required. Do NOT add LangChain/LlamaIndex (STACK.md What-NOT-to-use: framework abstraction hides the prompts being iterated — pure overhead at 2–4 call sites).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `openai` SDK | raw `httpx` calls to `https://openrouter.ai/api/v1/chat/completions` | httpx is already a dev dep and gives full control of the wire format; but the SDK gives retries/timeouts plumbing, typed responses, and is the documented path. SDK wins unless the team wants zero new runtime deps `[ASSUMED — discretion area]` |
| `openai` SDK | `openrouter` PyPI SDK | Official vendor SDK exists; OpenAI-compatible route has more examples and stays vendor-portable (STACK.md decision) |
| SDK structured outputs | prompt-side "respond in JSON" + validation | Prompt-side is provider-agnostic but unreliable; use `json_schema` AND Pydantic re-validation (belt and suspenders — per-provider enforcement varies) `[CITED: openrouter.ai/docs/guides/features/structured-outputs]` |

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| openai | PyPI | first published ~2023; latest release 2026-09-24 (signal: "too-new" is an artifact of the latest-release timestamp, one day before this research) | unknown (PyPI signal unavailable to checker) | github.com/openai/openai-python | SUS (likely false positive) | Approved with note — no checkpoint needed: official OpenAI repo, referenced by OpenRouter's own docs as the recommended Python client `[CITED: openrouter.ai/docs]` |

**Packages removed due to SLOP verdict:** none
**Packages flagged as suspicious [SUS]:** `openai` — the SUS verdict's reasons ("too-new", "unknown-downloads") key on the latest-release publish date (2026-09-24) and missing PyPI download signals, not on package identity. The source repo is the official `openai/openai-python` and OpenRouter's quickstart documents this SDK for Python. If the planner prefers protocol strictness, add a `checkpoint:human-verify` before `uv add openai`; research judges it unnecessary.

## Architecture Patterns

### System Architecture Diagram

```
 [prompts/keyword-extraction.md]     [content/profile.md]     [.env: OPENROUTER_API_KEY]
  (system prompt, user-edited)        (master-profile facts)    (secret, gitignored)
          │ fresh read per call              │ fresh load              │
          ▼                                  ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         app/llm/ gateway (backend)                          │
│  1. load_prompt(stage) ── fail-fast Pydantic frontmatter (extra=forbid)     │
│  2. compose user message (input text JD/objective + profile facts + lang)   │
│  3. call OpenRouter (openai SDK, response_format=json_schema, provider      │
│     prefs require_parameters) ── model slug from config (D-01/D-02)         │
│  4. parse JSON ── Pydantic strict validation                                │
│     ├─ valid ──────────────► return typed result                            │
│     └─ invalid ──► append validation error to messages ──► retry (≤2, D-04) │
│          └─ exhausted ──► loud LLMError (PT-BR msg + raw detail; D-03)      │
│  5. EVERY attempt ──► one JSONL line {stage, model, tokens, cost,           │
│     latency, language, attempt, status} ──► logs/runs.jsonl (D-13/D-14)     │
└─────────────────────────────────────────────────────────────────────────────┘
          │ typed KeywordExtraction                     │
          ▼                                             ▼
  Phase 3 consumers (coverage hooks:         logs/runs.jsonl ──► Phase 5/6 run store
  covered/adjacent/absent in schema shape)
```

Offline tests mock step 3 (SDK client / httpx transport); `pytest -m llm` runs steps 1–5 against the real API with fixture JD + career objective in both languages.

### Recommended Project Structure
```
backend/app/llm/
├── __init__.py
├── config.py        # (or extend app/config.py): model slug, PROMPTS_DIR, LOGS path, retry cap, default max_tokens
├── prompts.py       # meta-prompt loader: frontmatter model + fail-fast load (mirrors app/profile/loader.py)
├── schemas.py       # keyword output schema (canonical+aliases, fixed categories, coverage hooks) + strict JSON Schema dict
├── gateway.py       # single entry: run_stage(stage, input_text, language, profile) → typed result; retry loop; JSONL log
├── logging.py       # JSONL writer + terminal summary (D-13); append, one line per attempt
└── errors.py        # LLMError(message_ptbr, raw) — same shape as ProfileError
prompts/
└── keyword-extraction.md   # user-edited meta-prompt (frontmatter: id, temperature, max_tokens; body: system prompt)
logs/                       # created at first write; gitignored (runs.jsonl)
backend/tests/
├── test_prompt_loader.py   # offline: frontmatter typos fail loudly, fresh read
├── test_gateway.py         # offline: mock SDK — happy path, malformed→retry→recovered, malformed→retry-exhausted→loud error, log lines written
├── test_keyword_schema.py  # offline: strict schema rejects unknown keys/categories
└── test_llm_harness.py     # marked @pytest.mark.llm — real API, EN + PT-BR fixtures
```
(Exact layout is discretion; the key constraint is ONE gateway module every call flows through.)

### Pattern 1: OpenRouter call via OpenAI SDK with structured outputs
**What:** Single gateway function calling `chat.completions.create` with strict `json_schema`.
**When to use:** every LLM call in the app.
```python
# Anchored to STACK.md pattern + corrected per current OpenRouter docs (verified 2026-09-25)
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,  # from app/config.py (.env)
)

resp = client.chat.completions.create(
    model=LLM_MODEL,               # slug from config, not code (D-01/D-02)
    messages=[
        {"role": "system", "content": prompt_file.body},   # D-07
        {"role": "user", "content": composed_user_message}, # input text + profile facts + language
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "keyword_extraction",
            "strict": True,
            "schema": KEYWORD_STRICT_SCHEMA,  # hand-maintained strict dict (see Pattern 2)
        },
    },
    extra_body={"provider": {"require_parameters": True}},  # verified: provider-preference FIELD, not a header
    temperature=prompt_file.temperature,
    max_tokens=prompt_file.max_tokens,          # D-04 guardrail
)
content = resp.choices[0].message.content
usage = resp.usage  # prompt_tokens / completion_tokens / total_tokens / .cost (credits) — automatic, no include param
```
`[CITED: openrouter.ai/docs/guides/features/structured-outputs]` (strict flag, require_parameters as provider preference, per-provider enforcement caveat) · `[CITED: openrouter.ai/docs/use-cases/usage-accounting]` (usage/cost fields, automatic inclusion, deprecated include param). NOTE: STACK.md line 120 shows `extra_headers={"require_parameters": True}` — superseded; current docs place it in provider preferences (`extra_body.provider`).

### Pattern 2: Strict JSON Schema vs Pydantic — keep two locked representations
**What:** The schema sent to OpenRouter (`strict: true`) requires OpenAI-style strictness: `additionalProperties: false` at every object level and ALL properties listed in `required` (optionals expressed as `type: ["x", "null"]`). Pydantic v2's `model_json_schema()` does NOT emit that shape directly. `[ASSUMED — based on training knowledge of strict-mode schemas; verify with a one-line test comparing what the API accepts]`
**Recommendation:** hand-maintain the strict schema dict in `schemas.py` and add an offline test asserting every property of the dict appears in the Pydantic model's `model_json_schema()` (and vice versa) so the two cannot drift. Validate responses ONLY with the Pydantic model (`KeywordExtraction.model_validate(json.loads(content))`) — never trust wire conformance (`[CITED: openrouter.ai/docs/guides/features/structured-outputs]`: enforcement varies by provider; some treat the schema "as a strong hint").

### Pattern 3: Validation-error retry loop (D-03/D-04/D-14)
```python
messages = [system_msg, user_msg]
for attempt in range(1, MAX_ATTEMPTS + 1):        # MAX_ATTEMPTS from config (e.g., 3 = 1 + 2 retries)
    resp = call_openrouter(messages)               # log line per attempt (D-14)
    try:
        return Model.model_validate(json.loads(resp.choices[0].message.content))
    except ValidationError as exc:
        raw = "\n".join(str(e) for e in exc.errors(include_url=False))
        write_log_line(..., status="invalid", attempt=attempt)
        messages.append({"role": "assistant", "content": resp.choices[0].message.content})
        messages.append({"role": "user", "content": f"JSON inválido. Corrija SOMENTE os erros abaixo e reenvie o objeto completo:\n{raw}"})
raise LLMError("Falha na geração após N tentativas — resposta inválida (detalhes no terminal)", raw)
```
Fail loud at exhaustion (D-03); malformed content never returns downstream (SC3). Retry is for VALIDATION errors only — network/API errors surface immediately (discretion: classify transient 429/5xx as fatal per D-03's no-fallback stance; the SDK's built-in connection retries can stay enabled).

### Pattern 4: Prompt file loader (mirror of profile loader)
Reuse the exact Phase 1 shape: `frontmatter.load(path, encoding="utf-8")` → strict Pydantic frontmatter model (`id: str`, `temperature: float`, `max_tokens: int`; `extra="forbid"` so a typo'd key fails loudly naming the key — D-06) → PromptError(message_ptbr, raw). Body (Markdown) = system prompt verbatim (D-07). Fresh read every call, no cache (D-08/Phase 1 D-15). `[VERIFIED: backend/app/profile/loader.py:29-54 is the template]`

### Pattern 5: JSONL call log (D-13/D-14)
One `json.dumps(..., ensure_ascii=False)` line appended per LLM attempt + a terminal summary line per run. Suggested field set (discretion): `ts, stage, model, language, attempt, status (ok|invalid|error), prompt_tokens, completion_tokens, total_tokens, cost, latency_ms, error` — `cost` straight from `usage.cost` (credits) `[CITED: openrouter.ai/docs/use-cases/usage-accounting]`. Open in append mode with `encoding="utf-8"`; create `logs/` on first write; add `logs/` to `.gitignore`. Rotation: file is small at personal scale — none for MVP, note as accepted simplification.

### Pattern 6: pytest marker harness (D-15/D-16)
In `backend/pyproject.toml` `[tool.pytest.ini_options]` (currently only `testpaths`/`pythonpath` — `[VERIFIED: backend/pyproject.toml:14-16]`):
```toml
markers = ["llm: real OpenRouter API calls (spend) — run explicitly with -m llm"]
addopts = "-m 'not llm'"   # day-to-day runs never touch the network (D-16); CLI -m llm overrides
```
Harness tests skip cleanly when the key is absent: `pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY ausente")`. Offline mocking: monkeypatch the gateway's SDK client (or inject a fake client) — no extra dependency needed.

### Anti-Patterns to Avoid
- **Sending Pydantic's `model_json_schema()` raw as the strict schema** — strict mode rejects it (optionals/`additionalProperties` shape mismatch); use Pattern 2.
- **`extra_headers={"require_parameters": True}`** — outdated; it's a provider-preference body field now `[CITED: openrouter.ai/docs/guides/features/structured-outputs]`.
- **Trusting `strict: true` on the wire** — per-provider enforcement varies; Pydantic re-validation is mandatory `[CITED]`.
- **Caching prompt files** (or the profile) between calls — violates D-08/SC1 (edit → next run reflects it).
- **Silent fallback to another model** — violates D-03.
- **Logging only the final attempt** — violates D-14; every retry must be auditable from the log alone.
- **Logging the full prompt/response content into runs.jsonl by default** — grows fast and duplicates profile/JD data; log metadata (tokens/cost/latency/status) and keep content out unless an explicit debug flag adds it `[ASSUMED — discretion]`.
- **Registering new routers after the SPA mount** — Pitfall 5 (`[VERIFIED: backend/app/main.py:20-30]` — though this phase may expose no new routes at all).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM HTTP client (auth, retries, streaming, errors) | raw requests plumbing | `openai` SDK with `base_url` | Documented OpenRouter path; typed `usage`/`cost`; timeouts handled |
| JSON schema generation for strict mode | runtime schema-transformation framework | Hand-maintained strict dict + drift-lock test (Pattern 2) | 2 schemas total; a framework is the LangChain trap by another name |
| Frontmatter parsing | custom `---` splitter | `python-frontmatter` (installed) | Same lib as profile loader; UTF-8 pitfalls already solved |
| PT-BR error rendering | new mapping | Reuse `app/profile/errors.py` patterns (map + fallback template) | Consistent UX; same error types occur (`extra_forbidden`, `missing`) |
| Cost calculation | multiplying tokens by price tables | `usage.cost` from OpenRouter | Official, exact, includes provider routing effects `[CITED: usage-accounting docs]` |

**Key insight:** the phase's real complexity is in the retry/validation/logging orchestration and the two-locked-schemas discipline — everything else is configuration of standard libraries.

## Common Pitfalls

### Pitfall 1: Strict json_schema rejected by the API
**What goes wrong:** 400 error — schema not strict-conformant (missing `additionalProperties: false`, optional fields not in `required`).
**Why:** Pydantic's JSON schema output doesn't match OpenAI-style strict mode.
**How to avoid:** Pattern 2; first `-m llm` run acts as the live probe.
**Warning signs:** API error mentioning "schema"/"strict" on the very first harness run.

### Pitfall 2: `require_parameters` sent as header (stale pattern)
**What goes wrong:** No error — silently ignored; requests route to providers without `response_format` support → JSON-in-prose responses.
**How to avoid:** `extra_body={"provider": {"require_parameters": True}}` `[CITED: current docs]`. Also verify the chosen model's supported-parameters page before pinning the slug.

### Pitfall 3: Model slug doesn't exist / renamed on OpenRouter
**What goes wrong:** 404/400 at harness run.
**Why:** STATE.md blocker — no model pinned yet; slug names change (`anthropic/claude-*` naming).
**How to avoid:** Slug in config only; harness's first job is validating the candidate slug. Exact default slug `[ASSUMED]` — confirm on openrouter.ai/models before pinning.
**Warning signs:** harness 404 naming the model.

### Pitfall 4: Missing/empty OPENROUTER_API_KEY at harness run
**What goes wrong:** 401 — or worse, tests fail confusingly.
**Why:** Probed NOW: key is unset/empty in `.env` (Environment Availability below).
**How to avoid:** skipif guard + clear skip reason telling the user to set the key.
**Warning signs:** every `-m llm` test skipped (silent success-looking output).

### Pitfall 5: Windows encoding on JSONL and prompt files
**What goes wrong:** mojibake PT-BR in logs / prompt read failures.
**Why:** Windows default codepage (Phase 1 Pitfall 7 already hit this).
**How to avoid:** explicit `encoding="utf-8"` on every file open (loader, JSONL writer); `ensure_ascii=False` in `json.dumps`. `[VERIFIED: backend/app/profile/loader.py:38 comment "Pitfall 7: explicit UTF-8"]`

### Pitfall 6: addopts marker exclusion hides the harness
**What goes wrong:** `pytest -m llm` deselects everything (marker not registered / addopts conflict) — or default run spends money.
**How to avoid:** register the marker (unknown-marker warning) and `-m 'not llm'` default; CLI `-m llm` comes after addopts and wins. Verify both commands behave in Wave 0.

### Pitfall 7: Retry loop resends the SAME messages
**What goes wrong:** identical failure repeated; no self-correction.
**How to avoid:** Pattern 3 — append the assistant's bad output + the validation error before retrying (SC3's exact requirement).

### Pitfall 8: logs/ not gitignored → secrets/content leaks into git
**What goes wrong:** runs.jsonl (containing model+cost metadata) committed.
**How to avoid:** add `logs/` to `.gitignore` in the same task that creates the writer. `[VERIFIED: .gitignore currently lacks a logs entry — read this session]`

## Code Examples

### Keyword output schema (reusing Phase 1 primitives)
```python
# Source: anchored to backend/app/profile/models.py (Language/LocalizedText/_Strict read this session)
from typing import Literal
from pydantic import BaseModel, ConfigDict
from app.profile.models import Language, LocalizedText  # "pt-BR" | "en"; dict[Language, str]

KeywordCategory = Literal[
    "competencias", "ferramentas", "titulos_de_vaga", "certificacoes"
]  # D-10 fixed set — exact token spelling is a planner decision (costly per D-10)

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Keyword(_Strict):
    canonical: str            # D-11
    aliases: list[str] = []
    pt: str | None = None     # D-09 pair — proper nouns identical, translatables paired
    en: str | None = None

class KeywordExtraction(_Strict):
    keywords: list[Keyword]
    # SC4 hooks: classification happens in Phase 3, but the shape must allow it —
    # Phase 3 extends/derives; no classification field is needed NOW beyond the
    # canonical/aliases/categories being machine-readable.
```
(Category tokens above are illustrative — the user-facing names in CONTEXT.md D-10 are "competências, ferramentas, títulos de vaga, certificações"; pin exact schema tokens at planning.)

### Config extension (anchored to existing config.py)
```python
# app/config.py additions (discretion on exact shape)
PROMPTS_DIR = REPO_ROOT / "prompts"
LOGS_DIR = REPO_ROOT / "logs"
RUNS_LOG = LOGS_DIR / "runs.jsonl"
LLM_MODEL = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5")  # slug [ASSUMED — verify on openrouter.ai/models]
LLM_MAX_ATTEMPTS = 3   # 1 + 2 validation retries (D-04)
```
`[VERIFIED: backend/app/config.py:13-21 — REPO_ROOT/CONTENT_DIR pattern exists; additions are new]`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `usage: {include: true}` / `stream_options` to get usage | usage returned automatically; `usage.cost` in credits | current docs (verified 2026-09-25) | Log writer reads `resp.usage.cost` directly |
| `require_parameters` as request header | provider-preferences body field (`provider.require_parameters`) | current docs (verified 2026-09-25) | Use `extra_body`, not `extra_headers` |
| prompt-side "output JSON only" enforcement | `response_format: {type: json_schema, strict: true}` + healing + Pydantic re-validation | — | Belt-and-suspenders; enforcement still varies by provider |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Default slug `anthropic/claude-sonnet-4.5` exists/is current on OpenRouter | Code Examples / Pitfall 3 | Harness 404; one-line config fix (slug is config-only by design); confirm on openrouter.ai/models |
| A2 | Strict-mode schemas require `additionalProperties: false` + all-properties-required; Pydantic `model_json_schema()` does not emit that | Pattern 2 / Pitfall 1 | First harness run 400s; fix is the hand-maintained dict (recommended anyway) |
| A3 | No extra mocking library needed (monkeypatch of SDK client suffices) | Pattern 6 | Minor: add respx/pytest-httpx if monkeypatching proves awkward |
| A4 | `logs/` directory can be auto-created on first write; no rotation needed at personal scale | Pattern 5 | Trivial: add rotation later |
| A5 | Log lines omit prompt/response content by default | Pattern 5 / anti-pattern | Discretion call; revisit if debugging needs content |
| A6 | Keyword schema category tokens (exact spelling, accents vs ASCII keys) | Code Examples | Naming is costly per D-10 — planner should pin exact tokens; fixtures + Phase 3 build on them |

## Open Questions

1. **Exact Claude Sonnet slug** — What we know: family pinned (D-01), slug in config. What's unclear: current OpenRouter slug string (A1). Recommendation: harness Wave-0 includes a tiny slug-probe test; user confirms slug on openrouter.ai/models.
2. **Does Phase 2 expose any HTTP route?** Success criteria are all harness/file-level; no UI. Recommendation: no new routes (keeps Pitfall 5 moot); the gateway is exercised via tests/scripts. Planner confirms.
3. **Category token spelling in the schema** (A6) — pt with accents vs ASCII keys. Recommendation: ASCII keys + PT-BR display labels, decided at planning.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | backend management | ✓ | 0.12.5 | — |
| Python | backend runtime | ✓ | 3.12.10 | — |
| FastAPI/Pydantic/pytest/httpx stack | existing suite | ✓ | per pyproject (installed) | — |
| `openai` PyPI package | gateway | ✗ (not installed) | — | `uv add openai` (planner task) |
| OPENROUTER_API_KEY in `.env` | `-m llm` harness only | ✗ (unset/empty — probed) | — | skipif guard; user sets key before running harness |
| OpenRouter network reachability | `-m llm` harness | untested | — | harness run is the probe |
| `prompts/`, `logs/` dirs | meta-prompts, run log | ✗ (absent — probed) | — | created by phase tasks; `logs/` gitignored |

**Missing dependencies with no fallback:** OPENROUTER_API_KEY (user action — add real key to `.env`; blocks only the `-m llm` harness, not offline work).
**Missing dependencies with fallback:** `openai` package (install task); dirs (create task).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (installed, `backend/pyproject.toml [tool.pytest.ini_options]`) |
| Config file | `backend/pyproject.toml` — needs `markers` + `addopts = "-m 'not llm'"` added |
| Quick run command | `uv run --project backend pytest` (offline, excludes llm) |
| Full suite command | `uv run --project backend pytest` then optionally `uv run --project backend pytest -m llm` (real API, needs key) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROFILE-03 / SC1 | Prompt-file edit reflected on next run (fresh read; loader validates frontmatter strictly) | unit | `uv run --project backend pytest tests/test_prompt_loader.py -x` | ❌ Wave 0 |
| SC2 | Gateway logs every call (stage/model/tokens/cost/lang); model from config | unit (mock client) | `uv run --project backend pytest tests/test_gateway.py -x` | ❌ Wave 0 |
| SC2 | Real harness EN + PT-BR | integration (marked llm) | `uv run --project backend pytest -m llm -x` | ❌ Wave 0 |
| SC3 | Malformed → retried with error appended → recovered OR loud failure; nothing invalid passes | unit (mock client) | `uv run --project backend pytest tests/test_gateway.py -k retry -x` | ❌ Wave 0 |
| SC4 | Keyword schema: PT↔EN mapping, fixed categories, canonical+aliases, coverage-hook shape | unit | `uv run --project backend pytest tests/test_keyword_schema.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run --project backend pytest`
- **Per wave merge:** same + `pytest -m llm` if key available
- **Phase gate:** offline suite green; `-m llm` run (with key) green in both languages — SC2's acceptance bar

### Wave 0 Gaps
- [ ] `backend/tests/test_prompt_loader.py` — PROFILE-03/SC1
- [ ] `backend/tests/test_gateway.py` — SC2/SC3 (mock client)
- [ ] `backend/tests/test_keyword_schema.py` — SC4
- [ ] `backend/tests/test_llm_harness.py` — SC2 real API (`@pytest.mark.llm`, skipif no key)
- [ ] pyproject: register `llm` marker + `addopts = "-m 'not llm'"`
- [ ] `.gitignore`: add `logs/`
- [ ] Install: `uv add --project backend openai`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Single-user localhost; no auth (PROJECT.md) |
| V3 Session Management | no | — |
| V4 Access Control | no | Localhost personal tool |
| V5 Input Validation | yes | Strict Pydantic (`extra="forbid"`) on prompt frontmatter, LLM responses, keyword schema; json.loads of model content only after length/type guards |
| V6 Cryptography | no | Key handled by transport (HTTPS to OpenRouter) |
| V14 Config & Secrets | yes | `OPENROUTER_API_KEY` stays in gitignored `.env` (V14.3); never logged into runs.jsonl; `logs/` gitignored; fail loud if key missing when a real call is attempted |

### Known Threat Patterns for LLM-gateway stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via pasted JD (untrusted input → LLM) | Tampering/Elevation | JD is data in the user message, never system (D-07); system prompt declares facts-only; output is schema-validated and never executed — worst case is a failed validation, contained by the retry cap |
| Secret leakage into logs | Information Disclosure | runs.jsonl logs metadata only (A5); no `.env` values in log lines; `logs/` gitignored |
| Excessive spend (runaway loop) | DoS (wallet) | max_tokens per stage + hard retry cap in config (D-04); every attempt logged for audit (D-14) |
| Malicious/typosquatted dependency | Supply Chain | Package Legitimacy Audit above; `openai` is the official OpenAI repo package |

## Sources

### Primary (HIGH confidence)
- Codebase read this session: `backend/app/config.py`, `app/main.py`, `app/profile/{models,loader,errors}.py`, `app/routes/profile.py`, `backend/pyproject.toml`, `backend/tests/conftest.py`, `.gitignore`
- https://openrouter.ai/docs/guides/features/structured-outputs — strict flag, provider-preference `require_parameters`, per-endpoint enforcement variance, Response Healing (fetched 2026-09-25)
- https://openrouter.ai/docs/use-cases/usage-accounting — `usage.cost` (credits), automatic usage inclusion, deprecated include param (fetched 2026-09-25)
- `.planning/research/STACK.md` — pinned stack decisions (OpenAI SDK + base_url, Pydantic re-validation mandate)
- Environment probes: uv 0.12.5, Python 3.12.10, openai not installed, key unset, dirs absent

### Secondary (MEDIUM confidence)
- `.planning/phases/01-.../01-CONTEXT.md` decisions referenced via CONTEXT.md canonical_refs (not re-read this session)

### Tertiary (LOW confidence)
- Training-knowledge items logged as Assumptions A1–A3

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — one new dependency, official-docs-verified integration path
- Architecture: HIGH — anchored on Phase 1 code read this session; decisions D-01..D-16 fix the shape
- Pitfalls: MEDIUM-HIGH — two doc-verified corrections (require_parameters, usage.cost); strict-schema shape is assumption A2 until first harness run

**Research date:** 2026-09-25
**Valid until:** 2026-10-25 (model slugs and OpenRouter API details drift — re-verify slug before pinning)
