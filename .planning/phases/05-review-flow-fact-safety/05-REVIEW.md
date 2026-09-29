---
phase: 05-review-flow-fact-safety
reviewed: 2026-09-27T12:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/app/resume/facts.py
  - backend/app/resume/pipeline.py
  - backend/app/routes/resume.py
  - backend/tests/test_comparison_vectors.py
  - backend/tests/test_resume_api.py
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
findings:
  critical: 1
  warning: 2
  info: 5
  total: 8
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-09-27T12:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the Phase 5 review-flow/fact-safety surface: the regen pipeline + route
(backend), the comparison mechanics port (`comparison.ts` + canonical vectors),
and the editing/version/confirm/panel UI stack. Cross-module contracts were
verified against the called modules (`coverage.py` fold/term mechanics,
`errors.py` `.raw`/`.message_ptbr` shape, `gateway.py` user-message template,
`export.py` `ExportarSecoes` floors, `main.py` router-before-mount) — all
consistent; the canonical comparison vectors match the TS port's actual regex
semantics, and the tests genuinely pin the documented invariants.

One Critical defect was found: the "long-op locks guarantee the displayed state
cannot change between mutate() and onSuccess" invariant is false — the open
editor's Salvar button is not gated by the long-op lock, so an edit saved during
a sibling section's regen flight is silently and permanently destroyed by the
regen response's wholesale `secoes` swap, and the lost text is not on the
version stack. Additionally, the frontend enforces none of the backend's
max-length ceilings (dica 500 / jd_text 20000), producing misleading dead-end
error states, and one shared component docstring asserts a data-safety guarantee
the code does not implement.

No security vulnerabilities found: all LLM/profile/edited content renders as
JSX text children (no raw-HTML path), no hardcoded secrets, the dica travels as
user-message DATA only (verified: system message and runs.jsonl untouched, and
the tests pin this), and regexes are linear-time with correct escaping.

## Critical Issues

### CR-01: Edit saved during a sibling section's regen flight is silently destroyed (data loss)

**File:** `frontend/src/pages/CurriculoHome.tsx:459-473` (with `frontend/src/components/SectionEditor.tsx:100-115` and `frontend/src/pages/CurriculoHome.tsx:274-283`)
**Issue:** The code's own invariant — "Long-op locks guarantee the displayed state cannot change between mutate() and onSuccess, so the closure reads below are always the texts being replaced" (CurriculoHome.tsx:429-432) — is false. While a section regen is in flight (a window of seconds to ~60s of LLM latency), an already-open editor on a *different* section remains fully interactive: `SectionEditor`'s Salvar/Cancelar buttons are gated only by `!canSave` / `dirty`, never by the pending-op lock, and `salvarEdicao()` (CurriculoHome.tsx:459) has no pending-op guard either. (Sibling regen with an editor open is an explicitly supported path — CurriculoHome.tsx:537-539, ResumeResult.tsx:537-539 comments.)

The lossy sequence:
1. Editor open on `experiencias`; user clicks "Regenerar seção" on `resumo` → regen in flight, submitted `secoes` captured.
2. During the flight the user edits the experiências draft and clicks "Salvar alterações" → `salvarEdicao` stacks the PRE-save experiências text (`empilharVersaoAtual`), writes the NEW text into `resultado.secoes`, sets badge `editado`.
3. Regen succeeds → `regenerar.onSuccess` replaces `resultado.secoes` WHOLESALE with the response's merged sections (CurriculoHome.tsx:274-283). Per the backend contract (D-07/SC1, `pipeline.py:169-179`), the response's sibling `experiencias` is the SUBMITTED (pre-save) text. The saved edit now exists nowhere: not displayed (clobbered by the swap) and not on the version stack (only the pre-save text was stacked). The badge still reads "Editado" for text that is no longer the edit.

This is exactly the class of silent loss the D-14/SC4 stack-before-mutate discipline was built to prevent. (The same-section variant — clean editor open, regen same section, save mid-flight — is recoverable because `onSuccess` stacks the then-current text before the swap, but the sibling path is not.)

**Fix:** Close the lock gap — the editor's own controls must respect the pending-op lock:
```tsx
// SectionEditor: accept a `locked` (long-op pending) prop
<button type="button" onClick={onSave} disabled={!canSave || locked} ...>
<button type="button" onClick={() => (dirty ? setConfirmandoDescarte(true) : onCancel())} disabled={locked} ...>
```
passing `locked={operacaoLongaPendente}` from CurriculoHome through ResumeResult/GeneratedSection (i.e., the op-pending part of `locksEdicao`, not `editor !== null`). Belt-and-braces: also guard the mutation-side write:
```ts
function salvarEdicao() {
  if (!editor || !resultado) return
  if (operacaoLongaPendente) return // never write under an in-flight wholesale swap
  ...
}
```

## Warnings

### WR-01: Backend max-length ceilings not enforced client-side → permanent misleading dead-end errors

**File:** `frontend/src/components/ResumeResult.tsx:269-277` (dica input), `frontend/src/pages/CurriculoHome.tsx:569-575, 603-609` (jd textarea/CTA)
**Issue:** The backend treats 422 as "a client bug, not a UI state" (`backend/app/routes/resume.py:17-19`), which obligates the client to mirror the bounds. The client enforces only the 80-char floor on `jd_text`; none of the ceilings are enforced:
- The dica input has no `maxLength`, but `RegenerarRequest.dica` is `Field(max_length=500)` (`resume.py:84`). A 501-char dica → 422 → `regenerar.onError` → section error panel with the generic hint "Tente regenerar novamente…" (CurriculoHome.tsx:297-300) — and every retry fails identically until the user guesses that the invisible dica is the cause.
- `jd_text` has no 20000-char ceiling client-side (`JD_MAX_LENGTH`, `resume.py:51`): an oversized paste → 422 on gerar (and on lint) → generic "Tente novamente" panels whose retry can never succeed.
- Secondary: a resumo edit has no length bound (`RESUMO_MAX_LENGTH = 8000` in `export.py:68`); a huge saved resumo poisons every subsequent regen/export POST with the same 422 dead-end.

**Fix:** Mirror the backend bounds in the inputs — `maxLength={500}` on the dica input, a max-char guard/hint on the JD textarea (mirroring the existing min-80 hint), and a bound on the resumo editor — so a 422 becomes unreachable from the UI.

### WR-02: ConfirmStrip docstring asserts a false data-safety invariant for the dirty-cancel path

**File:** `frontend/src/components/ConfirmStrip.tsx:26-28` (vs `frontend/src/components/SectionEditor.tsx:110` and `frontend/src/pages/CurriculoHome.tsx:477-479`)
**Issue:** The shared component's docstring claims: "the 'discarded' text is always stacked into Versões before anything proceeds (D-14), so nothing is ever irrecoverable" — explicitly enumerating the dirty-cancel edit confirmation among the strips it covers. That is false for the dirty-cancel path: `SectionEditor`'s discard confirmation goes straight to `onCancel` → `fecharEditor()` → `setEditor(null)`, dropping the dirty draft without stacking (unlike `confirmarRegenSobreEdicao`, CurriculoHome.tsx:383-396, which stacks first). The runtime behavior (explicit user-confirmed discard) is acceptable; the documented guarantee is not, and a maintainer relying on it when evolving these flows will introduce real, silent loss.

**Fix:** Correct the docstring to scope the stack-first guarantee to the regen/full-regen strips only, or make the claim true by stacking the dirty draft (as an `'editado'` version) in the discard path before closing.

## Info

### IN-01: An unrelated section's regen success silently dismisses a pending confirm strip

**File:** `frontend/src/pages/CurriculoHome.tsx:259-261`
**Issue:** `regenerar.onSuccess` begins with an unconditional `setStripRegen(null)` ("The pending D-14 confirm (if any) concluded with this attempt"). If the pending strip belongs to section A (dirty/editado) and the user regenerates section B, B's success closes A's confirmation without it ever being acted on — the user's pending intent is silently dropped. Only the strip's own section's attempt (or the confirmed path) should clear it.

**Fix:** `setStripRegen((prev) => (prev === variables.secao ? null : prev))`.

### IN-02: `ComparisonPanel`'s `texto` prop is ignored for the experiências branch

**File:** `frontend/src/components/ComparisonPanel.tsx:171-182, 210-232` (caller: `frontend/src/components/ResumeResult.tsx:641`)
**Issue:** For `secao === 'experiencias'` the panel computes everything from `entradas` and never reads `texto` — yet ResumeResult dutifully computes and passes `panelTexto={secoes.experiencias.map(...).join('\n\n')}`. The prop contract misleads: a future edit that renders `texto` on this branch would silently diverge from the per-entry marking logic.

**Fix:** Make `panelEntradas` authoritative in the type (`texto` optional/unused-only-for-non-experiencias, documented at the prop), or stop computing `panelTexto` for experiências at the call site.

### IN-03: Education date range renders " – 2019" when `start_date` is null

**File:** `frontend/src/components/ResumeResult.tsx:77-79, 694-698`
**Issue:** `dateRange(ed.start_date ?? '', ed.end_date)` substitutes an empty string for a missing start (`start_date` is optional in `EducationEntryDTO`), producing a malformed " – 2019" / " – atual" range in the card.

**Fix:** Render only the end (or only the start) when one side is absent, e.g. `end && !start ? end : dateRange(...)`.

### IN-04: `/lint` loads the profile after the paid LLM extraction call

**File:** `backend/app/resume/pipeline.py:64-68`
**Issue:** `run_lint_only` runs the keyword-extraction stage first and only then calls `load_profile()` for the lint. With a broken profile, every `/lint` request still consumes an OpenRouter call before failing with the profile error — wasteful, and inconsistent with `run_resume_pipeline`, which loads the profile first (pipeline.py:88).

**Fix:** Hoist `profile = load_profile()` above the `run_stage` call in `run_lint_only`.

### IN-05: Profile fetch-level failure renders a bare line without the house fail-loud convention

**File:** `frontend/src/pages/CurriculoHome.tsx:507-509`
**Issue:** `perfilQuery.isError` renders a single unstyled red line (`PERFIL_ERROR_TITLE`) with no hint about the terminal-only detail — inconsistent with the lint/gerar/export fetch-failure convention in the same file (red panel + generic "o detalhe técnico completo aparece no terminal" hint, WR-02 pattern from plan 03).

**Fix:** Render the same red-panel + hint pattern used for lint/gerar fetch failures.

---

_Reviewed: 2026-09-27T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
