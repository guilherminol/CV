---
phase: "3"
slug: "resume-vertical-slice"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-26"
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from `03-RESEARCH.md` §Validation Architecture (Nyquist).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.1.1 (backend; offline by default — `addopts = "-m 'not llm'"`, `llm` marker for real-API spend) |
| **Config file** | backend/pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `cd backend && uv run pytest -q` (1.2s baseline, 87 passed / 5 deselected) |
| **Full suite command** | `cd backend && uv run pytest -q` + on-demand `cd backend && uv run pytest -m llm` (spend); frontend `cd frontend && npm run build` (tsc -b gate) |
| **Estimated runtime** | ~2 seconds offline (baseline 1.2s + new Wave 0 files) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q` (frontend tasks add `cd frontend && npm run build`)
- **After every plan wave:** Run full offline suite + `tsc -b`
- **Before `/gsd:verify-work`:** Full offline suite green + `cd backend && uv run pytest -m llm` bilingual resume-harness green (spend, on demand); human-verify end-of-phase per config (`human_verify_mode`)
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (seed — bind to plan task IDs at planning) | TBD | 1 | RESUME-01 | T-03 prompt injection | JD is data in user message, never instruction | offline unit (FakeClient per stage, both languages) | `cd backend && uv run pytest tests/test_resume_pipeline.py -q` | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | RESUME-01/SC5 | T-03 | lint/extract endpoint envelope, never 500 | offline route test | `cd backend && uv run pytest tests/test_resume_api.py -q` | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | RESUME-02 | — | keywords echoed verbatim, 4 fixed categories | offline unit + route | same as above | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | RESUME-03 | T-03 elevation of trust | no invented metric/tech/date; bilingual | offline fixture assertions + `-m llm` harness | `cd backend && uv run pytest tests/test_resume_grounding.py -q` ; `cd backend && uv run pytest -m llm` | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | RESUME-04 | — | matcher incl. `C++`/`.NET`/`C#`, accents, aliases, run-language field, canonical fallback | offline unit (pure-function table) | `cd backend && uv run pytest tests/test_coverage.py -q` | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | RESUME-04 | — | tally singular/plural, never a score | offline (backend-computed tally) | included in full suite | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | PROFILE-02 | — | D-04 checks (a)/(b)/(c) fire and stay silent when clean; non-blocking | offline unit (pure function over profile fixtures) | `cd backend && uv run pytest tests/test_resume_lint.py -q` | ❌ W0 | ⬜ pending |
| (seed) | TBD | 1 | PROFILE-02/RESUME-01 | T-05 secret leakage | broken-profile gate; error envelope PT-BR only, raw detail terminal-only (caplog) | offline route test | `cd backend && uv run pytest tests/test_resume_api.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_coverage.py` — matcher table incl. special-char keywords (RESUME-04)
- [ ] `backend/tests/test_resume_lint.py` — D-04 (a)/(b)/(c) + clear-line (PROFILE-02)
- [ ] `backend/tests/test_resume_pipeline.py` + scripted fake clients for the 3 new stages, both languages (RESUME-01/03)
- [ ] `backend/tests/test_resume_api.py` — route envelope, all-or-nothing, terminal-only raw detail (RESUME-01, PROFILE-02)
- [ ] Drift-lock tests for each new wire schema (extend the `test_keyword_schema.py` pattern)
- [ ] `-m llm` harness fixtures: example profile + JD_EN/JD_PT (reuse `tests/llm_fixtures.py` texts) asserting bilingual grounding
- [ ] (Conditional) vitest scaffold — only if the planner adopts research Open Question 4 option (a)
- No framework install needed for backend (pytest present; no new deps)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PT-BR generation quality reads naturally (not machine-translated) | RESUME-01/03 | Human judgment on prose quality | Run `cd backend && uv run pytest -m llm -v` with OPENROUTER_API_KEY set; read generated PT-BR sections from the harness output |
| Coverage checklist is honest and readable at 30+ keywords (UI) | RESUME-04 | Visual/backstop check per UI-SPEC | Generate from a keyword-rich JD in the browser; confirm chips wrap, groups visible, no cramping |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
