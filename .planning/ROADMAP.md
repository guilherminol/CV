# Roadmap: Career Tailor

## Overview

Career Tailor goes from an empty repo to a localhost app the user actually sends job applications with. The build order follows the dependency graph: the master profile schema is the root of everything, so it lands first with loud validation; then the LLM gateway proves OpenRouter structured outputs, logging, and bilingual fixtures before any product surface exists; then the first vertical slice delivers core value (paste JD → grounded, keyword-targeted resume sections); the PDF phase makes the output genuinely sendable, with the ATS parse-back gate built as the phase's first task — not bolted on after; the review flow turns the user into the quality gate before export; and the LinkedIn module reuses the whole engine, paying only for prompts and block types. Language (PT-BR/EN) is a prompt parameter from Phase 2 onward and gets hardened — glossary, QA gate, both-language fixtures — in the final phase.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation — Scaffold + Master Profile** - App runs locally with a PT-BR interface; git-versioned master profile schema with example data, validated loudly on load
- [ ] **Phase 2: LLM Generation Core** - One logged, schema-validated, bilingual OpenRouter gateway with meta-prompts as editable git files and an input-agnostic {en, pt} keyword engine
- [ ] **Phase 3: Resume Vertical Slice** - Paste JD → grounded, keyword-targeted resume sections with visible keyword extraction, coverage checklist, and completeness lint
- [ ] **Phase 4: PDF Export + ATS Self-Check** - Sendable single-column Google-format PDF whose text layer is proven by an automated parse-back gate, in both languages
- [ ] **Phase 5: Review Flow + Fact Safety** - Per-section regenerate, inline editing, and source-vs-generated fact diff before export
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
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Walking Skeleton: scaffold (gitignore-first, uv backend on pinned 3.12, Vite frontend) + end-to-end perfil path (content/profile.md → Pydantic → GET /api/profile → PT-BR shell with placeholder banner), dev + prod modes
- [ ] 01-02-PLAN.md — Profile contract: full strict schema (localized maps, base pt-BR, extra=forbid everywhere), fail-fast loader with PT-BR error localization, fully bilingual example persona, completude in the API envelope
- [ ] 01-03-PLAN.md — Perfil UI: three-state Perfil home (loading / error panel with verbatim PT-BR lines / ok), completeness grid, resume-style preview, finalized run docs

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
**Plans**: TBD

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
**Plans**: TBD
**UI hint**: yes

### Phase 4: PDF Export + ATS Self-Check
**Goal**: The user can export a genuinely sendable resume — a single-column Google-format PDF whose text layer is proven to parse correctly, automatically, in both languages.
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: REVIEW-02, REVIEW-03
**Success Criteria** (what must be TRUE):
  1. User exports the resume as a single-column Google-format PDF (classic sections, simple fonts, no tables/side columns/icons) that matches what was reviewed in-app.
  2. The automated parse-back extraction gate passes on every export: text extracts in reading order with contact first, canonical headings, co-occurring company/title/dates, and intact PT-BR accents — verified in both PT-BR and EN exports.
  3. User can run the ATS self-check in-app and see verification of section order and keyword survival for the exported PDF, in both languages.
**Plans**: TBD
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
**Plans**: TBD
**UI hint**: yes

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
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation — Scaffold + Master Profile | 0/3 | Not started | - |
| 2. LLM Generation Core | 0/TBD | Not started | - |
| 3. Resume Vertical Slice | 0/TBD | Not started | - |
| 4. PDF Export + ATS Self-Check | 0/TBD | Not started | - |
| 5. Review Flow + Fact Safety | 0/TBD | Not started | - |
| 6. LinkedIn Module + Bilingual Hardening | 0/TBD | Not started | - |
