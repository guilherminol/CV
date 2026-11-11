---
phase: 07-application-tracker-pipeline-follow-up
fixed_at: 2026-11-11T10:24:03Z
review_path: .planning/phases/07-application-tracker-pipeline-follow-up/07-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 7: Code Review Fix Report

**Fixed at:** 2026-11-11T10:24:03Z
**Source review:** `.planning/phases/07-application-tracker-pipeline-follow-up/07-REVIEW.md`
**Iteration:** 1
**Scope:** CRITICAL findings only (CR-01, CR-02) — Warning/Info findings untouched, per disposition.

**Summary:**
- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### CR-01: SQLite connection used across threads under concurrency — `sqlite3.ProgrammingError` + silent data loss (200 ok, write rolled back)

**Files modified:** `backend/app/tracker/db.py`, `backend/app/routes/tracker.py`, `backend/tests/test_tracker_db.py`
**Commit:** `42dc4e1`

**Applied fix:** `conectar()` now opens the per-request connection with
`sqlite3.connect(TRACKER_DB, check_same_thread=False)` — the FastAPI-documented
relaxation for the yield-dependency pattern. The connection stays confined to a
single request's lifecycle (setup → sync handler → teardown, which anyio may
place on different threadpool workers) and is never shared across requests.
The false threading-contract claims were corrected in three docstrings:
the `db.py` module docstring (previously "SQLite's same-thread restriction is
never relaxed anywhere in this module"), the `routes/tracker.py` module
docstring ("opened on the serving thread"), and the `get_tracker_db`
dependency docstring ("opened on THIS request's thread") — all now state the
per-REQUEST confinement contract.

**Test evidence (`backend/tests/test_tracker_db.py`, +2 tests):**
- `test_conectar_relaxa_mesma_thread_por_request` — connection-factory pin: a
  spy on `sqlite3.connect` asserts `conectar()` passes
  `check_same_thread=False` (note: `Connection.check_same_thread` is not a
  readable attribute on this CPython 3.12.10/Windows build, so the attribute
  route from the review sketch was replaced by the factory-spy route the
  review explicitly allows).
- `test_conexao_aceita_uso_de_outra_thread` — behavioral pin of the exact
  production failure mode: using the connection from a thread other than the
  one that opened it (as the teardown commit/close does under a real server)
  executes without `sqlite3.ProgrammingError`.

### CR-02: Calendar-invalid dates accepted (regex-only validation) → unhandled `ValueError` → HTTP 500 on create; one poisoned event row breaks `GET /api/tracker/resumo` permanently

**Files modified:** `backend/app/tracker/models.py`, `backend/tests/test_tracker_api.py`
**Commit:** `2a1ddcc`

**Applied fix:** added a `DataISO = Annotated[str, AfterValidator(_data_iso_valida)]`
type in `models.py`, where `_data_iso_valida` calls `date.fromisoformat` so an
impossible calendar date raises `ValueError` inside pydantic → house 422 at
the DTO boundary. Applied to all five date-field sites across the four date
fields: `data_aplicacao` + `prazo_retorno` (both `CandidaturaCriacaoRequest`
and `CandidaturaEdicaoRequest`), `data_evento` (`EventoRegistroRequest`), and
`nova_data` (`FollowupAdiamentoRequest`). The existing `Field(pattern=_PADRAO_DATA)`
constraints are unchanged; the fields stay `str` (rows/JSON carry ISO strings
end-to-end) — only calendar validity is pinned. Bad input can no longer reach
`derivar_campos`/`adiar_followup` unguarded, and no poisoned event row can be
persisted, so `GET /api/tracker/resumo` cannot be broken by new input.

**Not applied (deliberate):** the review's "Optionally, defense-in-depth"
per-row projection guard in `obter_resumo` (degrade one corrupt LEGACY row to
a per-candidatura erro instead of a 500). Marked optional by the review and
outside the minimal-fix contract; with the DTO gate in place no new poisoned
row can be created. Flagged here for a future phase if legacy-row tolerance
is wanted.

**Test evidence (`backend/tests/test_tracker_api.py`, +4 named vectors, new
section (g2)):**
- `test_422_prazo_retorno_calendario_invalido_na_criacao` — create with
  `"prazo_retorno": "2026-02-30"` → 422 (the review's repro answered HTTP
  500); nothing persisted (`ativas == 0`).
- `test_422_data_evento_calendario_invalido_no_registro` — event with
  `"data_evento": "2026-13-05"` → 422 (was 200 ok + permanently-500 resumo);
  `GET /resumo` stays 200 ok afterward.
- `test_422_nova_data_calendario_invalida_no_adiar` — `"nova_data":
  "2027-02-30"` on adiar → 422 (was ValueError → 500 at service.py:347).
- `test_422_datas_calendario_invalidas_na_edicao` — edit DTO
  `data_aplicacao=2026-02-30` and `prazo_retorno=2027-04-31` → 422 each.

## Verification

**Where the gates ran (#2825):** inside the isolated review-fix worktree
(`.claude/worktrees/rf-07-1246-1794392003`, branch `gsd-reviewfix/07-1246`),
on the exact tree `1d48825` + these two commits. The worktree required two
temporary, never-committed copies from the main checkout to import `app.main`
and register the SPA mount: the untracked `backend/app/candidatura/` +
`backend/app/routes/candidatura.py` modules (HEAD's `main.py` imports them;
they are another stream's uncommitted work) and the gitignored
`frontend/dist` build output. Both are untracked/gitignored and were never
staged or committed.

- Tracker trio (`tests/test_tracker_api.py tests/test_tracker_service.py
  tests/test_tracker_db.py`): **79 passed, 0 failed** (73 baseline + 6 new).
- Full suite (`uv run pytest -q`): in the worktree, **493 passed, 4 failed** —
  the 4 failures (`test_api.py::test_get_profile_returns_ok_envelope`,
  `test_api.py::test_get_profile_ok_envelope_includes_completude`,
  `test_export_gate.py::test_gate_passes_real_pdf[en]`,
  `test_export_gate.py::test_survival_on_pdf_text[en]`) proved PRE-EXISTING
  and environmental: re-running exactly those 4 tests after
  `git checkout 1d48825` in the same worktree reproduces the identical 4
  failures (they live in the profile-envelope and PDF-export-gate modules,
  untouched by both fixes; zero tracker tests fail). **Authoritative totals
  from the MAIN checkout after the fast-forward** (real tree = baseline +
  fixes + the user's in-progress working state): tracker trio **79 passed**,
  full suite **522 passed, 9 deselected, 0 failed — fully green**.

Per-finding commits (code + tests together, atomic):
- `42dc4e1` — fix(07): CR-01 — relax sqlite3 same-thread restriction per request (check_same_thread=False)
- `2a1ddcc` — fix(07): CR-02 — reject calendar-invalid dates at the DTO boundary (DataISO AfterValidator)

## Skipped Issues

None — both in-scope findings were fixed.

---

_Fixed: 2026-11-11T10:24:03Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
