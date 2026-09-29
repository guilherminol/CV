---
phase: 05-review-flow-fact-safety
fixed_at: 2026-09-27T16:35:00-03:00
review_path: .planning/phases/05-review-flow-fact-safety/05-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 6
skipped: 2
status: partial
---

# Phase 5: Code Review Fix Report

**Fixed at:** 2026-09-27T16:35:00-03:00
**Source review:** .planning/phases/05-review-flow-fact-safety/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (1 Critical, 2 Warning, 5 Info)
- Fixed: 6 (CR-01, WR-01, WR-02, IN-01, IN-03, IN-04)
- Skipped: 2 (IN-02, IN-05 — contract-redesign scope, per coordinator instruction)

Scope rule applied: ALL Critical + Warning findings fixed; of the 5 Info findings,
the mechanical ones (IN-01, IN-03, IN-04) fixed and the contract-redesign ones
(IN-02, IN-05) skipped with reasons below.

## Fixed Issues

### CR-01: Edit saved during a sibling section's regen flight is silently destroyed (data loss)

**Files modified:** `frontend/src/components/SectionEditor.tsx`, `frontend/src/components/ResumeResult.tsx`, `frontend/src/pages/CurriculoHome.tsx`
**Commit:** 96462e7
**Status:** fixed: requires human verification (logic-level race fix — no frontend test runner exists; verified structurally + tsc, semantic correctness needs the verifier phase / manual UAT)
**Applied fix:** Defense in depth, both suggested mechanisms:
1. **Editor lock (primary):** `SectionEditor` gained a `locked` prop (long-op
   pending). `Salvar alterações` disables on `!canSave || locked`, `Cancelar
   edição` disables on `locked`. Wired as `locked={regenerando}` at all three
   call sites in ResumeResult (the op-pending half of `locksEdicao`, not
   `editor !== null` — the editor stays open and its draft editable; only the
   closing/saving actions freeze for the flight).
2. **Mutation-side guard (belt-and-braces):** `salvarEdicao()` returns early
   when `operacaoLongaPendente` — the handler itself refuses to write the
   displayed state under an in-flight wholesale swap.
3. **Stack-before-wholesale-swap (third layer):** `regenerar.onSuccess` now
   stacks any section whose CURRENT displayed text differs from the request's
   submitted snapshot (`variables.secoes`) BEFORE the wholesale `secoes` swap —
   so even a future reopened gap cannot destroy an edit silently (empty noise
   avoided: unchanged siblings are not stacked).
4. The previously-false invariant comment (CurriculoHome "Long-op locks
   guarantee…") was rewritten to state the true three-layer invariant in the
   plan's terms: stack-before-mutate on EVERY displayed-state mutation, with
   the lock layers named.

**Provable invariants (grep-pins, 05-02 structural style — all verified on the
fixed tree):**
```
grep -n "disabled={!canSave || locked}\|disabled={locked}" src/components/SectionEditor.tsx   # 2 hits (lines 130, 138)
grep -c "locked={regenerando}" src/components/ResumeResult.tsx                                # 3 (all editor sites)
grep -n "if (operacaoLongaPendente) return" src/pages/CurriculoHome.tsx                       # salvarEdicao guard (line 504)
grep -c "empilharVersaoAtual\|empilharValor(" src/pages/CurriculoHome.tsx                     # 14 stack-before-mutate sites
grep -n "JSON.stringify(resultado.secoes\[irma\])" src/pages/CurriculoHome.tsx                # sibling drift stack (line 291)
```

### WR-01: Backend max-length ceilings not enforced client-side

**Files modified:** `frontend/src/pages/CurriculoHome.tsx`, `frontend/src/components/ResumeResult.tsx`, `frontend/src/components/SectionEditor.tsx`, `frontend/src/constants/ui.ts`
**Commit:** 05a3387
**Applied fix:** The 422 is now unreachable from the UI:
- JD textarea: `maxLength={JD_MAX_CHARS}` (20000, mirroring `JD_MAX_LENGTH`,
  routes/resume.py) + a gray cap hint `CURRICULO_JD_TOO_LONG_HINT` (new
  constants/ui.ts string, PT-BR, shown at the cap — mirrors the existing
  min-80 hint pattern).
- Dica input: `maxLength={DICA_MAX_CHARS}` (500, mirroring
  `RegenerarRequest.dica Field(max_length=500)`).
- Resumo editor: `maxLength` 8000 on the resumo textarea +
  `textoEditorValido('resumo')` now enforces `1..8000` trimmed chars
  (mirroring `RESUMO_MAX_LENGTH`, routes/export.py — an oversized saved
  resumo previously poisoned every later regen/export POST). Numeric bounds
  live as single-definition module constants in the file that uses them
  (JD_MIN_CHARS precedent), each citing its backend source of truth.

### WR-02: ConfirmStrip docstring asserts a false data-safety invariant for the dirty-cancel path

**Files modified:** `frontend/src/components/SectionEditor.tsx`, `frontend/src/components/ConfirmStrip.tsx`, `frontend/src/components/ResumeResult.tsx`, `frontend/src/pages/CurriculoHome.tsx`
**Commit:** 88f45cc
**Status:** fixed: requires human verification (behavior change — discarded drafts now stack; confirm this matches your intent for Versões noise)
**Applied fix:** Preferred option taken — made the claim TRUE instead of
weakening the docstring. The dirty-cancel strip's confirmed path now routes to
a new `onDescartar` prop → `CurriculoHome.descartarEdicao()`, which stacks the
dirty draft as an `'editado'` version BEFORE closing (same rule as
`confirmarRegenSobreEdicao`; empty/whitespace drafts skipped — nothing of
value). Clean cancel still goes straight to `onCancel` (no duplicate stacking).
This strengthens D-08: an explicitly discarded draft stays recoverable in
Versões. The ConfirmStrip docstring now enumerates all three strips' stack-first
paths by name (descartarEdicao / confirmarRegenSobreEdicao / gerarConfirmadoRef)
so the guarantee is verifiable.

### IN-01: An unrelated section's regen success silently dismisses a pending confirm strip

**Files modified:** `frontend/src/pages/CurriculoHome.tsx`
**Commit:** c4a6ed6
**Status:** fixed: requires human verification (logic tweak — strip dismissal scoping)
**Applied fix:** `regenerar.onSuccess` now clears the strip conditionally:
`setStripRegen((prev) => (prev === variables.secao ? null : prev))` — only the
owning section's attempt (or the already-confirmed path, which cleared the
strip before mutating) dismisses it; a sibling's success leaves the user's
pending intent mounted. `gerar.onSuccess`'s unconditional clear was left
intact (a concluded full regen replaces the whole result).

### IN-03: Education date range renders " – 2019" when `start_date` is null

**Files modified:** `frontend/src/components/ResumeResult.tsx`
**Commit:** 0f18c23
**Applied fix:** With only an end present the card renders just the end
(`ed.end_date ?? ''`); `dateRange()` is used only when `start_date` exists
("2015 – atual" / "2015 – 2019" stay as before; the empty/both-absent case
still renders nothing).

### IN-04: `/lint` loads the profile after the paid LLM extraction call

**Files modified:** `backend/app/resume/pipeline.py`, `backend/tests/test_resume_pipeline.py`
**Commit:** 7ce5156
**Applied fix:** `run_lint_only` now hoists `profile = load_profile()` above
`run_stage` (same load-first order as `run_resume_pipeline`; D-15 fresh, once)
— a broken profile fails `/lint` without consuming an OpenRouter call. No
contract reorder: the erro envelope shape and route handling are unchanged.
**Regression test added:** `test_run_lint_only_loads_profile_before_the_paid_call`
— monkeypatches `pipeline.load_profile` to raise `ProfileError` and asserts the
scripted client recorded ZERO calls (the paid extraction never fired).

## Verification

**Where the gates ran:** inside the isolated review-fix worktree
(`.claude/worktrees/rf-05-19899-…`), NOT the main checkout — the numbers are
reproducible from the worktree at the fix commits. Details:
- Frontend `npm run build` (tsc -b + vite): PASS after every fix and on the
  final tree. Run against an `npm ci`-installed `node_modules` inside the
  worktree (the worktree has no shared node_modules with the main checkout).
- Backend `pytest -q`: PASS — **267 passed, 7 deselected** (LLM-marked) =
  the 266 baseline + 1 new IN-04 regression test. Run from the worktree's
  `backend/` directory using the main checkout's `.venv` interpreter
  (dependencies only — every source/test file executed is the worktree's).
- Note: the 3 SPA-mount/router tests fail on a fresh worktree BEFORE any
  frontend build (they need the gitignored `frontend/dist/index.html`);
  they pass after the first build. This is environmental, not caused by the
  fixes — final suite is fully green.
- Frontend has no test runner (build = tsc gate per project convention), so
  the CR-01/WR-02/IN-01 logic fixes are pinned by the grep invariants above +
  tsc; semantic correctness lands on the verifier phase / UAT checklist
  (`/gsd-verify-work 5` locking-matrix walkthrough: editor open + sibling
  regen flight → Salvar/Cancelar disabled for the flight).

## Skipped Issues

### IN-02: `ComparisonPanel`'s `texto` prop is ignored for the experiências branch

**File:** `frontend/src/components/ComparisonPanel.tsx:171-182, 210-232`
**Reason:** Not mechanical — fixing it changes the shared component's public
prop contract (make `texto` optional/documented, or drop `panelTexto` for
experiências at the call site, which requires reshaping GeneratedSection's
required prop). Coordinator scope excluded contract redesign.
**Original issue:** For `secao === 'experiencias'` the panel computes
everything from `entradas` and never reads `texto`, yet ResumeResult computes
and passes it — the prop contract misleads future edits.

### IN-05: Profile fetch-level failure renders a bare line without the house fail-loud convention

**File:** `frontend/src/pages/CurriculoHome.tsx:507-509`
**Reason:** Requires new user-facing copy + a new rendered state outside the
mechanical scope agreed for this run (the UI-SPEC pins copy through its
Copywriting Contract; the coordinator's scope listed only IN-01/IN-03/IN-04
as mechanical fixes).
**Original issue:** `perfilQuery.isError` renders a single unstyled red line
(`PERFIL_ERROR_TITLE`) with no terminal-detail hint, unlike the lint/gerar/
export fetch-failure convention in the same file.

---

_Fixed: 2026-09-27T16:35:00-03:00_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
