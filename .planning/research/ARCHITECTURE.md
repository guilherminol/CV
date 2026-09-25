# Architecture Research

**Domain:** Personal LLM-powered job-search content toolkit (ATS resume tailoring + LinkedIn optimization), localhost-only web app
**Researched:** 2026-09-25
**Confidence:** HIGH (core integration mechanics verified against official docs; pipeline patterns corroborated across multiple sources)

## Standard Architecture

### System Overview

LLM document-generation apps (resume tailors, report writers, proposal generators) converge on the same shape: a **file-backed data source**, a **staged prompt pipeline** that turns one input into structured intermediate data and then independent per-section generations, a **backend-owned draft state** the user reviews and mutates, and a **rendering/export stage** that converts the accepted draft into the final artifact. Each stage communicates through a typed JSON contract (JSON Schema / Pydantic model), never through free-form prompt string passing. (MEDIUM — corroborated across ZenML pipeline guides, Vercel AI SDK structured-output patterns, LangGraph human-in-the-loop patterns)

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Vite + React + TS SPA)                 │
│  ┌──────────────┐  ┌──────────────────────────┐  ┌───────────────┐   │
│  │ Resume view  │  │ Review view (edit cards, │  │ LinkedIn view │   │
│  │ paste JD/obj │  │ regenerate per section)  │  │ + copy-out    │   │
│  └──────┬───────┘  └───────────┬──────────────┘  └──────┬────────┘   │
│         └────────── JSON/fetch + SSE (text/event-stream) ──────┘     │
├──────────────────────────────────────────────────────────────────────┤
│                     BACKEND (FastAPI, localhost)                     │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐     │
│  │ Profile      │   │ Prompt Pipeline (per module)             │     │
│  │ Loader       │──▶│  1. analyze input (JD/objective) → JSON  │     │
│  │ (frontmatter │   │  2. plan sections / select experiences   │     │
│  │ + Pydantic)  │   │  3. generate section-by-section          │     │
│  └──────────────┘   └───────────────┬──────────────────────────┘     │
│  ┌──────────────┐   ┌───────────────▼──────────────────┐             │
│  │ LLM Gateway  │◀──│ Run Store (draft state machine)  │             │
│  │ (OpenRouter, │   │ sections: pending/generating/    │             │
│  │ 1 call shape)│   │ generated/edited/accepted        │             │
│  └──────────────┘   └───────────────┬──────────────────┘             │
│  ┌──────────────┐   ┌───────────────▼──────────────────┐             │
│  │ Prompt files │   │ PDF Renderer                     │             │
│  │ (versioned   │   │ draft JSON → Jinja2 HTML + print │             │
│  │  .md templates)│ │ CSS → Chromium page.pdf()        │             │
│  └──────────────┘   └──────────────────────────────────┘             │
├──────────────────────────────────────────────────────────────────────┤
│                            DATA LAYER (files, git)                   │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │ profile/      │  │ prompts/     │  │ outputs/ (run JSON + PDFs,│  │
│  │ master profile│  │ meta-prompts │  │ gitignored or committed   │  │
│  │ .md + .yaml   │  │ per module   │  │ per user preference)      │  │
│  └───────────────┘  └──────────────┘  └───────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ OpenRouter API    │  (external, HTTPS)
                    │ + Chromium        │  (local, via Playwright)
                    └───────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Profile Loader** | Owns reading + validating the master profile into one typed object; fail-fast with file/field errors | `python-frontmatter` to parse `profile.md` (YAML frontmatter + Markdown body) → Pydantic `model_validate`; re-runs on file change or explicit reload route (HIGH — official Pydantic docs) |
| **LLM Gateway** | Single choke point for all OpenRouter calls: auth, model name, retries/timeouts, token/cost logging | OpenAI SDK with `base_url="https://openrouter.ai/api/v1"`; two functions: `complete_text()` and `complete_structured(schema)` using `response_format: json_schema` (HIGH — official OpenRouter docs) |
| **Prompt Pipeline** | Turns raw input (JD text / career objective) + profile + language into a structured draft, one stage at a time | Stage functions each load a meta-prompt template file, inject variables, call the gateway, validate JSON output against a stage schema |
| **Run Store** | Owns the draft (the generated resume/LinkedIn content) and per-section status; survives frontend refreshes | In-memory dict keyed by run id on the backend + JSON snapshot written to `outputs/<run-id>/`; no database (constraint: file-based) |
| **Review/Edit API** | Exposes generate / regenerate-section / edit-section / export endpoints; streams generation via SSE | FastAPI routes; section regeneration streams tokens as `text/event-stream` so the UI renders progressively (HIGH — official FastAPI docs) |
| **PDF Renderer** | Converts an accepted draft into the single-column ATS PDF; owns the print template | Jinja2 HTML template + dedicated print stylesheet → Playwright Chromium `page.pdf(format="A4", print_background=True)` (HIGH — official Chromium print-to-PDF semantics: print CSS media, text-based output) |
| **Frontend SPA** | Module inputs, review cards with inline editing + per-section regenerate buttons, export trigger, PT-BR UI strings | React + React Query for per-section mutation/refetch; zod re-validates LLM JSON before rendering |
| **Keyword Model** | Structured representation of what the vacancy/objective demands, shared by all downstream prompts | First pipeline stage output: `{role, seniority, hard_skills, tools, soft_skills, keywords: [{en, pt}], qualifications}` as JSON Schema |

## Recommended Project Structure

```
career-tailor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app; API routes first, SPA mount last
│   │   ├── config.py            # .env loading, model name, paths
│   │   ├── routes/
│   │   │   ├── resume.py        # POST /api/resume/runs, export
│   │   │   ├── linkedin.py      # POST /api/linkedin/runs
│   │   │   ├── sections.py      # PATCH + regenerate (SSE) endpoints
│   │   │   └── profile.py       # GET /api/profile, reload
│   │   ├── llm/
│   │   │   ├── gateway.py       # OpenRouter client, complete_text/complete_structured
│   │   │   └── schemas.py       # JSON Schemas for every stage output (JDProfile, SectionDraft…)
│   │   ├── pipeline/
│   │   │   ├── resume.py        # analyze_jd → plan → generate_section
│   │   │   └── linkedin.py      # analyze_objective → generate_block
│   │   ├── profile/
│   │   │   ├── loader.py        # frontmatter + Pydantic validation
│   │   │   └── models.py        # Profile, Experience, Project, …
│   │   ├── runs/
│   │   │   ├── store.py         # run registry, section state machine
│   │   │   └── models.py        # Run, Section, SectionStatus
│   │   └── pdf/
│   │       ├── renderer.py      # draft → HTML → Chromium page.pdf
│   │       └── templates/resume.html.j2 + print.css
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── views/ (ResumeView, ReviewView, LinkedInView)
│   │   ├── api/client.ts        # typed fetch + SSE reader
│   │   └── schemas/             # zod mirrors of backend contracts
├── profile/
│   ├── profile.md               # YAML frontmatter (contact, skills) + Markdown body (experiences, projects)
│   └── keywords.pt-BR.yaml      # optional sidecar market-keyword lists
├── prompts/
│   ├── resume/ (analyze_jd.md, plan.md, section-summary.md, section-experience.md, …)
│   └── linkedin/ (analyze_objective.md, headline.md, about.md, …)
├── outputs/                     # run snapshots + exported PDFs
└── .env                         # OPENROUTER_API_KEY only (gitignored)
```

### Structure Rationale

- **`profile/`, `prompts/`, `outputs/` at the repo root, outside app code:** they are *content*, not code. The user edits them in their editor and commits them; the app treats them as read-at-runtime data. This directly implements the "Markdown/YAML in git, no admin UI" decision in PROJECT.md.
- **One `prompts/` file per pipeline stage:** meta-prompts are iterated on constantly (they *are* the product). Versioned template files make diffs meaningful in git and let the roadmap add a section type without touching Python.
- **`llm/schemas.py` as the contract registry:** every LLM stage output has one Pydantic model + matching JSON Schema. This is the seam the frontend zod schemas mirror — one place to change when a stage output evolves.
- **`runs/` separate from `pipeline/`:** generation (stateless functions) and draft state (the review flow) are different concerns with different lifetimes; keeping them apart is what makes "regenerate just this section" trivial.

## Architectural Patterns

### Pattern 1: Typed Profile-as-Data with Fail-Fast Loading

**What:** The master profile is a file contract. Load = parse frontmatter/YAML → Pydantic `model_validate` → typed object used everywhere. Invalid profile = loud error at load, never mid-generation.
**When to use:** Any system where humans edit structured files by hand.
**Trade-offs:** Strict schema means occasional friction when adding a field; far cheaper than silent `None` bugs appearing in generated resumes.

**Example:**
```python
import frontmatter, yaml
from pydantic import BaseModel, ValidationError

class Experience(BaseModel):
    company: str
    role: str
    start: str; end: str | None
    highlights: list[str]        # markdown bullets, verbatim ground truth

class Profile(BaseModel):
    name: str; contact: dict[str, str]
    skills: list[str]
    experiences: list[Experience]
    summary_md: str              # markdown body of profile.md

def load_profile(path="profile/profile.md") -> Profile:
    post = frontmatter.load(path)          # YAML frontmatter + Markdown body
    data = {**post.metadata, "summary_md": post.content}
    return Profile.model_validate(data)    # ValidationError lists every failing field
```

### Pattern 2: Staged Prompt Pipeline with Structured-Output Contracts

**What:** Generation is never one prompt. Stage 1 (analyze input) and Stage 3 (generate a section) are separate LLM calls, each returning JSON validated against a schema via OpenRouter `response_format: json_schema`. Stage 2 (planning) is cheap Python or a small LLM call. Because Stage 3 is *one call per section* with shared context (profile slice + JobProfile + language), "regenerate this section" is the same code path as initial generation. (MEDIUM — corroborated plan→sections→assemble pattern)
**When to use:** Any document with section-independent parts and a review flow — which this project is by definition.
**Trade-offs:** More calls = more latency and cost than one-shot generation; mitigated by streaming per-section results as they complete and by cheap models for the analysis stage.

**Example:**
```python
def analyze_jd(jd_text: str) -> JobProfile:
    return gateway.complete_structured(
        prompt=render("prompts/resume/analyze_jd.md", jd=jd_text),
        schema=JobProfile.model_json_schema(),
    )  # gateway sets response_format={"type":"json_schema", ...}, strict=True

def generate_section(section_id, profile_slice, job: JobProfile, lang: str) -> SectionDraft:
    meta = render(f"prompts/resume/section-{section_id}.md",
                  profile=profile_slice, job=job, language=lang,
                  ats_rules=ATS_RULES)          # single-column, no fabrication, verb-led bullets
    return gateway.complete_structured(prompt=meta, schema=SectionDraft.model_json_schema())
```

**Grounding rule (non-negotiable):** the pipeline only ever injects real profile data into Stage 3, and meta-prompts state "select and rephrase from the provided experience; never invent employers, dates, or technologies." The LLM's job is selection + wording, not recall. This is the single biggest correctness lever in the whole system.

### Pattern 3: Backend-Owned Run with a Section State Machine

**What:** A *run* is the unit of work: `{id, module, input, language, job_profile, sections[]}`. Each section carries `status: pending → generating → generated → edited → accepted` (+ `regenerating` reuses `generating`). The backend owns this state; the frontend renders it. Regeneration calls the same Stage-3 function; inline edits are a `PATCH` that flips status to `edited`. Export validates all sections are `generated|edited|accepted` first.
**When to use:** Whenever humans review AI output piecemeal.
**Trade-offs:** Slightly more backend machinery than holding state in React — but it survives page refreshes, keeps history in `outputs/`, and makes the review API testable without a browser.

**Example:**
```python
class SectionStatus(str, Enum):
    pending="pending"; generating="generating"
    generated="generated"; edited="edited"; accepted="accepted"

def regenerate(run: Run, section_id: str, hint: str | None) -> AsyncIterator[str]:
    section = run.section(section_id)
    section.status = SectionStatus.generating
    section.hint = hint                      # optional "make it more concise" user steer
    for token in pipeline.resume.generate_section_stream(run, section):
        yield token                          # SSE: text/event-stream to the review card
    section.status = SectionStatus.generated
    snapshot(run)                            # persist draft JSON to outputs/<run-id>/
```

### Pattern 4: One HTML Print Template as the Single Source of Truth for PDF

**What:** The ATS resume's layout lives in exactly one place: a Jinja2 HTML template + a print stylesheet (`@page` A4, single column, standard headings, no tables/columns/icons). The review UI renders the *same* HTML for preview; export feeds it to headless Chromium's `page.pdf()`. Chromium applies the **print CSS media type**, producing a text-based PDF whose visual order equals extraction order — exactly what ATS parsers need (parsers garble two-column layouts, tables, and header/footer content). (HIGH — official Chromium/Puppeteer/Playwright print semantics; MEDIUM — ATS parsing rules)
**When to use:** Always for this project — it guarantees the preview the user approves is byte-for-byte the layout they export.
**Trade-offs:** Requires the Chromium download (`playwright install chromium`, once). Generic markdown-to-PDF converters are lighter but cannot express the ATS layout rules reliably.

**Example:**
```python
from playwright.sync_api import sync_playwright

def render_pdf(draft: Run, lang: str) -> bytes:
    html = jinja_env.get_template("resume.html.j2").render(
        sections=draft.accepted_sections(), headings=HEADINGS[lang])  # localized headings
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.set_content(html, wait_until="networkidle")
        return page.pdf(format="A4", print_background=True)
```

### Pattern 5: Language as a Run Parameter, Not a Translation Step

**What:** Target language (`pt-BR` | `en`) is injected into every prompt of a run; content is *generated natively* in the target language. When the job description's language differs from the output language, the analysis stage returns keywords cross-mapped in both languages (`{en, pt}` pairs), so the tailored resume keeps ATS-matching vocabulary in whichever language it is written. Section headings come from a localized dict in the PDF template. Default rule per run: output language follows the vacancy/objective language. (MEDIUM — Brazilian market practice is separate single-language versions, never mixed; native generation avoids translation drift)
**When to use:** Always; translate-after-generate costs a second LLM pass per section and produces second-person-voice artifacts, especially damaging in LinkedIn About text.
**Trade-offs:** Meta-prompts must state PT-BR conventions explicitly (e.g., keep tech terms in English — "React", "cloud" — natural in Brazilian tech writing); this is one line per prompt, cheap.

## Data Flow

### Generation Flow (Resume module)

```
[Paste JD + pick language]
    ↓ POST /api/resume/runs
Profile Loader ──▶ Profile (validated) ──▶ Prompt Pipeline
    │                                          │
    │                            Stage 1: analyze_jd → JobProfile JSON (validated)
    │                            Stage 2: plan (which experiences/projects feature)
    │                            Stage 3: per-section generate (parallel/streamed)
    │                                          │
    ├──────────────▶ Run Store ◀───────────────┘
    │                (sections: status + content)
    ↓ SSE per section as it completes
[Review view: editable cards]  ──PATCH /sections/{id}──▶  status=edited
    ├──POST /sections/{id}/regenerate──▶ Stage 3 again (same prompt + optional hint)
    ↓ POST /api/resume/runs/{id}/export  (validates all sections ready)
PDF Renderer: draft JSON → Jinja2 HTML (print CSS, localized headings) → Chromium page.pdf
    ↓
outputs/<run-id>/resume.pt-BR.pdf  +  draft.json snapshot
```

### LinkedIn Module Flow (same skeleton, different prompts, no PDF)

```
[Career objective + language] → analyze_objective → TargetProfile JSON
    → generate blocks: headline | about | experience descriptions | skills
    → Run Store → Review view → copy-to-clipboard (no export stage)
```

### State Management

```
Backend Run Store = source of truth          Frontend = projection
  sections[].status ──(SSE / refetch)──▶  React Query cache per section
       ▲                                        │
       └── PATCH / regenerate ──────────────────┘  (mutations invalidate the section)
```

### Key Data Flows

1. **Profile → every prompt:** the profile is loaded once per run and *sliced* — each Stage-3 call receives only the slice relevant to its section (one experience, or the skills list). Smaller prompts, cheaper calls, and no risk of the model quoting an unrelated job.
2. **JobProfile → every Stage-3 prompt:** the extracted keyword set is the shared context that makes sections coherent; it is the artifact that makes "tailored" true. Persisted in the run snapshot for auditability.
3. **Review loop:** regenerate and edit mutate only one section; the run's other sections and the JobProfile are untouched. The optional user hint on regeneration is appended to the meta-prompt, not a new prompt type.
4. **Export:** read-only over the draft — validation (all sections ready, contact block present, single language) → render → write PDF + snapshot. Nothing in the run changes at export.

## Build Order Implications (for roadmap)

Dependency-driven; each step is testable alone:

1. **Profile schema + loader + example data** — everything depends on the typed profile; also the deliverable the user fills in with real data.
2. **LLM Gateway + one smoke meta-prompt** — proves OpenRouter connectivity, structured output, .env handling; zero product surface yet.
3. **Resume pipeline, sections generated as a batch** — analyze_jd → plan → per-section generate; CLI or minimal UI is enough. This is the vertical slice that proves the core value ("paste JD → tailored content").
4. **PDF Renderer + basic export** — template + Chromium + endpoint; delivers the first artifact you could actually send. (Could swap with 5, but the review flow's value is easiest to judge against a real PDF.)
5. **Review flow** — run state machine, regenerate/edit endpoints, review UI. Depends on 3 (Stage-3 isolation) and benefits from 4 (preview ≈ export).
6. **LinkedIn module** — reuses gateway, pipeline pattern, run store, and review UI wholesale; only prompts and block types are new. No PDF stage.
7. **Bilingual + keyword hardening** — cross-mapped keywords, PT-BR prompt conventions, localized headings; mostly prompt/template refinement, not new architecture.

Anti-dependency note: do not start with the review UI (it has nothing to review) or with bilingual features (they are parameters, not structure — the language param should exist in prompts from step 3, but refinement comes last).

## Scaling Considerations

Personal localhost tool — "scaling" means responsiveness and cost, not users:

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user, localhost (this project) | Monolith as designed. Warm the Chromium browser once per backend start (launch is the slow part, not the render). In-memory runs are fine; snapshots to `outputs/` give durability. |
| Heavier personal use (many runs/day) | Persist run index to a simple JSONL/SQLite file if snapshot listing gets slow; cache analyze_jd output keyed by JD text hash (same posting pasted twice = one analysis call). |
| If ever shared (out of scope by constraint) | That is a different product: auth, per-user profile stores, a real run database, a job queue for LLM calls. The pipeline/gateway/renderer components survive unchanged; the single-user shortcuts (in-memory runs, localhost trust) do not. |

### Scaling Priorities

1. **First bottleneck — LLM latency on the review flow:** a full resume is 6–10 Stage-3 calls. Stream each section as it finishes (SSE) and run sections concurrently; the user starts reading section 1 while section 6 generates.
2. **Second bottleneck — OpenRouter model variability:** structured-output support is per model/endpoint and `strict` enforcement varies by provider. The gateway should pin a model per stage in config, set `require_parameters` where needed, and re-validate every response with Pydantic — never trust conformance, even with `json_schema`. (HIGH — official OpenRouter docs)

## Anti-Patterns

### Anti-Pattern 1: One-Shot Whole-Resume Prompt
**What people do:** One giant prompt: "here is my profile and the job description, write the resume."
**Why it's wrong:** Regenerating "just the summary" is impossible (regenerate everything, paying full cost and re-rolling sections you liked); the model balances section quality against a huge output budget; the review flow — a core requirement — has nothing to attach to.
**Do this instead:** Per-section Stage-3 calls with shared JobProfile context (Pattern 2); the review flow falls out for free.

### Anti-Pattern 2: Client-Side PDF Generation (jsPDF, canvas, print-screenshot)
**What people do:** Render the resume in the browser DOM and print/screenshot to PDF from the frontend.
**Why it's wrong:** Canvas-based PDFs embed text as paths/images — ATS parsers extract nothing. Browser print dialogs produce inconsistent margins/fonts per browser.
**Do this instead:** Server-side HTML template + headless Chromium `page.pdf()` — real text layer, deterministic layout, and the preview the user reviewed is the exact rendering exported (Pattern 4).

### Anti-Pattern 3: Generate in One Language, Translate After
**What people do:** Generate the English resume, then run it through a translation call per language needed.
**Why it's wrong:** Two passes per section, voice drift ("I" vs implied-subject LinkedIn PT conventions), and keyword translation that no longer matches what the vacancy actually says.
**Do this instead:** Language is a run parameter in every meta-prompt; cross-map keywords at the analysis stage so ATS vocabulary survives the language switch (Pattern 5).

### Anti-Pattern 4: Trusting LLM Output Shape (and Facts)
**What people do:** Parse the model's JSON with no validation; accept content that invents a technology or stretches dates.
**Why it's wrong:** Strict-mode enforcement varies by provider on OpenRouter; and hallucinated credentials in a resume are worse than a parsing bug — you send them to real recruiters.
**Do this instead:** Pydantic re-validation on every stage output (retry once on failure, surface a clear error after); prompts grounded so selection happens over injected profile slices only; export-time validation re-checks that every experience entry traces to profile data.

### Anti-Pattern 5: Draft State Living Only in the Frontend
**What people do:** Keep generated sections in React state; regenerate = refetch, edit = local state.
**Why it's wrong:** A refresh or a crashed tab destroys a half-reviewed resume; the backend cannot validate at export ("is every section done?"); runs leave no audit trail.
**Do this instead:** Backend-owned run store as source of truth, frontend as projection (Pattern 3); snapshots to `outputs/` give history for free.

### Anti-Pattern 6: OpenRouter Calls Scattered Through Route Handlers
**What people do:** Each endpoint builds its own HTTP call to the LLM with inline prompts.
**Why it's wrong:** Model name, retries, cost logging, and the OpenRouter response quirk handling get duplicated and drift; swapping models (the stated reason for choosing OpenRouter) becomes a search-and-replace across the codebase.
**Do this instead:** One gateway module; model-per-stage in config; prompts as files in `prompts/`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenRouter | OpenAI SDK, `base_url="https://openrouter.ai/api/v1"`, key from `.env` | `response_format: json_schema` + `strict: true` for every structured stage; support is per model/endpoint — pin models in config; streaming = SSE chunks (HIGH — official docs) |
| Chromium (via Playwright) | Local headless browser; `set_content(html)` → `page.pdf(format="A4", print_background=True)` | One-time `playwright install chromium`; applies print CSS media type; produces text-based ATS-parseable PDF (HIGH — official docs) |
| Git / filesystem | Profile, prompts, outputs are plain files; app never writes to `profile/` | No database by constraint; `.env` gitignored before first commit |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Frontend ↔ Backend | JSON REST + SSE streams, zod/Pydantic contracts both sides | Mount SPA *after* API routes in FastAPI or the catch-all swallows `/api/*` (HIGH — official docs) |
| Pipeline ↔ Gateway | `complete_text` / `complete_structured(schema)` only | Pipeline never sees HTTP details; gateway never sees prompt content |
| Modules (resume/linkedin) ↔ shared core | Both consume gateway + run store + review endpoints; own only prompts + stage functions | New module = new prompts + block types, zero core changes |
| Review UI ↔ PDF Renderer | Shared Jinja2 HTML template | Preview parity: what is reviewed is what exports |

## Sources

- OpenRouter official docs — structured outputs (`response_format: json_schema`, `strict`, per-endpoint support, `require_parameters`), chat completions API shape, OpenAI SDK compatibility, SSE streaming. (HIGH)
- FastAPI official docs — StaticFiles mounting with `html=True`, mount-after-routes ordering, StreamingResponse / SSE with cancellation-aware async generators. (HIGH)
- Pydantic v2 official docs — BaseModel validation, `model_validate` for parsed YAML/JSON dicts, aggregated ValidationError, `model_dump`. (HIGH)
- Puppeteer/Chromium print-to-PDF official docs — `page.pdf()` uses print CSS media type; format/margins/printBackground options; text-based output. Same engine behind Playwright's Python API. (HIGH)
- LLM document-generation architecture patterns (plan → per-section generation → validate → human-in-the-loop → assemble/export; structured output as stage contract): corroborated across ZenML pipeline guides, Vercel AI SDK structured-output/streaming patterns, LangGraph human-in-the-loop patterns. (MEDIUM)
- ATS parsing behavior (reading-order extraction; multi-column/table/header-footer failures; single-column standard headings parse reliably): consistent vendor guidance + the Google-format requirement fixed in PROJECT.md. (MEDIUM)
- Bilingual PT-BR/EN resume practice (language matches posting; separate single-language versions; keyword matching per language; Brazilian currículo conventions): latojobs.com, edugradus.com, resume-example.com market guides. (MEDIUM)
- Keyword-extraction approach (LLM-stage structured extraction over NLP libraries): inference from ecosystem tool patterns (Jobscan/Teal/Rezi all keyword-target) + reuse of the already-required LLM infra; dedicated comparison search was rate-limited, flag for phase-level validation. (MEDIUM-LOW)

---
*Architecture research for: Career Tailor — LLM-powered ATS resume + LinkedIn toolkit*
*Researched: 2026-09-25*
