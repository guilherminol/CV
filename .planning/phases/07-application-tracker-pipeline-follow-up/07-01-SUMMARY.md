---
phase: 07-application-tracker-pipeline-follow-up
plan: 01
subsystem: tracker
tags: [sqlite, fastapi, pydantic, react-query, dnd-kit, migrations]

# Dependency graph
requires:
  - phase: 06-linkedin-module-bilingual-hardening
    provides: house route posture (sync def, 200 envelope, extra=forbid, router-before-mount), test patterns (_iter_api_routes, caplog raw-only), working-tree Phase 6 source baselines
provides:
  - tracker persistence layer — conectar() connection factory + PRAGMA user_version migration runner + MIGRATIONS v1 (3 tables + 5 seed stages) + TRACKER_APPLICATION_ID pin
  - all 8 tracker request DTOs, Wave-0 drift-locked (extra=forbid, bounded fields, five event-type literals)
  - criar_candidatura + obter_resumo service (D-07 event-derived contadores, D-09 prazo ordering, server-computed derived fields, injectable hoje)
  - GET /api/tracker/resumo + POST /api/tracker/candidaturas routes (200 envelope, connection-per-request yield dependency with auto-migration)
  - Rastreador fifth nav view (TrackerHome skeleton: query/contadores/list/create form) + trackerPrefill D-13 seam state in App
  - typed client mirror (CandidaturaDTO/EventoDTO/EstagioDTO + TrackerResumoResponse + fetchTrackerResumo/criarCandidatura)
  - Wave-0 test suites test_tracker_db.py (9) + test_tracker_api.py (9) — runnable verification targets for every later plan
affects: [07-02, 07-03, 07-04, 07-05]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 12840
  tasks: 3
  commits: 5

# Tech tracking
tech-stack:
  added: ["@dnd-kit/core@^6.3.1", "@dnd-kit/sortable@^10.0.0", "@dnd-kit/utilities@^3.2.2 (the single D-14 exception; legitimacy audit all OK)"]
  patterns:
    - "Connection-per-request yield dependency with auto-migration (FastAPI docs pattern; sync-def threadpool-safe SQLite)"
    - "PRAGMA user_version migration runner — one transaction per migration, idempotent by construction"
    - "Service raises untouched; route owns the erro envelope (raw to logger, PT-BR to user)"
    - "Pure projection derived fields with injectable hoje (pytest-pinnable date arithmetic)"
    - "First persistent view: queryClient.invalidateQueries(['tracker']) after every successful mutation"

key-files:
  created:
    - backend/app/tracker/__init__.py
    - backend/app/tracker/db.py
    - backend/app/tracker/models.py
    - backend/app/tracker/service.py
    - backend/app/routes/tracker.py
    - backend/tests/test_tracker_db.py
    - backend/tests/test_tracker_api.py
    - frontend/src/pages/TrackerHome.tsx
  modified:
    - backend/app/config.py
    - backend/app/main.py
    - .gitignore
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/App.tsx

key-decisions:
  - "A2 pinned: archive is the candidaturas.arquivada flag (+ arquivada_em), NOT a final stage — a flag survives user-edited stage vocabularies (D-05)"
  - "A3 pinned: follow-up pending is data-inferred (followup event with future date) — NO executada column; eventos DDL is final"
  - "estagio_id optional on create with server-side default to FIRST stage by ordem — never hardcode a seed id at call sites (D-05-safe minimal UI contract)"
  - "TRACKER_FOLLOWUP_SUGGEST_DAYS pinned at 7 (D-12 discretion area closed); TRACKER_DB env-overridable for the homelab bind mount (D-02)"

patterns-established:
  - "Tracker request DTOs live in ONE module imported by routes AND service — the wire shape cannot drift (linkedin/models.py precedent)"
  - "POST response carries the SAME projected shape as the resumo rows (one CandidaturaDTO wire contract)"
  - "Wave-0 DTO drift lock: all request DTOs pinned before the route stages that consume them exist (06-01 precedent)"

requirements-completed: [TRK-01, TRK-02, TRK-04]

# Coverage metadata (#1602) — one entry per shipped deliverable. Drives DETERMINISTIC UAT routing in verify-work.
coverage:
  - id: D1
    description: "SQLite persistence layer: fresh TRACKER_DB auto-migrates to schema v1 (3 tables + 5 seed stages) idempotently; FK pragma on; application_id stamped; env override honored"
    requirement: TRK-01
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_db.py::test_migracao_fresh_db_user_version_1"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_db.py::test_schema_v1_tem_exatamente_tres_tabelas"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_db.py::test_migracao_idempotente"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_db.py::test_config_env_override_cria_diretorio_pai"
        status: pass
    human_judgment: false
  - id: D2
    description: "All 8 Wave-0 request DTOs strict (extra=forbid) with bounded fields, Literal modalidade/event-tipo, ISO date patterns"
    requirement: TRK-04
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_422_chave_desconhecida_no_body"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_422_empresa_acima_do_limite"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_422_data_fora_do_padrao_iso"
        status: pass
    human_judgment: false
  - id: D3
    description: "GET /api/tracker/resumo + POST /api/tracker/candidaturas — house 200 envelope, event-derived contadores, router before SPA mount, sync handlers, no destructive route"
    requirement: TRK-04
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_resumo_zero_state_fresh_db"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_criar_candidatura_roundtrip"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_router_registered_before_spa_mount"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_handlers_are_sync_def_never_coroutines"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_rotas_tracker_nao_tem_caminho_destrutivo"
        status: pass
    human_judgment: false
  - id: D4
    description: "Rastreador fifth nav view: create a candidatura through the UI form and the row survives a page reload (first persistent state)"
    requirement: TRK-02
    verification:
      - kind: automated_ui
        ref: "cd frontend && npm run build (tsc -b + vite green — compiles the full view chain)"
        status: pass
    human_judgment: true
    rationale: "The plan's own verification marks this check Manual: UI create + reload persistence needs a browser session with the backend running; the automated layer proves compilation and the API roundtrip (test_criar_candidatura_roundtrip) but not the rendered UX. Re-surfaces via /gsd-verify-work."
  - id: D5
    description: "Typed client mirror + nav item: NAV_ITEMS fifth entry, view union, DTO interfaces under the drift-gate banner; no existing label touched (D-16)"
    requirement: TRK-02
    verification:
      - kind: automated_ui
        ref: "cd frontend && npm run build (tsc -b fails on union/drift mismatch — green = mirrors in sync)"
        status: pass
      - kind: other
        ref: "git diff check: zero removed lines in constants/ui.ts (existing labels byte-identical)"
        status: pass
    human_judgment: false
  - id: D6
    description: "@dnd-kit install (D-14 single exception) — exactly 3 packages added, no other new dependency"
    requirement: TRK-02
    verification:
      - kind: other
        ref: "package.json dependencies diff vs pre-phase state: only @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities added"
        status: pass
    human_judgment: false

# Metrics
duration: 16min
completed: 2026-11-10
status: complete
---

# Phase 7 Plan 1: Tracer — Persistence-to-UI Deterministic Path Summary

**End-to-end tracer path proven: UI form → POST /api/tracker/candidaturas → SQLite (v1 migrations + seed) → GET /api/tracker/resumo → Rastreador view rendering contadores + candidaturas — the app's first persistent state.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-11-10T22:38:46Z
- **Completed:** 2026-11-10T22:55:26Z
- **Tasks:** 3 (1 tracer + 2 auto)
- **Files modified:** 16

## Accomplishments
- First SQLite module in the project: connection-per-request factory, idempotent PRAGMA user_version migrations (v1: estagios/candidaturas/eventos + 5 seed stages), application_id pin — fully offline-testable
- House contracts hold from day one: 200 envelope, extra=forbid 422s, sync def handlers, router before the SPA mount, parameterized-only SQL (T-07-01), no destructive route (D-04)
- Rastreador live as the fifth nav view (D-16, existing labels byte-untouched); create-candidatura persists and the ['tracker'] query cache invalidates (Pitfall 6)
- @dnd-kit installed as the single D-14 exception; tsc -b green — research Assumption A1 (React 19 + dnd-kit typings via skipLibCheck) empirically settled

## Task Commits

Each task was committed atomically (plus the plan's two baseline chore commits):

1. **Task 1: Tracer persistence layer** - `2c57bbc` (feat)
2. **Task 2: Tracer service + routes** - `228ef9a` (feat)
3. **Task 3: Tracer frontend** - `012f814` (feat)

**Baseline chores (per plan revision note 2):** `31c1afe` (chore: pending main.py Phase 6 content), `45f76f7` (chore: pending App.tsx Phase 6 content)

**Plan metadata:** pending (docs commit follows)

## Files Created/Modified
- `backend/app/tracker/db.py` - connection factory + PRAGMA user_version migrations v1 + seed (D-02 path via config)
- `backend/app/tracker/models.py` - all 8 Wave-0 request DTOs, extra=forbid, bounded (JD 20000, notas 5000, observacao 2000)
- `backend/app/tracker/service.py` - criar_candidatura + obter_resumo (D-07 contadores from events, D-09 ordering, derived fields, injectable hoje)
- `backend/app/routes/tracker.py` - resumo/create routes, yield dependency with auto-migration, house envelope
- `backend/app/main.py` - tracker router registered BEFORE the SPA mount
- `backend/app/config.py` - TRACKER_DB (env-overridable, parent auto-created) + TRACKER_FOLLOWUP_SUGGEST_DAYS=7 (D-12)
- `backend/tests/test_tracker_db.py` - 9 offline tests: migrations/seed/idempotency/FK/env override
- `backend/tests/test_tracker_api.py` - 9 offline tests: router order, sync pin, zero state, roundtrip, 422 vectors, erro-envelope caplog pin, no-DELETE pin
- `frontend/src/api/client.ts` - tracker DTO mirrors + fetchTrackerResumo/criarCandidatura under the drift-gate banner
- `frontend/src/constants/ui.ts` - NAV_ITEMS fifth entry + RASTREADOR_* PT-BR strings
- `frontend/src/App.tsx` - view union 'rastreador' + trackerPrefill D-13 seam + render branch
- `frontend/src/pages/TrackerHome.tsx` - fifth view: query/isPending/erro/ok branches, contadores, list, minimal create form
- `frontend/package.json` / `package-lock.json` - @dnd-kit family (only new deps)
- `.gitignore` - `data/` entry (D-01/D-02)
- `.planning/PROJECT.md` - D-01 reversal row ALREADY recorded at planning (verified present, no edit needed)

## Decisions Made
- Archive pinned as the `arquivada` flag (+ arquivada_em), not a final stage (A2 — survives user-edited stage vocabularies)
- Follow-up pending pinned as data-inferred (future-dated followup event), no executada column (A3)
- `estagio_id` optional on create; None resolves server-side to the FIRST stage by ordem (see Deviations #1)
- Follow-up suggestion threshold pinned at 7 days (D-12); TRACKER_DB env-overridable (D-02)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] estagio_id made optional with server-side default-stage resolution**
- **Found during:** Task 1 (models.py), implemented in Task 2 (service.py)
- **Issue:** The plan listed `estagio_id int` (required) on CandidaturaCriacaoRequest, but the pinned minimal create UI (Task 3: empresa + cargo only) cannot supply a stage id without hardcoding seed id 1 at the call site — which breaks under D-05 stage customization (a deleted first stage would fail every create).
- **Fix:** `estagio_id: int | None = None`; service `_resolver_estagio` falls back to `SELECT id FROM estagios ORDER BY ordem LIMIT 1` and raises a loud TrackerErro when the stage table is empty or the explicit id is unknown.
- **Files modified:** backend/app/tracker/models.py, backend/app/tracker/service.py
- **Verification:** test_criar_candidatura_roundtrip asserts estagio_nome "Pesquisando"; test_erro_envelope_estagio_desconhecido pins the loud unknown-id path
- **Committed in:** 2c57bbc + 228ef9a

**2. [Rule 1 - Bug] POST response shape diverged from the CandidaturaDTO wire contract**
- **Found during:** Task 2 verification (test_criar_candidatura_roundtrip KeyError 'estagio_nome')
- **Issue:** criar_candidatura returned the raw row dict — no estagio_nome, no derived fields — while the typed client mirror types the create response as CandidaturaDTO.
- **Fix:** criar_candidatura now runs the same `_derivados` projection as obter_resumo (one wire shape for both paths)
- **Files modified:** backend/app/tracker/service.py
- **Verification:** test_criar_candidatura_roundtrip passes (derived fields + estagio_nome present)
- **Committed in:** 228ef9a

**3. [Rule 1 - Bug] Destructive-route test read `.methods` off the endpoint function**
- **Found during:** Task 2 verification (AttributeError: 'function' object has no attribute 'methods')
- **Issue:** HTTP methods live on the APIRoute object, not the endpoint callable.
- **Fix:** added `_rotas_api()` helper yielding APIRoute objects (same nested-_IncludedRouter handling); test uses `rota.methods`
- **Files modified:** backend/tests/test_tracker_api.py
- **Verification:** test_rotas_tracker_nao_tem_caminho_destrutivo passes
- **Committed in:** 228ef9a

**4. [Rule 1 - Bug] db.py docstring carried the literal forbidden token failing the plan's negative-grep acceptance criterion**
- **Found during:** Task 1 acceptance gate (grep -c check_same_thread = 1)
- **Issue:** The acceptance criterion requires the literal absent from backend/app/tracker/db.py; the docstring's threading note quoted it (the planner's discipline pass explicitly keeps negative-grep literals out of bodies).
- **Fix:** reworded to "SQLite's same-thread restriction is never relaxed anywhere in this module" — grep now returns 0
- **Files modified:** backend/app/tracker/db.py
- **Verification:** grep -c returns 0; suite still 9 passed
- **Committed in:** 2c57bbc

**5. [Rule 3 - Blocking] Missing RASTREADOR_CONTADORES_LABELS import failed the first build**
- **Found during:** Task 3 verification (tsc TS2304)
- **Fix:** added the constant to TrackerHome's imports; build green
- **Files modified:** frontend/src/pages/TrackerHome.tsx
- **Verification:** npm run build exits 0
- **Committed in:** 012f814

---

**Total deviations:** 5 auto-fixed (3 Rule 1 bugs, 1 Rule 2 missing-critical, 1 Rule 3 blocking)
**Impact on plan:** None negative — all five were within-task corrections; every acceptance criterion passes and the full suite is green (461 passed, 9 deselected llm-marker).

### Notes (not deviations)
- `.planning/PROJECT.md` was listed in files_modified for the D-01 reversal row, but the row already exists (recorded during phase planning, committed pre-execution) — verified present instead of re-appended.
- The working tree carried additional pending Phase 6 modifications beyond the plan's three named files (llm/gateway.py, resume/lint.py, routes/profile.py, tests, content/profile.md, prompts, components). Out of scope — untouched per the scope boundary; the baseline gate applied ONLY to files this plan edits (main.py in Task 2, App.tsx in Task 3), exactly per the plan's revision note.

## Issues Encountered
None beyond the auto-fixed deviations above. Tracer feedback gate passed post-commit (9/9 db tests re-run green before expansion).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 07-02 (CRUD + service tests + export) can consume the pinned DTOs, TrackerErro, _derivados projection, and both Wave-0 test suites as runnable targets
- 07-03 replaces TrackerHome's minimal form with CandidaturaForm (same mutation, same query key — the seam is prepared) and builds the kanban on the installed @dnd-kit
- 07-04 wires the "Registrar candidatura" button: trackerPrefill state + prop path already exist in App/TrackerHome
- Blockers: none. OpenRouter credits (Phase 6 blocker) do not affect this deterministic module (D-15)

---
*Phase: 07-application-tracker-pipeline-follow-up*
*Completed: 2026-11-10*
