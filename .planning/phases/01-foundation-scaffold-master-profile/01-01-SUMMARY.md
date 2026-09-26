---
phase: 01-foundation-scaffold-master-profile
plan: 01
subsystem: infra
tags: [vite, react, typescript, fastapi, uv, pydantic, python-frontmatter, tailwind, react-query, walking-skeleton]

# Dependency graph
requires:
  - phase: none
    provides: greenfield repo (only .planning/ artifacts existed)
provides:
  - Runnable full-stack skeleton: Vite+React+TS frontend, uv+FastAPI backend on pinned Python 3.12
  - Strict minimal profile schema slice (_Strict extra=forbid, LocalizedText maps, Experience/Impact/Profile with example flag)
  - Fail-fast load_profile() with ProfileError(message_ptbr, raw), no caching (D-15)
  - GET /api/profile status envelope (ok/erro) with raw detail terminal-only (D-13)
  - content/profile.md bilingual example persona with example: true (D-05/D-06/D-11/D-16/D-17)
  - PT-BR shell with header, nav placeholders, PlaceholderBanner via React Query v5
  - .gitignore-first repo hygiene + automated SC5 secrets test; documented dev + prod run modes
affects: [01-02 profile contract full schema, 01-03 Perfil UI, phase 2 LLM gateway (loader call sites)]

# Actuals (#2632)
actuals:
  tokens: 61862
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: [vite 8.3.1, react 19.3.0, typescript 5.9.3, @tanstack/react-query 5.103.2, tailwindcss 4.3.3, @tailwindcss/vite 4.3.3, fastapi 0.141.1, uvicorn 0.54.0, pydantic 2.13.5, python-frontmatter 1.3.0, python-dotenv 1.2.3, pytest 9.1.1, httpx 0.28.1, uv 0.12.5]
  patterns: [gitignore-first scaffold, uv virtual project (no build-system) on pinned 3.12, strict Pydantic slice with extra=forbid base, fail-fast loader raising ProfileError(message_ptbr, raw), status-envelope API (never 500), StaticFiles-mount-last, Vite proxy on 127.0.0.1 (host AND target), React Query v5 single-options useQuery, PT-BR strings constants module]

key-files:
  created:
    - .gitignore
    - .env.example
    - README.md
    - content/profile.md
    - backend/.python-version
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/app/config.py
    - backend/app/profile/models.py
    - backend/app/profile/loader.py
    - backend/app/routes/profile.py
    - backend/app/main.py
    - backend/tests/test_secrets.py
    - backend/tests/test_api.py
    - frontend/vite.config.ts
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/components/PlaceholderBanner.tsx
  modified:
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - frontend/src/index.css
    - frontend/index.html

key-decisions:
  - "uv project made virtual (no build-system/scripts table) — FastAPI app runs via uvicorn, not an installable package; uv build of src/backend otherwise fails (A2 fallback)"
  - "typescript pinned ~5.9 (5.9.3) — create-vite template now ships 6.0.3; plan + STACK.md pin advice require the 5.x line"
  - "Vite dev server host pinned to 127.0.0.1 — default 'localhost' bind resolved to ::1 on this machine, breaking the documented http://127.0.0.1:5173 URL"
  - "pytest pythonpath=[\".\"] — makes `import app.*` work from backend/ rootdir without packaging the app"
  - "git.allow_default_branch_commits=true — this repo's convention is GSD commits on master (branching_strategy: none); documented override applied"

patterns-established:
  - "Status envelope contract: GET /api/profile always answers 200 {status: ok|erro}; raw technical detail only in the uvicorn log (D-13)"
  - "Strict schema pattern: every profile model inherits _Strict (extra=forbid); LocalizedText = dict[Literal['pt-BR','en'], str]"
  - "Mount-last SPA serving: /api router included before the guarded FRONTEND_DIST StaticFiles mount"
  - "Dev proxy discipline: Vite host and proxy target both pinned to 127.0.0.1, never localhost"

requirements-completed: [PROFILE-01]

coverage:
  - id: D1
    description: ".env provably gitignored and untracked (SC5) — automated secrets test"
    requirement: PROFILE-01
    verification:
      - kind: unit
        ref: "backend/tests/test_secrets.py#test_env_is_gitignored"
        status: pass
      - kind: unit
        ref: "backend/tests/test_secrets.py#test_env_is_not_tracked"
        status: pass
    human_judgment: false
  - id: D2
    description: "GET /api/profile returns the ok envelope parsed fresh from content/profile.md (status ok, exemplo true, perfil object)"
    requirement: PROFILE-01
    verification:
      - kind: integration
        ref: "backend/tests/test_api.py#test_get_profile_returns_ok_envelope"
        status: pass
    human_judgment: false
  - id: D3
    description: "StaticFiles SPA mount serves index.html at / without swallowing /api routes (after npm run build)"
    requirement: PROFILE-01
    verification:
      - kind: integration
        ref: "backend/tests/test_api.py#test_get_serves_spa_index_html"
        status: pass
    human_judgment: false
  - id: D4
    description: "Backend runs on uv-pinned Python 3.12 with the full dependency set installed"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: cd backend && uv run python -V"
        status: pass
    human_judgment: false
  - id: D5
    description: "Frontend gate green: tsc -b && vite build with template + app code"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: cd frontend && npm run build"
        status: pass
    human_judgment: false
  - id: D6
    description: "Dev-mode loop: Vite (127.0.0.1:5173) proxies /api to the backend (127.0.0.1:8000) returning the status-ok envelope; dev root serves index.html; no stray servers"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: curl http://127.0.0.1:5173/api/profile (status ok) + curl root 200, servers killed after check"
        status: pass
    human_judgment: false
  - id: D7
    description: "PT-BR shell renders in a browser at localhost in both prod and dev modes: header, nav, banner on exemplo:true, error lines list on broken file"
    requirement: PROFILE-01
    verification: []
    human_judgment: true
    rationale: "Visual browser confirmation is human-observable evidence — deferred to the end-of-phase UAT per human_verify_mode: end-of-phase (plan <verify> human-checks are phase-UAT items)"

# Metrics
duration: 17 min
completed: 2026-09-25
status: complete
---

# Phase 1 Plan 01: Walking Skeleton Summary

**Full-stack skeleton proven end-to-end: bilingual content/profile.md → Pydantic strict validation → GET /api/profile status envelope → PT-BR React shell with placeholder-data banner, served in prod mode (StaticFiles) and dev mode (Vite proxy on 127.0.0.1)**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-25T23:49:30Z
- **Completed:** 2026-09-26T00:06:14Z
- **Tasks:** 3
- **Files modified:** 36 (3545 insertions)

## Accomplishments
- .gitignore-first repo hygiene (first content commit, before any install) with an automated SC5 proof: `.env` is gitignored and untracked
- uv backend pinned to Python 3.12.10 with fastapi/uvicorn/pydantic/python-frontmatter/python-dotenv + pytest/httpx; committed uv.lock; `uv run pytest` green (4 tests)
- Strict minimal profile slice: `_Strict(extra="forbid")` base, `LocalizedText` bilingual maps, `Experience`/`Impact`/`Profile` with the `example: bool` flag (D-01…D-11)
- Fail-fast `load_profile()` → `ProfileError(message_ptbr, raw)` with explicit UTF-8 and zero caching (D-15); `GET /api/profile` answers a 200 status envelope with raw detail terminal-only (D-13)
- `content/profile.md` ships a fully bilingual example persona (senior AI engineer, generative-AI focus) flagged `example: true`
- PT-BR shell (React Query v5 + Tailwind v4): header, nav placeholders (Currículo/LinkedIn), PlaceholderBanner while `exemplo: true`, error-lines list on broken profile
- Dev-mode loop proven with real processes: Vite 5173 proxies /api to the uvicorn 8000 backend through 127.0.0.1; both run modes documented in README.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Repo scaffold (gitignore-first, uv backend on 3.12, Vite frontend)** — `94c4821` + `ef506ef` (chore/feat)
2. **Task 2 (tracer): End-to-end perfil path** — `c1d9006` (feat)
3. **Task 3: Dev-mode loop verified (Vite host pin)** — `625ab39` (fix)

**Plan metadata:** committed with the docs commit (see below)

_Note: Task 1 spans two commits by design — `.gitignore` had to be the repo's first content commit before any install artifact existed (Pitfall 2)._

## Files Created/Modified
- `.gitignore` - repo-wide ignores (.env, node_modules/, dist/, .venv/, __pycache__/, outputs/) — first content commit
- `.env.example` - committed empty-value key template (`OPENROUTER_API_KEY=`); `.env` stays local
- `README.md` - both run modes (two-terminal dev on 5173/8000; single-process build on 8000) + profile-edit refresh note
- `content/profile.md` - bilingual example profile, all content in frontmatter, quoted dates, minimal body
- `backend/.python-version`, `backend/pyproject.toml`, `backend/uv.lock` - uv project pinned 3.12, pytest config (testpaths + pythonpath), locked deps
- `backend/app/config.py` - REPO_ROOT/CONTENT_DIR/FRONTEND_DIST paths, tolerant .env read (key empty/absent is fine)
- `backend/app/profile/models.py` - strict schema slice (extra=forbid everywhere, LocalizedText maps, date coercion)
- `backend/app/profile/loader.py` - fail-fast loader, ProfileError(message_ptbr, raw), no cache
- `backend/app/routes/profile.py` - GET /api/profile ok/erro envelope
- `backend/app/main.py` - API router first, guarded StaticFiles mount last
- `backend/tests/test_secrets.py`, `backend/tests/test_api.py` - SC5 secrets proof; ok-envelope + SPA-mount tests
- `frontend/vite.config.ts` - react + tailwindcss plugins; host + /api proxy pinned to 127.0.0.1
- `frontend/src/` (main.tsx, App.tsx, index.css, api/client.ts, constants/ui.ts, components/PlaceholderBanner.tsx) - PT-BR shell, React Query v5 wiring, typed discriminated-union client, banner
- `frontend/index.html` - lang="pt-BR", title Career Tailor

## Decisions Made
- uv project is virtual (no `[build-system]`/scripts) — the FastAPI app runs via uvicorn from backend/, it is not an installable package; uv otherwise fails building the template's src/backend layout (A2 fallback exercised)
- TypeScript pinned `~5.9` (5.9.3): the current create-vite template ships 6.0.3; plan and STACK.md pin advice require the 5.x line (npm `latest` 7.x is explicitly rejected)
- Vite dev server `host: '127.0.0.1'`: on this machine Vite 8's default localhost bind resolves to ::1 only, leaving the documented http://127.0.0.1:5173 unreachable — same IPv6/IPv4 class as proxy Pitfall 4
- pytest `pythonpath = ["."]` so `import app.*` resolves from backend/ without packaging the app
- Interim Pydantic error rendering in the loader (loc path + msg per line) — plan 02 replaces it with the full PT-BR mapper at the same call sites, per plan

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] uv add failed building the packaged template layout**
- **Found during:** Task 1 (backend scaffold)
- **Issue:** `uv init --app` wrote a build-system + scripts table; `uv add` then failed ("Expected a Python module at src\\backend\\__init__.py") after the stray src/ tree was removed
- **Fix:** Rewrote pyproject.toml as a minimal virtual `[project]` table (requires-python >=3.12, no build-system) — the documented A2 fallback
- **Files modified:** backend/pyproject.toml
- **Verification:** `uv add` runtime + dev deps succeeded; `uv run pytest` runs green
- **Committed in:** ef506ef

**2. [Rule 3 - Blocking] create-vite template shipped TypeScript 6.0.3**
- **Found during:** Task 1 (frontend scaffold)
- **Issue:** Template now pins `typescript: ~6.0.2` — plan acceptance requires a 5.x version (STACK.md: pin ~5.9, reject npm latest 7.x)
- **Fix:** `npm install -D typescript@~5.9` → 5.9.3
- **Files modified:** frontend/package.json, frontend/package-lock.json
- **Verification:** `npm ls typescript` = 5.9.3; `npm run build` (tsc -b && vite build) green
- **Committed in:** ef506ef

**3. [Rule 1 - Bug] pytest could not import `app.*` (ModuleNotFoundError)**
- **Found during:** Task 2 (tracer)
- **Issue:** backend/ rootdir not on sys.path when running `uv run pytest` (tests/ has no package parent)
- **Fix:** Added `pythonpath = ["."]` to `[tool.pytest.ini_options]`
- **Files modified:** backend/pyproject.toml
- **Verification:** `uv run pytest -q` → 4 passed
- **Committed in:** c1d9006

**4. [Rule 1 - Bug] Vite dev server unreachable at the documented http://127.0.0.1:5173**
- **Found during:** Task 3 (dev-mode check)
- **Issue:** Vite 8 default `localhost` host bound ::1 only on this machine (netstat: `[::1]:5173`); curl to 127.0.0.1:5173 refused — README's documented dev URL would fail for a fresh contributor
- **Fix:** `server.host: '127.0.0.1'` in vite.config.ts (file is in Task 3's file list); re-ran the full dev loop
- **Files modified:** frontend/vite.config.ts
- **Verification:** proxied `curl http://127.0.0.1:5173/api/profile` returns status-ok envelope; root 200; both PIDs killed, no stray servers
- **Committed in:** 625ab39

**5. [Rule 3 - Blocking] Commits blocked on protected default branch**
- **Found during:** Task 1 (first commit)
- **Issue:** gsd-tools reports `master` protected; without an override no plan commit is permitted, while this repo's entire GSD history is commits on master (`branching_strategy: none` — no-branching is the configured convention)
- **Fix:** Set `git.allow_default_branch_commits: true` in .planning/config.json — the guard's documented override
- **Files modified:** .planning/config.json
- **Verification:** gsd-tools branch check passes; all 4 task commits landed
- **Committed in:** with the docs/metadata commit

---

**Total deviations:** 5 auto-fixed (3 blocking, 2 bugs)
**Impact on plan:** All fixes unblocked planned work or made documented commands match reality; no scope creep. Install batch otherwise matches the 01-RESEARCH.md Package Legitimacy Audit exactly (react/react-dom 19.3.0, vite 8.3.1, @vitejs/plugin-react 6.1.1, @tanstack/react-query 5.103.2, tailwindcss + @tailwindcss/vite 4.3.3, fastapi 0.141.1, uvicorn 0.54.0, pydantic 2.13.5, python-frontmatter 1.3.0, python-dotenv 1.2.3, pytest 9.1.1, httpx 0.28.1).

## Issues Encountered
- Starlette TestClient emits an ecosystem deprecation warning (httpx → httpx2) on import — pre-existing upstream warning, tests pass; out of scope for this plan
- Git auto-configured the commit identity from the user's work account (guilhermino.araujo@groupsoftware.com.br); user may want a personal `git config user.email` for this repo

## Known Stubs
None blocking. Intentional, plan-scoped placeholders (documented, resolved by later plans in this phase):
- Nav items Currículo/LinkedIn render disabled — future-module placeholders by design (D-12; modules arrive in phases 3/6)
- Perfil completeness grid and resume-style preview deferred to plan 03 (D-12 scope split)
- Interim error rendering in loader.py — full PT-BR mapper lands in plan 02 (same call sites)

## User Setup Required

None - no external service configuration required. (.env is scaffolded locally with an empty OPENROUTER_API_KEY; Phase 1 never calls OpenRouter.)

## Next Phase Readiness
- Walking skeleton proven end-to-end; SKELETON.md architecture decisions all exercised (schema slice, loader, envelope route, mount-last, dev proxy)
- Ready for 01-02 (full strict schema + PT-BR error mapper + completude in the envelope) — the loader call sites and models architecture stay as established
- Phase UAT will cover the human checks: prod-mode browser smoke at 127.0.0.1:8000 (SC1) and the package-legitimacy spot-check batch

---
*Phase: 01-foundation-scaffold-master-profile*
*Completed: 2026-09-25*

## Self-Check: PASSED

All 21 key files exist on disk; all 4 commit hashes found in git log; plan-level verification re-run green (4 backend tests passed, frontend build green, .gitignore first content commit, .env never tracked).
