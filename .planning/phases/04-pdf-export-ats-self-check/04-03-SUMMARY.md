---
phase: 04-pdf-export-ats-self-check
plan: 03
subsystem: frontend
tags: [react, react-query, export, self-check, blob-download, ats, ui-spec, deferred-uat]

# Dependency graph
requires:
  - phase: 04-pdf-export-ats-self-check (plan 02)
    provides: POST /api/resume/exportar envelope contract (ok={status, filename, pdf_base64, selfcheck{ordem, sobrevivencia, gate}} | erro={status, erros}), normative ordem row ids (contato + section_keys), verbatim PT-BR failure lines
  - phase: 03-resume-vertical-slice
    provides: CoberturaItemDTO chip semantics (KeywordsPanel), ErrorPanel verbatim-line discipline, CurriculoHome useMutation envelope branching + aria-live region, PRIMARY_BUTTON_CLASSES, GerarResponse displayed-state fields (D-10)
provides:
  - frontend/src/api/client.ts — ExportarResponse discriminated union + SelfCheckDTO + exportarCurriculo() + downloadPdf() blob helper (backend-filename-only, D-11); header names 04-02 as the normative pair ("change BOTH together", tsc -b drift gate)
  - frontend/src/constants/ui.ts — EXPORTAR_*/SELFCHECK_* PT-BR constants (UI-SPEC Copywriting Contract verbatim) + SELFCHECK_ORDEM_LABELS map + counts-only comment block
  - frontend/src/components/ExportZone.tsx — Zone 6 CTA + caption + in-flight label + green role="status" receipt + red verbatim-error panel (no modal, no toast, no retry button)
  - frontend/src/components/SelfCheckPanel.tsx — ordem rows (contato first, raw-id fallback), survival tally + CATEGORY_ORDER chips (absence = neutral gray, never red), zero-keyword loud line, gate footer; exported resumoSobrevivenciaCopy pure function
  - frontend/src/pages/CurriculoHome.tsx — export useMutation (one POST → download + receipt + panel), symmetric locking (generate CTA + Gerar novamente + export CTA all lock during either pending), regeneration resets export state (D-16)
affects: [Phase 4 verification (/gsd-verify-work 4 — human UAT re-surface), Phase 5 (review flow edits must flow into the export payload's displayed state)]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 6488         # 25954 chars / 4 over the realized diff (5 files, +437/-11)
  tasks: 3             # Task 3 = human checkpoint, resolved-as-deferred
  commits: 2           # MEASURED: git rev-list --count a026f48..HEAD
commits: 2
plan_head_before: a026f48e2e44aede46e28c505efcd4cf33855f3d

# Tech tracking
tech-stack:
  added: []
  patterns: [discriminated-union envelope mirrored client-side (tsc -b as the two-sided drift gate), one-POST-three-effects (download + receipt + panel from a single response), symmetric pending locking across both CTAs, failure-never-blanks (erro paths never clear receipt/panel), atob→Uint8Array→Blob→anchor→revokeObjectURL with no module byte state, run-language chip display via displayed-state keywords lookup]

key-files:
  created:
    - frontend/src/components/ExportZone.tsx
    - frontend/src/components/SelfCheckPanel.tsx
  modified:
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/pages/CurriculoHome.tsx

key-decisions:
  - "Task 3 checkpoint resolved [deferred — silence]: the 4 human checks (SC1 PDF-vs-screen fidelity, SC3 download UX feel, SC2/EN heading viewer inspection, backstop full-page readability) were NOT run — autonomous run, user unavailable. Never claimed as passed; routed to /gsd-verify-work 4 as human_needed UAT, same pattern as Phase 1's deferred verification."
  - "The automated SC2 proof STANDS without the human check: 223 backend tests include the parse-back gate on real PT-BR/EN Chromium renders (test_gate_passes_real_pdf[pt-BR]/[en]) — text layer, reading order, headings map, accents; what defers is the visual/feel dimension only."
  - "REVIEW-03 CHECKED in REQUIREMENTS.md: its user story ('user can RUN an ATS self-check') completes with this plan's panel (04-02 deliberately left it for 04-03); the REQUIREMENTS.md line notes the human UAT is pending. REVIEW-02 stays checked from 04-01 (automated criteria met: gate on real renders in both languages)."
  - "SelfCheckPanel takes the run's keywords prop ([Rule 3]): backend sobrevivencia entries carry canonical terms only; run-language chip display (KeywordsPanel pt/en mirror) needs the displayed-state lookup — no refetch, no recomputation (D-10 intact)."
  - "Symmetric lock extended to the MAIN generate CTA ([Rule 2]): Gerar currículo, Gerar novamente, and Exportar PDF all disable while either operation is pending — one long operation at a time, per the UI-SPEC interaction rule."

requirements-completed: [REVIEW-03]

# Metrics
duration: 23min
completed: 2026-09-27
status: complete
---

# Phase 4 Plan 3: Export Zone + Self-Check Panel Summary

**Zone 6 closed end-to-end: one click under the reviewed resume fires one POST that starts the PDF download, mounts the green receipt naming the backend filename, and renders the honest ATS self-check (order rows + survival chips) — with the checkpoint's four human checks deferred, not claimed**

## Performance

- **Duration:** 23 min
- **Started:** 2026-09-27T21:42:44Z (04-02 metadata commit)
- **Completed:** 2026-09-27T22:05:51Z
- **Tasks:** 3 (2 auto + 1 human checkpoint resolved-as-deferred)
- **Files modified:** 5 (+437/−11 lines)

## Accomplishments
- **Contract layer (Task 1, `ffa6f92`):** `ExportarResponse` discriminated union mirrors the 04-02 envelope exactly (ok: filename/pdf_base64/selfcheck; erro: erros — nothing else); `CoberturaItemDTO` reused for sobrevivencia (no duplicate chip type); `exportarCurriculo()` follows the gerarCurriculo fetch pattern; `downloadPdf()` converts atob→Uint8Array→`application/pdf` Blob→detached anchor click→revokeObjectURL, filename taken from the backend verbatim (D-11, never recomposed). client.ts header now names routes/export.py as the normative pair — tsc -b is the drift gate.
- **Zone 6 (Task 2, `3538089`):** ExportZone (CTA + caption + in-flight label + green role="status" receipt + red verbatim-error panel — no modal/toast/retry button) and SelfCheckPanel (ordem rows in payload order with contato first and raw-id fallback, singular/plural factual survival tally, CATEGORY_ORDER chips where absence is neutral gray ○ — honest information, never red — loud zero line, gate footer) wired into CurriculoHome below ResumeResult, inside the existing aria-live region. One POST drives all three effects; erro paths NEVER clear receiptFilename/selfcheck; regeneration clears receipt + panel + export errors before mounting the new result; export state is React session state only (D-16).
- **Prohibitions hold:** git diff on package.json/package-lock.json across the plan is EMPTY (native fetch/Blob only — no-new-frontend-deps contract held since Phase 3); every PT-BR string resolves to a constants/ui.ts import; JSX text children only (T-04-07).
- **Automation green at checkpoint AND re-proven at SUMMARY time:** backend `uv run pytest -q` → **223 passed, 7 deselected** (10.32s — includes the real-render parse-back gate in both languages); frontend `npm run build` → green (tsc -b + vite, 471ms); repo-wide oxlint → 0 errors, 2 pre-accepted warnings (below).

## Task Commits

Each task was committed atomically:

1. **Task 1: Contract layer — typed export client + blob helper + PT-BR constants** - `ffa6f92` (feat)
2. **Task 2: Zone 6 — ExportZone + SelfCheckPanel + CurriculoHome wiring** - `3538089` (feat)
3. **Task 3: End-of-phase human verification** — checkpoint resolved-as-deferred (no commit; no files)

**Plan metadata:** committed after SUMMARY (docs: complete plan)

## Deferred Human Verification (Task 3 — resolved "deferred — record UAT")

The checkpoint was resolved with the user's response **"deferred — record UAT"** (autonomous run; user unavailable — silence recorded, per run convention). The four checks below were **NOT executed and are NOT claimed as passed**. Automation was already green at checkpoint time (223 backend tests incl. the parse-back gate on real PT-BR/EN renders; frontend build green; app live and healthy) and was re-run and re-proven at SUMMARY time (identical results).

| # | Deferred check | What the human must do | Automated proof standing in |
|---|----------------|------------------------|------------------------------|
| 1 | **SC1 visual fidelity** | Open a downloaded `curriculo-*.pdf` in a viewer; confirm it matches the on-screen result card (single column, same sections/order) | Template is a pure D-05 montage builder unit-pinned to PREVIEW order; gate asserts contact-first + heading order on real renders |
| 2 | **SC3 download UX feel** | Click Exportar PDF; confirm auto-download starts, green receipt names the file, panel shows ✓ rows + chips | One-POST-three-effects is code-pinned; build green — the *feel* is what defers |
| 3 | **SC2/EN headings in viewer** | Run in English, export, select text in the viewer to confirm English headings + working text layer; panel rows follow | **Strongest standing proof:** `test_gate_passes_real_pdf[en]` extracts real Chromium-rendered PDF text and asserts the EN headings map (the automated SC2 core) |
| 4 | **Backstop readability** | With a keyword-rich JD (30+ keywords), confirm the fully checked page stays readable | flex-wrap-only chips + vertical growth are pinned class strings; visual confirmation defers |

**Re-surface path:** the phase-level verify step re-surfaces all four as `human_needed` UAT for `/gsd-verify-work 4` — the same pattern as Phase 1's deferred verification (STATE.md Deferred Verification table, phase 4 row added). A WINDOWS.md `unrun-verify` ledger entry records the deferral for the ship gate.

## Files Created/Modified
- `frontend/src/api/client.ts` — ExportarResponse union + SelfCheckDTO + ExportarRequest + exportarCurriculo + downloadPdf; normative-pair header comment (04-02: change BOTH together)
- `frontend/src/constants/ui.ts` — EXPORTAR_* (CTA, in-flight, caption, hint, receipt, error title/hint) + SELFCHECK_* (title, labels, ORDEM_LABELS map, singular/plural tally templates, zero line, gate footer) + counts-only comment block (no score/percentage/meter — REQUIREMENTS Out of Scope)
- `frontend/src/components/ExportZone.tsx` — render-only Zone 6 control surface; primary CTA reuses PRIMARY_BUTTON_CLASSES verbatim; error lines mapped verbatim (ErrorPanel discipline)
- `frontend/src/components/SelfCheckPanel.tsx` — render-only honest panel; exported resumoSobrevivenciaCopy pure function (mirrors resumoCoberturaCopy); local keywordDisplay mirror with source comment
- `frontend/src/pages/CurriculoHome.tsx` — exportar useMutation + three useState slots + regeneration reset + symmetric locking + Zone 6 composition

## Decisions Made

**REVIEW-03 checked; REVIEW-02 stays checked.** The plan's frontmatter listed both. REVIEW-02 was checked by 04-01 (its automated criteria — gate-proven single-column PDF text layer — are met). REVIEW-03's user story completes with this plan's panel, so it is now checked with a trailing note on the REQUIREMENTS.md line: automated criteria met 2026-09-27, human UAT of the panel deferred to `/gsd-verify-work 4`.

**Deferred-checkpoint posture.** Nothing was claimed as visually confirmed. The SUMMARY records the deferral, the standing automated proofs, and the exact re-verification instructions — the verifier decides with the user, exactly as Phase 1's deferral was handled.

**Deviation-widened props kept minimal.** The `keywords` prop passes the ALREADY-displayed `resultado.keywords` — no refetch, no recomputation, D-10 intact.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SelfCheckPanel needs the run's keywords as a prop**
- **Found during:** Task 2
- **Issue:** Plan props were `{ selfcheck, idioma }`, but backend sobrevivencia entries carry only canonical/category/termo/status — the run-language chip display (KeywordsPanel pt/en mirror with canonical fallback, mandated by the UI-SPEC) cannot be computed from the payload alone
- **Fix:** Added `keywords: KeywordDTO[]` to SelfCheckPanelProps; CurriculoHome passes `resultado.keywords` (displayed state)
- **Files modified:** frontend/src/components/SelfCheckPanel.tsx, frontend/src/pages/CurriculoHome.tsx
- **Commit:** 3538089

**2. [Rule 2 - Missing critical] Main generate CTA missing from the symmetric lock**
- **Found during:** Task 2
- **Issue:** Plan text locked the export CTA and "Gerar novamente" during export, but the MAIN "Gerar currículo" button (line 249 region) would have stayed enabled during an export — two long operations could run concurrently, violating the UI-SPEC one-long-operation rule
- **Fix:** Main CTA `disabled` now includes `exportar.isPending`; both CTAs lock symmetrically (`gerar.isPending || exportar.isPending` in all three places)
- **Files modified:** frontend/src/pages/CurriculoHome.tsx
- **Commit:** 3538089

**3. [Rule 1 - Bug] TypeScript narrowing error caught by the tsc -b drift gate**
- **Found during:** Task 2 (build gate)
- **Issue:** A discriminated-union branch needed an explicit narrow before property access; `npm run build` failed inside Task 2's dev loop
- **Fix:** Narrowed before access; build green before the Task 2 commit
- **Files modified:** frontend/src/pages/CurriculoHome.tsx
- **Commit:** 3538089

**Pre-accepted (not defects): 2 oxlint `react(only-export-components)` warnings** — KeywordsPanel's `resumoCoberturaCopy` (Phase 3, twice-recorded in WINDOWS.md) and this plan's twin `resumoSobrevivenciaCopy` (SelfCheckPanel.tsx:39). Both are plan-MANDATED pure copy-function exports from component files; the caveat is dev-only fast refresh, builds unaffected. Repo-wide oxlint: 0 errors, exactly these 2 warnings.

**Total deviations:** 3 auto-fixed (1 blocking, 1 missing-critical, 1 bug — all within Task 2's files)
**Impact on plan:** No scope creep; all three are the plan's own UI-SPEC rules made true. Task 3 resolved-as-deferred per the user's recorded response.

## Issues Encountered
- None beyond the deviations above. Automation re-run at SUMMARY time reproduced the checkpoint-time green exactly (223 passed / 7 deselected; build green).

## Known Stubs

None. Grep for TODO/FIXME/placeholder/coming-soon across the five files hits only pre-existing legitimate uses (PlaceholderBanner component from Phase 1, the JD textarea's placeholder ATTRIBUTE, the D-11 `example` flag comment) — nothing introduced by this plan; every rendered value is wired to backend data.

## User Setup Required

None — no new dependencies (package.json untouched; native fetch + Blob only).

## Next Phase Readiness
- **Phase 4 is functionally complete but NOT user-verified:** run `/gsd-verify-work 4` — it will re-surface the four deferred checks as human_needed UAT (instructions table above), the same flow as Phase 1's deferred verification
- Phase 5 (Review Flow + Fact Safety) consumes: the export payload's displayed-state composition (`perfil + resultado.secoes + resultado.keywords + resultado.idioma`, D-10) — inline edits must flow through the same fields; the symmetric-lock pattern (both CTAs) extends naturally to per-section regeneration
- No blockers: full offline suite 223 passed / 7 deselected; frontend build green; oxlint 0 errors

---
*Phase: 04-pdf-export-ats-self-check*
*Completed: 2026-09-27*

## Self-Check: PASSED

All 6 claimed files exist on disk (5 source + this SUMMARY); both task commits found in git history (ffa6f92, 3538089); commit count measured from the plan ledger (a026f48..HEAD) = 2. Task 3 has no commit by design (human checkpoint, resolved-as-deferred).
