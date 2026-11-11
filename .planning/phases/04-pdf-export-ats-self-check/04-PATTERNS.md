# Phase 4: PDF Export + ATS Self-Check - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 15 (9 new, 6 modified)
**Analogs found:** 13 / 15 (2 new files have no in-codebase analog — RESEARCH.md probe code is the source)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/export/__init__.py` | package init | — | `backend/app/resume/__init__.py` | exact |
| `backend/app/export/render.py` | utility (pure HTML builder) | transform | no code analog — structure mirrors `frontend/src/components/ResumeResult.tsx` D-05 montage | none (structural ref) |
| `backend/app/export/pdf.py` | service (engine seam) | transform (HTML→bytes) | no analog — RESEARCH.md verified probe | none |
| `backend/app/export/gate.py` | service (parse-back checks, pure fns) | batch (ordered checks) | `backend/app/resume/coverage.py` | role-match (fold mechanics exact) |
| `backend/app/export/selfcheck.py` | service (payload builder, pure fns) | transform | `backend/app/resume/coverage.py` (`classify_coverage`/`summarize_coverage`) | exact (reuses it) |
| `backend/app/routes/export.py` | route/controller | request-response | `backend/app/routes/resume.py` | exact |
| `backend/app/routes/export.py` (`ExportError`) | error type | — | `backend/app/llm/errors.py` (`LLMError` shape) | exact |
| `backend/app/main.py` (modify) | app entrypoint/config | — | itself (router-before-mount block) | exact |
| `backend/pyproject.toml` (modify) | config (deps + pytest) | — | itself (existing `addopts`, deps) | exact |
| `backend/tests/test_export_gate.py` | test (unit + session fixture) | batch | `backend/tests/test_coverage.py` + `backend/tests/conftest.py` | exact |
| `backend/tests/test_export_api.py` | test (API contract, offline) | request-response | `backend/tests/test_resume_api.py` | exact |
| `frontend/src/api/client.ts` (modify) | client/DTO | request-response | itself (`gerarCurriculo` + envelope types) | exact |
| `frontend/src/components/ExportZone.tsx` | component | request-response | error section in `frontend/src/pages/CurriculoHome.tsx` + `frontend/src/components/ErrorPanel.tsx` | role-match |
| `frontend/src/components/SelfCheckPanel.tsx` | component (render payload) | — | `frontend/src/components/KeywordsPanel.tsx` | exact |
| `frontend/src/pages/CurriculoHome.tsx` (modify) | page/controller | — | itself (mutation + result zones) | exact |
| `frontend/src/constants/ui.ts` (modify) | config (PT-BR strings) | — | itself (`CURRICULO_*` block conventions) | exact |

Plus one docs touch: D-04 setup step (`uv run playwright install chromium`) documented in root `README.md` (no `backend/README.md` exists — verified).

## Pattern Assignments

### `backend/app/routes/export.py` (route, request-response)

**Analog:** `backend/app/routes/resume.py` — copy its entire structure: module docstring citing decision IDs, sync `def`, strict request model, 200-envelope.

**Module docstring + imports pattern** (lines 1-34):
```python
"""POST /api/resume/lint + POST /api/resume/gerar — 200-envelope contract.

Both handlers are PLAIN `def` (NEVER async def): run_stage blocks on the
synchronous OpenAI SDK client ... Starlette dispatches sync endpoints to its
threadpool so the event loop stays responsive ...

House envelope rule (same as routes/profile.py): EVERY failure ... answers
HTTP 200 with {"status": "erro", "erros": [PT-BR lines]}; the raw exception
detail goes to the uvicorn terminal log ONLY — never an HTTP 500 ...
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

logger = logging.getLogger(__name__)

router = APIRouter()
```
For Phase 4: same skeleton; `sync_playwright` REQUIRES the plain `def` (async def route wrapping sync Playwright raises `RuntimeError` — RESEARCH Pitfall 1). New imports: `base64`, `datetime.date`, `app.export.render/pdf/gate/selfcheck`.

**Strict request model pattern** (lines 42-53) — `ExportarRequest` follows this, composing existing models instead of new fields:
```python
class LintRequest(BaseModel):
    """Strict body for POST /api/resume/lint."""

    model_config = ConfigDict(extra="forbid")

    jd_text: str = Field(min_length=JD_MIN_LENGTH, max_length=JD_MAX_LENGTH)


class GerarRequest(LintRequest):
    """Strict body for POST /api/resume/gerar — language defaults to pt-BR."""

    language: Literal["pt-BR", "en"] = "pt-BR"
```
Reuse `app.profile.models.Profile`, `app.llm.schemas.ExperienciaGerada`, `app.llm.schemas.Keyword` directly in the request model (D-10: the displayed state travels verbatim).

**Core route pattern — envelope + error split** (lines 56-74):
```python
@router.post("/api/resume/lint")
def lint_vaga(payload: LintRequest) -> dict:
    """Pre-generate keyword extraction + JD-tied lint (SC5) — sync def."""
    try:
        return {"status": "ok", **run_lint_only(payload.jd_text)}
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na análise da vaga:\n%s", exc.raw)  # raw → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
```
For `/api/resume/exportar`: gate failure is NOT an exception — return `{"status": "erro", "erros": gate.erros_ptbr}` after `logger.error(...gate.raw)` (D-08). Success envelope: `{"status":"ok","filename": f"curriculo-{payload.idioma}-{date.today().isoformat()}.pdf", "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"), "selfcheck": {...}}` (D-11/D-13, RESEARCH Pattern 4).

---

### `ExportError` (error type, in `backend/app/export/`)

**Analog:** `backend/app/llm/errors.py` lines 43-50 — exact `(message_ptbr, raw)` constructor shape:
```python
class LLMError(Exception):
    """LLM call failure (missing key, API error, exhausted retries) — D-03:
    never silently falls back to another model; always loud."""

    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw  # terminal-only detail (D-13/D-14)
```
Same shape covers: Chromium missing (Pitfall 4 → PT-BR line "O navegador de renderização não está instalado. Execute `uv run playwright install chromium` e tente novamente."), render failure, extraction failure.

---

### `backend/app/export/gate.py` (service, batch checks)

**Analog:** `backend/app/resume/coverage.py` — pure deterministic check functions, module docstring citing decision IDs, `_fold` reused verbatim.

**Fold + pattern mechanics** (lines 33-41) — import and reuse, do NOT re-implement:
```python
def _fold(text: str) -> str:
    """Casefold + NFKD accent-fold (drop combining marks) — both sides, once."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _term_pattern(term: str) -> re.Pattern:
    """Lookaround-bounded pattern over the FOLDED term — never \\b (Pitfall 1)."""
    return re.compile(r"(?<!\w)" + re.escape(_fold(term)) + r"(?!\w)", re.IGNORECASE)
```
Gate usage: `_fold` for order/heading comparison space (CSS `text-transform: uppercase` is baked into extracted text — folding recovers the match); `flat.casefold()` (accent-SENSITIVE) for the integrity check; mojibake sentinels: no U+FFFD, no "Ã"/"â€" sequences (RESEARCH Pattern 3, check 4).

**Pure-check-function style** (lines 58-79) — build gate result entries as plain dicts like `classify_coverage` does:
```python
def classify_coverage(
    keywords: list[Keyword], generated_text: str, language: str
) -> list[dict]:
    cobertura: list[dict] = []
    for keyword in keywords:
        termo = keyword_in_text(keyword, generated_text, language)
        cobertura.append(
            {
                "canonical": keyword.canonical,
                "category": keyword.category,
                "termo": termo,
                "status": "coberto" if termo is not None else "ausente",
            }
        )
    return cobertura
```
Gate API per RESEARCH: `parse_back_check(pdf_bytes, expected) -> GateResult` with `ok`, `erros_ptbr` (PT-BR lines naming the failed check), `raw` (extracted text + detail, terminal-only). Normalize whitespace ONCE (`re.sub(r"\s+", " ", text)`) before all position math (Pitfall 5).

---

### `backend/app/export/selfcheck.py` (service, transform)

**Analog:** `backend/app/resume/coverage.py` — direct dependency, same output shape.

**Matcher reuse** (lines 44-55) — `keyword_in_text` is the locked D-15 reuse; selfcheck calls it per keyword over the PDF text:
```python
def keyword_in_text(keyword: Keyword, text: str, language: str) -> str | None:
    """Return the FIRST matching candidate term string (D-02 auditability) or None.

    Candidate order (D-11 Fase 2): the run-language rendering (kw.pt for a
    pt-BR run, kw.en otherwise), then canonical, then aliases.
    """
    folded_text = _fold(text)
    primary = keyword.pt if language == "pt-BR" else keyword.en
    for term in [primary, keyword.canonical, *keyword.aliases]:
        if term and _term_pattern(term).search(folded_text):
            return term
    return None
```
`selfcheck.sobrevivencia` entries mirror `classify_coverage`'s dict shape exactly (`canonical/category/termo/status`) — RESEARCH Pattern 4 confirms the frontend consumes "same shape as CoberturaItemDTO". `ordem` rows: `{"id": <PREVIEW_SECTIONS key or "contato">, "ok": bool}` — ids come from the heading map shared with `render.py` (single source of truth).

---

### `backend/app/export/render.py` (utility, transform) — NO code analog

No HTML-building code exists yet. Sources for the planner:

1. **Section ORDER to mirror (D-05):** `frontend/src/components/ResumeResult.tsx` lines 181-255 render exactly: resumo (gerado) → experiencias (gerado) → formacao (perfil) → habilidades (gerado) → certificacoes/idiomas/projetos (perfil, each hidden when empty). The template reproduces this montage; contact header pattern at lines 141-148:
```typescript
const contactLine = [
  perfil.contact.email,
  perfil.contact.location,
  perfil.contact.phone,
  perfil.contact.linkedin,
]
  .filter(Boolean)
  .join(PREVIEW_CONTACT_SEPARATOR)
```
and date display convention (line 41-43):
```typescript
function dateRange(start: string, end: string | null | undefined): string {
  return end ? `${start} – ${end}` : `${start} – ${PREVIEW_PRESENT}`
}
```
2. **Pure-function discipline:** `coverage.py` style — module docstring with decision IDs, no I/O, plain functions. Escape EVERY interpolation with `html.escape(s, quote=True)` (server-side analogue of the JSX-text-children convention, V5.3).
3. **Heading map** is THE shared source of truth (render + gate order check + selfcheck ordem rows), per-language pt/en maps — RESEARCH template skeleton (`HEADINGS = {"pt-BR": {...}, "en": {...}}`), extending `CURRICULO_GENERATED_SECTIONS` (constants/ui.ts lines 135-138) with the 4 passthrough headings localized (A2).
4. **CSS:** block layout only, `@page { size: A4; margin: 1.6cm; }`, both `break-inside: avoid` AND `page-break-inside: avoid`, UTF-8 `<meta charset>` (RESEARCH Pattern 1 — keeps WeasyPrint viable per D-02).

---

### `backend/app/export/pdf.py` (service, transform) — NO code analog

No browser/Playwright code exists. Use the RESEARCH-verified probe verbatim (RESEARCH.md Code Examples, probe run 2026-09-27 on this machine):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    try:
        page = browser.new_page()
        page.set_content(HTML, wait_until="load")   # UTF-8 <meta charset> in template
        pdf_bytes = page.pdf(format="A4", print_background=True,
                             prefer_css_page_size=True, tagged=True)
    finally:
        browser.close()
```
Hard rules: this file is THE ONLY playwright import (engine seam, D-02); per-request launch + close in `finally` (no module-level cached browser — anti-pattern); no `asyncio` anywhere in the export path; catch launch/lookup errors → `ExportError` with the PT-BR install hint. Pin `playwright==1.62.0` (matches cached chromium-1234).

---

### `backend/app/main.py` (modify — router registration)

**Analog:** itself, lines 14-27 — add the export router in the same block:
```python
from app.routes.profile import router as profile_router
from app.routes.resume import router as resume_router

app = FastAPI(title="Career Tailor")

# API routes FIRST — anything registered after the "/" mount is unreachable.
app.include_router(profile_router)
app.include_router(resume_router)  # before the SPA mount (Pitfall 3/5)

if FRONTEND_DIST.exists():  # Pitfall 5: mount LAST
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="spa",
    )
```
Add `from app.routes.export import router as export_router` + `app.include_router(export_router)` BEFORE the mount (RESEARCH Pitfall 6).

---

### `backend/tests/test_export_api.py` (test, request-response)

**Analog:** `backend/tests/test_resume_api.py` — copy its four test families:

1. **Stubbing seam** (lines 111-131) — monkeypatch the renderer (`app.export.pdf.html_to_pdf`) the way run_stage is stubbed:
```python
def _stub_stages(monkeypatch: pytest.MonkeyPatch, script: list | None = None) -> None:
    """Stub app.resume.pipeline.run_stage: canned model per requested stage
    (or the next scripted item — content str or exception)."""
    import app.resume.pipeline as pipeline_module

    items = list(script) if script is not None else list(_STAGE_CONTENT.values())

    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        item = items.pop(0)
        if isinstance(item, Exception):
            raise item
        ...
    monkeypatch.setattr(pipeline_module, "run_stage", fake_run_stage)
```
2. **Erro-envelope + caplog terminal-only assertion** (lines 199-219):
```python
    with caplog.at_level(logging.ERROR, logger="app.routes.resume"):
        resp = client.post(
            "/api/resume/gerar", json={"jd_text": JD_PT, "language": "pt-BR"}
        )
    assert resp.status_code == 200  # never an HTTP 500 (house envelope rule)
    body = resp.json()
    assert body["status"] == "erro"
    ...
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-DETAIL-secreto" in terminal_text
    # ...but NEVER the API envelope (T-03-02).
    assert "RAW-DETAIL-secreto" not in " ".join(body["erros"])
```
3. **422 strict-validation tests** (lines 262-276): unknown extra key → 422; unknown language literal → 422.
4. **Structural pins** (lines 284-321): `_iter_api_routes()` helper + `test_handlers_are_sync_def_never_coroutines` (`inspect.iscoroutinefunction(endpoint) is False`) + `test_resume_router_registered_before_spa_mount` — add `/api/resume/exportar` to both loops.

---

### `backend/tests/test_export_gate.py` (test, unit + integration fixture)

**Analog:** `backend/tests/test_coverage.py` (pure-function tables) + `backend/tests/conftest.py` (fixture style).

**Parametrized pure-function table** (test_coverage.py lines 42-57) — gate failure-branch tests follow this shape with synthetic extracted text (no browser):
```python
@pytest.mark.parametrize(
    ("canonical", "text", "expected_term"),
    [
        ("C++", "sei C++ e C", "C++"),
        ("C#", "programo em C# hoje", "C#"),
        (".NET", "usa .NET no trabalho", ".NET"),
        ("CI/CD", "experiência com CI/CD no dia a dia", "CI/CD"),
    ],
)
def test_special_char_keywords_match_via_lookaround(
    canonical: str, text: str, expected_term: str
) -> None:
    kw = _kw(canonical, category="ferramentas")
    assert keyword_in_text(kw, text, "en") == expected_term
```
**Session-scoped real-render fixture** — build on conftest patterns (lines 115-130); per RESEARCH fixture strategy: render ONCE via the real engine (~3s, offline, local Chromium), all gate tests consume the bytes; if Chromium is missing the fixture FAILS LOUD with the PT-BR setup hint (never skip-silent). Profile content for the fixture: reuse `conftest.minimal_profile()` shape (lines 23-52 — note the PT-BR accents: "São Paulo", "Engenheira de Software Sênior", "atual" dates) plus an EN variant. Assert LOGICAL properties only, never `pdf_bytes == fixture` (anti-pattern).

---

### `frontend/src/api/client.ts` (modify — typed client)

**Analog:** itself — add `exportarCurriculo` + envelope types mirroring the existing POST functions (lines 164-191):
```typescript
/** One-shot generate: extraction → lint → 3 sequential section stages → coverage. */
export async function gerarCurriculo(payload: {
  jd_text: string
  language: ResumeLanguage
}): Promise<GerarResponse> {
  const resp = await fetch('/api/resume/gerar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/resume/gerar falhou: ${resp.status}`)
  }
  return (await resp.json()) as GerarResponse
}
```
Envelope discriminated-union convention (lines 148-163):
```typescript
export type LintResponse =
  | { status: 'ok'; keywords: KeywordDTO[]; avisos: string[] }
  | { status: 'erro'; erros: string[] }
```
`ExportarResponse` = same union with ok branch `{ status: 'ok'; filename: string; pdf_base64: string; selfcheck: {...} }`. Request payload reuses existing DTOs (`PerfilDTO`, `SecoesDTO`, `KeywordDTO`, `ResumeLanguage`) — `tsc -b` is the drift gate (header comment, lines 1-4). Header comment must name the new normative plan, as the resume block does (lines 110-112: "Change BOTH together").

---

### `frontend/src/components/SelfCheckPanel.tsx` (component, render-only)

**Analog:** `frontend/src/components/KeywordsPanel.tsx` — copy its three conventions:

1. **Exported pure copy picker** (lines 20-29) — unit-testable by construction (no JS test runner; tsc + review):
```typescript
export function resumoCoberturaCopy(cobertos: number, total: number): string {
  const template = total === 1 ? CURRICULO_COBERTURA_SINGULAR : CURRICULO_COBERTURA_PLURAL
  return template.replace('{covered}', String(cobertos)).replace('{total}', String(total))
}
```
2. **Glyph + sr-only label — never color/glyph alone** (lines 72-90):
```tsx
<li
  key={`${i}-${item.canonical}`}
  className={
    coberto
      ? 'rounded-full border border-green-200 bg-green-50 px-2 py-1 text-xs text-green-700'
      : 'rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-500'
  }
>
  <span aria-hidden>{coberto ? '✓' : '○'}</span>{' '}
  {keywordDisplay(byCanonical.get(item.canonical), item.canonical, idioma)}
  <span className="sr-only">
    {coberto ? CURRICULO_KEYWORD_COBERTO : CURRICULO_KEYWORD_AUSENTE}
  </span>
</li>
```
3. **Section skeleton** (lines 52-56): `<section aria-labelledby="...-panel-title">` + `<h3 id=... className="text-base font-semibold text-gray-900">`; empty-state `<p>` pattern (lines 58-59).

Ordem rows render ✓/✗ per the same glyph+sr-only rule; `gate.coocorrencia/acentos` surface in a footer line (D-06 checks the ordem panel doesn't show). Survival chips reuse `CoberturaItemDTO` shape verbatim.

---

### `frontend/src/components/ExportZone.tsx` (component, request-response)

**Analog:** error section + button classes in `frontend/src/pages/CurriculoHome.tsx`; verbatim-error discipline from `frontend/src/components/ErrorPanel.tsx`.

**Mutation-triggered panel with envelope branching** (CurriculoHome.tsx lines 93-109):
```typescript
const gerar = useMutation({
  mutationFn: gerarCurriculo,
  onSuccess: (data) => {
    if (data.status === 'ok') {
      setResultado(data)
      setGerarErros(null)
    } else {
      // 200-envelope erro: backend PT-BR lines, rendered verbatim below.
      setGerarErros(data.erros)
    }
  },
  onError: () => {
    // Fetch-level failure (server down): fail-loud panel + retry, prior
    // result stays mounted. Raw detail is in the uvicorn terminal only.
    setGerarErros([])
  },
})
```
**Error lines rendered verbatim** (lines 225-242; ErrorPanel.tsx lines 14-31 — "must not parse, re-map, or translate"):
```tsx
<ul className="mt-2 list-disc pl-5 text-sm text-red-700">
  {gerarErros.map((linha, i) => (
    <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
      {linha}
    </li>
  ))}
</ul>
```
**Pinned button classes** (CurriculoHome.tsx lines 43-46 — copy, don't reinvent):
```typescript
const PRIMARY_BUTTON_CLASSES =
  'min-h-10 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
```
Blob download on ok (RESEARCH Code Examples): `Uint8Array.from(atob(data.pdf_base64), c => c.charCodeAt(0))` → `URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }))` → anchor click with `download: data.filename` → `URL.revokeObjectURL`. Filename comes from the backend (single source, D-11). Locked while `gerar.isPending` (symmetric with "Gerar novamente", UI-SPEC).

---

### `frontend/src/pages/CurriculoHome.tsx` (modify — wire export + self-check)

**Analog:** itself — the result-zone composition (lines 254-271) is exactly where the new blocks attach:
```tsx
{resultado && (
  <>
    {/* Zone 4 — assembled card ... Zone 5 stacks the coverage panel below. */}
    <ResumeResult
      perfil={perfilQuery.data.perfil}
      secoes={resultado.secoes}
      idioma={resultado.idioma}
      onRegenerar={gerarAgora}
      regenerando={gerar.isPending}
    />
    <KeywordsPanel
      keywords={resultado.keywords}
      cobertura={resultado.cobertura}
      cobertura_resumo={resultado.cobertura_resumo}
      idioma={resultado.idioma}
    />
  </>
)}
```
Add `<ExportZone>` (below ResumeResult — D-09 CTA position) + `<SelfCheckPanel>` fed by the export response's selfcheck payload (D-13/D-14, session-only state D-16). Export mutation follows the same `useMutation` pattern; the export needs `perfil` + `resultado.secoes` + `resultado.keywords` + `resultado.idioma` — all already in scope here.

---

### `frontend/src/constants/ui.ts` (modify — PT-BR strings)

**Analog:** itself — the `CURRICULO_*` block (lines 95-138). New `EXPORTAR_*` / `SELFCHECK_*` constants follow: one line per string, PT-BR, `{slot}` interpolation style like `CURRICULO_COBERTURA_SINGULAR` (lines 105-108), plus a comment block explaining the copy contract (no score, no percentage — REQUIREMENTS Out of Scope). Note existing keys the panel reuses: `PREVIEW_SECTIONS` (lines 57-65) for ordem-row ids and `CATEGORY_LABELS`/`CATEGORY_ORDER` (lines 115-126) for survival grouping.

---

### `backend/pyproject.toml` (modify) and `backend/app/export/__init__.py` (new)

- `pyproject.toml`: add `playwright==1.62.0` and `pypdf>=6.19.0` via `uv add` (behind planner's human-verify checkpoint per legitimacy audit). Existing `addopts = -m 'not llm'` stays — the gate is offline by nature.
- `__init__.py`: one-line docstring exactly like `backend/app/resume/__init__.py`:
```python
"""Resume module package (Phase 3): profile-fact serialization and the resume generation pipeline."""
```

## Shared Patterns

### 200-envelope error contract (never HTTP 500)
**Source:** `backend/app/routes/resume.py` lines 1-20 (docstring) + 56-74 (handlers)
**Apply to:** `backend/app/routes/export.py`, gate failure path (D-08)
Every failure → HTTP 200 `{"status": "erro", "erros": [PT-BR lines naming the failed check]}`; `logger.error(...raw)` terminal-only. Validation failures are the ONE exception: FastAPI 422 (malformed request = client bug).

### Sync `def` routes for blocking work
**Source:** `backend/app/routes/resume.py` lines 1-7 + `backend/tests/test_resume_api.py` lines 301-309
**Apply to:** `exportar_curriculo` (Playwright launch is ~0.9s blocking; async def + sync_playwright raises RuntimeError — RESEARCH Pitfall 1). Pinned by a structural test.

### Strict Pydantic `extra="forbid"` on every request model
**Source:** `backend/app/llm/schemas.py` lines 22-25 (`_Strict`) + `backend/app/routes/resume.py` lines 42-53
**Apply to:** `ExportarRequest` — compose existing `Profile`/`ExperienciaGerada`/`Keyword` models (all already strict, `backend/app/profile/models.py` lines 153-165).

### Error type: `message_ptbr` + `raw` split
**Source:** `backend/app/llm/errors.py` lines 43-50
**Apply to:** `ExportError` (render/launch/extraction failures); gate failures carry the same split inside `GateResult`.

### Deterministic matching: `_fold` + lookaround, never `\b`
**Source:** `backend/app/resume/coverage.py` lines 33-55
**Apply to:** `gate.py` (order/heading fold space) and `selfcheck.py` (keyword survival — locked D-15 reuse). Integrity check adds casefold-only (accent-SENSITIVE) comparison + mojibake sentinels.

### Router registration BEFORE SPA mount
**Source:** `backend/app/main.py` lines 14-27
**Apply to:** export router insertion; pinned by the `test_resume_router_registered_before_spa_mount` structural test pattern.

### Module docstrings cite decision IDs; files are small and single-purpose
**Source:** every backend file read (`resume.py`, `coverage.py`, `errors.py`, `schemas.py`, `main.py`)
**Apply to:** all new backend files — docstring names the decisions (D-01..D-16) and threats the file implements.

### Offline tests with monkeypatch seams + fail-loud fixtures
**Source:** `backend/tests/test_resume_api.py` lines 111-131 (stub seam), `backend/tests/conftest.py` lines 115-130 (fixture style)
**Apply to:** both new test files. `runs.jsonl` gets NO export lines (LLM-calls-only contract — CONTEXT integration point).

### JSX text children only; glyphs always paired with sr-only labels
**Source:** `frontend/src/components/ResumeResult.tsx` lines 127-138 (docstring), `frontend/src/components/KeywordsPanel.tsx` lines 72-90
**Apply to:** `ExportZone.tsx`, `SelfCheckPanel.tsx` (server-side analogue: `html.escape` on every template interpolation).

### Session-only (ephemeral) result state, PT-BR constants module
**Source:** `frontend/src/pages/CurriculoHome.tsx` lines 71-74 (`useState` only, D-06/D-16), `frontend/src/constants/ui.ts` (whole file)
**Apply to:** export/self-check state — React state only, no persistence, strings in `constants/ui.ts`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/export/render.py` | utility (HTML builder) | transform | No HTML/template-building code exists anywhere in the codebase. Planner builds from RESEARCH.md template skeleton + CSS, mirroring the section order of `frontend/src/components/ResumeResult.tsx` lines 181-255 and the escape-everything rule. |
| `backend/app/export/pdf.py` | service (engine seam) | transform | No browser-automation code exists. Planner uses the RESEARCH.md probe (verified on this machine 2026-09-27) verbatim as the function body: `sync_playwright` → `launch(headless=True)` → `set_content` → `page.pdf(format="A4", print_background=True, prefer_css_page_size=True, tagged=True)` → `finally: browser.close()`. |

## Metadata

**Analog search scope:** `backend/app/**`, `backend/tests/**`, `frontend/src/**` (full enumeration — 55 source files scanned by find; 14 read in full or targeted)
**Files scanned:** 55 (all listed), 14 read
**Tracked-source gate:** all 15 named analog paths verified via `git ls-files` (all tracked — no gitignored mirrors)
**Pattern extraction date:** 2026-09-27
