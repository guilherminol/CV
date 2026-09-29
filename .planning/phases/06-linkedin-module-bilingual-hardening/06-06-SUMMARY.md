---
phase: 06-linkedin-module-bilingual-hardening
plan: 06
subsystem: phase-gate-uat
tags: [uat, checkpoint, linkedin, bilingual, deferred-verification, phase-gate]
requires:
  - 06-01 tracer slice (LinkedIn page skeleton, CharacterCounter, Copiar, gerar route)
  - 06-02 full quartet pipeline + lint + per-section regen (backend envelopes final)
  - 06-03 four-block result card + editors/versions/comparison + locking matrix
  - 06-04 deterministic QA core (glossario + bleed → the qa envelope key)
  - 06-05 "Verificação de idioma" QA panel + bilingual DoD harness (-m llm)
provides:
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-06-SUMMARY.md — the phase's UAT outcome record (resolved-as-deferred, run convention Phases 1/4/5)
  - Automation-green baseline at phase close (403 backend offline tests + frontend build + the 06-05 dedicated bilingual real-API LinkedIn run) for /gsd-verify-work 6
affects:
  - /gsd-verify-work 6 (re-surfaces the deferred UAT below plus the credits-gated DoD re-run as human_needed)
tech-stack:
  added: [] # zero new dependencies — checkpoint plan, no code changes
  patterns:
    - deferred-UAT recording per the run convention (05-04-SUMMARY pattern): never claim an unexecuted visual check (T-06-17 record honesty)
key-files:
  created:
    - .planning/phases/06-linkedin-module-bilingual-hardening/06-06-SUMMARY.md
  modified: []
requirements-completed: [LI-01, LI-02, LI-03, LI-04, LI-05]
decisions:
  - "Checkpoint pre-resolved 'deferred — record UAT' per the run convention (Phases 1/4/5; user unavailable — autonomous run); the automation gate ran FIRST and green before the deferral was recorded (the <fails_when> bar: the phase cannot close on red automation)"
  - "No visual check is claimed as passed — each deferred check carries its standing automated proof and exact re-verification instructions for /gsd-verify-work 6; the OpenRouter-credits DoD blocker is recorded with its resume action (WINDOWS.md entry 10), not masked"
metrics:
  duration: 6 min
  completed: 2026-09-29
status: complete
actuals:
  tokens: 2900 # chars/4 over the realized diff (docs-only: this SUMMARY)
  tasks: 1
  commits: 2 # MEASURED: git rev-list --count 062206e..HEAD (SUMMARY commit + final state/docs commit)
plan_head_before: 062206eb13e404a431bb746b3c2c64d65d049fc1
---

# Phase 6 Plan 06: End-of-Phase UAT Checkpoint (Copy-Paste + Counters + QA Panel + Max-Volume Backstop) Summary

**One-liner:** Phase 6 closed with the automation gate green (403 backend offline tests + frontend build, plus the 06-05 dedicated bilingual real-API LinkedIn DoD run) and the four human UAT areas recorded as explicitly deferred per the run convention — each with its standing automated proof and the /gsd-verify-work 6 re-surface pointer — with the standing OpenRouter-credits blocker on the full-file DoD re-run recorded alongside.

## What Was Done

Single checkpoint task (`checkpoint:human-verify`, gate blocking):

1. **Automation gate ran FIRST** (the checkpoint must not open against red automation — `<fails_when>`, run at SUMMARY time):
   - `cd backend && uv run pytest -q` → **403 passed, 9 deselected in 13.19s** (full offline suite, exactly the expected count; includes all 06-01..06-04 LinkedIn pipeline/schema/QA/regen/API vectors, 100% offline)
   - `cd frontend && npm run build` → **green** (tsc -b + vite, 85 modules, built in 459ms)
2. **Checkpoint resolved "deferred — record UAT"** — the interactive browser walkthrough was not run by the user (unavailable — autonomous run convention, same as Phases 1, 4, and 5). Per the plan's own design note, resolved-as-deferred is acceptable; it is recorded below with the re-surface path.

## Deferred Human Verification (Task 1 — resolved "deferred — record UAT")

The four checks below were **NOT executed and are NOT claimed as passed**. Automation was green immediately before the checkpoint (results above, run at SUMMARY time).

| # | Deferred check | What the human must do (from 06-VALIDATION.md §Manual-Only + plan Task 1) | Standing automated proof |
|---|----------------|---------------------------------------------------------------------------|--------------------------|
| 1 | **Copy-paste UX** (LI-05) | Generate in PT-BR; click Copiar on Headline, Sobre, each Experiência entry, and Habilidades; paste into a text editor; confirm pasted text equals displayed text (per-entry paste = that entry's descricao only) and each click showed Copiado! | `CopiarButton` (06-03, commit 03ebc3d) writes the exact displayed text via `navigator.clipboard.writeText`, Copiado! ~2 s with `aria-live="polite"`, pinned failure line; per-entry Copiar copies `descricao` ONLY (06-02 contract); the green build proves the component compiles and is mounted on every block/entry |
| 2 | **Counters + over-limit path** (LI-02/03/04, SC2) | Watch counters live-update while editing (amber ≥ 90%, red over); force a draft past a limit → red flag names the excess, Salvar alterações disables with the reduce-first hint; regen the section to recover; confirm nothing was ever truncated | `CharacterCounter` pure formatter/class functions (06-01); `LinkedinSectionEditor` maxLength client mirrors 220/2600/2000 + over-save guard with the `O texto excede o limite em {excesso} caracteres` hint (06-03); the D-07 limit-or-flag contract is pinned offline (schema/pipeline vectors incl. oversize guards: 3000-char sobre, 2500-char descricao validate cleanly — never truncated) AND asserted live against the real API in 06-05's dedicated bilingual run |
| 3 | **QA panel framing** (SC4/D-14) | On a PT-BR result: "Verificação de idioma" lists glossary substitutions ({de} → {para}) and/or amber bleed avisos ({termo} — {seção}) WITHOUT blocking Copiar; zero blocks show their loud zero lines; the legend is visible; on an EN run the neutral note renders | `LinkedinQaPanel` renders the 06-04 payload verbatim — no client-side recomputation exists; legend renders in BOTH branches (dict and null), EN note replaces only the two blocks (06-05, feb53cc); the qa envelope contract is pinned offline (pt-BR ok always `{glossario, bleed}` loud-empty lists, en ok always null; both generation-success swap paths only); 06-05's real-API dedicated run asserted the qa contract green for BOTH labels (linkedin-PT, linkedin-EN — 2 passed, 64.10s) |
| 4 | **Max-volume backstop** (UI-SPEC) | With a long Sobre (~2.600 chars), several experiências, and all disclosures open, confirm the page stays readable: blocks clearly separated, no cramping | Blocks are inline disclosures in normal flow per the UI-SPEC Component conventions (06-03 sibling components, no fixed heights or overflow-clipped containers); D-07 oversize guards prove max-volume content survives the full data layer untruncated; green build. (The readability judgment itself is inherently visual — that is the human check.) |
| 5 | **DoD re-run standing blocker** (carried from 06-05, WINDOWS.md entry 10) | Top up OpenRouter credits at https://openrouter.ai/settings/credits, then re-run `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q` and confirm the FULL-FILE run exits 0 | The DoD mechanism is proven: the dedicated run `uv run pytest tests/test_llm_harness.py -m llm -q -k linkedin` passed BOTH labels green (2 passed, 64.10s) before the 402 credit wall; offline suite green (403). The full-file run failed ONLY on account-level 402 Payment Required (also hits pre-existing resume tests) — no code change can or should mask it |

**Re-surface path:** the phase-level verify step re-surfaces all five rows as `human_needed` UAT for `/gsd-verify-work 6` — the same pattern as Phases 1, 4, and 5 (05-04-SUMMARY deferred table). Prohibition honored: no deferred check silently dropped; every row names its standing proof, and row 5 names its resume action.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Checkpoint: end-of-phase UAT — copy-paste, counters, QA panel, max-volume backstop (resolved deferred) | (this docs commit) | .planning/phases/06-linkedin-module-bilingual-hardening/06-06-SUMMARY.md |

## Verification Results

- `cd backend && uv run pytest -q` → **403 passed, 9 deselected in 13.19s** (full offline suite — exactly the plan's expected count)
- `cd frontend && npm run build` → **green** (tsc -b + vite, 85 modules, 459ms)
- SC4 DoD standing state: **mechanism proven** (06-05 dedicated bilingual LinkedIn real-API run green on both labels), **full-file run pending credits** (row 5 above; WINDOWS.md entry 10)
- UAT record present (above) — all four manual-only areas resolved-as-deferred with standing proofs and the re-surface pointer

## Deviations from Plan

None — the plan anticipated the deferral path itself ("resolved as `deferred — record UAT` … a deferral is the honest outcome" in how-to-verify); execution followed it exactly. No code changes were made by this plan (files_modified: [] honored).

## Auth / Spend Gates

- **OpenRouter credit exhaustion (402 Payment Required)** — standing from 06-05, unchanged at phase close (no re-run attempted: the account balance cannot complete the full-file run, and the dedicated LinkedIn proof already stands). Required user action: add credits at https://openrouter.ai/settings/credits, then re-run `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q` to claim the full-file DoD green. NOT mocked to green.

## Notes for /gsd:verify-work

- Offline gate: **403 passed, 9 deselected**. Build gate: **green**.
- Real-API gate: LinkedIn fixtures proven green (06-05 dedicated run, both labels, no skips, 64.10s); the full-file `-m llm` green is pending the credit top-up + one re-run command. Until then treat WINDOWS.md entry 10 as the open item.
- The four human checks and their per-check standing proofs are in the Deferred Human Verification table above; re-surface them as `human_needed` UAT per the run convention.
- The checkpoint does not gate on avisos (D-14 discipline): QA findings never block Copiar — pinned offline and rendered verbatim from the backend payload.

## Self-Check: PASSED

- Created file verified on disk: .planning/phases/06-linkedin-module-bilingual-hardening/06-06-SUMMARY.md (this file — docs-only plan, no code files).
- Automation results recorded from live runs at SUMMARY time (13.19s / 459ms).
- `git rev-list --count 062206e..HEAD` = 2 (SUMMARY commit + final state/docs commit, matching the plan_head_before ledger).
