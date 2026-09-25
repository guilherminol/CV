# Phase 1: Foundation — Scaffold + Master Profile - Context

**Gathered:** 2026-09-25
**Status:** Ready for planning

<domain>
## Phase Boundary

The app runs locally with a PT-BR interface (Vite + React + TS frontend, FastAPI backend via uv), and the master profile is a git-versioned, schema-validated source of truth: `content/profile.md` validated loudly on load by Pydantic (file/field errors, unknown keys rejected), shipped with fully bilingual example data flagged as placeholder, OpenRouter key in gitignored `.env`. Delivers PROFILE-01. No LLM calls, no resume generation, no PDF — those are Phases 2+.

</domain>

<decisions>
## Implementation Decisions

### Bilingual schema shape (the flagged Phase 1 decision)
- **D-01:** Localized content is encoded as **localized maps** — one field holding a language→text map (e.g., `summary: {pt-BR: …, en: …}`). Single source of truth; Pydantic validates all language variants side by side; adding a language later is trivial. — **Reversibility:** one-way — this is the schema shape research explicitly flagged as "retrofitting later is the expensive path": changing encoding means migrating the user's hand-maintained profile data plus every downstream consumer (loader, prompts, generation, preview).
- **D-02:** **What gets localized:** narrative fields (summary, experience descriptions, project descriptions, impacts) AND job titles (e.g., "Senior Software Engineer" / "Engenheiro de Software Sênior"). Company names, tech/skill names, dates, and contact info stay single-value (proper nouns, language-neutral). — **Reversibility:** costly — moving a field between localized-map and single-value changes schema, existing data, and every consumer of that field.
- **D-03:** **Fallback policy:** base + fallback — the schema requires exactly one declared base language per localized field; other languages optional; generation falls back to base text when the run's language is missing; never blocks the user. — **Reversibility:** costly — tied to D-01's map shape; re-keying base language means re-keying every map.
- **D-04:** **Declared base language: PT-BR** — the user writes real data naturally in PT-BR and adds EN translations over time.

### Profile file layout
- **D-05:** **Single `content/profile.md`** — one file to edit, commit, and validate. Markdown body stays minimal/unused.
- **D-06:** **All content lives in YAML frontmatter** — structured data AND bilingual narrative as localized maps; one parser, everything Pydantic-validated. — **Reversibility:** costly — restructuring means rewriting the loader, schema, and the user's file in one move.
- **D-07:** **Full resume section set in v1 schema:** contact, summary, experiences (with embedded impacts), education, skills, certifications, languages, projects — everything a Google-format resume needs, so no schema migration is needed when Phases 3–4 consume it.
- **D-08:** **Impacts embedded per experience** — each experience entry carries its own impacts array (action + metric + context). Grounding is natural: generation for a job sees exactly that job's impacts. — **Reversibility:** costly — extracting impacts into a separate section later restructures every entry and the prompt-slicing logic.
- **D-09:** **Skills as categorized groups** (linguagens, frameworks, ferramentas, cloud, …), each entry a plain tech name — maps naturally to keyword extraction (Phase 2) and the resume skills section.
- **D-10:** **Unknown keys are rejected loudly** (Pydantic `extra='forbid'`) — a typo like `experiance:` fails validation naming the exact key and location; a mistyped section can never silently vanish from generation.
- **D-11:** **Placeholder tracking via `example: true` flag in frontmatter** — the shipped file IS the example; the placeholder banner shows while the flag is set; the user removes the flag when real data is in. One file, one source of truth.

### Phase 1 UI scope
- **D-12:** **App shell + Perfil status home + rendered profile preview.** Shell has header and nav placeholders for the future modules. The Perfil home shows load status, validation errors in-app, section completeness at a glance, and the placeholder-data banner. Additionally, a preview renders the profile formatted like a resume page so the user sees their data the way the app sees it.
- **D-13:** **Validation errors surface in-app AND in the terminal.** A broken profile blocks the app; the UI shows the error in PT-BR; uvicorn logs keep the full raw Pydantic output.
- **D-14:** **Error style:** UI shows a PT-BR friendly message carrying the exact file/field path (e.g., "Erro no perfil: experiences[2].data_fim — data esperada, encontrado texto"); raw Pydantic detail lives in the terminal only.
- **D-15:** **No profile caching — validate on every load.** The backend re-reads and re-validates `content/profile.md` on every request; edit file → refresh browser → current. Fine at localhost scale; can never be stale.

### Example data persona
- **D-16:** The example persona mirrors the user's actual shape: **senior AI engineer focused on generative AI, also doing backend and frontend plus a bit of infra for those services.** Realistic (not cartoonish), demonstrably fake via the `example: true` banner.
- **D-17:** **Example data is fully bilingual** — every localized field carries both `{pt-BR, en}`, proving the schema end-to-end (ROADMAP SC4). The fallback path only fires once real data with gaps replaces it.

### Claude's Discretion
- Exact scaffold mechanics: package versions/pins per `.planning/research/STACK.md`, ESLint/Prettier flat config, ports, Vite proxy setup, FastAPI StaticFiles mounting order.
- Schema key naming language (English snake_case keys with bilingual values recommended — matches code conventions; example values in PT-BR/EN).
- Pydantic model file organization, loader module structure, test framework and fixtures for the validation path.
- UI implementation details (React Query setup, Tailwind styling, component breakdown) within the decided scope.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — constraints (JS frontend/Python backend, file-based store, localhost only), key decisions, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — PROFILE-01 (this phase's requirement) and the v1 requirement set the schema must eventually feed
- `.planning/ROADMAP.md` — Phase 1 goal + 5 success criteria (the acceptance bar)

### Research (pinned decisions and patterns)
- `.planning/research/STACK.md` — pinned stack + verified versions + install commands (Vite/React/TS, FastAPI/uvicorn/uv, python-frontmatter, Pydantic, python-dotenv, Tailwind, React Query, zod); profile store pattern; What-NOT-to-use table
- `.planning/research/ARCHITECTURE.md` — component architecture; Profile Loader fail-fast pattern; repo-as-content principle
- `.planning/research/PITFALLS.md` — Pitfall 6 (profile drift, localization retrofit) is this phase's core risk; loud validation is its mitigation
- `.planning/research/FEATURES.md` — dependency graph showing the profile as root of everything
- `.planning/research/SUMMARY.md` — consolidated implications, incl. "localization schema shape must be decided in Phase 1" (decided here, see D-01–D-04)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield repo. Only `.planning/` and `.claude/CLAUDE.md` exist. This phase defines the repo layout (frontend/, backend/, content/, .env) that everything else connects to.

### Established Patterns
- No established code patterns. Research-documented patterns to follow on first write: Vite dev proxy `/api` → FastAPI; FastAPI serves `frontend/dist` via StaticFiles (mounted after API routes) for daily use; python-frontmatter parse → `model_validate` → typed object, fail-fast with file/field errors.

### Integration Points
- `content/profile.md` is the contract every later phase consumes (loader → keyword engine → resume pipeline → PDF renderer).
- `.env` (gitignored before first commit) will hold `OPENROUTER_API_KEY` from Phase 2 onward.

</code_context>

<specifics>
## Specific Ideas

- Example persona described by the user, in their words: "Atualmente AI engineer com foco em IA generativa, e também backend e front além de um pouco de infra desses serviços" — seniority: Sênior. The persona should feel like a plausible version of the user, not a stranger.
- The user edits the profile by hand in their own editor — file ergonomics (clear structure, loud errors on typos) matter more than UI convenience.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Foundation — Scaffold + Master Profile*
*Context gathered: 2026-09-25*
