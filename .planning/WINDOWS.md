---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 2
total_count: 3
last_updated: 2026-09-26T00:48:40.525Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | stub | frontend/src/constants/ui.ts | 5 | Nav items Curriculo/LinkedIn are disabled future-module placeholders (D-12; modules arrive in phases 3/6) | open |  | 2026-09-26T00:09:51.974Z |  |
| 2 | 01 | stub | frontend/src/App.tsx | 55 | Perfil completeness grid + resume preview deferred to plan 03 (D-12 scope split) | fixed |  | 2026-09-26T00:09:52.721Z | 2026-09-26T00:48:39.755Z |
| 3 | 01 | deviation | backend/app/profile/loader.py | 48 | Interim Pydantic error rendering; full PT-BR mapper lands in plan 02 at same call sites | fixed |  | 2026-09-26T00:09:53.460Z | 2026-09-26T00:48:40.525Z |

````json
[
  {
    "id": 1,
    "kind": "stub",
    "phase": "01",
    "file": "frontend/src/constants/ui.ts",
    "line": 5,
    "description": "Nav items Curriculo/LinkedIn are disabled future-module placeholders (D-12; modules arrive in phases 3/6)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-26T00:09:51.974Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 2,
    "kind": "stub",
    "phase": "01",
    "file": "frontend/src/App.tsx",
    "line": 55,
    "description": "Perfil completeness grid + resume preview deferred to plan 03 (D-12 scope split)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-26T00:09:52.721Z",
    "resolved_at": "2026-09-26T00:48:39.755Z",
    "milestone": null
  },
  {
    "id": 3,
    "kind": "deviation",
    "phase": "01",
    "file": "backend/app/profile/loader.py",
    "line": 48,
    "description": "Interim Pydantic error rendering; full PT-BR mapper lands in plan 02 at same call sites",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-26T00:09:53.460Z",
    "resolved_at": "2026-09-26T00:48:40.525Z",
    "milestone": null
  }
]
````
