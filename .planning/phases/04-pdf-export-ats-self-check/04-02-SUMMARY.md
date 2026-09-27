---
phase: 04-pdf-export-ats-self-check
plan: 02
subsystem: api
tags: [fastapi, export, self-check, envelope, ats, parse-back-gate, base64]

# Dependency graph
requires:
  - phase: 04-pdf-export-ats-self-check (plan 01)
    provides: build_resume_html / join_experience_dates / iter_rendered_strings / HEADINGS / section_keys, html_to_pdf engine seam, parse_back_check + GateResult, ExportError, session real-render fixture persona
  - phase: 03-resume-vertical-slice
    provides: coverage.classify_coverage / keyword_in_text (the locked D-15 deterministic matcher), routes/resume.py 200-envelope pattern, Profile/ExperienciaGerada/Keyword schemas
provides:
  - backend/app/export/selfcheck.py — build_selfcheck(pdf_text, keywords, idioma, gate) -> {ordem, sobrevivencia, gate} reusing classify_coverage verbatim
  - GateResult extended: flat_text (whitespace-normalized extraction) + ordem_rows (leading contato row + one row per exported section, honest partial order on failure)
  - POST /api/resume/exportar — one-shot render → PDF → gate → envelope route with strict ExportarRequest (extra=forbid)
  - export router registered BEFORE the SPA mount in main.py
  - test_export_api.py envelope family (14 tests); test_survival_on_pdf_text + ordem-row pins in test_export_gate.py (26 total in file)
affects: [04-03 (frontend ExportZone + SelfCheckPanel mirror the envelope contract pinned here)]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 9653         # 38612 chars / 4 over the realized diff (6 files, +766/-4)
  tasks: 2
  commits: 2           # MEASURED: git rev-list --count 6725aa0..HEAD
commits: 2
plan_head_before: 6725aa0032c70c11d97877441a088c762b37ae2e

# Tech tracking
tech-stack:
  added: []
  patterns: [one-GateResult-feeds-both-delivery-and-selfcheck (no second extraction, no divergent verdicts), gate-failure erro carries NO PDF key (ordering IS the D-07 guarantee), strict request floors mirroring the all-or-nothing generation envelope, monkeypatch-at-module-under-test seam, no-LLM-machinery AST scan scoped to export modules, runs.jsonl before/after count pin]

key-files:
  created:
    - backend/app/export/selfcheck.py
    - backend/app/routes/export.py
    - backend/tests/test_export_api.py
  modified:
    - backend/app/export/gate.py
    - backend/app/main.py
    - backend/tests/test_export_gate.py

key-decisions:
  - "REVIEW-03 left UNCHECKED in REQUIREMENTS.md: this plan completes its data layer (order rows + honest survival over real PDF text, both languages); the user-facing panel is plan 04-03's surface — only plans that complete the user story mark the requirement."
  - "No-LLM structural test calibrated to the CALL machinery: bans app.llm gateway/prompts/logging/client + app.resume.pipeline imports across backend/app/export/* and routes/export.py; ALLOWS app.llm.schemas (pure DTOs the plan itself mandates for the request model). The literal 'no app.llm import' reading would fail the plan's own required imports."
  - "Ordem rows record HONEST PARTIAL ORDER on failing gates: rows before the failed key are ok=True (found at monotonic positions), the failed key and everything after ok=False — a future UI could show partial order even though export rejects."
  - "The real-render API test reuses 04-01's exact persona (test-module import of _persona) and pins the runs.jsonl before/after line count in the same session fixture — the LLM-calls-only logging contract is enforced, not convention."

requirements-completed: []

# Metrics
duration: 14min
completed: 2026-09-27
status: complete
---

# Phase 4 Plan 2: Self-Check Payload + Export Endpoint Summary

**POST /api/resume/exportar — one sync-def request renders the submitted displayed state, runs the four-check parse-back gate, and answers the house 200 envelope: base64 PDF + self-check payload on gate-ok, named PT-BR failure lines with NO PDF key on failure**

## Performance

- **Duration:** 14 min
- **Started:** 2026-09-27T21:25:56Z
- **Completed:** 2026-09-27T21:39:54Z
- **Tasks:** 2
- **Files modified:** 6 (+766/−4 lines)

## Accomplishments
- Self-check payload builder (`build_selfcheck`) reuses the Phase 3 matcher **verbatim** (D-15: canonical OR alias, case/punctuation-insensitive, run-language candidate order) over the FULL extracted PDF text — proven against real Chromium renders in both languages with zero new matching logic; counts-only honesty pinned structurally (sobrevivencia entries carry exactly canonical/category/termo/status — no score, no ratio, no meter)
- GateResult now carries `flat_text` + `ordem_rows` from the SAME pass the delivery decision uses — one gate pass feeds the whole self-check (no second extraction, no divergent verdicts); ordem rows honestly record partial order on failing gates
- `POST /api/resume/exportar`: strict `ExportarRequest` (extra=forbid; min_length=1 floors make an empty/partial section set a loud 422 — the route can never render an empty or partial document), plain-`def` handler (sync Playwright), gate-failure answers `{status: erro, erros}` with raw detail terminal-only and **no PDF payload key under any circumstance** (D-07/D-08/T-04-04)
- Export router registered before the SPA mount; full offline suite green with zero regressions: **223 passed, 7 deselected** (llm) — up from 202 in 04-01 (21 new tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: selfcheck.py — honest survival + order rows from one GateResult** - `7ee0792` (feat)
2. **Task 2: POST /api/resume/exportar — envelope route, strict request, main.py wiring, full API test family** - `83ef32d` (feat)

**Plan metadata:** committed after SUMMARY (docs: complete plan)

## The 04-03 Contract (envelope field names — normative)

Request `POST /api/resume/exportar`:

```jsonc
{
  "perfil": PerfilDTO,                        // app.profile.models.Profile — verbatim displayed state (D-10)
  "secoes": {
    "resumo": "string",                       // Field(min_length=1, max_length=8000)
    "experiencias": [ExperienciaGeradaDTO],   // Field(min_length=1)
    "habilidades": ["string"]                 // Field(min_length=1)
  },
  "keywords": [KeywordDTO],                   // may be [] — zero-keyword runs are legitimate
  "idioma": "pt-BR" | "en"                    // Literal, REQUIRED (no default — a missing idioma is a client bug → 422)
}
```

ok response (HTTP 200):

```jsonc
{ "status": "ok",
  "filename": "curriculo-{idioma}-{YYYY-MM-DD}.pdf",   // e.g. curriculo-pt-BR-2026-09-27.pdf (D-11)
  "pdf_base64": "<ascii base64 of the PDF bytes>",
  "selfcheck": {
    "ordem": [ {"id": "contato", "ok": true}, {"id": "<section_key>", "ok": true}, ... ],
    "sobrevivencia": [ {"canonical": "Python", "category": "competencias", "termo": "Python", "status": "coberto"} ],
    "gate": { "coocorrencia": true, "acentos": true }
  } }
```

gate-failure / export-error response (HTTP 200 — house envelope):

```jsonc
{ "status": "erro", "erros": ["PT-BR line naming the failed check"] }
// NO "filename", NO "pdf_base64", NO "selfcheck" keys — ever (T-04-04, test-pinned)
```

**Normative ordem row ids (the label-mapping contract):** `"contato"` + `render.section_keys` — `contato, resumo, experiencias, formacao, habilidades, certificacoes, idiomas, projetos` — one row per section ACTUALLY exported, in render order (empty passthrough sections render no row). The research Pattern 4 example's singular `"experiencia"` spelling is superseded by the plural `section_keys` as shipped in render.py. The frontend maps ids to labels and renders unknown ids raw — never silently dropped (D-14).

**Field bound values chosen:** `resumo` 1..8000 chars (≈10x the longest realistic summary; JD_MAX_LENGTH precedent); `experiencias` / `habilidades` `min_length=1`; `keywords` unbounded list (may be empty).

**Failure lines the frontend must render verbatim:** gate lines live only in `backend/app/export/gate.py` (contact-first, section-out-of-order per key, co-occurrence per company, accent integrity); the chromium-missing line lives only in `backend/app/export/pdf.py` ("O navegador de renderização não está instalado. Execute `uv run playwright install chromium` e tente novamente."). Raw extracted text / exception detail is terminal-only, NEVER an envelope field (T-04-03, caplog-pinned).

## Files Created/Modified
- `backend/app/export/selfcheck.py` - build_selfcheck: {ordem = gate.ordem_rows verbatim, sobrevivencia = classify_coverage over the FULL PDF text, gate = {coocorrencia, acentos} from the passed-in GateResult}; module docstring documents the input difference vs Phase 3 (passthrough sections included — D-15 audits the sendable artifact)
- `backend/app/export/gate.py` - GateResult gains flat_text + ordem_rows (default_factory); heading walk runs once for both the check-2 verdict and the rows; every return path records what was found
- `backend/app/routes/export.py` - POST /api/resume/exportar: strict ExportarRequest/ExportarSecoes, _expected_doc from render outputs (dateless entries skip only the date sub-check), gate-failure erro without PDF key, ExportError → install-hint envelope, no runs.jsonl write, no bytes/base64 logging
- `backend/app/main.py` - export router included after resume, before the SPA mount
- `backend/tests/test_export_gate.py` - +7 tests: test_survival_on_pdf_text (real extracted text, both languages: pt rendering wins pt-BR, en wins en, alias-only survival via "Docker", ausente termo None, loud-zero), test_ordem_rows_on_real_pdf (contato first + section_keys order, all ok), partial-order and contato-false failure rows, footer-from-same-GateResult
- `backend/tests/test_export_api.py` - 14 tests: ok envelope both languages (exact key set, filename regex, base64 round-trip, selfcheck shape), gate-failure erro (no PDF key + caplog terminal-only split), browser-missing erro (install hint), 5-case 422 strict set, sync-def + router-before-mount structural pins, no-LLM-machinery AST scan, one REAL render end-to-end (D-07 proof at the route layer, includes runs.jsonl no-write pin)

## Decisions Made

**REVIEW-03 not marked complete.** The plan frontmatter lists `requirements: [REVIEW-02, REVIEW-03]`, but REVIEW-02 was already checked by 04-01 and REVIEW-03's user story ("user can RUN an ATS self-check") completes only when the panel renders in 04-03. Marking it now would falsify REQUIREMENTS.md; `requirements mark-complete` was deliberately skipped.

**No-LLM structural test calibration.** The prohibition's parenthetical "(gateway/prompts/client)" is operative: the scan bans `app.llm.gateway/prompts/logging/client` and `app.resume.pipeline` imports in export modules while allowing `app.llm.schemas` — the route legitimately imports ExperienciaGerada/Keyword from schemas (D-10 displayed-state reuse), so a literal "no app.llm import" rule would fail the plan's own required code.

**idioma has no default on ExportarRequest** (unlike GerarRequest): the exported state always carries the run language from the screen; absence is a malformed request → 422 (D-12 without an extra selector).

**Manual /docs smoke substituted by a stronger automated proof.** The plan's `<verification>` names a manual smoke from /docs; the real-render API test POSTs the actual route through the full ASGI app with the real Chromium + real gate and asserts the complete ok envelope (including the `%PDF-` magic header) — the same path, automated. The interactive smoke will occur naturally with 04-03's Export button.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Two in-task bugs caught by tests BEFORE the Task 1 commit (normal dev loop, fixed in `7ee0792`): (1) the new `_ordem_rows` helper initially appended the failed key with `ok=True` before setting the failure flag — its own test caught it; (2) a test fixture string used `ana@exemplo.com` instead of the module's `EMAIL` constant (`ana.exemplo@example.com`), tripping the contact-first check for the wrong reason.

## Known Stubs

None. Repo-wide scan of app/export/, routes/export.py and both test files found no TODO/FIXME/placeholder patterns; every payload key is wired to real data (the frontend consumer is 04-03's scope, not a stub).

## User Setup Required

None — no new dependencies; the export path uses the already-installed playwright==1.62.0 + cached chromium-1234 (setup documented in README since 04-01).

## Next Phase Readiness
- Plan 04-03 consumes the contract pinned above (mirror it in `frontend/src/api/client.ts` as `ExportarResponse`; `tsc -b` is the drift gate): envelope union `{status:"ok", filename, pdf_base64, selfcheck} | {status:"erro", erros}`, ordem row ids `contato + section_keys`, sobrevivencia entries shaped exactly like `CoberturaItemDTO`, footer booleans `gate.coocorrencia` / `gate.acentos`
- Blob download recipe: `Uint8Array.from(atob(data.pdf_base64), c => c.charCodeAt(0))` → `URL.createObjectURL(new Blob([bytes], {type: "application/pdf"}))` → anchor `download: data.filename` → revoke
- Loud-zero edge: a `keywords: []` request yields `sobrevivencia: []` — the UI line for that is already consumed by test
- No blockers: full offline suite 223 passed / 7 deselected; both export test files green standalone (40 passed)

---
*Phase: 04-pdf-export-ats-self-check*
*Completed: 2026-09-27*

## Self-Check: PASSED

All 6 claimed files exist on disk; both task commits found in git history (7ee0792, 83ef32d); commit count measured from the plan ledger (6725aa0..HEAD) = 2.
