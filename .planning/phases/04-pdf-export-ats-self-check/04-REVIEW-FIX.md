---
phase: 04-pdf-export-ats-self-check
fixed_at: 2026-09-27T22:49:47Z
review_path: .planning/phases/04-pdf-export-ats-self-check/04-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 8
skipped: 3
status: partial
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-09-27T22:49:47Z
**Source review:** .planning/phases/04-pdf-export-ats-self-check/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 11 (all 2 Critical + 2 Warning, plus the 4 low-risk mechanical Info findings the orchestrator directed; the 3 structural-test-scope Info findings were recorded as skips)
- Fixed: 8
- Skipped: 3 (IN-05, IN-06, IN-07 — one-line reasons below)

**Verification ran in the isolated review-fix worktree** (`.claude/worktrees/rf-04-7757-1790548010`, branch `gsd-reviewfix/04-7757`), NOT the main checkout: backend deps were freshly `uv sync --frozen`-ed and frontend deps `npm ci`-ed inside the worktree, so every number below is reproducible from the worktree tree (not from the main checkout, which has no `.venv`/`node_modules`). After the fast-forward the main checkout receives the same commits but NOT those dependency dirs.

**Verification per fix:**
- Backend fixes (CR-01, CR-02, WR-01, IN-01, IN-02): `cd backend && uv run pytest tests/test_export_gate.py tests/test_export_api.py -q` — final state **49 passed** (was 42 passing + 1 env-failing pre-fix; net +7 regression tests). Includes real-Chromium renders (session persona, uppercase-contact persona, partial-profile route export).
- Frontend fixes (WR-02, IN-03, IN-04): `cd frontend && npm run build` (tsc -b + vite) — green after each fix.
- One pre-existing env quirk observed en route: `test_export_router_registered_before_spa_mount` (IN-05's subject) failed in the fresh worktree solely because `frontend/dist` did not exist there; it passed once the frontend was built in the worktree. No fix commit relates to it.

## Fixed Issues

### CR-01: Gate demanded all 7 headings — profiles with empty passthrough sections could never export

**Files modified:** `backend/app/export/render.py`, `backend/app/routes/export.py`, `backend/app/export/gate.py`, `backend/app/export/selfcheck.py`, `backend/tests/test_export_gate.py`, `backend/tests/test_export_api.py`
**Commit:** e32d6fe
**Status:** fixed — logic change, requires human verification (regression-covered: `test_rendered_section_keys_matches_template_hidden_sections`, `test_exportar_partial_profile_exports_ok` through the REAL Chromium chain)

**Applied fix:** Single-sourced via the review's "better still" option — `rendered_section_keys(perfil, secoes, datas, idioma)` in render.py derives the rendered key set from the SAME `_sections_content` traversal `build_resume_html` renders from (the template IS the truth; no duplicated presence logic to drift). `_expected_doc` builds `ExpectedDoc.headings` from it; the gate's order checks are untouched (the keys arrive in render order). Docstrings in gate.py/selfcheck.py updated to "one row per RENDERED section". `test_export_api.py`'s ordem-ids assertion now derives from `rendered_section_keys` instead of the unconditional `section_keys`.
**Deviation from review sketch:** the review's `_PASSING_GATE.ordem_rows` stub was left as the full-7 set on purpose — it stubs a full-persona pass where rendered == all 7; the dynamic derivation is pinned by the real-render assertion and the new partial-profile test.

### CR-02: Mojibake sentinel "Ã" false-positived on legitimate uppercase accented text

**Files modified:** `backend/app/export/gate.py`, `backend/tests/test_export_gate.py`
**Commit:** c48f304
**Status:** fixed — logic change, requires human verification (regression-covered: synthetic "SÃO PAULO"/"MANHÃ" pass cases + real-Chromium `test_gate_passes_real_pdf_with_uppercase_accented_contact`)

**Applied fix:** `\ufffd` and `â€` remain bare-substring sentinels; the bare "Ã" was replaced by the contextual pattern `_MOJIBake_A_TILDE = re.compile(r"Ã(?=[^\x00-\x7f])")` — Ã followed by a non-ASCII char (the exact UTF-8→Latin-1 mangling signature: every C3-led byte pair mangles to Ã + U+0080–U+00FF). Byte-perfect accent assertions are untouched and still pass.
**Deviations from review sketch:** (1) implemented the finding's stated signature ("Ã followed by another non-ASCII byte-mapping char", per the orchestrator directive) rather than the sketch's `Ã(?![A-Za-z])`, which would false-positive on legit words ENDING in uppercase Ã (MANHÃ, IRMÃ, MAÇÃ); (2) the existing "mojibake" test case actually corrupted "São"→"SÃo" (Ã + ASCII O) — under the corrected rule that shape is indistinguishable from legit caps and now PASSES by design, so the case was rewritten to true mojibake bytes ("S\u00c3\u00a3o" = Ã + U+00A3).

### WR-01: `join_experience_dates` collapsed same-company stints to the last one

**Files modified:** `backend/app/export/render.py`, `backend/app/routes/export.py`, `backend/tests/test_export_gate.py`
**Commit:** 584d5fd
**Status:** fixed — logic change, requires human verification (regression-covered: `test_join_experience_dates_same_company_stints_map_positionally` with HTML-level date assertions)

**Applied fix:** Stored ranges are grouped per folded company and consumed positionally in generated-entry order; unmatched or exhausted-bucket entries are dateless.
**Deviation from review sketch (required for correctness):** the sketch still keyed `joined` by the company string — two generated entries with IDENTICAL company strings (the exact career-progression scenario the finding describes) would collide in that dict and both print the last range, i.e. the bug survives. Implemented as an INDEX-ALIGNED list (one element per `secoes.experiencias` entry, in order); `_sections_content`, `iter_rendered_strings`, `build_resume_html`, and `_expected_doc` were updated to the per-entry contract.

### WR-02: Lint fetch-level failure rendered nothing in Zone 2

**Files modified:** `frontend/src/pages/CurriculoHome.tsx`, `frontend/src/constants/ui.ts`
**Commit:** d1815bc
**Status:** fixed

**Applied fix:** `lintReady && lintQuery.isError` now renders the red panel with a generic PT-BR hint (new `CURRICULO_LINT_FETCH_ERRO` constant in constants/ui.ts — raw detail stays terminal-only), matching the gerar/exportar `erros=[]` panel convention.

### IN-01: `html_to_pdf` blamed the browser install for every failure

**Files modified:** `backend/app/export/pdf.py`, `backend/tests/test_export_gate.py`
**Commit:** e37a4c1
**Status:** fixed (branch behavior pinned by two offline fake-playwright tests: launch failure keeps the install hint; render failure gets the generic retry hint)

**Applied fix:** Stage split instead of message sniffing — `chromium.launch` failures raise ExportError with the install hint (`_BROWSER_MISSING_PTBR`); render-stage (`new_page`/`set_content`/`page.pdf`) and driver-startup failures raise ExportError with the new generic `_RENDER_FALHOU_PTBR`. Raw detail stays terminal-only in both branches (D-08). The missing-Chromium fail-loud fixture path is unchanged.

### IN-02: Contact check misattributed a missing first heading to a contact failure

**Files modified:** `backend/app/export/gate.py`, `backend/tests/test_export_gate.py`
**Commit:** 5aa0451
**Status:** fixed — logic change, requires human verification (regression-covered: new parametrized order-failure case asserting `msg_secao_fora_de_ordem("resumo")`)

**Applied fix:** The `min(contact_positions) < first_heading_pos` comparison runs only when `first_heading_pos >= 0`; an absent Resumo heading now falls through to the heading check, which names the section exactly.

### IN-03: `downloadPdf` revoked the object URL synchronously after `click()`

**Files modified:** `frontend/src/api/client.ts`
**Commit:** cda5539
**Status:** fixed

**Applied fix:** `URL.revokeObjectURL(url)` deferred to a subsequent task (`setTimeout(..., 0)`); docstring updated.

### IN-04: `PRIMARY_BUTTON_CLASSES` duplicated despite a "never redefined" comment

**Files modified:** `frontend/src/constants/ui.ts`, `frontend/src/pages/CurriculoHome.tsx`, `frontend/src/components/ExportZone.tsx`
**Commit:** 3130c07
**Status:** fixed

**Applied fix:** Exactly one definition exported from `constants/ui.ts`; both consumers import it. The string is byte-identical to the previous two copies (verified by the tsc build).

## Skipped Issues

### IN-05: Router-order test depends on `frontend/dist` existing

**File:** `backend/tests/test_export_api.py:289-297`
**Reason:** Requires a CI/test-infrastructure decision (skipif semantics change what CI proves on fresh clones, or a guaranteed build step) — not a mechanical edit; recorded here instead. (Its environment sensitivity was empirically observed in the worktree during this run.)

### IN-06: Wire bounds exist only for `resumo`

**File:** `backend/app/routes/export.py:81-83`
**Reason:** Requires choosing specific `max_length` values — an API contract/product decision, not mechanical; deferred to the humans.

### IN-07: `test_pdf_bytes_never_written_to_disk` checks a narrower property than it pins

**File:** `backend/tests/test_export_gate.py:192-195`
**Reason:** Broadening the denylist is a structural-test-scope redesign (false-positive risk on legit code, e.g. `io.BytesIO`/`open(` reads); needs a deliberate decision.

---

_Fixed: 2026-09-27T22:49:47Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
