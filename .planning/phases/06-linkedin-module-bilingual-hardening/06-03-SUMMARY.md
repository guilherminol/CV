---
phase: "06"
plan: "03"
subsystem: linkedin-frontend
tags: [linkedin, react, tanstack-query, clipboard, regen, versions, comparison, tailwind]
requires:
  - 06-02 backend envelopes: gerar/regenerar ok shape {status, idioma, secoes{headline,sobre,experiencias[entries],habilidades}, limites{headline,sobre,experiencias[index-aligned],habilidades{contagem,limite}}} + POST /api/linkedin/lint (verbatim run_lint_only reuse)
  - Phase 5 mechanics: stack-before-mutate + wholesale swap (CurriculoHome regen onSuccess), sibling-drift defense, ConfirmStrip trio, D-14 gates, locking-boolean derivation
  - 06-01 LinkedInHome tracer skeleton + CharacterCounter + gerarLinkedin client
provides:
  - complete LinkedIn page product surface: debounced lint zone + four-block result card in fixed order (Headline → Sobre → Experiência → Habilidades)
  - CopiarButton (D-08) — clipboard affordance with Copiado! feedback + pinned failure line, reused on every block/entry
  - LinkedinSectionEditor (D-12 sibling) — per-block maxLength client mirrors, over-limit save guard, Habilidades one-skill-per-line granularity
  - LinkedinComparisonPanel (D-09/D-10/D-11 sibling) — Texto no LinkedIn header, adapted legend, company fold-match + all-entries fallback
  - regenerarSecaoLinkedin client (dica-key omission) + per-block regen mutations with stack-before-mutate + sibling-drift defense + failure-never-blanks
  - full locking matrix (operacaoLongaPendente / locksEdicao) per the UI-SPEC interaction table
affects:
  - 06-04/06-05 (QA panel "Verificação de idioma" mounts below this result card; bilingual harness drives the same page contract)
tech-stack:
  added: []
  patterns:
    - stack-before-mutate on EVERY destructive path (edit save, regen success, restore, discard, confirmed full regen) — versions survive every swap (D-11/D-14)
    - sibling components over generalizing shipped Currículo components (UI-SPEC scope fence; reuse via import, divergence via new files)
    - wholesale swap from responses, never client-side merge; QA-style payload never recomputed client-side
    - honest-information counters: pure singular/plural functions, no invented limits (D-05)
key-files:
  created:
    - frontend/src/components/CopiarButton.tsx
    - frontend/src/components/LinkedinSectionEditor.tsx
    - frontend/src/components/LinkedinComparisonPanel.tsx
  modified:
    - frontend/src/pages/LinkedInHome.tsx
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
decisions:
  - SectionVersionsPanel was Currículo-typed (secao: SecaoId, valor: SecoesDTO[SecaoId]) — per the plan's check instruction, the sibling choice was taken: version rows render via a local LinkedinVersaoRow inside LinkedInHome rather than modifying the shipped component (scope fence).
  - Experiência versions are PER ENTRY (keyed experiencias-{i}, profile-order aligned) with ONE group-level Versões toggle counting all entry stacks — the UI-SPEC anatomy gives the group a single toggle while stacks stay per entry.
  - Headline/Sobre comparison grounds suspect tokens against the WHOLE-profile facts blob while the facts column shows the profile summary (the 05-03 resume-summary precedent — a headline/About legitimately synthesizes the entire profile).
  - Regen request builders mirror Phase 5: the dica key is OMITTED when blank (extra=forbid hygiene); the experiência group is one regen unit (secao='experiencias').
  - REGEN_*/strip/comparison-reusable strings reuse the Currículo constants verbatim (UI-SPEC "reused" rows); only LinkedIn-scoped copy (lint title/clear, zero line, skills count, editor over-limit hint, comparison header/legend, DICA_MAX_CHARS mirror, sobre/experiencia limits) became LINKEDIN_* constants.
  - Editor save-guard reality: backend output can arrive OVER the limit (D-07 flagged, never truncated), so the editor pre-fill can start over-limit and Salvar stays disabled with the reduce-first hint until reduced — maxLength alone cannot produce that state.
metrics:
  duration: 17 min
  completed: 2026-09-29
actuals:
  tokens: 23802 # chars/4 over the realized diff (95210 diff chars)
  tasks: 3
  commits: 3 # measured: git rev-list --count 2d25d9c..HEAD
plan_head_before: 2d25d9c48c1dde2115dfaac996b7bae13cdfb5a9
status: complete
---

# Phase 6 Plan 3: LinkedIn Frontend Product Surface Summary

**One-liner:** the LinkedIn page now delivers the full UI-SPEC Zone 1-3 contract — debounced non-blocking lint, four blocks in fixed display order with profile-fact-anchored experiência sub-blocks, Copiar everywhere with Copiado! feedback, honest per-block/per-entry counters and over-limit flags, one-at-a-time inline editing with the over-save guard, per-entry version stacks with restore, deterministic amber comparison, per-block/group regeneration with sibling-drift defense, and the complete locking matrix — all Phase 5 mechanics, Currículo untouched.

## What Was Built

- **Task 1 — lint zone + four-block card:** `fetchLinkedinLint` (POST /api/linkedin/lint) behind the exact Phase 3 debounce mechanism (800 ms, ≥ min trimmed chars, pending renders nothing); LintPanel structure verbatim with LinkedIn-scoped title/clear, backend avisos verbatim, Currículo fetch-failure convention. `LinkedinSecoesDTO`/`LinkedinLimitesDTO` extended to the full 06-02 envelope (index-aligned experiências limites, habilidades {contagem, limite}). Four blocks rendered from the static `BLOCOS_FIXOS` array (LI-01/ordering provable by code inspection); experiência sub-block headers read PROFILE facts (company — title, run language) with per-entry Copiar of `descricao` ONLY; habilidades renders the prioritized ordered list with the pure singular/plural count line (no fake `/Y`); CharacterCounter + red over-limit flag per block/entry (Copiar stays enabled). New `CopiarButton` (D-08): exact displayed text to the clipboard, `Copiado!` ~2 s with `aria-live="polite"`, pinned red failure line persisting until the next success. Gerado/Editado badges per block/entry mounted.
- **Task 2 — editors + versions + comparison:** `LinkedinSectionEditor` sibling (shipped SectionEditor untouched): TEXTAREA_CLASSES verbatim, per-block maxLength client mirror (220/2600/2000; habilidades unbounded), over-limit save guard with `O texto excede o limite em {excesso} caracteres — reduza antes de salvar.`, Habilidades one-skill-per-line via the reused `dividirLinhas` + zero-items EDIT_SAVE_GUARD, dirty cancel through the reused amber ConfirmStrip. Version stacks per block AND per experiência entry (sibling rows: origin badge + Restaurar versão + line-clamp-2); every restore stacks the current version first. `LinkedinComparisonPanel` sibling: `Texto no LinkedIn` right column, adapted legend ending `Confira você mesmo antes de copiar.`, zero-suspects line + fallback note + sr-only mark suffix reused verbatim, comparison.ts fold/numeral mechanics reused as-is, habilidades facts grouped under category sublabels as plain text. Dica state + Adicionar dica toggles (500-char client mirror) wired per block/group feeding Task 3's mutations. Locking booleans derived once; one editor at a time.
- **Task 3 — regen + locking + failure-never-blanks:** `regenerarSecaoLinkedin` with the dica-key omission (extra=forbid hygiene); per-block `Regenerar seção` (group = one unit) with in-flight labels + the "outras seções permanecem inalteradas" line. Regen success stacks the target FIRST (every entry for the group), then the sibling-drift defense compares each sibling's current JSON to the submitted snapshot and stacks drift BEFORE the wholesale swap; badges → Gerado; an editor open on the regenerated block closes (stale-draft hazard). Full `Gerar novamente` (header + form CTA) routes through the D-14 strip verbatim; the confirmed path stacks every block/entry and version stacks survive the swap. Locking matrix per the UI-SPEC table: pending ops disable CTA/Gerar novamente/Regenerar/edit controls/Restaurar/dica while Comparar/Versões toggles and every Copiar stay usable; an open editor freezes its own Salvar/Cancelar. Failed regen renders the red panel INSIDE the owning block with prior text intact; a failed gerar keeps any prior result mounted.

## Tasks Completed

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | Lint zone + four-block result card (experiência group, skills list, Copiar) | 03ebc3d |
| 2 | Inline editor + versions + comparison (Phase 5 mechanics on LinkedIn blocks) | e1de0f1 |
| 3 | Regen wiring + locking matrix + failure-never-blanks | e0f9aa2 |

## Verification

- `cd frontend && npm run build` → **green after every task** (tsc -b drift gate; final build 84 modules)
- `cd backend && uv run pytest -q` → **350 passed, 7 deselected** at plan end (exactly the 06-02 baseline — no accidental backend touch; only frontend files in the plan's diffs)
- Manual smoke (dev servers: generate → four ordered blocks with counters; edit/save/restore; compare; regen; copy each block type; over-limit edit guard) is deferred to the phase's end-of-phase human verification per `human_verify_mode: end-of-phase` (06-01 precedent); the max-volume readability backstop is staged for the same UAT pass.

## Deviations from Plan

None — plan executed exactly as written. (One mechanical pre-commit fix inside Task 1's own authoring: a typo'd constant reference caught by tsc before commit; no behavior change. The Task 2 sibling choices — LinkedinSectionEditor/LinkedinComparisonPanel files + local version rows — are the plan's own sanctioned branch: "if a prop is Currículo-typed, note the sibling choice in the summary rather than modifying shipped components".)

## Known Stubs

None created by this plan. The LinkedIn result card is fully wired to the live 06-02 envelopes; the QA panel ("Verificação de idioma") is intentionally absent — it belongs to 06-04/06-05 per the phase plan set, mounting below this card.

## Self-Check: PASSED

- Created files verified on disk (3 created, 3 modified — all in the task file lists).
- Commits verified in git log: 03ebc3d, e1de0f1, e0f9aa2.
- `git rev-list --count 2d25d9c..HEAD` = 3 (matches the commits ledger; no uncommitted code changes).
