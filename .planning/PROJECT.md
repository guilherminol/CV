# Career Tailor

## What This Is

A personal, locally-run web app with two modules that generate job-search content in both English and Portuguese: (1) a resume builder that produces an ATS-optimized, personalized resume (Google-recommended single-column format, PDF export) from a pasted job description, and (2) a LinkedIn profile optimizer that rewrites headline, About section, experience descriptions, and skills based on a stated career objective. Both modules draw from a single master profile — the user's complete work history, projects, technologies, and impacts — stored as Markdown/YAML files in git. All content is generated via LLM calls (OpenRouter) driven by meta-prompts, with keyword optimization targeting the current tech job market.

## Core Value

Paste a job description (or state a career objective for LinkedIn) and get polished, ATS-optimized, keyword-targeted output in English or Portuguese that the user would actually send or post — without manual rewriting from scratch.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Shared master profile: Markdown/YAML base in git, schema-validated, example data — Phase 1
- ✓ Resume generation from pasted JD (PT/EN, grounded in profile facts, coverage checklist) — Phase 3
- ✓ PDF export in Google single-column format with automated parse-back ATS gate + in-app ATS self-check — Phase 4
- ✓ Keyword optimization: extraction with PT↔EN mapping, deterministic coverage matching — Phases 2–3
- ✓ Review flow: per-section regeneration with hint, inline editing (ephemeral, explicit policy), version history, fact-vs-generated comparison with deterministic suspicion marks — Phase 5

### Active

<!-- Current scope. Building toward these. -->

- [ ] LinkedIn module: generate headline, About, experience descriptions, and skills from a career objective (PT/EN)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Job posting extraction from URL — job sites (LinkedIn, Gupy) block scraping; paste-text works with any site
- Multi-user support, auth, and cloud hosting — personal tool, runs on localhost only
- Admin CRUD UI for the master profile — Markdown/YAML files are edited directly in the user's editor
- DOCX export — PDF (ATS-friendly) covers the need; reconsider only if a vacancy explicitly demands Word
- Cover letter generation — not requested; can be a future module

## Context

- The user is a tech professional building this for their own job search; outputs must be good enough to send real applications with.
- "Google model" = the resume format Google recommends in its own hiring process: single column, no tables/side columns/icons, classic sections (contact, summary, experience, education, skills), simple fonts — parses reliably in ATS systems.
- The LinkedIn optimizer is NOT vacancy-driven: it is guided by a user-stated career objective (e.g., the type of role they're targeting). The resume module IS vacancy-driven (pasted job description text).
- OpenRouter is the LLM provider — model choice stays flexible without code changes.
- Review-in-app flow matters: the user wants to regenerate individual sections and edit generated text on screen before exporting, not a one-shot black box.
- Initial master profile ships as schema + fake example data; the user fills in real data afterwards.
- App UI language is Portuguese (user's language); generated content is PT-BR or English, selected per run.

## Constraints

- **Stack**: JavaScript frontend; Python acceptable for backend — matches user's comfort and preference.
- **LLM access**: all generation goes through OpenRouter; API key in local `.env` only.
- **Runtime**: local (localhost) only — no hosting, no auth, no external database.
- **Data store**: file-based (Markdown/YAML in git), not a database.
- **Languages**: all generated content available in both English and PT-BR.
- **Output format**: single-column ATS-friendly PDF in the Google-recommended style.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| OpenRouter as LLM provider | Model flexibility without code changes; user already plans to use it | — Pending |
| Markdown/YAML in git as master profile store | Versioned, editable in any editor, no admin UI or DB needed | — Pending |
| Review-before-export flow (per-section regenerate + inline edit) | Quality control before sending real applications | — Pending |
| PDF engine: Playwright pinned 1.62.0 (cached Chromium), empirical gate-first decision, WeasyPrint as uninstalled fallback | Zero-download setup on this machine; parse-back gate proves the text layer on every export | ✓ Phase 4 |
| EN exports localize all 7 section headings (render.py HEADINGS single source, shared with gate + self-check) | The PDF is the sendable artifact; SC2 requires canonical headings in both languages | ✓ Phase 4 [auto — silence, user review pending] |
| Edit policy: ephemeral session edits with permanent explicit notice; edits flow into export/self-check; version stack on every destructive path | User is the quality gate without mutating the master profile; SC4 "never silently destroys" | ✓ Phase 5 [auto — silence, user review pending] |
| LinkedIn module driven by career objective, not vacancy | A LinkedIn profile targets a direction, not one specific posting | — Pending |
| ATS-friendly Google-format PDF as the only resume output | ATS parsing reliability beats visual flair for job applications | — Pending |
| Local web app with simple routes + meta-prompts | Matches the "meta prompts and simple routes" vision; personal use | — Pending |
| SQLite local store for the tracker ONLY (point reversal of "file-based, not a database" — D-01); master profile stays Markdown/YAML in git; .db in a gitignored, env-overridable path (TRACKER_DB) targeted by the homelab bind mount (D-02) | Tracker data is relational CRUD (stages, events, deadlines), not versioned content; reversibility: costly (storage-layer rewrite if undone) | ✓ Phase 7 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-11 after Phase 7*
