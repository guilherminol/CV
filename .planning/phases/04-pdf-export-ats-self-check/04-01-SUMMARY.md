---
phase: 04-pdf-export-ats-self-check
plan: 01
subsystem: api
tags: [playwright, chromium, pypdf, pdf-export, ats, parse-back-gate, fastapi]

# Dependency graph
requires:
  - phase: 03-resume-vertical-slice
    provides: D-05 result montage (ResumeResult.tsx — mirrored by the template), coverage.py _fold/_term_pattern primitives (imported, never re-implemented), conftest personas (fixture shape)
  - phase: 01-foundation-scaffold-master-profile
    provides: Profile schema (contact/experiences/education/certifications/languages/projects), LLMError (message_ptbr, raw) error shape, fail-loud envelope philosophy
provides:
  - backend/app/export/ package: build_resume_html (pure D-05 montage builder), HEADINGS pt/en single source, join_experience_dates, format_date_range, iter_rendered_strings
  - html_to_pdf engine seam (the ONLY playwright import; WeasyPrint = one-function swap)
  - parse_back_check four-check gate (contact-first, heading order, co-occurrence, accent integrity) with GateResult per-check booleans
  - ExportError (message_ptbr, raw) error type
  - offline test suite with session real-render fixture (bilingual Chromium renders)
  - README "Backend setup" step (D-04): uv sync + playwright install chromium
affects: [04-02 (export endpoint + selfcheck), 04-03 (frontend export zone + self-check panel)]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 18291        # 73163 chars / 4 over the realized diff (9 files, +1245 lines)
  tasks: 3
  commits: 3           # MEASURED: git rev-list --count 6f2cf47..HEAD

# Tech tracking
tech-stack:
  added: [playwright==1.62.0, pypdf>=6.19.0 (6.19.0 locked)]
  patterns: [engine seam (one playwright import), pure-function HTML builder with html.escape(quote=True) everywhere, coverage._fold reuse for text-layer checks, parse-back gate before engine trust, fail-loud fixtures (never skip-silent), per-request Chromium launch closed in finally]

key-files:
  created:
    - backend/app/export/__init__.py
    - backend/app/export/errors.py
    - backend/app/export/render.py
    - backend/app/export/pdf.py
    - backend/app/export/gate.py
    - backend/tests/test_export_gate.py
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - README.md

key-decisions:
  - "D-02 verdict (EMPIRICAL): Playwright embeds — the parse-back gate existed first and the real Chromium renders passed all four checks in BOTH languages. The two engines were never both installed; the gate passed on the real candidate engine, WeasyPrint stays the documented pre-approved fallback against the same gate."
  - "A2 RESOLVED [auto — silence]: EN-run exports localize ALL 7 section headings (HEADINGS pt/en maps in render.py is the single source of truth; the gate asserts against the same map). Recommended option adopted with the orchestrator-reported user resolution, pending user review per run convention."
  - "Pin playwright==1.62.0 deliberately DIVERGES from STACK.md's 1.63.0 row: 1.62.0 bundles chromium-1234, already cached on this machine — latest would demand a ~170MB chromium-1243 download for zero features this phase needs (documented in README)."
  - "Dates join (Open Questions 1+3): strip+coverage._fold company join between perfil.experiences and secoes.experiencias; matched entries render RAW stored strings 'start – end|atual'; unmatched entries render dateless and the gate skips ONLY the date sub-check — no invented dates, ever."
  - "Gate core split: check_extracted_text(text, expected) is pure (no pypdf, no browser) so every failure branch is table-tested on synthetic text; parse_back_check wraps extraction + crash-to-ExportError."
  - "GateResult carries per-check booleans (contato_primeiro/ordem_titulos/coocorrencia/acentos) — the plan-04-02 selfcheck footer block reads them directly."

patterns-established:
  - "Engine seam: exactly one playwright import per backend (AST-pinned by test); template + gate stay engine-agnostic (D-01 reversibility)"
  - "D-08 message set lives in exactly one place (gate.py); tests import constants — never restate PT-BR lines"
  - "Single traversal content builder: _sections_content feeds both build_resume_html and iter_rendered_strings — the accent-integrity universe can never drift from the template"
  - "Check spaces: coverage._fold (casefold+NFKD) for order/heading/window math; casefold-ONLY (accent-sensitive) + U+FFFD/Ã/â€ sentinels for integrity"

requirements-completed: [REVIEW-02]

coverage:
  - id: D1
    description: "Pinned export deps installed (playwright==1.62.0 + pypdf>=6.19.0 in pyproject/uv.lock) and browser setup step documented in README Backend setup section (D-04)"
    requirement: REVIEW-02
    verification:
      - kind: other
        ref: "command: cd backend && uv run python -c \"from importlib.metadata import version; print(version('playwright'), version('pypdf'))\" → 1.62.0 6.19.0; playwright install chromium --dry-run → chromium-1234 (cached, zero download)"
      - kind: other
        ref: "manual ref: README.md '## Backend setup' section names cd backend && uv sync && uv run playwright install chromium"
    human_judgment: false
  - id: D2
    description: "Engine-agnostic pure HTML template mirroring the D-05 montage (all 7 sections, PREVIEW order, empty-passthrough hidden) with HEADINGS pt/en single source and html.escape on every interpolation"
    requirement: REVIEW-02
    verification:
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_render_html_escapes_hostile_strings"
        status: pass
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_render_html_full_montage_in_preview_order"
        status: pass
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_headings_map_covers_all_sections_in_render_order"
        status: pass
    human_judgment: false
  - id: D3
    description: "html_to_pdf engine seam — the only playwright import in the backend, per-request launch + close in finally, ExportError install hint on failure"
    requirement: REVIEW-02
    verification:
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_engine_seam_pdf_is_the_only_playwright_import"
        status: pass
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_pdf_bytes_never_written_to_disk"
        status: pass
    human_judgment: false
  - id: D4
    description: "Parse-back gate checks 1-2: contact-first and heading order on the coverage fold, first failure short-circuits with its exact PT-BR line"
    requirement: REVIEW-02
    verification:
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_order_failures"
        status: pass
      - kind: integration
        ref: "backend/tests/test_export_gate.py#test_gate_short_circuits_on_shuffled_headings"
        status: pass
    human_judgment: false
  - id: D5
    description: "Parse-back gate checks 3-4: company+title+dates co-occurrence in the Experiências window (graceful dateless skip) and accent integrity (casefold-only space + mojibake sentinels)"
    requirement: REVIEW-02
    verification:
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_cooccurrence_and_accents"
        status: pass
      - kind: unit
        ref: "backend/tests/test_export_gate.py#test_join_experience_dates_pure_and_accent_tolerant"
        status: pass
    human_judgment: false
  - id: D6
    description: "Real bilingual Chromium exports pass ALL FOUR gate checks (SC2 verified in both PT-BR and EN) — the empirical D-02 engine verdict"
    requirement: REVIEW-02
    verification:
      - kind: integration
        ref: "backend/tests/test_export_gate.py#test_gate_passes_real_pdf[pt-BR]"
        status: pass
      - kind: integration
        ref: "backend/tests/test_export_gate.py#test_gate_passes_real_pdf[en]"
        status: pass
    human_judgment: false

# Metrics
duration: 23min
completed: 2026-09-27
status: complete
---

# Phase 4 Plan 1: PDF Export Engine + Parse-Back Gate Summary

**Four-check pypdf parse-back gate proven against real Chromium exports in PT-BR and EN behind a one-function Playwright seam (playwright==1.62.0 → cached chromium-1234, zero browser download) — the empirical D-02 verdict that embeds Playwright**

## Performance

- **Duration:** 23 min
- **Started:** 2026-09-27T20:56:20Z
- **Completed:** 2026-09-27T21:19:34Z
- **Tasks:** 3 (checkpoint install + tracer + expansion)
- **Files modified:** 9

## Accomplishments
- Export package created: pure HTML builder (D-03/D-05 montage), one-function Playwright seam (D-01/D-02), four-check pypdf gate (D-05/D-06), ExportError house shape — the gate existed BEFORE the engine was trusted (user-locked D-02 sequencing)
- Real Chromium exports in both run languages pass all four SC2 checks offline (session-rendered fixture, ~3s/render); full offline suite 202 passed, 7 deselected (llm), zero regressions
- D-04 setup documented: README "Backend setup" — `cd backend && uv sync && uv run playwright install chromium`; pinned playwright==1.62.0 hit the already-cached chromium-1234 with NO download (dry-run verified the revision mapping)
- D-08 split enforced end-to-end: PT-BR failure lines live only in gate.py, raw detail terminal-only, per-check booleans ready for plan 04-02's selfcheck footer

## Task Commits

Each task was committed atomically:

1. **Task 0: Human checkpoint (T-04-SC) — pinned installs + README setup step** - `cea5a88` (chore)
2. **Task 1: Tracer — one PT-BR/EN path end-to-end behind the engine seam** - `b70837c` (feat)
3. **Task 2: Expansion — full gate (co-occurrence + accent integrity) + full D-05 montage** - `5d0eb1e` (feat)

**Plan metadata:** committed after SUMMARY (docs: complete plan)

_Note: Task 0's blocking-human checkpoint was resolved by the orchestrator before this executor spawned: user approved both PyPI packages ("verified") and confirmed A2 ("confirm"); the chromium-1234 cache precondition was verified MET._

## Files Created/Modified
- `backend/app/export/render.py` - Pure D-05 montage builder: HEADINGS pt/en single source (A2), join_experience_dates (fold join, dateless fallback), format_date_range (raw strings), iter_rendered_strings (accent universe, one traversal with the builder)
- `backend/app/export/pdf.py` - html_to_pdf engine seam: THE only sync_playwright import, per-request launch, close in finally, PT-BR install hint on failure
- `backend/app/export/gate.py` - parse_back_check: contact-first, heading order, window co-occurrence, accent integrity + mojibake sentinels; D-08 message set; GateResult with per-check booleans
- `backend/app/export/errors.py` - ExportError(message_ptbr, raw) mirroring LLMError
- `backend/app/export/__init__.py` - Package docstring
- `backend/tests/test_export_gate.py` - Session real-render fixture (bilingual), structural seam pins (AST), synthetic failure tables, full-gate integration tests (19 tests)
- `backend/pyproject.toml` + `backend/uv.lock` - playwright==1.62.0, pypdf>=6.19.0 added
- `README.md` - Backend setup section (D-04)

## Decisions Made

**D-02 engine verdict (EMPIRICAL — discharges the STATE.md blocker):** Playwright embeds. The gate was built first (Task 1, checks 1-2) and the expansion (Task 2) proved all four checks on REAL Chromium exports in BOTH languages. **The two engines were never both installed** — WeasyPrint was never installed (its MSYS2/Pango path stays documented in 04-RESEARCH.md); the gate passed on the real candidate engine, which per D-02's tie-break (fidelidade de layout) settles it. WeasyPrint remains a pre-approved, uninstalled fallback against this same gate: the template is block-layout-only CSS with both break-inside properties, and html_to_pdf is a one-function swap (AST-pinned).

**A2 resolution (EN-run heading localization):** RESOLVED **[auto — silence]** — the RECOMMENDED option was adopted: EN-run exports localize ALL 7 section headings (Summary/Experience/Education/Skills/...), diverging presentation-only from the in-app preview's PT-BR passthrough labels; content travels verbatim (D-10). HEADINGS in render.py is the single source of truth and the gate asserts against the same map, so a future user decline confines the change to that one map. Recorded as pending user review per the run convention.

**Playwright pin vs STACK.md divergence:** STACK.md's row lists playwright 1.63.0 (registry latest at research time); this plan pinned **1.62.0** deliberately — 1.62.0 bundles chromium-1234, the revision already cached in %LOCALAPPDATA%\ms-playwright on this machine, avoiding a ~170MB chromium-1243 download for zero needed features. The divergence is intentional and documented in README's setup step.

**Dates join graceful skip (research Open Questions 1+3):** join_experience_dates matches perfil.experiences to secoes.experiencias by strip+coverage._fold company; matched entries render the RAW stored range ("2022-03 – atual"); unmatched entries render dateless and the gate skips ONLY the date sub-check (company+title still asserted) — no invented dates, ever.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Task 0 verify smoke: playwright.__version__ attribute does not exist**
- **Found during:** Task 0 (import smoke)
- **Issue:** The plan's `<verify>` command prints `playwright.__version__`; the playwright PyPI package exposes no `__version__` module attribute (AttributeError), so the command as written cannot pass on ANY correct install
- **Fix:** Same smoke via the canonical version read — `from importlib.metadata import version; print(version('playwright'), version('pypdf'))` → `1.62.0 6.19.0`; the sync_playwright import succeeded in both attempts
- **Files modified:** none (verify command mechanics only)
- **Verification:** exit 0, versions exactly the pins; uv.lock shows playwright 1.62.0 / pypdf 6.19.0
- **Committed in:** cea5a88 (Task 0 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — verify-command mechanics, not product code)
**Impact on plan:** Cosmetic fix to the verification command; no scope creep, no product-code deviation.

## Issues Encountered
- None beyond the deviation above. `uv run playwright install chromium` completed silently with no output (cache hit for chromium-1234 — the expected near-instant pass; `--dry-run` confirmed "playwright chromium v1234").

## Known Stubs

None. The Task 1 tracer's sanctioned fill-later scope (passthrough sections + dates rendering) was completed by Task 2 in this same plan; a repo-wide stub scan of app/export/ + tests found no TODO/FIXME/placeholder patterns.

## User Setup Required

None on this machine — chromium-1234 was already cached. On a fresh clone the README "Backend setup" section now documents the one-time browser download (`cd backend && uv sync && uv run playwright install chromium`, ~170MB where no cache exists).

## Next Phase Readiness
- Plan 04-02 consumes: build_resume_html + join_experience_dates + iter_rendered_strings (ExpectedDoc building), parse_back_check + GateResult booleans (gate envelope path + selfcheck footer), ExportError handling, and the PT-BR install-hint line
- selfcheck.py (ordem rows + keyword survival via coverage.keyword_in_text) and routes/export.py (POST /api/resume/exportar, router BEFORE the SPA mount) are the 04-02 surface; this plan deliberately kept the gate OFF any endpoint (D-07 lands there)
- No blockers: full offline suite green (202 passed, 7 deselected)

---
*Phase: 04-pdf-export-ats-self-check*
*Completed: 2026-09-27*

## Self-Check: PASSED

All 9 claimed files exist on disk; all 3 task commits found in git history (cea5a88, b70837c, 5d0eb1e); commit count measured from the plan ledger (6f2cf47..HEAD) = 3.
