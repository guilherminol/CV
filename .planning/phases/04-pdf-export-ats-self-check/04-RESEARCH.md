# Phase 4: PDF Export + ATS Self-Check - Research

**Researched:** 2026-09-27
**Domain:** Server-side HTML→PDF rendering (Playwright/Chromium), parse-back text-extraction gate (pypdf), FastAPI binary+JSON export endpoint, React blob download
**Confidence:** HIGH — the render→extract loop was probed empirically on the target machine this session; engines, gate design, and endpoint patterns all verified against official docs and the existing codebase

<user_constraints>
## User Constraints (from CONTEXT.md)

### Implementation Decisions

### Motor de renderização do PDF
- **D-01:** **Playwright** (Chromium headless, print-to-PDF) como motor de renderização — fidelidade ao layout revisado no app via print CSS; controle total do texto no template. `window.print()` client-side foi rejeitado: o gate de parse-back não seria automatizável. — **Reversibility:** reversible — o template HTML server-side é motor-agnóstico; WeasyPrint consome o mesmo HTML.
- **D-02:** **Decisão Playwright vs WeasyPrint é empírica** — construir o gate de parse-back primeiro, testar ambos os motores contra ele, embarcar o que passar (preocupação registrada no STATE.md; WeasyPrint é o fallback pré-aprovado). Se ambos passarem, Playwright embarca (fidelidade de layout).
- **D-03:** **Template HTML dedicado server-side (Python)** espelhando a montagem D-05 da tela de resultado — única fonte de verdade do layout de export, motor-agnóstico, funciona para Playwright e WeasyPrint. reportlab texto puro rejeitado: perderia a fidelidade visual do formato Google.
- **D-04:** **Playwright pinado em dev-deps + `playwright install chromium` como passo de setup documentado** no README/backend. (Se WeasyPrint vencer o gate, a dependência de browser é dispensada.)

### Gate de parse-back (REVIEW-03)
- **D-05:** **pypdf** como extrator de texto do gate — Python puro, leve, prova exatamente o que importa: a camada de texto existe e é extraível em ordem.
- **D-06:** **Checagens completas da SC2:** ordem de leitura (contato primeiro, títulos canônicos na ordem esperada), coocorrência empresa+cargo+datas por experiência, acentos PT-BR intactos — verificado em exports PT-BR e EN.
- **D-07:** **Gate automático em todo export, server-side** — faz parte do endpoint de export (SC2: "passes on every export"), não depende de ação ou disciplina do usuário.
- **D-08:** **Falha do gate = falha alta:** export rejeitado, mensagem PT-BR nomeando a verificação que falhou, raw detail só no terminal (filosofia fail-fast das Fases 1–2, D-13/D-14). PDF com defeito nunca chega ao usuário como se estivesse bom.

### Fluxo de exportação (UX)
- **D-09:** **CTA primário na tela de resultado**, abaixo do currículo montado — "Exportar PDF".
- **D-10:** **Exporta exatamente o estado montado exibido no app** (seções geradas + passthrough) — SC1 "matches what was reviewed in-app". Regenerar server-side a partir do perfil rejeitado: não seria o que o usuário revisou.
- **D-11:** **Endpoint POST retorna os bytes do PDF → download no browser**, nome convencional `curriculo-{idioma}-{data}.pdf`.
- **D-12:** **Idioma do PDF segue automaticamente o idioma da execução** — sem seletor extra no export.

### Self-check ATS na interface (REVIEW-03 UX)
- **D-13:** **Self-check roda automaticamente logo após o export bem-sucedido** (mesma resposta do endpoint) — sem botão separado.
- **D-14:** **Painel na tela de resultado:** ordem das seções ✓/✗ + sobrevivência de keywords sobre o texto extraído do PDF.
- **D-15:** **Sobrevivência de keywords reusa o matcher determinístico da Fase 3** (canônico+alias, D-02/D-11) sobre o texto extraído do PDF, por idioma — checklist honesto e auditável. Julgamento por LLM rejeitado: precisão falsa (REQUIREMENTS exclui score ATS) e custo.
- **D-16:** **Resultados efêmeros, na sessão** (coerente com D-06 Fase 3).

### Claude's Discretion
- Mecânica exata do Playwright no backend (síncrono em threadpool vs subprocess), versionamento do browser, template engine (string/HTML direto recomendado — sem engine de template nova se dispensável).
- Detalhes das checagens do gate (tolerância de whitespace, normalização de acentos na comparação), mensagens PT-BR exatas de cada falha.
- Estrutura do módulo backend (ex.: `app/export/`), contrato exato do endpoint (multipart vs bytes diretos), headers de download.
- Componentes React do painel de self-check, reuso de StatusLine/chips existentes, strings em `constants/ui.ts`.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (Phase boundary from CONTEXT.md domain: sem regenerar seção individual, edição inline, diff fato-vs-gerado e política de write-back [Fase 5]; LinkedIn [Fase 6]; glossário/QA gate de PT-BR [Fase 6]. Sem score numérico de ATS [REQUIREMENTS Out of Scope].)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REVIEW-02 | Export the resume as a single-column Google-format PDF with a clean, selectable text layer (ATS-parseable reading order) | Playwright 1.62.0 + cached Chromium probe VERIFIED on this machine: text layer extracts in DOM order, accents byte-perfect (Standard Stack; Architecture Patterns 1–3; probe evidence in Code Examples) |
| REVIEW-03 | ATS self-check that extracts the text from the exported PDF and verifies section order and keyword survival, in both languages | Gate design (Architecture Pattern 4) reuses `coverage._fold`/`keyword_in_text` [VERIFIED: backend/app/resume/coverage.py:33-55]; offline pytest strategy in Validation Architecture |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

From `.claude/CLAUDE.md` (PROJECT + STACK sections):

- **Stack:** JavaScript frontend; Python backend; localhost-only, no auth, no database — file-based store. All content in PT-BR and EN. **Output format: single-column ATS-friendly PDF, Google-recommended style.**
- **PDF export:** STACK.md already pins **playwright (PyPI)** HTML→PDF with `page.pdf(...)` + one-time `playwright install chromium` (HIGH — official docs). This research confirms it.
- **What NOT to use (STACK.md):** wkhtmltopdf/html-pdf (abandoned); canvas/jsPDF image PDFs (no text layer — fatal); client-side-only jsPDF/pdfmake; pdf-lib as primary layout engine; LaTeX toolchain on Windows; DOCX generators (out of scope); axios (native fetch); i18n frameworks (constants module).
- **Frontend deps discipline:** native fetch + React Query + Tailwind v4 only; `tsc -b` is the Pydantic↔TS drift gate (client.ts header comment). No JS test runner was introduced in Phase 3 (decision recorded in STATE.md) — pure copy functions stay unit-testable by construction.
- **Backend conventions:** sync `def` routes for blocking work (Starlette threadpool); 200-envelope error contract (never HTTP 500, raw detail terminal-only); strict Pydantic `extra="forbid"` on every request model; tests 100% offline by default (`addopts = -m 'not llm'`); routes registered BEFORE the SPA mount; `runs.jsonl` gets lines only for LLM calls (export adds none).
- **GSD workflow:** repo edits go through GSD commands (this research is one).

## Summary

Phase 4 is technically de-risked to an unusual degree because the decisive question (D-02: Playwright vs WeasyPrint) was answered **empirically during this research session on the target machine**. A mini parse-back gate probe — realistic PT-BR resume HTML → `page.pdf(format="A4")` via playwright 1.62.0 + the already-cached Chromium → `pypdf.extract_text()` — passed every SC2 property: contact line first, headings in DOM order, company+title+dates co-occurring, PT-BR accents byte-perfect ("João", "março de 2020", "EXPERIÊNCIA" with `text-transform: uppercase`), middle-dot and C++/C#/.NET tokens intact. Cold cost: **3.15s total** (import 1.4s, Chromium launch 0.88s, render+PDF 0.72s, 33KB A4). Playwright will pass the gate; the empirical sequencing D-02 demands is preserved by keeping the renderer behind a one-function engine seam and writing the template with conservative CSS (block layout only), which keeps WeasyPrint a genuinely installable fallback without pre-deciding.

The build is then: a pure Python HTML builder (no template engine — house discretion), a thin Playwright PDF function, the pypdf parse-back gate (order + co-occurrence + accent-integrity, reusing `coverage._fold`), a `POST /api/resume/exportar` route returning a **JSON 200-envelope with base64 PDF + self-check payload** (uniform error path; gate failure = `{status:"erro", erros:[PT-BR naming the failed check]}` per D-08), and frontend export mutation + Blob download + self-check panel reusing Phase 3 chip semantics. No new frontend deps; backend adds exactly two packages: `playwright==1.62.0` (pins chromium-1234, **already downloaded on this machine** — zero browser install) and `pypdf>=6.19` (pure Python).

**Primary recommendation:** Build gate-first behind an engine seam (`render_resume_html()` → `html_to_pdf()` → `parse_back_check()`), pin `playwright==1.62.0` + `pypdf`, ship the base64-envelope endpoint, and treat both SC2 languages as parametrized tests. Flag the two surfaced tensions (dates on generated experiences; EN-run passthrough headings) — both have recommended resolutions in Open Questions.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Print template (HTML/CSS mirror of D-05 montage) | API/Backend | — | D-03: single server-side source of truth; frontend has no print path |
| HTML→PDF rendering | API/Backend | — | D-01: server-side Playwright; client `window.print()` rejected (gate not automatable) |
| Parse-back gate (order, co-occurrence, accents) | API/Backend | — | D-07: automatic, server-side, in the export path |
| Keyword survival over PDF text | API/Backend | — | D-15: reuses backend matcher `coverage.keyword_in_text` |
| Export orchestration + 200-envelope errors | API/Backend | — | House route pattern (routes/resume.py) |
| PDF delivery (Blob download + filename) | Browser/Client | API/Backend (envelope carries bytes+filename) | D-11: browser native download UI; no new frontend deps |
| Self-check panel (order rows, chips) | Browser/Client | — | D-13/D-14/D-16: renders the payload the export response carries; session-only state |
| In-flight/locked state machine | Browser/Client | — | UI-SPEC: symmetric locking of export CTA + "Gerar novamente" |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| playwright (PyPI) | **1.62.0** (pinned; released 2026-07-31) | Headless Chromium `page.pdf()` — real embedded text layer | D-01 + STACK.md pin. **1.62.0 is the exact version whose bundled Chromium is v1234 — already downloaded in `%LOCALAPPDATA%\ms-playwright\chromium-1234` (probed via `playwright install chromium --dry-run`)**. Latest 1.63.0 would demand chromium-1243 (~170MB new download). Zero browser install on this machine. [VERIFIED: local dry-run probe + PyPI JSON] |
| pypdf | 6.19.0 (latest, 2026-09-16) | Parse-back text extraction (`PdfReader`, `extract_text`) | D-05: pure-Python, tiny wheel, no native deps. Probe-verified extraction fidelity on Chromium output. [VERIFIED: PyPI JSON + local probe] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| html.escape (stdlib) | — | Escape every interpolated string in the template builder | Always — LLM/profile text goes into HTML; server-side analogue of the JSX-only convention |
| unicodedata / casefold (stdlib) | — | Accent-preserving casefold for accent checks; `coverage._fold` for order/heading checks | Always |
| FastAPI `Response`/JSONModel | existing | Export endpoint envelope | Existing app |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Playwright 1.62.0 | Playwright 1.63.0 (latest) | ~170MB Chromium-1243 download for a patch-level bump; no feature this phase needs. Revisit at a later phase. |
| WeasyPrint 70.0 | (D-02 fallback) | Pure-Python install BUT native Pango via **MSYS2** (`pacman -S mingw-w64-ucrt-x86_64-pango` + PATH), Windows 10 64-bit only [CITED: doc.courtbouillon.org first_steps]. Real install friction vs Playwright's already-cached browser. Only if Playwright fails the gate (probe says it won't). |
| Jinja2 | Plain Python f-string builder with `html.escape` | One template, ~100 lines — a template engine buys nothing and adds a dep; house discretion explicitly prefers no new engine. (Legitimacy seam flagged jinja2 SUS anyway.) |
| Base64 JSON envelope | Raw `application/pdf` bytes + Content-Disposition | Bytes-on-success forces the frontend to branch on content-type and forces the self-check payload into a response header (h11 header-size risk) or a second request. Envelope keeps ONE content-type and the uniform `{status, erros}` path. ~45KB→~60KB on localhost: irrelevant. |

**Installation:**
```bash
cd backend
uv add "playwright==1.62.0" "pypdf>=6.19.0"
uv run playwright install chromium   # no-op on this machine (chromium-1234 cached); ~170MB on a new machine
```

**Version verification (this session):** PyPI JSON API: playwright latest 1.63.0 (2026-09-15), 1.62.0 (2026-07-31); pypdf 6.19.0 (2026-09-16); weasyprint 70.0 (2026-09-08). [VERIFIED: pypi.org/pypi/{pkg}/json]

## Package Legitimacy Audit

> Seam verdicts below come from `gsd-tools query package-legitimacy check --ecosystem pypi`. Both core packages were flagged **[SUS]** on heuristic signals only: "too-new" (recent publish date — i.e., actively maintained), "unknown-downloads" (PyPI JSON API provides no download counts at all — every PyPI package gets this flag), and for playwright "no-repository" (a checker read failure — the PyPI metadata repo is github.com/microsoft/playwright-python). Counter-evidence recorded per row; per protocol the planner should still gate installs behind a lightweight `checkpoint:human-verify`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| playwright | PyPI | 8+ yrs (Microsoft, 2020–) | ~2M/wk (PyPI stats sites) | github.com/microsoft/playwright-python | [SUS] (heuristic noise) | Approved — maintained by Microsoft, pinned in STACK.md (HIGH — official docs); planner adds cheap human-verify at install |
| pypdf | PyPI | ~10 yrs lineage (PyPDF2 renamed 2022) | ~1M/wk | github.com/py-pdf/pypdf (seam found repo OK) | [SUS] (too-new + unknown-downloads) | Approved — canonical pure-Python PDF lib, py-pdf org; planner adds cheap human-verify at install |
| weasyprint | PyPI | ~14 yrs (Kozea) | — | weasyprint.org / github.com/Kozea/WeasyPrint | [SUS] (too-new + unknown-downloads) | Fallback only — do NOT install unless the gate unexpectedly fails |
| jinja2 | PyPI | 20 yrs | — | github.com/pallets/jinja | [SUS] (unknown-downloads) | REMOVED — not needed (plain Python builder) |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** playwright, pypdf, weasyprint (heuristic noise — evidence above) → planner inserts `checkpoint:human-verify` before each `uv add` (verify `uv add` output + `uv run python -c "import playwright, pypdf"`).

## Architecture Patterns

### System Architecture Diagram

```
[Frontend: ResumeResult state (perfil + secoes + keywords + idioma)]
        │  POST /api/resume/exportar  (strict Pydantic body)
        ▼
[FastAPI sync def route ──── Starlette threadpool (no asyncio loop in thread)]
        │
        ▼
[render_resume_html()]  pure Python builder + html.escape  →  HTML string
        │
        ▼
[html_to_pdf()]  engine seam: sync_playwright → Chromium page.pdf() → bytes
        │                                   (WeasyPrint swap = this one function)
        ▼
[parse_back_check()]  pypdf extract_text → gate: contact first / heading order /
        │              company+title+dates co-occurrence / accent integrity
        │                    │
        │              FAIL ─┴─▶ {status:"erro", erros:[PT-BR naming check]}   (D-08)
        ▼ PASS
[self_check()]  ordem rows + keyword survival via coverage.keyword_in_text (D-15)
        │
        ▼
[200 envelope: {status:"ok", filename, pdf_base64, selfcheck}]
        │
        ▼
[Browser: base64→Blob→anchor download (D-11) + receipt + self-check panel (D-13/D-14)]
```

### Recommended Project Structure

```
backend/app/export/
├── __init__.py
├── render.py        # build_resume_html(perfil, secoes, datas_por_empresa, idioma) -> str — PURE, no deps
├── pdf.py           # html_to_pdf(html) -> bytes — THE ONLY playwright import (engine seam)
├── gate.py          # parse_back_check(pdf_bytes, expected) -> GateResult (pypdf; check functions pure)
└── selfcheck.py     # build_selfcheck(pdf_text, keywords, idioma) -> dict (reuses coverage.py)
backend/app/routes/export.py   # POST /api/resume/exportar — envelope + error contract
backend/tests/test_export_gate.py    # gate unit tests + session-scoped fixture PDF
backend/tests/test_export_api.py     # envelope/error contract (renderer stubbed) + 1 real render
frontend/src/api/client.ts           # + exportarCurriculo(): blob-path export (base64→Blob)
frontend/src/components/ExportZone.tsx      # CTA + receipt + error panel (UI-SPEC Zone 6)
frontend/src/components/SelfCheckPanel.tsx  # order rows + survival chips (KeywordsPanel mirror)
```

### Pattern 1: Engine seam preserves D-02's empirical decision

**What:** All Playwright usage lives in one function; template + gate are engine-agnostic (D-01 reversibility clause).
**When to use:** Always — this is what makes "build the gate first, choose the engine empirically" executable.
**Mechanics:** Template CSS stays conservative (block layout, no flex/grid/floats; declare BOTH the legacy `page-break-inside: avoid` and the standard `break-inside: avoid` — Chromium honors both, WeasyPrint reliably honors the legacy one) so WeasyPrint could render the identical HTML if ever needed.

### Pattern 2: Sync Playwright inside the sync `def` route (threadpool)

**What:** `sync_playwright()` requires a thread with NO running asyncio loop — it raises `RuntimeError("It looks like you are using Playwright Sync API inside the asyncio loop...")` otherwise [CITED: playwright docs/issues #480/#202].
**When to use:** The route MUST stay `def` (house pattern: routes/resume.py docstring, "NEVER async def" for blocking work) — Starlette dispatches it to the anyio threadpool where no loop exists.
**Critical:** launch **per request**, close in `finally`. The sync Playwright instance is not designed for reuse across different pool threads; per-request launch costs ~0.9s (probe) — irrelevant for a single user, and trivially correct.

### Pattern 3: The parse-back gate (SC2 mechanics)

**What:** Deterministic checks over `pypdf` extracted text, all comparisons on normalized text:
1. **Contact first** — folded(email) [or name] position < folded(first heading) position.
2. **Heading order** — the section list the template actually rendered (single source: same heading map used by `render.py`), each heading found at a monotonically increasing position. Use `coverage._fold` (casefold+NFKD) — VERIFIED necessary AND sufficient: Chromium applies CSS `text-transform: uppercase` before printing, so extracted text is "EXPERIÊNCIA", not "Experiência"; folding recovers the match in both languages (probe + fold probe both PASS).
3. **Co-occurrence** — per generated experience entry: company AND title (run language) AND date range all present within the section's index window (between the Experiência heading position and the next heading position). Dates come from a backend-side join: `perfil.experiences[].company` == `secoes.experiencias[].company` (casefold/strip) → render `start_date – end_date|atual`. No match → entry renders without dates and the gate's date check is skipped FOR THAT ENTRY (company+title still asserted). Field provenance: `Experience.start_date: str`, `end_date: str | None` [VERIFIED: backend/app/profile/models.py:111-112]; `ExperienciaGerada` has company/title/bullets only, no dates [VERIFIED: backend/app/llm/schemas.py:52-57].
4. **Accent integrity** — for every rendered string, the words containing non-ASCII characters must appear in the extracted text under **casefold-only** comparison (case-insensitive, accent-SENSITIVE — "EXPERIÊNCIA"=="experiência" but mojibake "EXPERIÃŠNCIA" fails) + a mojibake sentinel: no U+FFFD and no "Ã"/"â€" sequences. Exhaustive over resume-size content, not sampled.
**Fail behavior (D-08):** first failing check produces its PT-BR line ("Contato não encontrado no topo do PDF.", "Seção {X} fora de ordem no PDF.", "Empresa, cargo ou datas não extraídos juntos para {company}.", "Acentos corrompidos na camada de texto do PDF.") → `{status:"erro", erros:[...]}`; raw extracted text + detail to `logger.error` terminal-only.

### Pattern 4: Single-POST export envelope (D-11 + D-13)

**What:** One POST carries PDF bytes AND the self-check payload. Recommended contract:

```jsonc
// success (status 200)
{ "status": "ok",
  "filename": "curriculo-pt-BR-2026-09-27.pdf",
  "pdf_base64": "JVBERi0xLjQK...",
  "selfcheck": {
    // ids = frontend PREVIEW_SECTIONS keys (constants/ui.ts:57-65) + "contato" row
    "ordem": [ {"id": "contato", "ok": true}, {"id": "resumo", "ok": true}, {"id": "experiencia", "ok": true}, {"id": "formacao", "ok": true}, {"id": "habilidades", "ok": true} ],
    "sobrevivencia": [ {"canonical": "Python", "category": "competencias", "termo": "Python", "status": "coberto"} ],  // same shape as CoberturaItemDTO
    "gate": { "coocorrencia": true, "acentos": true }   // D-06 checks the panel doesn't show, surfaced in the footer line
  } }
// gate failure (status 200 — house envelope)
{ "status": "erro", "erros": ["Empresa, cargo ou datas não extraídos juntos para Acme Ltda."] }
```

Request body (strict, `extra="forbid"` — reuses existing Pydantic models directly):
`{ perfil: Profile, secoes: { resumo: str, experiencias: list[ExperienciaGerada], habilidades: list[str] }, keywords: list[Keyword], idioma: Literal["pt-BR","en"] }` — `Profile` [VERIFIED: backend/app/profile/models.py:153-165], `ExperienciaGerada`/`Keyword` [VERIFIED: backend/app/llm/schemas.py:28-33, 52-57]. Sending the DUMP means the displayed state travels verbatim (D-10). Validation failure = FastAPI 422 (house convention: malformed request is a client bug).

### Anti-Patterns to Avoid

- **async def route wrapping sync_playwright** — RuntimeError inside the running loop; also blocks the loop during the ~1s render. Keep `def`.
- **Module-level cached browser/shared sync instance across threads** — anyio pool threads differ per request; sync Playwright has per-thread state assumptions. Per-request launch/close is the correct cost/benefit here.
- **Matching extracted text without folding** — CSS `text-transform: uppercase` is applied in the text layer (probe-proven). Fold case for order/heading checks; keep accents (casefold-only) for integrity checks.
- **Byte-identical PDF fixtures** — assert LOGICAL properties (order, presence, co-occurrence), never `assert pdf_bytes == fixture_bytes`. Chromium output embeds timestamps/metadata.
- **layout_mode extraction** — `extract_text(extraction_mode="layout")` is slower and whitespace-quirky; plain mode already follows content-stream order = reading order for single-column output (probe).
- **Jinja2/string concatenation without escaping** — every interpolated value goes through `html.escape()`; LLM output is untrusted-shaped content even though it is the user's own data.
- **Logging pdf bytes or the base64 payload** — terminal noise; `runs.jsonl` stays LLM-call-only (CONTEXT integration contract).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text layer | reportlab/fpdf coordinate layout, canvas-to-PDF | Chromium `page.pdf()` | Raw layout libs lose the HTML/CSS fidelity of the reviewed montage and re-implement pagination badly; canvas has NO text layer (STACK.md: fatal) |
| Text extraction | regex over PDF bytes, pdftotext subprocess | pypdf `extract_text()` | Pure-Python, in-process, no external binary; probe-verified fidelity on this exact output |
| Accent folding / keyword matching | custom normalize + search | `coverage._fold` + `keyword_in_text` (D-15 locked reuse) | Already handles case+punctuation+NFKD with lookaround bounds that survive C++/C#/.NET (Phase 3, 15-row probe table) |
| Browser download plumbing | download-manager code | Blob + `URL.createObjectURL` + anchor click | 6 lines; native browser UI is the D-11 contract |
| Date formatting/i18n libraries | babel/luxon | Raw date strings as displayed in-app (`dateRange()` convention: `start – end|atual`) | D-10 display parity + gate matches the exact rendered strings |

**Key insight:** the gate is not generic PDF QA — it checks the exact properties SC2 names, on text the app itself rendered. Everything generic (extraction, folding, matching) already exists as a verified library or Phase 3 module.

## Common Pitfalls

### Pitfall 1: Sync Playwright vs the event loop
**What goes wrong:** `RuntimeError: It looks like you are using Playwright Sync API inside the asyncio loop` — or the async route freezes during render.
**Why:** sync Playwright owns a greenlet+loop pair; it cannot run where an asyncio loop already runs (Jupyter/FastAPI-async are the classic triggers) [CITED: github.com/microsoft/playwright-python issues #480, #202].
**How to avoid:** route stays `def`; render function synchronous; no `asyncio` anywhere in the export path.
**Warning signs:** any `async def exportar` in review; any `await` near `sync_playwright`.

### Pitfall 2: Browser binary version skew
**What goes wrong:** `Executable doesn't exist ... run playwright install` despite chromium being "installed".
**Why:** each playwright release pins ONE chromium revision (1.62.0→1234, 1.63.0→1243 — probed). A mismatched cache is invisible until launch.
**How to avoid:** pin `playwright==1.62.0` exactly; keep `uv run playwright install chromium` as the documented setup step (D-04); the launch-failure envelope (Pitfall 4) names the fix.
**Warning signs:** `uv lock` diff touching playwright without running the install step.

### Pitfall 3: CSS text-transform changes the extracted case
**What goes wrong:** heading assertions fail though the PDF looks right.
**Why:** the print pipeline applies the TRANSFORMED glyphs to the text layer (probe: source "Experiência" extracts as "EXPERIÊNCIA" — accent intact, case transformed).
**How to avoid:** fold case for every order/heading comparison; simplest template: write headings in final case, skip `text-transform` entirely.
**Warning signs:** exact-case `in` checks in gate tests.

### Pitfall 4: Chromium missing on a fresh checkout
**What goes wrong:** first export dies with an English Playwright stack trace.
**How to avoid:** catch launch/lookup errors at the route → envelope line "O navegador de renderização não está instalado. Execute `uv run playwright install chromium` e tente novamente." + raw detail terminal-only (D-08 house pattern). Same catch covers Playwright's `Error: Executable doesn't exist`.
**Warning signs:** tests that skip silently when chromium is absent — must fail loud instead (project test philosophy).

### Pitfall 5: pypdf whitespace/format artifacts
**What goes wrong:** co-occurrence checks flake on spacing/line breaks.
**Why:** PDF text positioning "makes it very hard to guarantee correct whitespaces" [CITED: pypdf docs, extract-text].
**How to avoid:** normalize once (`re.sub(r"\s+", " ", text)`) for ALL position math; search for distinctive tokens (email, company names, date ranges), never layout-dependent phrases.
**Warning signs:** assertions on multi-word sentences spanning line breaks.

### Pitfall 6: Forgetting the router order
**What goes wrong:** export route 404s behind the SPA mount.
**How to avoid:** `app.include_router(export_router)` in `main.py` BEFORE the StaticFiles mount (Pitfall 3/5 comment, main.py:16-27) [VERIFIED: backend/app/main.py:16-27].
**Warning signs:** only the export endpoint failing while `/api/resume/*` works.

### Pitfall 7: EN-run passthrough headings (design, not code)
**What goes wrong:** an otherwise-English PDF renders "Formação/Certificações" (in-app UI convention reuses PT-BR labels for passthrough sections — constants/ui.ts:133-137), failing the "genuinely sendable" bar and making EN canonical-heading checks incoherent.
**How to avoid:** the EXPORT template localizes ALL 7 headings by run language (pt map + en map, owned by render.py); the gate asserts against the same per-language map. Divergence from the in-app preview convention is presentation-only; content is untouched (D-10 honored). Surfaced as Assumption A2 for confirmation.

## Code Examples

### Verified probe — the whole loop, run on this machine this session (playwright 1.62.0 + cached chromium-1234 + pypdf 6.19.0)

```python
# Verified output (2026-09-27, Windows, backend venv):
# [timing] import=1.42s launch=0.88s render+pdf=0.72s close=0.13s total=3.15s
# [pdf] 32940 bytes, 1 page A4
# Extracted: "João Aparecido da Silva Júnior" → contact line with "·" →
#   RESUMO → EXPERIÊNCIA (uppercase from CSS, accent intact) → FORMAÇÃO → HABILIDADES
#   "Acme Tecnologia Ltda. — Engenheiro de Software Sênior" + "março de 2020 – atual"
#   "Python, C++, C#, .NET, CI/CD, Django, React"  ← special-char tokens verbatim
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

`page.pdf()` options verified against official docs: returns `bytes`; `format` defaults "Letter" (A0–A6 supported); `margin` sides default 0; `print_background` default False; `prefer_css_page_size` gives `@page` size priority; `tagged` (v1.42) generates an accessible/tagged PDF; default media is **print CSS**; `-webkit-print-color-adjust` forces exact colors [CITED: playwright.dev/python/docs/api/class-page]. `tagged=True` recommended — real heading structure helps some ATS parsers (cost: slightly larger file).

### Template skeleton (engine-agnostic, gate-friendly)

```css
@page { size: A4; margin: 1.6cm; }           /* + prefer_css_page_size=True */
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; }
section { break-inside: avoid; page-break-inside: avoid; }  /* Chromium + WeasyPrint */
/* block layout only — no flex/grid/floats (keeps WeasyPrint viable per D-02) */
```

```python
# render.py — every interpolation escaped; heading map is THE single source
# of truth shared with gate.py (order check) and selfcheck ordem rows.
HEADINGS = {
    "pt-BR": {"resumo": "Resumo", "experiencias": "Experiência", "formacao": "Formação",
              "habilidades": "Habilidades", "certificacoes": "Certificações",
              "idiomas": "Idiomas", "projetos": "Projetos"},
    "en":    {"resumo": "Summary", "experiencias": "Experience", "formacao": "Education",
              "habilidades": "Skills", "certificacoes": "Certifications",
              "idiomas": "Languages", "projetos": "Projects"},
}
def esc(s: str) -> str: return html.escape(s, quote=True)
```

### Gate core (reuses Phase 3 folding — quote from coverage.py:33-36)

```python
# [VERIFIED: backend/app/resume/coverage.py:33-41] — verbatim:
# def _fold(text: str) -> str:
#     """Casefold + NFKD accent-fold (drop combining marks) — both sides, once."""
#     decomposed = unicodedata.normalize("NFKD", text.casefold())
#     return "".join(ch for ch in decomposed if not unicodedata.combining(ch))
# def _term_pattern(term: str) -> re.Pattern:
#     return re.compile(r"(?<!\w)" + re.escape(_fold(term)) + r"(?!\w)", re.IGNORECASE)

def parse_back_check(pdf_bytes: bytes, expected: "ExpectedDoc") -> GateResult:
    text = "\n".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(pdf_bytes)).pages)
    flat = re.sub(r"\s+", " ", text)          # normalize whitespace once (Pitfall 5)
    folded = _fold(flat)                       # order/heading space
    casefolded = flat.casefold()               # accent-SENSITIVE space (integrity)
    # 1) contact first   2) headings monotonic (expected.sections from render.py map)
    # 3) per-entry company/title/dates within the Experiência→next-heading window
    # 4) every accented word of every rendered string in `casefolded` + no U+FFFD/"Ã"
    ...  # first failure -> (PT-BR line, raw detail for logger)
```

### Frontend blob download (no new deps)

```typescript
// client.ts — envelope type mirrors Pattern 4; tsc -b is the drift gate
export async function exportarCurriculo(payload: ExportarRequest): Promise<ExportarResponse> {
  const resp = await fetch('/api/resume/exportar', { method: 'POST',
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) throw new Error(`POST /api/resume/exportar falhou: ${resp.status}`)
  return (await resp.json()) as ExportarResponse
}
// component — on ok envelope:
const bytes = Uint8Array.from(atob(data.pdf_base64), c => c.charCodeAt(0))
const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }))
const a = Object.assign(document.createElement('a'), { href: url, download: data.filename })
a.click(); URL.revokeObjectURL(url)   // filename from backend = single source (D-11)
```

### Route skeleton (house envelope, sync def)

```python
@router.post("/api/resume/exportar")
def exportar_curriculo(payload: ExportarRequest) -> dict:
    try:
        html_doc = build_resume_html(payload.perfil, payload.secoes, payload.idioma)
        pdf_bytes = html_to_pdf(html_doc)                     # engine seam
        gate = parse_back_check(pdf_bytes, expected_from(payload, html_doc))
        if not gate.ok:
            logger.error("Gate de parse-back reprovou o export:\n%s", gate.raw)
            return {"status": "erro", "erros": gate.erros_ptbr}       # D-08
        selfcheck = build_selfcheck(pdf_bytes, payload.keywords, payload.idioma)
        return {"status": "ok",
                "filename": f"curriculo-{payload.idioma}-{date.today().isoformat()}.pdf",
                "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii"),
                "selfcheck": selfcheck}
    except ExportError as exc:                                # incl. chromium missing
        logger.error("Falha no export do PDF:\n%s", exc.raw)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| wkhtmltopdf / html-pdf | Chromium print-to-PDF (Playwright) | wkhtmltopdf archived (2023) | STACK.md already forbids; moot |
| PyPDF2 | pypdf (renamed successor, same org) | 2022 | Install `pypdf`, never `PyPDF2` (abandoned) |
| WeasyPrint GTK3 runtime installer on Windows | MSYS2 `pacman -S mingw-w64-ucrt-x86_64-pango` | docs switch (~2024, issue #2105) | Fallback path exists but is heavier than Playwright here [CITED: doc.courtbouillon.org] |
| Playwright untagged PDF | `tagged=True` accessible/tagged PDF | v1.42+ | Better ATS structure hints for free |
| Playwright 1.63.0 (2026-09-15) | 1.62.0 pin for chromium-1234 cache reuse | this research | ~170MB avoided on this machine; revisit later |

**Deprecated/outdated:** PyPDF2; wkhtmltopdf; WeasyPrint GTK3-installer instructions; `\b` regex boundaries for keyword matching (Phase 3 already bans them — coverage.py docstring).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Per-request Chromium launch (~0.9s + 0.7s render ≈ acceptable per export; no browser reuse needed for a single local user) | Architecture Pattern 2 | Low — worst case a future optimization (dedicated render thread); no correctness risk |
| A2 | Export template localizes ALL 7 headings by run language (diverging from the in-app convention of PT-BR passthrough labels in EN runs) | Pitfall 7 / Open Question 2 | Cosmetic-to-moderate: EN PDF with PT headings fails the "genuinely sendable" intent; needs user confirmation via planner checkpoint |
| A3 | Chromium + pypdf rendering/extraction are deterministic enough on fixed input that logical gate assertions (not byte equality) are stable across runs on this machine | Pattern 3 / Validation | Low — gate asserts order/presence, which are layout-structural, not rendering-incidental |
| A4 | `tagged=True` improves (or at least never harms) ATS parseability of this output | Code Examples | Low — worst case neutral; optional flag, trivially removable |
| A5 | WeasyPrint fallback viability (MSYS2 Pango path) is accurately characterized but NOT probed live (install not performed) | Standard Stack | Low — fallback only; if ever needed, D-02's gate re-runs empirically anyway |

## Open Questions

1. **Dates on generated experience entries (D-06 vs the D-05 montage)**
   - What we know: SC2/D-06 require company+title+**dates** co-occurring per experience, but the generated entries carry no dates (`ExperienciaGerada` = company/title/bullets [VERIFIED: schemas.py:52-57]) and the in-app montage renders none (ResumeResult.tsx:102-117). Profile experiences DO carry `start_date`/`end_date` [VERIFIED: models.py:111-112].
   - What's unclear: intended source of the PDF's dates.
   - Recommendation: backend-side join by casefolded company name between `perfil.experiences` and `secoes.experiencias`; render `start – end|atual` (raw strings, display parity); unmatched entries render dateless and the gate skips only the date sub-check for that entry. Planner should surface as a one-question checkpoint (cheap to confirm).

2. **EN-run heading language for passthrough sections** — see Assumption A2 / Pitfall 7. Recommendation: localize all headings in the export template (pt/en maps); confirm with user.

3. **Date format parity** — raw ISO-ish profile strings ("2022-03 – atual", matching the in-app `dateRange()` convention) vs locale-formatted ("março de 2020"). Recommendation: raw strings for display parity + exact gate matching; prettifying can come later as a pure template change.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | package management | ✓ | 0.12.5 | — |
| Python | backend | ✓ | 3.12.10 | — |
| Chromium (ms-playwright cache) | PDF rendering | ✓ | chromium-1234 + chromium_headless_shell-1234 (INSTALLATION_COMPLETE markers present) | `uv run playwright install chromium` (~170MB) on machines without the cache |
| playwright (PyPI pkg) | rendering | ✗ not yet in venv | pin 1.62.0 (~37MB wheel) | — |
| pypdf | gate | ✗ not yet in venv | ≥6.19.0 (pure Python) | — |
| Node | frontend | ✓ | 22.16.0 | — |
| MSYS2/Pango (WeasyPrint fallback only) | fallback engine | ✗ not installed | — | Only needed if Playwright fails the gate (probe says it won't); do NOT install preemptively |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** chromium download on machines without the cache (documented D-04 setup step).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (backend/pyproject.toml `[tool.pytest.ini_options]`, `addopts = -m 'not llm'` — offline default) |
| Config file | backend/pyproject.toml (exists) |
| Quick run command | `cd backend && uv run pytest tests/test_export_gate.py tests/test_export_api.py -x` |
| Full suite command | `cd backend && uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| REVIEW-02 | Gate passes on a real Chromium export, PT-BR | integration (session-scoped real render, offline) | `uv run pytest tests/test_export_gate.py::test_gate_passes_real_pdf[pt-BR] -x` | ❌ Wave 0 |
| REVIEW-02 | Gate passes on a real Chromium export, EN | integration | `...::test_gate_passes_real_pdf[en] -x` | ❌ Wave 0 |
| REVIEW-02 | Template = pure function: section order mirrors ResumeResult; all interpolations escaped | unit | `uv run pytest tests/test_export_gate.py::test_render_html -x` | ❌ Wave 0 |
| REVIEW-03 | Order check fails loud with named PT-BR line when headings shuffled | unit (synthetic text) | `...::test_order_failures -x` | ❌ Wave 0 |
| REVIEW-03 | Co-occurrence + accent checks (incl. mojibake rejection) | unit | `...::test_cooccurrence_and_accents -x` | ❌ Wave 0 |
| REVIEW-03 | Endpoint: gate failure → 200 `{status:"erro", erros:[...]}`; success → envelope with pdf_base64 + selfcheck | integration (renderer stubbed; 1 real-render case) | `uv run pytest tests/test_export_api.py -x` | ❌ Wave 0 |
| REVIEW-03 | Keyword survival via `keyword_in_text` on extracted PDF text, per language | unit | `...::test_survival_on_pdf_text -x` | ❌ Wave 0 |
| UI-SPEC copy | Singular/plural survival lines pure function | frontend pure-function contract (no JS runner — mirror `resumoCoberturaCopy` pattern) | manual review + tsc | n/a |

**Fixture strategy:** session-scoped pytest fixture renders the canonical test resume ONCE via the real engine (~3s) into module-level bytes; all gate tests consume those bytes — offline (local Chromium, zero network). If chromium is missing, the fixture **fails loud** with the PT-BR setup hint (never skip-silent). Synthetic-text unit tests cover all failure branches without any browser.

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_export_gate.py tests/test_export_api.py -x`
- **Per wave merge:** full backend suite `uv run pytest` + frontend `tsc -b`
- **Phase gate:** full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_export_gate.py` — REVIEW-02/REVIEW-03 gate + render unit tests + session PDF fixture
- [ ] `backend/tests/test_export_api.py` — envelope/error contract + real-render case
- [ ] `backend/app/export/` module skeleton (engine seam first, per D-02 sequencing)
- [ ] `uv add playwright==1.62.0 pypdf` + documented `uv run playwright install chromium` (no-op here) — with planner's human-verify checkpoint

*(Framework install: none needed — pytest already configured.)*

## Security Domain

`security_enforcement: true`, ASVS Level 1 (config.json). Localhost, no auth, no sessions, no crypto surface.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | localhost personal tool (PROJECT constraint) |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | single user, no multi-tenant surface |
| V5 Input Validation | **yes** | strict Pydantic `extra="forbid"` on ExportarRequest reusing validated models (`Profile`, `ExperienciaGerada`, `Keyword`); FastAPI 422 on malformed bodies (house convention) |
| V5.3 Output Encoding | **yes** | `html.escape()` on EVERY string interpolated into the export template — server-side analogue of the JSX-text-children convention; prevents profile/LLM text from injecting HTML into the rendered document |
| V6 Cryptography | no | no secrets handled; PDF is user's own data, never persisted server-side (bytes in memory only) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| HTML injection via profile/LLM text into the print template (broken layout, leaked tags into extracted text) | Tampering | `html.escape` at every interpolation; gate's accent/mojibake checks catch corrupted extractions |
| Unbounded export payload | DoS (minor, localhost) | Pydantic bounds mirroring existing limits (JD_MAX_LENGTH precedent); resume-size content is self-bounding |
| Verbose error leakage | Information Disclosure | house D-13/D-14 split: PT-BR line in envelope, raw detail terminal-only (D-08 extends it to the gate) |

## Sources

### Primary (HIGH confidence)
- **Local empirical probe (this session, target machine):** playwright 1.62.0 + cached chromium-1234 → `page.pdf` → pypdf extraction; order/accents/co-occurrence/uppercase-transform findings; timings 3.15s cold; `playwright install chromium --dry-run` revision mapping (1.62.0→1234, 1.63.0→1243)
- **PyPI JSON API (fetched 2026-09-27):** playwright 1.63.0/1.62.0 dates, pypdf 6.19.0, weasyprint 70.0
- **Codebase (Read this session):** backend/app/routes/resume.py (envelope + sync-def pattern); backend/app/resume/coverage.py (`_fold`, `keyword_in_text`); backend/app/llm/schemas.py (Keyword, ExperienciaGerada); backend/app/profile/models.py:88-165 (Experience dates, Profile); backend/app/main.py (router-before-mount); backend/pyproject.toml; frontend/src/api/client.ts (DTOs, fetch pattern); frontend/src/components/ResumeResult.tsx (montage order); frontend/src/constants/ui.ts (heading maps, chip semantics); backend/tests/conftest.py

### Secondary (MEDIUM-HIGH confidence)
- playwright.dev/python/docs/api/class-page — `page.pdf()` options/defaults, print media default, `tagged`, `set_content` semantics [CITED]
- playwright.dev docs + microsoft/playwright-python issues #480/#202 (via WebSearch) — sync API vs asyncio loop constraint [CITED]
- doc.courtbouillon.org/weasyprint/stable/first_steps.html (official docs, via WebSearch) — Windows MSYS2/Pango requirement, Windows 10 64-bit only [CITED]
- pypdf.readthedocs.io/en/stable/user/extract-text.html — extraction modes, whitespace/ligature limitations [CITED]

### Tertiary (LOW confidence — validated by probe where possible)
- WebSearch summaries for h11 header-size considerations (informed the envelope recommendation; recommendation does not rest on it alone)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pinned versions verified against PyPI; playwright pin chosen to match the already-downloaded browser revision (dry-run probed)
- Architecture: HIGH — every integration point read in-source; endpoint/envelope follows the shipped house pattern; engine seam is 3 functions
- Pitfalls: HIGH — Pitfalls 1–3 and 5 are probe-observed or doc-verified on this exact stack; 4/6/7 are established house patterns

**Research date:** 2026-09-27
**Valid until:** ~2026-10-27 (stable: pinned deps, no fast-moving surface; revisit only if playwright bumps the pin decision)
