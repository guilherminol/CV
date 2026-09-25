# Phase 1: Foundation — Scaffold + Master Profile - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 1-Foundation — Scaffold + Master Profile
**Areas discussed:** Bilingual schema shape, Profile file layout, Phase 1 UI scope, Example data persona

---

## Bilingual schema shape

| Option | Description | Selected |
|--------|-------------|----------|
| Localized maps (Recommended) | One field holding a language→text map (`summary: {pt-BR: …, en: …}`); single source of truth; trivial to add a language | ✓ |
| Suffixed fields | Separate flat fields per language (`summary_pt` / `summary_en`) with fallback; flatter but noisy and easy to desync | |
| Per-language files | Fully duplicated `profile.pt-BR.md` + `profile.en.md`; simplest schema, guaranteed drift | |

**User's choice:** Localized maps
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Narrative only | Summary/descriptions/impacts localized; titles, companies, tech, dates single-value | |
| Narrative + role titles | Above plus job titles localized ('Senior Software Engineer' / 'Engenheiro de Software Sênior') | ✓ |
| Everything user-visible | Any human-written field localizable, incl. skills descriptions, cert notes | |

**User's choice:** Narrative + role titles
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Base + fallback (Recommended) | Schema requires one declared base language; others optional; fallback to base; never blocks | ✓ |
| Fallback + lint flag | Same, plus Phase 3 lint explicitly reports translation gaps | |
| Both languages required | Schema demands pt-BR and en everywhere; forces translation before load | |

**User's choice:** Base + fallback
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| PT-BR base (Recommended) | User writes naturally in PT-BR, adds EN over time | ✓ |
| EN base | English-first, PT-BR translations added for Brazilian applications | |
| No declared base | Each field carries whichever languages exist; fallback ambiguous | |

**User's choice:** PT-BR base
**Notes:** —

---

## Profile file layout

| Option | Description | Selected |
|--------|-------------|----------|
| Single profile.md (Recommended) | YAML frontmatter + Markdown body; one file to edit/commit/validate | ✓ |
| Split by section | content/ folder, one file per section; loader joins, cross-file consistency is manual | |
| Single now, split later | Single file with section-wise schema so a later split is mechanical | |

**User's choice:** Single profile.md
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| All in frontmatter (Recommended) | Structured data AND bilingual narrative as localized maps in YAML; body minimal | ✓ |
| Body = PT-BR narrative | Markdown body carries PT-BR narrative; frontmatter carries EN translations | |
| Body blocks per language | Body uses language-hinted Markdown blocks; custom parse convention | |

**User's choice:** All in frontmatter
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| content/ folder (Recommended) | `content/profile.md` — content separated from code | ✓ |
| Repo root | `profile.md` next to README, maximum visibility | |
| data/ folder | Generic data dir; leaves `content/` for outputs/prompts | |

**User's choice:** content/ folder
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Flag in the file (Recommended) | `example: true` in frontmatter; banner shows while set; remove flag when real | ✓ |
| Separate example file | `profile.example.md` kept pristine + real `profile.md` to fill | |
| Fake-marker detection | Warn while known fake markers detected; brittle string-matching | |

**User's choice:** Flag in the file
**Notes:** —

*Second pass (user asked for more questions in this area):*

| Option | Description | Selected |
|--------|-------------|----------|
| Full resume set (Recommended) | Contact, summary, experiences, education, skills, certifications, languages, projects | ✓ |
| Minimal four | Only experiences, projects, technologies, impacts + minimal contact | |
| Middle ground | Four + education and skills; postpone certs/languages | |

**User's choice:** Full resume set
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Embedded per experience (Recommended) | Each experience carries its own impacts array; natural grounding per job | ✓ |
| Separate impacts section | Top-level impacts with IDs referencing experiences/projects | |
| Embedded + derived highlights | Embedded plus app-derived highlights list | |

**User's choice:** Embedded per experience
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Categorized groups (Recommended) | Skills grouped by category (linguagens, frameworks, ferramentas, cloud…) | ✓ |
| Flat list | One flat list of tech names | |
| Categorized + levels | Groups plus optional level/years per skill | |

**User's choice:** Categorized groups
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Reject unknown keys (Recommended) | Pydantic `extra='forbid'`; typos fail loudly with exact key/location | ✓ |
| Warn and ignore | Unknown keys listed as warnings; typo'd sections silently vanish | |

**User's choice:** Reject unknown keys
**Notes:** —

---

## Phase 1 UI scope

| Option | Description | Selected |
|--------|-------------|----------|
| Shell + profile home (Recommended) | Shell + 'Perfil' status home: load status, in-app validation errors, completeness, banner | |
| Bare shell | Header + placeholder page + banner; errors terminal-only | |
| Shell + profile + preview | Profile home PLUS rendered preview of the profile formatted like a resume page | ✓ |

**User's choice:** Shell + profile + preview (chose the richer option over the recommended one)
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| In-app + terminal (Recommended) | Broken profile blocks app; error in UI (PT-BR) and uvicorn logs (full detail) | ✓ |
| In-app only | UI only; backend logs stay clean | |
| Terminal only | Generic UI message; details in logs | |

**User's choice:** In-app + terminal
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| PT-BR + technical detail (Recommended) | PT-BR friendly message with exact file/field path; raw Pydantic in terminal | ✓ |
| Fully PT-BR | Everything translated; blurs precise cause | |
| Raw errors only | Raw Pydantic/English everywhere; user-hostile for PT-BR interface | |

**User's choice:** PT-BR + technical detail
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Validate on every load (Recommended) | No caching; re-read + re-validate per request; refresh = current | ✓ |
| Manual reload button | 'Recarregar perfil' button triggers re-validation on demand | |
| File watcher auto-reload | Backend watches file, pushes updates; most moving parts | |

**User's choice:** Validate on every load
**Notes:** —

---

## Example data persona

| Option | Description | Selected |
|--------|-------------|----------|
| Realistic persona, your shape (Recommended) | Fake but realistic professional mirroring the user's field/level | ✓ |
| Generic fictional persona | 'Maria Silva, dev full-stack, Empresa Exemplo' — clearly placeholder, weak as template | |
| Obviously fake | Cartoonish ('Exemplo da Silva @ Empresa Exemplo') — max clarity, min usefulness | |

**User's choice:** Realistic persona, your shape
**Notes:** User specified their shape: "Atualmente AI engineer com foco em IA generativa, e também backend e front além de um pouco de infra desses serviços" — seniority: Sênior.

| Option | Description | Selected |
|--------|-------------|----------|
| Fully bilingual (Recommended) | Every localized field carries {pt-BR, en}; proves schema end-to-end | ✓ |
| Mixed (shows fallback) | PT-BR everywhere + EN on some fields; demonstrates fallback | |
| PT-BR only | Simplest; doesn't demonstrate localization shape (ROADMAP SC4) | |

**User's choice:** Fully bilingual
**Notes:** —

## Claude's Discretion

- Scaffold mechanics: package versions per STACK.md, ESLint/Prettier, ports, Vite proxy, FastAPI mounting order
- Schema key naming language (English snake_case recommended)
- Pydantic model organization, loader structure, test framework/fixtures
- UI implementation details within decided scope

## Deferred Ideas

None — discussion stayed within phase scope.
