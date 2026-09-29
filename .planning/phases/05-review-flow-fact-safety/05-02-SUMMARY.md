---
phase: 05-review-flow-fact-safety
plan: 02
subsystem: review-editing-versioning
tags: [review-flow, inline-editing, version-stack, locking-matrix, confirm-strips, react]
requires:
  - 05-01 regen mutation + per-section action rows (the shell this plan extends)
  - Phase 4 export-state reset triple (extended to every displayed-content mutation)
  - Phase 4 ExportarSecoes displayed-state contract (edits flow to export/self-check via resultado.secoes)
provides:
  - ConfirmStrip.tsx — the one shared inline amber confirm strip (three uses, zero browser dialogs)
  - SectionEditor.tsx — per-section textarea editor + save/cancel + dirty-confirm + zero-items guard
  - SectionVersionsPanel.tsx — newest-first version rows + Restaurar versão (+ SectionVersion/OrigemBadge/SectionValor types)
  - tri-state badge (Gerado / Do perfil / Editado) + permanent D-02 policy line in the card
  - CurriculoHome editor/versions/origens/strip atoms + empilharVersaoAtual + derived locking booleans
affects:
  - 05-03 (comparison panel joins the same GeneratedSection action row — Comparar slot reserved)
  - 05-04 (UAT checklist exercises all four destructive paths)
tech-stack:
  added: [] # zero new dependencies (session React state only, D-01)
  patterns:
    - stack-before-mutate via ONE empilharVersaoAtual helper on all four destructive paths
    - derived locking booleans from state atoms (editor open / long-op pending) — no ad-hoc disabled logic
    - dirty derived (draft !== inicial), never stored; drafts live at page level for the D-14 pre-close stack
    - component-owned types (SectionVersion in SectionVersionsPanel, LintPanel's LintOk precedent)
key-files:
  created:
    - frontend/src/components/ConfirmStrip.tsx
    - frontend/src/components/SectionEditor.tsx
    - frontend/src/components/SectionVersionsPanel.tsx
  modified:
    - frontend/src/constants/ui.ts
    - frontend/src/components/ResumeResult.tsx
    - frontend/src/pages/CurriculoHome.tsx
decisions:
  - "empilharVersaoAtual reads the closure state at call time; long-op locks guarantee the displayed state cannot change between mutate() and onSuccess, so the stacked text is always the text being replaced"
  - "regen-over-edit stacks the DIRTY DRAFT at confirm time (before the editor closes) only when it passes the validity guard; the displayed text is stacked by the regen-success handler — no duplicate entries, nothing lost"
  - "version stacks persist across full regens (never cleared in-session) — the D-14 promise 'cada versão atual fica guardada em Versões' requires the stacked versions to stay restorable after the wholesale swap; disclosures reset"
  - "the Zone 1 form CTA routes through the same D-14 full-regen confirm as the header button (same destructive mutation); full regen is disabled outright while any editor is open"
  - "a section regen success closes an editor open on THAT section — a stale editor saving an old draft over regenerated text is a silent-overwrite hazard"
  - "TEXTAREA_CLASSES + badge class strings promoted to constants/ui.ts (IN-04) so the editor/form/panel cannot drift"
metrics:
  duration: 17 min
  completed: 2026-09-29
status: complete
actuals:
  tokens: 15200 # chars/4 over the realized diff (60910 diff chars, 965+/60- lines)
  tasks: 3
  commits: 3 # MEASURED: git rev-list --count f2c47c3..HEAD
plan_head_before: f2c47c36a02e954207f045e69121af2a61ec40a8
---

# Phase 5 Plan 02: Inline Editing + SC4 Safety Net Summary

**One-liner:** Every generated section edits inline in the result card (tri-state badge, dirty-confirm, zero-items guard), prior versions stack in session memory with restore on all four destructive paths, and the full UI-SPEC locking matrix plus three inline amber confirm strips guarantee regeneration never silently destroys edits — under the permanently visible D-02 edit-policy line.

## What Was Built

- **`frontend/src/components/ConfirmStrip.tsx`** — the ONE shared amber inline strip (UI-SPEC "panels, not modals", load-bearing): `⚠` aria-hidden message + optional note + Continuar/Descartar-style button pair. Used by all three confirm sites: dirty-cancel edit, regen-over-edit, full-regen-with-edits. `grep -RIn "window\.confirm|window\.alert|window\.prompt" frontend/src` → zero matches.
- **`frontend/src/components/SectionEditor.tsx`** — controlled textarea editor at the UI-SPEC granularity (Resumo whole string; Experiência per entry — bullets one per line, company/title fixed; Habilidades one skill per line; aria-label `Editar {seção}`). Footer: `Salvar alterações` (compact secondary, disabled with the `Guarde pelo menos um item — a seção não pode ficar vazia.` guard while the parsed list is empty — resumo included, matching the envelope min_length=1) · `Cancelar edição` (quiet; clean → immediate revert, dirty → the inline ConfirmStrip) + the D-02 policy line repeated. Exports `SecaoEditorState`, `dividirLinhas` (split/trim/drop-empties), `textoEditorValido`.
- **`frontend/src/components/SectionVersionsPanel.tsx`** — per-section disclosure panel: intro line, newest-first rows (stable `${secao}-${index}` keys), each with origin Badge (Gerado/Editado per the version's recorded origem) + `Restaurar versão` quiet button + `line-clamp-2` plain-text snippet. Owns `SectionVersion {secao, origem, valor}` / `OrigemBadge` / `SectionValor` types. In-memory only, no cap (D-01/D-08).
- **`frontend/src/components/ResumeResult.tsx`** — permanent D-02 policy line directly under the card header (`text-xs text-gray-600`, ⚠ aria-hidden); tri-state Badge (Editado = solid blue-600/white, class strings in constants per IN-04); action rows extended with `Editar seção` (Experiência gets per-entry `Editar entrada` + click affordances on every text block); Versões toggle (`Versões` disabled at 0, `Versões (N)` from 1, `aria-expanded`, read-only under long ops); panel disclosure; the regen-over-edit strip (under the action row, under the editor when one is open) and the full-regen strip (under the card header). Passthrough "Do perfil" sections untouched (D-13).
- **`frontend/src/pages/CurriculoHome.tsx`** — session state atoms: per-section `versoes` stacks, `origens` badges, the ONE-at-a-time `editor` ({secao, entryIdx, draft, inicial}; dirty derived), `versoesAbertas`, `stripRegen`/`stripGerarCompleta` pending strips, `gerarConfirmadoRef`. ONE `empilharVersaoAtual(secao)` helper called at the top of ALL FOUR destructive paths: edit save, section regen success, restore, confirmed full regen (9 grep lines). Every displayed-content mutation runs the export-state reset triple; edits/restores never touch cobertura chips. Derived locking booleans (`operacaoLongaPendente`, `locksEdicao`) implement the UI-SPEC interaction table: long op → all mutation controls disabled with Comparar/Versões read-only; editor open → Exportar PDF + Gerar novamente + every Restaurar versão disabled while Regenerar seção stays enabled (own section routes through the D-14 strip; siblings regenerate directly). D-14 gates: regen on an Editado section or dirty editor → strip (confirm stacks the dirty draft first, closes the editor, issues; Manter edição cancels); full regen with any Editado section → strip under the header (confirm sets the flag; gerar.onSuccess stacks EVERY section, resets all badges to Gerado, keeps the stacks restorable).
- **`frontend/src/constants/ui.ts`** — all Phase 5 PT-BR strings (policy line, badge, editor, guard, three strip copy sets, Versões labels) + `TEXTAREA_CLASSES` promoted from CurriculoHome (single definition; the JD form textarea imports it — no duplicate literal remains).

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Policy line + tri-state badge + inline editor with dirty-confirm | 87c7cf7 | constants/ui.ts, ConfirmStrip.tsx (new), SectionEditor.tsx (new), ResumeResult.tsx, CurriculoHome.tsx |
| 2 | Version stack panel + restore (SC4 prior versions accessible) | b3c2bb9 | SectionVersionsPanel.tsx (new), ResumeResult.tsx, CurriculoHome.tsx |
| 3 | SC4 locking matrix + D-14 confirm strips | 94659b9 | CurriculoHome.tsx, ResumeResult.tsx |

## Verification Results

- `cd frontend && npm run build` → **green after every task** (tsc -b + vite, final 381ms)
- Task 1 greps: TEXTAREA_CLASSES in constants/ui.ts (1) + CurriculoHome.tsx (3); `window.confirm` → zero matches; empilharVersaoAtual ≥2 sites at task close
- Task 2 greps: "Restaurar versão" + "line-clamp-2" present in SectionVersionsPanel.tsx and constants/ui.ts; restore path references the helper before any state write
- Task 3 greps: empilharVersaoAtual = 9 lines in CurriculoHome.tsx (≥4; all four destructive paths); `<ConfirmStrip` = 3 in ResumeResult.tsx + 1 in SectionEditor.tsx; zero browser-dialog calls
- `cd backend && uv run pytest -q` → **259 passed, 7 deselected** (zero regressions; no backend changes)
- T-05-06 posture: `dangerouslySetInnerHTML` → zero matches (all content JSX text children)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical functionality] The Zone 1 form CTA routes through the D-14 full-regen confirm + editor lock**
- **Found during:** Task 3
- **Issue:** The plan pins the full-regen confirm for "Gerar novamente", but the Zone 1 "Gerar currículo" submit triggers the SAME gerar mutation and replaces the mounted result — leaving it ungated would preserve a silent-destroy path for edits (and a replace-under-open-editor path).
- **Fix:** Both entry points route through `tentarGerarCompleta()` (strip only when a section is Editado; unchanged no-confirm Phase 3 behavior otherwise) and both disable while an editor is open.
- **Files modified:** frontend/src/pages/CurriculoHome.tsx, frontend/src/components/ResumeResult.tsx
- **Commit:** 94659b9

**2. [Rule 2 - Correctness] Section regen success closes an editor open on that section**
- **Found during:** Task 1 (regen onSuccess wiring)
- **Issue:** A regen swap under an open editor would leave a stale draft whose next "Salvar alterações" would silently overwrite the regenerated text.
- **Fix:** `setEditor(prev => prev?.secao === variables.secao ? null : prev)` in the ok branch.
- **Files modified:** frontend/src/pages/CurriculoHome.tsx
- **Commit:** 87c7cf7

**3. [Rule 3 - Blocking] tsc noUnusedLocals scope adjustments inside Task 1**
- **Found during:** Task 1 (verify run)
- **Issue:** The `versoes` atom (consumed by Task 2's panel) and the `editandoAqui` prop (consumed by Task 3's strip placement) had no reader at Task 1 scope; tsc -b failed with TS6133.
- **Fix:** `_versoes` underscore-exempt until Task 2 renamed it; `editandoAqui` deferred to Task 3 where its consumer landed. Both resolved within this plan.
- **Files modified:** frontend/src/pages/CurriculoHome.tsx, frontend/src/components/ResumeResult.tsx
- **Commit:** 87c7cf7 / 94659b9

### Documented decisions (planner-discretion calls)

- **D-14 stacking timing:** the dirty draft is stacked at confirm time (it would be lost when the editor closes; empty drafts are skipped — nothing of value); the displayed text is stacked by the pinned regen-success handler. Satisfies "confirming stacks first, then regenerates" against the destructive write, with no duplicate stack entries.
- **Version stacks persist across full regens:** the D-14 promise requires the just-stacked versions to remain restorable after the confirmed swap; badges reset to Gerado, disclosures close, stacks stay.

## Auth Gates

None — fully offline execution, no credentials touched.

## Known Stubs

None — every control is wired to real state/endpoint paths; no placeholder data.

## Threat Flags

None — no new network endpoints, auth paths, file access, or schema changes. T-05-06 held (JSX-text-only rendering, controlled textarea); T-05-07 mitigated by the four-path stack invariant + permanent policy line + inline strips; T-05-08 unchanged (session-only state, D-01).

## Notes for 05-03 (comparison panel)

- The `Comparar com o perfil` toggle slot is reserved in the GeneratedSection action row order (Editar · Comparar · Versões · dica · Regenerar) — insert it between the edit control and the Versões toggle; under long ops it must stay usable read-only (same treatment as the Versões toggle).
- `GeneratedSection` already carries the disclosure pattern to copy (`versoesAberta` + panel after `{children}`); the comparison panel renders the same way.
- The left-column facts source is the `perfil` prop already mounted in ResumeResult; edits/restores deliberately never touch cobertura chips, so the comparison's "Texto no currículo" column must read `resultado.secoes` (it does — the single displayed-state source).
- `OrigemBadge`/`SectionVersion`/`SectionValor` live in SectionVersionsPanel.tsx if the comparison panel needs the badge classes (BADGE_GERADO_CLASSES/BADGE_EDITADO_CLASSES in constants/ui.ts).

## Self-Check: PASSED

- Files exist: all 6 key-files verified on disk (3 created via git `create mode`, 3 modified in the commit manifests)
- Commits exist: 87c7cf7, b3c2bb9, 94659b9 in `git log` (3 MEASURED from ledger f2c47c3..HEAD)
- Clean tree: no uncommitted source changes; untracked files are pre-existing .planning/ orchestrator artifacts only
- Zero file deletions across the plan's commits (`git diff --diff-filter=D` empty)
