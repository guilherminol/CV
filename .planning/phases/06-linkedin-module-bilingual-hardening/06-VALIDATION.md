---
phase: "6"
slug: "linkedin-module-bilingual-hardening"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-29"
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 06-RESEARCH.md §Validation Architecture (codebase-grounded; 267 offline tests green at research time).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend, offline default) + `tsc -b` (frontend drift lock); NO JS test runner |
| **Config file** | backend/pyproject.toml (`addopts = "-m 'not llm'"`) |
| **Quick run command** | `cd backend && uv run pytest -q` |
| **Full suite command** | `cd backend && uv run pytest -q` + `uv run pytest -m llm` (spend — the SC4 DoD) + `cd frontend && npm run build` |
| **Estimated runtime** | ~15s offline; `-m llm` adds real-API spend (run explicitly at phase gate) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q` (+ `npm run build` on frontend tasks)
- **After every plan wave:** Full offline suite + frontend build green
- **Before `/gsd:verify-work`:** Offline green + `uv run pytest -m llm` green (bilingual LinkedIn fixtures) — **this IS the SC4 definition-of-done mechanism**
- **Max feedback latency:** ~15 seconds (offline)

---

## Per-Task Verification Map

Task IDs are assigned when the planner creates plans. Requirement→test mapping fixed by research:

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (planner maps) | 01 | 0→1 | LI-01 | — | N/A | unit/integration (offline) | `cd backend && uv run pytest tests/test_linkedin_pipeline.py tests/test_linkedin_api.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | LI-02 | — | N/A | unit (headline block, 220-constant plumbing) | `cd backend && uv run pytest tests/test_linkedin_schema.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | LI-03 | — | N/A | unit (sobre block, 2600-constant plumbing) | `cd backend && uv run pytest tests/test_linkedin_schema.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 02 | 1→2 | LI-04 | — | N/A | unit (one experiências stage, per-entry bounds) | `cd backend && uv run pytest tests/test_linkedin_regen_pipeline.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 02 | 1→2 | LI-05 | — | N/A | unit (skills priority order + copy-ready blocks) | `cd backend && uv run pytest tests/test_linkedin_pipeline.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 02 | 1→2 | SC4 | — | glossary/bleed QA is deterministic — no LLM judge | unit (vectors incl. UTF-8 + negative PT controls) | `cd backend && uv run pytest tests/test_linkedin_qa.py -q` | ❌ W0 | ⬜ pending |
| (planner maps) | 03 | 2→3 | SC4 DoD | — | N/A | real-API (`-m llm`, explicit) | `cd backend && uv run pytest -m llm` | ✅ file / ❌ tests W0 | ⬜ pending |
| (planner maps) | 01 | 0→1 | drift lock | — | 4 new wire schemas pinned | unit | `cd backend && uv run pytest tests/test_linkedin_schema.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_linkedin_schema.py` — drift-lock for 4 new wire schemas
- [ ] `backend/tests/test_linkedin_qa.py` — glossary + bleed vectors (incl. UTF-8 + negative PT controls)
- [ ] `backend/tests/test_linkedin_pipeline.py` — offline 4-stage orchestration via FakeClient
- [ ] `backend/tests/test_linkedin_regen_pipeline.py` — group-swap + sibling byte-identity
- [ ] `backend/tests/test_linkedin_api.py` — envelopes + objetivo bounds
- [ ] Extend `backend/tests/test_llm_harness.py` — bilingual LinkedIn DoD tests
- [ ] `prompts/glossario.md` + 4 `prompts/linkedin-*.md` files (production artifacts; harness needs them)

*Framework install: none needed — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Copy-paste UX ("Copiar" → clipboard → "Copiado!") | LI-05 | clipboard permission lives in the browser | On the LinkedIn page: click Copiar per block, paste into a text editor, confirm exact text |
| Counters live-update (amber ≥90%, red over) + over-limit flag + regen path | LI-02/03/04 (SC2) | interaction states in a no-JS-test-runner frontend | Generate, check counters while editing; force an over-limit edit, confirm red counter + flag + regen offer |
| QA panel framing (glossary substitutions listed, bleed avisos non-blocking) | SC4 | visual rendering of the report | Generate PT-BR, check "Verificação de idioma" panel: substitutions listed, bleed items flagged, generate NOT blocked |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s (offline)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
