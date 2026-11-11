# Phase 7: Application Tracker — Pipeline & Follow-up - Pattern Map

**Mapped:** 2026-11-10
**Files analyzed:** 25 (15 new, 10 modified)
**Analogs found:** 22 / 25

## Tracked-Source Gate (read first)

Phase 6's candidatura module is the newest and closest analog family, but it is
**UNTRACKED working-tree source** (`git status` = `??`, pending commit — NOT
gitignored, verified 2026-11-10):

| Untracked analog | Tracked substitute with the SAME pattern |
|---|---|
| `backend/app/routes/candidatura.py` | `backend/app/routes/linkedin.py` (identical envelope + sync def + extra=forbid + logger.error posture, lines 91-129) |
| `backend/app/candidatura/pipeline.py` | `backend/app/profile/completeness.py` (for pure derived computation) |
| `backend/tests/test_candidatura_api.py` | `backend/tests/test_linkedin_api.py` (`_iter_api_routes` at line 446, `test_linkedin_router_registered_before_spa_mount` at line 478) |
| `frontend/src/pages/CandidaturaHome.tsx` | `frontend/src/pages/CurriculoHome.tsx` (same form→mutation→result page family) |

PATTERNS.md cites the untracked Phase 6 files (they ARE the closest analogs) with
line numbers, but every such section names the tracked substitute. The executor
should ensure the Phase 6 files are committed (or work from the tracked
substitutes) before building on them. No gitignored mirror paths are cited anywhere.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/tracker/__init__.py` | package marker | — | any `backend/app/*/__init__.py` (e.g. `backend/app/linkedin/__init__.py`, tracked) | exact (trivial) |
| `backend/app/tracker/db.py` | model (persistence) | CRUD | — NO analog (first DB) | none — use RESEARCH Patterns 1-3 |
| `backend/app/tracker/models.py` | model (DTOs) | request-response | `backend/app/linkedin/models.py` | exact |
| `backend/app/tracker/service.py` | service | CRUD + transform | `backend/app/profile/completeness.py` (derived counters) + `backend/app/candidatura/pipeline.py` (service-layer seams) | role-match |
| `backend/app/routes/tracker.py` | controller (route) | request-response | `backend/app/routes/candidatura.py` (tracked sub: `routes/linkedin.py`) | exact |
| `backend/tests/test_tracker_db.py` | test | CRUD | — no direct analog (style: `tests/test_candidatura_api.py` / `tests/test_linkedin_api.py`) | partial |
| `backend/tests/test_tracker_service.py` | test | transform | `backend/app/profile/completeness.py` (pure-function vectors) + test style above | partial |
| `backend/tests/test_tracker_api.py` | test | request-response | `backend/tests/test_candidatura_api.py` (tracked sub: `tests/test_linkedin_api.py`) | exact |
| `backend/app/config.py` (modify) | config | — | self (`config.py` env-overridable + gitignored-dir precedents) | exact |
| `backend/app/main.py` (modify) | controller (app) | — | self (router-registration order) | exact |
| `.gitignore` (modify) | config | — | self (`logs/` entry) | exact |
| `frontend/src/pages/TrackerHome.tsx` | component (page) | request-response | `frontend/src/pages/CandidaturaHome.tsx` (tracked sub: `CurriculoHome.tsx`) + `App.tsx` PerfilHome query | exact |
| `frontend/src/components/tracker/KanbanBoard.tsx` | component | event-driven (DnD) | — NO analog (first DnD) | none — use RESEARCH Pattern 5 |
| `frontend/src/components/tracker/CandidaturaCard.tsx` | component | event-driven | `ResumeResult.tsx` (JSX-text-only posture) | partial |
| `frontend/src/components/tracker/CandidaturaForm.tsx` | component (form) | request-response | `frontend/src/pages/CandidaturaHome.tsx` form block | exact |
| `frontend/src/components/tracker/EstagioManager.tsx` | component (form/list) | CRUD | `frontend/src/pages/CandidaturaHome.tsx` form block | role-match |
| `frontend/src/components/tracker/EventosPanel.tsx` | component (list) | request-response | `frontend/src/components/CompletenessGrid.tsx` (DTO projection) | role-match |
| `frontend/src/components/tracker/ContadoresGrid.tsx` | component (grid) | request-response | `frontend/src/components/CompletenessGrid.tsx` | exact |
| `frontend/src/api/client.ts` (modify) | service (client) | request-response | self (`responderCandidatura`, `downloadPdf`) | exact |
| `frontend/src/constants/ui.ts` (modify) | config (strings) | — | self (NAV_ITEMS, pinned classes, sr-only marks) | exact |
| `frontend/src/App.tsx` (modify) | controller (shell) | — | self (view switch + isPending query) | exact |
| `frontend/src/pages/CurriculoHome.tsx` (modify) | component (page) | — | self (mutation state threading) | exact |
| `frontend/src/components/ResumeResult.tsx` (modify) | component | — | self (props interface) | exact |
| `frontend/src/pages/CandidaturaHome.tsx` (modify) | component (page) | — | self | exact |
| `frontend/package.json` (modify via npm install @dnd-kit/*) | config | — | RESEARCH Standard Stack (the D-14 single exception) | — |

## Pattern Assignments

### `backend/app/routes/tracker.py` (controller, request-response)

**Analog:** `backend/app/routes/candidatura.py` (UNTRACKED — tracked substitute: `backend/app/routes/linkedin.py` lines 91-129, identical posture)

**Strict request DTO** (candidatura.py lines 43-50):
```python
class CandidaturaRespostaRequest(BaseModel):
    """Strict body for POST /api/candidatura/responder."""

    model_config = ConfigDict(extra="forbid")

    pergunta: str = Field(min_length=PERGUNTA_MIN_LENGTH, max_length=PERGUNTA_MAX_LENGTH)
    vaga_texto: str | None = Field(default=None, max_length=VAGA_MAX_LENGTH)
    language: Literal["pt-BR", "en"] = "pt-BR"
```
Copy for every tracker body: `extra="forbid"` + `Field` bounds mirroring D-06
fields; `modalidade` as `Literal['remoto','hibrido','presencial']`. Bounds
constants live at module top (lines 38-40: `PERGUNTA_MAX_LENGTH = 2000` etc.).

**Envelope pattern — sync def, PT-BR erros, raw detail terminal-only** (candidatura.py lines 53-66):
```python
@router.post("/api/candidatura/responder")
def responder_candidatura(payload: CandidaturaRespostaRequest) -> dict:
    try:
        result = run_candidatura_resposta(...)
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na resposta de candidatura:\n%s", exc.raw)  # raw → terminal
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {"status": "ok", **result}
```
Tracker adaptation: NOT-FOUND ids also return the 200 erro envelope (house
style — never a bare 404); validation failures stay FastAPI 422s. Plain `def`,
NEVER `async def` (house rule, docstring lines 3-6: sync endpoints dispatch to
the Starlette threadpool). Module header carries `logger = logging.getLogger(__name__)`
and `router = APIRouter()` (lines 34-36).

---

### `backend/app/tracker/models.py` (model, request-response)

**Analog:** `backend/app/linkedin/models.py` (TRACKED, 33 lines) — the DTO-only module precedent: one definition, imported by BOTH the route (request model) and the service, so the wire shape can never drift (docstring lines 7-9).

**DTO module pattern** (linkedin/models.py lines 20-33):
```python
from pydantic import BaseModel, ConfigDict, Field


class LinkedinSecoes(BaseModel):
    """The four LinkedIn sections, verbatim from the displayed state."""

    model_config = ConfigDict(extra="forbid")

    headline: str = Field(min_length=1)
    sobre: str = Field(min_length=1)
    experiencias: list[ExperienciaLinkedin]
    habilidades: list[str]
```

---

### `backend/app/tracker/service.py` (service, CRUD + transform)

**Analog (derived counters):** `backend/app/profile/completeness.py` (TRACKED, lines 11-29) — the D-07 "mechanical honesty" precedent: pure function, PT-BR-keyed dict, computed fresh per request, no caching:
```python
def compute_completude(profile: Profile) -> dict:
    """PT-BR-keyed map of section presence and counts for GET /api/profile."""
    return {
        "resumo": bool(profile.summary),
        "experiencias": bool(profile.experiences),
        "experiencias_qtde": len(profile.experiences),
        ...
    }
```
Tracker's `contadores` (enviados/entrevistas/ativas) and `dias_para_prazo` /
`sugerir_followup` are this same kind of pure projection — computed from the
events rows, never stored, with `hoje` as an injectable parameter (RESEARCH
Pattern 6) so pytest pins boundary vectors.

**Analog (service-layer seams):** `backend/app/candidatura/pipeline.py` (UNTRACKED, lines 52-59) — keyword-only injection params keep tests offline and deterministic:
```python
def run_candidatura_resposta(
    pergunta: str,
    language: str,
    vaga_texto: str | None = None,
    *,
    runs_log: Path | None = None,
    client: object | None = None,
) -> dict:
```
Tracker adaptation: `hoje: date | None = None` (default `date.today()`) and
`conn: sqlite3.Connection` as the injected seams. Also copy the all-or-nothing
exception discipline (docstring lines 12-14): the service raises untouched; the
ROUTE owns the erro envelope.

---

### `backend/app/tracker/db.py` (model/persistence, CRUD) — NO ANALOG

**Reason:** the project's first SQLite file. There is no connection factory,
no migration runner, no FK usage anywhere in the codebase.
**Source instead:** RESEARCH.md Patterns 1-4 (connection-per-request `yield`
dependency; `PRAGMA user_version` migrations; `TRACKER_DB` path). The only
in-repo seeds are path/config precedents below.

---

### `backend/app/config.py` (modify — config)

**Analog: self.** Add the tracker block after the Phase 6 block (lines 39-57
show the per-phase section-comment convention: `# --- Phase 6: LinkedIn ---`).

**Env-overridable constant precedent** (config.py lines 32-34):
```python
# Model slug is config-only (D-01/D-02): swapping models must never need a code
# change. Env-overridable so the fixture harness (02-04) can pin a test model.
LLM_MODEL = os.environ.get("LLM_MODEL", "anthropic/claude-sonnet-4.5")
```
**Path + gitignored-dir precedent** (config.py lines 13, 28-30):
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
...
# Run logs: JSONL metadata written by the run-log writer (02-02). Gitignored.
LOGS_DIR = REPO_ROOT / "logs"
RUNS_LOG = LOGS_DIR / "runs.jsonl"
```
Tracker block per RESEARCH Pattern 3:
```python
TRACKER_DB = Path(os.environ.get("TRACKER_DB", str(REPO_ROOT / "data" / "tracker.db")))
TRACKER_DB.parent.mkdir(parents=True, exist_ok=True)
TRACKER_FOLLOWUP_SUGGEST_DAYS = int(os.environ.get("TRACKER_FOLLOWUP_SUGGEST_DAYS", "7"))
```

### `.gitignore` (modify)

**Analog: self** (lines 13-14) — add a `# Tracker DB (D-02)` comment + `data/` entry mirroring the `logs/` entry.

### `backend/app/main.py` (modify — router registration)

**Analog: self** (lines 10-24) — verbatim order discipline:
```python
from app.routes.candidatura import router as candidatura_router
...
# API routes FIRST — anything registered after the "/" mount is unreachable.
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(linkedin_router)  # before the SPA mount (research Pitfall 8)
app.include_router(candidatura_router)  # before the SPA mount (Pitfall 5)
app.include_router(export_router)  # before the SPA mount (Pitfall 3/5/6)
```
Add `from app.routes.tracker import router as tracker_router` + `app.include_router(tracker_router)  # before the SPA mount (Pitfall 5)` with the other include_router calls, before the `FRONTEND_DIST.exists()` mount (line 28).

---

### `backend/tests/test_tracker_api.py` (test, request-response)

**Analog:** `backend/tests/test_candidatura_api.py` (UNTRACKED — tracked substitute: `backend/tests/test_linkedin_api.py`, `_iter_api_routes` line 446 + `test_linkedin_router_registered_before_spa_mount` line 478)

**Route-order test pattern** (test_candidatura_api.py lines 75-99):
```python
def _iter_api_routes():
    """(path, endpoint_or_None, position) in registration order — handles the
    FastAPI >= 0.141 nested-_IncludedRouter layout (test_linkedin_api precedent)."""
    for position, entry in enumerate(app.routes):
        if isinstance(entry, APIRoute):
            yield entry.path, entry.endpoint, position
        elif hasattr(entry, "original_router"):
            for sub in entry.original_router.routes:
                if isinstance(sub, APIRoute):
                    yield sub.path, sub.endpoint, position
        elif type(entry).__name__ == "Mount":
            yield entry.path, None, position
...
def test_router_registered_before_spa_mount() -> None:
    routes = list(_iter_api_routes())
    paths = [path for path, _, _ in routes]
    assert "/api/candidatura/responder" in paths
    pos_rota = next(pos for path, _, pos in routes if path == "/api/candidatura/responder")
    pos_mount = next(pos for path, endpoint, pos in routes if endpoint is None)
    assert pos_rota < pos_mount
```

**Sync-handler pin** (lines 102-110):
```python
def test_handler_is_sync() -> None:
    endpoints = [endpoint for path, endpoint, _ in _iter_api_routes() if path == "/api/candidatura/responder"]
    assert endpoints, "rota não registrada"
    for endpoint in endpoints:
        assert not inspect.iscoroutinefunction(endpoint)
```

**Erro-envelope + caplog raw-only pin** (lines 145-155):
```python
    with caplog.at_level(logging.ERROR):
        resp = client.post("/api/candidatura/responder", json={"pergunta": PERGUNTA})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"] == ["Falha na chamada ao modelo"]
    assert "raw: boom" in caplog.text  # raw detail → terminal ONLY
```

**422 vector style** (lines 179-202): short/oversized/unknown-key/unknown-Literal
cases as separate `test_422_*` functions.

**Test isolation seam** (lines 58-72, `perfil_valido` fixture): monkeypatch the
module-level path constant to `tmp_path`. Tracker version: point `TRACKER_DB`
at `tmp_path` (monkeypatch env var BEFORE importing app.main, or monkeypatch
`app.tracker.db.TRACKER_DB`) — never the real `data/` (RESEARCH Wave 0 gap).

### `backend/tests/test_tracker_db.py` / `test_tracker_service.py` (tests, CRUD/transform)

**No direct analog** (first DB; first deterministic-vector service). Style and
fixtures from test_candidatura_api.py / test_linkedin_api.py; vectors per
RESEARCH Test Map (TRK-01..TRK-06 rows) — user_version idempotency, FK
stage-deletion blocking, counters from events only, follow-up pending/overdue/
execute with injected `hoje`, CSV BOM `EF BB BF`, no-DELETE-endpoint pin.

---

### `frontend/src/pages/TrackerHome.tsx` (component/page, request-response)

**Analog:** `frontend/src/pages/CandidaturaHome.tsx` (UNTRACKED — tracked substitute: `frontend/src/pages/CurriculoHome.tsx`) for the form+mutation half; `App.tsx` PerfilHome (lines 21-30) for the GET-half.

**Mutation envelope branch** (CandidaturaHome.tsx lines 53-70):
```tsx
const responder = useMutation({
  mutationFn: responderCandidatura,
  onSuccess: (data) => {
    if (data.status === 'ok') {
      setResultado(data)
      setErros(null)
    } else {
      // Backend PT-BR lines verbatim; the prior answer stays mounted.
      setErros(data.erros)
    }
  },
  onError: () => {
    // Fetch-level failure (server down) — generic PT-BR hint path.
    setErros(['Não foi possível gerar a resposta — o detalhe técnico completo aparece no terminal onde o servidor está rodando.'])
  },
})
```
Tracker deltas: mutations must ALSO call `queryClient.invalidateQueries({ queryKey: ['tracker'] })` on success (RESEARCH Pitfall 6 — the house pages don't need this because they hold ephemeral state; the tracker is the first persistent view).

**GET + isPending** (App.tsx lines 21-30):
```tsx
const { data, isPending, isError } = useQuery({
  queryKey: ['perfil'],
  queryFn: fetchProfile,
})
if (isPending) {
  return <p className="text-gray-500">{PERFIL_LOADING}</p>
}
if (isError || !data) { return <p className="text-red-600">{PERFIL_ERROR_TITLE}</p> }
if (data.status === 'erro') {
  return (<div className="space-y-4"><StatusLine ok={false} /><ErrorPanel erros={data.erros} /></div>)
}
```

**Card + submit gate** (CandidaturaHome.tsx lines 25, 83-94, 147-149):
```tsx
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
...
<form className={CARD_CLASSES} onSubmit={(event) => {
  event.preventDefault()
  if (!podeEnviar || responder.isPending) return
  setErros(null)
  responder.mutate({ ... })
}}>
...
<button type="submit" disabled={!podeEnviar || responder.isPending} className={PRIMARY_BUTTON_CLASSES}>
  {responder.isPending ? CANDIDATURA_CTA_INFLIGHT : CANDIDATURA_CTA}
</button>
```

**Client-bound mirrors server bounds** (CandidaturaHome.tsx lines 30-32):
```tsx
// Mirrors the backend request bound (routes/candidatura.py Field(max_length)).
const PERGUNTA_MAX_CHARS = 2000
const VAGA_MAX_CHARS = 20000
```
Copy for tracker field maxLengths (JD 20000 etc.); labels/strings from `constants/ui.ts` only.

---

### `frontend/src/components/tracker/ContadoresGrid.tsx` (component, request-response)

**Analog:** `frontend/src/components/CompletenessGrid.tsx` (TRACKED, lines 62-91) — pure DTO projection into a `dl` grid with neutral-vs-positive styling and labels/units imported from constants:
```tsx
export function CompletenessGrid({ completude }: { completude: CompletudeDTO }) {
  const keys = Object.keys(COMPLETENESS_LABELS) as SectionKey[]
  return (
    <section aria-labelledby="completude-title">
      <h3 id="completude-title" className="text-base font-semibold text-gray-900">
        {COMPLETENESS_TITLE}
      </h3>
      <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {keys.map((key) => {
          const { present, detail } = summarize(completude, key)
          return (
            <div key={key} className={present
              ? 'rounded-md border border-green-200 bg-green-50 px-3 py-2'
              : 'rounded-md border border-gray-200 bg-gray-50 px-3 py-2'}>
              <dt className="text-sm font-medium text-gray-800">{COMPLETENESS_LABELS[key]}</dt>
              <dd className={`mt-0.5 text-xs ${present ? 'text-green-700' : 'text-gray-400'}`}>
                {present ? (detail ?? COMPLETENESS_OK) : COMPLETENESS_EMPTY}
              </dd>
            </div>
          )
        })}
      </dl>
    </section>
  )
}
```
`EventosPanel.tsx` reuses this projection-of-DTO discipline (render only what the payload carries; loud-empty lines from constants, never a silently blank panel).

---

### `frontend/src/components/tracker/CandidaturaForm.tsx` / `EstagioManager.tsx` (components, request-response)

**Analog:** CandidaturaHome.tsx form block (excerpt above) — textarea + radio
fieldset (lines 125-145 show the sr-only radio idiom for language), maxLength
mirror, disabled gate, PRIMARY_BUTTON_CLASSES CTA. EstagioManager's delete is
blocked server-side while in use: render the returned erro lines in ErrorPanel.

### `frontend/src/components/tracker/KanbanBoard.tsx` / `CandidaturaCard.tsx` — NO ANALOG

**Reason:** first drag-and-drop surface in the app. No DnD code exists.
**Source instead:** RESEARCH Pattern 5 (`@dnd-kit/core` + `@dnd-kit/sortable`,
one `DndContext`, one `SortableContext` per column, `closestCorners`,
PointerSensor with `activationConstraint: { distance: 8 }` — Pitfall 4,
`items` array must match render order — Pitfall 10). Card content follows the
ResumeResult posture (below).

---

### `frontend/src/api/client.ts` (modify — service client)

**Analog: self.**

**Envelope function pattern** (lines 153-174):
```tsx
// --- candidatura endpoints — answers open application-form questions from the
// profile facts (vaga → perfil module). Same 200-envelope contract.

export type CandidaturaRespostaResponse =
  | { status: 'ok'; resposta: string }
  | { status: 'erro'; erros: string[] }

export async function responderCandidatura(payload: {
  pergunta: string
  vaga_texto?: string | null
  language: ResumeLanguage
}): Promise<CandidaturaRespostaResponse> {
  const resp = await fetch('/api/candidatura/responder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/candidatura/responder falhou: ${resp.status}`)
  }
  return (await resp.json()) as CandidaturaRespostaResponse
}
```
Tracker: one discriminated-union response type + one function per endpoint,
under a `// --- tracker endpoints ---` banner. DTO interfaces per RESEARCH Code
Examples (`EventoDTO`, `EstagioDTO`, `CandidaturaDTO` with server-computed
`dias_para_prazo` / `sugerir_followup`).

**Drift-gate banner** (lines 176-178) — copy the comment style for the tracker section:
```tsx
// --- resume endpoints (plan 03-04) — mirrors the NORMATIVE response contract
// in .planning/phases/03-resume-vertical-slice/03-03-PLAN.md, implemented by
// backend/app/routes/resume.py. Change BOTH together; tsc -b is the drift gate.
```

**Download anchor pattern** (lines 562-577) — for the JSON/CSV export button (D-03):
```tsx
export function downloadPdf(pdfBase64: string, filename: string): void {
  const bytes = Uint8Array.from(atob(pdfBase64), (c) => c.charCodeAt(0))
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 0)
}
```
Tracker export reuses this shape (`type: 'application/json'` /
`'text/csv'`; note the revoke-in-a-subsequent-task discipline at lines 565-567).
Transport planner pin: the house precedent delivers bytes INSIDE the 200
envelope as base64 (`routes/export.py` lines 301-306: `"pdf_base64"` +
backend-generated `"filename"` — never recomposed client-side).

---

### `frontend/src/constants/ui.ts` (modify — strings config)

**Analog: self.**

**NAV_ITEMS** (lines 5-10) — add the fifth entry (D-16), existing entries untouched:
```tsx
export const NAV_ITEMS = [
  { id: 'curriculo', label: 'Currículo', enabled: true },
  { id: 'perfil', label: 'Perfil', enabled: true },
  { id: 'linkedin', label: 'LinkedIn', enabled: true },
  { id: 'candidatura', label: 'Candidatura', enabled: true },
] as const
```
Because `as const` + `setView(item.id)` (App.tsx line 82), the App.tsx union
MUST gain `'rastreador'` or `tsc -b` fails — the drift gate working as designed.

**Pinned class strings** (lines 74-96): `PRIMARY_BUTTON_CLASSES`,
`QUIET_BUTTON_CLASSES`, `COMPACT_SECONDARY_BUTTON_CLASSES`, `HINT_INPUT_CLASSES`,
`TEXTAREA_CLASSES`, badge classes — import, never redefine (IN-04 rule). The
RASTREADOR_* strings and the deadline chip classes (amber/red per D-09,
RESEARCH "Deadline chip classes") go here as new pinned constants.

**Status never color-alone** (lines 340-341) — apply to deadline/overdue chips:
```tsx
// sr-only suffix per mark — status never conveyed by color alone (UI-SPEC).
export const COMPARACAO_MARK_SR_ONLY = ' (não consta no perfil)'
```

**Server-bound mirror precedent** (lines 355-364, WR-01): client constants
mirroring backend config bounds with a "Change BOTH together" comment — reuse
for tracker field limits if mirrored client-side.

---

### `frontend/src/App.tsx` (modify — shell controller)

**Analog: self.**

**View union** (line 69) — extend with `'rastreador'`:
```tsx
const [view, setView] = useState<'curriculo' | 'perfil' | 'linkedin' | 'candidatura'>('curriculo')
```
**Render chain** (lines 106-114):
```tsx
{view === 'perfil' ? (
  <PerfilHome />
) : view === 'linkedin' ? (
  <LinkedInHome />
) : view === 'candidatura' ? (
  <CandidaturaHome />
) : (
  <CurriculoHome />
)}
```
Add `view === 'rastreador' ? <TrackerHome prefill={trackerPrefill} ... />` before
the CurriculoHome fallback, following the per-view comment convention (lines 64-68).

**Prefill state (D-13, RESEARCH Pattern 9):** App owns
`const [trackerPrefill, setTrackerPrefill] = useState<{ jd_texto: string; language: ResumeLanguage } | null>(null)`;
`CurriculoHome` passes an optional callback prop down to `ResumeResult`; the
button sets prefill + `setView('rastreador')`; `TrackerHome`'s form consumes and
clears it once. New props on ResumeResult MUST be optional (no existing call
site breaks).

---

### `frontend/src/components/ResumeResult.tsx` (modify — component)

**Analog: self** — props interface (lines 440-494): all state comes in as props
from CurriculoHome; add ONE optional pair:
`onRegistrarCandidatura?: () => void` (+ optional boolean for disabled state).
**Security posture** (docstring lines 514-517): ALL content renders exclusively
as JSX text children — no raw-HTML injection path; keep this for JD/company/
notes text in tracker cards, and render `link_vaga` as a plain anchor with
`rel="noreferrer"`, never `dangerouslySetInnerHTML`.

### `frontend/src/pages/CurriculoHome.tsx` (modify)

**Analog: self** — mutation state threading (lines 282-326 show the
onSuccess envelope-branch + state-reset discipline; line 842 shows the
`<ResumeResult ... />` usage site where the new optional callback prop goes).

### `frontend/src/pages/CandidaturaHome.tsx` (modify)

**Analog: self** — add the association control (metadata-only event per D-08/A9)
following its own form/mutation envelope discipline (excerpt above).

---

## Shared Patterns

### S1. 200-envelope failure contract (backend routes)
**Source:** `backend/app/routes/candidatura.py` lines 53-66 (tracked sub: `backend/app/routes/linkedin.py` lines 91-129)
**Apply to:** ALL `routes/tracker.py` handlers — every failure answers HTTP 200
`{"status": "erro", "erros": [PT-BR lines]}`; raw detail ONLY to
`logger.error`; never HTTP 500, never raw detail in the envelope; validation
failures stay 422; not-found ids use the erro envelope (no bare 404).

### S2. Strict Pydantic request bodies
**Source:** `backend/app/routes/candidatura.py` lines 43-50; `backend/app/linkedin/models.py` lines 25-33
**Apply to:** every tracker request model — `model_config = ConfigDict(extra="forbid")`, `Field` bounds on all strings, `Literal` for enums (`modalidade`, event `tipo`).

### S3. Sync `def` + router-before-mount
**Source:** `backend/app/main.py` lines 19-24; candidatura.py docstring lines 3-6
**Apply to:** all tracker routes (plain `def`) + one `include_router` line BEFORE the SPA mount.

### S4. Deterministic derived fields, pure functions (D-07)
**Source:** `backend/app/profile/completeness.py` lines 11-29
**Apply to:** `tracker/service.py` — counters/deadline deltas/badges are pure
projections computed per request, PT-BR-keyed payload keys, `hoje` injectable,
cached nothing.

### S5. Typed client mirror + tsc -b drift gate
**Source:** `frontend/src/api/client.ts` lines 153-178
**Apply to:** all tracker client functions and DTO interfaces — mirrors
`routes/tracker.py`; "Change BOTH together; tsc -b is the drift gate" banner.

### S6. PT-BR strings + pinned Tailwind classes centralized
**Source:** `frontend/src/constants/ui.ts` lines 1-10 (strings-only file), 74-96 (class constants), 340-341 (sr-only)
**Apply to:** every tracker component — zero inline user-facing strings, zero
inline class-string redefinitions; status colors (amber/red, D-09) always with
an sr-only text suffix.

### S7. React Query v5 envelope discipline
**Source:** `frontend/src/App.tsx` lines 21-30 (isPending); CandidaturaHome.tsx lines 53-70 (mutation branch)
**Apply to:** TrackerHome + child components — `isPending` for initial load
(never `isLoading`, Pitfall 9), ok/erro branch in `onSuccess`, generic PT-BR
hint in `onError`, and ADD `queryClient.invalidateQueries({ queryKey: ['tracker'] })`
after every successful mutation (Pitfall 6 — first persistent view in the app).

### S8. Download via object URL + anchor
**Source:** `frontend/src/api/client.ts` lines 562-577; `backend/app/routes/export.py` lines 301-306 (base64-in-envelope + backend-generated filename)
**Apply to:** the JSON + CSV export buttons (D-03); CSV bytes encoded `utf-8-sig` server-side (RESEARCH Pattern 10).

### S9. Offline test style + tmp_path seams
**Source:** `backend/tests/test_candidatura_api.py` lines 58-110, 145-202 (tracked sub: `tests/test_linkedin_api.py` lines 446-479)
**Apply to:** all three tracker test files — monkeypatch the DB path/env to
`tmp_path`, `_iter_api_routes` order pin, sync-handler pin, 422 vectors,
caplog raw-only pin; suite stays 100% offline (tracker has no LLM at all, D-15).

### S10. No destructive paths (D-04) + JSX-text-only rendering
**Source:** ResumeResult.tsx docstring lines 514-517; RESEARCH Pitfall 5
**Apply to:** no DELETE candidaturas endpoint, no cascade stage deletion
(envelope erro instead); all user text renders as JSX text children;
`link_vaga` as plain anchor with `rel="noreferrer"`.

## No Analog Found

| File | Role | Data Flow | Reason | Use instead |
|------|------|-----------|--------|-------------|
| `backend/app/tracker/db.py` | model (persistence) | CRUD | Project's first SQLite file — no connection factory, no migrations, no FK enforcement anywhere | RESEARCH Patterns 1-3 + config.py path precedent (S4 above) |
| `backend/tests/test_tracker_db.py` | test | CRUD | Nothing tests a DB yet | Style from `tests/test_linkedin_api.py`; vectors from RESEARCH Test Map |
| `backend/tests/test_tracker_service.py` | test | transform | No pure-vector service test exists (completeness is tested via API) | Style from test_candidatura_api.py; boundary vectors from RESEARCH TRK-04/TRK-05 rows |
| `frontend/src/components/tracker/KanbanBoard.tsx` | component | event-driven | First DnD surface; `@dnd-kit` not yet installed | RESEARCH Pattern 5 verbatim |
| `frontend/src/components/tracker/CandidaturaCard.tsx` | component | event-driven | First sortable card | RESEARCH Pattern 5 (`useSortable` block) + S10 posture |

## Metadata

**Analog search scope:** `backend/app/**`, `backend/tests/**`, `frontend/src/**`, repo root configs
**Files read:** 15 in full or targeted range (routes/candidatura.py, candidatura/pipeline.py, routes/export.py, routes/linkedin.py grep, config.py, main.py, linkedin/models.py, profile/completeness.py, tests/test_candidatura_api.py, App.tsx, CandidaturaHome.tsx, CompletenessGrid.tsx, client.ts (2 ranges), ui.ts (2 ranges), ResumeResult.tsx (props range), CurriculoHome.tsx (mutation range), .gitignore)
**Files scanned:** 96 source files listed; 17 candidate analogs verified
**Tracked-source gate:** run (`git ls-files`); 4 closest analogs are untracked Phase 6 working-tree source — tracked substitutes named per section; zero gitignored mirror paths cited
**Pattern extraction date:** 2026-11-10
