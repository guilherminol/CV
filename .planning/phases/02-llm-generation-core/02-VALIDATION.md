---
phase: "2"
slug: "llm-generation-core"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-25"
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Python 3.12, uv-managed) |
| **Config file** | backend/pyproject.toml (markers + addopts) |
| **Quick run command** | `cd backend && uv run pytest -q` |
| **Full suite command** | `cd backend && uv run pytest -q && uv run pytest -m llm -q` |
| **Estimated runtime** | ~10 s offline; ~60–120 s with `-m llm` (network) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest -q`
- **After every plan wave:** Run `cd backend && uv run pytest -q` (plus `-m llm` when OPENROUTER_API_KEY is set)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds (offline suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | PROFILE-03 | — | N/A | unit | `cd backend && uv run pytest tests/test_prompt_loader.py -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | PROFILE-03 | — | API key never logged | unit (mocked) | `cd backend && uv run pytest tests/test_gateway.py -q` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | PROFILE-03 | — | N/A | unit (mocked retry) | `cd backend && uv run pytest tests/test_gateway.py -q` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | PROFILE-03 | — | logs/ gitignored | unit | `cd backend && uv run pytest tests/test_run_log.py -q` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | PROFILE-03 | — | N/A | integration (llm marker) | `cd backend && uv run pytest -m llm -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_prompt_loader.py` — stubs for PROFILE-03 (strict prompt frontmatter validation)
- [ ] `backend/tests/test_gateway.py` — stubs (mocked OpenRouter: happy path, malformed-response retry, loud failure)
- [ ] `backend/tests/test_run_log.py` — stubs (JSONL line schema, retry attempt numbers)
- [ ] `backend/tests/test_keywords.py` — stubs (bilingual mapping shape, category enum)
- [ ] `llm` marker registered in `backend/pyproject.toml` with `addopts = "-m 'not llm'"`

*Existing pytest infrastructure from Phase 1 covers the runner itself.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real EN + PT-BR generation quality | PROFILE-03 | Requires real API + human judgment of prose | Set OPENROUTER_API_KEY in backend/.env; run `uv run pytest -m llm -q`; inspect logs/runs.jsonl lines and generated text in both languages |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
