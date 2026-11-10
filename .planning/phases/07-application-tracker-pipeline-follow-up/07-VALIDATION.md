---
phase: "7"
slug: "application-tracker-pipeline-follow-up"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-10"
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from 07-RESEARCH.md §Validation Architecture (codebase-grounded; tracker é 100% determinístico — D-15 — então quase tudo é testável offline).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.1.1 (offline by default, `addopts = "-m 'not llm'"`); frontend gate = `tsc -b` via `npm run build` (sem runner JS novo — D-14) |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `cd backend && uv run pytest tests/test_tracker_api.py tests/test_tracker_service.py tests/test_tracker_db.py -q` |
| **Full suite command** | `cd backend && uv run pytest -q` + `cd frontend && npm run build` |
| **Estimated runtime** | ~30s (tracker tests puros SQLite/tmp_path, sem rede) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/test_tracker_api.py tests/test_tracker_service.py tests/test_tracker_db.py -q`
- **After every plan wave:** Run `cd backend && uv run pytest -q` + `cd frontend && npm run build`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | TRK-01 | T-07-01 / — | SQL parametrizado; DB em `data/` fora do git | unit | `cd backend && uv run pytest tests/test_tracker_db.py -q` | ❌ W0 | ⬜ pending |
| 07-01-* | 01 | 1 | TRK-02 | T-07-01 | Stage deletion bloqueada enquanto referenciada; router antes do mount SPA | unit | `cd backend && uv run pytest tests/test_tracker_api.py -q` | ❌ W0 | ⬜ pending |
| 07-02-* | 02 | 2 | TRK-03/04 | T-07-01 | Envelope 200+{status,erros}; extra=forbid → 422; contadores só de eventos | unit | `cd backend && uv run pytest tests/test_tracker_api.py tests/test_tracker_service.py -q` | ❌ W0 | ⬜ pending |
| 07-03-* | 03 | 3 | TRK-05 | — | Prazos: future=pending, past=vencido; badge em exatamente N dias (vetores com `hoje` injetado) | unit | `cd backend && uv run pytest tests/test_tracker_service.py -q` | ❌ W0 | ⬜ pending |
| 07-0X | exports | — | TRK-06 | T-07-02 | CSV com BOM + sanitização de fórmula (`= + - @`); nenhum endpoint destrutivo | unit | `cd backend && uv run pytest tests/test_tracker_api.py -q` | ❌ W0 | ⬜ pending |
| ALL | todos | — | ALL | — | DTO mirror + kanban compila + nav union (`tsc -b`) | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| UX | frontend | — | UX | — | Drag feel, keyboard DnD, cores âmbar/vermelho | manual-only | /gsd:verify-work (convenção da casa para UAT de UI) | human_needed | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_tracker_db.py` — migrations + env override + seed de estágios
- [ ] `backend/tests/test_tracker_service.py` — contadores + vetores de follow-up/prazo com `hoje` injetado
- [ ] `backend/tests/test_tracker_api.py` — envelope contracts, router-order, 422s, export BOM
- [ ] Test isolation: tracker tests apontam `TRACKER_DB` para `tmp_path` (monkeypatch env) — nunca o `data/` real
- [ ] Frontend install: `npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities` (a única exceção de dep — D-14)
- Framework install: none needed (pytest present; no JS test runner — house rule)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drag-and-drop fluido no kanban | UX (D-14) | Feel de interação não é observável por build/tsc | Arrastar cartão entre estágios; verificar persistência após reload |
| Navegação por teclado no DnD | UX (D-14) | Comportamento de sensor acessível | Focar cartão, usar teclas de rearranjo do @dnd-kit |
| Destaques visuais de prazo (âmbar/vermelho) | TRK-05 (D-09/D-11) | Cor renderizada não é afirmável por build | Conferir badges "vence em X dias" / "venceu há X dias" na visão geral |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
