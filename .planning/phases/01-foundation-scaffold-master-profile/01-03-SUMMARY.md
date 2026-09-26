---
phase: 01-foundation-scaffold-master-profile
plan: 03
subsystem: frontend/perfil-ui
tags: [react, typescript, react-query-v5, tailwind, discriminated-union, pt-br, error-ux, completude, resume-preview]

# Dependency graph
requires:
  - phase: 01-foundation-scaffold-master-profile
    provides: plan-02 finalized GET /api/profile contract (perfil dump + completude + PT-BR erros lines) and plan-01 tracer shell (QueryClientProvider, header/nav, PlaceholderBanner)
provides:
  - Finalized typed client contract (PerfilDTO/CompletudeDTO + ok/erro discriminated union) in frontend/src/api/client.ts
  - ErrorPanel rendering backend erros[] lines verbatim — the UI never parses, maps, or translates errors (D-13/D-14)
  - CompletenessGrid: section presence/counts at a glance from the completude DTO, empty-optional sections neutral (D-12)
  - ProfilePreview: resume-style render of every D-07 section, pt-BR base values from localized maps (D-04), text children only (T-01-08)
  - Full PT-BR string set in constants/ui.ts (status labels, error hint, completude labels, preview headings) — no i18n framework
  - App.tsx Perfil home three-state render (isPending / erro / ok) with load-status line (D-12)
  - Finalized README: dev + prod flows, edit-refresh behavior, error surfacing, Phase 1 smoke check
affects: [phase 3 resume builder (consumes PerfilDTO shape), phase 4 print template (builds on the preview's visual order), phase UAT (SC1/SC3 browser smoke)]

# Actuals (#2632)
actuals:
  tokens: 6180        # chars/4 over the realized diff (24,720 bytes, 8 files, +498/−29)
  tasks: 2
  commits: 2          # MEASURED: git rev-list --count 6862663..HEAD
plan_head_before: 68626634acd0655fdbeef20561b5146169915336

# Tech tracking
tech-stack:
  added: []
  patterns: [typed discriminated union mirroring the Pydantic dump (tsc -b as drift gate), verbatim-error rendering panel (UI never maps errors, D-13/D-14), present-vs-neutral completeness states, localized display helper picking the pt-BR base value, three-state useQuery render (isPending/erro/ok), placeholder banner as pure status with no control]

key-files:
  created:
    - frontend/src/components/ErrorPanel.tsx
    - frontend/src/components/CompletenessGrid.tsx
    - frontend/src/components/ProfilePreview.tsx
  modified:
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/components/PlaceholderBanner.tsx
    - frontend/src/App.tsx
    - README.md

key-decisions:
  - "Client types mirror the full Pydantic dump including the example flag and None-able optionals (string | null); tsc -b in npm run build is the standing Pydantic↔TS drift gate (STACK.md)"
  - "ErrorPanel is dumb by design: erros[] lines render verbatim as JSX text children — zero parsing, mapping, or translation in the UI (D-13/D-14 division of labor)"
  - "CompletenessGrid treats empty optional sections as a neutral state (gray, 'vazio'), not errors — empty is normal for optional sections (D-12)"
  - "ProfilePreview hides sections with no entries (resume convention) and renders localized maps via one helper that picks pt-BR with a defensive fallback; single-value fields render as-is (D-02/D-04)"
  - "PlaceholderBanner stays purely informational — no dismiss control exists anywhere in the UI; the example flag flips only when the user edits content/profile.md (plan prohibition)"

requirements-completed: [PROFILE-01]

coverage:
  - id: D1
    description: "Finalized typed client contract: ok-envelope with PerfilDTO (full D-07 dump incl. example flag) + CompletudeDTO (15 keys), erro-envelope erros: string[]"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: cd frontend && npm run build (tsc -b contract gate) — exit 0"
        status: pass
      - kind: other
        ref: "command: live uvicorn smoke — /api/profile envelope keys match PerfilDTO (example,name,contact,…projects; completude 15 keys)"
        status: pass
    human_judgment: false
  - id: D2
    description: "ErrorPanel renders backend erros[] lines verbatim in a styled list with stable accessible heading — no client-side error mapping or translation"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep -q 'erros' frontend/src/components/ErrorPanel.tsx (consumes the backend array) — pass"
        status: pass
      - kind: other
        ref: "command: cd frontend && npm run build — exit 0 (no mapping logic typechecks alongside the union)"
        status: pass
    human_judgment: false
  - id: D3
    description: "App.tsx Perfil home three-state render: isPending loading text, status erro → ErrorPanel (app stays up), status ok → home; React Query v5 isPending (Pitfall 9)"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep ErrorPanel + isPending in frontend/src/App.tsx — both found"
        status: pass
    human_judgment: false
  - id: D4
    description: "CompletenessGrid renders all 7 completude sections with PT-BR labels and presence/count states; empty optional sections neutral"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep CompletenessGrid in frontend/src/App.tsx — found; build exit 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "ProfilePreview renders all D-07 sections resume-style, picking pt-BR values from localized maps; single-value fields as-is"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep 'pt-BR' frontend/src/components/ProfilePreview.tsx — found (base-language selection)"
        status: pass
      - kind: other
        ref: "command: cd frontend && npm run build — exit 0"
        status: pass
    human_judgment: false
  - id: D6
    description: "PlaceholderBanner prominent on exemplo:true and purely informational — no dismiss/edit control over the example flag"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep -E 'onClick|<button|dismiss' frontend/src/components/PlaceholderBanner.tsx — only the doc comment stating no control exists; zero interactive elements"
        status: pass
    human_judgment: false
  - id: D7
    description: "No raw-HTML injection path in any profile-rendering component (T-01-08 mitigation)"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep -c dangerouslySetInnerHTML App.tsx ProfilePreview.tsx ErrorPanel.tsx | non-zero lines = 0"
        status: pass
    human_judgment: false
  - id: D8
    description: "README finalized: dev flow, prod flow, edit-refresh behavior (D-15), where errors appear (UI + terminal), Phase 1 smoke check section"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: grep 'smoke check' README.md — found; sections verified by authoring read"
        status: pass
    human_judgment: false
  - id: D9
    description: "Full backend suite + frontend build green together — the phase's two automated gates pass on the finished UI (35 tests, build exit 0)"
    requirement: PROFILE-01
    verification:
      - kind: integration
        ref: "command: cd backend && uv run pytest -q — 35 passed"
        status: pass
      - kind: other
        ref: "command: cd frontend && npm run build — exit 0"
        status: pass
    human_judgment: false
  - id: D10
    description: "Browser-visual Perfil home (SC1/SC3 final): PT-BR shell, banner 'Dados de exemplo', completeness grid, resume preview of Ana Exemplo; broken profile shows the PT-BR error panel in-app; edit-refresh returns the healthy home without restart"
    requirement: PROFILE-01
    verification: []
    human_judgment: true
    rationale: "Visual browser confirmation is human-observable evidence — steps are scripted in README's 'Phase 1 smoke check' and run at the end-of-phase UAT per human_verify_mode: end-of-phase (same routing as plan-01 D7)"

# Metrics
duration: 7 min
completed: 2026-09-26
status: complete
---

# Phase 1 Plan 03: Perfil UI — Error State, Completeness Grid, Resume Preview Summary

**The Perfil home as a pure projection of GET /api/profile: typed contract with completude, verbatim PT-BR error panel, at-a-glance completeness grid, prominent example-data banner, and a resume-style preview of the profile — closing SC1 and SC3.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-26T00:38:51Z
- **Completed:** 2026-09-26T00:45:56Z
- **Tasks:** 2
- **Files modified:** 8 (3 created, 5 modified; +498/−29)

## Accomplishments

- **Finalized client contract** (`api/client.ts`): discriminated union `{status:"ok"; exemplo; perfil: PerfilDTO; completude: CompletudeDTO} | {status:"erro"; erros: string[]}` — PerfilDTO mirrors the full Pydantic dump (all D-07 sections, `example` flag, None-able optionals as `string | null`); native fetch, no axios
- **ErrorPanel** renders each backend `erros[]` line VERBATIM as a styled list with a stable accessible heading (`aria-labelledby`) — the backend's PT-BR messages carry the exact file/field path and the UI adds no mapping or translation (D-13/D-14); a broken profile is a rendered state and the app shell stays up
- **App.tsx three-state Perfil home**: isPending → loading text; status erro → ErrorPanel; status ok → load-status line, banner, completeness grid, preview — header + disabled nav placeholders kept from the tracer shell
- **CompletenessGrid**: all 7 sections (Resumo, Experiência, Formação, Habilidades, Certificações, Idiomas, Projetos) with presence accents and counts read straight from the completude DTO ("3 experiências · 8 impactos"); empty optional sections render neutral gray "vazio", not errors
- **ProfilePreview**: resume-style page — name, contact line, summary, experiences with date ranges and embedded impact bullets, education, skills by category, certifications, languages, projects with technologies; localized maps render the pt-BR base value via one defensive helper (D-04); single-value fields as-is (D-02); text children only (T-01-08)
- **PlaceholderBanner final form**: prominent amber status banner; purely informational — no dismiss or flag control anywhere (the placeholder state flips only via the file)
- **constants/ui.ts** completed with the full hardcoded PT-BR string set (status labels, error hint pointing at the file + terminal, completude labels keyed to `compute_completude`, preview headings) — no i18n framework
- **README finalized**: dev + prod flows, edit-refresh behavior, error surfacing (UI + terminal), and a "Phase 1 smoke check" section scripting the UAT steps
- **Both automated gates green together**: `uv run pytest -q` → 35 passed; `npm run build` → exit 0; live uvicorn smoke confirmed the ok envelope (exemplo true, 15 completude keys, 3 experiences / 8 impacts) and the SPA serving at the root

## Task Commits

Each task was committed atomically:

1. **Task 1: typed contract + ErrorPanel + three-state Perfil home wiring** — `eaf3dbb` (feat)
2. **Task 2: CompletenessGrid + ProfilePreview + banner final form + README** — `542e9e8` (feat)

## Files Created/Modified
- `frontend/src/api/client.ts` — finalized PerfilDTO/CompletudeDTO + ok/erro discriminated union (plan-02 contract)
- `frontend/src/constants/ui.ts` — complete PT-BR string set: status labels, error hint, banner copy, completude labels + units, preview headings
- `frontend/src/components/ErrorPanel.tsx` — verbatim erros[] rendering (D-13/D-14)
- `frontend/src/components/CompletenessGrid.tsx` — section presence/counts at a glance (D-12)
- `frontend/src/components/ProfilePreview.tsx` — resume-style render with pt-BR base-language selection (D-12/D-04)
- `frontend/src/components/PlaceholderBanner.tsx` — final prominent, control-free form
- `frontend/src/App.tsx` — three-state Perfil home assembly (D-12)
- `README.md` — run docs finalized + Phase 1 smoke check section

## Decisions Made
- Client types mirror the **full Pydantic dump** — including the `example` flag and None-able optionals typed `string | null` — so `tsc -b` stays the standing Pydantic↔TS drift gate (STACK.md).
- ErrorPanel is **dumb by design**: zero parsing/mapping logic in the UI; the backend owns all error prose (D-13 division of labor).
- CompletenessGrid treats **empty optional sections as neutral**, not errors — the grid answers "what's in the profile at a glance" without scolding (D-12).
- ProfilePreview **hides empty sections** (a resume never shows an empty heading) and routes every localized map through one helper picking `pt-BR` with a defensive fallback (the schema already forbids its absence).
- The banner has **no dismiss control anywhere** — per the plan prohibition, the UI never offers a way to change the `example` flag.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] T-01-08 verify grep matched its own doc comment**
- **Found during:** Task 2 (verification run)
- **Issue:** The ProfilePreview doc comment quoted the literal `dangerouslySetInnerHTML` when stating its absence, so the mechanical "no non-zero lines" grep gate counted 1
- **Fix:** Reworded the comment ("no raw-HTML injection path") — no code change; gate re-run clean (count 0)
- **Files modified:** frontend/src/components/ProfilePreview.tsx
- **Verification:** grep gate → 0 non-zero lines; build still green
- **Committed in:** 542e9e8

**2. [Scope note] constants/ui.ts received two Task-2 string constants**
- **Found during:** Task 2 (implementation)
- **Issue:** CompletenessGrid needs `COMPLETENESS_OK`/`COMPLETENESS_EMPTY`, but `constants/ui.ts` sits in Task 1's file list, not Task 2's
- **Fix:** Added the two strings to the constants module (the plan requires all PT-BR strings live there) and staged it with Task 2
- **Files modified:** frontend/src/constants/ui.ts
- **Verification:** build green; grid renders the constants
- **Committed in:** 542e9e8

---
**Total deviations:** 2 minor (1 verify-gate unblock, 1 file-list scope note). **Impact on plan:** none on behavior or scope; both changes serve the plan's own stated requirements.

## Issues Encountered
- Starlette TestClient httpx-deprecation warning persists (pre-existing, upstream, out of scope)
- The plan-level human-check smoke is scheduled for the end-of-phase UAT per `human_verify_mode: end-of-phase`; its steps are scripted in README's "Phase 1 smoke check" and coverage entry D10 routes it to the human. The API-level halves were proven live (ok envelope + SPA serving) and by the 35-test suite.

## Known Stubs
None blocking. The nav items Currículo/LinkedIn remain disabled **by design** (D-12 future-module placeholders; modules arrive in phases 3/6) — already tracked as open entry 1 in `.planning/WINDOWS.md`. Windows ledger entries 2 (completeness grid + preview deferred to plan 03) and 3 (interim error rendering superseded by plan 02's mapper) are resolved by this plan and were marked `fixed`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- **Phase 1 is functionally complete**: SC1/SC2/SC4/SC5 proven by plans 01–02 and this plan; SC1/SC3's browser-visual confirmation is the end-of-phase UAT item (README smoke check)
- The UI is a pure projection of GET /api/profile (Architectural Responsibility Map): D-12/D-13/D-14/D-15 obligations discharged in the frontend; Phases 2+ can extend the shell (nav modules) against the finalized PerfilDTO contract
- Phase 4's print template can build on the preview's visual order (banner → completeness → resume sections), as anticipated by the plan
- Phase UAT still to run: `/gsd:verify-work 1` (coverage block routes D10 — the browser smoke — to the human)

---
*Phase: 01-foundation-scaffold-master-profile*
*Completed: 2026-09-26*

## Self-Check: PASSED

All 8 key files exist on disk; both task commit hashes (`eaf3dbb`, `542e9e8`) found in git log; plan-level verification re-run green (`npm run build` exit 0; `uv run pytest -q` → 35 passed; T-01-08 grep count 0; live uvicorn smoke: ok envelope with 15 completude keys + SPA 200). WINDOWS.md: entries 2 and 3 marked fixed; entry 1 (nav placeholders, phases 3/6) intentionally remains open.
