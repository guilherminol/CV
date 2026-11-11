---
phase: 07-application-tracker-pipeline-follow-up
plan: 03
subsystem: [ui]
tags: [react, dnd-kit, react-query, tailwind, kanban, forms]
requires:
  - phase: 07-application-tracker-pipeline-follow-up (plans 01+02)
    provides: the stable 11-route /api/tracker surface (200 envelope, server-computed derived fields, base64 export transport), @dnd-kit trio installed, Rastreador fifth-view skeleton with the ['tracker'] query key and prefill seam
provides:
  - complete Rastreador UI — ContadoresGrid, Visão geral with prazo chips + follow-up badge, D-14 KanbanBoard (dnd-kit sortable, droppable empty columns, keyboard sensor), CandidaturaCard, one-at-a-time detail region with aligned field grid, full D-06 CandidaturaForm (create + edit), EventosPanel with the follow-up lifecycle controls, EstagioManager, JSON/CSV export section
  - typed client mutation surface — moverCandidatura, editarCandidatura, registrarEvento, executarFollowup, adiarFollowup, criarEstagio, renomearEstagio, reordenarEstagios, removerEstagio, exportarTracker + downloadConteudo (S8 anchor discipline)
  - server-side follow-up panel slots: followup_pendente_data + followup_vencido_dias in the derived projection (pytest-pinned, injectable hoje)
  - every user-facing string/class centralized under RASTREADOR_* in constants/ui.ts (zero inline strings)
affects: [07-04, 07-05]
actuals:
  tokens: 23200    # chars/4 over the measured diff (92805 chars, 1986+/117-)
  tasks: 3
  commits: 3       # measured: git rev-list --count 2f664c9..HEAD
plan_head_before: 2f664c9bd3aa86f03e4c14f2e23aa2703703cace
plan_head_after: 132415f1a9b1e693337e1cecd356a53ee59d10f2
tech-stack:
  added: []        # zero new deps — @dnd-kit family was already installed by 07-01
  patterns:
    - "RESEARCH Pattern 5 verbatim: one DndContext (PointerSensor distance-8 + KeyboardSensor sortableKeyboardCoordinates, closestCorners), one SortableContext per column, items derived from the SAME array the JSX maps (Pitfall 10), droppable column bodies for empty columns, prefixed column ids (no PK collision with card ids)"
    - "No optimistic update on drops (A8): the ['tracker'] refetch is the truth; intra-column visual sorts are not persisted and skip the mutation"
    - "Server-computed string slots: the panel renders {data}/{X} from the payload — the client never sources 'hoje' (Pitfall 7; zero new Date() in tracker components)"
    - "Presentational form + local state: CandidaturaForm bubbles onSubmit to TrackerHome's mutations; omitted empty keys mean 'untouched' on the edit path (extra=forbid-safe)"
tech-stack-notes: none
key-files:
  created:
    - frontend/src/components/tracker/ContadoresGrid.tsx
    - frontend/src/components/tracker/CandidaturaForm.tsx
    - frontend/src/components/tracker/EventosPanel.tsx
    - frontend/src/components/tracker/KanbanBoard.tsx
    - frontend/src/components/tracker/CandidaturaCard.tsx
    - frontend/src/components/tracker/EstagioManager.tsx
  modified:
    - frontend/src/pages/TrackerHome.tsx
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - backend/app/tracker/service.py
    - backend/tests/test_tracker_service.py
key-decisions:
  - "Follow-up panel strings ({data}/{X}) render from TWO NEW server-computed fields (followup_pendente_data, followup_vencido_dias) — the payload lacked them and the client has no honest way to source 'hoje' (Pitfall 7); all date math stays server-side and pytest-pinned"
  - "Kanban columns render the ACTIVE pipeline only (arquivada filtered out) — the overview keeps the full payload history; same-stage drops skip the mutation (no no-op writes)"
  - "Adiar date input carries NO min attribute — the UI never computes 'tomorrow' client-side; a past target returns the PT-BR erro envelope, which the panel renders verbatim (plan gate overrides the UI-SPEC min suggestion)"
  - "The form has NO stage field — kanban drops own stage changes; create defaults server-side to the first stage by ordem (07-01 pin)"
patterns-established:
  - "trackerMutacao envelope runner in client.ts — one JSON-body runner per tracker mutation, typed per endpoint, non-2xx throws with the route name (generic PT-BR hint at the caller)"
  - "Render-time state adjustment (React-documented) instead of effects for prop-driven resets (EventosPanel registro clear; TrackerHome edit-session close on candidatura switch)"
requirements-completed: [TRK-02, TRK-03, TRK-04, TRK-05, TRK-06]  # copied verbatim from 07-03-PLAN.md frontmatter; REQUIREMENTS.md checkboxes governed by the Shared-ID gate (co-declared with 07-04/07-05)
coverage:
  - id: D1
    description: "ContadoresGrid: the three honest numbers rendered as a pure prop passthrough (CompletenessGrid tile pattern, pinned 18px semibold exception)"
    requirement: TRK-04
    verification:
      - kind: other
        ref: "cd frontend && npm run build (exit 0 — tsc -b + vite)"
        status: pass
      - kind: other
        ref: "grep: ContadoresGrid renders only contadores[chave] — zero computation beyond prop passthrough"
        status: pass
    human_judgment: false
  - id: D2
    description: "CandidaturaForm: all 11 D-06 fields with WR-01 maxLength mirrors of models.py bounds (200/200/200/2000/100/200/5000/20000), sr-only modalidade radio idiom, create + edit modes"
    requirement: TRK-03
    verification:
      - kind: other
        ref: "grep: maxLength={RASTREADOR_LIMITE_*} present for empresa/cargo/fonte/link_vaga/faixa_salarial/contato/notas/jd_texto (+ evento observacao 2000)"
        status: pass
      - kind: other
        ref: "cd frontend && npm run build (exit 0)"
        status: pass
    human_judgment: false
  - id: D3
    description: "EventosPanel: executar/adiar controls gated STRICTLY by payload followup_pendente/followup_vencido; metadata-only registro form; loud empty line"
    requirement: TRK-05
    verification:
      - kind: other
        ref: "cd frontend && npm run build (exit 0); backend vectors test_followup_pendente_data_e_vencido_dias_derivados + test_followup_derivados_nulos_sem_followups pin the payload slots (73 tracker tests green)"
        status: pass
    human_judgment: false
  - id: D4
    description: "KanbanBoard config: PointerSensor activationConstraint distance 8 + KeyboardSensor sortableKeyboardCoordinates + closestCorners; SortableContext items = the rendered array; droppable column bodies; card handle carries listeners, body button opens detail"
    requirement: TRK-02
    verification:
      - kind: other
        ref: "grep: activationConstraint distance 8 / sortableKeyboardCoordinates / closestCorners / useDroppable in KanbanBoard.tsx"
        status: pass
      - kind: other
        ref: "grep -rn dangerouslySetInnerHTML frontend/src/components/tracker = 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "Drag feel, keyboard DnD end-to-end, amber/red chip color rendering on the live board"
    requirement: TRK-02
    verification: []
    human_judgment: true
    rationale: "The plan's own verification marks these Manual-only, routed to 07-05 UAT; the automated layer proves configuration and compilation only."
  - id: D6
    description: "EstagioManager: add/rename/reorder (complete id list)/remove; blocked removal renders the backend PT-BR refusal verbatim through ErrorPanel; export buttons pass the envelope filename verbatim to downloadConteudo; archive is the only closure control"
    requirement: TRK-02
    verification:
      - kind: unit
        ref: "cd backend && uv run pytest tests/test_tracker_api.py tests/test_tracker_service.py tests/test_tracker_db.py -q (73 passed)"
        status: pass
      - kind: other
        ref: "grep -rni 'remover candidatura|excluir candidatura' tracker components + TrackerHome = 0; grep new Date( = 0"
        status: pass
    human_judgment: false
  - id: D7
    description: "Every tracker mutation (criar/editar/arquivar/mover/evento/executar/adiar/estagio CRUD/export) invalidates ['tracker']; erro envelopes render verbatim per section"
    requirement: TRK-04
    verification:
      - kind: other
        ref: "cd frontend && npm run build (exit 0 — tsc -b gates every mutation branch); full offline suite 516 passed"
        status: pass
    human_judgment: false
duration: 24min
completed: 2026-11-11
status: complete
---

# Phase 7 Plan 3: Rastreador Full UI — Kanban, D-06 Form, Eventos, Estágios, Export Summary

**The complete Rastreador UI on the 07-02 contract: a dnd-kit kanban (distance-8 clicks, droppable empty columns, keyboard sensor, no optimistic update), the full 11-field D-06 form, the eventos panel with payload-gated follow-up lifecycle controls, stage vocabulary management with honest erro rendering, and JSON/CSV export with backend filenames — every mutation through the shared ['tracker'] key.**

## Performance
- **Duration:** 24 min
- **Started:** 2026-11-10T23:42:45Z
- **Completed:** 2026-11-11T00:07:29Z
- **Tasks:** 3 (all type="auto")
- **Files modified:** 11 (6 created, 5 modified)

## Accomplishments
- D-14 kanban live: one DndContext with PointerSensor(distance 8) + KeyboardSensor(sortableKeyboardCoordinates) and closestCorners; one SortableContext per column whose items derive from the exact rendered array (Pitfall 10); every column body is a useDroppable target so EMPTY columns accept drops; drops resolve through the mover mutation + invalidation — zero hand-rolled drag, zero optimistic update (A8)
- Full D-06 CandidaturaForm: empresa/cargo/fonte/link_vaga/modalidade(sr-only radio idiom)/datas/faixa_salarial/contato_recrutador/notas/jd_texto with WR-01 maxLength mirrors naming models.py bounds; create + edit modes ("Salvar alterações", cancel, PATCH semantics via omitted empty keys)
- EventosPanel: events list (loud empty), metadata-only registro form (five tipo labels, idioma options reusing CURRICULO_IDIOMA_OPTIONS, observacao 2000), and follow-up controls gated STRICTLY by payload pendente/vencido — the red vencido line and the pendente date render from server-computed slots, never client date math
- EstagioManager: add/rename(inline)/reorder(up/down over the complete id list)/remove — blocked removal renders the backend's PT-BR refusal verbatim through ErrorPanel; collapsed by default
- Export: "Exportar JSON"/"Exportar CSV" with inflight swap; the ok envelope's backend filename passes verbatim to downloadConteudo (S8 anchor+revoke discipline)
- Overview rows carry the D-09 prazo chips (amber 0..3 / red negative / neutral, with sr-only suffixes) + the D-12 "Considerar follow-up" badge; detail region renders the aligned field grid with loud nulls and link_vaga as the only anchor (rel="noreferrer")
- Backend: derivar_campos now carries followup_pendente_data + followup_vencido_dias (the pinned panel strings' slots), pinned by 2 new offline vectors — tracker trio 73 green; full offline suite 516 passed

## Task Commits
1. **Task 1: Contadores + full CandidaturaForm + EventosPanel + TrackerHome assembly** - `e185f13` (feat)
2. **Task 2: KanbanBoard + CandidaturaCard — the D-14 ready-made DnD board** - `ae8a7ca` (feat)
3. **Task 3: EstagioManager + export buttons — vocabulary management and D-03 UI closure** - `132415f` (feat)

**Plan metadata:** docs commit follows (SUMMARY + STATE + ROADMAP)

## Files Created/Modified
- `frontend/src/components/tracker/KanbanBoard.tsx` - one DndContext board: sensors, closestCorners, per-column SortableContext, droppable empty columns, prefixed column ids, same-stage drop guard
- `frontend/src/components/tracker/CandidaturaCard.tsx` - useSortable card with header drag handle + body open-button; exports PrazoChip/FollowupBadge reused by the overview
- `frontend/src/components/tracker/CandidaturaForm.tsx` - full D-06 form, presentational + local state, onSubmit bubbles to TrackerHome mutations
- `frontend/src/components/tracker/EventosPanel.tsx` - events list + registro + payload-gated follow-up controls (executar/adiar with date input)
- `frontend/src/components/tracker/EstagioManager.tsx` - stage add/rename/reorder/remove with verbatim erro rendering
- `frontend/src/components/tracker/ContadoresGrid.tsx` - honest counters, pure prop passthrough
- `frontend/src/pages/TrackerHome.tsx` - full assembly: contadores, overview with chips, Pipeline board, detail region (grid + Editar/Arquivar + EventosPanel), create/edit form, Estágios manager, export section; 12 mutations all invalidating ['tracker']
- `frontend/src/api/client.ts` - tracker mutation surface (10 functions + downloadConteudo) under the drift-gate banner; CandidaturaDTO gains the two follow-up slots
- `frontend/src/constants/ui.ts` - all RASTREADOR_* strings/classes/formatters (chips verbatim from the UI-SPEC, bounds mirrors WR-01)
- `backend/app/tracker/service.py` - derivar_campos + followup_pendente_data / followup_vencido_dias (Rule 2, see Deviations)
- `backend/tests/test_tracker_service.py` - 2 new vectors pinning the follow-up panel slots

## Decisions Made
- Follow-up panel slots are SERVER-computed (see Deviations #1) — consistent with dias_para_prazo: the client renders deltas and never sources "hoje"
- Kanban = the ACTIVE pipeline (archived candidaturas filtered from columns; overview keeps full payload history with an "(arquivada)" suffix — D-04 closure semantics)
- Same-stage drops skip the mover mutation (no no-op writes; intra-column visual sorts are not persisted by design — no candidatura ordem exists)
- The create/edit form has no stage select — drops own stage changes; server default-to-first-stage covers create (07-01 pin)
- Adiar input has no min attribute (no client "tomorrow"); the server's future-date refusal renders verbatim

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Pinned follow-up strings needed payload slots the projection lacked**
- **Found during:** Task 1 (EventosPanel design against the 07-02 wire contract)
- **Issue:** The plan/UI-SPEC pin 'Follow-up pendente para {data}.' and 'Follow-up venceu há {X} dia(s).' and demand the panel never compute them client-side — but the 07-02 payload carries only the pendente/vencido BOOLEANS (no date, no day delta), and the acceptance gate bans `new Date(` in tracker components. The strings were unrenderable from the payload as shipped.
- **Fix:** derivar_campos (pure, hoje-injected) now also returns `followup_pendente_data` (earliest strictly-future followup) and `followup_vencido_dias` (days since the most recent lapse); CandidaturaDTO mirrors both; 2 offline vectors pin them. All date math stays server-side exactly like dias_para_prazo.
- **Files modified:** backend/app/tracker/service.py, backend/tests/test_tracker_service.py, frontend/src/api/client.ts
- **Verification:** test_followup_pendente_data_e_vencido_dias_derivados + test_followup_derivados_nulos_sem_followups pass; tracker trio 73 green
- **Committed in:** e185f13

**2. [Rule 1 - Bug] Missing imports failed the build gate**
- **Found during:** Task 1 verification (tsc TS2304/TS2552) and Task 3 verification (TS6133)
- **Issue:** RASTREADOR_LIMITE_CARGO and the ErrorPanel import were missing in CandidaturaForm/EventosPanel; RASTREADOR_ESTAGIO_ADD_CTA was imported-but-unused in TrackerHome (noUnusedLocals).
- **Fix:** imports corrected; build green. (One further missing import — RASTREADOR_LABEL_EMPRESA — was caught and fixed before the first build.)
- **Files modified:** frontend/src/components/tracker/CandidaturaForm.tsx, frontend/src/components/tracker/EventosPanel.tsx, frontend/src/pages/TrackerHome.tsx
- **Verification:** npm run build exits 0
- **Committed in:** e185f13, 132415f

**3. [Rule 2 - Missing critical functionality] Kanban renders the ACTIVE pipeline only; same-stage drops skip the mutation**
- **Found during:** Task 2 (board assembly against the resumo payload)
- **Issue:** The payload includes archived candidaturas and the plan is silent on filtering; rendering them in the working board makes closed applications draggable, contradicting D-04's archive-as-closure model. Additionally, the plan's literal onDragEnd ("call the onMover callback") would fire a no-op write on every intra-column visual sort.
- **Fix:** columns filter `arquivada` (the overview above keeps the full history, suffixed "(arquivada)"); onDragEnd guards `target === origem.estagio_id` with a comment. Both are minimal, commented, and UAT-visible.
- **Files modified:** frontend/src/pages/TrackerHome.tsx, frontend/src/components/tracker/KanbanBoard.tsx
- **Verification:** build green; archived rows remain visible in Visão geral
- **Committed in:** ae8a7ca

**4. [Rule 3 - Blocking] UI-SPEC's "adiar min = tomorrow" contradicts the plan's no-client-date-math gate**
- **Found during:** Task 1 (EventosPanel)
- **Issue:** The UI-SPEC suggests the adiar date input carry `min` = tomorrow's ISO built from local parts — which requires `new Date()` inside a tracker component, violating the plan's grep-pinned acceptance criterion (count must be 0).
- **Fix:** no min attribute; the comment points at the honest path — the server rejects past targets with the PT-BR erro envelope, which the panel renders verbatim (plan gate wins over UI-SPEC detail).
- **Files modified:** frontend/src/components/tracker/EventosPanel.tsx
- **Verification:** grep -c "new Date(" across frontend/src/components/tracker = 0
- **Committed in:** e185f13

---

**Total deviations:** 4 auto-fixed (2 Rule 2 missing-critical, 1 Rule 1 bug, 1 Rule 3 blocking)
**Impact on plan:** None negative — every acceptance criterion passes (build green after every task, tracker trio 73, full suite 516, all negative greps 0). Deviation #1 is the substantive one: it adds two server-computed fields to the as-built contract, pinned by tests, strictly additive to the wire shape.

## Issues Encountered
None beyond the auto-fixed deviations. The 07-01/07-02 as-built API matched the plan's expectations everywhere else (mover/editar/evento/followup/estagio/export envelopes consumed exactly as the 07-02 SUMMARY documented).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ready for 07-04 (entry doors): the prefill seam is live — CandidaturaForm initializes jd_texto from `valoresIniciais` and TrackerHome remounts it via `formKey`; the criar onSuccess consumes the prefill exactly as 07-01 declared. Note for 07-04: the create wire contract carries NO idioma key, so prefill.language has no form field to land on as-is — 07-04 should either extend the form deliberately or drop that part of the seam (extra=forbid would 422 otherwise)
- 07-04's Respostas association consumes `registrarEvento` + `fetchTrackerResumo` as-is; the '(arquivada)' picker suffix string (RASTREADOR_ARQUIVADA_SUFIXO) already exists in constants
- 07-05 UAT routing: drag feel, keyboard DnD end-to-end, amber/red chip rendering, and export click-through are human_judgment items (coverage D5) — the automated layer proves configuration + compilation only
- Blockers: none (deterministic module — OpenRouter credit exhaustion is irrelevant here, D-15)

## Self-Check: PASSED

- All 6 created components + TrackerHome/client.ts/constants found on disk; backend service.py + test vectors found
- Commits e185f13, ae8a7ca, 132415f all ancestors of HEAD
- Measured commits: git rev-list --count 2f664c9..HEAD = 3 (matches frontmatter actuals; ledger .git/gsd-plan-head-before-07-03)
- Verifications: npm run build green after every task; tracker trio 73 passed; full offline suite 516 passed, 9 deselected (llm marker)

---
*Phase: 07-application-tracker-pipeline-follow-up*
*Completed: 2026-11-11*
