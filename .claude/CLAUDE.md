<!-- GSD:project-start source:PROJECT.md -->

## Project

**Career Tailor**

A personal, locally-run web app with two modules that generate job-search content in both English and Portuguese: (1) a resume builder that produces an ATS-optimized, personalized resume (Google-recommended single-column format, PDF export) from a pasted job description, and (2) a LinkedIn profile optimizer that rewrites headline, About section, experience descriptions, and skills based on a stated career objective. Both modules draw from a single master profile — the user's complete work history, projects, technologies, and impacts — stored as Markdown/YAML files in git. All content is generated via LLM calls (OpenRouter) driven by meta-prompts, with keyword optimization targeting the current tech job market.

**Core Value:** Paste a job description (or state a career objective for LinkedIn) and get polished, ATS-optimized, keyword-targeted output in English or Portuguese that the user would actually send or post — without manual rewriting from scratch.

### Constraints

- **Stack**: JavaScript frontend; Python acceptable for backend — matches user's comfort and preference.
- **LLM access**: all generation goes through OpenRouter; API key in local `.env` only.
- **Runtime**: local (localhost) only — no hosting, no auth, no external database.
- **Data store**: file-based (Markdown/YAML in git), not a database.
- **Languages**: all generated content available in both English and PT-BR.
- **Output format**: single-column ATS-friendly PDF in the Google-recommended style.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Vite | 8.3.1 | Frontend build tool + dev server with `/api` proxy | The default choice for "a JS frontend, no framework opinions." Instant HMR, zero config, and for a localhost tool you need none of Next.js's server machinery. Dev proxy to FastAPI removes CORS friction. (HIGH — registry) |
| React | 19.3.0 | UI for both modules (review flow, per-section regenerate, LinkedIn generator) | User constraint is "JavaScript frontend"; React has the deepest ecosystem and virtually every LLM-app UI example targets it. The review-edit-regenerate flow maps cleanly to controlled components + React Query. (HIGH — registry; framework choice MEDIUM) |
| TypeScript | ~5.9 (pin 5.x line; npm `latest` is 7.0.2) | Types shared across profile schema and LLM JSON contracts | Vite doesn't typecheck (esbuild strips types), so dev velocity is unaffected; `tsc --noEmit` catches contract drift between Pydantic and frontend. Stick to 5.x until typescript-eslint fully supports TS 7 (Go-native compiler, just became `latest`). (HIGH version fact / MEDIUM pin advice) |
| Python | 3.12.10 (already installed) | Backend runtime | PROJECT.md constraint: "Python acceptable — matches user's comfort and preference." For a personal tool the maintainer's fluency beats any technical tiebreaker. (HIGH — verified local install) |
| FastAPI | 0.141.1 | Local API server (routes: generate, regenerate-section, export-pdf, profile) | The de-facto standard for Python LLM services: async endpoints (LLM calls are I/O-bound), Pydantic-native request/response models, free interactive `/docs` for testing routes without touching the UI. (HIGH — registry) |
| uvicorn | 0.54.0 | ASGI server that runs FastAPI | Standard companion; `uv run uvicorn app.main:app --reload` is the whole dev backend story. (HIGH — registry) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai (PyPI) | 3.19.2 | OpenRouter client via `OpenAI(base_url="https://openrouter.ai/api/v1")` | All LLM calls. The OpenAI-compatible pattern is the most documented path, keeps you vendor-portable (swap `base_url` to point anywhere), and supports `response_format` passthrough. (HIGH — official OpenRouter docs) |
| playwright (PyPI) | 1.63.0 | PDF export: render the resume HTML template in headless Chromium, `page.pdf(...)` | PDF export. First-party Microsoft package; produces a real embedded-text layer (text-selectable, ATS-parseable) with pixel parity between the in-app preview and the exported file. Run `playwright install chromium` once. (HIGH — official docs) |
| python-frontmatter | 1.3.0 | Parse `profile.md`: YAML frontmatter (structured data) + Markdown body (narrative) | Profile loading at startup and on reload. Exactly the "Markdown/YAML in git" model in PROJECT.md. (HIGH — registry) |
| pydantic | 2.13.5 | Schema validation for master profile AND LLM JSON output | Validate the profile against a strict schema with readable error messages (file/field level); re-validate every LLM response — never trust model output conformance, even with structured outputs (OpenRouter docs: enforcement varies by provider). (HIGH — registry) |
| PyYAML | 6.0.3 | Pure-YAML files (e.g., keyword lists, language variants) | If profile splits into `.yaml` sidecar files (e.g., `keywords.pt-BR.yaml`). Already a python-frontmatter dependency. (HIGH — registry) |
| python-dotenv | 1.2.3 | Load `OPENROUTER_API_KEY` from local `.env` | Meets the "API key in local `.env` only" constraint; add `.env` to `.gitignore` before first commit. (HIGH — registry) |
| @tanstack/react-query | 5.103.2 | Server-state for generation calls (loading, error, per-section regenerate/refetch) | The review flow is dominated by "call LLM, show result, regenerate one section" — React Query models exactly this mutation/refetch cycle. (HIGH — registry) |
| zod | 4.6.5 | Frontend validation of LLM JSON before rendering | Defense-in-depth: backend validates with Pydantic, frontend re-checks shape before rendering sections. `import { z } from "zod"` is the v4 API in 4.x. (HIGH — registry) |
| tailwindcss + @tailwindcss/vite | 4.3.3 | Styling, including print CSS via variants | Tailwind v4's Vite plugin is the official integration; print-specific utilities (`print:` variants) keep resume styling next to screen styling. UI language is PT-BR — hardcode strings in a constants module, no i18n framework needed for one user. (HIGH — registry) |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | 0.12.19 — Python env + dependency management | The 2025/2026 standard; replaces pip/venv/pip-tools dance. `uv add <pkg>`, `uv run` — no manual venv activation. (HIGH — registry) |
| `npm create vite` | Frontend scaffold | `--template react-ts` |
| Playwright browser install | One-time Chromium download for PDF rendering | `uv run playwright install chromium` (~150–300 MB, one-time, cached) |
| ESLint (flat config) + Prettier | Lint/format | Use current `eslint@9` flat config from the Vite template; no extra plugins needed |
| Acceptance check: PDF text extraction | Verify ATS-parseability | After export, `pdftotext` (or plain copy-paste from a PDF viewer) must yield clean text in correct reading order — make this an automated smoke test |

## Installation

# Frontend (from repo root)

# devDependencies from template: typescript, vite, @vitejs/plugin-react, eslint

# Backend

# .env (gitignored, repo root)

# OPENROUTER_API_KEY=sk-or-...

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| FastAPI backend | Express 5.2.1 (Node) | If the user later prefers a single language/runtime for everything. Full Node variant exists (see Patterns by Variant) — express 5.2.1 + gray-matter 4.0.3 + zod + playwright npm 1.63.0. Not chosen: stated Python preference wins for a personal tool. |
| openai SDK + `base_url` | Official OpenRouter SDKs: `openrouter` (PyPI 1.2.28, "stable as of v1.0") / `@openrouter/sdk` (npm 1.3.29, has `./react-query` integration) | If you want first-class typed access to OpenRouter-specific features (credit tracking, analytics, provider routing preferences) or follow OpenRouter docs' "prefer official SDKs" guidance. Both are official and stable; the OpenAI-compatible route just has vastly more community examples and keeps you portable. |
| Playwright HTML→PDF | @react-pdf/renderer 4.9.0 | If the Chromium download is unacceptable. Pure-JS, deterministic Yoga-flexbox layout, real text layer, renders in Node or browser. Cost: a second layout implementation that can drift from the HTML review preview, plus manual font file management. |
| Playwright HTML→PDF | Typst 0.15.1 (Jul 2026) | Best-in-class typography from a tiny binary; great if you enjoy learning its markup language. Cost: non-JS/Python toolchain, and preview-in-app parity needs extra work. Overkill for a single-column Google-format resume. |
| Vite + React | SvelteKit | If the user prefers compiler-minimal JS with less boilerplate. Perfectly capable for this app; smaller ecosystem and fewer LLM-app examples. |
| python-frontmatter + Pydantic | gray-matter + zod (Node) | Only in the Express variant. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Next.js | SSR, file routing, server components, and Vercel deploy assumptions are dead weight for a localhost personal tool; heavier dev loop, more concepts to maintain | Vite + React |
| wkhtmltopdf, html-pdf, html-pdf-node | Abandoned/deprecated (ancient QtWebKit), poor modern CSS support, unreliable text extraction | Playwright `page.pdf()` |
| Image/Canvas-based PDFs (jsPDF from canvas, screenshot-to-PDF) | **No text layer at all — ATS parsers read nothing. Fatal for the core requirement.** | Any text-embedding approach (Playwright or @react-pdf/renderer) |
| Client-side-only PDF libraries (jsPDF, pdfmake in the browser) | Coordinate-based manual layout, no real CSS, painful pagination — you'd rebuild a layout engine | Server-side Playwright render of the same HTML |
| pdf-lib (as the primary generator) | Excellent low-level PDF surgery library, but you'd hand-place every text line in a multi-section flowing document | pdf-lib only for post-processing (merge/stamp), never layout |
| LaTeX toolchain | Heavy Windows install, slow iteration cycle, massive overkill for single-column resumes | HTML/CSS + Playwright |
| LangChain / LlamaIndex / prompt-frameworks | The app has ~2–4 call sites driven by meta-prompts. Framework abstraction hides the exact prompts you're iterating on and adds dependency churn — pure overhead at this scale | Direct openai-SDK calls + your own `prompts/` module |
| Any database (SQLite included) | Violates the file-based constraint; git IS the store with history/rollback for free | `profile.md` in git |
| axios | Native `fetch` is standard in both modern browsers and the backend via the SDKs; axios adds nothing here | fetch / React Query |
| react-i18next or i18n frameworks | One user, one UI language (PT-BR); generated-content language is a generation parameter, not a UI-i18n problem | Constants module + `language: "pt-BR" \| "en"` in generation requests |
| DOCX generators (docx, python-docx) | Explicitly out of scope in PROJECT.md | PDF only |

## Stack Patterns by Variant

- Express 5.2.1 + gray-matter 4.0.3 + zod 4.6.5 + playwright (npm) 1.63.0, frontend served by the same process
- Because: single runtime, single process even in dev; trades away the stated Python preference
- @react-pdf/renderer 4.9.0: author a `<ResumeDocument>` React component as the single source of truth; embed it BOTH in the web preview (react-pdf's built-in viewer) and in `renderToBuffer()` for export
- Because: pure JS, no browser binary. Acceptance check stays the same: pdftotext must extract clean text
- Typst 0.15.1 as a template engine: backend fills a `.typ` template with profile data, runs `typst compile`
- Because: superior justification, kerning, and page-break control; accept the extra language
- Always re-validate `resp.choices[0].message.content` with Pydantic — OpenRouter docs explicitly warn schema enforcement varies by provider even with `strict: true`
- Language selection (EN vs PT-BR) is a parameter inside the meta-prompt, never a separate translation pass
- Keep model slugs (e.g., an OpenRouter "latest" alias) in a config file so model swaps need no code change — this is the point of OpenRouter
- One `profile.md`: YAML frontmatter for structured fields (contact, skills, languages, projects) + Markdown body for narrative (summary, experience entries as `##` sections)
- Optional per-language fields (`summary_en` / `summary_pt`) with fallback, so both output languages draw from one source
- Validate at startup and on manual reload; surface Pydantic errors with file path + field name before any generation runs

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Vite 8.3.1 | Node ≥ 20.19 / ≥ 22.12 | Local machine has Node v22.16.0 — OK (verified) |
| @vitejs/plugin-react 6.1.1 | Vite 8, React 19.3 | Use the plugin (not `@vitejs/plugin-react-swc`) unless build speed becomes a problem |
| FastAPI 0.141.1 | Python 3.12.10 (installed), pydantic 2.13.5 | No known conflicts; all pure-Python wheels on Windows |
| playwright PyPI 1.63.0 | playwright npm 1.63.0 | Same version line; both use the shared browser cache (`%LOCALAPPDATA%\ms-playwright` on Windows), so one `install chromium` serves either driver (cache-dir claim: MEDIUM) |
| openai PyPI 3.19.2 | OpenRouter `/api/v1` | OpenAI-compatible endpoint is a first-class, doc-verified OpenRouter feature |
| zod 4.6.5 | TS 5.x | `import { z } from "zod"` IS the v4 API; ignore older tutorials mentioning the `zod/v4` subpath (that was the 3.25+ migration bridge) |
| TypeScript | npm `latest` = 7.0.2 (Go-native compiler) | Vite never typechecks, so dev is unaffected; pin `typescript@~5.9` until typescript-eslint and lint tooling officially support TS 7 |
| @react-pdf/renderer 4.9.0 | React 19 (variant only) | Current major supports modern React; verify peer deps if adopting the no-Chromium variant (MEDIUM) |

## Sources

- npm registry `/latest` + dist-tags endpoints (fetched 2026-09-25): react 19.3.0, vite 8.3.1, @vitejs/plugin-react 6.1.1, typescript (latest 7.0.2), tailwindcss 4.3.3, @tailwindcss/vite 4.3.3, @tanstack/react-query 5.103.2, zod 4.6.5, gray-matter 4.0.3, express 5.2.1, playwright 1.63.0, @react-pdf/renderer 4.9.0, pdf-lib 1.17.1, yaml 2.9.1, js-yaml 5.4.2, openai 7.23.0, @openrouter/sdk 1.3.29 — HIGH (authoritative registry)
- PyPI JSON API (fetched 2026-09-25): fastapi 0.141.1, uvicorn 0.54.0, pydantic 2.13.5, playwright 1.63.0, python-frontmatter 1.3.0, PyYAML 6.0.3, python-dotenv 1.2.3, uv 0.12.19, openai 3.19.2, openrouter 1.2.28 — HIGH
- https://openrouter.ai/docs/quickstart — OpenAI SDK `baseURL`/`base_url` patterns for JS and Python, official SDK examples (`@openrouter/sdk`, `pip install openrouter`), attribution headers — HIGH (official vendor docs)
- https://openrouter.ai/docs/guides/features/structured-outputs — `response_format: json_schema`, `strict: true`, `require_parameters` provider preference, per-provider enforcement caveat, Response Healing — HIGH (official)
- https://playwright.dev/docs/api/class-page — `page.pdf()` options (format, margin, printBackground, preferCSSPageSize, scale, tagged, outline), print-media CSS default — HIGH (official). Note: current docs no longer explicitly state engine restrictions for `page.pdf()`; treat "Chromium-only" as MEDIUM confidence (moot here — we always launch bundled Chromium)
- https://react-pdf.org/ — renderer capabilities (Yoga layout, Node/browser render, fonts, hyphenation, page-break control) — HIGH (official landing page; detailed API claims MEDIUM)
- https://api.github.com/repos/typst/typst/releases/latest — Typst 0.15.1 (2026-07-17) — HIGH
- Local environment verification: Node v22.16.0, Python 3.12.10 installed — HIGH
- Caveat: WebSearch was rate-limited during this session, so *community-consensus* claims (e.g., "Vite+React is the default for small tools") rest on registry evidence plus prior knowledge — MEDIUM by itself; all version and integration claims above are independently HIGH

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
