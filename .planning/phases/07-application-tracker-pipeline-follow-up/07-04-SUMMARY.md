---
phase: 07-application-tracker-pipeline-follow-up
plan: 04
subsystem: [ui]
tags: [react, react-query, view-state-wiring, tracker, metadata-only-events]
requires:
  - phase: 07-application-tracker-pipeline-follow-up (plans 01+02+03)
    provides: trackerPrefill state + TrackerHome prefill seam (07-01), the registrarEvento / fetchTrackerResumo client surface + 'resposta' tipo contract (07-02), the assembled Rastreador view with ['tracker'] cache + CandidaturaForm valoresIniciais (07-03)
provides:
  - D-13 door 2 — "Registrar candidatura" CTA on the Currículo result card (optional props on ResumeResult; hidden when the callback is absent); hands {jd_texto, language} of the run to App's trackerPrefill and switches the view
  - D-13 door 3 — Respostas association control: ['tracker']-cached candidatura picker ("empresa — cargo", "(arquivada)" suffix) recording a metadata-only 'resposta' event {tipo, data_evento local-parts, idioma, fixed observacao} through the existing registrarEvento path
  - consume-once prefill semantics — the Rastreador reads the pending prefill in one effect and clears it in the same pass; a second visit via the nav never re-sees stale JD
  - RASTREADOR_REGISTRAR_CTA + RASTREADOR_ASSOCIACAO_* strings + the fixed RASTREADOR_RESPOSTA_OBSERVACAO note in constants/ui.ts (zero inline strings)
affects: [07-05]
actuals:
  tokens: 7688     # chars/4 over the measured diff (30753 chars, 482+/29-)
  tasks: 2
  commits: 4       # measured: git rev-list --count b1d22d2..HEAD (2 plan chores: Phase 6 tracked-source baselines)
plan_head_before: b1d22d2b8de7276e22f420ae14a5e67b2ff486ec
plan_head_after: 0035d06
tech-stack:
  added: []        # zero new dependencies (T-07-SC held: no installs in this plan)
  patterns:
    - "Pattern 9 verbatim: App owns trackerPrefill + setView; CurriculoHome receives the optional setter callback and passes a capturing closure down to ResumeResult (values read from the SAME jdText/idioma state the gerar run consumed — captured at call time, no refs into mutation internals)"
    - "Consume-once via one useEffect (read + clear in the same pass) + formKey remount feeding valoresIniciais — the plan-pinned posture, replacing 07-01's criar.onSuccess consumption"
    - "Local-parts date string (getFullYear/getMonth/getDate, zero-padded) for the association's data_evento — never toISOString (Pitfall 7 posture; the one sanctioned client-side 'today' in the phase)"
    - "Shared ['tracker'] query key across views — the picker shares the cache with the Rastreador page; association success invalidates it so contadores/kanban can never desynchronize (Pitfall 6)"
tech-stack-notes: none
key-files:
  created: []      # zero new files — pure wiring on existing surfaces
  modified:
    - frontend/src/App.tsx
    - frontend/src/pages/CurriculoHome.tsx
    - frontend/src/components/ResumeResult.tsx
    - frontend/src/pages/TrackerHome.tsx
    - frontend/src/pages/CandidaturaHome.tsx
    - frontend/src/constants/ui.ts
key-decisions:
  - "Prefill hand-off carries exactly {jd_texto, language}; only jd_texto lands in the form — the D-06 create contract (CandidaturaCriacaoRequest, extra=forbid) has NO idioma key and the form has NO idioma field (idioma is EVENT metadata per D-08), so the language part is dropped at the consumption point (07-03's readiness note anticipated this fork; extending the schema would violate this plan's no-new-backend-surface objective)"
  - "The association's idioma pins THE ANSWER'S generation language, captured from the submitted payload in responder.onSuccess(variables) — not the live selector, which the user may change after generating"
  - "The association UI resets on each new successful answer (a new answer is a fresh association opportunity); the ok feedback renders with role=status inside the answer card"
  - "Baseline chore commits (c2c5c47, 7304ea9) landed the Phase 6 working-tree sources (ResumeResult.tsx modifications, untracked CandidaturaHome.tsx) per the PATTERNS.md tracked-source gate BEFORE any plan edit — the plan diffs carry only the door wiring"
patterns-established:
  - "Optional callback-prop doors: new affordances on shipped components enter as optional props + constants strings, rendering nothing for existing call sites (ResumeResult posture — reusable for future cross-view CTAs)"
  - "hojeLocalIso() local-parts helper in the consuming page (not a tracker component) — the phase's single sanctioned client-side 'today'"
requirements-completed: [TRK-03, TRK-04]  # copied verbatim from 07-04-PLAN.md frontmatter; REQUIREMENTS.md carries no TRK-* rows (plan-level IDs co-declared with 07-03/07-05, same as 07-03's SUMMARY)
coverage:
  - id: D1
    description: "Door 2 — Registrar click hands {jd_texto, language} of the run to the Rastreador form; prefill consumed exactly once; empresa/cargo stay user-typed; existing call-site contracts untouched"
    requirement: TRK-03
    verification:
      - kind: other
        ref: "cd frontend && npm run build (exit 0 — tsc -b + vite)"
        status: pass
      - kind: other
        ref: "grep proofs: onRegistrarCandidatura?: () => void (optional token) at ResumeResult:500; CurriculoHome:890 builds {jd_texto: trimmed, language: idioma} (the gerar mutation's exact inputs); App:135 setTrackerPrefill+setView; TrackerHome effect reads prefill.jd_texto and calls onPrefillConsumida in the SAME pass; TrackerPrefill interface carries exactly jd_texto+language"
        status: pass
    human_judgment: false
  - id: D2
    description: "Door 3 — association records a metadata-only 'resposta' event (tipo/data_evento/idioma/observacao only, fixed note), picker \"empresa — cargo\" + \"(arquivada)\", loud-empty zero state, ['tracker'] invalidation"
    requirement: TRK-04
    verification:
      - kind: unit
        ref: "cd backend && uv run pytest tests/test_tracker_api.py -q (32 passed — the 'resposta' literal + EventoRegistroRequest contract unchanged); full offline suite 516 passed, 9 deselected"
        status: pass
      - kind: other
        ref: "grep proofs: payload exactly tipo:'resposta'/data_evento: hojeLocalIso()/idioma/observacao: RASTREADOR_RESPOSTA_OBSERVACAO (CandidaturaHome:131-134); option label line 286 + suffix 287; loud-empty line 272; invalidateQueries(['tracker']) line 143; git ls-files shows CandidaturaHome.tsx tracked (baseline 7304ea9)"
        status: pass
    human_judgment: false
  - id: D3
    description: "End-to-end feel: registrar-click → prefilled form in the browser; association → event visible in EventosPanel + follow-up anchor behavior on the live board"
    requirement: TRK-03
    verification: []
    human_judgment: true
    rationale: "The plan's own verification routes the manual click-through to 07-05 UAT; the automated layer proves compilation, the wire contract, and the payload shape only."
duration: 9min
completed: 2026-11-11
status: complete
---

# Phase 7 Plan 4: Entry Doors — Registrar Prefill + Respostas Association Summary

**Both remaining D-13 doors live with zero backend surface and zero new dependencies: the Currículo result's "Registrar candidatura" CTA hands the run's {jd_texto, language} through App state into the Rastreador form (consumed exactly once), and the Respostas screen associates answers with candidaturas via metadata-only 'resposta' events on the existing registrarEvento contract — the tracker now participates in the daily flow from the moment a resume is generated.**

## Performance
- **Duration:** 9 min
- **Started:** 2026-11-11T00:12:02Z
- **Completed:** 2026-11-11T00:21:05Z
- **Tasks:** 2 (both type="auto") + 2 plan-mandated baseline chores
- **Files modified:** 6 (0 created, 6 modified)

## Accomplishments
- Door 2 (Currículo result): ResumeResult gained the OPTIONAL `onRegistrarCandidatura`/`registrarDesabilitado` props and renders the "Registrar candidatura" CTA (COMPACT_SECONDARY_BUTTON_CLASSES) below the generated sections — hidden entirely when the callback is absent, so every existing call site compiles and renders untouched
- CurriculoHome threads the callback down, building the prefill from the SAME state the gerar run consumed (`jd_texto: trimmed, language: idioma`) captured at call time; App owns the hand-off (`setTrackerPrefill` + `setView('rastreador')`) per Pattern 9
- Consume-once prefill: one useEffect in TrackerHome reads the pending JD into the create-form seed and calls `onPrefillConsumida()` in the same pass, with a formKey remount — a second Rastreador visit via the nav shows a clean form; create success also clears the seed so the fresh form stays clean
- Door 3 (Respostas): the association control renders under a successful answer — a select fed by `fetchTrackerResumo` under the SHARED `['tracker']` cache key (options as "empresa — cargo" with the "(arquivada)" suffix), the "Associar" CTA with inflight swap, and the loud-empty line when zero candidaturas exist
- Metadata-only event: `registrarEvento(candidatura_id, { tipo: 'resposta', data_evento: <local-parts today>, idioma: <the answer's generation language>, observacao: RASTREADOR_RESPOSTA_OBSERVACAO })` — exactly four fields; the question and answer text never leave the page's ephemeral state (D-08/A9; no schema column exists to receive them)
- onSuccess: "Resposta registrada na candidatura." + `invalidateQueries(['tracker'])` so contadores and the follow-up anchor reflect the activity; erro envelopes render verbatim via ErrorPanel; fetch-level failures take the generic PT-BR hint
- All new strings centralized: RASTREADOR_REGISTRAR_CTA, RASTREADOR_ASSOCIACAO_* (label/placeholder/CTA/inflight/ok/erro/sem-candidaturas) and the fixed RASTREADOR_RESPOSTA_OBSERVACAO note — zero inline user-facing strings
- Gates: frontend build green after each task; tracker API suite 32 passed; full offline suite 516 passed, 9 deselected (llm marker) — zero regressions

## Task Commits
1. **Task 1: "Registrar candidatura" prefill — Currículo result door** - `90cab99` (feat; preceded by baseline chore `c2c5c47` — ResumeResult.tsx Phase 6 tracked-source gate)
2. **Task 2: Respostas association — metadata-only 'resposta' event door** - `0035d06` (feat; preceded by baseline chore `7304ea9` — untracked CandidaturaHome.tsx tracked per the gate)

**Plan metadata:** docs commit follows (SUMMARY + STATE + ROADMAP)

## Files Created/Modified
- `frontend/src/App.tsx` - passes the optional onRegistrarCandidatura setter into CurriculoHome (setTrackerPrefill + setView in one callback); prefill state ownership unchanged from 07-01
- `frontend/src/pages/CurriculoHome.tsx` - optional prop typed on TrackerPrefill; the ResumeResult usage site passes the capturing closure ({jd_texto: trimmed, language: idioma})
- `frontend/src/components/ResumeResult.tsx` - two optional props + the hidden-when-absent CTA below the generated sections (Phase 6 baseline committed first as c2c5c47)
- `frontend/src/pages/TrackerHome.tsx` - consume-once effect (read + clear in one pass + formKey remount), seed cleared on create success, valoresIniciais from the seed; comment documents why language has no landing field
- `frontend/src/pages/CandidaturaHome.tsx` - tracked first (7304ea9), then the association block: picker + mutation + feedback + loud-empty + hojeLocalIso() local-parts helper
- `frontend/src/constants/ui.ts` - RASTREADOR_REGISTRAR_CTA + RASTREADOR_ASSOCIACAO_* + RASTREADOR_RESPOSTA_OBSERVACAO

## Decisions Made
- The prefill's language part is dropped at the consumption point (see Deviations #1) — the hand-off still carries exactly {jd_texto, language} as pinned
- The association's idioma comes from responder.onSuccess(variables.language) — the answer's actual generation language, immune to post-generation selector changes
- The association UI resets on every new successful answer; ok feedback renders inline in the answer card with role=status
- Baseline chore commits for the Phase 6 sources (ResumeResult.tsx pending diff, untracked CandidaturaHome.tsx) landed BEFORE the plan edits so each plan diff carries only its own wiring (PATTERNS.md tracked-source gate, plan-mandated)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking seam] prefill.language has no landing field — dropped at the consumption point**
- **Found during:** Task 1 (TrackerHome wiring against the 07-01/07-03 as-built form)
- **Issue:** The task action says to "map prefill.language ('pt-BR' | 'en') to the form's idioma field" — but CandidaturaForm has NO idioma field (the D-06 contract's 11 fields exclude it) and CandidaturaCriacaoRequest (extra=forbid) carries NO idioma key, exactly as 07-03's Next Phase Readiness warned. Sending idioma on create would 422; adding the field means a DB column + DTO + route + tests on the shipped 07-02 contract — a Rule 4 schema change that also contradicts this plan's own objective ("pure view-state wiring... no new backend surface").
- **Fix:** The hand-off carries exactly {jd_texto, language} (TrackerPrefill pins both keys; CurriculoHome sends both — the acceptance criterion holds); TrackerHome consumes jd_texto into the form seed only, with a comment naming the reason. Language remains declarative in the seam for a future plan (e.g. as an event-level default on 'envio_curriculo').
- **Files modified:** frontend/src/pages/TrackerHome.tsx (comment + consumption shape only)
- **Verification:** build green; create payload identical to the shipped contract
- **Committed in:** 90cab99

---

**Total deviations:** 1 auto-fixed (1 Rule 3 blocking seam; zero Rule 1/2 — both builds were green on first attempt)
**Impact on plan:** None negative — every acceptance criterion passes. The door-2 UX is "JD prefilled, language remembered in the seam" instead of "both prefilled"; empresa/cargo stay user-typed exactly per D-13. All three doors work end-to-end on shipped contracts.

## Issues Encountered
None beyond deviation #1. The 07-01 prefill seam (state + props), the 07-02 event contract ('resposta' literal accepted), and the 07-03 form/eventos surfaces consumed exactly as built; CandidaturaForm's valoresIniciais docstring had already anticipated the idioma fork.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for 07-05 (UAT/verification): all three D-13 doors are live on shipped contracts — manual form (07-01/03), registrar prefill (this plan), Respostas association (this plan)
- 07-05 UAT routing: door-2 click-through (JD lands prefilled, form clean on second visit), door-3 click-through (event appears in EventosPanel, contadores move, follow-up anchor reacts) are human_judgment items (coverage D3) — the automated layer proves compilation + wire contract + payload shape only
- Note for any future plan: the prefill's language part sits unused in the seam by design; the natural landing is event-level (idioma on the 'envio_curriculo' registration), not the candidatura row
- Blockers: none (deterministic module — OpenRouter credit exhaustion is irrelevant here, D-15)

## Self-Check: PASSED

- All 6 modified files found on disk with the door wiring; CandidaturaHome.tsx git-tracked (7304ea9)
- Commits c2c5c47, 90cab99, 7304ea9, 0035d06 all ancestors of HEAD
- Measured commits: git rev-list --count b1d22d2..HEAD = 4 (matches frontmatter actuals; ledger .git/gsd-plan-head-before-07-04)
- Verifications: npm run build green after both tasks; backend tracker suite 32 passed; full offline suite 516 passed, 9 deselected

---
*Phase: 07-application-tracker-pipeline-follow-up*
*Completed: 2026-11-11*
