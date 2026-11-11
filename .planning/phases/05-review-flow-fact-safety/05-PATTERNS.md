# Phase 5: Review Flow + Fact Safety - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 14 (7 modified, 7 new)
**Analogs found:** 14 / 14 (10 exact, 3 role-match, 1 port-source)

**Companion contract:** `.planning/phases/05-review-flow-fact-safety/05-UI-SPEC.md` (approved 7/7) pins every class string, PT-BR copy line, state-machine rule, and the three amber confirm strips. This document supplies the CODE to imitate; the UI-SPEC supplies the exact classes/copy. Where both speak, the UI-SPEC wins on classes/copy, this file wins on code mechanics.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/routes/resume.py` (mod) | route/controller | request-response | `backend/app/routes/resume.py` (self, extend) + `backend/app/routes/export.py` | exact |
| `backend/app/resume/pipeline.py` (mod) | service | batch/orchestration | `backend/app/resume/pipeline.py` (self, extend) | exact |
| `backend/app/resume/facts.py` (mod) | utility | transform | `backend/app/resume/facts.py` `compose_stage_input` (self, extend) | exact |
| `backend/tests/test_resume_regen_api.py` (new) | test | request-response | `backend/tests/test_resume_api.py` | exact |
| `backend/tests/test_resume_regen_pipeline.py` (new) | test | batch | `backend/tests/test_resume_pipeline.py` (ScriptedClient) | exact |
| `frontend/src/api/client.ts` (mod) | service (typed API client) | request-response | `frontend/src/api/client.ts` (self, extend) | exact |
| `frontend/src/pages/CurriculoHome.tsx` (mod) | controller/page | event-driven + request-response | `frontend/src/pages/CurriculoHome.tsx` gerar/exportar mutations (self, extend) | exact |
| `frontend/src/components/ResumeResult.tsx` (mod) | component | transform (render) | `frontend/src/components/ResumeResult.tsx` (self, extend) | exact |
| `frontend/src/constants/ui.ts` (mod) | config | static | `frontend/src/constants/ui.ts` (self, extend) | exact |
| `frontend/src/lib/comparison.ts` (new) | utility (pure functions) | transform | `backend/app/resume/coverage.py` + `backend/tests/test_resume_grounding.py:146-181` (port source, NOT a TS analog) | port-source |
| `frontend/src/components/ComparisonPanel.tsx` (new) | component | client-compute render | `frontend/src/components/SelfCheckPanel.tsx` | role-match |
| `frontend/src/components/SectionVersionsPanel.tsx` (new) | component | state-list render | `frontend/src/components/SelfCheckPanel.tsx` (row-list pattern) | role-match |
| `frontend/src/components/SectionEditor.tsx` (new) | component | stateful form | `frontend/src/pages/CurriculoHome.tsx` Zone 1 textarea form (lines 203-256) | role-match |
| `frontend/src/components/ConfirmStrip.tsx` (new) | component (shared strip) | static render | `frontend/src/components/ErrorPanel.tsx` (inline panel shape, amber not red) | role-match |

## Pattern Assignments

### `backend/app/routes/resume.py` — add `RegenerarRequest` + `POST /api/resume/regenerar` (route, request-response)

**Analog:** `backend/app/routes/resume.py` (handler/envelope) + `backend/app/routes/export.py` (displayed-state request model — the regen request REUSES `ExportarSecoes` for its `secoes` field).

**Route module header discipline** (routes/resume.py lines 1-20 — the docstring IS the contract; copy this style for the new endpoint's rationale: sync-def rationale, 200-envelope rule, strict-validation, hint-as-DATA):
```python
"""POST /api/resume/lint + POST /api/resume/gerar — 200-envelope contract.

Both handlers are PLAIN `def` (NEVER async def): run_stage blocks on the
synchronous OpenAI SDK client for up to ~60s per generate, and Starlette
dispatches sync endpoints to its threadpool so the event loop stays
responsive during the run (RESEARCH Pitfall 2, threat T-03-06).

House envelope rule (same as routes/profile.py): EVERY failure (ProfileError,
PromptError, LLMError) answers HTTP 200 with {"status": "erro", "erros":
[PT-BR lines]}; the raw exception detail goes to the uvicorn terminal log
ONLY — never an HTTP 500, never raw detail in the envelope (D-13/D-14,
threat T-03-02).
...
Request validation is strict (extra=forbid, threat T-03-01): jd_text bounded
80..20000 chars, language pinned by Literal defaulting to pt-BR.
"""
```

**Strict request model pattern** (routes/resume.py lines 38-53 — extend with `RegenerarRequest`; same `JD_MIN_LENGTH`/`JD_MAX_LENGTH` constants at lines 38-39):
```python
JD_MIN_LENGTH = 80
JD_MAX_LENGTH = 20000

class LintRequest(BaseModel):
    """Strict body for POST /api/resume/lint."""
    model_config = ConfigDict(extra="forbid")
    jd_text: str = Field(min_length=JD_MIN_LENGTH, max_length=JD_MAX_LENGTH)

class GerarRequest(LintRequest):
    """Strict body for POST /api/resume/gerar — language defaults to pt-BR."""
    language: Literal["pt-BR", "en"] = "pt-BR"
```

**Displayed-state shape to reuse for the regen body's `secoes`** (routes/export.py lines 71-97 — import `ExportarSecoes` from here, do NOT duplicate; note `keywords: list[Keyword] = []` precedent for optional-empty lists):
```python
RESUMO_MAX_LENGTH = 8000

class ExportarSecoes(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resumo: str = Field(min_length=1, max_length=RESUMO_MAX_LENGTH)
    experiencias: list[ExperienciaGerada] = Field(min_length=1)
    habilidades: list[str] = Field(min_length=1)

class ExportarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    perfil: Profile
    secoes: ExportarSecoes
    keywords: list[Keyword] = []  # zero-keyword runs are legitimate (loud-zero UI)
    idioma: Literal["pt-BR", "en"]
```

**Handler + envelope pattern** (routes/resume.py lines 66-74 — plain `def`, try/except the exact three exceptions, `logger.error(raw)` terminal-only, `message_ptbr.splitlines()` in the envelope; regen handler is this shape + a pipeline call):
```python
@router.post("/api/resume/gerar")
def gerar_curriculo(payload: GerarRequest) -> dict:
    """One-shot generate: extraction → lint → 3 sections → coverage — sync def."""
    try:
        result = run_resume_pipeline(payload.jd_text, payload.language)
    except (ProfileError, PromptError, LLMError) as exc:
        logger.error("Falha na geração do currículo:\n%s", exc.raw)  # raw → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return result
```

---

### `backend/app/resume/pipeline.py` — add `run_section_regen()` + `SECTION_STAGE_BY_ID` (service, batch)

**Analog:** `backend/app/resume/pipeline.py` `run_resume_pipeline` (lines 62-117).

**Stage registry + one-function-per-API-surface** (lines 36-37; the regen map extends this — module docstring lines 1-26 document the house disciplines: exceptions propagate UNTOUCHED, no caching, `runs_log`/`client` threaded to EVERY run_stage call):
```python
EXTRACTION_STAGE = "keyword-extraction"
SECTION_STAGES = ("resume-summary", "resume-experiencias", "resume-skills")  # D-01

# Phase 5 adds (section id → gateway stage), built FROM SECTION_STAGES order:
# SECTION_STAGE_BY_ID = {"resumo": "resume-summary",
#                        "experiencias": "resume-experiencias",
#                        "habilidades": "resume-skills"}
```

**The pipeline skeleton to mirror** (lines 75-117 — fresh `load_profile()` → facts → compose → `run_stage` → coverage over generated text ONLY → ok envelope; `run_section_regen` repeats this for ONE stage and merges over the SUBMITTED sections instead of building all three):
```python
profile = load_profile()  # fresh, once per invocation (D-15) — passed down
facts = serialize_profile_facts(profile, language)
stage_input = compose_stage_input(facts, jd_text)
# ... run_stage(SECTION_STAGES[i], stage_input, language, runs_log=runs_log, client=client) ...
secoes = {
    "resumo": summary.resumo,
    "experiencias": [entry.model_dump() for entry in experiencias.experiencias],
    "habilidades": list(skills.habilidades),
}
# Coverage input is the GENERATED sections' text ONLY — never profile
# passthrough content, never the other language's renderings (Pitfall 7).
generated_text = "\n".join(
    [summary.resumo]
    + [bullet for entry in experiencias.experiencias for bullet in entry.bullets]
    + list(skills.habilidades)
)
cobertura = classify_coverage(keywords, generated_text, language)
return {
    "status": "ok", "idioma": language,
    "keywords": [keyword.model_dump() for keyword in keywords],
    "avisos": avisos, "secoes": secoes,
    "cobertura": cobertura,
    "cobertura_resumo": summarize_coverage(cobertura),
}
```
Regen response shape (from the gateway's validated models): the new section dict merged into the submitted `secoes` (Pydantic-validate the submitted `ExportarSecoes` content per section stage's output model: `ResumeSummary` / `ResumeExperiencias` / `ResumeSkills` from `app.llm.schemas`), plus recomputed `cobertura` + `cobertura_resumo`. Siblings must pass through **byte-identical** (SC1 — assert in tests).

**Gateway seam being reused (DO NOT TOUCH)** — `backend/app/llm/gateway.py` lines 49-54 and 105-111: the three resume stages are already registered; the hint enters through `input_text` inside the user message; metadata-only logging (lines 113-123: ts/stage/model/language/tokens/latency/error) keeps the hint out of `runs.jsonl` (D-15) with zero gateway changes:
```python
_STAGE_SCHEMAS: dict[str, tuple[type, dict]] = {
    "keyword-extraction": (KeywordExtraction, KEYWORD_STRICT_SCHEMA),
    "resume-summary": (ResumeSummary, RESUME_SUMMARY_STRICT_SCHEMA),
    "resume-experiencias": (ResumeExperiencias, RESUME_EXPERIENCIAS_STRICT_SCHEMA),
    "resume-skills": (ResumeSkills, RESUME_SKILLS_STRICT_SCHEMA),
}
# ...
loaded = load_prompt(stage)  # fresh read every call (D-08/SC1)
messages: list[dict] = [
    {"role": "system", "content": loaded.body},
    {"role": "user", "content": f"Idioma preferido de saída: {language}\n\nTexto:\n{input_text}"},
]
```

---

### `backend/app/resume/facts.py` — add `compose_regen_stage_input()` (utility, transform)

**Analog:** `backend/app/resume/facts.py` `compose_stage_input` (lines 147-157 — the exact function the hint variant wraps):
```python
def compose_stage_input(facts: str, jd_text: str) -> str:
    """The single input blob a resume run passes as run_stage input_text: the
    profile-fact section plus the pasted job description — both DATA inside
    the gateway's existing user-message template (T-02-01), never plumbing."""
    return (
        "FATOS DO PERFIL:\n"
        f"{facts}\n"
        "\n"
        "DESCRIÇÃO DA VAGA:\n"
        f"{jd_text}"
    )
```
Hint extension (research Pattern 2): call `compose_stage_input`, then append the `DICA DE DIRECIONAMENTO` block only when `dica` is non-empty after `.strip()` — strip-empty → None at the route/pipeline boundary.

**Left-column facts source for ComparisonPanel** (facts.py lines 81-98 — the experience block shape; the client-side panel mirrors this field set from `PerfilDTO`: title/company/dates/description/impacts per entry):
```python
lines = [
    f"cargo: {resolve_loc(exp.title, language)}",
    f"empresa: {exp.company}",
]
# ...
lines.append(f"período: {period}")
lines.append(f"descrição: {resolve_loc(exp.description, language)}")
for impact in exp.impacts:
    lines.append(_impact_line(impact, language))
```

---

### `backend/tests/test_resume_regen_api.py` (test, request-response)

**Analog:** `backend/tests/test_resume_api.py` — copy the whole harness structure.

**Offline stubbing seams** (lines 103-131 — retarget `PROFILE_PATH`, stub `pipeline.run_stage` with canned models; the regen test file needs exactly this + a scriptable single-stage mode):
```python
@pytest.fixture
def _profile_file(monkeypatch: pytest.MonkeyPatch, valid_profile_path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    import app.profile.loader as loader_module
    monkeypatch.setattr(loader_module, "PROFILE_PATH", valid_profile_path)

def _stub_stages(monkeypatch: pytest.MonkeyPatch, script: list | None = None) -> None:
    """Stub app.resume.pipeline.run_stage: canned model per requested stage."""
    import app.resume.pipeline as pipeline_module
    items = list(script) if script is not None else list(_STAGE_CONTENT.values())
    def fake_run_stage(stage, input_text, language, runs_log=None, client=None):
        item = items.pop(0)
        if isinstance(item, Exception):
            raise item
        if item is None:  # canned model for the requested stage
            return _canned_model(stage)
        return _STAGE_MODELS[stage].model_validate(json.loads(item))
    monkeypatch.setattr(pipeline_module, "run_stage", fake_run_stage)
```
(Canned per-stage JSON payloads: lines 42-96 — `KEYWORDS_CONTENT`, `RESUMO_CONTENT`, `EXPERIENCIAS_CONTENT`, `SKILLS_CONTENT`, `_STAGE_MODELS`.)

**Erro-envelope test to mirror** (lines 199-219 — 200 status, no section keys, PT-BR lines only, raw detail terminal-only via `caplog`):
```python
def test_gerar_erro_envelope_on_llm_error(monkeypatch, _profile_file, caplog) -> None:
    _stub_stages(monkeypatch, script=[LLMError("Falha na geração", "RAW-DETAIL-secreto")])
    with caplog.at_level(logging.ERROR, logger="app.routes.resume"):
        resp = client.post("/api/resume/gerar", json={"jd_text": JD_PT, "language": "pt-BR"})
    assert resp.status_code == 200  # never an HTTP 500 (house envelope rule)
    body = resp.json()
    assert body["status"] == "erro"
    assert "secoes" not in body  # all-or-nothing
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "RAW-DETAIL-secreto" in terminal_text
    assert "RAW-DETAIL-secreto" not in " ".join(body["erros"])
```

**Strict-validation tests to mirror** (lines 262-276): 422 on short `jd_text`, unknown extra key (`{"hack": True}`), unknown `language` — add the regen equivalents (unknown `secao`, oversized `dica`, empty submitted sections).

**Structural pins to EXTEND** (lines 284-322 — `_iter_api_routes` + both tests below must learn `/api/resume/regenerar` in their path tuples; live in test_resume_api.py, not the new file):
```python
def test_handlers_are_sync_def_never_coroutines() -> None:
    endpoints = {path: endpoint for path, endpoint, _ in _iter_api_routes() if endpoint is not None}
    for path in ("/api/resume/lint", "/api/resume/gerar"):   # ← add "/api/resume/regenerar"
        endpoint = endpoints[path]
        assert inspect.iscoroutinefunction(endpoint) is False, path

def test_resume_router_registered_before_spa_mount() -> None:
    # same walker — add "/api/resume/regenerar" to the path list
```

---

### `backend/tests/test_resume_regen_pipeline.py` (test, batch)

**Analog:** `backend/tests/test_resume_pipeline.py` `ScriptedClient` (lines 63-82 — copied verbatim between test files in this repo; it RECORDS every `create()` kwargs, which is how hint-as-data is asserted):
```python
class ScriptedClient:
    """Fake returning a scripted SEQUENCE of contents / exceptions — one per
    attempt — recording every create() call."""
    def __init__(self, script: list):
        self._script = list(script)
        self.calls: list[dict] = []
        chat = type("Chat", (), {})()
        completions = type("Completions", (), {})()
        def create(**kwargs):
            self.calls.append(kwargs)
            item = self._script.pop(0)
            if isinstance(item, Exception):
                raise item
            return _FakeResponse(item)
        completions.create = create
        chat.completions = completions
        self.chat = chat
```
Assertions this enables (per research Pattern 5): exactly ONE stage ran (`len(client.calls) == 1`); the hint text landed in `messages[1]["content"]` (user) and NOT in `messages[0]["content"]` (system = untouched prompt body); sibling byte-identity on the merged `secoes`; coverage recomputed over the merged text.

---

### `frontend/src/api/client.ts` — add `regenerarSecao()` + `RegenerarRequest`/`RegenerarResponse` (service, request-response)

**Analog:** `frontend/src/api/client.ts` — extend in place, same section-comment + drift-gate discipline (lines 193-197 header style: "Change BOTH together; tsc -b is the drift gate").

**Existing DTOs the regen types REUSE verbatim** (lines 127-146 — do not duplicate; import):
```typescript
export interface ExperienciaGeradaDTO {
  company: string
  title: string
  bullets: string[]
}
export interface SecoesDTO {
  resumo: string
  experiencias: ExperienciaGeradaDTO[]
  habilidades: string[]
}
export interface CoberturaItemDTO {
  canonical: string
  category: KeywordCategory
  termo: string | null
  status: 'coberto' | 'ausente'
}
```

**Envelope union + POST-function pattern** (lines 152-162 for the response union shape, 227-237 for the function — the regen function is `exportarCurriculo`'s twin with different keys):
```typescript
export type GerarResponse =
  | { status: 'ok'; idioma: ResumeLanguage; keywords: KeywordDTO[]; avisos: string[]
      secoes: SecoesDTO; cobertura: CoberturaItemDTO[]
      cobertura_resumo: { cobertos: number; total: number } }
  | { status: 'erro'; erros: string[] }

export async function exportarCurriculo(payload: ExportarRequest): Promise<ExportarResponse> {
  const resp = await fetch('/api/resume/exportar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/resume/exportar falhou: ${resp.status}`)
  }
  return (await resp.json()) as ExportarResponse
}
```
Regen request interface mirrors `ExportarRequest` (lines 219-224: displayed state travels verbatim; add `secao` + optional `dica`, omit `dica` key when empty — Pitfall 5's 422 guard).

---

### `frontend/src/pages/CurriculoHome.tsx` — add `regenerar` mutation + section UI state (controller/page)

**Analog:** `frontend/src/pages/CurriculoHome.tsx` gerar/exportar mutations.

**State atoms** (lines 78-90 — `resultado` (GerarOk) is THE displayed state; the new section UI atoms (versions/dica/editor) join these; do NOT keep a shadow copy of `resultado.secoes` — RESEARCH Pattern 4 invariant 1):
```typescript
const [resultado, setResultado] = useState<GerarOk | null>(null)   // ← displayed state
const [gerarErros, setGerarErros] = useState<string[] | null>(null)
const [receiptFilename, setReceiptFilename] = useState<string | null>(null)
const [selfcheck, setSelfcheck] = useState<SelfCheckDTO | null>(null)
const [exportarErros, setExportarErros] = useState<string[] | null>(null)
```

**Mutation + export-state reset pattern** (lines 109-131 — the THREE clears are the exact rule Phase 5 extends: ANY displayed-content mutation (edit save, regen success, restore) runs the same three clears before mounting new state; the regen `onSuccess` also swaps `resultado.secoes` AND `resultado.cobertura`/`cobertura_resumo` wholesale from the response — no client-side merge, Pitfall 2):
```typescript
const gerar = useMutation({
  mutationFn: gerarCurriculo,
  onSuccess: (data) => {
    if (data.status === 'ok') {
      // Regeneration reset (UI-SPEC): the prior exported PDF no longer matches
      // the displayed resume — clear the receipt + self-check panel + export
      // errors BEFORE mounting the new result.
      setReceiptFilename(null)
      setSelfcheck(null)
      setExportarErros(null)
      setResultado(data)
      setGerarErros(null)
    } else {
      setGerarErros(data.erros)   // 200-envelope erro: PT-BR lines verbatim
    }
  },
  onError: () => { setGerarErros([]) },  // fetch-level failure, raw terminal-only
})
```

**Wiring pattern for the result card** (lines 316-341 — props down from narrowed ok payload; regen mutation follows the same capture-as-const narrowing discipline documented at lines 184-187):
```tsx
<ResumeResult
  perfil={perfilQuery.data.perfil}
  secoes={resultado.secoes}
  idioma={resultado.idioma}
  onRegenerar={gerarAgora}
  regenerando={gerar.isPending || exportar.isPending}
/>
```

**Stack-before-mutate invariant (SC4, D-14):** one helper (e.g. `empilharVersaoAtual(section)`) called at the TOP of every destructive path (edit save, regen success, restore, confirmed full regen) — pushes current displayed text + badge-origin onto that section's `versions` array before any write. Four paths, four calls — reviewable by grep (Pitfall 3).

---

### `frontend/src/components/ResumeResult.tsx` — extend: policy line, per-section action rows, badge Editado (component)

**Analog:** `frontend/src/components/ResumeResult.tsx` (self).

**Badge pattern to extend to tri-state** (lines 45-60 — D-04 adds `'editado'` as a third `BadgeKind`; copy the conditional-class ternary style, amber token per UI-SPEC; strings `BADGE_EDITADO` go in constants/ui.ts):
```typescript
type BadgeKind = 'gerado' | 'perfil'

function Badge({ kind }: { kind: BadgeKind }) {
  return (
    <span className={kind === 'gerado'
      ? 'normal-case rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700'
      : 'normal-case rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-xs font-semibold text-gray-500'}>
      {kind === 'gerado' ? BADGE_GERADO : BADGE_DO_PERFIL}
    </span>
  )
}
```

**Ephemeral notice — the D-02 policy-line pattern** (lines 152-157; the permanent edit-policy line uses the SAME structure/copy source `CURRICULO_EPHEMERAL_NOTICE`, placed inside the card next to editable text per UI-SPEC):
```tsx
<div role="status" className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
  <span aria-hidden>⚠</span> {CURRICULO_EPHEMERAL_NOTICE}
</div>
```

**Section wrapper + tLang** (lines 32-38, 63-81 — `tLang` is the run-language resolver the ComparisonPanel's left column reuses; `Section` is the bordered-heading + badge shell each action row attaches to):
```typescript
function tLang(map: LocalizedText | null | undefined, language: ResumeLanguage): string {
  if (!map) return ''
  if (language === 'en') {
    return map.en ?? map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
  }
  return map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
}
```
XSS posture (lines 136-137 docstring): ALL content (LLM output, edited text, hint echo) renders exclusively as JSX text children — never `dangerouslySetInnerHTML`. The `<mark>` invention highlights are JSX segmentation (array of spans), not HTML injection.

---

### `frontend/src/constants/ui.ts` — add Phase 5 PT-BR strings (config)

**Analog:** `frontend/src/constants/ui.ts` (self — every new string lands here; no hardcoded copy in components; UI-SPEC copywriting contract is the source of the exact wording).

**String constants + interpolation-slot conventions to copy** (lines 107-112 for badge/notice strings; lines 115-123 for `{slot}` interpolation style — plain template replace, never a formatter library):
```typescript
export const BADGE_GERADO = 'Gerado'
export const BADGE_DO_PERFIL = 'Do perfil'
export const CURRICULO_EPHEMERAL_NOTICE =
  'Este resultado existe apenas nesta página — atualizar ou fechar o navegador perde o conteúdo. Copie o que quiser guardar.'
// {covered}/{total} interpolation slots — plain factual tally ONLY
export const CURRICULO_COBERTURA_SINGULAR =
  '{covered} de {total} keyword da vaga aparece no currículo.'
```
Also promotes `TEXTAREA_CLASSES` here (UI-SPEC IN-04 — same single-definition rule as `PRIMARY_BUTTON_CLASSES`, lines 69-74; source value currently duplicated in CurriculoHome.tsx lines 55-56).

---

### `frontend/src/lib/comparison.ts` (utility, transform) — TS port, no TS analog

**Port source (Python, read verbatim — transcribe mechanically, do not redesign):**

`backend/app/resume/coverage.py` lines 33-41:
```python
def _fold(text: str) -> str:
    """Casefold + NFKD accent-fold (drop combining marks) — both sides, once."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))

def _term_pattern(term: str) -> re.Pattern:
    """Lookaround-bounded pattern over the FOLDED term — never \\b (Pitfall 1)."""
    return re.compile(r"(?<!\w)" + re.escape(_fold(term)) + r"(?!\w)", re.IGNORECASE)
```

`backend/tests/test_resume_grounding.py` lines 146-162 (numeral prior art — copy the regex STRUCTURALLY: date shape first, %-with-sign, plain numbers, lookarounds both sides):
```python
_NUMERAL_RE = re.compile(
    r"""
    (?<!\w)                  # not the tail of a word/identifier
    (?:
        \d{4}-\d{2}          # AAAA-MM date shape, kept whole
      | \d+(?:[.,]\d+)*%     # percentage with the sign attached
      | \d+(?:[.,]\d+)*      # plain / decimal / thousand-grouped number
    )
    (?!\w)                   # no identifier tail either
    """,
    re.VERBOSE,
)

def extract_numerals(text: str) -> set[str]:
    return set(_NUMERAL_RE.findall(text))
```
`assert_invention_free` semantics (lines 165-181): folded SUBSTRING containment against the facts blob — a generated "2022" matches facts "2022-03" (not token equality).

**TS mapping (the only three translation decisions):**
1. fold: `text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '')` (JS has no casefold — `toLowerCase` is the documented PT-BR/EN approximation)
2. term boundary: `new RegExp(`(?<!\\w)${escapeRegExp(fold(term))}(?!\\w)`, 'i')` — NEVER `\b` (verifiably false-negatives C++/C#/.NET/CI/CD)
3. numerals: JS `RegExp` with the same alternation order and lookarounds (no `\b`)

Header comment must cross-reference `backend/app/resume/coverage.py:33-41` + `backend/tests/test_resume_grounding.py:146-157` (Pitfall 1). Pure functions only — no React imports, no fetch; output is segmentation data (ordered `{text, suspect}` spans) so the panel renders `<mark>` as JSX children.

---

### `frontend/src/components/ComparisonPanel.tsx` (component, client-compute)

**Analog (role-match):** `frontend/src/components/SelfCheckPanel.tsx` — the house "honest checklist panel" pattern.

**Panel skeleton to copy** (SelfCheckPanel.tsx lines 89-98 — section with aria-labelledby heading, then subsections with mt-4 h4 labels; the two-column facts-vs-generated body per UI-SPEC):
```tsx
export function SelfCheckPanel({ selfcheck, keywords, idioma }: SelfCheckPanelProps) {
  return (
    <section aria-labelledby="selfcheck-panel-title">
      <h3 id="selfcheck-panel-title" className="text-base font-semibold text-gray-900">
        {SELFCHECK_TITLE}
      </h3>
      <h4 className="mt-4 text-sm font-semibold text-gray-900">{SELFCHECK_ORDEM_LABEL}</h4>
      <ul className="mt-1 space-y-1">...</ul>
    </section>
  )
}
```

**Chip + sr-only pairing pattern** (lines 129-141 — the suspicion highlight legend uses the same glyph-aria-hidden + `sr-only` text pairing; all copy from constants):
```tsx
<li key={`${i}-${item.canonical}`} className={sobreviveu ? GREEN_CHIP_CLASSES : GRAY_CHIP_CLASSES}>
  <span aria-hidden>{sobreviveu ? '✓' : '○'}</span> {label}
  <span className="sr-only">{sobreviveu ? SELFCHECK_KEYWORD_NO_PDF : SELFCHECK_KEYWORD_AUSENTE}</span>
</li>
```
Company fold-match for the left column uses `comparison.ts`'s fold (Pitfall 8: fold-equality on company; fallback = show ALL profile entries with a neutral note — never an empty panel). Zero fetch: facts come from the `PerfilDTO` prop already mounted in ResumeResult.

---

### `frontend/src/components/SectionVersionsPanel.tsx` (component)

**Analog (role-match):** `frontend/src/components/SelfCheckPanel.tsx` row-list pattern (lines 95-107: map over an array, stable `${i}-${id}` keys, one action per row) + `SECONDARY_BUTTON_CLASSES` (defined locally in ResumeResult.tsx lines 23-24 / CurriculoHome.tsx lines 53-54 — promote or re-declare per UI-SPEC). Rows = prior versions (newest first from the `versions` stack), each with a single "Restaurar versão" action that stacks the current displayed text BEFORE restoring (SC4 invariant).

### `frontend/src/components/SectionEditor.tsx` (component, stateful form)

**Analog (role-match):** `frontend/src/pages/CurriculoHome.tsx` Zone 1 controlled-textarea form (lines 210-225 — label + controlled `<textarea>` + hint `<p>`, `TEXTAREA_CLASSES`; UI-SPEC pins textarea, NOT contentEditable):
```tsx
<label htmlFor="jd-textarea" className="block text-sm font-semibold text-gray-900">
  {CURRICULO_JD_LABEL}
</label>
<textarea
  id="jd-textarea"
  value={jdText}
  onChange={(event) => setJdText(event.target.value)}
  placeholder={CURRICULO_JD_PLACEHOLDER}
  className={TEXTAREA_CLASSES}
/>
```
Save/cancel buttons reuse `PRIMARY_BUTTON_CLASSES` / `SECONDARY_BUTTON_CLASSES` (constants/ui.ts line 73-74 and CurriculoHome.tsx lines 53-54). For experiencias, the line-split contract applies per UI-SPEC (textarea text → bullets by newline on save).

### `frontend/src/components/ConfirmStrip.tsx` (shared amber strip)

**Analog (role-match):** `frontend/src/components/ErrorPanel.tsx` (whole file, 33 lines — the inline panel shape: bordered rounded block + heading + body + action; swap the red palette for the UI-SPEC amber tokens; strings from constants/ui.ts). The three uses (regen-over-edit, restore, confirmed full regen) share this ONE component — no `window.confirm` anywhere (UI-SPEC load-bearing ban, Pitfall 9).

---

## Shared Patterns

### 1. 200-envelope + terminal-only raw errors (ALL backend work)
**Source:** `backend/app/routes/resume.py` lines 66-74 (handler shape), tests pin it at `backend/tests/test_resume_api.py` lines 199-236.
```python
try:
    result = run_section_regen(...)
except (ProfileError, PromptError, LLMError) as exc:
    logger.error("Falha na regeneração da seção:\n%s", exc.raw)  # raw → terminal ONLY
    return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
return result  # {"status": "ok", ...}
```
**Apply to:** the new regen route handler. Never HTTP 500; never raw detail in the envelope; PT-BR lines rendered verbatim by the frontend (ErrorPanel convention).

### 2. Sync `def` + router-before-SPA-mount (new route)
**Source:** `backend/app/routes/resume.py` lines 1-20 (why), `backend/app/main.py` (registration order); structural pins at `backend/tests/test_resume_api.py` lines 301-322 (extend both path lists with `/api/resume/regenerar`).
**Apply to:** the regen endpoint. `async def` on this route is an instant review finding (Pitfall 6/7).

### 3. Strict Pydantic request models (V5)
**Source:** `backend/app/routes/resume.py` lines 42-53 + `backend/app/routes/export.py` lines 71-97.
**Apply to:** `RegenerarRequest` — `ConfigDict(extra="forbid")`, `Literal` for `language`/`secao`, `Field` bounds (`jd_text` 80..20000, `dica: str | None` ≤500, `secoes: ExportarSecoes` imported, `keywords: list[Keyword] = []`). Validation failure = FastAPI 422 (client bug, not UI state).

### 4. Offline test seams (ALL new tests)
**Source:** `backend/tests/test_resume_api.py` lines 103-131 (`PROFILE_PATH` retarget + `run_stage` stub), `backend/tests/test_resume_pipeline.py` lines 63-82 (`ScriptedClient` recording `create()` kwargs).
**Apply to:** both new test files. 100% offline; `ScriptedClient` proves hint-in-user-message / system-untouched / one-stage-run; caplog proves raw-detail-terminal-only.

### 5. Export-state reset on displayed-content mutation (frontend)
**Source:** `frontend/src/pages/CurriculoHome.tsx` lines 111-120.
**Apply to:** every destructive path's success handler (edit save, regen success, restore): the same `setReceiptFilename(null); setSelfcheck(null); setExportarErros(null)` triple BEFORE writing new displayed content. Edits/restores do NOT touch cobertura chips (gerar-time snapshot stays — only regen success swaps it from the response).

### 6. JSX text children only — no raw HTML (frontend)
**Source:** `frontend/src/components/ResumeResult.tsx` lines 136-137 (docstring posture), ErrorPanel/SelfCheckPanel render style.
**Apply to:** edited text, LLM output, hint echoes, `<mark>` highlights — all JSX children/spans; no `dangerouslySetInnerHTML`.

### 7. PT-BR copy centralized in constants/ui.ts (frontend)
**Source:** `frontend/src/constants/ui.ts` (whole file); interpolation via `template.replace('{slot}', String(v))` (SelfCheckPanel.tsx lines 39-42).
**Apply to:** every new string (badges, policy line, confirm strips, panel titles, legend, version labels). No hardcoded PT-BR in components.

### 8. `runs_log`/`client` injection seams (backend pipeline)
**Source:** `backend/app/resume/pipeline.py` lines 17-18 (docstring), 51-53, 79-81 (threading).
**Apply to:** `run_section_regen` — same optional `runs_log: Path | None = None, client: object | None = None` params on every `run_stage` call; this is what keeps the default suite offline (D-16).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `frontend/src/lib/comparison.ts` | utility | transform | No `frontend/src/lib/` directory and no pure-TS algorithm module exists yet (frontend is all components/pages/api). The ALGORITHM has a verified Python source (`coverage.py` + `test_resume_grounding.py`) — this file is a mechanical port, not an imitation of a TS sibling. Establish the lib/ dir with it. |
| `frontend/src/components/ConfirmStrip.tsx` | component | static | No amber inline-strip component exists; closest shape is ErrorPanel.tsx (red palette). New component, palette/copy per UI-SPEC. |
| `frontend/src/components/SectionEditor.tsx` / `SectionVersionsPanel.tsx` | component | stateful | No prior inline-editor or version-list UI exists; both are compositions of the SelfCheckPanel row-list + CurriculoHome textarea/button patterns above. |

## Metadata

**Analog search scope:** `backend/app/routes/`, `backend/app/resume/`, `backend/app/llm/`, `backend/tests/`, `frontend/src/{api,components,pages,constants}`
**Files scanned:** 16 source files read (5 backend app, 3 backend tests, 6 frontend, gateway excerpt) + `git ls-files` tracking verification (all analogs tracked; no gitignored mirrors exist in this repo)
**Pattern extraction date:** 2026-09-27
