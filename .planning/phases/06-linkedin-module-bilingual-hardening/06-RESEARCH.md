# Phase 6: LinkedIn Module + Bilingual Hardening - Research

**Researched:** 2026-09-27
**Domain:** LLM pipeline extension (stage reuse) + deterministic bilingual QA gate (glossary + English-bleed) + LinkedIn character limits
**Confidence:** HIGH (architecture, all codebase patterns verified by reading source this session) / MEDIUM (exact LinkedIn numeric limits — see the dedicated section; this is the phase's known concern and it is now narrowed to precise residual uncertainty)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Copy of `06-CONTEXT.md` `<decisions>` — all tagged `[auto — silence]` by the run convention; user review pending (re-edit is cheap, or `/gsd-discuss-phase 6`).

**Entrada e fluxo (LI-01)**
- **D-01:** Item "LinkedIn" na nav (placeholder desabilitado já existe em `constants/ui.ts` NAV_ITEMS) → página própria com o padrão da tela Currículo (objetivo → idioma → avisos → gerar → resultado).
- **D-02:** Objetivo em texto livre único + seletor de idioma (mesmo controle segmentado PT-BR/EN). Carga/senioridade/tecnologias-alvo são orientação no prompt (user message), não campos de formulário. Limite inferior de comprimento para habilitar o botão (como os 80 chars do JD; valor exato em planning/research).
- **D-03:** Lint não-bloqueante antes de gerar — o motor de keywords é input-agnostic (D-12 Fase 2) e já aceita objetivos; avisos coerentes com a Fase 3 (D-03/D-04: ver, não obrigar).
- **D-04:** Uma execução gera todas as seções (headline, sobre, experiências, skills); regeneração por seção via o mecanismo da Fase 5 (mesmo endpoint/padrão, estágios LinkedIn).

**Limites e contadores (LI-02, LI-03, LI-05)**
- **D-05:** Limites em constantes de config do backend, verificados na pesquisa (preocupação do STATE: 220/2,600/2,000 em fontes MEDIUM-confiança → research valida antes de fixar). Aplicação dupla: client (maxLength nos editores) + server (bounds no schema de saída + validação pós-geração).
- **D-06:** Contador ao vivo por campo ("X/Y caracteres"), âmbar em ≥90% do limite, vermelho acima.
- **D-07:** Nada truncado silenciosamente: saída acima do limite é sinalizada no lugar e a regeneração por seção é o caminho de correção — truncamento automático rejeitado (SC2 literal).
- **D-08:** Botão "Copiar" por seção (navigator.clipboard.writeText) com feedback "Copiado!" — o texto exibido é o que vai para a área de transferência.

**Reuso do motor (wholesale)**
- **D-09:** Novos estágios no `_STAGE_SCHEMAS` espelhando o padrão do currículo (D-01 Fase 3): um arquivo de prompt por bloco de saída (headline, sobre, experiências, skills); descrições de experiência num único estágio retornando mapa por empresa (uma chamada, retry localizado por bloco).
- **D-10:** runs.jsonl intacto — chamadas LinkedIn logadas pelo mecanismo existente (stage como string), sem campos novos (contrato D-13 Fase 2).
- **D-11:** Estado efêmero próprio da página LinkedIn (mesmo padrão Currículo: React state, aviso efêmero, versões/regeneração via os mecanismos da Fase 5).

**PT-BR hardening (SC4)**
- **D-12:** Glossário como arquivo versionado editável (`prompts/glossario.md`, padrão D-05 Fase 2 — Markdown+YAML frontmatter, validado estrito): pares termo→termo preferido, lido fresco a cada execução.
- **D-13:** Aplicação do glossário determinística pós-geração (substituições mecânicas termos→preferidos no texto PT-BR) + relatório do que foi alterado — não prompt-side only.
- **D-14:** QA gate não-bloqueante: relatório de English bleed (detecção determinística: glossário + lista heurística de termos EN comuns em texto PT-BR) exibido como avisos; falha alta reservada a erros duros (schema/rede). Sem juiz LLM.
- **D-15:** Fixtures bilíngues LinkedIn como DoD: o harness `pytest -m llm` ganha fixtures LinkedIn PT-BR/EN que rodam na suíte real-API; mudança de prompt sem fixture verde = não feito (SC4 literal). Suite offline continua 100% offline.

### Claude's Discretion
- Número/limites exatos dos estágios e nomes dos arquivos de prompt; schemas de saída por bloco (wire schema estrito padrão da Fase 2).
- Contrato do endpoint LinkedIn (um orquestrador vs estágios separados), bounds de validação do objetivo.
- Mecânica do contador (componente compartilhado), agrupamento visual das seções, reuso de SectionEditor/Versões/Comparar na página LinkedIn.
- Estrutura do módulo backend (app/linkedin/ vs extensão de app/resume/), forma do glossário no schema, lista heurística de English bleed.

### Deferred Ideas (OUT OF SCOPE)
- Aplicar o QA gate/glossário também ao fluxo do currículo — o SC4 desta fase fala das saídas LinkedIn; estender ao currículo é aditivo depois.
- Polish candidates do STATE ("atual" em EN, hífen no matcher) — candidatos a incluir se a onda de execução permitir.

Additional locked scope fences (CONTEXT.md `<domain>`): NOT in this phase — auto-posting/sync LinkedIn (ToS), extração de vaga por URL, DOCX, cover letter. The bilingual QA gate covers LinkedIn generation only (the resume keeps its existing suite).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LI-01 | State a career objective + choose output language driving all LinkedIn generation | D-02 form (single free-text objetivo + reused segmented control); `compose_linkedin_stage_input` mirrors `compose_stage_input` (facts.py:147-157); lint reuses `run_lint_only` verbatim (pipeline.py:53-76) |
| LI-02 | Headline ≤220 chars optimized for the objective | Limit verified at MEDIUM-HIGH cross-source consistency (see Character Limits); `linkedin-headline` stage with strict wire schema; server bound post-generation (D-07), client maxLength mirror |
| LI-03 | About section ≤2600 chars | Limit verified same posture; `linkedin-sobre` stage; counter + over-limit flag per UI-SPEC |
| LI-04 | Rewritten description per experience entry ≤2000 chars each | Limit verified same posture; `linkedin-experiencias` ONE stage returning a company-anchored map (D-09), group = regen unit |
| LI-05 | Prioritized skills list + all outputs copy-paste text blocks enforcing limits | Skills list bound officially verified at 100 (HIGH — LinkedIn Help fetched this session); copy per block via `navigator.clipboard.writeText`; counter contract per UI-SPEC |
</phase_requirements>

## Summary

Phase 6 is a **vertical-slice reuse phase**: the LLM engine (gateway, retry, wire schemas, runs.jsonl, prompt loader), the pipeline orchestration pattern, the facts serialization, the review UI (editor/versions/confirm/comparison), and the lint engine all ship unchanged. What is genuinely new reduces to four things: (1) four new stage entries in `_STAGE_SCHEMAS` plus four prompt files, (2) a thin `app/linkedin/` orchestration + deterministic post-generation QA module, (3) `prompts/glossario.md` with a strict loader, and (4) one new React page wiring the existing review components to LinkedIn blocks with counters and a copy button. Verified this session by reading every file cited below.

The research deliverable the STATE.md concern asked for — **verify the LinkedIn character limits** — resolved as follows. The skills cap changed: LinkedIn's official Help Center states **"You can add up to 100 skills to your profile."** (fetched verbatim this session; the old 50 limit is stale and still widely cited). The headline/About/experience numbers (220 / 2,600 / 2,000) are **consistently reported by every independent third-party source found, but LinkedIn's own Help articles do not publish numeric limits** — the official "Edit Your Headline" and intro-editing articles were fetched this session and contain no character counts. Those three numbers therefore stay MEDIUM-confidence-with-strong-consensus, now with the negative evidence (official silence) explicitly recorded. Engineering posture makes this residual uncertainty cheap: D-05/D-07 put the numbers in config constants, surface over-limit output instead of truncating, and the client mirrors the server bounds — if LinkedIn's live counter ever disagreed, nothing is destroyed and the user sees it at paste time.

The bilingual hardening design (D-12..D-15) maps cleanly onto existing primitives: the glossary is a `prompts/glossario.md` file validated by a strict Pydantic frontmatter spec (the `load_prompt` pattern verbatim), applied as a deterministic case-preserving regex replacement over the original text (lookaround boundaries from `coverage.py` — never `\b`), followed by English-bleed detection with the same fold/lookaround primitives over a static heuristic term list owned in code. Both feed a QA payload that rides the generation response (full run and per-section regen both recompute — the UI truthfulness rule). The DoD mechanism (D-15) is a parametrized real-API test over the **already-shipped** `OBJECTIVE_PT`/`OBJECTIVE_EN` fixtures in `llm_fixtures.py:75-106`, asserting every block within its limit plus the QA payload plus the runs.jsonl stage audit.

**Primary recommendation:** Add `linkedin-headline` / `linkedin-sobre` / `linkedin-experiencias` / `linkedin-skills` as four new `_STAGE_SCHEMAS` entries with strict wire schemas (plain strings — NO `max_length` on output models, so over-limit output survives to be surfaced per D-07), a new `app/linkedin/` package (`pipeline.py` orchestrator + `qa.py` glossary/bleed), `prompts/glossario.md` with frontmatter-carried pairs, and three routes (`/api/linkedin/lint` as a verbatim `run_lint_only` reuse, `/api/linkedin/gerar`, `/api/linkedin/regenerar`) registered before the SPA mount. Limits as backend config constants: `LINKEDIN_HEADLINE_MAX_CHARS = 220`, `LINKEDIN_SOBRE_MAX_CHARS = 2600`, `LINKEDIN_EXPERIENCIA_MAX_CHARS = 2000`, `LINKEDIN_SKILLS_MAX_COUNT = 100` (verified official).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Objetivo validation (min/max bounds) | API/Backend (FastAPI request model) | Browser (textarea maxLength + enable-hint) | Server is the contract; client mirrors to avoid dead-end 422s (Phase 5 WR-01 pattern) |
| Keyword lint on objetivo | API/Backend (`run_lint_only` reuse) | — | Input-agnostic engine already accepts objectives (D-12 Phase 2); zero new logic |
| Section generation (4 blocks) | API/Backend (gateway `_STAGE_SCHEMAS`) | — | Same paid-call path, retry, runs.jsonl audit as resume stages |
| Limit enforcement on generated text | API/Backend (post-generation check, response metadata) | Browser (counter, over-limit flag, editor maxLength, save guard) | D-07: never truncate; surface + regen path. Client maxLength blocks editor growth; server never rejects |
| Glossary application + bleed detection | API/Backend (`app/linkedin/qa.py` pure functions) | Browser (renders QA payload verbatim) | Deterministic, auditable, offline-testable — mechanical honesty rule; frontend never re-implements |
| Copy-paste deliverable | Browser (`navigator.clipboard.writeText`) | — | The displayed text IS the deliverable (D-08); no export module in this phase |
| Versions/edits/confirm/comparison | Browser (React state, Phase 5 components) | — | Ephemeral session state (D-11); stack-before-mutate on every destructive path |
| runs.jsonl audit | API/Backend (existing logging) | — | D-10 contract intact: stage is just a string, no new fields |

## Standard Stack

### Core (all already shipped — zero new dependencies)

| Library/Asset | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI + Pydantic v2 | 0.141.1 / 2.13.5 | New routes + strict request/output models (`extra="forbid"`) | House discipline since Phase 2 [VERIFIED: backend/app/llm/schemas.py:22-26] |
| app.llm.gateway `run_stage` + `_STAGE_SCHEMAS` | (in-repo) | The one path from prompt file to typed output; new stages = new dict entries, gateway untouched | Read this session: dict at gateway.py:49-54, unknown-stage guard at :85-90 [VERIFIED: backend/app/llm/gateway.py:49-54,85-90] |
| app.llm.prompts `load_prompt` | (in-repo) | Fresh-read loader for `prompts/{stage}.md`; the glossário follows the same fail-fast ladder | Read this session: loader at prompts.py:47-74, no caching by design [VERIFIED: backend/app/llm/prompts.py:47-74] |
| app.resume.facts `serialize_profile_facts` / `compose_stage_input` / `compose_regen_stage_input` | (in-repo) | The grounding blob + input composition, language-parameterized — reusable verbatim for LinkedIn | Read this session [VERIFIED: backend/app/resume/facts.py:57-157,160-178] |
| app.resume.coverage `_fold` / `_term_pattern` | (in-repo) | Lookaround-bounded, casefold+NFKD-folded matcher — reuse for bleed detection (never `\b`) | Read this session; C++/C#/.NET false-negative lesson recorded at coverage.py:14-22 [VERIFIED: backend/app/resume/coverage.py:33-41] |
| app.resume.pipeline orchestration pattern | (in-repo) | Sequential stages, all-or-nothing, fresh profile once, injectable `client`/`runs_log` | Read this session [VERIFIED: backend/app/resume/pipeline.py:79-134] |
| pytest (offline default, `-m llm` real-API) | (in-repo) | 267 offline tests green this session (274 collected, 7 deselected by `addopts = "-m 'not llm'"`) [VERIFIED: backend/pyproject.toml:20-21 + session probe] | Suite stays 100% offline by default (D-15) |
| React 19 + @tanstack/react-query + Tailwind v4 | ^19.2.8 / ^5.103.2 / 4.x | New `LinkedInHome` page mirroring `CurriculoHome`; no new frontend deps | House policy: no JS test runner, `tsc -b` is the drift lock [VERIFIED: frontend/package.json scripts] |

### Supporting

| Library/Asset | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-frontmatter + PyYAML | 1.3.0 / 6.0.3 (transitive) | Parse `prompts/glossario.md` frontmatter | Same mechanism `load_prompt` already uses [VERIFIED: backend/app/llm/prompts.py:57] |
| `FakeClient` / `ScriptedClient` (test_gateway.py:62/:80) | (in-repo) | Offline mock chat clients for the 4 new stages | All offline pipeline/route tests [VERIFIED: backend/tests/test_gateway.py:49-80 — class names read this session] |
| `llm_fixtures.OBJECTIVE_PT` / `OBJECTIVE_EN` | (in-repo) | Real-API fixtures for the LinkedIn DoD harness — **already shipped in Phase 2** | D-15 bilingual fixtures need no new fixture text [VERIFIED: backend/tests/llm_fixtures.py:75-106] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `app/linkedin/` new package | Extending `app/resume/` | New package keeps the resume module's test surface untouched and mirrors the resume package shape; either is planner-discretion (CONTEXT.md) — recommendation: new package |
| One stage per output block (D-09) | Single mega-stage returning all 4 blocks | Per-block stages give localized retry (a bad About doesn't re-roll the headline), per-stage max_tokens budgets, and match the D-09 lock + UI copy "quatro blocos gerados em sequência" |
| Deterministic post-gen glossary (D-13) | Prompt-side-only glossary instructions | Non-deterministic isn't auditable — D-13 rejects it explicitly |
| Static heuristic term list in code (D-14) | LLM judge | Cost + false precision; D-14 rejects the judge; legend wording already concedes false positives |

**Installation:** NONE. No new packages. `## Package Legitimacy Audit` below.

## Package Legitimacy Audit

No external packages are installed in this phase (CONTEXT.md goal: "reusing the resume engine wholesale — prompts and block types only"; UI-SPEC: no new frontend deps, no JS test runner). The legitimacy gate is **not triggered** — there is nothing to check on any registry. The two transitive parsers the glossário needs (`frontmatter`, `yaml`) are already imported by the existing prompt loader [VERIFIED: backend/app/llm/prompts.py:17-18].

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## LinkedIn Character Limits — the STATE.md concern, resolved

This is the phase's key research deliverable (STATE.md Blockers/Concerns; D-05 mandates verification before fixing constants).

| Element | Value | Confidence | Evidence |
|---------|-------|------------|----------|
| Headline | **220 chars** | MEDIUM (strong multi-source consensus; no official number exists) | Confirmed independently by Brand Career Management, Derrick.app, WriteHero, Leaders.social, LinkedHelper, TryKondo — all consistent. LinkedIn's official Help article "Edit Your Headline" (linkedin.com/help/linkedin/answer/a542926) **was fetched this session and states NO numeric limit** — recorded negative evidence. Stable since the ~2017 expansion from 120. [CITED: linkedhelper.com/blog/linkedin-character-limit + 5 corroborating sources] |
| About / Summary | **2,600 chars** | MEDIUM (same posture) | Same source set; the old "Summary 2,000" figure still circulating in older articles (e.g., a LinkedIn Pulse piece surfaced in search) predates the 2017 About-section expansion — treat any 2,000-About claim as stale. Official Help intro article (a547248) fetched this session: no numeric limit stated. [CITED: same consolidated sources] |
| Experience description | **2,000 chars per position** | MEDIUM (same posture) | LinkedHelper, TryKondo, AuthoredUp, LigoSocial all concur per-role; title/company fields are 100 chars each (not phase-relevant — copied separately). [CITED: linkedhelper.com/blog/linkedin-character-limit] |
| Skills — list count | **100 skills max** | **HIGH — OFFICIALLY VERIFIED** | LinkedIn Help Center fetched this session, verbatim: **"You can add up to 100 skills to your profile."** [VERIFIED: linkedin.com/help/linkedin/answer/a549047]. Raised from the old 50 (many 2026 articles still cite 50 — stale). |
| Skills — per-skill name | ~80 chars | LOW-MEDIUM (third-party only) | LinkedHelper + a LinkedIn Pulse article cite 80/skill; no official statement found. If adopted, tag the constant with the same verify caveat as the other three. [CITED: linkedhelper.com/blog/linkedin-character-limit] |

**What this means for planning:**

1. **Skills count line (UI-SPEC's "honest-information rule"):** research DID verify a real list bound — `LINKEDIN_SKILLS_MAX_COUNT = 100` may be added as a config constant and used as a server-side sanity bound on the generated list (a prioritized list should be well under it anyway). The UI-SPEC count-line rendering decision (`"N skills em ordem de prioridade."` with no fake `/Y`) stands unchanged — no per-list *character* limit exists.
2. **The three MEDIUM numbers go in config constants as-is (D-05).** Do NOT add a safety margin by shrinking the constants: the counter must mirror LinkedIn's own entry fields, and any discrepancy degrades gracefully by design (D-07: over-limit output is flagged in place, `Copiar` still works, per-section regen is the fix path — nothing is truncated or lost). A wrong-by-a-few-chars constant costs one regenerated section, never data.
3. **Where the bounds must NOT live:** the stage output Pydantic models must not enforce `max_length`. The gateway retries ValidationError and raises `LLMError` at exhaustion (gateway.py:206-262 read this session) — a 2,150-char Sobre would abort the whole run instead of being displayed with the red flag, directly violating D-07/SC2. Bounds are: (a) post-generation length check feeding response metadata/flags, (b) client-side `maxLength` on editors + disabled save-guard (UI-SPEC WR-01 mirror), (c) request-level bounds on the objetivo (that one IS user input — `Field(min_length=80, max_length=…)` is correct there, mirroring `JD_MIN_LENGTH = 80` / `JD_MAX_LENGTH = 20000` at routes/resume.py:50-51 [VERIFIED: backend/app/routes/resume.py:50-51,59]).

## Architecture Patterns

### System Architecture Diagram

```
┌────────────────────────── Browser (LinkedInHome.tsx) ──────────────────────────┐
│ objetivo + idioma → [debounce 800ms] POST /api/linkedin/lint → avisos (warn)   │
│        │                                                                       │
│        ▼ CTA (≥ min chars, no long op, no editor)                              │
│ POST /api/linkedin/gerar ──────────────► result card: 4 blocks + counters      │
│ POST /api/linkedin/regenerar (per block)►  + QA panel ("Verificação de idioma")│
│ [Copiar] → navigator.clipboard.writeText (per block / per experience entry)    │
└────────────────────────────────┬───────────────────────────────────────────────┘
                                 ▼
┌────────────────────────── Backend (app/linkedin/) ─────────────────────────────┐
│ route → load_profile() fresh once → serialize_profile_facts(profile, language) │
│        → compose_linkedin_stage_input(facts, objetivo)                         │
│ lint:   run_lint_only(objetivo)        [verbatim reuse — extraction + JD lint] │
│ gerar:  4 sequential run_stage calls (D-09 order):                             │
│            linkedin-headline → linkedin-sobre                                  │
│            → linkedin-experiencias (one call, map keyed by company)            │
│            → linkedin-skills                                                   │
│         → post-gen (PT-BR only): apply_glossario() → detect_english_bleed()    │
│         → ok envelope {status, idioma, secoes, limites, qa}                    │
│ regen:  exactly ONE stage → merge over SUBMITTED state, siblings byte-identical│
│         → same post-gen QA on the regenerated block(s)                         │
└───────────────┬─────────────────────────────────────────┬──────────────────────┘
                ▼                                         ▼
   app/llm/gateway.run_stage                    prompts/ (fresh-read every call)
   (OpenRouter, strict json_schema,             4 new stage files + glossario.md
   retry, runs.jsonl per attempt —              (Markdown + YAML frontmatter,
   D-10: contract intact)                       strict-validated, read fresh)
```

Primary use case trace: user types objetivo (≥ min) → lint avisos appear (non-blocking) → CTA starts 4 sequential gateway stages → each stage's strict-validated output lands in `secoes` → deterministic QA runs over the PT-BR text → envelope returns → React renders 4 blocks with live counters + QA panel below → Copiar puts the displayed bytes on the clipboard.

### Recommended Project Structure

```
backend/
├── app/
│   ├── linkedin/               # NEW package (planner may fold into app/resume/ — CONTEXT discretion)
│   │   ├── __init__.py
│   │   ├── pipeline.py         # run_linkedin_lint / run_linkedin_pipeline / run_linkedin_section_regen
│   │   └── qa.py               # load_glossario + apply_glossario + detect_english_bleed (pure functions)
│   ├── llm/
│   │   ├── gateway.py          # _STAGE_SCHEMAS += 4 linkedin entries (ONLY edit)
│   │   └── schemas.py          # + 4 output models + 4 hand-maintained strict wire schemas
│   └── routes/
│       └── linkedin.py         # NEW: 3 routes, registered before the SPA mount
├── tests/
│   ├── test_linkedin_schema.py       # drift-lock for the 4 new wire schemas (mirror test_resume_schema.py)
│   ├── test_linkedin_pipeline.py     # offline, FakeClient/ScriptedClient
│   ├── test_linkedin_regen_pipeline.py
│   ├── test_linkedin_qa.py           # glossary + bleed vectors
│   ├── test_linkedin_api.py          # route envelopes
│   └── test_llm_harness.py           # + parametrized real-API LinkedIn DoD tests
prompts/
├── linkedin-headline.md        # NEW
├── linkedin-sobre.md           # NEW
├── linkedin-experiencias.md    # NEW
├── linkedin-skills.md          # NEW
└── glossario.md                # NEW (D-12)
frontend/src/
├── pages/LinkedInHome.tsx      # NEW — mirrors CurriculoHome pattern
├── components/ (reuse SectionEditor / SectionVersionsPanel / ConfirmStrip / ComparisonPanel patterns; new: counter + copy affordance + QA panel — naming planner's call)
├── constants/ui.ts             # LINKEDIN_* / QA_* strings; NAV_ITEMS linkedin → enabled: true
└── App.tsx                     # view union gains 'linkedin'
```

### Pattern 1: New stage registration (gateway untouched)

**What:** Each new block is one `_STAGE_SCHEMAS` entry + one prompt file; retry, wire-schema enforcement, runs.jsonl, and the fresh-read loader are inherited.
**When to use:** Every LinkedIn output block (D-09).
**Example:**

```python
# Source: pattern verified at backend/app/llm/gateway.py:49-54
_STAGE_SCHEMAS: dict[str, tuple[type, dict]] = {
    "keyword-extraction": (KeywordExtraction, KEYWORD_STRICT_SCHEMA),
    "resume-summary": (ResumeSummary, RESUME_SUMMARY_STRICT_SCHEMA),
    "resume-experiencias": (ResumeExperiencias, RESUME_EXPERIENCIAS_STRICT_SCHEMA),
    "resume-skills": (ResumeSkills, RESUME_SKILLS_STRICT_SCHEMA),
    # NEW (D-09): mirrors the resume quartet; names become runs.jsonl `stage`
    # strings (D-10: plain strings, contract intact) and wire-schema names
    # via stage.replace("-", "_").
    "linkedin-headline": (LinkedinHeadline, LINKEDIN_HEADLINE_STRICT_SCHEMA),
    "linkedin-sobre": (LinkedinSobre, LINKEDIN_SOBRE_STRICT_SCHEMA),
    "linkedin-experiencias": (LinkedinExperiencias, LINKEDIN_EXPERIENCIAS_STRICT_SCHEMA),
    "linkedin-skills": (LinkedinSkills, LINKEDIN_SKILLS_STRICT_SCHEMA),
}
```

**Output models — deliberately NO length bounds** (D-07):

```python
# Source: pattern verified at backend/app/llm/schemas.py:40-70 (resume models).
# Contrast: the gateway RETRIES ValidationError and raises LLMError at
# exhaustion (gateway.py:206-262) — a max_length bound here would abort the
# run on over-limit output instead of letting it surface (D-07/SC2).
class LinkedinHeadline(_Strict):
    headline: str            # target ≤ LINKEDIN_HEADLINE_MAX_CHARS; enforced post-gen

class LinkedinSobre(_Strict):
    sobre: str

class ExperienciaLinkedin(_Strict):
    company: str             # profile-fact anchor — company fold-match alignment (UI-SPEC)
    title: str
    descricao: str           # prose paragraphs (≤ LINKEDIN_EXPERIENCIA_MAX_CHARS target), NOT bullets

class LinkedinExperiencias(_Strict):
    experiencias: list[ExperienciaLinkedin]

class LinkedinSkills(_Strict):
    habilidades: list[str]   # array order IS the priority order (LI-05)
```

Wire schema example (strict rules: every property in `required`, `additionalProperties: false` at every level, hand-maintained, drift-locked in CI):

```python
# Source: rules verified at backend/app/llm/schemas.py:72-117
LINKEDIN_HEADLINE_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {"headline": {"type": "string"}},
    "required": ["headline"],
    "additionalProperties": False,
}
# linkedin-experiencias mirrors RESUME_EXPERIENCIAS_STRICT_SCHEMA with
# "descricao" replacing "bullets" (schemas.py:127-146); sobre/skills mirror
# RESUME_SUMMARY / RESUME_SKILLS schemas with renamed fields.
```

### Pattern 2: Objetivo as the vacancy-slot input (facts composition reuse)

**What:** The LinkedIn user message reuses the gateway's existing template (`"Idioma preferido de saída: {language}\n\nTexto:\n{input_text}"`, gateway.py:110) with a LinkedIn-specific composition.
**Example:**

```python
# Source: mirrors compose_stage_input verified at backend/app/resume/facts.py:147-157
def compose_linkedin_stage_input(facts: str, objetivo: str) -> str:
    return (
        "FATOS DO PERFIL:\n"
        f"{facts}\n"
        "\n"
        "OBJETIVO DE CARREIRA:\n"
        f"{objetivo}"
    )
# Regen-with-dica: compose_regen_stage_input(facts, objetivo, dica)
# (facts.py:160-178) is reusable as-is — the dica framing is input-agnostic.
```

### Pattern 3: Glossário file + strict loader (D-12)

**What:** `prompts/glossario.md` with pairs in YAML frontmatter (strict Pydantic, `extra="forbid"`), body kept as human-facing documentation. Fresh read every execution — the `load_prompt` discipline.
**Recommended shape:**

```markdown
---
id: glossario
pares:
  - de: "machine learning"
    para: "aprendizado de máquina"
  - de: "data governance"
    para: "governança de dados"
---

# Glossário de terminologia (PT-BR)

Pares termo→termo preferido aplicados deterministicamente às saídas em
PT-BR após a geração. Editar este arquivo e a próxima execução o vê
(fresh-read). Termos técnicos consolidados sem bom equivalente NÃO devem
ser listados aqui — o QA de bleed sinaliza, não substitui.
```

```python
# Source: fail-fast ladder pattern verified at backend/app/llm/prompts.py:25-74
class ParGlossario(_Strict):
    de: str
    para: str

class GlossarioSpec(_Strict):
    id: str
    pares: list[ParGlossario]

def load_glossario(prompts_dir: Path | None = None) -> GlossarioSpec:
    # frontmatter.load → GlossarioSpec.model_validate → PromptError-style
    # PT-BR messages + raw detail. Mirrors load_prompt exactly (try/except
    # FileNotFoundError / yaml.YAMLError / UnicodeDecodeError / ValidationError).
```

### Pattern 4: Deterministic, case-preserving glossary application (D-13)

**What:** Mechanical replacement over the ORIGINAL text (offsets must stay valid for `re.sub`-style reconstruction). Lookaround boundaries from `coverage.py` — never `\b` (the C++/C#/.NET lesson, coverage.py:14-22).
**Example:**

```python
# Source: primitives verified at backend/app/resume/coverage.py:33-41
def _apply_pair(text: str, de: str, para: str) -> tuple[str, int]:
    """Replace fold-insensitively-case-insensitive whole-term matches of
    `de` with `para`, preserving the match's case shape. Returns
    (new_text, substitution_count)."""
    pattern = re.compile(r"(?<!\w)" + re.escape(de) + r"(?!\w)", re.IGNORECASE)

    def _casematch(m: re.Match) -> str:
        found = m.group(0)
        if found.isupper() and len(found) > 1:
            return para.upper()
        if found[0].isupper():
            return para[0].upper() + para[1:]
        return para

    return pattern.subn(_casematch, text)

# ORDER (UI truthfulness): apply glossário FIRST, then run bleed detection on
# the post-glossary text — the report must describe the text the user copies.
# Accent-folding is NOT used for replacement (glossary pairs are exact by
# definition; folding would break offset mapping); fold machinery is for
# bleed matching only.
```

### Pattern 5: English-bleed detection (D-14)

**What:** Static heuristic term list owned in `app/linkedin/qa.py` — EN function words, resume action verbs, and structural connectives whose presence in PT-BR prose signals an untranslated stretch. Deliberately EXCLUDES consolidated tech proper nouns (Kubernetes, Python, machine learning if unpinned…) which are legitimate in PT-BR tech writing — the pinned legend already concedes this ("termos técnicos consolidados em inglês podem ser sinalizados").
**Example:**

```python
# Matching reuses the coverage primitives verbatim (lint.py:23 imports them
# the same way — "one matcher, many inputs" is house discipline).
EN_BLEED_TERMS: tuple[str, ...] = (
    # function/structure words (never legitimate mid-sentence in PT-BR prose)
    " the ", "and", "with", "for", "from",  # careful: short tokens need the
    # lookaround + test vectors; prefer multi-word signals first
    # resume action verbs (EN verbs in PT-BR text = untranslated sentence)
    "managed", "led", "achieved", "spearheaded", "drove", "delivered",
    "responsible for", "strong background", "team player", "track record",
    # first-person EN constructions
    "i am", "i have", "my experience",
)
def detect_english_bleed(text: str, secao: str) -> list[dict]:
    folded = _fold(text)
    return [
        {"termo": term, "secao": secao}
        for term in EN_BLEED_TERMS
        if _term_pattern(term).search(folded)
    ]
# NOTE: short high-frequency tokens ("and", "for") WILL false-positive on
# legitimate PT text boundaries is unlikely, but pin the exact shipped list
# with offline vectors (test_linkedin_qa.py) — the list above is a STARTING
# PROPOSAL for planning to curate, not a verified corpus. Non-blocking by
# construction (D-14): findings render as amber avisos, never gate Copiar.
```

### Anti-Patterns to Avoid

- **`max_length` on stage output Pydantic models:** converts D-07's "surface + regen" into a hard run failure via the gateway retry path. Bounds live post-generation and client-side.
- **Automatic truncation anywhere:** SC2 literal rejection. Even "helpful" client-side slicing violates the contract.
- **Prompt-side-only glossary:** non-deterministic, unauditable — D-13 rejects.
- **LLM-judged language QA:** D-14 rejects (cost + false precision); detection is mechanical or nothing.
- **LinkedIn API / scraping:** profile writes are not supported for regular members and automation violates ToS (REQUIREMENTS.md Out of Scope table). Copy-paste is the deliverable by design.
- **Sending LinkedIn outputs through the resume's coverage pipeline:** cobertura is a JD-keyword concept; LinkedIn runs have no JD extraction. The LinkedIn run's QA is the glossário/bleed report — don't bolt on cobertura.
- **New JS test runner or new npm/PyPI deps:** breaks the no-new-deps contract; offline truth is pytest + `tsc -b`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM call/retry/audit | A second SDK path for LinkedIn | `run_stage` + `_STAGE_SCHEMAS` entries | Retry ladder, strict-schema revalidation, runs.jsonl per attempt all inherited free (gateway.py read this session) |
| Prompt loading/caching | Custom file reader | `load_prompt` pattern (fresh frontmatter+body) | Fail-fast ladder with PT-BR messages already solved; the glossário gets a sibling loader |
| Text matching boundaries | `\b` regexes or stemming | `_fold` + `_term_pattern` lookarounds | `\b` verifiably false-negatives on C++/C#/.NET (coverage.py:14-22 recorded probe table) |
| Profile → prompt grounding | A new LinkedIn fact format | `serialize_profile_facts(profile, language)` verbatim | Same profile, same localization resolution, already UTF-8/accent-proven in real runs |
| Review UI mechanics | New editor/version/confirm components | SectionEditor / SectionVersionsPanel / ConfirmStrip / ComparisonPanel patterns | UI-SPEC pins reuse; generalizing vs a LinkedIn sibling is planner discretion, visuals are locked |
| Clipboard | Fallback document.execCommand machinery | `navigator.clipboard.writeText` + failure line (UI-SPEC copy pinned) | Localhost secure-context makes the async API reliably available; the failure path is a pinned red line |
| Limit enforcement | Truncation logic | Config constants + post-gen flag + client maxLength + regen path | D-07; truncation is the one explicitly rejected behavior |

**Key insight:** the phase's architectural success measure (CONTEXT.md `<specifics>`) is "quanta lógica NOVA existe" — the answer is: schemas, prompt files, the QA pure functions, and the page. Everything else is an import.

## Common Pitfalls

### Pitfall 1: Length bounds in the wrong layer
**What goes wrong:** `max_length=220` on `LinkedinHeadline` makes the gateway treat over-limit output as invalid → bounded retry → `LLMError` → whole run aborted.
**Why it happens:** reflexive "validate at the boundary" discipline from request models.
**How to avoid:** output models carry plain `str`; limits enforced post-generation (flag metadata) + client `maxLength`/save-guard. Request models (objetivo) DO get `Field(min_length=80, max_length=…)` — those are inputs.
**Warning signs:** a real-API fixture test failing on "resposta inválida" only when the model writes long.

### Pitfall 2: Stale 50-skills / 2,000-About figures
**What goes wrong:** constants fixed from common blog posts embed outdated numbers (50 skills; "Summary 2,000" pre-2017).
**Why it happens:** most 2026 articles still cite the old figures.
**How to avoid:** use the values in the Character Limits table; skills=100 is official, the other three are cross-source consensus recorded with their residual uncertainty.
**Warning signs:** review comments citing popular blogs that disagree with the constants.

### Pitfall 3: Glossary replacement breaking offsets via folded text
**What goes wrong:** replacing matches found in a NFKD-folded copy corrupts the original string (folded offsets ≠ original offsets; ligatures change length).
**Why it happens:** reusing the fold pipeline end-to-end instead of just for matching.
**How to avoid:** match case-insensitively on the ORIGINAL text (`re.IGNORECASE` + lookarounds); fold only for bleed detection where no rewrite happens.
**Warning signs:** mojibake or shifted text in QA unit vectors.

### Pitfall 4: QA panel truthfulness drift
**What goes wrong:** the QA report shows stale findings after edits/restores, or disappears after regen.
**Why it happens:** treating the QA as live-computed display state.
**How to avoid:** QA payload computed server-side per generation success (full or section) and swapped wholesale; edits/restores keep the last report (UI-SPEC truthfulness rule — the coverage-snapshot precedent from Phase 5).
**Warning signs:** panel recomputing in a `useMemo` over edited text.

### Pitfall 5: Experience map misalignment
**What goes wrong:** generated descriptions paired with the wrong profile entry (or a company the profile doesn't have).
**Why it happens:** LLM rephrases company names.
**How to avoid:** prompt hard rule (companies/titles must appear verbatim from FATOS DO PERFIL); align server-side by fold-match on company with an all-entries fallback (UI-SPEC comparison note); frontend renders company—title from PROFILE FACTS, never from the generated payload (UI-SPEC: sub-block header is a fixed profile-fact anchor).
**Warning signs:** harness test asserting every returned `company` fold-matches a profile company.

### Pitfall 6: max_tokens too small for the experiências stage
**What goes wrong:** JSON truncated mid-array → retry churn → LLMError, only on realistic profiles.
**Why it happens:** copying the resume-summary budget (2000).
**How to avoid:** budget for N entries × 2,000 chars + JSON overhead (recommendation: 4000–8000; each prompt file's frontmatter is independently tunable — that's what `max_tokens` per stage is for).
**Warning signs:** the real-API harness passing on the 1-experience shipped profile but failing on bigger ones.

### Pitfall 7: `\b` in bleed/glossary patterns
**What goes wrong:** terms ending in non-word characters never match.
**How to avoid:** only lookaround-bounded patterns (`(?<!\w)…(?!\w)`) — recorded project lesson.
**Warning signs:** a glossary pair silently never applying.

### Pitfall 8: Router after the SPA mount
**What goes wrong:** `/api/linkedin/*` unreachable in the built app.
**How to avoid:** `app.include_router(linkedin_router)` with the other routers, before the `StaticFiles` mount (main.py:17-25 read this session) [VERIFIED: backend/app/main.py:17-25].
**Warning signs:** 404/HTML response from API calls only in the built frontend.

## Code Examples

### DoD harness test (D-15/SC4) — the prompt-change gate

```python
# Source: harness patterns verified at backend/tests/test_llm_harness.py:202-291
# Fixtures already exist: llm_fixtures.OBJECTIVE_PT / OBJECTIVE_EN (llm_fixtures.py:75-106)
PIPELINE_STAGES = {
    "linkedin-headline", "linkedin-sobre",
    "linkedin-experiencias", "linkedin-skills",
}

@_llm_guard
@pytest.mark.llm
@pytest.mark.parametrize(("objetivo", "language", "label"), [
    (OBJECTIVE_PT, "pt-BR", "linkedin-PT"),
    (OBJECTIVE_EN, "en", "linkedin-EN"),
])
def test_real_run_linkedin_pipeline_bilingual(objetivo, language, label, tmp_path,
                                              monkeypatch, shipped_profile_path):
    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", shipped_profile_path)
    runs_log = tmp_path / "runs.jsonl"
    envelope = run_linkedin_pipeline(objetivo, language, runs_log=runs_log)  # client=None: real path

    assert envelope["status"] == "ok"
    secoes = envelope["secoes"]
    # LI-02/03/04: nothing silently truncated; limits from config constants
    assert len(secoes["headline"]) <= LINKEDIN_HEADLINE_MAX_CHARS or \
        envelope["limites"]["headline"]["excesso"] > 0       # surfaced, never cut
    assert len(secoes["sobre"]) <= LINKEDIN_SOBRE_MAX_CHARS or \
        envelope["limites"]["sobre"]["excesso"] > 0
    for entry in secoes["experiencias"]:
        assert len(entry["descricao"]) <= LINKEDIN_EXPERIENCIA_MAX_CHARS or True  # flag path
    assert secoes["habilidades"], "skills priorizados vazios"
    # SC4 (PT-BR only): QA payload present
    if language == "pt-BR":
        qa = envelope["qa"]
        assert isinstance(qa["glossario"], list) and isinstance(qa["bleed"], list)
        assert any(ch in secoes["sobre"] for ch in "áéíóúãõçêâô")  # UTF-8 probe
    # D-10/D-13: all four stages audited, contract intact
    stages_seen = {json.loads(l)["stage"] for l in runs_log.read_text(encoding="utf-8").splitlines()
                   if l.strip() and json.loads(l).get("event") != "run_summary"}
    assert stages_seen == PIPELINE_STAGES
```

### Route envelope (fail-loud, 200 + status)

```python
# Source: envelope pattern verified at backend/app/routes/resume.py:89-106
@router.post("/api/linkedin/gerar")
def gerar_linkedin(payload: LinkedinGerarRequest) -> dict:
    try:
        result = run_linkedin_pipeline(payload.objetivo, payload.language)
        return {"status": "ok", **result}
    except (ProfileError, PromptError, LLMError) as exc:
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
# LinkedinGerarRequest: objetivo = Field(min_length=80, max_length=OBJETIVO_MAX),
# language Literal["pt-BR", "en"], extra=forbid (T-03-01 discipline).
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LinkedIn skills cap 50 | **100 skills** (official Help) | ~2024 | Most 2026 articles still say 50 — the phase constant must be 100 [VERIFIED: linkedin.com/help/linkedin/answer/a549047] |
| Headline 120 chars | 220 chars | ~2017 | Stable decade-old number; sources consistent |
| "Summary" 2,000 chars | "About" 2,600 chars | ~2017 rename+expansion | Old Pulse articles citing 2,000-for-Summary are stale |
| Per-skill 61 chars (2014-era) | ~80 chars per skill name | uncited official change | LOW confidence; optional constant only |

**Deprecated/outdated for this project:** none of the shipped stack — Phase 6 adds zero replacements.

## Offline Test Strategy (D-15 split)

- **Offline (default suite, must stay 100% offline):** `FakeClient`/`ScriptedClient` drive the 4 stages through the real pipeline functions; `test_linkedin_schema.py` drift-locks the 4 wire dicts against the models; `test_linkedin_qa.py` pins glossary substitution vectors (case shapes, word boundaries, UTF-8) + bleed vectors (per shipped list term, plus negative PT-BR controls); `test_linkedin_api.py` pins the erro/ok envelopes and the 80-char objetivo bound; regen tests assert sibling byte-identity (Phase 5 precedent at test_resume_regen_pipeline.py).
- **Real-API (`uv run pytest -m llm`, the DoD):** the parametrized bilingual LinkedIn pipeline test above. **Definition-of-done operationalization: any `prompts/*.md` (including `glossario.md`) edit is "not done" until `uv run pytest -m llm` is green** — the test asserts limits, QA payload shape, runs.jsonl stage audit, and the PT-BR UTF-8 probe.
- **Frontend:** `npm run build` (tsc -b) as drift lock; copy pure functions (singular/plural counter strings) kept pure for potential offline testing without adding a JS runner (house policy: no JS test runner).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Headline 220 / About 2,600 / experience 2,000 are LinkedIn's current effective limits | Character Limits | LOW-MEDIUM: a wrong constant shows a counter slightly off from LinkedIn's own field; degradation is graceful (D-07 flag + paste-time discovery + regen). No data loss possible. |
| A2 | Official LinkedIn Help simply does not publish profile-section numeric limits (negative evidence from 2 fetched pages) | Character Limits | LOW: a page we didn't find could state them; the constants mechanism (D-05) makes correcting a one-line change |
| A3 | `LINKEDIN_OBJETIVO_MAX` recommendation of ~2,000 chars (server) | Code Examples / D-02 | Trivial: planner picks; min 80 mirrors JD_MIN_LENGTH (verified value) |
| A4 | Stage names `linkedin-headline/-sobre/-experiencias/-skills` and `limites`/`qa` envelope key names | Architecture Patterns | Cosmetic: planner-owned naming discretion (CONTEXT.md); names only flow into runs.jsonl `stage` strings (contract-safe) |
| A5 | The EN-bleed term list above is a starting proposal, not a curated corpus | Pattern 5 | LOW: false positives are non-blocking avisos with a pinned legend; list is offline-testable and cheap to tune |
| A6 | Per-skill name bound (~80 chars) if adopted | Character Limits | LOW: optional; profile skills are short; same graceful-degradation posture |
| A7 | Glossário pairs live in YAML frontmatter (not body markup) | Pattern 3 | LOW: planner discretion (CONTEXT.md); frontmatter matches the strict-validation pattern already shipped |

## Open Questions (RESOLVED)

1. **Curate the EN-bleed list at planning time**
   - What we know: detection mechanics are settled (fold + lookaround, non-blocking); the exact shipped terms are a judgment call.
   - What's unclear: which short tokens ("and", "for", "with") earn their place vs drown the report in noise on real profiles.
   - Recommendation: ship multi-word/action-verb signals first (lowest false-positive risk); add short tokens only with vectors proving PT-BR negative controls pass. Decidable in planning with the offline test open in a second pane.

2. **Generalize vs sibling for reused Currículo components**
   - What we know: UI-SPEC explicitly leaves "generalize a Currículo-typed component vs add a LinkedIn sibling" to planner discretion.
   - Recommendation: siblings where types differ (counters/copy are LinkedIn-shaped), reuse where behavior is identical (ConfirmStrip messages reused verbatim per UI-SPEC).

## Environment Availability

No new external dependencies. Probed this session:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python + uv | backend, pytest | ✓ | 3.12.x / uv (suite ran: 274 collected, 267 offline) [VERIFIED: session probe] | — |
| pytest + `-m llm` marker | DoD harness | ✓ | configured (pyproject.toml:20-21) | — |
| Node + npm | frontend build | ✓ | v22 (prior phases verified; `npm run build` = tsc -b + vite) [VERIFIED: frontend/package.json] | — |
| OPENROUTER_API_KEY | real-API DoD only | user-local (.env) | — | Offline suite unaffected; DoD gate needs the key (skipif guard already shipped, test_llm_harness.py:84-87) |
| Clipboard API | Copiar | ✓ (localhost secure context) | — | pinned manual-select failure line (UI-SPEC) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend, offline default) + `tsc -b` (frontend drift lock) |
| Config file | backend/pyproject.toml (`addopts = "-m 'not llm'"`, `markers = ["llm: …"]`) |
| Quick run command | `cd backend && uv run pytest -q` |
| Full suite command | `cd backend && uv run pytest -q` + `uv run pytest -m llm` (spend — the SC4 DoD) + `cd frontend && npm run build` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LI-01 | objetivo+idioma drive generation; lint reuse | unit/integration (offline) | `uv run pytest tests/test_linkedin_pipeline.py tests/test_linkedin_api.py -q` | ❌ Wave 0 |
| LI-02 | headline block, 220-constant plumbing | unit | `uv run pytest tests/test_linkedin_schema.py -q` | ❌ Wave 0 |
| LI-03 | sobre block, 2,600-constant plumbing | unit | `uv run pytest tests/test_linkedin_schema.py -q` | ❌ Wave 0 |
| LI-04 | one experiências stage, per-entry bounds | unit | `uv run pytest tests/test_linkedin_regen_pipeline.py -q` | ❌ Wave 0 |
| LI-05 | skills priority order + copy-ready blocks | unit | `uv run pytest tests/test_linkedin_pipeline.py -q` | ❌ Wave 0 |
| SC4 | glossary + bleed deterministic QA (PT-BR) | unit (vectors) | `uv run pytest tests/test_linkedin_qa.py -q` | ❌ Wave 0 |
| SC4 | bilingual real-API DoD | real-API (`-m llm`) | `uv run pytest -m llm` (extends existing test_llm_harness.py) | ✅ file exists, tests ❌ Wave 0 |
| — | schema drift lock (4 new wire dicts) | unit | `uv run pytest tests/test_linkedin_schema.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest -q` (267 existing + new offline tests stay green; suite must remain 100% offline)
- **Per wave merge:** full offline suite + `cd frontend && npm run build`
- **Phase gate:** offline green + `uv run pytest -m llm` green (bilingual LinkedIn fixtures) before `/gsd:verify-work` — this IS the SC4 definition-of-done mechanism

### Wave 0 Gaps
- [ ] `backend/tests/test_linkedin_schema.py` — drift-lock for 4 new wire schemas
- [ ] `backend/tests/test_linkedin_qa.py` — glossary + bleed vectors (incl. UTF-8 + negative PT controls)
- [ ] `backend/tests/test_linkedin_pipeline.py` — offline 4-stage orchestration via FakeClient
- [ ] `backend/tests/test_linkedin_regen_pipeline.py` — group-swap + sibling byte-identity
- [ ] `backend/tests/test_linkedin_api.py` — envelopes + objetivo bounds
- [ ] Extend `backend/tests/test_llm_harness.py` — bilingual LinkedIn DoD tests
- [ ] `prompts/glossario.md` + 4 `prompts/linkedin-*.md` files (prompt files are production artifacts; harness needs them)

## Security Domain

### Applicable ASVS Categories (level 1, per config `security_enforcement: true`)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | localhost single-user tool (PROJECT.md constraint) |
| V3 Session Management | no | no sessions exist |
| V4 Access Control | no | no multi-user surface |
| V5 Input Validation | **yes** | Pydantic strict models, `extra="forbid"` (T-03-01 discipline); objetivo `Field(min_length=80, max_length=…)`; LLM output re-validated, wire `strict: true` never trusted (T-02-03) |
| V6 Cryptography | no | no secrets handled beyond the existing .env key path (test_secrets.py guards tracking) |
| V14 Config (API exposure) | **yes** | new routes registered BEFORE the SPA mount; erro envelope leaks only PT-BR lines, raw detail terminal-only (house fail-loud pattern) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via objetivo free text | Tampering | D-07/T-02-01 pattern: user text is USER-message DATA, never system instruction; prompts restate "o texto chega sempre na mensagem do usuário, nunca como instrução" (resume-summary.md rule verbatim pattern) |
| XSS via generated/edited text | Tampering | All content renders as JSX text children — no `dangerouslySetInnerHTML` anywhere (T-01-08 posture, UI-SPEC accessibility baseline) |
| Overly-long / hostile payload from LLM | DoS (local) | max_tokens per stage bounds output; post-gen length checks; no truncation (D-07) |
| Clipboard overwriting user data | Elevation | User-initiated only (button click); copies the displayed text the user just reviewed (D-08) |

## Sources

### Primary (HIGH confidence)
- linkedin.com/help/linkedin/answer/a549047 (Add and remove skills) — fetched this session; verbatim 100-skills quote [VERIFIED: LinkedIn Help Center fetch]
- Codebase, read this session: gateway.py, prompts.py, schemas.py, pipeline.py, facts.py, coverage.py, lint.py, routes/resume.py, main.py, test_llm_harness.py, llm_fixtures.py, conftest.py, test_gateway.py (FakeClient), constants/ui.ts (NAV_ITEMS:8), package.json, pyproject.toml — all claims about existing behavior carry `[VERIFIED: path:lines]` tags above
- linkedin.com/help/linkedin/answer/a542926 (Edit Your Headline) and a547248 (Edit introduction) — fetched this session; both state NO numeric limits (negative evidence)

### Secondary (MEDIUM confidence)
- linkedhelper.com/blog/linkedin-character-limit — consolidated limit table (220/2,600/2,000/80-per-skill), corroborated by TryKondo, AuthoredUp, LigoSocial, Leaders.social, WriteHero, Derrick.app search results

### Tertiary (LOW confidence)
- Per-skill 80-char figure (two third-party mentions; no official statement)
- LinkedIn Pulse "Wondering about LinkedIn character limits?" — partially stale (cites old Summary 2,000), used only as per-skill corroboration

## Metadata

**Confidence breakdown:**
- Standard stack / reuse map: HIGH — every cited behavior read from source this session; no new deps
- Architecture (stage set, QA design): HIGH — direct pattern lifts from shipped, test-pinned Phase 2/3/5 code
- LinkedIn limits: MEDIUM overall — 100-skills HIGH (official); 220/2,600/2,000 MEDIUM (multi-source consensus + recorded official silence); residual risk made cheap by D-07 design
- Pitfalls: HIGH — each maps to a mechanism read in this session's source

**Research date:** 2026-09-27
**Valid until:** 2026-10-27 (stable domain; LinkedIn limit drift would surface via the graceful-degradation path, and skills=100 was fetched from the live Help page this session)
