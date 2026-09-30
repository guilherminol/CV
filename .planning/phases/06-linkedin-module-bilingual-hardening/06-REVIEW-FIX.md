---
phase: 06-linkedin-module-bilingual-hardening
fixed_at: 2026-09-30T14:03:05Z
review_path: .planning/phases/06-linkedin-module-bilingual-hardening/06-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 6: Code Review Fix Report

**Fixed at:** 2026-09-30T14:03:05Z (worktree run `rf-06-24546-1790775796`, branch `gsd-reviewfix/06-24546`)
**Source review:** .planning/phases/06-linkedin-module-bilingual-hardening/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 9 (WR-01..WR-06 + IN-01..IN-03, per the fix request)
- Fixed: 9
- Skipped: 0

## Fixed Issues

### WR-01: Section-regen response mutates sibling text via the glossário

**Files modified:** `backend/app/linkedin/qa.py`, `backend/app/linkedin/pipeline.py`, `backend/tests/test_linkedin_regen_pipeline.py`
**Commit:** 5bf1399
**Status:** fixed — requires human verification (logic change)
**Applied fix:** `run_linkedin_qa` gained `apply_glossario_to: str | None = None` — the glossário MUTATION is confined to the regenerated section id while detection still covers the whole merged state. The regen path passes `apply_glossario_to=secao`; the full-gerar path passes nothing (all surfaces mutate, unchanged). This is stronger than snapshot/restore: the report can never claim a substitution the displayed text does not carry (D-13 text/report agreement preserved — with snapshot/restore, sibling glossário rows would overstate). Two regression tests added: the reviewer's exact vector (live `machine learning → aprendizado de máquina` pair, regen headline over a submitted sobre containing the term → `envelope["secoes"]["sobre"] is submitted.sobre`, zero glossário rows, sibling bleed row still present) and the complementary vector (the pair matching the TARGET is still applied and reported, sibling untouched).

### WR-02: `_align_experiencias` silently drops surplus returned entries

**Files modified:** `backend/app/linkedin/pipeline.py`, `backend/tests/test_linkedin_pipeline.py`
**Commit:** be98e2a
**Status:** fixed — requires human verification (logic change)
**Applied fix:** In the all-paired path, surplus returned entries now ride after the matched ones in RETURNED order (`matched.extend(returned[i] for i in range(len(returned)) if i not in used)`), mirroring the keep-everything discipline of the pairing-failure fallback. Regression test: 1 profile experience + 3 returned entries → all 3 come back in order, limites index-aligned (len 3).

### WR-03: Frontend anchors experiência headers to profile facts by index in fallback mode

**Files modified:** `frontend/src/pages/LinkedInHome.tsx`
**Commit:** 5359fb8
**Status:** fixed — requires human verification (logic change)
**Applied fix:** Option (b), client-side verification before anchoring: `anchorOk = perfilExp !== undefined && fold(perfilExp.company) === fold(entrada.company)` — the PROFILE FACT header renders only when the companies fold-match; otherwise the entry's own generated `company`/`title` (so per-entry Copiar always copies what its header shows). No envelope change (no backend wire drift); `fold` imported from `../lib/comparison`. Component docstring updated.

### WR-04: Comparison panel pairs every same-company entry to the FIRST profile entry

**Files modified:** `frontend/src/components/LinkedinComparisonPanel.tsx`
**Commit:** e8e0035
**Status:** fixed — requires human verification (logic change)
**Applied fix:** Mirrored the backend's first-unused-match consumption: a `used` Set of profile indices + `findIndex((exp, i) => !used.has(i) && fold(exp.company) === fold(entrada.company))` — same-company generated entries each ground against one DISTINCT profile entry (LI-04/adjacency vector), no duplicated facts rows.

### WR-05: Zero-experience profiles can never generate

**Files modified:** `backend/app/linkedin/pipeline.py`, `backend/tests/test_linkedin_pipeline.py`, `frontend/src/pages/LinkedInHome.tsx`, `frontend/src/constants/ui.ts`
**Commit:** 9387d22
**Status:** fixed — requires human verification (logic change)
**Applied fix:** Backend: `_process_experiencias` empty-list guard is now profile-aware — `if not returned and profile_experiences:` (the exact `_process_habilidades` mirror); raw detail gained "(profile has experiences to draw from)". Module docstring's LOUD-EMPTY bullet updated. A zero-experience profile now completes gerar with `experiencias: []` (regression test with `minimal_profile()` + empty experiences → 4 stage calls, empty list + empty limites). Frontend: the zero line is differentiated per cause — profile-empty keeps `LINKEDIN_EXPERIENCIA_ZERO`; the defensive list-empty arm renders the new `LINKEDIN_EXPERIENCIA_LISTA_ZERO` ("Nenhuma experiência foi gerada nesta execução.") and no longer claims "no perfil" when the profile has entries.

### WR-06: Regen dead-end 422 on a shortened objetivo

**Files modified:** `frontend/src/pages/LinkedInHome.tsx`
**Commit:** a4adf98
**Status:** fixed — requires human verification (logic change)
**Applied fix:** Derived `objetivoCurto`/`objetivoCurtoHint` next to the CTA gate. Every regen entry point now gates on the same 80-char floor: per-section Regenerar buttons AND the header Gerar novamente button are disabled with the `LINKEDIN_OBJETIVO_TOO_SHORT_HINT` as their `title`; `tentarRegenerarSecao`/`regenerarSecaoAgora`/`tentarGerarCompleta` carry the guard too (never POST a request the bound rejects). The header button was included deliberately — it is the same dead-end class (full gerar with the current form objetivo), one atomic fix.

### IN-01: `ContadorLimite` defined inside the render body

**Files modified:** `frontend/src/pages/LinkedInHome.tsx`
**Commit:** dd2b999
**Status:** fixed (mechanical — stable identity, no closure variables needed)
**Applied fix:** Hoisted to module scope next to `LinkedinLintPanel`, with a comment stating why (fresh type identity per render → subtree unmount/remount).

### IN-02: QA bleed labels described as the "profile-fact anchor"

**Files modified:** `backend/app/linkedin/qa.py`
**Commit:** 2050601
**Status:** fixed (comment-only — the reviewer's sanctioned minimum)
**Applied fix:** The bleed-label comment now states the truth: experiência rows carry the RETURNED company string (the alignment contract lets it deviate from the profile fact), and the header above the same text may show the profile-fact spelling (per WR-03's client-side verification). Overwriting `entry.company` post-alignment was rejected: it would break the pinned "display anchors ride along" contract (test_linkedin_pipeline.py asserts the returned company strings) for a label cosmetic.

### IN-03: Orphaned per-entry version stacks unreachable after count-changing swaps

**Files modified:** `frontend/src/pages/LinkedInHome.tsx`, `frontend/src/constants/ui.ts`
**Commit:** 9f5ac5e
**Status:** fixed — requires human verification (logic change)
**Applied fix:** Both halves of the reviewer's option A, made complete: (1) the group Versões count reads the STACKS themselves (every `experiencias-N` key), so orphaned stacks stay counted by the toggle; (2) orphaned stacks (indices >= current list length) render as rows inside the open group panel under a new `VERSOES_EXPERIENCIA_ORFAAS_NOTA` line, with Restaurar disabled and a no-op handler (restoring into a nonexistent index would remove the version from its stack with nowhere to write it). Nothing is silently unreachable; "never capped, never silently dropped" holds literally.

## Skipped Issues

None — all 9 in-scope findings were fixed.

## Verification

- **Where the gates ran:** inside the isolated review-fix worktree `.claude/worktrees/rf-06-24546-1790775796` (deps installed there: `uv` backend venv + `npm ci`). The numbers below are NOT reproducible from the main checkout until the fast-forward lands and deps exist there; the worktree (with its venv/node_modules/dist) is removed at cleanup.
- **Backend:** baseline re-run in the worktree BEFORE any fix: `403 passed, 9 deselected` (matches the stated baseline; 4 SPA-mount tests initially failed until `frontend/dist` was built in the worktree). After all fixes: `407 passed, 9 deselected` — baseline + 4 new regression tests (2 × WR-01, 1 × WR-02, 1 × WR-05), zero pre-existing failures.
- **Frontend:** `npm run build` (tsc -b + vite) green after every frontend-touching fix; `npx oxlint` clean on every modified file.
- **Logic caveat:** WR-01..WR-06 and IN-03 change conditions/pairing logic that syntax checks cannot prove semantically — each is flagged "requires human verification" above for the developer to confirm before the phase proceeds to verification.

---

_Fixed: 2026-09-30T14:03:05Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
