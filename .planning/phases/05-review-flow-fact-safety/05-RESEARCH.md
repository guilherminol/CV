# Phase 5: Review Flow + Fact Safety - Research

**Researched:** 2026-09-27
**Domain:** In-app review flow (per-section regeneration, inline editing, deterministic fact-vs-generated comparison) on the existing FastAPI + React 19 stack — zero new dependencies
**Confidence:** HIGH (codebase-grounded; every reused seam read this session; 232 offline tests green; frontend build green)

## Summary

Phase 5 adds three powers to the existing result card — regenerate one section, edit any generated text inline, and compare profile facts vs generated text with deterministic invention highlights — without a single new package. The stack that Phases 1–4 shipped already contains every primitive this phase needs: the stage-based gateway (`run_stage` + `_STAGE_SCHEMAS` with the three resume stages registered) makes per-section regeneration a one-stage call with localized retry for free; the deterministic matcher's fold/lookaround primitives (`coverage.py`) port directly to the client-side invention highlighter; and the Phase 4 export endpoint already posts the *displayed* state (D-10), which means inline edits flow into the PDF with zero backend change.

The only new backend surface is one endpoint, `POST /api/resume/regenerar`, mirroring the established envelope discipline (sync `def`, 200 + `{status, erros}`, Pydantic `extra="forbid"`). It takes the section id, the JD, the run language, the current displayed sections, the run's keywords, and an optional hint; runs exactly one `run_stage`; merges the new section over the submitted siblings server-side; and returns the **full merged `secoes` + recomputed coverage** — so the frontend replaces its state wholesale (no client-side merge logic to get wrong) and sibling byte-identity (D-07/SC1) is a directly testable property of the response. The hint joins the user message as data via a compose-level helper (D-07 pattern), leaving the gateway, prompt files, and `runs.jsonl` untouched (D-15).

The comparison panel is 100% client-side: the full `PerfilDTO` is already mounted in `ResumeResult`, so both the left "Fatos do perfil" column and the invention tokenization compute locally with zero latency after every edit. The highlighter is a TypeScript port of the verified Python mechanics — the fold (casefold + NFKD strip-combining) and lookaround-bounded matching from `coverage.py`, plus the numeral-extraction regex already proven in `tests/test_resume_grounding.py` (`extract_numerals` / `assert_invention_free` are the Phase 5 invention detector's prior art, currently test-only). The UI contract (05-UI-SPEC.md, approved 7/7) pins every class, copy string, state-machine rule, and the "suspicion, not verdict" framing (D-11).

**Primary recommendation:** One new endpoint (`/api/resume/regenerar`) returning the full merged `secoes` + recomputed coverage; one compose-level hint helper in `pipeline.py`/`facts.py`; all edit/version/comparison/highlight logic as client-side React state + one pure TS module porting the coverage fold mechanics; no new dependencies anywhere.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
*(all 15 decisions `[auto — silence]`, copied from 05-CONTEXT.md)*

**Política de edição**
- **D-01:** Edições vivem em estado efêmero da sessão (React state). Atualizar a página descarta — com aviso visível. Write-back aos arquivos do perfil rejeitado; localStorage rejeitado (duas verdades efêmeras).
- **D-02:** Política explícita na UI: aviso permanente junto ao texto editável — "Edições valem apenas para esta execução — atualizar a página descarta" — no padrão do CURRICULO_EPHEMERAL_NOTICE.
- **D-03:** Edições fluem automaticamente para export e self-check — a Fase 4 já exporta o estado exibido (D-10 Fase 4); nenhum passo "aplicar" extra.
- **D-04:** Terceiro estado de badge: **Editado** (Gerado / Do perfil / Editado).

**Regeneração por seção (REVIEW-01)**
- **D-05:** Dica de direcionamento opcional por seção: campo de texto exibido sob demanda, anexado ao user message da chamada de regeneração (padrão D-07 Fase 2 — dados no user message, nunca no system prompt).
- **D-06:** Regeneração = run_stage do estágio da seção via gateway existente (`_STAGE_SCHEMAS`), merge do resultado no estado montado. Retry localizado, custo só da seção.
- **D-07:** Seções irmãs intactas (SC1 literal). Cobertura de keywords recalculada sobre o texto montado inteiro após o merge (matcher determinístico).
- **D-08:** Pilha de versões por seção em memória de sessão: cada regeneração empilha a versão anterior; painel "versões" lista as anteriores com ação de restaurar. Sem persistência em arquivo.

**Fato vs gerado (SC3)**
- **D-09:** Painel de comparação por seção gerada, expansível ("Comparar com o perfil"): duas colunas — fatos do perfil | texto gerado. Experiências comparadas por campo.
- **D-10:** Destaques de invenção determinísticos: entidades/métricas/tecnologias nomeadas no texto gerado ausentes dos fatos da fonte, marcadas visualmente. Sem juiz LLM. Reusa as primitivas de fold/normalização do matcher (coverage.py).
- **D-11:** O highlight é suspeita, não sentença: a UI deixa claro que a comparação mecânica destaca candidatos a invenção; o julgamento final é do usuário.

**Fluxo e integração**
- **D-12:** Edição inline no card de resultado: clique para editar transforma a seção em textarea; salvar retorna ao texto com badge Editado. Sem modal, sem modo separado.
- **D-13:** Perfil view intocado — a Fase 5 toca apenas a tela de resultado.
- **D-14:** Regenerar sobre edição não salva pede confirmação leve ("isso vai descartar sua edição — continuar?") — a versão editada é empilhada antes da regeneração, então nada se perde mesmo sem confirmar.
- **D-15:** runs.jsonl intocado: regeneração loga como qualquer chamada de estágio; sem campos novos.

### Claude's Discretion
- Mecânica exata do editor inline (textarea vs contentEditable — UI-SPEC resolved: textarea), estados de foco/atalhos, acessibilidade do fluxo de edição.
- Formato exato dos destaques de invenção, tokens comparados (métricas numéricas, nomes próprios, tecnologias).
- Estrutura do backend: endpoint único de regeneração vs reuso direto do endpoint existente por estágio; forma do hint no payload (estrito, extra="forbid").
- Estrutura da pilha de versões no frontend (hook/componente), limites de versões em memória.

### Deferred Ideas (OUT OF SCOPE)
- Write-back de edições ao perfil ("salvar no perfil") — aditivo quando o usuário quiser.
- Normalização de hífen no matcher de cobertura e localização do marcador "atual" em EN — polish candidates (Fase 6 ou follow-up).
- Not in this phase: LinkedIn (Fase 6); PT-BR hardening/glossário (Fase 6).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REVIEW-01 | User can regenerate individual resume sections and edit generated text inline in the app before exporting | New `POST /api/resume/regenerar` (one `run_stage` per call, D-06); client-side edit/version/comparison state per the UI-SPEC contract; edits flow to export via the already-shipped displayed-state contract (D-03) |
| SC1 | Regenerate single section without affecting others, optionally with a hint | Endpoint returns full merged `secoes` — siblings verified byte-identical in tests; hint joins user message via compose-level helper (D-05) |
| SC2 | Inline edits flow exactly into preview and exported PDF | `resultado.secoes` in CurriculoHome IS the displayed state; export already posts it (ExportarRequest, D-10 Fase 4) — no backend change |
| SC3 | Side-by-side profile-facts vs generated comparison with inventions immediately visible | 100% client-side ComparisonPanel + pure TS port of `coverage.py` fold primitives + `extract_numerals` regex from test_resume_grounding.py |
| SC4 | Regeneration never silently destroys edits; prior versions accessible; edit policy explicit | Per-section version stack in React state (stack-before-mutate invariant); three amber confirm strips; permanent policy line — all pinned by 05-UI-SPEC.md |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Extracted from `.claude/CLAUDE.md` (Project + STACK.md blocks) — planner must verify compliance:
- **Localhost only** — no hosting, no auth, no external database, no multi-user. File-based store (Markdown/YAML in git); backend is read-only over `content/` (verified: tests never write there, conftest.py:3-5).
- **All LLM access via OpenRouter**; API key in local `.env` only; model slug config-only (`LLM_MODEL`).
- **No new frontend dependencies** (STACK.md What NOT to Use: axios → native fetch; no i18n framework — PT-BR strings in `constants/ui.ts`; no Next.js; no LangChain/prompt frameworks). The no-JS-test-runner stance is a held house contract (STATE.md: "no JS test runner introduced").
- **TypeScript ~5.9 pinned**; `tsc -b` is the Pydantic↔TS drift gate (client.ts header comment; verified build green).
- **Tailwind v4, hand-rolled utility components, no component library** — re-affirmed by 05-UI-SPEC.md (Tool: none, checker 7/7).
- **GSD workflow enforcement** — no direct repo edits outside GSD flow (meta; this research is part of that flow).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Per-section regeneration (SC1) | API/Backend | — | One `run_stage` call needs the profile facts supply line + runs.jsonl audit — both live backend-side |
| Hint steering (D-05) | API/Backend (compose) | Frontend (input state) | Hint is user DATA joined into the user message blob at compose level; never the system prompt |
| Coverage recompute post-regen (D-07) | API/Backend | — | `classify_coverage` + keywords live backend; response carries recomputed cobertura (client has no matcher — UI-SPEC pins this) |
| Inline editing + version stack (D-12/D-08) | Browser/Client | — | Pure session React state; export consumes it via the existing displayed-state contract |
| Edit policy notice (D-02) | Browser/Client | — | Permanent UI line inside the card (UI-SPEC pins placement/copy) |
| Fact-vs-generated comparison (D-09) | Browser/Client | — | `PerfilDTO` already mounted in ResumeResult; zero-latency recompute after every edit demands client execution |
| Invention highlights (D-10/D-11) | Browser/Client | — | Must recompute against the *currently displayed* (post-edit) text per UI-SPEC — a backend round trip per save would be wrong; TS port of verified fold mechanics |
| Export with edits (D-03/SC2) | API/Backend (unchanged) | Frontend (payload) | Phase 4 endpoint already renders the submitted state verbatim — zero contract change |

## Standard Stack

### Core (all existing — verified this session; **no new packages**)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.141.1 (verified via `uv run` import) | New `/api/resume/regenerar` route, sync `def` | House envelope + threadpool pattern established in routes/resume.py / export.py |
| pydantic | 2.13.5 (verified) | `RegenerarRequest` strict model, `extra="forbid"` | Every request in the app is strict-validated (T-03-01/T-04-02 posture) |
| openai (PyPI) | 3.19.2 (verified) | Indirect only — via existing `run_stage` gateway | Regeneration NEVER calls the SDK directly |
| React | 19.2.8 (package.json, verified) | Edit/version/comparison state | House pattern: session React state, no external state lib |
| @tanstack/react-query | 5.103.2 (package.json) | New `regenerarSecao` mutation only | gerar/exportar already use useMutation with 200-envelope branching |
| TypeScript | ~5.9 (package.json) | TS port of fold primitives; `tsc -b` gate | Verified `npm run build` green (604ms) |
| Tailwind CSS | 4.3.3 (package.json) | All new UI per UI-SPEC class table | `line-clamp-2` is core in v4 [CITED: tailwindcss.com/docs/line-clamp] — no plugin needed |

### Supporting (existing, reused)
- `backend/app/resume/coverage.py` — `_fold` (casefold + NFKD strip combining, coverage.py:33-36), `_term_pattern` lookaround `(?<!\w)term(?!\w)` (coverage.py:39-41) — algorithm to port verbatim to TS.
- `backend/tests/test_resume_grounding.py:146-181` — `extract_numerals` regex + `assert_invention_free` — the invention detector prior art (numerals: AAAA-MM dates kept whole, percentages with sign, thousand-grouped/decimal numbers, identifier-tail guard `utf8`/`v2`).
- `backend/app/resume/facts.py` — `serialize_profile_facts` / `compose_stage_input` — the facts supply line; compose variant gains the optional hint block.
- `frontend/src/api/client.ts` — typed client; `SecoesDTO`/`ExportarRequest` mirrors; add `regenerarSecao` here.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New `/api/resume/regenerar` endpoint | Reusing `POST /api/resume/gerar` | Rejected: gerar always runs extraction + all 3 stages — violates SC1 (sibling byte-identity) and D-06 (cost only of the section) |
| Returning only the regenerated section | Returning the full merged `secoes` | Full merge returned by backend kills client-side merge bugs and makes D-07 a response-level testable property — recommended |
| Client TS port of fold primitives | Backend highlight endpoint called per edit | Client port recommended: highlights must recompute on the displayed text after every edit/save/restore; a fetch per save adds latency and breaks the read-only-toggle rule |
| `useReducer` for section state machine | Plain `useState` hooks | React docs: prefer a reducer "if you often encounter bugs due to incorrect state updates… many event handlers modify state in similar ways" [CITED: react.dev/learn/extracting-state-logic-into-a-reducer] — the UI-SPEC lock matrix qualifies; either is house-legal, planner picks |
| Extending `run_stage(stage, input, lang, hint)` | Compose-level hint in `facts.py`/`pipeline.py` | Compose-level recommended: zero gateway churn (its 3 test files + drift-locks untouched), runs.jsonl automatically unchanged (D-15) |

**Installation:**
```bash
# Nothing to install. Verify existing stack:
cd backend && uv run python -c "import fastapi, pydantic, openai; print('ok')"
cd frontend && npm run build   # tsc -b drift gate
```

## Package Legitimacy Audit

> Gate protocol run: this phase installs **zero external packages** (D-01/D-06 mandate reuse; UI-SPEC pins Tool: none). `uv run pytest` (232 passed) and `npm run build` (green) prove the existing dependency set works. No `npm install` / `uv add` step exists in this phase, so the per-package legitimacy table is not applicable.

**Packages removed due to [SLOP] verdict:** none — no packages proposed.
**Packages flagged as suspicious [SUS]:** none.
**If the planner later proposes any package** (e.g., a diff library — explicitly rejected by the research focus), it must pass the legitimacy gate before install.

## Architecture Patterns

### System Architecture Diagram

```
Browser (React session state — CurriculoHome owns resultado.secoes = THE displayed state)
  │
  ├─ [Regenerar seção] ────► POST /api/resume/regenerar  (NEW, sync def)
  │     body: {jd_text, language, secao, dica?, secoes (current displayed), keywords}
  │        │ extra="forbid" Pydantic → 422 on malformed
  │        ▼
  │     run_section_regen (pipeline.py, NEW)
  │        ├─ load_profile() fresh → serialize_profile_facts(profile, language)
  │        ├─ compose_regen_stage_input(facts, jd_text, dica)   ← hint block = DATA
  │        ├─ run_stage(SECTION_STAGE_BY_ID[secao], input, language)
  │        │      └─ gateway.py (UNCHANGED) ──► OpenRouter ──► runs.jsonl metadata-only
  │        ├─ merge: submitted secoes with new section (server-side)
  │        └─ classify_coverage(keywords, assembled generated text) → cobertura/resumo
  │     ◄──── {status:"ok", idioma, secoes (FULL merged), cobertura, cobertura_resumo}
  │     ◄──── {status:"erro", erros:[PT-BR]}  (200 envelope; prior text stays mounted)
  │
  ├─ [Editar / Salvar / Cancelar / Restaurar] — pure client state
  │     invariant: EVERY destructive path stacks the current displayed text FIRST
  │
  ├─ [Comparar com o perfil] — pure client compute (zero fetch)
  │     left column: facts from the mounted PerfilDTO (tLang run-language resolution)
  │     right column: displayed text segmented around suspect tokens → <mark>
  │     tokenization: TS port of _fold + _term_pattern + extract_numerals
  │
  └─ [Exportar PDF] (UNCHANGED Phase 4) — posts displayed state; edits flow into PDF
        Export-state reset rule: ANY displayed-content mutation clears receipt/selfcheck/errors
```

### Recommended Project Structure

```
backend/
├── app/
│   ├── resume/
│   │   ├── pipeline.py        # + run_section_regen(), SECTION_STAGE_BY_ID map
│   │   └── facts.py           # + compose_regen_stage_input() (or hint param on compose_stage_input)
│   └── routes/
│       └── resume.py          # + RegenerarRequest + POST /api/resume/regenerar
└── tests/
    ├── test_resume_regen_api.py     # NEW: envelope/422/structural tests
    └── test_resume_regen_pipeline.py # NEW: one-stage run, sibling identity, hint-as-data
frontend/src/
├── api/client.ts              # + regenerarSecao() + RegenerarRequest/Response types
├── lib/comparison.ts          # NEW: fold/tokenize pure functions (port of coverage.py mechanics)
├── components/
│   ├── ResumeResult.tsx       # extends: policy line, per-section action rows, badge Editado
│   ├── ComparisonPanel.tsx    # NEW: two-column panel + <mark> segmentation + legend
│   ├── SectionVersionsPanel.tsx # NEW: version rows + Restaurar versão
│   ├── SectionEditor.tsx      # NEW: textarea editor + save/cancel + dirty confirm
│   └── ConfirmStrip.tsx       # NEW: shared amber strip (3 uses)
├── pages/CurriculoHome.tsx    # + regenerar mutation + section UI state (versions/hints/editor)
└── constants/ui.ts            # + all PT-BR strings; TEXTAREA_CLASSES promoted here (UI-SPEC IN-04)
```

### Pattern 1: Regeneration endpoint reusing the stage gateway (D-06/D-07/D-15)

**What:** One route handler → one pipeline function → one `run_stage` call; response carries the FULL merged section set + recomputed coverage.
**When to use:** Every per-section regen. Never re-run extraction or sibling stages.

```python
# Verified seams this builds on:
# backend/app/llm/gateway.py:49-54 — _STAGE_SCHEMAS keys (verbatim):
#   "keyword-extraction", "resume-summary", "resume-experiencias", "resume-skills"
# backend/app/resume/pipeline.py:37 (verbatim):
#   SECTION_STAGES = ("resume-summary", "resume-experiencias", "resume-skills")
# backend/app/routes/resume.py:50-53 — GerarRequest pattern:
#   class GerarRequest(LintRequest):
#       language: Literal["pt-BR", "en"] = "pt-BR"
# backend/app/routes/export.py:71-83 — ExportarSecoes bounds (verbatim):
#   resumo: str = Field(min_length=1, max_length=RESUMO_MAX_LENGTH)   # 8000
#   experiencias: list[ExperienciaGerada] = Field(min_length=1)
#   habilidades: list[str] = Field(min_length=1)

SECTION_STAGE_BY_ID = {
    "resumo": "resume-summary",
    "experiencias": "resume-experiencias",
    "habilidades": "resume-skills",
}

class RegenerarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    jd_text: str = Field(min_length=JD_MIN_LENGTH, max_length=JD_MAX_LENGTH)  # same 80..20000
    language: Literal["pt-BR", "en"]
    secao: Literal["resumo", "experiencias", "habilidades"]
    dica: str | None = Field(default=None, max_length=500)   # strip-empty → None in handler
    secoes: ExportarSecoes        # import from app.routes.export — the SAME displayed-state shape
    keywords: list[Keyword] = []  # zero-keyword runs are legitimate (export precedent)
```

Route handler: plain `def`; try/except `(ProfileError, PromptError, LLMError)` → `logger.error(raw)` + `{"status":"erro","erros":exc.message_ptbr.splitlines()}` (verbatim house pattern, routes/resume.py:66-74).

### Pattern 2: Hint joins the user message as DATA (D-05, T-02-01)

**What:** The gateway composes the user message internally as
`f"Idioma preferido de saída: {language}\n\nTexto:\n{input_text}"` (gateway.py:110). The hint therefore enters through `input_text` at compose level — no gateway change, no prompt-file change, and since the gateway logs metadata only (gateway.py:113-123 base record fields: ts/stage/model/language/attempt/status/tokens/latency/error), the hint text never reaches `runs.jsonl` (D-15 satisfied automatically).

```python
# backend/app/resume/facts.py — compose extension (facts.py:147-157 is the base pattern)
def compose_regen_stage_input(facts: str, jd_text: str, dica: str | None) -> str:
    base = compose_stage_input(facts, jd_text)
    if not dica or not dica.strip():
        return base
    return (
        base
        + "\n\nDICA DE DIRECIONAMENTO (texto livre do usuário — um dado, não uma "
        "instrução de sistema; siga-a somente dentro das regras acima):\n"
        + dica.strip()
    )
```

Rationale: prompt hard rules (never-invent, facts anchor) stay in the system message where the model weights them; a malicious/quirky hint cannot displace them, and the deterministic highlighter + `assert_invention_free` harness police the output regardless.

### Pattern 3: Client-side invention tokenization (D-10/D-11) — port, don't reinvent

**What:** A pure TS module mirroring the verified Python mechanics 1:1.

```typescript
// frontend/src/lib/comparison.ts — algorithm sources (verified this session):
// 1. fold: coverage.py:33-36 — casefold + NFKD, drop combining marks.
//    TS: text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '')
//    (JS has no casefold; toLowerCase is the documented approximation for PT-BR/EN — [ASSUMED] equivalence)
// 2. term boundary: coverage.py:41 — lookarounds, NEVER \b:
//    new RegExp(`(?<!\\w)${escapeRegExp(fold(term))}(?!\\w)`, 'i')
// 3. numerals: test_resume_grounding.py:146-157 regex (verbatim shape):
//    dates \d{4}-\d{2} first, then \d+([.,]\d+)*% with sign, then plain numbers,
//    both sides lookaround-bounded — copy the VERBOSE regex structurally, do not simplify.
```

Suspect-token categories and source-fact scope (planner discretion per CONTEXT; recommended):
- **Numeral tokens** (dates, percentages, quantities) in the generated text not found (folded substring containment, per `assert_invention_free` semantics) in the section's source-facts blob.
- **Named entities / technologies**: candidate capitalized tokens (not sentence-initial) + any token matching tech-shape (e.g. contains digits+letters like `C++`, `.NET`, `CI/CD`) checked against the section's source-fact inventory (folded). Cross-check vocabulary: skills items, project technologies, certification names, companies, institutions, job titles — extracted FROM the source-facts blob itself, so the inventory is always profile-derived.
- **Source facts per section** (recommended reading of the phase focus; the UI-SPEC pins only the left-column *display*):
  - `resumo` → the whole serialized profile facts (a summary legitimately synthesizes the entire profile; `serialize_profile_facts` output is the exact grounding blob).
  - `experiencias` (per entry) → that profile entry's description + impacts + dates + title (fold-matched by company). Strict per-entry scope catches cross-entry contamination (a metric from another job) — a real failure mode worth false-suspects; D-11's legend is the designed escape hatch.
  - `habilidades` → the profile's full skill inventory (`skills[].items` + project technologies).
- Precision/recall honesty: pure-token matching WILL flag legitimate paraphrases (that is D-11's stated, desired behavior) and may miss synonyms (acceptable — deterministic honesty beats fake precision; REQUIREMENTS bans the LLM-judge alternative).

### Pattern 4: Section state machine + version stack (D-08/D-12/D-14)

**What:** Per generated section, session React state:

```typescript
// Recommended shape (planner discretion: useReducer vs useState hooks — both house-legal)
type BadgeKind = 'gerado' | 'perfil' | 'editado'          // D-04 third state
interface SectionVersion { secao: SecoesContent; origem: 'gerado' | 'editado' }
interface SectionUiState {
  versions: SectionVersion[]        // newest first; restore stacks displayed first, then pops
  dica: string                      // persists across regens of the section until cleared
  dicaAberta: boolean; comparacaoAberta: boolean; versoesAberta: boolean
}
// editing state is GLOBAL-ISH: one editor open at a time (UI-SPEC rule)
// { section: SecaoId | null, entryIdx?: number, draft: string, dirty: boolean }
```

**Critical invariants (each maps to a UI-SPEC row):**
1. `resultado.secoes` (the `GerarOk` state in CurriculoHome) is the SINGLE source of displayed content — save/restore/regen success all write there, so export + self-check + coverage consume the edited state automatically (D-03). Do NOT keep a shadow copy.
2. Every destructive mutation (save, regen success, restore, confirmed full regen) pushes the current displayed text + its badge-origin onto `versions` FIRST (SC4 "never silently" is this invariant, testable in code review + UAT).
3. The locking matrix from UI-SPEC (one editor at a time; editor open → export/full-regen/restore disabled but own-section regen allowed via D-14 strip; any long op → all regen/edit/export/restore/dica disabled, Comparar/Versões stay usable) must be implemented as derived booleans from a small set of state atoms (`editor`, `regenPending`, `exportar.isPending`).
4. Export-state reset (extends the existing gerar onSuccess reset, CurriculoHome.tsx:112-119): ANY displayed-content mutation clears `receiptFilename`/`selfcheck`/`exportarErros` before mounting the new state.
5. Edits/restores do NOT recompute coverage chips (no client matcher — UI-SPEC pins the gerar-time snapshot stays); only a section-regen success swaps Zone 5 from the response's recomputed `cobertura`.

### Pattern 5: Response envelope and offline test seams (established, inherited)

- Route tests stub `app.resume.pipeline.run_stage` via `monkeypatch.setattr` (test_resume_api.py:111-131 `_stub_stages`) and retarget `PROFILE_PATH` (D-15/D-16 seams) — mirror this for the regen route; `TestClient(app)` + `caplog` raw-detail assertions are the house pattern.
- Pipeline/gateway-level tests inject `ScriptedClient` (test_resume_pipeline.py / test_resume_grounding.py, copied verbatim between files) — it **records every `create()` kwargs**, which is exactly how to assert (a) the hint text landed in `messages[1]["content"]`, (b) `messages[0]` (system) is the untouched prompt body, (c) exactly one stage ran.
- Structural pins to extend: `test_handlers_are_sync_def_never_coroutines` and `test_resume_router_registered_before_spa_mount` (test_resume_api.py:301-322) must learn the `/api/resume/regenerar` path.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Accent/case-insensitive matching | Custom normalization (unidecode-style tables, regex classes) | Port `coverage.py` `_fold` verbatim (casefold + NFKD strip-combining) | Already empirically verified on this project's runtime; `unidecode` would be a new dep |
| Term boundary matching | `\b` regex | `(?<!\w)term(?!\w)` lookarounds | `\b` verifiably false-negatives C++/C#/.NET/CI-CD (coverage.py:14-21, verified probe table) |
| Numeral/invention detection in tests | New detector design | `extract_numerals` + `assert_invention_free` from test_resume_grounding.py:146-181 | Proven regex: dates whole, %-sign attached, identifier tails guarded |
| LLM retry/validation/audit | Anything touching the retry loop | `run_stage` as-is | Bounded retry + runs.jsonl inherited free (D-06/D-15) |
| 200-envelope + PT-BR error split | New error shape | House try/except + `logger.error(raw)` pattern | Pinned by tests (test_resume_api.py:199-236) |
| Text diffs | jsdiff/diff-match-patch or a custom full-diff engine | Suspect-token segmentation only (highlight spans, not diffs) | Research focus bans diff libs; the UI-SPEC wants marked terms, not redlines; zero deps |
| Fact-vs-generated judgment | LLM-judged diff / NER via model | Deterministic token matching | REQUIREMENTS Out of Scope: "AI-invented achievements" ban + fake-precision ban; D-10 locks mechanical |
| Version history | Undo/redo library or command pattern | Plain array stack, newest-first | UI-SPEC: no cap required, single restore action, in-memory only (D-08) |
| Editor surface | contentEditable + rich-text plumbing | `<textarea>` + line-split contract | UI-SPEC pins textarea; contentEditable adds selection/serialization bugs for zero gain |
| Frontend server state | Redux/Zustand for this flow | React state + existing react-query mutations | House contract: no new deps; React docs confirm useState/useReducer suffice [CITED: react.dev reducer guide] |

**Key insight:** This phase is almost entirely *composition of verified seams*. The riskiest new logic is the TS port of the fold/numeral mechanics — and even that is a transcription of tested Python, not novel design.

## Common Pitfalls

### Pitfall 1: `\b` boundaries or ad-hoc normalization in the TS port
**What goes wrong:** Highlights silently miss `C++`, `.NET`, or accented PT-BR terms, or fire on substrings.
**Why it happens:** Reaching for familiar regex idioms instead of transcribing the verified primitives.
**How to avoid:** `lib/comparison.ts` carries a header comment cross-referencing `coverage.py:33-41` and `test_resume_grounding.py:146-157`; copy the regex structurally.
**Warning signs:** Manual UAT: "AWS" unmarked while "A WS"-ish tokens marked; C++ never marked.

### Pitfall 2: Merge-into-state bugs on regen success
**What goes wrong:** Sibling sections change, or export consumes stale sections.
**Why it happens:** Client-side merging of one section into three.
**How to avoid:** Backend returns the FULL merged `secoes`; frontend replaces `resultado.secoes` wholesale in the mutation's `onSuccess`. Assert sibling byte-identity in the pipeline test (submitted === returned for non-target sections).
**Warning signs:** tsc-level shape churn; any `...spread` merge of sections in frontend code.

### Pitfall 3: Breaking SC4's stack-before-mutate invariant
**What goes wrong:** A regen/restore path drops the current text without stacking — "silently destroys edits."
**Why it happens:** Four destructive paths (save, regen, restore, confirmed full regen) each need the push; it's easy to cover three.
**How to avoid:** One helper (`empilharVersaoAtual(section)`) called at the top of every destructive path; UAT checklist exercises all four.
**Warning signs:** Any destructive state write that doesn't reference the versions helper.

### Pitfall 4: Coverage chips lying after edits
**What goes wrong:** UI recomputes coverage client-side after an edit and drifts from the server matcher, or stays silently stale after a regen.
**Why it happens:** Over-engineering (client matcher — forbidden) or under-wiring (forgetting to swap Zone 5 from the regen response).
**How to avoid:** Exactly the UI-SPEC rule: edits/restores keep the gerar-time snapshot; section-regen success swaps `resultado.cobertura`/`cobertura_resumo` from the response.
**Warning signs:** Any folding logic imported into CurriculoHome; regen onSuccess not touching cobertura.

### Pitfall 5: Hint validation and logging surprises
**What goes wrong:** 422s from `extra="forbid"` (frontend sends a field the model doesn't declare), or the hint leaking into runs.jsonl.
**How to avoid:** `dica: str | None = Field(default=None, max_length=500)` declared explicitly; strip-empty→None in the pipeline; frontend omits the key when empty. The gateway's metadata-only logging already keeps the hint out of runs.jsonl (verified: base_record fields, gateway.py:113-123) — do not add logging.
**Warning signs:** New fields in run records; `hack`-style 422s in manual curl tests.

### Pitfall 6: Async def on the new route
**What goes wrong:** Event loop freezes during the ~60s blocking SDK call.
**How to avoid:** Plain `def` (threadpool), and extend the existing structural test that pins it (test_resume_api.py:301-309).
**Warning signs:** `async def` in the new handler — instant review finding.

### Pitfall 7: Route registered after the SPA mount
**What goes wrong:** `/api/resume/regenerar` unreachable in production mode (StaticFiles mount shadows it).
**How to avoid:** Add the route to the existing `resume.py` router (registered before the mount, main.py:18-20); extend `test_resume_router_registered_before_spa_mount`'s path list.
**Warning signs:** 404/HTML response when curling the endpoint against a built dist.

### Pitfall 8: Company-name matching for the comparison's left column
**What goes wrong:** No profile entry shown for a generated entry whose company was paraphrased.
**How to avoid:** Fold-equality match on company (`_fold` both sides); documented fallback when no match (planner discretion — recommend showing all profile entries in the left column with a neutral note rather than an empty panel).
**Warning signs:** Empty left column in UAT with a renamed/paraphrased company.

### Pitfall 9: Treating the confirmation strips as optional polish
**What goes wrong:** `window.confirm` or a missing strip violates the UI contract ("no modal dialogs, no window.confirm, no toasts" — UI-SPEC is load-bearing here).
**How to avoid:** The three amber strips are inline blocks per the pinned classes; all three share one `ConfirmStrip` component.
**Warning signs:** Any `confirm(` call in the diff.

## Code Examples

### Verified: the exact user-message composition the hint extends (gateway.py:105-111)
```python
# Source: backend/app/llm/gateway.py (read this session)
loaded = load_prompt(stage)  # fresh read every call (D-08/SC1)
messages: list[dict] = [
    {"role": "system", "content": loaded.body},
    {"role": "user", "content": f"Idioma preferido de saída: {language}\n\nTexto:\n{input_text}"},
]
```

### Verified: coverage primitives to port (coverage.py:33-55, verbatim quotes)
```python
# Source: backend/app/resume/coverage.py
def _fold(text: str) -> str:
    """Casefold + NFKD accent-fold (drop combining marks) — both sides, once."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))

def _term_pattern(term: str) -> re.Pattern:
    """Lookaround-bounded pattern over the FOLDED term — never \\b (Pitfall 1)."""
    return re.compile(r"(?<!\w)" + re.escape(_fold(term)) + r"(?!\w)", re.IGNORECASE)
```

### Verified: invention-detector prior art (test_resume_grounding.py:146-162, verbatim quote)
```python
# Source: backend/tests/test_resume_grounding.py
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
    """Every numeric token in the text: percentages, AAAA-MM dates, numbers."""
    return set(_NUMERAL_RE.findall(text))
```

### Verified: facts display basis for the comparison left column (facts.py:94-96 + models)
```python
# Source: backend/app/resume/facts.py — experience block shape (verbatim lines)
lines.append(f"descrição: {resolve_loc(exp.description, language)}")
for impact in exp.impacts:
    lines.append(_impact_line(impact, language))
# Profile model fields backing the panel: Experience{company, title: LocalizedText,
# description: LocalizedText, impacts: list[Impact]}, Impact{action, metric, context}
# (backend/app/profile/models.py:97-114) — run-language resolution = client.ts tLang()
```

### Verified: export-state reset pattern the phase extends (CurriculoHome.tsx:112-119)
```typescript
// Source: frontend/src/pages/CurriculoHome.tsx — gerar mutation onSuccess
setReceiptFilename(null)
setSelfcheck(null)
setExportarErros(null)
setResultado(data)
setGerarErros(null)
// Phase 5: the SAME three clears run after every displayed-content mutation
// (edit save, section regen success, restore, confirmed full regen) — UI-SPEC rule.
```

### Verified: exported contracts that must not drift (client.ts mirrors)
```typescript
// Source: frontend/src/api/client.ts:134-138 (verbatim)
export interface SecoesDTO {
  resumo: string
  experiencias: ExperienciaGeradaDTO[]
  habilidades: string[]
}
// ExperienciaGeradaDTO = { company: string; title: string; bullets: string[] } (127-131)
// RegenerarResponse's secoes reuses SecoesDTO; cobertura reuses CoberturaItemDTO (141-146).
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM-judged fact diff ("AI checks AI") | Deterministic token matching presented as suspicion | Project-locked from Phase 3 (D-02 matcher); REQUIREMENTS bans fake precision | Highlighter is mechanical; user is the judge (D-11) |
| contentEditable inline editors | Plain textarea + line-split save contract | UI-SPEC (approved 2026-09-27) | No selection/serialization bug class; paste-safe |
| localStorage draft persistence | Session React state + permanent policy line | D-01/D-02 (this phase's locked decision) | Single ephemeral truth; refresh behavior is explicit UI copy |
| Diff libraries (jsdiff et al.) | Suspect-span segmentation only | This phase's research focus (banned) | Zero deps; no redline UI to maintain |

**Deprecated/outdated (in-repo):** none — no approach this phase touches has been superseded within the repo.

## Runtime State Inventory

Omitted — this is a feature phase (no rename/refactor/migration). Verified non-issues recorded anyway: `logs/runs.jsonl` is gitignored, metadata-only, and D-15 keeps it untouched; no stored data, OS-registered state, secrets, or build artifacts carry any string this phase renames (nothing is renamed).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Request/response field names (`secao`, `dica`, full-merged `secoes` response) — recommendation, planner-discretion area per CONTEXT | Architecture Pattern 1 | Cosmetic; tests pin whatever is chosen |
| A2 | Exact hint block wording (`DICA DE DIRECIONAMENTO…`) in the composed input | Pattern 2 | Low — wording only; the DATA-in-user-message placement is the locked part (D-05) |
| A3 | `toLowerCase()` ≈ `casefold()` for PT-BR/EN text in the TS fold port | Pattern 3 | Low — no casefold-only divergences in these alphabets; false-suspects are a designed, surfaced outcome (D-11) |
| A4 | Proper-noun candidate heuristic (capitalized, non-sentence-initial, tech-shape) suffices for entity highlighting | Pattern 3 | Medium — precision/recall tradeoff is real; mitigated by D-11 legend + UAT tuning; worst case is noisy amber marks, never silent invention |
| A5 | Per-section source-fact scope (experiencias strict per-entry; resumo whole-profile) | Pattern 3 | Low-Medium — UI copy ("fatos do perfil") tolerates whole-profile scope; planner may widen experiencias scope to reduce false suspects |
| A6 | Node 22.16's `--experimental-strip-types` could smoke-test the TS pure functions without any package | Validation Architecture | Low — optional; skipped entirely if planner holds the no-JS-test-runner line strictly |
| A7 | Importing `ExportarSecoes` from `app.routes.export` into `routes/resume.py` is acceptable coupling | Pattern 1 | Low — alternative is a tiny shared contracts module |

## Open Questions

1. **Highlight tokenizer host — locked enough?**
   - What we know: UI-SPEC explicitly leaves client-TS vs backend to planner discretion; everything else (identical normalization primitives, suspicion framing) is pinned.
   - What's unclear: nothing material — recommendation is client TS (latency + read-only-toggle rule).
   - Recommendation: client TS port; treat A3/A4 as discuss-phase confirmables only if the planner disagrees.

2. **Zero-dep TS smoke test vs house no-JS-test-runner rule.**
   - What we know: `node --experimental-strip-types` (Node 22.16, verified installed) can run plain assert scripts with zero packages — but STATE.md records "no JS test runner introduced" as a held contract.
   - Recommendation: default to tsc + UAT checklist; if the planner wants automated coverage of `lib/comparison.ts`, surface `checkpoint:human-verify` before adopting the node flag (A6).

3. **Comparison left column when company fold-match fails.**
   - Recommendation: show all profile experience entries in the left column (neutral, honest) rather than an empty panel — planner discretion (A-adjacent, UI-level).

4. **`dica` max_length value.**
   - Recommendation: 500 chars (personal scale; the JD bounds precedent is 80..20000 for a much larger payload). Any value is safe; tests pin it.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | frontend build (tsc -b) | ✓ | 22.16.0 | — |
| npm | frontend scripts | ✓ | 10.9.2 | — |
| Python | backend runtime | ✓ | 3.12.10 | — |
| uv | backend env/pytest | ✓ | 0.12.5 | — |
| fastapi/pydantic/openai | new route + gateway reuse | ✓ | 0.141.1 / 2.13.5 / 3.19.2 (verified via `uv run` import) | — |
| Playwright + Chromium | unchanged export path | ✓ (shipped Phase 4; pinned 1.62.0) | — | not exercised by Phase 5 changes |
| pytest | offline suite | ✓ | 232 passed, 7 llm-deselected, 10.3s (verified run) | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none. This phase installs nothing new.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥9.1.1 (backend dev group); frontend has NO JS test runner by design |
| Config file | backend/pyproject.toml `[tool.pytest.ini_options]` — `addopts = "-m 'not llm'"`, `markers = ["llm: …"]` (verified) |
| Quick run command | `cd backend && uv run pytest -q` (10.3s) |
| Full suite command | `cd backend && uv run pytest -q` + `cd frontend && npm run build` (tsc -b gate, verified 604ms) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC1 (regen) | One stage runs; siblings byte-identical; coverage recomputed over merged text | unit+route (offline, ScriptedClient + stubbed run_stage) | `uv run pytest tests/test_resume_regen_pipeline.py tests/test_resume_regen_api.py -q` | ❌ Wave 0 |
| SC1 (hint) | Hint reaches the USER message only; system message untouched; runs.jsonl unchanged fields | unit (assert on recorded `create()` kwargs) | `uv run pytest tests/test_resume_regen_pipeline.py -q` | ❌ Wave 0 |
| SC2 (edits→PDF) | Export posts displayed state | already proven (Phase 4 suite); no new backend code | `uv run pytest tests/test_export_api.py -q` | ✅ |
| SC3 (comparison) | Tokenizer purity/fold correctness vectors | unit (Python mirror documenting vectors) + tsc + UAT | `uv run pytest tests/test_coverage.py -q` (existing primitives); TS side manual/smoke (Open Q2) | partial ✅ / ❌ TS Wave 0 decision |
| SC4 (no silent destroy) | Stack-before-mutate on all 4 destructive paths; confirm strips | mostly manual UAT (locking matrix); version-helper invariant reviewable | manual checklist at `/gsd:verify-work 5` | ❌ UAT doc |
| Structural | sync `def` + router-before-mount for regenerar | structural | `uv run pytest tests/test_resume_api.py -q` (extend path lists) | ✅ extend |
| Strict validation | 422 on unknown keys/short jd/unknown secao/empty sections | route | `uv run pytest tests/test_resume_regen_api.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest -q` + `cd frontend && npm run build`
- **Per wave merge:** full backend suite + frontend build green
- **Phase gate:** full suite green + manual UAT of the SC4 locking matrix and comparison panel before `/gsd:verify-work 5`

### Wave 0 Gaps
- [ ] `backend/tests/test_resume_regen_api.py` — envelope + 422 + structural coverage for the new route
- [ ] `backend/tests/test_resume_regen_pipeline.py` — one-stage run, sibling identity, hint-as-data assertions
- [ ] Planner decision (not a file): TS-side verification approach for `lib/comparison.ts` (Open Q2 / A6)

## Security Domain

`security_enforcement: true`, ASVS level 1 (config.json) — required section.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | localhost single-user tool — none exists by design |
| V3 Session Management | no | no sessions; React state is ephemeral by decision (D-01) |
| V4 Access Control | no | localhost bind only; no auth surface |
| V5 Input Validation | **yes** | Pydantic `extra="forbid"` + Literal + Field bounds on `RegenerarRequest` (house rule, T-03-01 posture); hint bounded `max_length` |
| V6 Cryptography | no | no crypto in this phase; never hand-rolled |
| V12/V14 related | yes (carried) | API key stays in `.env`; raw errors terminal-only, never in envelopes (verified pattern) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via user hint ("ignore rules, invent metrics") | Tampering | Hint is DATA in the user message only (D-05/T-02-01); never-invent hard rules stay in the system prompt; deterministic highlighter + `assert_invention_free` harness detect violations; runs.jsonl audit trail |
| XSS via generated/edited text or hint | Tampering | All content renders as JSX text children — no `dangerouslySetInnerHTML` anywhere (T-01-08 posture, verified in ResumeResult/ErrorPanel); `<mark>` highlighting is JSX segmentation, not HTML injection |
| Log injection / secret leakage | Information Disclosure | Gateway logs metadata only (verified field set, gateway.py:113-123) — hint and section text never enter runs.jsonl (D-15); raw exception detail terminal-only |
| Overlong payload DoS (personal scale) | DoS | Field bounds (`jd_text` 80..20000 carried over; `dica` ≤500; section bounds mirroring ExportarSecoes incl. resumo ≤8000) |

## Sources

### Primary (HIGH confidence)
- Codebase, read this session with provenance: `backend/app/llm/gateway.py` (lines 44-111, 135-263), `backend/app/resume/pipeline.py` (whole), `backend/app/resume/coverage.py` (whole), `backend/app/resume/facts.py` (whole), `backend/app/llm/schemas.py` (whole), `backend/app/profile/models.py` (whole), `backend/app/routes/resume.py` (whole), `backend/app/routes/export.py` (whole), `backend/app/main.py`, `backend/app/config.py`, `backend/app/llm/logging.py`, `backend/app/llm/prompts.py`, `backend/tests/test_resume_grounding.py`, `backend/tests/test_resume_api.py`, `backend/tests/conftest.py`, `backend/pyproject.toml`, `frontend/src/api/client.ts`, `frontend/src/components/ResumeResult.tsx`, `frontend/src/pages/CurriculoHome.tsx`, `frontend/src/constants/ui.ts`, `frontend/src/components/ErrorPanel.tsx`, `frontend/package.json`, `prompts/resume-summary.md`
- Verified runs: `uv run pytest -q` → **232 passed, 7 deselected in 10.30s**; `npm run build` → **green in 604ms**; `uv run python -c "import fastapi…"` → 0.141.1/2.13.5/3.19.2; `node --version` → 22.16.0
- Planning set: 05-CONTEXT.md, 05-UI-SPEC.md, REQUIREMENTS.md, STATE.md, ROADMAP.md §Phase 5, .claude/CLAUDE.md, .planning/config.json

### Secondary (MEDIUM confidence — official docs fetched this session, cross-checked against the repo)
- https://tailwindcss.com/docs/line-clamp — line-clamp core in v4 (matches installed 4.3.3)
- https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/mark — mark semantics + screen-reader non-announcement (confirms UI-SPEC sr-only contract)
- https://react.dev/learn/extracting-state-logic-into-a-reducer — useReducer guidance (supports no-new-deps state design)

### Tertiary (LOW confidence)
- None — no finding in this document rests on search-engine-only evidence.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; every reused API read and exercised this session
- Architecture: HIGH — endpoint/state-machine designs map 1:1 onto verified seams; UI-SPEC is an approved 7/7 contract
- Pitfalls: HIGH for backend items (patterns pinned by existing tests), MEDIUM for the TS-port precision items (inherently heuristic; D-11 framing is the designed mitigation)

**Research date:** 2026-09-27
**Valid until:** ~2026-10-27 (stable — local codebase; no external version surface changes expected)
