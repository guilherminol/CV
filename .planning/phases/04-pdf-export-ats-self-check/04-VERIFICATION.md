---
phase: 04-pdf-export-ats-self-check
verified: 2026-09-27T23:59:00Z
status: passed
score: 14/16 must-haves verified
covered_files:
  - .planning/phases/04-pdf-export-ats-self-check/04-01-PLAN.md
  - .planning/phases/04-pdf-export-ats-self-check/04-01-SUMMARY.md
  - .planning/phases/04-pdf-export-ats-self-check/04-02-PLAN.md
  - .planning/phases/04-pdf-export-ats-self-check/04-02-SUMMARY.md
  - .planning/phases/04-pdf-export-ats-self-check/04-03-PLAN.md
  - .planning/phases/04-pdf-export-ats-self-check/04-03-SUMMARY.md
  - backend/app/export/__init__.py
  - backend/app/export/errors.py
  - backend/app/export/render.py
  - backend/app/export/pdf.py
  - backend/app/export/gate.py
  - backend/app/export/selfcheck.py
  - backend/app/routes/export.py
  - backend/app/main.py
  - backend/pyproject.toml
  - backend/tests/test_export_gate.py
  - backend/tests/test_export_api.py
  - frontend/src/api/client.ts
  - frontend/src/constants/ui.ts
  - frontend/src/components/ExportZone.tsx
  - frontend/src/components/SelfCheckPanel.tsx
  - frontend/src/pages/CurriculoHome.tsx
  - README.md
covered_digest: "v1:sha256:863c60a096ab6780e4ab211d0ed02222a0875aeaac0368994c2e9de651099cee"
behavior_unverified: 2
overrides_applied: 0
re_verification: null
behavior_unverified_items:
  - truth: "SC3 — user can run the ATS self-check in-app and see verification of section order and keyword survival for the exported PDF (panel runtime behavior)"
    test: "Run the app, generate a resume, click Exportar PDF; watch the panel mount"
    expected: "Self-check panel appears after a successful export: contato-first ordem rows, survival chips grouped by category, gate footer line; zero-keyword run shows the loud zero line while the order block still renders"
    why_human: "Frontend has no test runner (no vitest/jest); npm run build proves compilation only — panel mount and render-from-payload are browser-runtime behavior grep cannot see"
  - truth: "Zone 6 UI state machine (pre-export ghost-panel absence, in-flight label swap, one-POST-three-effects with automatic download, failure-never-blanks, regeneration reset, D-16 session ephemerality)"
    test: "Walk the UI states: before export, during export, on success, on a gate/fetch failure, after regeneration, after page refresh"
    expected: "Only the CTA + caption before export; 'Exportando PDF…' + symmetric locking during; auto-download + green receipt + panel on success; red panel with verbatim lines and prior receipt/panel intact on failure; export state cleared on regeneration and refresh"
    why_human: "React runtime behavior with no automated frontend tests; the download auto-start and state transitions are only observable in a real browser session"
human_verification:
  - test: "SC1 visual fidelity — export a PT-BR resume and open the downloaded curriculo-*.pdf in a viewer"
    expected: "PDF matches the on-screen result card: single column, same sections in the same order, classic formatting"
    why_human: "Visual fidelity of a rendered PDF against the screen is not machine-checkable; template structure and montage order are code-pinned, the look is not"
  - test: "SC3 download UX feel — click Exportar PDF and watch what happens"
    expected: "Download starts automatically, the green receipt names the backend filename, the panel shows ✓ order rows plus survival chips"
    why_human: "The feel of the download flow (timing, feedback) is subjective runtime behavior; one-POST-three-effects is code-pinned but unexercised by any test"
  - test: "SC2/EN headings in viewer — switch the run to English, export again, select text in the PDF viewer"
    expected: "Selected text carries English headings (Summary/Experience/Education/...) and a working text layer; the panel rows follow"
    why_human: "Viewer text-selection inspection of the real downloaded artifact; the automated proof (test_gate_passes_real_pdf[en] on real Chromium bytes) stands, this confirms it on the shipped file"
  - test: "Backstop readability — with a keyword-rich JD (30+ keywords), review the fully checked page"
    expected: "Result card + export zone + both checklists stay readable: zones separated, chips wrap, page grows vertically, no cramping"
    why_human: "Full-page visual readability at populated volume is a human judgment; flex-wrap class strings are pinned but the rendered result is not"
---

# Phase 4: PDF Export + ATS Self-Check — Verification Report

**Phase Goal:** The user can export a genuinely sendable resume — a single-column Google-format PDF whose text layer is proven to parse correctly, automatically, in both languages.
**Verified:** 2026-09-27T22:59:02Z
**Status:** human_needed (no gaps — all automatable must-haves verified; 4 deferred human checks re-surfaced)
**Re-verification:** No — initial verification

## Goal Achievement

### User Flow Coverage (MVP mode — flow derived from ROADMAP success criteria)

The phase goal is not in strict `As a…, I want to…, so that…` User Story form (the format guard returns invalid), so the flow table below is derived from the ROADMAP's three explicit Success Criteria — the same three steps the plans and the deferred human checks enumerate. This is noted as an advisory; the SCs are the roadmap contract and are fully verifiable.

| # | Flow step (from SC) | Expected | Evidence in codebase | Status |
|---|---------------------|----------|----------------------|--------|
| 1 | User exports the reviewed resume (SC1) | Single-column Google-format PDF mirroring the in-app montage | `backend/app/export/render.py` `build_resume_html`: block-only CSS (no flex/grid/table/float — confirmed by direct render smoke), `_sections_content` in PREVIEW order with empty passthrough sections hidden; route `backend/app/routes/export.py` POST /api/resume/exportar returns base64 bytes + filename | ✓ VERIFIED (structural) / visual fidelity → human item 1 |
| 2 | Automated gate proves the text layer on EVERY export (SC2) | Contact first, canonical headings in order, company/title/dates co-occurring, accents intact — both languages | `backend/app/export/gate.py` `parse_back_check` (4 checks, coverage-fold primitives imported from `app/resume/coverage.py`); wired server-side: `pdf_base64` placed only after `gate.ok`; `test_gate_passes_real_pdf[pt-BR]`/`[en]` real Chromium renders PASSED in the 232-test run | ✓ VERIFIED (behavioral) |
| 3 | User reads the ATS self-check in-app (SC3) | Section-order rows + keyword survival for the exported PDF, both languages | `backend/app/export/selfcheck.py` `build_selfcheck` (classify_coverage over real extracted text; both languages proven by `test_survival_on_pdf_text[pt-BR]`/`[en]`); `frontend/src/components/SelfCheckPanel.tsx` renders ordem/chips/footer from the payload | Data layer ✓ VERIFIED / panel runtime ⚠️ PRESENT_BEHAVIOR_UNVERIFIED → human items 2–3 |

**Score:** 14/16 truths verified (2 present, behavior-unverified)

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1 — export produces a single-column Google-format PDF mirroring the reviewed montage | ✓ VERIFIED | render.py block-only CSS (smoke: no flex/grid/table/float), D-05 order mirror, `test_render_html_full_montage_in_preview_order` passed |
| 2 | SC2 — parse-back gate passes on every export, both languages | ✓ VERIFIED | `test_gate_passes_real_pdf[pt-BR]`/`[en]` + uppercase-accent-contact render, all PASSED in full suite (232 passed / 7 deselected); gate enforced in route ordering |
| 3 | SC3 — self-check visible in-app for the exported PDF | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Data layer proven both languages; panel mount/render is React runtime with no frontend test runner — human items 2–3 |
| 4 | Real Chromium PT-BR render passes all four gate checks | ✓ VERIFIED | Behavioral: `test_gate_passes_real_pdf[pt-BR]` (real Chromium, cached chromium-1234, offline) |
| 5 | EN render passes all four gate checks (A2: EN headings localized) | ✓ VERIFIED | Behavioral: `test_gate_passes_real_pdf[en]`; HEADINGS['en'] single source in render.py (smoke: 'Experience') |
| 6 | Co-occurrence window + graceful dateless skip (no invented dates) | ✓ VERIFIED | `test_cooccurrence_and_accents` table incl. "entrada sem datas passa"; WR-01 positional join `test_join_experience_dates_same_company_stints_map_positionally` |
| 7 | Accent integrity: casefold-ONLY space + mojibake sentinels | ✓ VERIFIED | Table: lost accent fails, U+FFFD fails, real mangling "Ã+non-ASCII" fails; legit "SÃO PAULO"/"MANHÃ" pass (CR-02 regression, ran green) |
| 8 | Pure template; every interpolation html.escape(quote=True) | ✓ VERIFIED | `test_render_html_escapes_hostile_strings`; esc() at every f-string site in render.py |
| 9 | Engine seam: pdf.py is the ONLY playwright import in the backend | ✓ VERIFIED | grep across backend/app: only `app/export/pdf.py`; AST-pinned by `test_engine_seam_pdf_is_the_only_playwright_import` |
| 10 | Bytes NEVER delivered unless gate passed; erro envelope has no PDF key | ✓ VERIFIED | routes/export.py ordering (pdf_base64 only on gate.ok branch); `test_exportar_gate_failure_erro_envelope` asserts `"pdf_base64" not in body` + caplog terminal-only split |
| 11 | Empty/partial section set rejected loudly (422, extra=forbid) | ✓ VERIFIED | 5-case 422 set (extra key, empty resumo/experiencias/habilidades, unknown idioma) all assert 422; min_length=1 floors in ExportarSecoes |
| 12 | Survival uses the SAME deterministic matcher (classify_coverage), counts only | ✓ VERIFIED | selfcheck.py imports classify_coverage verbatim; sobrevivencia entries exactly {canonical, category, termo, status} — no score/ratio field |
| 13 | Ordem rows: contato first, one row per RENDERED section, ids from render (CR-01) | ✓ VERIFIED | `_expected_doc` derives headings from `rendered_section_keys` (same traversal as the template); partial-profile real render `test_exportar_partial_profile_exports_ok` PASSED; direct smoke: partial profile yields exactly (resumo, experiencias, habilidades) |
| 14 | Gate failure answers 200 {status: erro, erros} with raw terminal-only | ✓ VERIFIED | caplog assertions in test_export_api.py; MSG set lives only in gate.py |
| 15 | Export adds NO runs.jsonl line; no LLM machinery in export path | ✓ VERIFIED | runs.jsonl before/after count pin (test line 342–347); no-app.llm AST scan (schemas allowed per calibrated decision); grep confirms no gateway/client import in export path |
| 16 | Zone 6 UI state machine (ghost-panel absence, in-flight swap, one-POST-three-effects, failure-never-blanks, regeneration reset, D-16 ephemerality) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | All code present and wired (ExportZone.tsx, SelfCheckPanel.tsx, CurriculoHome.tsx lines 87–154, 251, 285, 326–344; reset wired in gerar.onSuccess); tsc -b green; no frontend test runner exercises the runtime — human item 2 + behavior_unverified_items |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/app/export/__init__.py` | Package init | ✓ VERIFIED | Exists, substantive |
| `backend/app/export/errors.py` | ExportError(message_ptbr, raw) | ✓ VERIFIED | Exact LLMError mirror |
| `backend/app/export/render.py` | build_resume_html + HEADINGS + section_keys + join + rendered_section_keys | ✓ VERIFIED | 409 lines, pure, single traversal; WIRED (imported by routes/export.py) |
| `backend/app/export/pdf.py` | html_to_pdf — only playwright import | ✓ VERIFIED | Stage-split error hints (IN-01 fix); per-request launch + finally close |
| `backend/app/export/gate.py` | ExpectedDoc/GateResult/parse_back_check + 4 checks + ordem_rows/flat_text | ✓ VERIFIED | 324 lines; WIRED by route + selfcheck |
| `backend/app/export/selfcheck.py` | build_selfcheck {ordem, sobrevivencia, gate} | ✓ VERIFIED | classify_coverage verbatim; smoke: exact 3 keys, zero-keyword → [] |
| `backend/app/routes/export.py` | POST /api/resume/exportar + strict ExportarRequest | ✓ VERIFIED | sync def, extra=forbid, D-07 ordering |
| `backend/app/main.py` | export router BEFORE SPA mount | ✓ VERIFIED | Line 20, before mount (line 24) |
| `backend/tests/test_export_gate.py` | Gate family incl. real renders | ✓ VERIFIED | 26+ tests, all passed |
| `backend/tests/test_export_api.py` | Envelope family + structural pins | ✓ VERIFIED | 14+ tests incl. real render end-to-end + runs.jsonl pin |
| `frontend/src/api/client.ts` | ExportarResponse union + exportarCurriculo + downloadPdf | ✓ VERIFIED | Lines 203–251; deferred revocation (IN-03 fix); normative-pair header |
| `frontend/src/constants/ui.ts` | EXPORTAR_*/SELFCHECK_* + PRIMARY_BUTTON_CLASSES single-source | ✓ VERIFIED | 18 export/selfcheck constants; IN-04 fix applied |
| `frontend/src/components/ExportZone.tsx` | Zone 6 CTA/receipt/error panel | ✓ VERIFIED | Wired via CurriculoHome; verbatim error lines |
| `frontend/src/components/SelfCheckPanel.tsx` | Ordem rows + chips + zero line + footer | ✓ VERIFIED | raw-id fallback, CATEGORY_ORDER grouping, aria-hidden glyphs |
| `frontend/src/pages/CurriculoHome.tsx` | Zone 6 wiring, symmetric locking, regeneration reset | ✓ VERIFIED | Lines 87–154, 251, 285, 326–344; reset verified at lines 116–118 |
| `backend/pyproject.toml` | playwright==1.62.0 + pypdf>=6.19.0 | ✓ VERIFIED | Both pinned; installed versions confirmed 1.62.0 / 6.19.0 |
| `README.md` | D-04 backend setup step | ✓ VERIFIED | "## Backend setup" section with uv sync + playwright install chromium |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| render.py HEADINGS/section_keys | gate.py heading-order check | ExpectedDoc built by routes/export.py from render outputs — never duplicated | ✓ WIRED | `_expected_doc` imports HEADINGS + rendered_section_keys; gate receives, never re-declares |
| perfil.experiences[].company | secoes.experiencias[].company | join_experience_dates fold join → raw stored date strings | ✓ WIRED | strip+_fold join, positional buckets (WR-01); rendered verbatim, gate matches exactly |
| coverage._fold | gate.py + render.py | import, never re-implement | ✓ WIRED | `from app.resume.coverage import _fold, _term_pattern` in gate.py:42; render.py:49 |
| parse_back_check | build_selfcheck | same GateResult feeds delivery + payload | ✓ WIRED | route passes `gate` (the same object) to build_selfcheck; footer booleans from it |
| routes/export.py envelope | client.ts ExportarResponse | tsc -b drift gate | ✓ WIRED | client.ts:203–236 mirrors {status, filename, pdf_base64, selfcheck{ordem, sobrevivencia, gate}} / {status, erros}; build green |
| ExportarRequest fields | frontend displayed state | verbatim D-10 | ✓ WIRED | CurriculoHome.mutate({perfil: perfilQuery.data.perfil, secoes: resultado.secoes, keywords: resultado.keywords, idioma: resultado.idioma}) |
| SelfCheckPanel ordem ids | render.py section_keys | backend payload + raw-id fallback | ✓ WIRED | SELFCHECK_ORDEM_LABELS map + `ordemLabels[row.id] ?? row.id` (unknown ids render raw, never dropped) |
| ExportZone filename | backend D-11 filename | backend is single source | ✓ WIRED | receipt interpolates data.filename; downloadPdf takes it as argument, never recomposed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| SelfCheckPanel chips | selfcheck.sobrevivencia | classify_coverage over gate.flat_text (pypdf extraction of real Chromium PDF) | Yes | ✓ FLOWING |
| SelfCheckPanel ordem rows | selfcheck.ordem | gate.ordem_rows from the heading walk on the same extraction | Yes | ✓ FLOWING |
| Receipt filename | receiptFilename | backend date.today() + idioma | Yes | ✓ FLOWING |
| ExportZone error lines | exportarErros | backend gate.erros_ptbr / ExportError lines / [] on fetch failure | Yes | ✓ FLOWING |
| Chip display text | keywordDisplay lookup | resultado.keywords (displayed state) with canonical fallback | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full offline backend suite | `uv run pytest -q` (backend) | 232 passed, 7 deselected (llm) in 8.01s — includes real-Chromium renders both languages, CR-01/CR-02/WR-01/IN-02 regression tests | ✓ PASS |
| Frontend compile drift gate | `npm run build` (tsc -b + vite) | green, 409ms | ✓ PASS |
| Deps pinned as claimed | importlib.metadata versions | playwright 1.62.0, pypdf 6.19.0 | ✓ PASS |
| Engine seam | grep playwright across backend/app | exactly one file (app/export/pdf.py) | ✓ PASS |
| Partial-profile render (CR-01) | direct render smoke, education/certs/languages/projects empty | rendered keys = (resumo, experiencias, habilidades) — passthrough hidden, not demanded | ✓ PASS |
| A2 EN headings | direct HEADINGS check + real-render test[en] | 'Experience' for experiencias; EN gate pass | ✓ PASS |
| Single-column CSS | direct render smoke | no flex/grid/table/float in output HTML | ✓ PASS |
| Contact-first structure | direct render smoke | email position < first heading position | ✓ PASS |
| build_selfcheck contract | direct smoke | keys exactly {gate, ordem, sobrevivencia}; zero-keyword → [] | ✓ PASS |
| No new frontend deps | git log 6f2cf47..HEAD -- package.json package-lock.json | empty — zero changes in the whole phase range | ✓ PASS |
| Prohibition: no PDF key on gate failure | test_export_api.py:193,212 | `"pdf_base64" not in body` asserted, passing | ✓ PASS |
| Prohibition: no LLM in export path | structural test + grep | only app.llm.schemas (pure DTOs, plan-mandated); no gateway/prompts/client/pipeline | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes exist or were declared for this phase. The equivalent runnable proof is the real-Chromium render gate inside the backend suite (run above, 232 passed) — the automatable SC2 proof re-executed by this verification, not trusted from SUMMARY claims.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| REVIEW-02 | 04-01, 04-02, 04-03 | Export as single-column Google-format PDF with clean selectable text layer (ATS-parseable reading order) | ✓ SATISFIED | [x] in REQUIREMENTS.md; gate proven on real renders both languages; enforced server-side on every export |
| REVIEW-03 | 04-02, 04-03 | ATS self-check: extract text from exported PDF, verify section order + keyword survival, both languages | ✓ SATISFIED (automated) | [x] with honest trailing note: automated criteria met 2026-09-27; human UAT of the panel deferred to /gsd-verify-work 4 — routed as human items 2–3 |

No orphaned requirements: REQUIREMENTS.md maps exactly REVIEW-02 and REVIEW-03 to Phase 4; both are claimed in all three plans' `requirements` frontmatter. REVIEW-01 maps to Phase 5 (not this phase).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| frontend/src/constants/ui.ts | 82 | `PLACEHOLDER` substring (CURRICULO_JD_PLACEHOLDER) | ℹ️ Info | Pre-existing Phase 1 textarea placeholder attribute — legitimate, not a debt marker |
| backend/tests/test_export_api.py | 289 | router-order test depends on frontend/dist existing (review IN-05, deliberately skipped) | ℹ️ Info | Passes here (dist exists); environment-sensitive on fresh clones — recorded skip, not a goal gap |
| backend/app/routes/export.py | 81–83 | wire bounds only on resumo (review IN-06, deliberately skipped) | ℹ️ Info | Accepted localhost risk; product decision deferred to humans |
| backend/tests/test_export_gate.py | 192 | pdf-never-written test checks narrower property than pinned (review IN-07, deliberately skipped) | ℹ️ Info | Structural-test scope decision; no observed violation |

No TBD/FIXME/XXX debt markers in any phase-modified file. No dangerouslySetInnerHTML anywhere in the new components. No stub patterns: every rendered value chains to real backend data.

### Advisory (New Scope, Unevidenced — informational)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Phase goal is not in strict User Story format (user-story.validate → invalid); verification grounded in the ROADMAP Success Criteria instead | other | Format normalization (optional): `/gsd mvp-phase 4` would set a canonical goal; does not affect this phase's evidence |
| 2 | playwright pinned 1.62.0 vs STACK.md 1.63.0 row | other | Intentional, documented (cached chromium-1234; README notes it) — STACK.md cell is the stale artifact |
| 3 | Review fixes (CR-01/CR-02/WR-01/WR-02/IN-01..04) are logic changes whose full behavioral confirmation rides the same deferred human UAT | other | All regression tests ran green in this verification's suite run (232 passed); the human dimension (real PDFs on screen) is covered by human items 1–4 |

### Human Verification Required

Four checks, deferred at the 04-03 checkpoint ("deferred — record UAT", autonomous run, user unavailable) and correctly never claimed as passed:

1. **SC1 visual fidelity** — open a downloaded `curriculo-*.pdf` and compare against the on-screen result card (single column, same sections/order).
2. **SC3 download UX feel** — click Exportar PDF: auto-download starts, green receipt names the file, panel shows ✓ rows + chips.
3. **SC2/EN headings in viewer** — EN run, export, select text in the viewer: English headings + working text layer; panel rows follow.
4. **Backstop readability** — keyword-rich JD (30+ keywords): the fully checked page stays readable.

### Gaps Summary

None. Every automatable must-have is verified against the codebase and re-proven by execution: the full offline suite (232 passed, 7 deselected) includes the real-Chromium parse-back gate in both languages, the route-level envelope family (bytes only after gate.ok, no PDF key on failure, 422 strict set, runs.jsonl pin, no-LLM scan), and the review-fix regression tests (CR-01 partial-profile real export, CR-02 uppercase-accent real render, WR-01 same-company positional join, IN-02 contact/heading attribution). The frontend compiles clean against the backend envelope, with zero new dependencies across the entire phase commit range. The two ⚠️ PRESENT_BEHAVIOR_UNVERIFIED truths are the React runtime behaviors no frontend test runner can exercise (the project has none by design) — they are routed to human verification along with the four deferred checkpoint checks, not absorbed as passes and not treated as gaps.

---

_Verified: 2026-09-27T22:59:02Z_
_Verifier: Claude (gsd-verifier)_
