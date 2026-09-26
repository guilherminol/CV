---
phase: 03-resume-vertical-slice
plan: 04
subsystem: ui
tags: [react, react-query, tailwind, vite, typescript, fetch, pt-br]

# Dependency graph
requires:
  - phase: 03-03
    provides: normative lint/gerar response contract (backend/app/routes/resume.py envelopes) mirrored by the typed client
  - phase: 01-foundation
    provides: ProfilePreview visual base, ErrorPanel pattern, hand-rolled Tailwind v4 component set, ['perfil'] React Query
provides:
  - Currículo screen end-to-end: JD form → debounced 80-char lint → generate → assembled result + honest coverage panel
  - Typed resume client (KeywordDTO, SecoesDTO, CoberturaItemDTO, LintResponse, GerarResponse, fetchResumeLint, gerarCurriculo) mirroring the 03-03 contract
  - Centralized Currículo copy contract in constants/ui.ts (UI-SPEC Copywriting Contract verbatim)
  - Nav view switch (curriculo | perfil, no router) with Currículo as default landing view
  - Reusable components: CurriculoHome, LintPanel, KeywordsPanel, ResumeResult, StatusLine
affects: [04-pdf-export (render base for the print template), 05-review-flow (per-section regenerate builds on ResumeResult)]

# Actuals (#2632) — same scale as the plan's estimate (chars/4 over the realized diff).
actuals:
  tokens: 9939
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: [] # no-new-frontend-deps contract held (native fetch + React Query v5 + Tailwind v4 only)
  patterns:
    - "View switching via useState without a router (STACK.md lean stack)"
    - "Debounced query gate: 800ms useEffect/setTimeout copy drives a useQuery enabled at >= 80 trimmed chars (one LLM call per settled state)"
    - "Zone composition: profile gate → form card → lint → aria-live region (in-flight/error/result)"
    - "Pure copy functions for PT-BR pluralization (resumoCoberturaCopy) — unit-testable offline, no test runner added"
    - "tLang(map, language) run-language display convention extending ProfilePreview's D-04 t()"

key-files:
  created:
    - frontend/src/pages/CurriculoHome.tsx
    - frontend/src/components/LintPanel.tsx
    - frontend/src/components/KeywordsPanel.tsx
    - frontend/src/components/ResumeResult.tsx
    - frontend/src/components/StatusLine.tsx
  modified:
    - frontend/src/constants/ui.ts
    - frontend/src/api/client.ts
    - frontend/src/App.tsx

key-decisions:
  - "View switch without a router: useState<'curriculo' | 'perfil'>('curriculo') in App; Currículo is the default landing view (planner decision); enabled nav items are buttons with aria-current + focus-visible rings"
  - "StatusLine extracted from App.tsx to components/StatusLine.tsx so CurriculoHome reuses the exact render without a circular import (render identical)"
  - "Coverage tally singular/plural keyed on total (total === 1 → '1 de 1 keyword … aparece'; otherwise the plural template) — noun-number agreement with total; contract examples pin only the total=1 case"
  - "Generated result sections (resumo/experiências/habilidades) always render (backend envelope is all-or-nothing); zero-entry passthrough sections stay hidden (ProfilePreview convention)"
  - "Badge spans carry normal-case inside uppercase section headings so the copy contract renders 'Gerado'/'Do perfil' verbatim, not shouted"
  - "CurriculoHome stub in Task 1 (plan-sanctioned) fully replaced by the real screen in Task 2"

patterns-established:
  - "Debounced lint gate: queryKey ['resume-lint', debouncedTrimmed], enabled only at >= 80 trimmed chars (T-03-10 LLM-spend bound)"
  - "aria-live polite region wrapping zones 3/4/5 — in-flight hint, error panel, and result announce without focus stealing"
  - "Chip status = aria-hidden glyph + visually-hidden text label (never glyph/color alone)"
  - "All-or-nothing result mount: mutation error or erro envelope never unmounts a prior result"

requirements-completed: [RESUME-01, RESUME-02, RESUME-04, PROFILE-02]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "Typed client mirrors the 03-03 normative contract: KeywordDTO/SecoesDTO/CoberturaItemDTO, LintResponse/GerarResponse unions, fetchResumeLint + gerarCurriculo POST fetchers"
    requirement: RESUME-01
    verification:
      - kind: other
        ref: "cd frontend && npm run build (tsc -b — the Pydantic↔TS drift gate) exits 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Full UI-SPEC Copywriting Contract centralized in constants/ui.ts as as-const exports (incl. tally singular/plural templates, CATEGORY_LABELS/CATEGORY_ORDER, curriculo nav flag enabled)"
    requirement: RESUME-04
    verification:
      - kind: other
        ref: "grep spot-checks for placeholder/clear-line/empty-keywords/tally strings + npm run build exit 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "CurriculoHome state machine: idle → typing → in-flight → result; CTA disabled under 80 trimmed chars (exactly 80 enables); 800ms debounced lint query; in-flight label swap + hint; failure never blanks a prior result"
    requirement: PROFILE-02
    verification: []
    human_judgment: true
    rationale: "Interactive runtime behavior needs a browser session; no JS test runner is allowed this phase (no-new-frontend-deps contract). End-of-phase human walkthrough is scheduled in plan 03-05 per the plan's verification section."
  - id: D4
    description: "LintPanel renders backend avisos verbatim (amber panel + non-blocking hint) or the green clear-line when empty; lint erro envelope lines render verbatim in a red panel"
    requirement: PROFILE-02
    verification: []
    human_judgment: true
    rationale: "Verbatim-render discipline is code-reviewed and compiles, but the rendered result needs visual confirmation (end-of-phase walkthrough, plan 03-05)."
  - id: D5
    description: "KeywordsPanel: plain factual tally (singular/plural, never a score/percentage), chips grouped by the 4 fixed categories in fixed order with empty categories hidden, flex-wrap, covered ✓ green / absent ○ gray, visually-hidden status labels"
    requirement: RESUME-04
    verification: []
    human_judgment: true
    rationale: "Copy function and grouping logic compile; chip readability incl. the 30+ keyword backstop row is explicitly a visual check at end-of-phase verification (UI-SPEC backstop)."
  - id: D6
    description: "ResumeResult assembled card (D-05): 3 Gerado-badged generated sections + Do perfil-badged formação/certificações/idiomas/projetos + name/contact header, ephemeral notice role=status above the card, Gerar novamente without confirmation, tLang EN-first convention, text-children-only render"
    requirement: RESUME-01
    verification: []
    human_judgment: true
    rationale: "Structure compiles and greps confirm no dangerouslySetInnerHTML and no persistence calls, but badge placement/visual assembly needs human eyes at the end-of-phase walkthrough (plan 03-05)."

# Metrics
duration: 13min
completed: 2026-09-26
status: complete
---

# Phase 3 Plan 4: Currículo Screen Summary

**The Currículo screen end-to-end: paste a JD, pick PT-BR/EN, see the debounced JD-tied lint, generate, and get the assembled resume (Gerado/Do perfil badged) with the honest keyword-coverage tally — on the approved UI-SPEC contract and the typed 03-03 client.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-26T22:10:23Z
- **Completed:** 2026-09-26T22:23:52Z
- **Tasks:** 3
- **Files modified:** 8 (5 created, 3 modified)

## Accomplishments

- Full Currículo screen: profile gate (shared ['perfil'] query) → Zone 1 form card (JD textarea, native-radio PT-BR/EN segmented control, primary CTA disabled under 80 trimmed chars) → Zone 2 debounced lint panel → Zone 3 in-flight hint → Zone 4 assembled resume card → Zone 5 keywords/coverage panel
- Typed client mirroring the normative 03-03 contract (KeywordDTO, SecoesDTO, CoberturaItemDTO, LintResponse, GerarResponse + fetchResumeLint/gerarCurriculo); tsc -b green as the standing Pydantic↔TS drift gate
- Every UI-SPEC Copywriting Contract string centralized in constants/ui.ts as as-const exports; coverage is a plain factual tally (singular/plural via the pure `resumoCoberturaCopy`) — no score, percentage, or meter anywhere
- Nav view switch without a router: enabled items are buttons (aria-current, focus-visible rings), Currículo enabled and the default landing view; disabled items stay aria-disabled spans
- Security posture held: JSX text children only (no dangerouslySetInnerHTML in any new component), generated content in React state only (no persistence calls), 800ms debounce + 80-char gate bounding pre-generate LLM spend

## Task Commits

Each task was committed atomically:

1. **Task 1: Contract layer — ui.ts copy contract, client.ts DTOs + fetchers, App.tsx nav switch** - `cd07843` (feat)
2. **Task 2: Zones 1/2/3/5 — CurriculoHome state machine + LintPanel + KeywordsPanel** - `c9c643b` (feat)
3. **Task 3: Zone 4 — ResumeResult assembled card** - `e1a7f42` (feat)

## Files Created/Modified

- `frontend/src/constants/ui.ts` — curriculo nav flag enabled; full Currículo copy contract + CATEGORY_LABELS/CATEGORY_ORDER + run-language generated headings
- `frontend/src/api/client.ts` — resume DTOs + unions mirroring 03-03; fetchResumeLint, gerarCurriculo
- `frontend/src/App.tsx` — curriculo|perfil view state, nav buttons, default CurriculoHome
- `frontend/src/pages/CurriculoHome.tsx` — the screen: state machine, form card, lint/in-flight/error/result zones (created as a plan-sanctioned stub in Task 1, fully implemented in Task 2)
- `frontend/src/components/LintPanel.tsx` — verbatim avisos / green clear-line
- `frontend/src/components/KeywordsPanel.tsx` — coverage chips by fixed category order + pure tally copy fn
- `frontend/src/components/ResumeResult.tsx` — assembled card, badges, ephemeral notice, tLang
- `frontend/src/components/StatusLine.tsx` — extracted from App.tsx (identical render, shared by both homes)

## Decisions Made

- View switching via useState with Currículo as default landing view (planner decision; trivially reversible) — no router dependency added
- StatusLine extracted to its own component rather than imported from App.tsx — avoids a circular import (App imports CurriculoHome); PerfilHome render unchanged
- Coverage tally singular/plural keyed on `total === 1`: "1 de 1 keyword … aparece" vs "{n} de {m} keywords … aparecem" — noun-number agreement with total; the contract examples pin only the total=1 case
- Generated sections always render (backend envelope is all-or-nothing so a partial set is unreachable); zero-entry passthrough sections stay hidden per ProfilePreview convention
- `normal-case` added to badge spans inside uppercase section headings so "Gerado"/"Do perfil" render per the copy contract rather than shouted
- Lint-panel fetch errors (server down) render nothing in Zone 2 — the plan pins only pending/ok/erro-envelope states; a generate attempt surfaces the failure loudly via its own error panel

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] StatusLine extracted from App.tsx to components/StatusLine.tsx**
- **Found during:** Task 2 (CurriculoHome profile gate)
- **Issue:** CurriculoHome must render "the established StatusLine + ErrorPanel verbatim pattern", but StatusLine was a local function inside App.tsx — importing it from App would create a circular import (App ↔ CurriculoHome)
- **Fix:** Moved StatusLine to frontend/src/components/StatusLine.tsx (byte-identical render); App.tsx imports it; PerfilHome internals unchanged
- **Files modified:** frontend/src/components/StatusLine.tsx (new), frontend/src/App.tsx
- **Verification:** npm run build green; both homes render the same status line
- **Committed in:** c9c643b (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Extraction-only refactor required for the plan's own "established verbatim pattern" requirement; zero behavior change.

## Issues Encountered

- oxlint (not part of the build gate) reports `react(only-export-components)` on KeywordsPanel.tsx because the plan mandates exporting the pure `resumoCoberturaCopy` from the component file ("Functions: resumoCoberturaCopy(cobertos, total) (KeywordsPanel.tsx)"). Kept as-is to honor the plan's artifact contract; it is a dev-only fast-refresh caveat, 0 errors, build unaffected.

## Verification Results

- `cd frontend && npm run build` → tsc -b + vite build green (run after every task and at plan close)
- `cd backend && uv run pytest -q` → 169 passed, 5 deselected (llm marker) — backend contract untouched
- Prohibition greps: no `dangerouslySetInnerHTML` in new components; no localStorage/sessionStorage/persistence calls; no score/percentage coverage strings
- Human walkthrough (idle → paste JD → lint at 80 chars → generate → badges + chips + ephemeral notice) is scheduled at end-of-phase verification in plan 03-05 per the plan's verification section

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The Currículo flow is complete and typed end-to-end; plan 03-05 (final phase plan) can run the end-of-phase human walkthrough against this screen
- Phase 4 (PDF export) renders the same assembled card ResumeResult builds — the D-05 section order is the print template's source order
- Phase 5 (review flow) extends the generate mutation path (per-section regenerate hooks into the same ['perfil'] + response state)
- RESUME-01 requirement marking deferred: plan 03-05 also declares RESUME-01 (shared-ID gate) and has no SUMMARY yet; it will flip complete when 03-05 finishes

---
*Phase: 03-resume-vertical-slice*
*Completed: 2026-09-26*
