---
phase: 07-application-tracker-pipeline-follow-up
recorded: 2026-11-10
source: 07-REVIEW.md (status: issues_found)
---

# Code Review Disposition — Phase 07

Ledger: one row per finding from 07-REVIEW.md. Disposition values: `open` | `fixed` | `skipped` | `deferred`. Reconciled from 07-REVIEW-FIX.md when a fix pass runs; hand-edits allowed (edit the Disposition cell + add the reason in Source).

open: 10 of 12 — 0 critical, 5 warning, 5 info

| ID | Title | Severity | Disposition | Source |
|----|-------|----------|-------------|--------|
| CR-01 | SQLite connection used across threads under concurrency — `sqlite3.ProgrammingError` + silent data loss (200 ok, write rolled back) | critical | fixed | 07-REVIEW-FIX.md — `check_same_thread=False` + docstrings corrected; factory-spy + behavioral cross-thread pins. Commit `42dc4e1` |
| CR-02 | Calendar-invalid dates accepted (regex-only validation) → unhandled `ValueError` → HTTP 500 on create; one poisoned event row breaks `GET /api/tracker/resumo` permanently | critical | fixed | 07-REVIEW-FIX.md — `DataISO` AfterValidator (`date.fromisoformat`) on all five date field sites; four named 422 vectors. Commit `2a1ddcc` |
| WR-01 | A lapsed (vencido) follow-up is permanently unresolvable — the red line can never be cleared | warning | open |  |
| WR-02 | Follow-up controls vanish on the day the follow-up is due | warning | open |  |
| WR-03 | CSV formula-injection guard misses the tab/CR prefix bypass | warning | open |  |
| WR-04 | `link_vaga` rendered as a raw anchor href — `javascript:`/`data:` scheme XSS sink | warning | open |  |
| WR-05 | The edit form can never clear any optional field — omitted empty keys mean "untouched" and null is never sent | warning | open |  |
| IN-01 | `EstagioEdicaoRequest.ordem` is a dead field that answers a misleading erro | info | open |  |
| IN-02 | Migration atomicity claim does not hold — `executescript` autocommits and `user_version` is stamped outside the transaction | info | open |  |
| IN-03 | Malformed `TRACKER_FOLLOWUP_SUGGEST_DAYS` env var crashes the app at import | info | open |  |
| IN-04 | Association event date sourced client-side can disagree with the server's "hoje" | info | open |  |
| IN-05 | `registrarDesabilitado` prop declared and documented but never supplied at the only call site | info | open |  |
