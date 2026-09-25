# Project Research Summary

**Project:** Career Tailor
**Domain:** Personal localhost LLM-powered content-generation web app (ATS resume tailoring + LinkedIn optimization), bilingual EN/PT-BR
**Researched:** 2026-09-25
**Confidence:** HIGH (stack and architecture verified against official docs and live registries; features and some pitfalls rest on cross-checked secondary sources — see Confidence Assessment)

## Executive Summary

Career Tailor is a single-user, localhost web app with two generation modules — an ATS resume tailored from a pasted job description, and LinkedIn sections driven by a career objective — both drawing from one master profile stored as Markdown/YAML in git, generating in EN and PT-BR via OpenRouter, and exporting a single-column Google-format PDF. This is a well-trodden product category, and the research converges on one clear shape: a **Vite + React + TypeScript SPA → FastAPI backend → OpenRouter via the OpenAI-compatible SDK with strict `json_schema` structured outputs**, a **staged prompt pipeline** (analyze input → plan → one LLM call per section), a **backend-owned run store** powering the review flow, and **one HTML print template rendered by headless Chromium** into a text-layer PDF. The commercial cluster (Jobscan, Teal, Rezi, Resume Worded) is broad but misses this project's exact niche: one shared profile feeding both input modes (vacancy + objective), bilingual generation, and git-owned data.

The recommended build order follows the dependency graph: master profile schema first (root of everything), then the LLM gateway with validation and a bilingual fixture harness, then a resume vertical slice (paste JD → tailored sections), then PDF export with an automated extraction gate, then the review flow, then the LinkedIn module which reuses the core wholesale. Bilingual support is a *parameter of every prompt from the start*, not a retrofit — retrofitting means re-testing every prompt in two languages.

The dominant risks are all known and preventable: (1) **a PDF that looks perfect but extracts as garbage** — ATS parsers read the text layer in glyph-emission order, scrambling columns/tables and silently mangling PT-BR accents; mitigate with an automated parse-back extraction gate built as the *first* task of the PDF phase, tested in both languages. (2) **LLM embellishment** — fabricated metrics sent to real employers; mitigate with facts-only grounding (inject profile slices, never ask for numbers) plus a source-vs-generated fact diff in the review UI. (3) **Structured-output non-compliance** — OpenRouter's `json_schema` enforcement varies per provider/endpoint; always re-validate with Pydantic and retry with the validation error appended. (4) **PT-BR quality drift** — documented 25–35% multilingual instruction-following gaps and a ~1.5–2x token cost; mitigate with target-language few-shot examples, a terminology glossary, and a both-languages fixture suite run on every prompt change.

## Key Findings

### Recommended Stack

Full detail in [STACK.md](STACK.md). All versions verified live from npm/PyPI on 2026-09-25. One line of shape: Vite dev-proxies `/api` to FastAPI; for daily use a single `npm run build` lets FastAPI serve `frontend/dist` — one process, no Node needed after build.

**Core technologies:**
- **Vite 8.3.1 + React 19.3 + TypeScript ~5.9** (pin 5.x; npm `latest` is 7.0.2 Go-native) — default JS frontend; `tsc --noEmit` catches drift between Pydantic and frontend contracts
- **FastAPI 0.141.1 + uvicorn 0.54.0 on Python 3.12.10 (installed)** — async endpoints for I/O-bound LLM calls, Pydantic-native contracts, free `/docs`; user's stated preference wins for a personal tool
- **openai SDK (PyPI 3.19.2) pointed at `base_url="https://openrouter.ai/api/v1"`** — the most-documented OpenRouter path; vendor-portable; `response_format: json_schema` + `require_parameters` header; model slugs live in config, never code
- **python-frontmatter 1.3.0 + Pydantic 2.13.5** — `profile.md` (YAML frontmatter + Markdown body) validated with file/field-level errors at load time
- **Playwright (PyPI 1.63.0) headless Chromium** — PDF export from the same HTML template reviewed in-app; real embedded text layer; one-time `playwright install chromium`
- **@tanstack/react-query 5.103.2 + zod 4.6.5** — per-section mutation/refetch for the review flow; frontend re-validation of LLM JSON before rendering
- **uv 0.12.19** for Python env management; Tailwind 4.3.3 with `print:` variants; PT-BR UI strings hardcoded (no i18n framework for one user)

**Explicitly rejected:** Next.js (dead weight on localhost), LangChain/prompt frameworks (~2–4 call sites; hides the prompts being iterated), any database (git is the store), client-side/canvas PDF generation (**no text layer — fatal for ATS**), DOCX generators (out of scope), axios, i18n frameworks. A full Node variant (Express 5.2.1 + gray-matter) exists as a documented fallback if the Python preference ever changes.

### Expected Features

Full detail in [FEATURES.md](FEATURES.md). The niche: no commercial tool combines one master profile + both input modes (vacancy and objective) + bilingual output + data ownership.

**Must have (table stakes):**
- Master profile as single source of truth (Teal's "master history" pattern) — schema design is the real work
- JD paste input + per-run language selector; keyword extraction with a *visible* keyword list (the category's core mechanic — confirmed for Western ATS and Gupy in Brazil)
- Sectioned resume generation grounded in the profile with a **facts-only constraint** (one-shot black-box generation is the category's #1 complaint)
- Review flow: per-section regenerate + inline edit — non-negotiable stated requirement
- Keyword coverage **checklist** (present/missing), not a vanity score
- ATS-safe single-column PDF with verified clean text layer; bilingual EN/PT-BR generation
- LinkedIn section generation (headline > About > experience > skills is the recruiter-search weight order)

**Should have (differentiators):**
- Git-versioned master profile (surface `git log` as a feature, not an implementation detail)
- Objective brief as first-class input feeding the same keyword engine (the project's stated twist)
- ATS self-check on the exported PDF — nobody in the consumer space verifies their own output
- Inspectable, editable meta-prompts in git; profile completeness lint; PT-BR UI

**Defer (v2+):** cover letters, DOCX export (build only when a real vacancy demands it), profile variants, application tracker.

**Anti-features (documented to prevent scope re-entry):** template gallery (conflicts with the fixed ATS format), numeric ATS score (fake precision), keyword stuffing, LLM-invented achievements, URL extraction, auto-apply, LinkedIn automation, multi-user/auth.

### Architecture Approach

Full detail in [ARCHITECTURE.md](ARCHITECTURE.md). The system is a monolith of seven small components over a file-based data layer: every LLM stage communicates through a typed JSON contract (Pydantic model + JSON Schema), never free-form prompt strings. Profile/prompts/outputs live at repo root as *content*, not code — the app reads them at runtime and never writes to `profile/`.

**Major components:**
1. **Profile Loader** — frontmatter parse → Pydantic `model_validate` → typed object; fail-fast with file/field errors before any generation
2. **LLM Gateway** — single choke point for all OpenRouter calls (auth, model-per-stage from config, retries, cost logging); `complete_structured(schema)` is the only shape pipelines consume
3. **Prompt Pipeline** — staged: analyze input → JobProfile JSON; plan; generate one section per call with a *sliced* profile (only the relevant experience/skills) + JobProfile + language
4. **Run Store** — backend-owned draft with a section state machine (`pending → generating → generated → edited → accepted`); snapshots to `outputs/<run-id>/`; survives refreshes; makes regenerate = same code path as initial generation
5. **PDF Renderer** — one Jinja2 HTML template + print CSS is the single source of truth for both the review preview and the exported file
6. **Frontend SPA** — React Query projections of backend state; SSE streaming per section; zod mirrors of backend contracts

**Non-negotiable patterns:** grounding rule (Stage 3 only ever sees real profile slices; the LLM selects and rewords, never recalls), language as a run parameter with keywords cross-mapped `{en, pt}` at the analysis stage, SPA mounted *after* API routes in FastAPI.

### Critical Pitfalls

Full detail in [PITFALLS.md](PITFALLS.md) — eight pitfalls with prevention mapped to phases. Top five:

1. **PDF extracts as garbage despite looking perfect** — extraction order is glyph-emission order, not visual order; two-column layouts interleave, tables flatten, PT-BR accents can silently corrupt. *Prevent:* single-column constraints enforced in the template itself; Latin-ext fonts; **automated parse-back gate (extract text and assert contact-first order, canonical headings, co-occurring company/title/dates, intact accents) as the first task of the PDF phase, run on every export in both languages.**
2. **LLM embellishment** — invented metrics/technologies sent to real employers. *Prevent:* prompts receive only profile-derived facts with an explicit "never add numbers, technologies, dates absent from the source"; never ask the model for metrics; fact-diff surfaced in the review UI.
3. **Structured-output non-compliance** — `json_schema` enforcement **varies by provider/endpoint** on OpenRouter. *Prevent:* `strict: true` + `require_parameters: true` + app-level Pydantic re-validation with the validation error appended on retry; template renders only from validated JSON.
4. **PT-BR quality drift + token multiplier** — documented multilingual instruction-following gaps; English bleed and PT-PT mixing; PT costs ~1.5–2x tokens. *Prevent:* language as a structured field with in-language few-shot examples; terminology glossary; language QA gate; both-language fixtures on every prompt change.
5. **Profile drift** — in-app edits that never return to git get reverted by the next regeneration; localization shape retrofitted late is painful (JSON Resume has no localization support). *Prevent:* decide the localization schema shape in Phase 1; validate on load; make the in-app edit policy explicit (ephemeral-with-warning or write-back) — no ambiguity.

Also load-bearing: keyword stuffing gains nothing with modern ATS and repels recruiters (design coverage/absent classification in, not patched on), and the prompt pipeline must be decomposed per-section with call logging and a fixture regression suite from day one (what makes OpenRouter model-flexibility real).

**One cross-research conflict, resolved:** STACK.md and ARCHITECTURE.md both recommend Playwright Chromium `page.pdf()` (preview parity, official docs); PITFALLS.md warns Chrome print-to-PDF reorders glyphs via CSS layout and prefers text-first engines (WeasyPrint). **Resolution: build with Playwright for preview parity — the fixed single-column template minimizes reordering risk — but the parse-back gate is the phase's first task and the acceptance criterion. If extraction assertions fail, WeasyPrint is the pre-approved fallback engine behind the same HTML-derived data.**

## Implications for Roadmap

Based on research, suggested phase structure (merges ARCHITECTURE.md's build order, PITFALLS.md's pitfall-to-phase mapping, and FEATURES.md's dependency graph/MVP definition):

### Phase 1: Foundation — Scaffold + Master Profile
**Rationale:** The profile is the root dependency of every feature (FEATURES.md dependency graph); the localization schema shape must be decided before any generation exists (Pitfall 6).
**Delivers:** Repo scaffold (Vite+React+TS frontend, FastAPI+uv backend, `.env` gitignored before first commit); `profile.md` schema + example data; Pydantic loader with loud file/field errors; **decided localization shape** (parallel localized fields vs per-language files); placeholder-data banner.
**Addresses:** Master profile (table stake), git-versioned profile (differentiator).
**Avoids:** Pitfall 6 (schema rot, example-data leak, localization retrofit).

### Phase 2: LLM Generation Core
**Rationale:** Prove OpenRouter connectivity, structured outputs, and .env handling with zero product surface before building UI on top (ARCHITECTURE build order 2). The keyword extraction engine must be input-agnostic (JD and objective modes) from day one to avoid a rewrite when LinkedIn arrives.
**Delivers:** LLM Gateway (model-per-stage in config, `complete_text`/`complete_structured`, retries); Pydantic re-validation + retry-with-error; prompts as versioned files; call logging; EN+PT-BR fixture harness; keyword extraction returning `{en, pt}` cross-mapped keywords with covered/adjacent/absent classification hooks.
**Uses:** openai SDK + `base_url`, python-frontmatter, pydantic, uv, python-dotenv.
**Avoids:** Pitfalls 5 and 7 (these are this phase's foundation, not polish); establishes grounding rules (Pitfall 2) and bilingual fixtures (Pitfall 4).

### Phase 3: Resume Pipeline — Vertical Slice
**Rationale:** The first proof of core value: paste JD → tailored, grounded sections. Minimal UI is enough; the review flow comes later and needs this phase's per-section isolation.
**Delivers:** Staged pipeline (analyze_jd → plan → per-section generate); JD paste + language selector (PT-BR UI strings); keyword coverage checklist (present/missing); sections rendered read-only.
**Addresses:** Four P1 table stakes (JD input, keyword extraction, sectioned grounded generation, coverage checklist).
**Avoids:** Pitfall 3 — coverage-not-density prompt rules and "never insert an absent keyword" are designed in here.

### Phase 4: PDF Export + ATS Self-Check
**Rationale:** Delivers the first actually-sendable artifact; the parse-back gate must exist *before styling work* (Pitfall 1's explicit instruction) and before anyone trusts an export.
**Delivers:** Jinja2 single-column print template (standard headings, Latin-ext fonts, localized headings dict); Playwright Chromium render; **parse-back extraction gate as the phase's first task** — assertions on contact-first order, canonical headings, co-occurring company/title/dates, intact PT-BR accents, run on every export in both languages; ATS self-check surfaced to the user.
**Addresses:** Google-format PDF export (table stake), ATS self-check (differentiator).
**Avoids:** Pitfall 1 — the single biggest real-world failure mode.

### Phase 5: Review Flow + Fact Safety
**Rationale:** The review flow is a stated core requirement and the human quality gate for LLM errors; it depends on Phase 3's section isolation and is easiest to judge against Phase 4's real PDF preview. The edit write-back policy must be resolved explicitly here (Pitfall 6).
**Delivers:** Backend run store with section state machine; per-section regenerate with optional user hint (SSE streaming, sections generated in parallel); inline edit; **side-by-side source-vs-generated fact diff**; explicit edit policy (ephemeral-with-warning or write-back to profile files); per-section version history.
**Addresses:** Review flow (table stake), fact-integrity and UX differentiators.
**Avoids:** Pitfall 2's UI half, Pitfall 6's edit-policy half, regenerate-replaces-history UX trap.

### Phase 6: LinkedIn Module + Bilingual Hardening
**Rationale:** Reuses gateway, pipeline pattern, run store, and review UI wholesale — only prompts and block types are new (no PDF stage). Comes last among feature phases because the shared engine should be validated by the resume module first. Bilingual hardening is last because it is refinement of parameters, not structure — though the language parameter itself exists from Phase 2.
**Delivers:** Objective brief input; headline/About/experience/skills generation with schema `maxLength` (220/2,600/2,000), live character counters, headline front-load check (~70 chars); copy-paste output blocks; PT-BR terminology glossary + language QA gate; both-language fixture run as definition-of-done for every prompt.
**Addresses:** LinkedIn generation (table stake), objective-driven input and honest-checklist differentiators.
**Avoids:** Pitfall 8 (silent truncation, resume/LinkedIn claim mismatch), formalizes Pitfall 4.

### Phase Ordering Rationale

- **Profile → generation core → resume slice:** strict dependency chain from FEATURES.md — nothing is meaningful before the typed profile, and nothing should consume the LLM before validation/logging/fixtures exist.
- **PDF before full review UI:** the review flow's value is easiest to judge against a real PDF, and the parse-back gate must precede trust in any export. (These two can swap if needed, but not by much.)
- **Resume before LinkedIn:** the vacancy-driven module is the core value and validates the shared keyword engine; LinkedIn then costs only prompts + block types.
- **Anti-dependency (from research):** do not start with the review UI (nothing to review) and do not bolt bilingual on late (language is a prompt parameter from Phase 2; refinement lands in Phase 6).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4:** PDF engine extraction-order verification — resolve the Playwright vs WeasyPrint tension empirically with the parse-back gate; verify font Latin-ext coverage for PT-BR. Recommend `/gsd:plan-phase --research-phase 4`.
- **Phase 6:** LinkedIn character limits (220/2,600/2,000) rest on MEDIUM-confidence secondary sources — verify at planning time.

Phases with standard patterns (skip research-phase):
- **Phase 1:** FastAPI/Vite/Pydantic scaffolding and frontmatter loading — exhaustively documented.
- **Phase 3:** staged LLM pipeline over verified OpenRouter patterns — the only open question (model choice) is answered empirically by the Phase 2 fixture harness, not by more web research.
- **Phase 5:** React Query + SSE + CRUD-style state machine — standard, well-documented patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every version verified live from npm/PyPI on 2026-09-25; integration patterns from official OpenRouter, Playwright, and FastAPI docs; local Node v22.16.0 / Python 3.12.10 verified. React choice itself is user-constrained (MEDIUM as a "best" claim). Caveat: WebSearch was rate-limited, so community-consensus framings rest on registry evidence + prior knowledge. |
| Features | MEDIUM | Every competitor claim cross-checked against an official product page plus an independent review; ATS/LinkedIn mechanics cross-checked across 3+ guides. No single-source findings. |
| Architecture | HIGH | Integration mechanics (OpenRouter structured outputs, SSE, print-to-PDF semantics, SPA mounting) from official docs; pipeline patterns corroborated across multiple ecosystem sources (corroboration is MEDIUM). |
| Pitfalls | HIGH | PDF/ATS mechanics, structured-output behavior, and multilingual findings from official docs + peer-reviewed papers. Keyword-stuffing penalties and LinkedIn limits are MEDIUM (secondary sources in agreement). Hallucination-in-resume specifics are LOW (practitioner consensus, no direct studies) — treat the risk as real regardless. |

**Overall confidence:** HIGH — sufficient for roadmap creation; the gaps below are bounded and each has a named resolution point.

### Gaps to Address

- **PDF engine extraction order (Playwright vs WeasyPrint):** resolve empirically in Phase 4's first task via the parse-back gate; WeasyPrint is the pre-approved fallback behind the same data.
- **OpenRouter model selection:** no specific model is pinned. Validate strict `json_schema` compliance and PT-BR quality with the fixture harness during Phase 2; keep slugs in config so swapping is a config change.
- **Localization schema shape:** per-field localized values vs per-language profile files is undecided (JSON Resume offers no localization). Decide in Phase 1 planning — retrofitting is the expensive path.
- **In-app edit write-back policy:** ephemeral-with-warning vs write-back to `profile/` files is a product decision that must be made explicitly in Phase 5, not left ambiguous.
- **Keyword extraction approach (LLM stage vs NLP libraries):** LLM-stage was inferred, not directly compared (search rate-limited). Validate quality against the fixture set in Phase 2; an NLP pre-pass is a contained addition if extraction proves weak.
- **LinkedIn character limits:** verify 220/2,600/2,000 against LinkedIn at Phase 6 planning.

## Sources

Aggregated from STACK.md, FEATURES.md, ARCHITECTURE.md, and PITFALLS.md (full per-file source lists in each document).

### Primary (HIGH confidence)
- npm registry + PyPI JSON API (fetched 2026-09-25) — all pinned versions
- OpenRouter official docs — OpenAI SDK compatibility, structured outputs (`json_schema`, `strict`, `require_parameters`), per-provider enforcement caveat, streaming
- Playwright / Puppeteer / Chromium official docs — `page.pdf()` options, print-CSS media semantics, text-based output
- FastAPI official docs — StaticFiles mounting order, SSE/streaming responses; Pydantic v2 docs — validation, aggregated errors
- PyMuPDF docs — PDF text extraction order and column behavior
- Anthropic docs — prompt chaining and validate-between-steps guidance
- Peer-reviewed: Marco-Bench-MIF (arXiv:2507.11882), Multi-IF (arXiv:2410.15553), M-IFEval (arXiv:2502.04688), tokenizer disparity (arXiv:2305.15425, NeurIPS 2023)
- JSON Resume schema (official) — absence of localization support

### Secondary (MEDIUM confidence)
- Jobscan, Teal, Rezi, Resume Worded, Kickresume official pages + independent reviews — competitor feature matrix
- Indeed / Novoresume ATS guides — keyword screening, format parsing rules
- LinkedIn limits and recruiter-search-weight guides (multiple secondary sources in agreement)
- Brazilian ATS (Gupy) guides — keyword-based screening in the dominant Brazilian platform
- Bilingual PT-BR/EN resume market practice guides
- ZenML / Vercel AI SDK / LangGraph patterns — plan→sections→review pipeline corroboration

### Tertiary (LOW confidence — validate during implementation)
- Hallucination-in-resume specifics — practitioner consensus, no direct studies; risk treated as real regardless
- LLM-stage keyword extraction vs NLP alternatives — inferred, comparison search rate-limited
- "Chromium-only" restriction for `page.pdf()` — current docs no longer state it explicitly (moot: bundled Chromium always used)

---
*Research completed: 2026-09-25*
*Ready for roadmap: yes*
