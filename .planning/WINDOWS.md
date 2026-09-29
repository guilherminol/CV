---
schema_version: 1
open_count: 6
waived_count: 0
fixed_count: 2
total_count: 8
last_updated: 2026-09-29T18:31:24.665Z
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
| 4 | 3 | lint-warning | frontend/src/components/KeywordsPanel.tsx | 26 | oxlint react(only-export-components) warning: plan-mandated pure export resumoCoberturaCopy from a component file; dev-only fast-refresh caveat, build unaffected | open |  | 2026-09-26T22:26:11.802Z |  |
| 5 | 3 | lint-warning | frontend/src/components/KeywordsPanel.tsx | 26 | oxlint only-export-components warning: plan-mandated pure export resumoCoberturaCopy; dev-only fast-refresh caveat, build unaffected | open |  | 2026-09-26T22:26:19.985Z |  |
| 6 | 3 | unrun-verify | backend/tests/test_llm_harness.py | 116 | Task 3 human-check: Currículo browser walkthrough (SC1-SC5 zones/badges/chips/ephemeral notice, 30+ keyword backstop) + PT-BR prose quality read not executable by the subagent executor - routed to end-of-phase human verification (human_verify_mode=end-of-phase) | open |  | 2026-09-26T22:41:33.828Z |  |
| 7 | 4 | unrun-verify | .planning/phases/04-pdf-export-ats-self-check/04-VALIDATION.md |  | 04-03 Task 3 human checkpoint deferred [auto - silence]: SC1 PDF-vs-screen fidelity, SC3 download UX feel, SC2/EN heading viewer inspection, backstop full-page readability not executable by the executor - routed to /gsd-verify-work 4 as human_needed UAT (automation green: 223 tests incl. real-render parse-back gate, build green) | open |  | 2026-09-27T22:06:40.390Z |  |
| 8 | 5 | unrun-verify | .planning/phases/05-review-flow-fact-safety/05-VALIDATION.md |  | 05-04 human checkpoint deferred (run convention): SC4 locking matrix across the 4 destructive paths, SC3 comparison amber marks + legend + zero-suspects line + company fallback, SC2 edits-flow-to-export, policy line + refresh return, disclosures-open backstop were NOT executed in the browser (user unavailable). Routed to /gsd-verify-work 5 as human_needed UAT. Automation green stands: 266 passed/7 deselected + frontend build (standing proofs per check in 05-04-SUMMARY.md Deferred table) | open |  | 2026-09-29T18:31:24.665Z |  |

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
  },
  {
    "id": 4,
    "kind": "lint-warning",
    "phase": "3",
    "file": "frontend/src/components/KeywordsPanel.tsx",
    "line": 26,
    "description": "oxlint react(only-export-components) warning: plan-mandated pure export resumoCoberturaCopy from a component file; dev-only fast-refresh caveat, build unaffected",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-26T22:26:11.802Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 5,
    "kind": "lint-warning",
    "phase": "3",
    "file": "frontend/src/components/KeywordsPanel.tsx",
    "line": 26,
    "description": "oxlint only-export-components warning: plan-mandated pure export resumoCoberturaCopy; dev-only fast-refresh caveat, build unaffected",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-26T22:26:19.985Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 6,
    "kind": "unrun-verify",
    "phase": "3",
    "file": "backend/tests/test_llm_harness.py",
    "line": 116,
    "description": "Task 3 human-check: Currículo browser walkthrough (SC1-SC5 zones/badges/chips/ephemeral notice, 30+ keyword backstop) + PT-BR prose quality read not executable by the subagent executor - routed to end-of-phase human verification (human_verify_mode=end-of-phase)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-26T22:41:33.828Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 7,
    "kind": "unrun-verify",
    "phase": "4",
    "file": ".planning/phases/04-pdf-export-ats-self-check/04-VALIDATION.md",
    "line": null,
    "description": "04-03 Task 3 human checkpoint deferred [auto - silence]: SC1 PDF-vs-screen fidelity, SC3 download UX feel, SC2/EN heading viewer inspection, backstop full-page readability not executable by the executor - routed to /gsd-verify-work 4 as human_needed UAT (automation green: 223 tests incl. real-render parse-back gate, build green)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-27T22:06:40.390Z",
    "resolved_at": null,
    "milestone": null
  },
  {
    "id": 8,
    "kind": "unrun-verify",
    "phase": "5",
    "file": ".planning/phases/05-review-flow-fact-safety/05-VALIDATION.md",
    "line": null,
    "description": "05-04 human checkpoint deferred (run convention): SC4 locking matrix across the 4 destructive paths, SC3 comparison amber marks + legend + zero-suspects line + company fallback, SC2 edits-flow-to-export, policy line + refresh return, disclosures-open backstop were NOT executed in the browser (user unavailable). Routed to /gsd-verify-work 5 as human_needed UAT. Automation green stands: 266 passed/7 deselected + frontend build (standing proofs per check in 05-04-SUMMARY.md Deferred table)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-29T18:31:24.665Z",
    "resolved_at": null,
    "milestone": null
  }
]
````
