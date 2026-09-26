---
phase: 01-foundation-scaffold-master-profile
fixed_at: 2026-09-26T01:58:39Z
review_path: .planning/phases/01-foundation-scaffold-master-profile/01-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 1: Code Review Fix Report

**Fixed at:** 2026-09-26T01:58:39Z
**Source review:** .planning/phases/01-foundation-scaffold-master-profile/01-REVIEW.md
**Iteration:** 1
**Scope:** critical_warning (WR-01…WR-04; Info findings IN-01…IN-05 out of scope)

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Verification

**Where the gates ran:** inside the isolated fix worktree (`.claude/worktrees/rf-01-1098-1790387385`, branch `gsd-reviewfix/01-1098`), NOT the main checkout — the worktree had its own `uv` venv (backend) and `npm install` (frontend, 46 packages), so the numbers below are reproducible from a fresh clone of the branch, not from the pre-teardown main tree.

- Backend: `cd backend && uv run pytest -q` → **43 passed** (baseline was 35; +8 new RED/GREEN tests added by these fixes). Final run is fully green including `test_get_serves_spa_index_html` (the one intermediate failure was only the missing `frontend/dist` in the worktree, resolved by the build below).
- Frontend: `cd frontend && npm run build` → **passes** (tsc + vite, 67 modules).
- Every backend fix followed RED/GREEN: the new test was run and failed BEFORE the fix, then passed after.

## Fixed Issues

### WR-01: Unmapped Pydantic error types leak English messages into the PT-BR UI

**Files modified:** `backend/app/profile/errors.py`, `backend/tests/test_loader.py`
**Commit:** 2be5362 — `fix(01): WR-01 map all producible Pydantic error types to PT-BR`
**Status:** fixed
**Applied fix:** Extended `_PTBR_BY_TYPE` with `model_type`, `dict_type`, `list_type`, `bool_type`, `bool_parsing` PT-BR phrases and restructured the renderer: `value_error` is handled explicitly (validator's own message passes through) and any type OUTSIDE the map now falls back to a PT-BR template (`"valor inválido para este campo (verifique o tipo e o formato do valor)"`) instead of raw English — closing the reviewer's exact leak (`contact: texto` / `experiences: ops` / `example: talvez`) AND the whole class of future unmapped types. Raw English detail still reaches `ProfileError.raw` (terminal only, D-13). Adaptation note: the review's suggested snippet conflated "unknown type" with "value_error" (both `.get()` to None); the explicit `_ptbr_message()` helper implements the stated intent without that conflation. The module docstring's false "exactly five producible" claim was corrected. New tests: model/dict/list-type end-to-end through `Profile.model_validate` + `render_errors_ptbr`, bool_parsing, and a synthetic unmapped-type unit test.

### WR-02: `value_error` passthrough carries Pydantic's English "Value error, " prefix into the UI

**Files modified:** `backend/app/profile/errors.py`, `backend/tests/test_loader.py`
**Commit:** cf89646 — `fix(01): WR-02 strip English 'Value error, ' prefix from passthrough messages`
**Status:** fixed
**Applied fix:** `_ptbr_message` now returns `error["msg"].removeprefix("Value error, ")` for `value_error`, so the base-language mixin's PT-BR prose renders verbatim without the English prefix. New test `test_value_error_renders_without_english_prefix` drives the real loader through the `missing_ptbr_profile_path` fixture and asserts both `"Value error, " not in msg` and that the validator's own PT-BR text survives.

### WR-03: Date fields accept arbitrary strings; date normalization is inconsistent between quoted and unquoted YAML

**Files modified:** `backend/app/profile/models.py`, `backend/tests/test_schema.py`
**Commit:** ef1012e — `fix(01): WR-03 enforce AAAA-MM date format loudly on date fields`
**Status:** fixed: requires human verification (new validation condition — logic-bearing)
**Applied fix:** `_date_to_str` (the existing `mode="before"` validator on `Experience.start_date/end_date` and `EducationEntry.start_date/end_date`) now raises `ValueError("data esperada no formato 'AAAA-MM' (ex.: 2022-03), encontrado '{v}'")` for any string not matching `[0-9]{4}-(0[1-9]|1[0-2])` (fullmatch — month range enforced, `[0-9]` not `\d` to bar Unicode digits). Surfaces as `value_error` on the field's loc (PT-BR, prefix-stripped by WR-02). Unquoted YAML dates still truncate `isoformat()[:7]`; explicit `null` still passes through (regression-tested). Verified decision points: shipped `content/profile.md` uses quoted `"YYYY-MM"` everywhere, so the strict rule validates it (loaded in `test_example_profile_validates`); quoted full dates (`"2022-03-15"`) are now rejected rather than silently stored in a second format — this is the review's chosen resolution of the mixed-format problem (reject-and-inform over silent normalization, matching the project's fail-fast philosophy).

### WR-04: Completeness grid shows skill-group count as "itens" and never renders `habilidades_itens_qtde`

**Files modified:** `frontend/src/components/CompletenessGrid.tsx`, `frontend/src/constants/ui.ts`
**Commit:** eb70ea7 — `fix(01): WR-04 render skill item count alongside group count in completude grid`
**Status:** fixed: requires human verification (UI rendering — verified by tsc/vite build only; the repo has no frontend test runner)
**Applied fix:** The `habilidades` case now renders `"{grupos} · {itens}"` (`"4 grupos · 15 itens"` for the shipped example), mirroring the experiencias detail line, so `habilidades_itens_qtde` is finally consumed. Added `grupos`/`gruposPlural` to `COMPLETENESS_UNIT`. No new backend test needed: the API half of the contract was already pinned (`test_api.py` asserts `habilidades_itens_qtde == 15`); the frontend half is gated by `npm run build` (tsc is the project's Pydantic↔TS drift gate per client.ts header).

## Skipped Issues

None — all 4 in-scope findings were fixed.

Out of scope (fix_scope=critical_warning), not attempted: IN-01 (empty-string localized values count as preenchida), IN-02 (dangling `–` separator when education start_date absent), IN-03 (OSError/PermissionError bypasses ProfileError → HTTP 500), IN-04 (SPA mount decided once at import), IN-05 (backend suite hard-fails without frontend/dist).

---

_Fixed: 2026-09-26T01:58:39Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
