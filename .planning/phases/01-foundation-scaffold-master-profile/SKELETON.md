# Walking Skeleton — Career Tailor

**Phase:** 1
**Generated:** 2026-09-25

## Capability Proven End-to-End

> The user starts the app on localhost and sees a PT-BR interface that loads the git-versioned master profile through the backend validator and shows the placeholder-data banner — the one path every later generation module will walk.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Frontend framework | Vite 8 + React 19 + TypeScript ~5.9 (react-ts template) | User constraint "JavaScript frontend"; Vite dev proxy kills CORS friction; `tsc -b` in build catches Pydantic↔TS contract drift |
| Backend framework | FastAPI 0.141.1 + uvicorn 0.54.0, managed by uv on pinned Python 3.12 | Pydantic-native validation for the profile contract; `uv run uvicorn app.main:app --reload` is the whole dev backend story; Python matches user preference |
| Data layer | `content/profile.md` (YAML frontmatter) in git, parsed by python-frontmatter, validated by Pydantic v2 strict (`extra='forbid'`) — no database, git IS the store | File-based store is a project constraint; versioning/rollback come free from git |
| Localization shape | Localized maps: `dict[Literal["pt-BR","en"], str]`, base language `pt-BR` required (D-01…D-04) | One source of truth; retrofitting later is the expensive path — decided here, once |
| Auth | None — single-user localhost tool | Explicit project constraint (no hosting, no auth, no external DB) |
| Deployment target | Localhost only — FastAPI serves the built SPA via `StaticFiles(html=True)` mounted last; dev mode is two terminals (Vite :5173 proxy → FastAPI :8000) | One process for daily use after build; dev proxy during development |
| Secrets | `OPENROUTER_API_KEY` in gitignored root `.env`, read tolerantly (empty is fine in Phase 1) | Key must never be committed; Phase 1 never uses it (Phase 2 gateway will) |
| Directory layout | `frontend/` (Vite app), `backend/app/{profile,routes}` (FastAPI), `backend/tests/`, `content/` (git-versioned data), root `.env`/`.env.example` | Backend owns validation; frontend is a projection of `GET /api/profile` |

## Stack Touched in Phase 1

- [x] Project scaffold (Vite react-ts + Tailwind v4 + React Query; uv + FastAPI + Pydantic; pytest)
- [x] Routing — one real API route (`GET /api/profile`) + SPA mount at `/`
- [x] Data — one real read: `content/profile.md` parsed and schema-validated per request (write path intentionally none — profile is hand-edited in git)
- [x] UI — Perfil home wired to the API via React Query: status, placeholder banner, PT-BR error panel, completeness grid, resume-style preview
- [x] Local run — documented two-terminal dev flow and single-process build+serve flow

## Out of Scope (Deferred to Later Slices)

- Any LLM/OpenRouter call (Phase 2 gateway — Phase 1 only scaffolds the gitignored key)
- Resume generation, keyword extraction, coverage checklist (Phase 3)
- PDF export + ATS parse-back gate (Phase 4)
- Per-section regenerate / inline edit / fact diff (Phase 5)
- LinkedIn module, language QA gate, both-language fixture suite (Phase 6)
- PROFILE-02 completeness lint tied to a JD (Phase 3 — Phase 1's `completude` is section presence/counts only)
- Admin CRUD UI for the profile — files are edited in the user's editor (project constraint)
- Any database, auth, multi-user, or hosting surface (out of scope project-wide)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: One logged, schema-validated, bilingual OpenRouter gateway + editable meta-prompts + keyword engine
- Phase 3: Paste JD → grounded, keyword-targeted resume sections with coverage checklist and JD-tied completeness lint
- Phase 4: Single-column Google-format PDF export proven by the automated parse-back gate
- Phase 5: Review flow — per-section regenerate, inline editing, source-vs-generated fact diff
- Phase 6: LinkedIn module reusing the engine + bilingual hardening (glossary, QA gate, fixtures)
