---
phase: "4"
slug: "pdf-export-ats-self-check"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-27"
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 04-RESEARCH.md §Validation Architecture (probe-verified on this machine).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (backend/pyproject.toml `[tool.pytest.ini_options]`, `addopts = -m 'not llm'` — offline default) |
| **Config file** | backend/pyproject.toml (exists) |
| **Quick run command** | `cd backend && uv run pytest tests/test_export_gate.py tests/test_export_api.py -x` |
| **Full suite command** | `cd backend && uv run pytest` (+ `cd frontend && npm run build` for tsc drift lock) |
| **Estimated runtime** | ~20 seconds (session-scoped real render ≈3s once, then offline gate units) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_export_gate.py tests/test_export_api.py -x`
- **After every plan wave:** Run `cd backend && uv run pytest` + `cd frontend && npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~20 seconds

---

## Per-Task Verification Map

Task IDs are assigned when the planner creates plans (Wave 0 seeds below). Requirement→test mapping is fixed by research:

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (planner maps) | 01 | 0→1 | REVIEW-02 | — | N/A | integration (session-scoped real render, offline) | `cd backend && uv run pytest tests/test_export_gate.py::test_gate_passes_real_pdf[pt-BR] -x` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | REVIEW-02 | — | N/A | integration | `...::test_gate_passes_real_pdf[en] -x` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | REVIEW-02 | — | N/A | unit (template pure function: order mirrors ResumeResult, interpolations escaped) | `...::test_render_html -x` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | REVIEW-03 | — | N/A | unit (synthetic text — order check fails loud with named PT-BR line) | `...::test_order_failures -x` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | REVIEW-03 | — | N/A | unit (co-occurrence + accents, incl. mojibake rejection) | `...::test_cooccurrence_and_accents -x` | ❌ W0 | ⬜ pending |
| (planner maps) | 02 | 1→2 | REVIEW-03 | T-04 (envelope) | gate failure never leaks raw detail; 200-envelope contract | integration (renderer stubbed; 1 real-render case) | `cd backend && uv run pytest tests/test_export_api.py -x` | ❌ W0 | ⬜ pending |
| (planner maps) | 02 | 1→2 | REVIEW-03 | — | N/A | unit (keyword survival via `keyword_in_text` on extracted PDF text, per language) | `...::test_survival_on_pdf_text -x` | ❌ W0 | ⬜ pending |
| (planner maps) | last | 2 | UI-SPEC copy | — | N/A | frontend pure-function contract (no JS runner — mirror `resumoCoberturaCopy` pattern) | manual review + `npm run build` | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_export_gate.py` — REVIEW-02/REVIEW-03 gate + render unit tests + session PDF fixture
- [ ] `backend/tests/test_export_api.py` — envelope/error contract + real-render case
- [ ] `backend/app/export/` module skeleton (engine seam first, per D-02 sequencing)
- [ ] `uv add playwright==1.62.0 pypdf` + documented `uv run playwright install chromium` (no-op on this machine — browser cached) — with planner's human-verify checkpoint

*Framework install: none needed — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Downloaded PDF opens in a real PDF viewer and looks like the reviewed in-app resume | REVIEW-02 (SC1) | visual fidelity is human judgment | Export from the running app (PT-BR run), open `curriculo-pt-br-{data}.pdf`, compare against the on-screen result card |
| Download UX (automatic download, filename, receipt + self-check panel appear) | REVIEW-03 (SC3) | browser download behavior not assertable offline | Run export in the browser; confirm download starts, receipt names the file, panel shows ✓ order rows and survival chips |
| EN export headings render in English in the PDF | SC2 (both languages) | rendered-glyph inspection | Export an EN run; confirm headings (Summary/Experience/Education/…) in the PDF text layer and visually |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
