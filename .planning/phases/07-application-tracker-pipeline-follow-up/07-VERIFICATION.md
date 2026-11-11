---
phase: 07-application-tracker-pipeline-follow-up
verified: 2026-11-11T12:12:56Z
status: human_needed
score: 9/12 must-haves verified
behavior_unverified: 3
overrides_applied: 0
covered_files: [".gitignore", ".planning/phases/07-application-tracker-pipeline-follow-up/07-01-PLAN.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-01-SUMMARY.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-02-PLAN.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-02-SUMMARY.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-03-PLAN.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-03-SUMMARY.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-04-PLAN.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-04-SUMMARY.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-05-PLAN.md", ".planning/phases/07-application-tracker-pipeline-follow-up/07-05-SUMMARY.md", "backend/app/config.py", "backend/app/main.py", "backend/app/routes/tracker.py", "backend/app/tracker/db.py", "backend/app/tracker/models.py", "backend/app/tracker/service.py", "backend/tests/test_tracker_api.py", "backend/tests/test_tracker_db.py", "backend/tests/test_tracker_service.py", "frontend/package.json", "frontend/src/App.tsx", "frontend/src/api/client.ts", "frontend/src/components/ResumeResult.tsx", "frontend/src/components/tracker/CandidaturaCard.tsx", "frontend/src/components/tracker/CandidaturaForm.tsx", "frontend/src/components/tracker/ContadoresGrid.tsx", "frontend/src/components/tracker/EstagioManager.tsx", "frontend/src/components/tracker/EventosPanel.tsx", "frontend/src/components/tracker/KanbanBoard.tsx", "frontend/src/constants/ui.ts", "frontend/src/pages/CandidaturaHome.tsx", "frontend/src/pages/CurriculoHome.tsx", "frontend/src/pages/TrackerHome.tsx"]
covered_digest: "v3:sha256:91119b3c001182c0cc3e35eee824df2c46a39875423ccbdff03416fcb03606ca"
behavior_unverified_items:
  - truth: "User drags a candidatura card onto another stage column (or an empty one) and the stage persists after reload; keyboard-only DnD works via the dnd-kit keyboard sensor; clicking a card still opens it"
    test: "On the running dev servers, Rastreador page with 2-3 candidaturas: drag a card between stage columns, reload — the card renders in the new column; drag into an EMPTY column — drop accepted and persists; Tab to a card drag handle, arrow-key move, release; click a card body — detail opens"
    expected: "Every drop persists through the mover mutation + ['tracker'] refetch (no optimistic-only render); keyboard path mirrors pointer path; sub-8px clicks open the detail instead of starting a drag"
    why_human: "Drag feel, activation threshold, and drop acceptance are browser-interaction behaviors; the repo has no JS test runner (tsc build is the gate), so dnd-kit sensor config (grep-pinned) and compilation are the ceiling of automated proof"
  - truth: "Overview renders server-supplied day deltas 'vence em X dias' in the amber family (0<=dias<=3) and 'venceu há X dias' in the red family (negative), each with an sr-only suffix; no automatic stage/arquivo action fires on vencido"
    test: "With one candidatura prazo 2 days out and one prazo last week, inspect the overview rendering and colors; confirm no stage change or archival happened to the overdue row"
    expected: "Amber family chip for the near prazo, red family for the past one, sr-only text ' (próximo do prazo)'/' (vencido)' present, overdue row untouched (archive manual-only)"
    why_human: "Color-family rendering and 'never color-alone' are visual properties grep/build cannot affirm; the class constants and payload wiring are pinned, the rendered look is not"
  - truth: "The three D-13 doors work click-through: manual form create+reload persistence, Currículo 'Registrar candidatura' → prefilled Rastreador form consumed exactly once, Respostas 'Associar' → metadata-only 'resposta' event visible in EventosPanel"
    test: "Create a candidatura via the form and reload (persist); generate a resume, click 'Registrar candidatura', confirm the JD lands prefilled and a second nav visit shows a clean form; submit an answer, associate it, confirm the event appears in EventosPanel and contadores move"
    expected: "Row survives reload; prefill lands once and clears; the associated event renders with the fixed note 'Resposta registrada via módulo Respostas' and increments the follow-up anchor behavior"
    why_human: "Wiring is grep-verified (App/CurriculoHome/ResumeResult/TrackerHome/CandidaturaHome) and the API roundtrip is test-pinned, but the end-to-end click-through across views is browser UX no automated check in this repo exercises"
human_verification:
  - test: "Kanban drag (D-14) — create 2-3 candidaturas across stages; drag a card from one stage column to another; reload the page: the card renders in the new column; drag a card into an EMPTY column: the drop is accepted and persists"
    expected: "Persisted stage after reload (not optimistic-only); empty-column drop accepted; same-stage visual sorts do not fire writes"
    why_human: "Drag feel/activation and drop acceptance are browser behaviors; automation ceiling is the pinned dnd-kit config + green build"
  - test: "Keyboard-only DnD (D-14/Pitfall 4) — Tab to a card's drag handle, activate, arrow-key it to another column, release — same persistence as check 1; then click a card body: its detail opens"
    expected: "KeyboardSensor path works end-to-end; clicks survive the distance-8 pointer sensor"
    why_human: "Focus order and key semantics are interaction-level"
  - test: "Amber/red prazo highlights (D-09/D-11) — one candidatura prazo 2 days out, one prazo last week: overview shows 'vence em 2 dias' (amber family) and 'venceu há 1 dia' (red family); sr-only suffix present; the overdue item triggered NO automatic stage change or archival"
    expected: "Both chips render from dias_para_prazo with sr-only text; overdue row unchanged (archive is manual-only)"
    why_human: "Color rendering and never-color-alone are visual properties"
  - test: "Follow-up lifecycle click-through (D-10/D-12) — schedule a follow-up dated tomorrow (pendente chip), execute it from the panel (becomes a dated event in EventosPanel), confirm the 'considerar follow-up' badge appears on a candidatura whose last event is 7+ days old"
    expected: "Pendente → executado transition visible in the UI; badge renders exactly from sugerir_followup"
    why_human: "The state machine is pytest-pinned (test_followup_transicao_pendente_executar_adiar, N=7 boundary vectors); the panel click-through is UX"
  - test: "Door 2 click-through (D-13) — generate a resume on the Currículo page, click 'Registrar candidatura' on the result, land on the Rastreador form with the JD prefilled; navigate away and back via the nav: the form is clean"
    expected: "JD prefilled once; prefill consumed exactly once (consume-and-clear effect); empresa/cargo empty for the user to type"
    why_human: "Cross-view state hand-off UX; wiring is grep-verified but the click-through is not automatable in this repo"
  - test: "Door 3 click-through (D-13/D-08) — submit an answer on the Respostas page, pick a candidatura in the 'Associar à candidatura' picker, confirm; open that candidatura's EventosPanel"
    expected: "'Resposta' event listed with today's date, the answer's language, and the fixed note 'Resposta registrada via módulo Respostas'; no question/answer text anywhere; contadores/kanban refresh via ['tracker'] invalidation"
    why_human: "Association UX across views; payload shape is grep-verified and the 'resposta' literal is test-pinned, but the end-to-end click-through is not"
---

# Phase 7: Application Tracker — Pipeline & Follow-up Verification Report

**Phase Goal:** The user tracks real job applications end-to-end — creates candidaturas (one application = one job posting), moves them through a personal kanban of customizable stages, records dated metadata-only events whose counters (currículos enviados, entrevistas, ativas) are derived mechanically from those events, sees return deadlines sorted by proximity with amber/red day-delta highlights, and schedules/executes/postpones follow-ups — all persisted in a local SQLite store, 100% deterministic with zero LLM calls, reachable from three doors (tracker form, Currículo result prefill, Respostas association).
**Verified:** 2026-11-11T12:12:56Z
**Status:** human_needed
**Re-verification:** No — initial verification (no previous VERIFICATION.md existed)

> **MVP-mode gate note (escalation):** ROADMAP declares `mode: mvp` for this phase, and the canonical User Story format gate (`user-story.validate`) returned `valid: false` — the goal is not in "As a [role], I want to [capability], so that [outcome]." form. Verification proceeded on the orchestrator's explicit instruction, using the roadmap's six Success Criteria as the User Flow Coverage contract (they enumerate the user-facing outcome clauses precisely). If canonical User Story format is wanted for the archive, run `/gsd:mvp-phase 7`. No verification conclusion below depends on the goal's phrasing.

> **Post-verification-review note:** 07-REVIEW.md found 2 criticals; both are FIXED and test-pinned in the current codebase — CR-01 (`check_same_thread=False` per-request confinement, commit 42dc4e1, present in `backend/app/tracker/db.py:104` with factory-spy + behavioral cross-thread pins) and CR-02 (`DataISO` AfterValidator calendar gate, commit 2a1ddcc, present in `backend/app/tracker/models.py:38-50` on all five date field sites). 10 lower-severity findings remain open per 07-REVIEW-DISPOSITION.md — see Known Open Findings below; none of them fails a phase must-have.

## Goal Achievement

### User Flow Coverage (MVP mode — mapped from the six Success Criteria)

| # | User-flow step (from SC) | Expected | Evidence in codebase | Status |
|---|--------------------------|----------|----------------------|--------|
| 1 | User creates/edits candidaturas with essential + detail fields; archive-only closure | 11-field form, edit PATCH semantics, `arquivada` flag, no destructive path | `CandidaturaForm.tsx` (11 fields, maxLength mirrors 200/200/200/2000/100/200/5000/20000 at ui.ts:559-566), `TrackerHome.tsx` criar/editar/alternarArquivada mutations, `service.py` editar_candidatura (None=untouched, A2 flag), `test_no_candidatura_removal_route` + `test_rotas_tracker_nao_tem_caminho_destrutivo` green; UI greps for remover/excluir/deletar candidatura = 0 matches | VERIFIED |
| 2 | User manages stage vocabulary and drags candidaturas between columns in a @dnd-kit kanban | add/rename/reorder/remove (blocked while referenced); drag persists | `service.py` criar/renomear/reordenar/remover_estagio + tests (test_remover_estagio_referenciado_bloqueado, test_remover_estagio_livre_mantem_ordem_contigua); `EstagioManager.tsx` renders the refusal verbatim via ErrorPanel; `KanbanBoard.tsx` DndContext distance-8 + KeyboardSensor + closestCorners + droppable empty columns + mover mutation, no optimistic update — **drag/keyboard interaction in a browser not test-exercised** | Split: stage engine VERIFIED; drag interaction PRESENT_BEHAVIOR_UNVERIFIED (human items 1-2) |
| 3 | Contadores computed server-side from dated events only; events metadata-only | enviados/entrevistas = COUNT(eventos), ativas = arquivada=0; no content column | `service.py` obter_resumo COUNT queries; test_contadores_derivam_somente_de_eventos + zero-state test; `ContadoresGrid.tsx` pure prop passthrough; eventos DDL exactly 6 metadata columns + `test_schema_v1_tem_exatamente_tres_tabelas` schema pin; association payload sends exactly tipo/data_evento/idioma/observacao (CandidaturaHome.tsx:130-134) | VERIFIED |
| 4 | Overview sorts by prazo proximity with amber/red day-deltas; follow-ups pendente until executed/postponed; N=7 deterministic badge | server-side ORDER BY, chip classes, re-date lifecycle, exact N=7 flip | `service.py` ORDER BY NULL-prazo-last + test_visao_geral_ordenada_por_proximidade_de_prazo; `CandidaturaCard.tsx` PrazoChip/FollowupBadge from payload only; test_followup_transicao_pendente_executar_adiar, N=7/6 boundary vectors, dias_para_prazo 0/-1/None vectors; sr-only constants ui.ts:682-683 — **rendered colors are a visual property** | Split: engine VERIFIED; amber/red rendering PRESENT_BEHAVIOR_UNVERIFIED (human item 3); lifecycle click-through human item 4 |
| 5 | User exports JSON + spreadsheet-friendly CSV from the UI; .db gitignored + env-overridable | base64 envelope + backend filename; BOM, ';', sanitization; data/ ignored | `service.py` exportar_json/exportar_csv (utf-8-sig, ';', _sanitizar_celula =+-@ apostrophe) + tests (BOM/sanitization/roundtrip/filename); `TrackerHome.tsx` export buttons → downloadConteudo(filename verbatim); config.py:66 TRACKER_DB env-overridable; .gitignore:18 `data/` | VERIFIED |
| 6 | Three doors feed the tracker behind a fifth nav item; no LLM in the module | manual form + Registrar prefill + Respostas association; D-15 clean | Door 1: TrackerHome form + roundtrip test; Door 2: ResumeResult.tsx:500,862-870 optional CTA → CurriculoHome.tsx:883-890 capturing closure → App.tsx:129-136 setTrackerPrefill+setView → TrackerHome.tsx:138-143 consume-once; Door 3: CandidaturaHome.tsx registrarEvento tipo 'resposta' metadata-only; NAV_ITEMS 5th entry (ui.ts:10) + App view union (App.tsx:72); `grep -rn "app\.llm" backend/app/tracker backend/app/routes/tracker.py` = 0 matches; suite runs offline (-m 'not llm') — **doors 2/3 click-through not browser-exercised** | Split: wiring VERIFIED; door click-throughs PRESENT_BEHAVIOR_UNVERIFIED (human items 5-6) |

### Observable Truths

| #   | Truth   | Status     | Evidence       |
| --- | ------- | ---------- | -------------- |
| 1 | User creates/edits candidaturas with all 11 D-06 fields and can only archive — no destructive path exists (SC-1, D-04) | ✓ VERIFIED | CandidaturaForm 11 fields + WR-01 maxLength mirrors; editar_candidatura None=untouched + A2 arquivada flag stamps/clears arquivada_em; test_no_candidatura_removal_route + test_rotas_tracker_nao_tem_caminho_destrutivo green; destructive-UI grep = 0 |
| 2 | Fresh TRACKER_DB auto-migrates to v1 (3 tables + 5 seeded stages) idempotently; FK on; env-overridable gitignored path (SC-5, D-01/D-02) | ✓ VERIFIED | db.py MIGRATIONS/aplicar_migracoes; test_tracker_db suite (migration/idempotency/seed/FK/env-override) green in the full run; .gitignore `data/`; config.py:66-67 |
| 3 | Contadores (enviados/entrevistas/ativas) computed server-side from persisted events only — never typed numbers (SC-3, D-07) | ✓ VERIFIED | obter_resumo COUNT(eventos tipo)/COUNT(arquivada=0); test_contadores_derivam_somente_de_eventos + test_resumo_zero_state_fresh_db; ContadoresGrid pure passthrough |
| 4 | Events store only metadata (data, tipo, idioma, observação) — never resume/answer content (SC-3, D-08) | ✓ VERIFIED | eventos DDL 6 metadata columns; schema pin test green; EventoRegistroRequest 4 fields; association payload exactly 4 fields with fixed observacao constant (ui.ts:551) |
| 5 | User manages stage vocabulary — add/rename/reorder; removal refused while referenced, no cascade (SC-2, D-05) | ✓ VERIFIED | service stage functions + reordenar 1..n transaction; test_remover_estagio_referenciado_bloqueado / test_remover_estagio_livre_mantem_ordem_contigua / test_reordenar_estagios_persiste_ordem green; EstagioManager renders the PT-BR refusal verbatim through ErrorPanel |
| 6 | User drags candidaturas between stage columns (incl. empty) in the @dnd-kit kanban; stage persists after reload; keyboard DnD works; clicks survive (SC-2, D-14) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | KanbanBoard.tsx pins PointerSensor distance-8, KeyboardSensor sortableKeyboardCoordinates, closestCorners, useDroppable empty columns, items = rendered array (Pitfall 10), mover mutation + invalidation, no optimistic update; no browser-interaction test exists (no JS runner by design) — see human items 1-2 |
| 7 | Overview sorts by prazo proximity, NULL last (SC-4, D-09) | ✓ VERIFIED | ORDER BY CASE NULL-last in obter_resumo and exportar_csv; test_visao_geral_ordenada_por_proximidade_de_prazo green |
| 8 | 'vence em X dias' amber (0..3) / 'venceu há X dias' red (negative) with sr-only suffixes; no automatic action on vencido (SC-4, D-11) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Chip classes/formatarPrazoContagem/sr-only constants pinned (ui.ts:651-655, 682-683); PrazoChip selects purely from dias_para_prazo; no overdue hook exists anywhere in tracker routes (no auto-action by construction) — rendered look is visual, see human item 3 |
| 9 | Follow-ups pendente until executed/postponed; executar re-dates to hoje; adiar forward; deterministic N=7 suggestion badge (SC-4, D-10/D-11/D-12) | ✓ VERIFIED | Data-inferred lifecycle (no executada column, grep 0); test_followup_transicao_pendente_executar_adiar; test_sugestao_followup_no_limiar_exato_de_7_dias / test_sugestao_followup_abaixo_do_limiar_6_dias; followup_pendente_data / followup_vencido_dias server slots pinned |
| 10 | User exports everything as JSON + CSV (utf-8-sig BOM, ';' delimiter, formula sanitization) from the UI with backend-generated filenames (SC-5, D-03) | ✓ VERIFIED | exportar_json roundtrip test + exportar_csv BOM/sanitization tests + API transport pins (base64, filename tracker-YYYY-MM-DD.ext); TrackerHome export buttons pass filename verbatim to downloadConteudo |
| 11 | Three doors feed the tracker; prefill carries exactly {jd_texto, language}, consumed once, empresa/cargo user-typed; association records metadata-only 'resposta' event (SC-6, D-13/A9) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | All wiring grep-verified (ResumeResult optional CTA → CurriculoHome closure → App trackerPrefill → TrackerHome consume-once effect 138-143; CandidaturaHome payload exactly tipo/data_evento/idioma/observacao); API roundtrips test-pinned — cross-view click-through needs a browser, see human items 5-6 |
| 12 | House contracts + determinism: 200 envelope everywhere, extra=forbid 422s, sync def handlers, router before SPA mount, fifth nav item, zero LLM (SC-6, TRK-04) | ✓ VERIFIED | 15 422-vector tests + 5 not-found envelope tests green; test_handlers_are_sync_def_never_coroutines; test_router_registered_before_spa_mount (main.py:26 include_router before mount at :30); NAV_ITEMS ui.ts:10 + App.tsx:72; LLM grep = 0; full suite runs offline (522 passed, 9 deselected llm-marker) |

**Score:** 9/12 truths verified (3 present, behavior-unverified)

**Coincidental-reliance check (advisory, #1955):** reviewed the passing boundary vectors — the N=7 flip and pendente→executar→adiar vectors inject `hoje` explicitly and the production routes pass `date.today()` through the same `derivar_campos`/selector the tests call (endogenous but declared: `hoje` is an explicit parameter everywhere, not an implicit ordering). No undeclared-precondition, incidental-ordering, or fixture-only flags.

### Required Artifacts

| Artifact | Expected    | Status | Details |
| -------- | ----------- | ------ | ------- |
| `backend/app/tracker/db.py` | conectar() factory + migrations + seed | ✓ VERIFIED | 127 lines; PRAGMA foreign_keys/busy_timeout/WAL; CR-01 check_same_thread=False; v1 DDL + 5 seed rows; importable TRACKER_DB from config |
| `backend/app/tracker/models.py` | all 8 request DTOs, extra=forbid | ✓ VERIFIED | 152 lines; ConfigDict(extra="forbid") on every model; Literal modalidade/tipo; CR-02 DataISO calendar gate |
| `backend/app/tracker/service.py` | full deterministic service | ✓ VERIFIED | 760 lines; lifecycle, events, stage mgmt, derivar_campos (pure, hoje-injectable), export builders; parameterized `?` SQL only |
| `backend/app/routes/tracker.py` | 11-route surface, 200 envelope | ✓ VERIFIED | 343 lines; sync def only; yield dependency with auto-migration; zero bare 404; S8 base64 export transport |
| `backend/tests/test_tracker_db.py` | migrations/seed/FK/env pins | ✓ VERIFIED | 186 lines, green (incl. CR-01 cross-thread pins) |
| `backend/tests/test_tracker_api.py` | envelope/422/not-found/export pins | ✓ VERIFIED | 571 lines, green; 15 422 vectors, 5 not-found envelopes, D-04 pin, CR-02 422 vectors |
| `backend/tests/test_tracker_service.py` | boundary vector suite | ✓ VERIFIED | 506 lines, green; N=7/6, prazo ±0, lifecycle transition, stage blocking, BOM/sanitization |
| `frontend/src/pages/TrackerHome.tsx` | fifth-view assembly | ✓ VERIFIED | 632 lines; query/mutations/invalidations/detail/export/stage manager; consume-once prefill |
| `frontend/src/components/tracker/*` (6) | board, card, form, panel, manager, contadores | ✓ VERIFIED | 100-322 lines each; all substantive, all imported and rendered by TrackerHome |
| `backend/tests/test_tracker_api.py (expanded)` — 07-02 artifact label | expanded API suite | ✓ VERIFIED (label artifact) | The plan wrote the label "(expanded)" into the artifact path; the literal-path checker reports "File not found". The real file exists (571 lines) and passes — false negative from plan wording, not a missing artifact |

### Key Link Verification

The `verify.key-links` checker returned parser-level false negatives on all plans (`from`/`to` carry descriptive labels like "backend/app/main.py" / "...client.ts tracker DTOs" rather than bare paths). Every link was verified manually:

| From | To  | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| backend/app/main.py | backend/app/routes/tracker.py | include_router before SPA mount | ✓ WIRED | main.py:26 `app.include_router(tracker_router)` precedes the FRONTEND_DIST mount at :30-31; test_router_registered_before_spa_mount green |
| frontend/src/api/client.ts | backend tracker envelope | drift-gate banner mirror | ✓ WIRED | banner at client.ts:176-177/284 naming models.py + routes/tracker.py; tsc -b green (build run) |
| frontend/src/constants/ui.ts NAV_ITEMS | frontend/src/App.tsx view union | as-const 'rastreador' id | ✓ WIRED | ui.ts:10 fifth entry; App.tsx:72 union includes 'rastreador'; App.tsx:122-128 renders TrackerHome |
| backend/app/config.py TRACKER_DB | backend/app/tracker/db.py conectar() | env-overridable path | ✓ WIRED | config.py:66-67; db.py:34 import + :104 connect; tests point TRACKER_DB at tmp_path |
| routes/tracker.py | tracker/service.py | yield dependency, service raises / route owns envelope | ✓ WIRED | every handler Depends(get_tracker_db); TrackerErro → PT-BR envelope, raw → logger.error |
| KanbanBoard onDragEnd | POST /candidaturas/{id}/mover | useMutation + invalidateQueries(['tracker']) | ✓ WIRED | TrackerHome mover mutation :200-212; KanbanBoard handleDragEnd :102-110; same-stage guard; no optimistic update |
| ResumeResult 'Registrar candidatura' | App trackerPrefill + setView | optional callback threaded through CurriculoHome | ✓ WIRED | ResumeResult.tsx:500,559-560,862-870; CurriculoHome.tsx:152,883-890; App.tsx:129-136; TrackerHome consume-once :138-143 |
| CandidaturaHome association | POST /candidaturas/{id}/eventos tipo 'resposta' | registrarEvento + ['tracker'] invalidation | ✓ WIRED | CandidaturaHome.tsx:130-143; 4-field payload with fixed observacao; invalidateQueries at :143 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| ContadoresGrid | contadores | payload.contadores ← SQL COUNT over eventos/candidaturas | Yes | ✓ FLOWING |
| PrazoChip / FollowupBadge | dias / sugerir | payload.dias_para_prazo / sugerir_followup ← derivar_campos(date math server-side) | Yes | ✓ FLOWING |
| EventosPanel follow-up lines | followup_pendente_data / followup_vencido_dias | server-computed slots (pytest-pinned) | Yes | ✓ FLOWING |
| Kanban columns | candidaturas per estagio | payload.candidaturas filtered by estagio_id | Yes | ✓ FLOWING |
| CandidaturaHome picker | candidatura options | fetchTrackerResumo under shared ['tracker'] key | Yes | ✓ FLOWING |
| Export downloads | conteudo_base64/filename | exportar_json/exportar_csv bytes, backend-generated filename | Yes | ✓ FLOWING |

No static fallbacks, hardcoded literals, or hollow props found in the tracker data paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full offline suite (every suite, tracker included) | `cd backend && uv run pytest -q` | 522 passed, 9 deselected in 26.44s | ✓ PASS |
| Frontend build (tsc -b + vite, the DTO drift gate) | `cd frontend && npm run build` | exit 0, built in 296ms | ✓ PASS |
| Tracker test inventory | `pytest tests/test_tracker_*.py --collect-only -q` | 79 tests collected | ✓ PASS |
| N=7 suggestion boundary + prazo ±0 + lifecycle + stage blocking + BOM vectors exist | collect-only grep | all named vectors present (test_sugestao_followup_no_limiar_exato_de_7_dias, test_dias_para_prazo_menos_um_e_vencido, test_followup_transicao_pendente_executar_adiar, test_visao_geral_ordenada_por_proximidade_de_prazo, test_remover_estagio_referenciado_bloqueado, test_exportar_csv_bom_delimitador_e_sanitizacao, test_exportar_json_roundtrip_tres_tabelas) — all green inside the single full-suite run | ✓ PASS |
| Disabled-test scan on tracker suites | grep skip/todo patterns | 0 matches | ✓ PASS |

Full-suite discipline: the workspace suite ran exactly once this verification; no per-truth filtered re-runs.

### Probe Execution

No probes declared: PLAN/SUMMARY files mention no `probe-*.sh` and no conventional `scripts/*/tests/probe-*.sh` exists. Not applicable.

### Requirements Coverage

Phase requirement IDs are phase-derived (ROADMAP §Phase 7 Requirements; REQUIREMENTS.md carries no TRK-* rows — verified against the Traceability table, which maps 15 v1 requirements, none TRK-*). Cross-referenced against the ROADMAP section and the plans' frontmatter:

| Requirement | Source Plan(s) | Description (ROADMAP §Phase 7) | Status | Evidence |
| ----------- | -------------- | ------------------------------ | ------ | -------- |
| TRK-01 | 07-01, 07-05 | SQLite persistence layer (migrations + seed + env path) | ✓ SATISFIED | Truth 2; test_tracker_db suite green |
| TRK-02 | 07-01, 07-02, 07-03, 07-05 | Rastreador nav + candidatura form + kanban + stage vocabulary | ✓ SATISFIED | Truths 1, 5, 6 (kanban interaction human-flagged), 11 |
| TRK-03 | 07-02, 07-03, 07-04 | D-06 field set + entry doors (prefill, association) | ✓ SATISFIED | Truths 1, 11 (door click-through human-flagged) |
| TRK-04 | 07-01, 07-02, 07-03, 07-04 | House envelope contracts (200 envelope, extra=forbid, sync handlers) | ✓ SATISFIED | Truth 12 |
| TRK-05 | 07-02, 07-03, 07-05 | Deadline/follow-up semantics (derived fields, N=7, lifecycle) + interaction UAT | ✓ SATISFIED | Truths 7-9 (rendering/lifecycle click-through human-flagged) |
| TRK-06 | 07-02, 07-05 | JSON+CSV export + phase gate | ✓ SATISFIED | Truth 10; gate re-run green this verification |
| HIST-01 | (REQUIREMENTS.md v2 conditional) | Application history log — "only if the user feels the tracker pain" | ✓ SATISFIED (materialized) | The tracker + full JSON/CSV export (three-table dump incl. eventos) materializes the application-history need this row reserved; no REQUIREMENTS.md edit required (conditional row, phase-derived contract per orchestrator note) |

**Orphaned requirements:** none — every TRK ID declared across the five plans' `requirements:` fields is accounted for above; REQUIREMENTS.md maps no additional IDs to Phase 7.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| backend/tests/test_tracker_db.py | TRK-01 | 14+ | 0 | No | Value (user_version, table set, row counts, pragma values) | SUFFICIENT |
| backend/tests/test_tracker_api.py | TRK-02/03/04/06 | 37+ | 0 | No | Value/Behavioral (envelope shapes, 422 vectors, BOM bytes, route-order pin) | SUFFICIENT |
| backend/tests/test_tracker_service.py | TRK-05/06 | 30 | 0 | No | Value/Behavioral (exact-day boundaries, transition sequences, BOM/sanitization) | SUFFICIENT |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0 (tests build their own tmp_path fixtures; no system-generated expected values). **Insufficient assertions:** 0 — requirement-linked boundaries are pinned at value level (exact day counts, exact BOM bytes, exact envelope shapes), not existence-only.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Debt markers (TBD/FIXME/XXX/HACK/unreferenced PLACEHOLDER) across all 24 covered implementation files | none | PLACEHOLDER grep matches are legitimate UI input `placeholder=` attributes and constant names, not stub markers |
| — | — | Empty implementations / console.log-only handlers in tracker code | none | The two `return null` instances in CandidaturaCard are null-guards for absent chips (no prazo / no suggestion), correct behavior |
| frontend/src/pages/TrackerHome.tsx | 497 | `link_vaga` rendered as a raw anchor `href` — `javascript:`/`data:` scheme sink (ledger WR-04) | ⚠️ Warning | Independently confirmed in current code; known open review finding (warning severity per 07-REVIEW-DISPOSITION.md); does not fail any phase must-have, but the developer should dispose it (scheme allow-list) |

### Decision Coverage (gate #2492)

All trackable CONTEXT.md decisions are honored by shipped artifacts — 16/16 honored, 0 not honored.

### Known Open Findings (from the phase's own review — informational, ledgered in 07-REVIEW-DISPOSITION.md)

Both criticals are FIXED and test-pinned (CR-01 commit 42dc4e1, CR-02 commit 2a1ddcc — verified present in current code and green in this verification's run). 10 lower-severity findings remain open: WR-01 (lapsed follow-up permanently unresolvable), WR-02 (follow-up controls vanish on the due day), WR-03 (CSV guard misses tab/CR prefix bypass), WR-04 (link_vaga href scheme sink — confirmed above), WR-05 (edit form cannot clear optional fields), IN-01..IN-05 (dead field, migration atomicity claim, env-var import crash, client-sourced association date, unused prop). None blocks a phase must-have; the ledger is the owner of their disposition. No later phase in the milestone covers them (Phase 7 is the last phase), so they must be resolved or explicitly dispositioned before milestone close.

### Human Verification Required

Six items (the four deferred interactions from 07-05-SUMMARY.md + the two D-13 door click-throughs deferred by 07-04's coverage D3). Resume action per run convention: `/gsd:verify-work 7`.

1. **Kanban drag + persistence + empty-column drop (D-14)** — drag a card between columns, reload, confirm persistence; drag into an empty column, confirm acceptance + persistence.
2. **Keyboard-only DnD + click survival (D-14/Pitfall 4)** — keyboard-move a card; click a card body opens the detail.
3. **Amber/red prazo chips + sr-only + no auto-archival (D-09/D-11)** — near-past and future prazos render the right families with sr-only text; the overdue row is untouched.
4. **Follow-up lifecycle click-through (D-10/D-12)** — tomorrow-dated follow-up shows pendente; executar produces a dated event; 7+-day-stale candidatura shows the 'considerar follow-up' badge.
5. **Door 2 click-through (D-13)** — 'Registrar candidatura' on the Currículo result lands on a JD-prefilled form, consumed once (clean form on the second nav visit); empresa/cargo stay empty.
6. **Door 3 click-through (D-13/D-08)** — associating an answer records a metadata-only 'resposta' event (fixed note, no answer text) visible in EventosPanel; contadores refresh.

### Gaps Summary

No gaps. Every must-have truth, artifact, and key link is present, substantive, and wired; all deterministic behaviors are pinned by 79 tracker tests inside a green 522-test offline suite, and the frontend build is green on the current post-fix codebase. The goal is not yet closable as `passed` only because six browser-level interaction/click-through behaviors remain unexercised by automation (structural: this repo deliberately has no JS test runner — `tsc -b` is the frontend gate). They are recorded above for human verification per the run convention; none is a functional defect suspect — each has its underlying server/wiring behavior test-pinned or grep-pinned.

---

_Verified: 2026-11-11T12:12:56Z_
_Verifier: Claude (gsd-verifier)_
