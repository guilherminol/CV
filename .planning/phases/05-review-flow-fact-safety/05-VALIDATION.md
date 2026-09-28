---
phase: "5"
slug: "review-flow-fact-safety"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-27"
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 05-RESEARCH.md §Validation Architecture (codebase-grounded; 232 tests green at research time).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.1.1 (backend dev group); frontend has NO JS test runner by design (tsc -b + UAT only) |
| **Config file** | backend/pyproject.toml `[tool.pytest.ini_options]` — `addopts = "-m 'not llm'"` |
| **Quick run command** | `cd backend && uv run pytest -q` |
| **Full suite command** | `cd backend && uv run pytest -q` + `cd frontend && npm run build` |
| **Estimated runtime** | ~12 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q` (+ `npm run build` on frontend tasks)
- **After every plan wave:** Full backend suite + frontend build green
- **Before `/gsd:verify-work`:** Full suite green + manual UAT of the SC4 locking matrix and comparison panel
- **Max feedback latency:** ~12 seconds

---

## Per-Task Verification Map

Task IDs are assigned when the planner creates plans. Requirement→test mapping fixed by research:

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (planner maps) | 01 | 0→1 | SC1 (regen) | — | N/A | unit+route (offline, ScriptedClient + stubbed run_stage) | `cd backend && uv run pytest tests/test_resume_regen_pipeline.py tests/test_resume_regen_api.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | SC1 (hint) | T-02-01 class | hint reaches USER message only; system prompt untouched; runs.jsonl fields unchanged | unit (assert on recorded create() kwargs) | `cd backend && uv run pytest tests/test_resume_regen_pipeline.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | — | — | SC2 (edits→PDF) | — | N/A | already proven (Phase 4 suite posts displayed state) | `cd backend && uv run pytest tests/test_export_api.py -q` | ✅ | ⬜ pending |
| (planner maps) | 02 | 1→2 | SC3 (comparison) | — | N/A | Python mirror vectors (existing coverage primitives) + tsc + UAT for the TS port | `cd backend && uv run pytest tests/test_coverage.py -q` + `cd frontend && npm run build` | partial ✅ / ❌ TS | ⬜ pending |
| (planner maps) | last | 2 | SC4 (no silent destroy) | — | N/A | mostly manual UAT (locking matrix); version-helper invariant reviewable | manual checklist at `/gsd-verify-work 5` | ❌ UAT doc | ⬜ pending |
| (planner maps) | 01 | 0→1 | Structural | — | sync def + router-before-mount for regenerar | structural | `cd backend && uv run pytest tests/test_resume_api.py -q` (extend path lists) | ✅ extend | ⬜ pending |
| (planner maps) | 01 | 0→1 | Strict validation | — | 422 on unknown keys / short jd / unknown secao / empty sections | route | `cd backend && uv run pytest tests/test_resume_regen_api.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_resume_regen_api.py` — envelope + 422 + structural coverage for the new route
- [ ] `backend/tests/test_resume_regen_pipeline.py` — one-stage run, sibling identity, hint-as-data assertions
- [ ] Planner decision (not a file): TS-side verification approach for `lib/comparison.ts` — RESOLVED by orchestrator: no JS test runner (house rule, Phase 3 D-03); pure function + tsc -b + phase UAT

*Framework install: none needed — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SC4 locking matrix (stack-before-mutate + 3 amber confirm strips across save/regen/restore/full-regen paths) | REVIEW-01 (SC4) | interaction sequencing in a no-JS-test-runner frontend | In the running app: edit a section → regenerate (expect confirm strip; accept → prior version stacked); restore a version; cancel editing with changes (expect strip) |
| Invention highlights render as amber suspicion marks with legend; zero-suspects loud line | REVIEW-01 (SC3) | visual rendering of the TS highlighter | Generate, expand "Comparar com o perfil", verify amber marks + legend; edit text to remove a suspect and re-check |
| Edited text flows to export + self-check | REVIEW-01 (SC2) | end-to-end UI flow | Edit a section → export → PDF + survival panel reflect the edited text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 12s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
