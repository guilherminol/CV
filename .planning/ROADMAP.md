# Roadmap: Career Tailor

## Overview

Career Tailor goes from an empty repo to a localhost app the user actually sends job applications with. The build order follows the dependency graph: the master profile schema is the root of everything, so it lands first with loud validation; then the LLM gateway proves OpenRouter structured outputs, logging, and bilingual fixtures before any product surface exists; then the first vertical slice delivers core value (paste JD → grounded, keyword-targeted resume sections); the PDF phase makes the output genuinely sendable, with the ATS parse-back gate built as the phase's first task — not bolted on after; the review flow turns the user into the quality gate before export; and the LinkedIn module reuses the whole engine, paying only for prompts and block types. Language (PT-BR/EN) is a prompt parameter from Phase 2 onward and gets hardened — glossary, QA gate, both-language fixtures — in the final phase.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation — Scaffold + Master Profile** - App runs locally with a PT-BR interface; git-versioned master profile schema with example data, validated loudly on load
- [x] **Phase 2: LLM Generation Core** - One logged, schema-validated, bilingual OpenRouter gateway with meta-prompts as editable git files and an input-agnostic {en, pt} keyword engine (completed 2026-09-26)
- [x] **Phase 3: Resume Vertical Slice** - Paste JD → grounded, keyword-targeted resume sections with visible keyword extraction, coverage checklist, and completeness lint (completed 2026-09-26)
- [x] **Phase 4: PDF Export + ATS Self-Check** - Sendable single-column Google-format PDF whose text layer is proven by an automated parse-back gate, in both languages (completed 2026-09-27)
- [x] **Phase 5: Review Flow + Fact Safety** - Per-section regenerate, inline editing, and source-vs-generated fact diff before export (completed 2026-09-29)
- [ ] **Phase 6: LinkedIn Module + Bilingual Hardening** - Career objective → headline/About/experience/skills, length-enforced and copy-paste ready in PT-BR or EN

## Phase Details

### Phase 1: Foundation — Scaffold + Master Profile

**Goal**: The app runs locally with a PT-BR interface, and the master profile is a git-versioned, schema-validated source of truth ready to feed both generation modules.
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: PROFILE-01
**Success Criteria** (what must be TRUE):

  1. User starts the app locally and sees the PT-BR interface at localhost (frontend served by FastAPI after build, or dev servers during development).
  2. The master profile (Markdown/YAML in git) loads and validates against the schema; a deliberately broken file produces a loud error naming the exact file and field — before any generation can run.
  3. Shipped example data covers experiences, projects, technologies, and impacts, and the app visibly flags that placeholder data is in use until the user replaces it with real data.
  4. The profile schema encodes the chosen localization shape (parallel localized fields vs per-language files), demonstrated by bilingual example data.
  5. The OpenRouter API key lives only in a gitignored `.env` — nothing secret is ever committed.

**Plans**: 3/3 plans executed

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Walking Skeleton: scaffold (gitignore-first, uv backend on pinned 3.12, Vite frontend) + end-to-end perfil path (content/profile.md → Pydantic → GET /api/profile → PT-BR shell with placeholder banner), dev + prod modes

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Profile contract: full strict schema (localized maps, base pt-BR, extra=forbid everywhere), fail-fast loader with PT-BR error localization, fully bilingual example persona, completude in the API envelope

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Perfil UI: three-state Perfil home (loading / error panel with verbatim PT-BR lines / ok), completeness grid, resume-style preview, finalized run docs

### Phase 2: LLM Generation Core

**Goal**: Every LLM call flows through one gateway that is logged, schema-validated, bilingual by parameter, and driven by meta-prompts the user can edit as versioned files in git.
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: PROFILE-03
**Success Criteria** (what must be TRUE):

  1. User edits a meta-prompt file in git (e.g., "more metrics", "more concise PT-BR") and the next generation run reflects the change with no code edits.
  2. The fixture harness generates successfully in both EN and PT-BR, and every call is logged (stage, model, tokens/cost) — swapping models is a config change, not code.
  3. A malformed structured response is caught by validation, retried with the validation error appended, and surfaces a clear failure — malformed content never reaches downstream stages.
  4. Keyword extraction run on a pasted JD or a career objective returns keywords mapped across {en, pt} with covered/adjacent/absent classification hooks for later coverage checks.

**Plans**: 5/5 plans executed (incl. 02-05 gap closure — SC3 containment; verification passed 13/13)

Plans:
**Wave 1**

- [x] 02-01-PLAN.md — Wave-0 config: openai dep, `llm` pytest marker + offline-by-default addopts, logs/ gitignore, config constants (slug, paths, retry cap)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md — Tracer: meta-prompt loader (fail-fast, D-05..D-08) + gateway happy path with mocked client → validated KeywordExtraction + first runs.jsonl line

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03-PLAN.md — Expansion: validation-error retry loop with appended correction + loud exhaustion (SC3), per-attempt JSONL logging contract (D-13/D-14), strict-schema drift-lock (Pattern 2)

**Wave 4** *(blocked on Wave 3 completion; needs OPENROUTER_API_KEY)*

- [x] 02-04-PLAN.md — Real-API harness: bilingual fixtures, slug probe, `pytest -m llm` runs through the gateway, blocking human verification of PT-BR quality (SC2)

**Wave 5** *(gap closure — closes the SC3 containment gap found by 02-VERIFICATION)*

- [x] 02-05-PLAN.md — Gap closure: contain malformed-but-200 response shapes (empty choices / None / non-str content) in the gateway via the CR-01 fix — same containment path as invalid content, pinned offline (SC3, PROFILE-03)

### Phase 3: Resume Vertical Slice

**Goal**: The first proof of core value — paste a job description, pick the language, and get grounded, keyword-targeted resume sections with an honest view of keyword coverage.
**Mode**: mvp
**Depends on**: Phases 1 and 2
**Requirements**: RESUME-01, RESUME-02, RESUME-03, RESUME-04, PROFILE-02
**Success Criteria** (what must be TRUE):

  1. User pastes a job description, chooses PT-BR or EN for the run, and receives sectioned resume content (summary, experience bullets, skills) in the chosen language.
  2. User sees the keywords extracted from the JD (skills, tools, titles, certs) that generation is targeting.
  3. Every claim in the generated sections traces to a master-profile fact — the output contains no metric, technology, or date absent from the profile (the AI rephrases, never invents).
  4. User sees a keyword coverage checklist showing which JD keywords made it into the resume and which did not — no numeric score.
  5. Before generating, user sees a completeness lint tying profile gaps to the JD (e.g., "no metrics for job X", "JD requires skill Y missing from profile").

**Plans**: 5/5 plans executed
**UI hint**: yes

Plans:
**Wave 1**

- [x] 03-01-PLAN.md — Engine: strict section contracts (3 models + hand-maintained wire schemas + drift-lock), 3 meta-prompts with the D-07 grounding rule, gateway stage registration, profile-fact serialization (RESUME-03, RESUME-01)

**Wave 2** *(blocked on Wave 1)*

- [x] 03-02-PLAN.md — Deterministic checks: keyword coverage matcher (lookaround boundaries, run-language, auditable matched terms) + JD-tied completeness lint (D-04 a/b/c, non-blocking) (RESUME-04, PROFILE-02)

**Wave 3** *(blocked on Waves 1-2)*

- [x] 03-03-PLAN.md — Orchestration + routes: run_resume_pipeline, POST /api/resume/lint + /api/resume/gerar (sync def, 200 envelope, all-or-nothing, router-before-mount) (RESUME-01/02/04, PROFILE-02)

**Wave 4** *(blocked on Wave 3)*

- [x] 03-04-PLAN.md — Frontend Currículo slice: nav enable + view switch, typed client, form/lint/keywords+coverage/result zones per approved UI-SPEC (RESUME-01/02/04, PROFILE-02)

**Wave 5** *(blocked on Waves 1-4; end-of-phase gate — depends_on 03-04 so the browser walkthrough runs against the finished Currículo screen)*

- [x] 03-05-PLAN.md — Grounding proof + real-API bilingual harness + end-of-phase human verification (RESUME-03, RESUME-01)

### Phase 4: PDF Export + ATS Self-Check

**Goal**: The user can export a genuinely sendable resume — a single-column Google-format PDF whose text layer is proven to parse correctly, automatically, in both languages.
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: REVIEW-02, REVIEW-03
**Success Criteria** (what must be TRUE):

  1. User exports the resume as a single-column Google-format PDF (classic sections, simple fonts, no tables/side columns/icons) that matches what was reviewed in-app.
  2. The automated parse-back extraction gate passes on every export: text extracts in reading order with contact first, canonical headings, co-occurring company/title/dates, and intact PT-BR accents — verified in both PT-BR and EN exports.
  3. User can run the ATS self-check in-app and see verification of section order and keyword survival for the exported PDF, in both languages.

**Plans**: 3/3 plans executed

Plans:
**Wave 1** *(gate first per D-02 — engine choice stays empirical)*

- [x] 04-01-PLAN.md — Package legitimacy checkpoint (playwright==1.62.0 + pypdf>=6.19.0) + gate-first tracer: engine seam (pdf.py), engine-agnostic HTML template mirroring the D-05 montage, pypdf parse-back gate with contact-first/heading-order/co-occurrence/accent-integrity checks, proven on real Chromium renders in both languages (REVIEW-02)

**Wave 2** *(blocked on Wave 1 — endpoint consumes the proven gate)*

- [x] 04-02-PLAN.md — Self-check payload builder (order rows + honest keyword survival via the Phase 3 matcher) + POST /api/resume/exportar with the strict request model, 200-envelope bytes+filename+selfcheck, gate-failure rejection (D-07/D-08), full API test family (REVIEW-02, REVIEW-03)

**Wave 3** *(blocked on Wave 2 — frontend consumes the envelope; ends with human verification)*

- [x] 04-03-PLAN.md — Frontend Zone 6: typed export client + blob download, Exportar PDF CTA + self-check panel per the approved UI-SPEC, symmetric locking + regeneration reset, end-of-phase human verification of SC1/SC3/SC2-EN (REVIEW-02, REVIEW-03)

**UI hint**: yes

### Phase 5: Review Flow + Fact Safety

**Goal**: Before anything is exported, the user is the quality gate — regenerating individual sections, editing text inline, and seeing exactly what the AI changed relative to profile facts.
**Mode**: mvp
**Depends on**: Phases 3 and 4
**Requirements**: REVIEW-01
**Success Criteria** (what must be TRUE):

  1. User regenerates a single section without affecting the others, optionally steering the regeneration with a hint.
  2. User edits any generated text inline in the app, and the edited version is exactly what the preview and the exported PDF show.
  3. User sees a side-by-side comparison of profile source facts vs generated text, making any invention immediately visible.
  4. Regenerating a section never silently destroys user edits — prior versions of each section remain accessible, and the edit policy (ephemeral vs written back to profile files) is explicit in the UI.

**Plans**: 4/4 plans executed
**UI hint**: yes

**Wave 1**

- [x] 05-01-PLAN.md — Tracer: per-section regeneration end-to-end — POST /api/resume/regenerar (one run_stage, full merged secoes, byte-identical siblings, recomputed coverage), hint-as-data compose, offline regen test family, "Regenerar seção" + "Adicionar dica" wiring on the result screen (REVIEW-01 SC1)

**Wave 2** *(blocked on Wave 1)*

- [x] 05-02-PLAN.md — Inline editor + Editado badge + version stack + SC4 locking matrix (D-01/D-02/D-04/D-08/D-12/D-14 confirm strips)

**Wave 3** *(blocked on Wave 2)*

- [x] 05-03-PLAN.md — Comparison panel: lib/comparison.ts port of the fold/numeral mechanics + facts-vs-generated two-column panel with deterministic invention highlights as suspicion (REVIEW-01 SC3)

**Wave 4** *(blocked on Waves 1-3; end-of-phase gate)*

- [x] 05-04-PLAN.md — Checkpoint: SC4 locking matrix + comparison + edits→export UAT (autonomous:false; resolved-as-deferred per run convention)

### Phase 6: LinkedIn Module + Bilingual Hardening

**Goal**: State a career objective once and get complete, length-compliant LinkedIn sections in PT-BR or EN — copy-paste ready — by reusing the resume engine wholesale (prompts and block types only).
**Mode**: mvp
**Depends on**: Phases 2, 3, and 5 (reuses gateway, pipeline pattern, run store, and review UI)
**Requirements**: LI-01, LI-02, LI-03, LI-04, LI-05
**Success Criteria** (what must be TRUE):

  1. User states a career objective (target roles, seniority, key technologies), chooses the language, and all LinkedIn outputs are generated from it.
  2. User gets a headline (≤220 chars), About section (≤2600), per-experience descriptions (≤2000 each), and a prioritized skills list — each inside its limit with a visible character counter; nothing is silently truncated.
  3. All outputs are copy-paste text blocks the user can paste straight into LinkedIn.
  4. PT-BR outputs pass the language QA gate (terminology glossary applied, no English bleed), and the both-language fixture suite runs as definition-of-done for every prompt change.

**Plans**: 6 plans

Plans:
**Wave 1**

- [ ] 06-01-PLAN.md — Tracer: linkedin-headline end-to-end (config constants, headline stage + prompt, pipeline, /api/linkedin/gerar, LinkedInHome skeleton with counter + Copiar) + Wave-0 seeds: all 4 wire schemas drift-locked, over-limit-safe (LI-01, LI-02)

**Wave 2** *(blocked on Wave 1)*

- [ ] 06-02-PLAN.md — Backend expansion: 3 remaining stages + prompts (experiências max_tokens 4000-8000), full 4-block pipeline with limites/alignment/dedupe, /api/linkedin/lint (run_lint_only reuse) + /api/linkedin/regenerar (Phase 5 semantics) (LI-03, LI-04, LI-05)

**Wave 3** *(blocked on Wave 2)*

- [ ] 06-03-PLAN.md — Frontend expansion: lint zone, four-block result card (experiência group + skills ordered list), Copiar everywhere, over-limit flags + editor save guard, versions + comparison, regen wiring + locking matrix (LI-02..LI-05)

**Wave 4** *(blocked on Wave 2)*

- [ ] 06-04-PLAN.md — QA gate backend: prompts/glossario.md + app/linkedin/qa.py (strict loader, deterministic case-preserving apply, mechanical bleed detection), PT-BR-only wiring glossary-before-bleed, qa envelope key, vector suite (SC4)

**Wave 5** *(blocked on Waves 3-4)*

- [ ] 06-05-PLAN.md — "Verificação de idioma" QA panel + DoD harness: bilingual real-API LinkedIn fixtures over OBJECTIVE_PT/EN (pytest -m llm green = SC4 definition-of-done) (SC4)

**Wave 6** *(blocked on Wave 5; end-of-phase gate — autonomous:false, resolved-as-deferred per run convention)*

- [ ] 06-06-PLAN.md — Checkpoint: copy-paste UX + counters + QA panel framing + max-volume backstop UAT (LI-01..LI-05)

**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation — Scaffold + Master Profile | 3/3 | In Progress|  |
| 2. LLM Generation Core | 5/5 | Complete    | 2026-09-26 |
| 3. Resume Vertical Slice | 5/5 | Complete    | 2026-09-26 |
| 4. PDF Export + ATS Self-Check | 3/3 | Complete    | 2026-09-27 |
| 5. Review Flow + Fact Safety | 4/4 | Complete    | 2026-09-29 |
| 6. LinkedIn Module + Bilingual Hardening | 0/6 | Not started | - |
