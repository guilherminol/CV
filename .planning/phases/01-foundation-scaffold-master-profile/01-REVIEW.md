---
phase: 01-foundation-scaffold-master-profile
reviewed: 2026-09-26T00:57:40Z
depth: standard
files_reviewed: 28
files_reviewed_list:
  - backend/app/main.py
  - backend/app/config.py
  - backend/app/profile/models.py
  - backend/app/profile/loader.py
  - backend/app/profile/errors.py
  - backend/app/profile/completeness.py
  - backend/app/routes/profile.py
  - backend/tests/test_secrets.py
  - backend/tests/test_api.py
  - backend/tests/test_schema.py
  - backend/tests/test_loader.py
  - backend/tests/conftest.py
  - frontend/src/main.tsx
  - frontend/src/App.tsx
  - frontend/src/index.css
  - frontend/src/api/client.ts
  - frontend/src/constants/ui.ts
  - frontend/src/components/PlaceholderBanner.tsx
  - frontend/src/components/ErrorPanel.tsx
  - frontend/src/components/CompletenessGrid.tsx
  - frontend/src/components/ProfilePreview.tsx
  - frontend/vite.config.ts
  - frontend/package.json
  - content/profile.md
  - README.md
  - .gitignore
  - .env.example
  - backend/pyproject.toml
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-09-26T00:57:40Z
**Depth:** standard
**Files Reviewed:** 28
**Status:** issues_found

## Summary

Reviewed all Phase 1 backend (FastAPI loader/schema/route), frontend (React/TS projection of the API), tests, and config/content files at standard depth, with empirical verification: the full backend suite was executed (35 passed) and broken-profile variants were run through the real `load_profile` path to confirm what actually reaches the UI.

The foundation is solid overall: `extra="forbid"` on every model (D-10), no-caching loader (D-15), the status-envelope route that never 500s for validation failures, verbatim rendering of backend PT-BR lines (D-13), no secrets in code, `.env` gitignored and enforced by test, and JSX-text-only rendering with no HTML injection path. However, the central Phase 1 promise — loud, fully PT-BR validation errors naming exact file and field (SC2/D-14) — has two proven leaks where English Pydantic prose reaches the in-app error panel (WR-01, WR-02), plus a date-field validation gap that lets typo'd dates pass silently (WR-03), and a completeness grid that mislabels group counts as item counts while ignoring the item-count field computed for exactly that purpose (WR-04). No Critical (security/data-loss/crash) findings.

## Warnings

### WR-01: Unmapped Pydantic error types leak English messages into the PT-BR UI

**File:** `backend/app/profile/errors.py:17-23` (map), `49-50` (fallback)
**Issue:** `_PTBR_BY_TYPE` maps only five error types and its docstring claims those are "exactly five producible" — empirically false. Running broken profiles through the real `load_profile` produced `model_type`, `list_type`, `dict_type`, and `bool_parsing` errors, all falling back to the raw English `e["msg"]` on the UI path. Verified end-to-end: a profile with `contact: texto` and `experiences: ops` renders in the API envelope / error panel:

```
• contact — Input should be a valid dictionary or instance of Contact
• experiences — Input should be a valid list
```

`example: talvez` likewise yields "Input should be a valid boolean, unable to interpret input". This contradicts SC2/D-14 ("the interface never shows English") and the README's claim about the error panel.
**Fix:** Extend the map to cover the realistically producible types and give unknown types a PT-BR template instead of raw English:

```python
_PTBR_BY_TYPE = {
    "missing": "campo obrigatório ausente",
    "extra_forbidden": "chave desconhecida — provável erro de digitação (chaves extras não são aceitas)",
    "string_type": "texto esperado, encontrado valor de outro tipo",
    "literal_error": "valor fora das opções permitidas",
    "value_error": None,
    "model_type": "estrutura esperada (bloco de dados), encontrado valor simples",
    "dict_type": "dicionário esperado, encontrado valor de outro tipo",
    "list_type": "lista esperada, encontrado valor de outro tipo",
    "bool_type": "verdadeiro/falso esperado, encontrado valor de outro tipo",
    "bool_parsing": "verdadeiro/falso esperado, encontrado texto não reconhecido",
}

...
msg = _PTBR_BY_TYPE.get(e["type"])
if msg is None:
    msg = e["msg"].removeprefix("Value error, ")  # value_error: validator's own PT-BR
else:
    msg = _PTBR_BY_TYPE[e["type"]]
```

(Keep the raw English in `ProfileError.raw` — terminal only.)

### WR-02: `value_error` passthrough carries Pydantic's English "Value error, " prefix into the UI

**File:** `backend/app/profile/errors.py:49-51`
**Issue:** For `value_error`, the mapper returns `None` and the renderer falls back to `e["msg"]`. Pydantic prefixes validator messages with `"Value error, "`, so the base-language error (D-03/D-04) renders in the UI as:

```
• estrutura do perfil — Value error, idioma base 'pt-BR' ausente no campo localizado 'summary' — adicione ao menos a chave 'pt-BR'
```

Verified through the real loader. The validator's message is PT-BR, but the English prefix leaks into the in-app panel (D-14 violation). Existing tests only assert substrings, so the prefix slips through.
**Fix:** Strip the prefix when passing the validator message through:

```python
elif e["type"] == "value_error":
    msg = e["msg"].removeprefix("Value error, ")
```

### WR-03: Date fields accept arbitrary strings; date normalization is inconsistent between quoted and unquoted YAML

**File:** `backend/app/profile/models.py:34-36`, `97-101` (Experience), `107-109` (EducationEntry)
**Issue:** `_date_to_str` truncates unquoted YAML dates to `YYYY-MM` (good), but the fields are plain `str` with no format check. Verified: `start_date: "banana"` validates cleanly; `start_date: 2022` (int) is the only rejected shape. Consequences: (a) the D-14-style date error ("data esperada, encontrado texto") can never actually fire for a typo'd string date — the exact silent-typo failure D-10 exists to prevent; (b) the same semantic date is stored differently depending on quoting — unquoted `2022-03-01` becomes `"2022-03"` while quoted `"2022-03-15"` stays `"2022-03-15"`, producing mixed formats in the store that downstream phases (sorting experiences, PDF output) will consume.
**Fix:** Enforce/normalize the month-precision format in the existing before-validator:

```python
import re
_DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

def _date_to_str(v: object) -> object:
    if isinstance(v, date):
        return v.isoformat()[:7]
    if isinstance(v, str) and not _DATE_RE.fullmatch(v):
        raise ValueError(
            f"data esperada no formato 'AAAA-MM' (ex.: 2022-03), encontrado '{v}'"
        )
    return v
```

The raised ValueError surfaces as `value_error` on the field's loc (PT-BR message names the field and offending value).

### WR-04: Completeness grid shows skill-group count as "itens" and never renders `habilidades_itens_qtde`

**File:** `frontend/src/components/CompletenessGrid.tsx:33-35` (and `backend/app/profile/completeness.py:22`)
**Issue:** The backend computes `habilidades_itens_qtde` (15 in the shipped example), it is typed into `CompletudeDTO` (`frontend/src/api/client.ts:87`) and asserted in tests — but no component ever renders it. The grid's `habilidades` case shows `habilidades_qtde` (number of groups = 4) labeled with `COMPLETENESS_UNIT.itens`, so the user sees "Habilidades — 4 itens" for a section that actually contains 15 technologies in 4 categories. Misleading information on the D-12 status home, plus a dead field transported through the whole API contract.
**Fix:** Render both numbers, mirroring the experiencias detail:

```tsx
case 'habilidades':
  return {
    present: completude.habilidades,
    detail: `${qtd(completude.habilidades_qtde, COMPLETENESS_UNIT.grupos, COMPLETENESS_UNIT.gruposPlural)} · ${qtd(completude.habilidades_itens_qtde, COMPLETENESS_UNIT.itens, COMPLETENESS_UNIT.itensPlural)}`,
  }
```

(add `grupos: 'grupo'` / `gruposPlural: 'grupos'` to `COMPLETENESS_UNIT` in `frontend/src/constants/ui.ts:44-51`).

## Info

### IN-01: Localized and string values accept empty strings, so blank content counts as "preenchida"

**File:** `backend/app/profile/models.py:25` (`LocalizedText = dict[Language, str]`), `77` (`email: str`)
**Issue:** `summary: {pt-BR: ""}` validates (no `min_length` on dict values); the preview then renders an empty summary while `compute_completude` reports `resumo: true` ("preenchida"). Same for an empty `email`. Consistent loud validation would reject empty required text.
**Fix:** Constrain localized values to non-empty: `LocalizedText = dict[Language, Annotated[str, StringConstraints(min_length=1)]]` (and consider the same for `email`/`name`), letting Pydantic produce a `string_too_short` error to map in `errors.py`.

### IN-02: Education entry with `end_date` but no `start_date` renders a dangling separator

**File:** `frontend/src/components/ProfilePreview.tsx:121-123`
**Issue:** `dateRange(ed.start_date ?? '', ed.end_date)` with `start_date` absent renders `" – 2016-12"` (leading separator and space). The schema makes `start_date` optional for education, so this state is reachable.
**Fix:** Build the range from whichever side exists:

```tsx
const range = [ed.start_date, ed.end_date ?? PREVIEW_PRESENT].filter(Boolean).join(` – `)
```

### IN-03: OS-level file errors bypass `ProfileError`, producing an HTTP 500 and breaking the route's "never 500" contract

**File:** `backend/app/profile/loader.py:37-47`, `backend/app/routes/profile.py:19-25`
**Issue:** The loader converts `FileNotFoundError`/`yaml.YAMLError`/`UnicodeDecodeError` but not `PermissionError` or `IsADirectoryError` (both `OSError`). If `content/profile.md` is locked/opened exclusively or replaced by a directory, `load_profile` raises unhandled and the route returns 500, contradicting its docstring "never HTTP 500". The UI degrades to the fetch-failure branch, but the promised PT-BR error panel naming the file never appears.
**Fix:** Add `except OSError as exc:` alongside the existing handlers, e.g. `raise ProfileError(f"Erro no perfil: {path} — não foi possível ler o arquivo", f"{type(exc).__name__}: {exc}")`.

### IN-04: SPA mount decided once at import time — starting uvicorn before the first build leaves `/` a silent 404

**File:** `backend/app/main.py:20-25`
**Issue:** `if FRONTEND_DIST.exists()` is evaluated once at import. If uvicorn starts before the first `npm run build`, `/` 404s with no hint until the server is restarted after the build. The dev-without-dist guard is reasonable, but the failure is invisible.
**Fix:** Log a warning when the mount is skipped (`logging.warning("frontend/dist ausente — rode 'cd frontend && npm run build'; reinicie o servidor após o build")`), or mount unconditionally with `StaticFiles(directory=..., check=False, html=True)` so a later build is picked up without restart.

### IN-05: Backend test suite hard-fails without a frontend build

**File:** `backend/tests/test_api.py:97-101`
**Issue:** `test_get_serves_spa_index_html` raises AssertionError when `frontend/dist` is absent — and since `dist/` is gitignored, a fresh clone running `uv run pytest` before `npm run build` sees an unrelated-looking backend failure (the message does explain, and README documents the order). This couples the backend gate to a frontend artifact.
**Fix:** Acceptable as documented behavior; if lower friction is wanted, `pytest.skip("frontend/dist ausente — npm run build")` instead of a hard failure, keeping the strict check in the phase smoke checklist.

---

_Positive notes (no action required): secret hygiene is verified and tested (`backend/tests/test_secrets.py`); no injection surface (profile strings render as JSX text only, no `dangerouslySetInnerHTML`); no CORS/proxy misconfiguration (`vite.config.ts` pins 127.0.0.1 on both sides, Pitfall 4); loader re-reads per request (D-15) and the `PROFILE_PATH` monkeypatch target works because the default resolves at call time._

_Reviewed: 2026-09-26T00:57:40Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
