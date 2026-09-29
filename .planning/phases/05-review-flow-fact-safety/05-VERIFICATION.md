---
phase: 05-review-flow-fact-safety
verified: 2026-09-29T19:21:57Z
status: passed
score: 23/34 must-haves verified
covered_files:
  - .planning/phases/05-review-flow-fact-safety/05-01-PLAN.md
  - .planning/phases/05-review-flow-fact-safety/05-01-SUMMARY.md
  - .planning/phases/05-review-flow-fact-safety/05-02-PLAN.md
  - .planning/phases/05-review-flow-fact-safety/05-02-SUMMARY.md
  - .planning/phases/05-review-flow-fact-safety/05-03-PLAN.md
  - .planning/phases/05-review-flow-fact-safety/05-03-SUMMARY.md
  - .planning/phases/05-review-flow-fact-safety/05-04-PLAN.md
  - .planning/phases/05-review-flow-fact-safety/05-04-SUMMARY.md
  - backend/app/resume/facts.py
  - backend/app/resume/pipeline.py
  - backend/app/routes/resume.py
  - backend/tests/test_comparison_vectors.py
  - backend/tests/test_resume_api.py
  - backend/tests/test_resume_pipeline.py
  - backend/tests/test_resume_regen_api.py
  - backend/tests/test_resume_regen_pipeline.py
  - frontend/src/api/client.ts
  - frontend/src/components/ComparisonPanel.tsx
  - frontend/src/components/ConfirmStrip.tsx
  - frontend/src/components/ResumeResult.tsx
  - frontend/src/components/SectionEditor.tsx
  - frontend/src/components/SectionVersionsPanel.tsx
  - frontend/src/constants/ui.ts
  - frontend/src/lib/comparison.ts
  - frontend/src/pages/CurriculoHome.tsx
covered_digest: "v1:sha256:0038ba5004983219fa58d3fc5cf59e5ebb93f9173fa44955733290d461ad1c9c"
behavior_unverified: 11 # present + wired truths whose interactive/browser behavior no test exercises; each maps into the 5 human UAT areas below
overrides_applied: 0
re_verification: null
behavior_unverified_items:
  - truth: "05-01 #5 — result screen offers 'Regenerar seção' per generated section with the in-flight sibling-reassurance line; displayed text stays fully mounted during flight"
    test: "Generate a resume, click Regenerar seção, watch the section while the request is in flight"
    expected: "Button label swaps to the in-flight form, the sibling-reassurance line appears in the aria-live region, and the section text stays mounted"
    why_human: "React runtime interaction with no frontend test runner (project has none by design); in-flight UI states are only observable in a browser"
  - truth: "05-01 #7 — a failed section regen renders a red panel scoped inside the owning section with backend PT-BR erros[] verbatim, prior text still mounted; fetch-level failure shows the generic hint"
    test: "Force a regen failure (stop the backend mid-session, or a stage error) while a result is mounted"
    expected: "Red panel appears inside the owning section with the erros[] lines (or the generic hint on fetch failure); the prior section text stays mounted"
    why_human: "Failure-state rendering is browser runtime; the backend erro envelope is test-verified but the panel mount is not"
  - truth: "05-02 #2 — clicking Editar opens a pre-filled textarea; Salvar mounts the edited text, sets badge Editado, stacks the pre-edit version; Cancelar reverts when clean, shows the amber strip when dirty"
    test: "Edit each section type (Resumo whole / Experiência per entry / Habilidades per line), save, then cancel dirty"
    expected: "Editor pre-fills from displayed text; save flips the badge and the pre-edit text lands at the top of Versões; dirty cancel shows the inline strip"
    why_human: "Interactive state transitions in the browser — deferred at the 05-04 checkpoint (UAT area 1)"
  - truth: "05-02 #6 — one editor at a time; an open editor disables Exportar PDF / Gerar novamente / every Restaurar versão while its own section's Regenerar seção stays enabled and routes through the D-14 strip"
    test: "Open an editor and inspect every locked control; click Regenerar seção on the edited section"
    expected: "Export/full-regen/restore disabled; own-section regen enabled and shows the amber strip; sibling regens proceed directly"
    why_human: "The UI-SPEC locking matrix is an interaction table — deferred at the 05-04 checkpoint (UAT area 1)"
  - truth: "05-02 #7 — while any regen/export is pending, all mutation controls disable while Comparar and Versões toggles stay usable read-only"
    test: "Start a regen (LLM latency window) and try each control; also open an editor and try restore"
    expected: "Regenerar/Gerar novamente/Exportar/edit/restore/dica disabled; Comparar and Versões open and render during the flight"
    why_human: "Runtime gating during an in-flight async op — deferred at the 05-04 checkpoint (UAT area 1)"
  - truth: "05-02 #8 — 'Regenerar seção' on an Editado/dirty section shows the amber strip; confirming stacks first, then regenerates"
    test: "Edit a section, press Regenerar seção, confirm with 'Regenerar mesmo assim', then open Versões"
    expected: "Strip with the exact copy; the edit is in Versões; only that section changed"
    why_human: "Interaction-sequencing truth (SC4) — deferred at the 05-04 checkpoint (UAT area 1)"
  - truth: "05-02 #9 — full 'Gerar novamente' with any Editado section asks once via the strip under the card header and stacks every section on confirm; disabled outright while an editor is open"
    test: "Edit a section, press Gerar novamente, confirm; then open an editor and try Gerar novamente again"
    expected: "Once-only strip; confirming leaves every section's prior text in Versões; the second attempt is disabled while the editor is open"
    why_human: "Interaction-sequencing truth (SC4) — deferred at the 05-04 checkpoint (UAT area 1)"
  - truth: "05-04 #1 — SC4 walkthrough passes end-to-end (edit → strip → confirm → only that section changes; restore stacks current first; dirty-cancel strip)"
    test: "Walk 05-VALIDATION.md §Manual-Only area 1 against the running app"
    expected: "Every SC4 matrix step behaves per the UI-SPEC interaction table"
    why_human: "The checkpoint itself is a human gate by design (05-04-PLAN checkpoint:human-verify); resolved-as-deferred per run convention"
  - truth: "05-04 #2 — SC3 walkthrough passes (amber marks + legend; editing away a suspect clears its mark; grounded section shows the loud-zero line; paraphrased company falls back to all entries)"
    test: "Walk 05-VALIDATION.md §Manual-Only area 2 in the browser"
    expected: "Marks, legend/zero framing, and fallback render as specified on real data"
    why_human: "Visual framing and recompute-on-edit are browser-render behaviors; the mechanics themselves are proven by the mirror vectors + node smoke"
  - truth: "05-04 #3 — SC2 walkthrough passes (edited text is exactly what the exported PDF and the ATS self-check survival rows show)"
    test: "Edit a section, Exportar PDF, compare the PDF text and the self-check rows against the edited screen"
    expected: "PDF and survival rows reflect the edited text with no extra step"
    why_human: "Real-PDF inspection on the shipped artifact; the code path (export posts resultado.secoes) is grep-verified"
  - truth: "05-04 #4 — policy line visible; refreshing returns to the last generated result, unedited"
    test: "Confirm the policy line under the card header; refresh the page"
    expected: "Line visible whenever a result is mounted; refresh returns to the plain generated result with edits discarded"
    why_human: "Visual presence + browser session lifecycle — deferred at the 05-04 checkpoint (UAT area 4)"
human_verification:
  - test: "SC4 locking matrix (UAT area 1) — generate a resume, then: edit a section → Regenerar seção shows the amber strip → Regenerar mesmo assim → the edit appears in Versões and only that section changed; restore a version (current text stacks first); dirty-cancel shows its strip; full Gerar novamente with edits asks once and stacks every section; with an editor open, Exportar PDF / Gerar novamente / Restaurar versão are disabled while the section's own Regenerar seção stays enabled; during a pending regen, edit/restore/dica controls disable while Comparar/Versões stay usable; the in-flight line names the section and the text stays mounted; a failed regen shows the section-scoped red panel with prior text mounted"
    expected: "Every step matches the UI-SPEC interaction table; nothing is ever silently destroyed"
    why_human: "Interaction-sequencing truths in the browser; the project has no frontend test runner by design, and the CR-01 lock layers' semantic correctness was explicitly routed here by the review fix"
  - test: "SC3 comparison framing (UAT area 2) — expand Comparar com o perfil on a section with foreign tokens: amber marks + D-11 legend; edit the text to remove a suspect → mark disappears on reopen; a fully grounded section shows the loud-zero line; a paraphrased company renders ALL profile entries with the neutral note"
    expected: "Suspicion framing reads as user-judged, not verdict; marks never appear in the card body"
    why_human: "Visual outcome on real data; mechanics proven (mirror vectors + node smoke in this verification), the seeing is not"
  - test: "SC2 edits→export (UAT area 3) — edit a section, Exportar PDF, confirm the PDF text and the ATS self-check survival rows reflect the edited text"
    expected: "Edits flow to export/self-check with zero extra steps"
    why_human: "Requires inspecting the real downloaded PDF and rendered panel"
  - test: "Policy visibility + refresh (UAT area 4) — confirm the permanent policy line 'Edições valem apenas para esta execução — atualizar a página descarta.' under the card header; refresh the page"
    expected: "Line always visible with a result mounted; refresh returns to the plain generated result, unedited (D-01/D-02)"
    why_human: "Visual presence and browser session lifecycle"
  - test: "Backstop: disclosures-open readability (UAT area 5) — open editor + comparison + versions on one section (plus a sibling panel) simultaneously"
    expected: "Card stays readable — blocks clearly separated, no cramping, vertical growth only"
    why_human: "Readability is a human visual judgment"
---

# Phase 5: Review Flow + Fact Safety — Verification Report

**Phase Goal:** Before anything is exported, the user is the quality gate — regenerating individual sections, editing text inline, and seeing exactly what the AI changed relative to profile facts.
**Verified:** 2026-09-29T19:21:57Z
**Status:** human_needed (no gaps — every automatable must-have verified against the codebase and re-proven by execution; the five human UAT areas deferred at 05-04 are re-surfaced here, never silently passed)
**Re-verification:** No — initial verification (covers the post-review-fix tree: CR-01/WR-01/WR-02/IN-01/IN-03/IN-04 landed after 05-02/05-04's summaries)

## Goal Achievement

### User Flow Coverage (MVP mode — derived from ROADMAP success criteria)

The phase goal is not in strict `As a…, I want to…, so that…` User Story form (`user-story.validate` → invalid), same as Phase 4 — noted as an advisory; the ROADMAP's four explicit Success Criteria are the contract and are fully verifiable. Each SC below synthesizes the plan truths detailed in the Observable Truths table.

| # | Flow step (from SC) | Expected | Evidence in codebase | Status |
|---|---------------------|----------|----------------------|--------|
| 1 | User regenerates a single section without affecting the others, optionally with a hint (SC1) | Exactly ONE gateway stage per regen; full merged secoes back with byte-identical siblings; recomputed coverage; dica as user-message DATA only | `backend/app/resume/pipeline.py` `run_section_regen` + `SECTION_STAGE_BY_ID`; `routes/resume.py` `RegenerarRequest` (extra=forbid, secoes reuses ExportarSecoes); `facts.py` `compose_regen_stage_input`; behavioral tests: one-stage ×3, sibling identity (`is`), hint-in-user-message-only, coverage-over-merged-text — all PASSED in the 267-test run; frontend wholesale swap (CurriculoHome.tsx:305–314) | ✓ VERIFIED (backend behavioral; frontend data-flow wired) — the click-through feel rides human UAT area 1 |
| 2 | User edits any generated text inline; the edited version is exactly what the preview and the exported PDF show (SC2) | Inline editor per section granularity; badge Editado; export/self-check consume the displayed state with zero extra steps | `SectionEditor.tsx` (controlled textarea, dividirLinhas, zero-items guard, resumo 1..8000); `salvarEdicao` writes `resultado.secoes` (CurriculoHome.tsx:496–517); export posts the same `resultado.secoes` (line 784); edits flow because there is exactly one displayed-state source | ✓ VERIFIED (structural — single source of truth) / exported-PDF-shows-edits → human UAT area 3 |
| 3 | User sees side-by-side profile facts vs generated text with inventions immediately visible (SC3) | Two-column panel per section, deterministic amber marks + sr-only suffixes, D-11 legend / loud-zero line, company fold-match fallback | `frontend/src/lib/comparison.ts` (pure port: fold/termPattern/extractNumerals/foldContains/suspectTokens/segmentText — node smoke PASSED, vectors match the Python mirror exactly); `ComparisonPanel.tsx` (three fact scopes + all-entries fallback, marks only inside the panel); `test_comparison_vectors.py` PASSED | ✓ VERIFIED (mechanics behavioral + panel structural) — the visual walkthrough is human UAT area 2 |
| 4 | Regenerating never silently destroys edits; prior versions remain accessible; edit policy explicit in the UI (SC4) | Stack-before-mutate on every destructive path; CR-01 three-layer race fix; Versões panel with restore; permanent policy line; amber confirm strips, never dialogs | `empilharVersaoAtual`/`empilharValor` at 14 grep sites covering ALL destructive paths (save :507, regen success :277 + sibling-drift stack :287–297, restore :555, confirmed full regen CurriculoHome.tsx:221–226, dirty-discard :531–545); CR-01 pins: SectionEditor `disabled={!canSave \|\| locked}` :130 / `disabled={locked}` :138, 3× `locked={regenerando}` in ResumeResult, `salvarEdicao` op-pending guard :504; `POLICY_EDICAO` pinned JSX under the card header (ResumeResult.tsx:578–580); zero browser dialogs | ✓ VERIFIED (structural — explicit code ordering + locks) — the interactive matrix is human UAT area 1 |

**Score:** 23/34 truths verified (11 present, behavior-unverified — all routed to the 5 human UAT areas; 0 failed)

### Observable Truths

Statuses: ✓ VERIFIED (B) = a passing offline test exercises the behavior (267-test run re-executed by this verification); ✓ VERIFIED (S) = deterministic code structure (explicit synchronous ordering, JSX conditional semantics, state writes, tsc gate); ⚠️ PBU = present + wired but the interactive/browser behavior no test exercises.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| **05-01** | | | |
| 1 | POST /api/resume/regenerar runs exactly ONE gateway stage via SECTION_STAGE_BY_ID; extraction and siblings never run | ✓ VERIFIED (B) | `test_run_section_regen_runs_exactly_one_stage[resumo/experiencias/habilidades]` — `len(client.calls) == 1` + wire name + strict schema; PASSED in suite |
| 2 | Successful regen response carries the FULL merged secoes; siblings byte-identical to submitted | ✓ VERIFIED (B) | `test_siblings_byte_identical_only_target_replaced` ×3 — `==` AND `is` identity assertions on sibling strings; pipeline merges by reference (pipeline.py:173–183) |
| 3 | Dica travels as DATA in the composed user-message input only; system prompt untouched; runs.jsonl stays metadata-only (D-05/D-15) | ✓ VERIFIED (B) | `test_dica_travels_as_user_message_data_system_and_log_untouched` — dica in messages[1], messages[0] == `load_prompt(stage).body`, unchanged create() field set, dica absent from runs.jsonl text |
| 4 | Coverage recomputed server-side over merged text on every regen; frontend swaps cobertura/cobertura_resumo from the response | ✓ VERIFIED (B/S) | `test_coverage_recomputed_over_merged_generated_text` (sibling-only AND new-section keywords both coberto); CurriculoHome.tsx:305–314 swaps secoes+cobertura+cobertura_resumo wholesale from the response; KeywordsPanel consumes resultado.cobertura |
| 5 | Result screen offers 'Regenerar seção' per generated section with the in-flight line; displayed text stays mounted during flight | ⚠️ PBU | Action row + `REGEN_INFLIGHT_LINE` ('Regenerando {secao}… as outras seções permanecem inalteradas.') + pending line render (ResumeResult.tsx:331–333); content `{children}` not replaced while pending — interactive confirmation → human UAT area 1 |
| 6 | Hint input hidden until the always-visible 'Adicionar dica' toggle is used | ✓ VERIFIED (S) | `{dicaAberta && (...)}` conditional (ResumeResult.tsx:269–285); toggle always rendered in the action row with aria-expanded |
| 7 | Failed regen → red panel scoped in the owning section, erros[] verbatim, prior text mounted; fetch failure → generic hint | ⚠️ PBU | Backend erro envelope behavioral-verified (`test_regen_erro_envelope_on_llm_error` + caplog); frontend panel render (ResumeResult.tsx:334–351) is browser runtime → human UAT area 1 |
| 8 | Every successful displayed-content mutation clears receiptFilename + selfcheck + exportarErros BEFORE mounting new state | ✓ VERIFIED (S) | Explicit ordering in `regenerar.onSuccess` (CurriculoHome.tsx:302–304 before :305), `salvarEdicao` (:508–510 before :512), `restaurar` (:564–566); synchronous handler — React applies the batch before the next render |
| 9 | Empty/whitespace edit rejected (client guard + strict server validation); regen yields content or a loud erro envelope | ✓ VERIFIED (B/S) | `textoEditorValido` (resumo 1..8000; lists ≥1 non-empty line — SectionEditor.tsx:54–60); server: `test_regen_rejects_short_jd_text/…/empty_submitted_habilidades` 422 family PASSED |
| 10 | /api/resume/regenerar served like every resume endpoint (dev + built SPA), sync def, never stalls the event loop | ✓ VERIFIED (B) | `test_handlers_are_sync_def_never_coroutines` + `test_resume_router_registered_before_spa_mount` list `/api/resume/regenerar` (test_resume_api.py:305,318); PASSED in suite |
| **05-02** | | | |
| 11 | Permanent D-02 policy line under the card header whenever a result is mounted | ✓ VERIFIED (S) | Unconditional JSX (ResumeResult.tsx:578–580): `<p className="mt-2 text-xs text-gray-600"><span aria-hidden>⚠</span> {POLICY_EDICAO}</p>`; string verbatim in constants/ui.ts:251; browser visibility → UAT area 4 |
| 12 | Editar opens pre-filled editor; Salvar mounts edited text + badge Editado + stacks pre-edit version; Cancelar reverts / dirty strip | ⚠️ PBU | Wiring complete: `abrirEditor` pre-fills from displayed text (:481–488), `salvarEdicao` stack→write→badge→close (:496–517), dirty derived `draft !== inicial`; interactive flow → human UAT area 1 |
| 13 | Every destructive path pushes current text + badge origin onto the version stack FIRST — one helper, four paths | ✓ VERIFIED (S) | `empilharVersaoAtual`/`empilharValor` = 14 grep sites; verified at the top of: edit save (:507), section regen success (:277), restore (:555), confirmed full regen (gerar.onSuccess :221–226) — plus the CR-01 sibling-drift stack (:287–297) and WR-02 dirty-discard (:531–545). Explicit synchronous sequencing in each handler |
| 14 | Versões panel newest-first with origin badge + line-clamp-2 snippet + Restaurar versão; restore stacks current first and adopts the version's origem; toggle disabled with no count suffix at zero | ✓ VERIFIED (S) | SectionVersionsPanel.tsx (prepend order in `empilharValor`, rows newest-first, `line-clamp-2`, `disabled={restaurarDesabilitado}`); toggle `disabled={versoes.length === 0}`, count suffix from 1 (ResumeResult.tsx:240–250); `restaurar` stacks → removes at indice+1 → mounts → adopts origem (:551–567); interactive confirm → UAT area 1 |
| 15 | Tri-state badge — Gerado (soft blue) / Do perfil (gray) / Editado (solid blue-600 white) | ✓ VERIFIED (S) | Badge component (ResumeResult.tsx:94–103) + BADGE_GERADO/EDITADO_CLASSES in constants/ui.ts; version rows reuse the same classes |
| 16 | Only one editor at a time; open editor disables Exportar/Gerar novamente/every Restaurar while own-section Regenerar stays enabled via the D-14 strip | ⚠️ PBU | Derived booleans single-source (`locksEdicao` :610); Exportar CTA `ctaDisabled={locksEdicao}` (:790), header button `disabled={locksEdicao}` (:562), restore `restaurarDesabilitado={locksEdicao}`; regen buttons not gated by locksEdicao; runtime matrix → human UAT area 1 |
| 17 | Long-op pending disables all mutation controls; Comparar and Versões toggles stay usable read-only | ⚠️ PBU | `operacaoLongaPendente` = gerar.isPending ‖ exportar.isPending ‖ regenerar.isPending (:609); mutation controls gated; Comparar (:229–236) and Versões (:240–250) toggles never disabled; runtime → human UAT area 1 |
| 18 | Regen-over-edit amber strip with exact copy; confirming stacks first, then regenerates | ⚠️ PBU | `tentarRegenerarSecao` gates on origem 'editado' or dirty editor (:399–407); `confirmarRegenSobreEdicao` stacks the dirty draft before closing (:414–427); strips render under the action row / under the editor (:290–310); runtime → human UAT area 1 |
| 19 | Full regen with edits asks once via the header strip and stacks EVERY section on confirm; disabled outright while an editor is open | ⚠️ PBU | `tentarGerarCompleta` (:370–381) + `gerarConfirmadoRef` → gerar.onSuccess stacks all three sections (:221–226); Zone 1 CTA routes through the same gate (:630, disabled `locksEdicao` :678); runtime → human UAT area 1 |
| 20 | Empty/whitespace edit save rejected; regenerated section always yields content or a loud erro envelope | ✓ VERIFIED (B/S) | Same evidence as truth 9; section regen errors route to the section-scoped panel, never a silent empty swap |
| 21 | Edits/versions are session React state only — no persistence, no shadow copy; export consumes the displayed state | ✓ VERIFIED (S) | All state via useState; zero localStorage/sessionStorage/network writes of edits (grep); export posts `resultado.secoes` (CurriculoHome.tsx:784); no fetch on edit/restore |
| **05-03** | | | |
| 22 | Every generated section offers 'Comparar com o perfil' (quiet, aria-expanded, swaps to 'Ocultar comparação'); open panel = two columns, stacks under sm, never horizontal scroll | ✓ VERIFIED (S) | Toggle (ResumeResult.tsx:229–236); panel `grid grid-cols-1 gap-4 sm:grid-cols-2` (ComparisonPanel.tsx:28) — deterministic Tailwind stacking; visual walkthrough → UAT area 2 |
| 23 | Left column facts per section scope: resumo → profile summary; experiências → fold-matched entry (fallback ALL entries + neutral note, never empty); habilidades → items under category sublabels, never chips | ✓ VERIFIED (S) | ComparisonPanel.tsx: resumo branch (:296–305), experiências fold-match + `casamentoFalhou` fallback (:210–249), habilidades plain text (:276–290) — no chip classes |
| 24 | Suspects render ONLY in the panel's right column, wrapped in `<mark>` with dual visual cue + sr-only suffix — never in the card body | ✓ VERIFIED (S) | `SegmentedText` used only inside ComparisonPanel; card body renders plain `{secoes...}` text; `COMPARACAO_MARK_SR_ONLY = ' (não consta no perfil)'`; amber classes only in the panel |
| 25 | All matching applies the coverage fold (casefold+NFKD) with `(?<!\w)term(?!\w)` lookarounds — never `\b`; equality on folded text | ✓ VERIFIED (B) | grep: no `\b` anchors in comparison.ts; node smoke (this verification): fold('Résumé')=='resume', C++ matched, xC++ tail rejected, folded containment 2022⊂2022-03 — exactly the Python mirror vectors; `test_comparison_vectors.py` (7 tests) PASSED in suite |
| 26 | Suspect detection deterministic: numerals not fold-contained in source facts + entity/tech-shape tokens absent from the profile inventory — no LLM judge | ✓ VERIFIED (B) | Node smoke (this verification): invented {2023, NuvemTech, Kubernetes} flagged; grounded {Python, AWS} not flagged; pure module — no fetch, no react import, zero new dependencies across the phase range |
| 27 | Legend (D-11, verbatim) when ≥1 mark; loud-zero line when zero — never a silently unmarked panel | ✓ VERIFIED (S) | `totalMarcas > 0 ? COMPARACAO_LEGENDA : COMPARACAO_ZERO_SUSPEITOS` (ComparisonPanel.tsx:322–324); both strings verbatim in constants/ui.ts |
| 28 | Highlights recompute against the CURRENTLY displayed text (post-edit/restore), client-side, zero fetch | ✓ VERIFIED (S) | `panelTexto` computed from the `secoes` prop (= resultado.secoes) on every render (ResumeResult.tsx:602/653/730); comparison.ts has no fetch; read-only compute never mutates displayed state |
| 29 | Mixed content renders per token — marked/unmarked segments interleave | ✓ VERIFIED (B) | Node smoke: `segmentText('Métricas na NuvemTech e AWS', …)` → [{false},{true 'NuvemTech'},{false}] — ordered spans covering the text exactly once |
| **05-04** | | | |
| 30 | SC4 walkthrough passes (edit → strip → confirm → only that section changes; restore stacks; dirty-cancel strip; full regen asks once) | ⚠️ PBU | The checkpoint is a human gate BY DESIGN (05-04-PLAN `checkpoint:human-verify`); resolved-as-deferred per the run's Phase 1/4 convention — re-surfaced here as human UAT area 1, never claimed as passed |
| 31 | SC3 walkthrough passes (marks + legend; edit clears mark; loud-zero; company fallback) | ⚠️ PBU | → human UAT area 2 |
| 32 | SC2 walkthrough passes (edited text in exported PDF + self-check survival rows) | ⚠️ PBU | → human UAT area 3 |
| 33 | Policy visibility + refresh returns to the plain generated result | ⚠️ PBU | → human UAT area 4 |
| 34 | Full offline suite + frontend build green at checkpoint time | ✓ VERIFIED (B) | Re-executed by this verification: `uv run pytest -q` → **267 passed, 7 deselected**; `npm run build` → **green, 79 modules, 1.49s** |

### Required Artifacts

All 21 planned artifacts exist, are substantive (no stubs), and are wired.

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/app/routes/resume.py` | RegenerarRequest (extra=forbid) + POST /api/resume/regenerar | ✓ VERIFIED | Fields per contract (jd 80..20000, Literal language/secao, dica ≤500, secoes: ExportarSecoes imported, keywords=[]); plain `def` handler; house 200-envelope |
| `backend/app/resume/pipeline.py` | SECTION_STAGE_BY_ID + run_section_regen | ✓ VERIFIED | Built from SECTION_STAGES order; one stage; merge by reference; coverage over FULL merged text; IN-04 load_profile hoist also landed here |
| `backend/app/resume/facts.py` | compose_regen_stage_input | ✓ VERIFIED | Blank/None → base unchanged; appends DICA DE DIRECIONAMENTO block framed as user DATA |
| `backend/tests/test_resume_regen_pipeline.py` | Offline ScriptedClient family | ✓ VERIFIED | 10+ tests: one-stage ×3, hint-as-data, sibling `is`-identity ×3, coverage-over-merge, blank-dica boundary ×3, compose unit ×2 |
| `backend/tests/test_resume_regen_api.py` | Envelope + 422 + structural family | ✓ VERIFIED | ok envelope, optional dica, erro envelope ×2 (caplog raw-terminal-only), 7× 422, route presence |
| `backend/tests/test_comparison_vectors.py` | Python mirror of the TS port vectors | ✓ VERIFIED | 7 vector tests PASSED; each vector annotated with its expected TS-side result |
| `frontend/src/api/client.ts` | RegenerarRequest/Response + regenerarSecao() | ✓ VERIFIED | Strict mirror; drops the empty dica KEY (never `dica: ""`) at lines 275–276 |
| `frontend/src/constants/ui.ts` | All Phase 5 PT-BR strings + TEXTAREA_CLASSES promotion | ✓ VERIFIED | Every UI-SPEC copy string verified verbatim (policy line, strips, Versões, comparison legend/zero); TEXTAREA_CLASSES single-source |
| `frontend/src/pages/CurriculoHome.tsx` | regenerar mutation + editor/versions/strips state + locks | ✓ VERIFIED | 813 lines; all four destructive paths + CR-01 three layers + IN-01 conditional strip clear (:272) |
| `frontend/src/components/ResumeResult.tsx` | Policy line, tri-state badge, action rows, strips, in-flight line, section-scoped error panel | ✓ VERIFIED | GeneratedSection shell with the full action row; passthrough sections untouched (D-13); IN-03 date fix (:713–715) |
| `frontend/src/components/ConfirmStrip.tsx` | The ONE shared amber strip (three uses) | ✓ VERIFIED | Docstring now enumerates all three stack-first paths by name (WR-02 made true) |
| `frontend/src/components/SectionEditor.tsx` | Textarea editor + save/cancel + dirty confirm + zero-items guard + CR-01 lock | ✓ VERIFIED | `locked` prop gates Salvar (:130) and Cancelar (:138); resumo maxLength 8000 (WR-01); onDescartar path (WR-02) |
| `frontend/src/components/SectionVersionsPanel.tsx` | Newest-first version rows + Restaurar versão | ✓ VERIFIED | Owns SectionVersion/OrigemBadge/SectionValor types; line-clamp-2 snippets |
| `frontend/src/components/ComparisonPanel.tsx` | Two-column panel with marks + legend/zero + fallback | ✓ VERIFIED | Three fact scopes; marks only inside the panel; IN-02 known skip does not affect behavior (see Anti-Patterns) |
| `frontend/src/lib/comparison.ts` | Pure fold/tokenize/segment port | ✓ VERIFIED | No react import, no fetch, no `\b` anchors; node smoke reproduces the canonical vectors exactly |
| `backend/tests/test_resume_api.py` | Structural pins extended with /regenerar | ✓ VERIFIED | Both lists at lines 305/318 |
| `backend/tests/test_resume_pipeline.py` | IN-04 regression test | ✓ VERIFIED | `test_run_lint_only_loads_profile_before_the_paid_call` — zero paid calls on broken profile |
| `.planning/.../05-04-SUMMARY.md` | UAT outcome record | ✓ VERIFIED | Five areas recorded resolved-as-deferred with standing proofs + re-surface pointer; nothing claimed as passed |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| route handler | pipeline.run_section_regen → run_stage(SECTION_STAGE_BY_ID[secao]) | one stage, siblings never touched | ✓ WIRED | resume.py:116 → pipeline.py:166–168; pinned by one-stage tests ×3 |
| compose_regen_stage_input DICA block | gateway f-string user message | hint = data, never system | ✓ WIRED | facts.py:170–178; test asserts dica in messages[1] and system == prompt body |
| regenerar onSuccess | resultado.secoes + cobertura + cobertura_resumo | wholesale swap from response, no client merge | ✓ WIRED | CurriculoHome.tsx:305–314 — spread keeps gerar-run keys/idioma, swaps exactly the three response fields |
| regenerar body | ExportarSecoes shape | the exact displayed state export posts | ✓ WIRED | routes/resume.py:85 `secoes: ExportarSecoes`; CurriculoHome posts `resultado.secoes` for BOTH export (:784) and regen (:443) |
| empilharVersaoAtual | all four destructive paths | stack-before-mutate at the top | ✓ WIRED | 14 sites; verified per-path (save :507, regen :277, restore :555, full regen :221–226) |
| save/restore/regen-success | resultado.secoes direct write + three export-state clears | export/self-check consume edited text | ✓ WIRED | Explicit ordering in every handler (see truth 8) |
| SectionEditor save | dividirLinhas split/trim/drop-empties | matches envelope min_length=1 | ✓ WIRED | SectionEditor.tsx:37–42; used by valorDeRascunho + textoEditorValido |
| locking booleans | state atoms (editor, gerar/exportar/regenerar isPending) | derived, no ad-hoc disabled logic | ✓ WIRED | `operacaoLongaPendente`/`locksEdicao` (:609–610) feed every gated control |
| comparison.ts fold | coverage.py _fold | mechanical port pinned by mirror | ✓ WIRED | Header cross-references coverage.py:33-41; mirror tests + node smoke match vector-for-vector |
| ComparisonPanel | mounted PerfilDTO prop + resultado.secoes | zero fetch, pure client compute | ✓ WIRED | Props threaded from ResumeResult (:601–603, 650–654, 728–730); no fetch anywhere in the module |
| company alignment | fold-equality on company, fallback all entries | Pitfall 8 | ✓ WIRED | ComparisonPanel.tsx:216–249 |
| suspect spans | ordered {text, suspect} segments as JSX children | no HTML string building | ✓ WIRED | segmentText → SegmentedText; `dangerouslySetInnerHTML` = zero matches in frontend/src |
| 05-04 checkpoint | finished screen from 05-01+02+03 | automation green first | ✓ WIRED | Suite + build re-run green in this verification before the human items are routed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| Section text (card + editor pre-fill + comparison right column) | resultado.secoes | POST /api/resume/gerar → /api/resume/regenerar merged response → edit/restaurar writes | Yes | ✓ FLOWING |
| Coverage chips (Zone 5) | resultado.cobertura / cobertura_resumo | classify_coverage + summarize_coverage over merged generated text, server-side | Yes | ✓ FLOWING |
| Comparison left column | perfil prop | GET /api/perfil (shared ['perfil'] query) | Yes | ✓ FLOWING |
| Version rows | versoes[secao] | empilharValor pushes on every destructive path | Yes | ✓ FLOWING |
| Regen error panel | regenErros[secao] | backend erros[] (message_ptbr lines) or [] on fetch failure | Yes | ✓ FLOWING |
| Dica sent to the LLM | dicas[secao] | user-typed input → request body (empty key dropped) → compose_regen_stage_input | Yes | ✓ FLOWING |

No rendered value terminates in a static return, hardcoded literal, or mock.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full offline backend suite | `uv run pytest -q` (backend) | 267 passed, 7 deselected in 25.79s — includes every regen/comparison/structural test family and the IN-04 regression test | ✓ PASS |
| Frontend compile drift gate | `npm run build` (frontend) | green — 79 modules, 1.49s | ✓ PASS |
| TS comparison mechanics (no JS runner exists) | tsc-compile comparison.ts → node smoke | fold Résumé→resume / Currículo→curriculo; C++ matched, xC++ tail rejected; numerals exactly {2022-03, 40%, 1.234, 7,5}; 2022 grounded in 2022-03; invented {2023, NuvemTech, Kubernetes} flagged, grounded {Python, AWS} not; segments interleave — SMOKE-PASS | ✓ PASS |
| CR-01 fix grep-pins (landed after 05-02's SUMMARY) | grep SectionEditor/CurriculoHome/ResumeResult | `disabled={!canSave \|\| locked}` + `disabled={locked}` (2); `locked={regenerando}` ×3; salvarEdicao guard (line 504); 14 stack-before-mutate sites; sibling-drift stack (line 291) | ✓ PASS |
| IN-01 conditional strip clear | grep `prev === variables.secao` | CurriculoHome.tsx:272 | ✓ PASS |
| Browser-dialog ban | `grep -RIn "window\.(confirm\|alert\|prompt)" frontend/src` | zero matches | ✓ PASS |
| Raw-HTML ban | `grep -RIn dangerouslySetInnerHTML frontend/src` | zero matches | ✓ PASS |
| Regex purity (never `\b`) | `grep -nE '\\b' frontend/src/lib/comparison.ts` | zero matches — lookarounds only | ✓ PASS |
| Zero new dependencies (all plans claim none) | `git diff 2b96e0d..HEAD -- package.json package-lock.json pyproject.toml` | empty — zero changes in the whole phase range | ✓ PASS |
| Debt markers in phase-modified files | grep TBD/FIXME/XXX/HACK across 15 files | zero (PLACEHOLDER hits are the pre-existing legitimate textarea-placeholder attribute constants) | ✓ PASS |
| runs.jsonl metadata-only under regen (D-15) | pinned by `test_dica_travels_as_user_message_data_system_and_log_untouched` | dica + DICA block asserted absent from the log file; create() field set unchanged | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist or were declared for this phase. The equivalent runnable proof is the offline suite re-executed above (267 passed) plus the direct node smoke of the TS port — both run by this verification, not trusted from SUMMARY claims.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| REVIEW-01 | 05-01, 05-02, 05-03, 05-04 | User can regenerate individual resume sections and edit generated text inline in the app before exporting | ✓ SATISFIED (automated) | [x] in REQUIREMENTS.md; regen (one stage, merged response, hint-as-data), inline editing with versions/locks, and the fact-safety comparison all shipped, wired, and re-proven by the 267-test run; the five browser UAT areas deferred at the 05-04 checkpoint are re-surfaced as human items below (run convention, same as Phase 4's REVIEW-03 note) |

No orphaned requirements: REQUIREMENTS.md maps exactly REVIEW-01 to Phase 5; all four plans declare `requirements: [REVIEW-01]`. No requirement mapped to this phase is missing from any plan.

### Prohibitions (must-NOT checks)

| Prohibition | Status | Evidence |
| ----------- | ------ | -------- |
| No AI-invented facts presented as truth; regen output stays grounded | ✓ VERIFIED | run_section_regen output validated against the stage's strict schema; the deterministic grounding harness (Phase 3) unchanged; the comparison panel frames marks as suspicion (D-11) |
| Sibling sections byte-identical on regen | ✓ VERIFIED | `is`-identity assertions ×3, PASSED |
| The hint never reaches runs.jsonl or the system prompt (D-15/D-05) | ✓ VERIFIED | Behavioral test asserts both absences + unchanged gateway field set |
| No raw exception detail in the response envelope | ✓ VERIFIED | caplog tests: raw in terminal records only, absent from erros[] (regen + gerar + export families) |
| Edits/regen results never written back to profile files (D-01) | ✓ VERIFIED | No write path anywhere: frontend edits live in useState; regen only reads (load_profile); zero persistence layers |
| Confirmations never browser dialogs | ✓ VERIFIED | zero window.confirm/alert/prompt; the three ConfirmStrip usages are the only confirmations |
| Amber never marks errors or verdicts | ✓ VERIFIED | ConfirmStrip = amber classes only; error panels = red classes; chips never amber; comparison marks amber only inside the panel |
| Deferred human checks never silently dropped | ✓ VERIFIED | 05-04-SUMMARY records all five with re-surface pointers; this report re-surfaces them as human_verification |
| No diff libraries / no LLM-judged comparison | ✓ VERIFIED | comparison.ts is pure in-repo code; zero new dependencies across the phase range |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| frontend/src/components/ComparisonPanel.tsx | 210–232 | `texto` prop ignored on the experiências branch (review IN-02 — deliberately skipped, contract-redesign scope) | ℹ️ Info | Behavior is correct (suspects compute from `entradas`, the actual displayed entries); only the prop contract misleads future edits |
| frontend/src/pages/CurriculoHome.tsx | 573–574 | Profile fetch-level failure renders a bare red line without the fail-loud hint (review IN-05 — deliberately skipped, new-copy scope) | ℹ️ Info | Pre-existing Phase 3 surface, out of the review-fix scope; never silent (PERFIL_ERROR_TITLE renders) |
| frontend/src/constants/ui.ts | 103, 241 | PLACEHOLDER substring | ℹ️ Info | Legitimate HTML placeholder attribute constants (pre-existing pattern since Phase 1), not debt markers |

No TBD/FIXME/XXX debt markers in any phase-modified file. No stub patterns — every rendered value chains to real backend data or explicit user/session state.

### Advisory (New Scope, Unevidenced — informational)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Phase goal is not in strict User Story format (user-story.validate → invalid); verification grounded in the ROADMAP's four Success Criteria instead | other | Same as Phase 4; optional normalization via `/gsd mvp-phase 5`; does not affect this phase's evidence |
| 2 | The CR-01/WR-02/IN-01 logic fixes are semantic changes whose full behavioral confirmation rides human UAT area 1 | other | All grep-pins verified in source by this verification; tsc green; the frontend has no test runner by project design — the review fix itself routed semantic confirmation here |
| 3 | IN-02/IN-05 review findings remain open as accepted skips with recorded reasons | other | Contract-redesign / new-copy scope decisions by the coordinator; neither affects a phase must-have |

### Human Verification Required

Five areas, deferred at the 05-04 checkpoint ("deferred — record UAT", autonomous run, user unavailable — the plan's own designed resolution path) and re-surfaced here per the run convention. The 11 present-but-behavior-unverified truths map into these areas. Nothing below is claimed as passed.

1. **SC4 locking matrix (area 1)** — edit a section → Regenerar seção shows the amber strip → confirm → the edit is in Versões and only that section changed; restore stacks current first; dirty-cancel shows its strip; full regen with edits asks once and stacks everything; editor open disables Exportar/Gerar novamente/Restaurar but keeps own-section regen; pending regen disables edit/restore/dica while Comparar/Versões stay usable; in-flight line shows and text stays mounted; a failed regen shows the section-scoped red panel with prior text mounted.
2. **SC3 comparison framing (area 2)** — amber marks + legend on suspect tokens; editing away a suspect clears its mark on reopen; a grounded section shows the loud-zero line; paraphrased company falls back to all profile entries with the neutral note.
3. **SC2 edits→export (area 3)** — edited text appears in the exported PDF and the ATS self-check survival rows with no extra step.
4. **Policy visibility + refresh (area 4)** — the permanent policy line under the card header; refresh returns to the plain generated result, unedited.
5. **Backstop (area 5)** — editor + comparison + versions open on one section (plus a sibling panel) stays readable.

### Gaps Summary

None. Every automatable must-have is verified against the codebase and re-proven by execution in this verification session: the full offline suite (267 passed, 7 deselected — the post-review-fix count including the IN-04 regression test), the frontend build (tsc -b + vite green), a direct node smoke of the TS comparison port reproducing the Python mirror vectors exactly, and all CR-01/WR-01/WR-02/IN-01 fix pins confirmed in source. All 21 artifacts are present, substantive, and wired; all 13 key links hold; every prohibition is enforced and pinned. The phase goal's automatable spine — one-stage regeneration with byte-identical siblings and hint-as-data, single-source displayed state flowing to export, deterministic invention detection with mandatory suspicion framing, and stack-before-mutate on every destructive path under the CR-01 three-layer lock — is proven. The 11 behavior-unverified truths are the interactive browser behaviors no frontend test runner can exercise (the project has none by design); they route to the five human UAT areas above, exactly as the 05-04 checkpoint's own design intended — recorded as human_needed, not gaps, and not silent passes.

---

_Verified: 2026-09-29T19:21:57Z_
_Verifier: Claude (gsd-verifier)_
