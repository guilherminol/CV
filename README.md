# Career Tailor

Personal, locally-run web app that generates job-search content (resume + LinkedIn) in PT-BR and English from a git-versioned master profile. See `.planning/PROJECT.md` for the full project definition.

## Repository layout

```
content/    Master profile (content/profile.md) — YAML frontmatter + minimal Markdown body
backend/    FastAPI app (uv + Python 3.12) — API routes + serves the built SPA
frontend/   Vite + React + TypeScript SPA (Tailwind v4, React Query)
.env        Local secrets (gitignored) — OPENROUTER_API_KEY lives here, never in git
```

## Running the app

### Daily use — single process (build once, then serve)

```bash
# 1. Build the frontend (once, and after any frontend change)
cd frontend && npm run build

# 2. Serve backend + built SPA in one process
cd backend && uv run uvicorn app.main:app
```

Open **http://127.0.0.1:8000** — the PT-BR interface is served by FastAPI (StaticFiles mount of `frontend/dist`).

### Development — two terminals with HMR

```bash
# Terminal 1 — backend API on port 8000
cd backend && uv run uvicorn app.main:app --reload

# Terminal 2 — Vite dev server on port 5173 (proxies /api to 127.0.0.1:8000)
cd frontend && npm run dev
```

Open **http://127.0.0.1:5173**.

### Editing the profile

Edit `content/profile.md` in your own editor and **refresh the browser** — the backend re-reads and re-validates the file on every request (no restart, no cache). A broken file surfaces as a loud PT-BR error naming the exact file and field, both in the UI and in the uvicorn terminal.

## Secrets

`OPENROUTER_API_KEY` lives only in the gitignored root `.env` (scaffolded empty — Phase 1 never calls OpenRouter). Copy `.env.example` if you need to recreate it. `.env` is never committed; `backend/tests/test_secrets.py` enforces this automatically.

## Tests

```bash
cd backend && uv run pytest -q        # backend suite (secrets + API + loader)
cd frontend && npm run build          # frontend gate: tsc -b && vite build
```

## Toolchain

- [uv](https://docs.astral.sh/uv/) 0.12.x — Python env + deps (pinned to Python 3.12 via `backend/.python-version`)
- Node 22.12+ / npm 10.x — frontend
