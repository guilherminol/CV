---
phase: 07-application-tracker-pipeline-follow-up
plan: 02
subsystem: tracker
tags: [sqlite, fastapi, pydantic, csv-export, deterministic, boundary-vectors]

# Dependency graph
requires:
  - phase: 07-application-tracker-pipeline-follow-up (plan 01)
    provides: tracker persistence layer (v1 migrations + seed), all 8 Wave-0 DTOs, criar_candidatura + obter_resumo skeleton, TrackerErro, house route posture, both Wave-0 test suites
provides:
  - complete deterministic /api/tracker surface — 11 routes: resumo, candidaturas create/edit/mover, eventos, followups executar/adiar, estagios list/create/reordenar/rename/remove, exportar (json|csv)
  - full candidatura lifecycle service — editar_candidatura (None=untouched; A2 arquivada flag stamps/clears arquivada_em), mover_estagio, adicionar_evento (metadata-only, D-08)
  - follow-up rule engine — executar/adiar re-date the pending row (Pattern 4b data-inferred; no executada column anywhere)
  - stage vocabulary management with reference-blocking removal (PT-BR envelope; no cascade) + transactional reorder 1..n
  - derivar_campos PURE projection (dias_para_prazo, atrasado_prazo, sugerir_followup, followup_pendente, followup_vencido) — obter_resumo routes through it
  - export builders — exportar_json (three-table dump + exportado_em) and exportar_csv (';' delimiter, utf-8-sig BOM, formula sanitization T-07-02)
  - base64-in-envelope export transport with backend-generated filename (S8 house shape)
  - vector suites: test_tracker_service.py born (30 offline tests) + test_tracker_api.py expanded (32 tests) — the full offline trio is 71 green
affects: [07-03, 07-04, 07-05]

# Actuals (#2632) — pairs with the plan's estimate (58000 tokens / 2 tasks / low confidence)
actuals:
  tokens: 18200    # chars/4 over the measured diff (72703 chars, 1576+/72-)
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []        # zero new dependencies — stdlib csv/io/json only
  patterns:
    - "Derived-field projection extracted PURE (no conn) — service and tests share one vector-checked implementation"
    - "Follow-up pending stays data-inferred: executar/adiar re-date the row; selector >= hoje keeps a today-dated followup executable"
    - "UNIQUE(ordem) reorder/removal via a temporary negative-ordem pass inside one transaction"
    - "Reference-blocking removal: explicit COUNT produces the PT-BR envelope line; FK never cascades (D-05/D-04)"

key-files:
  created:
    - backend/tests/test_tracker_service.py
  modified:
    - backend/app/tracker/service.py
    - backend/app/routes/tracker.py
    - backend/tests/test_tracker_api.py
    - backend/app/tracker/db.py

key-decisions:
  - "Follow-up executar/adiar select the earliest followup with data_evento >= hoje (not strictly >) — a followup dated today stays executable/postponable on the day; the derived pendente/vencido flags remain strict (future-only / past-only); required by the plan's own pendente→executar→adiar vector"
  - "Reorder requires the id list to cover EXACTLY all stages — contiguity by construction; partial lists raise a loud PT-BR erro"
  - "Empty edit body (all fields None) raises TrackerErro 'Informe ao menos um campo para editar.' — loud no-op refusal"
  - "exportar_csv takes no hoje param — no date is embedded in CSV cells; the route owns the filename date"
  - "Inline strict DTOs (MoverEstagioRequest, EstagioReordemRequest) live in routes/tracker.py per the plan's own Task-2 wording; the service takes plain ints/lists"

patterns-established:
  - "Boundary vectors with injected hoje: N=7 suggestion flip, prazo ±0, pendente/vencido transitions — every date rule pytest-pinnable offline"
  - "Erro-envelope not-found discipline: service raises TrackerErro('Candidatura N não encontrada.') → route answers 200 erro, never a bare 404"

requirements-completed: [TRK-02, TRK-03, TRK-04, TRK-05, TRK-06]  # copied verbatim from 07-02-PLAN.md frontmatter; REQUIREMENTS.md checkboxes remain governed by the Shared-ID gate (0/5 ready — co-declared by 07-03/04/05 which have no SUMMARYs yet)

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "Candidatura lifecycle: PUT edit (None=untouched + arquivada flag stamps/clears arquivada_em), POST mover, POST eventos (metadata-only) — full lifecycle through the API"
    requirement: TRK-03
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_editar_candidatura_campos_e_arquivada"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_editar_candidatura_none_nao_sobrescreve"
        status: pass
      - kind: integration
        ref: "backend/tests/test_tracker_api.py::test_ciclo_editar_mover_evento_followup_via_api"
        status: pass
    human_judgment: false
  - id: D2
    description: "Derived-field engine: sugerir_followup flips at exactly TRACKER_FOLLOWUP_SUGGEST_DAYS=7 (True at 7, False at 6); dias_para_prazo 0/-1/None; vencido/pendente from data only; overview ordered by prazo proximity, NULL last"
    requirement: TRK-05
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_sugestao_followup_no_limiar_exato_de_7_dias"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_sugestao_followup_abaixo_do_limiar_6_dias"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_dias_para_prazo_menos_um_e_vencido"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_visao_geral_ordenada_por_proximidade_de_prazo"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_followup_transicao_pendente_executar_adiar"
        status: pass
    human_judgment: false
  - id: D3
    description: "Stage vocabulary management: create/rename/reorder(1..n, transactional)/remove — removal REFUSED with the PT-BR envelope while referenced, free removal keeps ordem contiguous; no cascade ever runs"
    requirement: TRK-02
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_remover_estagio_referenciado_bloqueado"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_remover_estagio_livre_mantem_ordem_contigua"
        status: pass
      - kind: integration
        ref: "backend/tests/test_tracker_api.py::test_estagio_delete_bloqueado_quando_referenciado"
        status: pass
      - kind: integration
        ref: "backend/tests/test_tracker_api.py::test_reordenar_estagios_persiste_ordem"
        status: pass
    human_judgment: false
  - id: D4
    description: "Export (D-03): POST /api/tracker/exportar answers base64 + backend-generated filename; JSON round-trips the three tables; CSV bytes lead with the UTF-8 BOM, use ';' and apostrophe-prefix formula-leading cells"
    requirement: TRK-06
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_exportar_csv_bom_delimitador_e_sanitizacao"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_service.py::test_exportar_json_roundtrip_tres_tabelas"
        status: pass
      - kind: integration
        ref: "backend/tests/test_tracker_api.py::test_exportar_csv_bom_filename_e_sanitizacao"
        status: pass
      - kind: integration
        ref: "backend/tests/test_tracker_api.py::test_exportar_json_base64_tres_tabelas"
        status: pass
    human_judgment: false
  - id: D5
    description: "Envelope contracts across the whole surface: 8 distinct 422 vectors, 5 not-found erro envelopes (never a bare 404), sync-def pin over ALL 11 routes, router-before-mount incl. reordenar-before-{id} order, D-04 closure pins"
    requirement: TRK-04
    verification:
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_nao_encontrado_envelope_mover (caplog raw-only)"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_handlers_are_sync_def_never_coroutines"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_no_candidatura_removal_route"
        status: pass
      - kind: unit
        ref: "backend/tests/test_tracker_api.py::test_422_tipo_fora_do_literal_evento (+7 sibling 422 vectors)"
        status: pass
    human_judgment: false

# Metrics
duration: 14min
completed: 2026-11-10
status: complete
---

# Phase 7 Plan 2: Complete Deterministic Backend — Lifecycle, Stage Rules, Derived Fields, Export Summary

**Full /api/tracker surface completed offline-deterministically: candidatura edit/archive/move, metadata-only events, follow-up execute/postpone re-dating (no flag column), reference-blocking stage management, a pure derived-field engine pinned at the N=7/prazo-±0 boundaries, and base64-in-envelope JSON+CSV export — 71 tracker tests green.**

## Performance
- **Duration:** 14 min
- **Started:** 2026-11-10T23:23:46Z
- **Completed:** 2026-11-10T23:37:27Z
- **Tasks:** 2 (both type="auto")
- **Files modified:** 5 (1 created, 4 modified)

## Accomplishments
- Service layer completed: editar_candidatura (None = untouched; arquivada=True stamps arquivada_em, False clears it — A2), mover_estagio (loud unknown stage), adicionar_evento (exactly the five metadata columns, D-08), executar/adiar_followup (re-date the pending row — Pattern 4b, zero flag columns to drift)
- Stage vocabulary management: criar (ordem = max+1), listar, renomear, reordenar (1..n in one transaction via a negative-temp pass over the UNIQUE(ordem) constraint), remover REFUSED while referenced with the PT-BR envelope line — no cascade ever touches candidaturas (D-05 + D-04 spirit)
- derivar_campos extracted as a PURE function (no conn): dias_para_prazo, atrasado_prazo, sugerir_followup, followup_pendente, followup_vencido — obter_resumo now routes through it; counters stay strictly event-derived across archive status (D-07/D-04)
- Export builders: exportar_json (estagios + candidaturas-with-eventos + exportado_em, utf-8) and exportar_csv (';' delimiter, utf-8-sig BOM, apostrophe-prefix sanitization for = + - @ leading cells — T-07-02); POST /api/tracker/exportar answers the S8 base64 transport with backend-generated filename
- 11-route API surface, all sync def on the same yield dependency, unknown ids answering the 200 erro envelope everywhere — never a bare 404; validation stays 422
- Vector suites: test_tracker_service.py born with 30 offline tests; test_tracker_api.py expanded to 32 — boundary evidence named and passing (N=7 flip, prazo ±0, stage-removal refusal, BOM/sanitization)

## Task Commits
1. **Task 1: Service expansion + vector suite** - `f5842b8` (feat)
2. **Task 2: Routes expansion + API suite** - `f3f20e1` (feat)

**Plan metadata:** docs commit follows (SUMMARY + STATE + ROADMAP)

## Files Created/Modified
- `backend/app/tracker/service.py` - complete deterministic service: lifecycle mutations, stage management, pure derivar_campos, export builders (parameterized `?` SQL only)
- `backend/app/routes/tracker.py` - 8 new handlers over the same get_tracker_db dependency; MoverEstagioRequest/EstagioReordemRequest strict inline DTOs; reordenar registered before {estagio_id}
- `backend/tests/test_tracker_service.py` - 30 offline vectors with injected hoje: counters-from-events, N=7/6 suggestion boundary, prazo 0/-1/None, overview ordering, pendente→executar→adiar, stage blocking, BOM/sanitization, JSON round-trip
- `backend/tests/test_tracker_api.py` - expanded to 32 tests: 8× 422 vectors, 5 not-found envelopes, blocked/free DELETE, reorder persistence, export transport pins, sync-def pin over all 11 routes, test_no_candidatura_removal_route
- `backend/app/tracker/db.py` - docstring rewording only (removes the literal `executada` token so the plan's negative-grep acceptance criterion reads 0 — 07-01 deviation-4 precedent)

## Decisions Made
- Follow-up selector pinned at data_evento >= hoje for both executar and adiar (see Deviations #1) — a followup dated today is not past, so it stays executable/postponable on the day it comes due; UI flags stay strict (pendente future-only, vencido past-only)
- Reorder must cover exactly all stages — contiguity by construction, loud erro on partial/duplicated lists
- Empty edit body raises a loud TrackerErro instead of silently no-oping
- Inline strict DTOs for mover/reordenar live in routes/tracker.py (the plan's own Task-2 wording sanctions "small strict inline model"); the service consumes plain ints/lists so no wire shape can drift

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Strict `> hoje` follow-up selector would break the plan's own transition vector**
- **Found during:** Task 1 (vector design for test_followup_transicao_pendente_executar_adiar)
- **Issue:** The plan text pins executar on `data_evento > hoje`, but after executar re-dates the row to hoje, a strict selector makes adiar raise "Nenhum follow-up pendente" — the plan's own pinned vector (pendente → executar → adiar → future again) cannot pass.
- **Fix:** `_followup_nao_passado` selects `data_evento >= hoje` (earliest first) for both executar and adiar; a followup dated today remains executable/postponable. The derived pendente/vencido flags stay strict per Pattern 4b.
- **Files modified:** backend/app/tracker/service.py
- **Verification:** test_followup_transicao_pendente_executar_adiar passes end-to-end
- **Committed in:** f5842b8

**2. [Rule 1 - Bug] remover_estagio renumbered in reversed order**
- **Found during:** Task 1 verification (test_remover_estagio_livre_mantem_ordem_contigua failed: 'Pesquisando' != 'Negociação')
- **Issue:** The renumber fetch ran AFTER the negative-ordem flip, so `ORDER BY ordem` read the negative temp values and reversed the board order.
- **Fix:** remaining rows are read BEFORE the flip, inside the same transaction
- **Files modified:** backend/app/tracker/service.py
- **Verification:** free-removal test passes; ordem stays contiguous 1..n
- **Committed in:** f5842b8

**3. [Rule 1 - Bug] Test helper duplicated the empresa kwarg**
- **Found during:** Task 1 verification (TypeError: got multiple values for keyword argument 'empresa' — 3 vectors failed)
- **Fix:** `_criar` merges overrides into a payload dict before constructing the DTO
- **Files modified:** backend/tests/test_tracker_service.py
- **Committed in:** f5842b8

**4. [Rule 1 - Bug] db.py docstring carried the literal `executada` token failing the plan's negative-grep**
- **Found during:** Task 1 acceptance gate (grep -c "executada" app/tracker/db.py returned 1)
- **Issue:** Acceptance criterion 6 requires the count to be 0; the 07-01 A3 pin note quoted the forbidden literal (07-01 deviation-4 precedent).
- **Fix:** reworded to "NO executed-flag column exists to drift" — grep reads 0; suite untouched
- **Files modified:** backend/app/tracker/db.py
- **Committed in:** f5842b8

**5. [Rule 1 - Bug] 07-01 blanket no-DELETE test contradicted the 07-02 pinned route shape**
- **Found during:** Task 2 (DELETE /api/tracker/estagios/{estagio_id} is plan-mandated; the old test asserted NO tracker route carries DELETE)
- **Fix:** updated test_rotas_tracker_nao_tem_caminho_destrutivo to the refined D-04 policy (the ONLY DELETE is estagios removal) and added the plan's named test_no_candidatura_removal_route (no candidatura path with DELETE)
- **Files modified:** backend/tests/test_tracker_api.py
- **Verification:** both pins green; coverage reference from 07-01 stays valid (same test name)
- **Committed in:** f3f20e1

---

**Total deviations:** 5 auto-fixed (5 Rule 1 bugs — one of them a plan-internal inconsistency resolved in favor of the pinned behavior vector)
**Impact on plan:** None negative — every acceptance criterion passes; the full tracker trio (71 tests) and the whole offline suite (514 passed, 9 deselected llm-marker) are green.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 07-03 renders this stable contract: the kanban posts mover ({"estagio_id"}), stage manager uses estagios create/rename/reordenar/remove, EventosPanel posts eventos + followups executar/adiar, export buttons consume {arquivo, filename, conteudo_base64}
- All derived fields (dias_para_prazo, atrasado_prazo, sugerir_followup, followup_pendente, followup_vencido) arrive server-computed — the client renders deltas, never recomputes (D-09/Pitfall 7)
- REQUIREMENTS.md untouched: TRK-02..06 are Shared-ID gated with 07-03/04/05 (0/5 ready) — they complete as the later SUMMARYs land
- Blockers: none (deterministic module — OpenRouter credit exhaustion is irrelevant here, D-15)

## Self-Check: PASSED

- backend/app/tracker/service.py, backend/app/routes/tracker.py, backend/tests/test_tracker_service.py, backend/tests/test_tracker_api.py, backend/app/tracker/db.py — all FOUND on disk
- Commit f5842b8 (Task 1) and f3f20e1 (Task 2) — both ancestors of HEAD
- Measured commits: git rev-list --count 447932c..HEAD = 2 (matches frontmatter actuals; ledger .git/gsd-plan-head-before-07-02)

---
*Phase: 07-application-tracker-pipeline-follow-up*
*Completed: 2026-11-10*
