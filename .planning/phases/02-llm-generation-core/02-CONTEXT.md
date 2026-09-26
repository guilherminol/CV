# Phase 2: LLM Generation Core - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

One OpenRouter gateway through which every LLM call flows: logged per call to `logs/runs.jsonl`, schema-validated (strict Pydantic; malformed responses retried with the validation error appended, then loud failure), bilingual by parameter (PT-BR/EN, base pt-BR), and driven by meta-prompts the user edits as versioned git files in `prompts/`. Plus the input-agnostic keyword engine: one prompt that extracts keywords from a pasted JD or a career objective and returns them mapped across {en, pt}, classified in fixed categories, with canonical form + aliases and covered/adjacent/absent classification hooks for Phase 3's coverage checks. A real-API fixture harness (`pytest -m llm`) proves EN and PT-BR generation. Delivers PROFILE-03.

Not in this phase: any product UI, resume generation, PDF, LinkedIn — Phases 3–6. PT-BR hardening (terminology glossary, QA gate, both-language fixtures as definition-of-done) is Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Política de modelos
- **D-01:** **Default model family: Claude Sonnet** (`claude-*` on OpenRouter) for generation. User's choice among Claude/GPT/Gemini/other; strong PT-BR prose + strict structured outputs were the deciding qualities. — **Reversibility:** reversible — slug lives in config; swapping is a one-line change (roadmap SC2).
- **D-02:** **Single global model, no per-stage override.** One slug in config serves keyword extraction and generation alike. Simplicity over token-cost micro-optimization at personal scale; per-stage override can be added later as purely additive config.
- **D-03:** **Fail loud — no automatic model fallback.** Network error, unavailable model, or malformed JSON after retries surfaces as a clear error with the full detail in the log. Deliberately coherent with Phase 1's fail-fast loader philosophy (ProfileError pattern); fallback resilience would add config and unpredictable cost.
- **D-04:** **Cost/size guardrails live in config:** `max_tokens` per stage + a retry cap (e.g., 2 validation-error retries) fixed in one place. No unbounded runs.

### Meta-prompt files
- **D-05:** **One file per stage** (e.g., `prompts/keyword-extraction.md`; Phase 3 adds its own). Editing one prompt never means reading the others; new stages are new files.
- **D-06:** **Format: Markdown body + YAML frontmatter** (frontmatter holds id and stage params like temperature/max_tokens). Validated with strict Pydantic (`extra="forbid"`) so a typo'd key fails loudly naming the key — the same ergonomic the profile loader gives `content/profile.md`. — **Reversibility:** costly — the format is the user's hand-editing surface; changing it means migrating every prompt file plus the loader and its tests in one move.
- **D-07:** **Prompt file = system prompt; runtime inputs go in the user message.** The JD/objective text, master-profile facts, and the language parameter are composed into the user message by the gateway. No `{{template}}` variables — nothing to half-substitute silently; prompt files stay free of volatile data.
- **D-08:** **`prompts/` at repo root, sibling of `content/`.** Prompts are user-edited versioned content, not code. Files are read fresh on every call (same no-cache rule as the profile, Phase 1 D-15) — edit file → next run reflects it, which is SC1 verbatim.

### Keywords PT↔EN
- **D-09:** **The LLM maps PT↔EN in the extraction call itself** — the structured output carries each keyword in both languages (shape mirrors the schema's `LocalizedText` idea). Tech proper nouns pass through identical; translatable terms get their pair. The Phase 6 glossary can later pin/override bad translations without changing this shape.
- **D-10:** **Fixed categories in the structured output:** competências, ferramentas, títulos de vaga, certificações (roadmap SC4 / RESUME-02 list). — **Reversibility:** costly — Phase 3's coverage checklist and the fixtures are built on these category names; re-keying means migrating schema, fixtures, and UI labels together.
- **D-11:** **Canonical form + aliases** (e.g., canonical "Kubernetes", alias "k8s"). Phase 3 coverage counts a keyword as present if the canonical form OR any alias appears — abbreviations never become false negatives.
- **D-12:** **One input-agnostic prompt** for both JD and career objective (the "input-agnostic engine" of SC4 taken literally). Fewer files to maintain; the engine code path is identical regardless of input.

### Logs & fixtures
- **D-13:** **Call log is `logs/runs.jsonl` (gitignored), one JSON line per LLM call + terminal summary.** Fields include stage, model, tokens, cost, latency, language. This file is the foundation the Phase 5/6 run store builds on. — **Reversibility:** costly — once the run store and cost audits parse this file, changing its format means compat handling or migration; treat the line schema as a contract from day one.
- **D-14:** **Granularity: per LLM call, including retries** (line carries the attempt number). Auditing retries and exact spend must be possible from the log alone.
- **D-15:** **Fixture harness = `pytest -m llm`** — marked tests hitting the real OpenRouter API, run only on demand (`uv run pytest -m llm`). Integrated with the existing suite; the regular day-to-day run never touches the network. Harness fixtures cover EN and PT-BR generation (SC2).
- **D-16:** **Regular test suite is 100% offline** — OpenRouter responses are simulated/mocked; real API spend happens only under `-m llm`.

### Claude's Discretion
- Exact `claude-*` slug pinned as default — STATE.md requires the fixture harness to validate strict `json_schema` compliance and PT-BR quality before locking it; slug lives in config only.
- OpenRouter client mechanics: OpenAI-compatible SDK vs raw `httpx`, structured-outputs enforcement (`response_format: json_schema` vs prompt-side enforcement + validation), retry/backoff mechanics, what counts as transient vs fatal.
- JSONL line field names, terminal summary format, log file rotation policy.
- Prompt frontmatter exact key set and the Pydantic model for it; `app/llm/` package layout; how profile facts are serialized into the user message.
- Mocking library/technique for offline tests; fixture input texts (realistic sample JD + career objective) as long as both languages are covered.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — constraints (OpenRouter only, key in gitignored `.env`, localhost, JS frontend/Python backend), key decisions, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — PROFILE-03 (this phase), RESUME-02/RESUME-04 (Phase 3 consumers of the keyword engine's output), LI-01 (Phase 6 consumer)
- `.planning/ROADMAP.md` §Phase 2 — goal + 4 success criteria (the acceptance bar); also §Phase 6 for what is deliberately NOT here (glossary, QA gate)

### Prior phase decisions this phase builds on
- `.planning/phases/01-foundation-scaffold-master-profile/01-CONTEXT.md` — D-01–D-04 (localized maps, base pt-BR, fallback), D-09 (skills as categorized plain tech names), D-13/D-14 (error style), D-15 (no caching)

### Research (pinned patterns and risks)
- `.planning/research/STACK.md` — pinned stack/versions (FastAPI, Pydantic, httpx as dev dep); What-NOT-to-use table
- `.planning/research/ARCHITECTURE.md` — component architecture; Profile Loader fail-fast pattern this phase mirrors for prompt files
- `.planning/research/PITFALLS.md` — pitfalls referenced by existing code comments (registration order, UTF-8, YAML dates)

No external specs/ADRs — no user-referenced docs beyond the planning set above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/config.py` — central config with tolerant `OPENROUTER_API_KEY` read, `REPO_ROOT`, `CONTENT_DIR`; extend with model slug, `PROMPTS_DIR`, logs path, max_tokens/retry settings
- `backend/app/profile/models.py` — `Language = Literal["pt-BR", "en"]`, `LocalizedText`, `BASE_LANGUAGE`, and the `_Strict` (extra="forbid") base: reuse directly for the keyword output schema ({en, pt} mapping) and the prompt frontmatter model
- `backend/app/profile/loader.py` + `errors.py` — fail-fast file→Pydantic pattern with PT-BR message + raw terminal detail: the template for the meta-prompt file loader
- `backend/app/routes/profile.py` — status-envelope route pattern (200 + status, never 500, raw detail to terminal): the pattern for any route this phase exposes
- Existing pytest suite (`backend/tests/`, `httpx` dev dep) — home for both offline tests and the new `-m llm` mark

### Established Patterns
- Fail-fast validation, PT-BR user-facing message + raw detail terminal-only (Phase 1 D-13/D-14)
- No caching — fresh read per call (Phase 1 D-15), extended to prompt files by D-08
- Strict Pydantic `extra="forbid"` on every model
- API routes registered BEFORE the SPA StaticFiles mount in `main.py` (Pitfall 5)
- Config via `.env` + module constants

### Integration Points
- `backend/app/main.py` — any new router must be included before the SPA mount
- `.env` key already read tolerantly; Phase 2 makes it required-in-practice whenever a real generation is requested (fixtures, future phases)
- The gateway/keyword engine's structured output is the contract Phase 3 consumes (visible keywords RESUME-02, coverage checklist RESUME-04) — covered/adjacent/absent hooks (SC4) must exist in the shape now even though classification happens later
- `logs/runs.jsonl` is the seed of the Phase 5/6 run store
- `content/profile.md` → loader is the fact source the gateway serializes into user messages

</code_context>

<specifics>
## Specific Ideas

- User ran the entire discussion in PT-BR and requested future discussions in PT-BR — the app's PT-BR-first character (UI language, error messages per Phase 1 D-13/D-14) extends to this phase's user-facing errors.
- "Falhar alto" was chosen explicitly to stay coherent with Phase 1's fail-fast philosophy — the user values debuggability and predictable cost over resilience magic.
- SC1's editing loop is the core UX of this phase: edit a prompt file in git → run → reflected with zero code edits.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (PT↔EN glossary is roadmap-scheduled Phase 6 work, recorded in D-09, not deferred here.)

</deferred>

---

*Phase: 2-LLM Generation Core*
*Context gathered: 2026-09-25*
