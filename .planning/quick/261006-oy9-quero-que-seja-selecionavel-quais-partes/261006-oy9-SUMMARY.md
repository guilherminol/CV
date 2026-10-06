---
phase: quick-261006-oy9
plan: 01
subsystem: resume-export + master-profile
tags: [export-selection, per-experience-skills, parse-back-gate, pydantic-strict, react-panel]
requires:
  - backend/app/routes/export.py (ExportarRequest/ExportarSecoes strict envelope)
  - backend/app/export/render.py (_sections_content single traversal, CR-01 gate coupling)
  - backend/app/profile/models.py (_Strict extra=forbid schema)
  - backend/app/resume/facts.py (serialize_profile_facts supply line)
provides:
  - SelecaoExportacao (7 default-True flags + item index lists, all-false 422) at POST /api/resume/exportar
  - payload-filter-before-render/gate (filter → join → render → PDF → gate on ONE filtered payload)
  - Experience.skills profile schema field + per-experience `tecnologias:` facts line
  - ExportSelection.tsx panel (7 section toggles + per-item experiencias/projetos)
affects:
  - frontend export payload now carries optional `selecao` (omitted = behavior-identical)
  - fetched profile DTO now carries `skills` per experience (travels verbatim back)
tech-stack:
  added: []
  patterns:
    - model_copy(update=...) filtered profile views (validator-skip safe: subsets/[] only)
    - enumerate-membership index filtering (out-of-range/negative silently ignored)
    - duck-typed filtered views (_SecoesFiltradas) keeping render.py selection-agnostic
key-files:
  created:
    - frontend/src/components/ExportSelection.tsx
  modified:
    - backend/app/profile/models.py
    - backend/app/resume/facts.py
    - backend/app/routes/export.py
    - backend/app/export/render.py
    - content/profile.md
    - backend/tests/test_resume_schema.py
    - backend/tests/test_resume_grounding.py
    - backend/tests/test_export_api.py
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/pages/CurriculoHome.tsx
decisions:
  - "Selection is a PRESENTATIONAL post-validation filter inside the export route — the generation pipeline contract is untouched (D-02); omitted selecao is byte-identical to today"
  - "The filter runs BEFORE join/render/gate and _expected_doc consumes the SAME filtered views — the parse-back gate can only verify the document that actually renders (T-OY9-02)"
  - "perfil.experiences is NEVER filtered (positional date join); only secoes.experiencias + perfil section lists are filtered; model_copy(update=) skips validators safely (subsets of validated entries)"
  - "Zero-entry hiding extended to generated sections in render.py — safe by construction under the min_length=1 floors with no selection"
  - "Per-experience skills land as a `tecnologias:` line ONLY when non-empty (skill-less profiles keep byte-stable facts blocks), reusing the project-block label convention (D-03)"
  - "skills content LOCKED to each entry's own description/impact text; Red Lion honestly empty (D-03 grounding rule)"
  - "Selection resets to SELECAO_TODOS on every wholesale secoes swap (gerar AND per-section regen — a regen can change experiencias length and silently re-point indices)"
metrics:
  duration: 14 min
  completed: 2026-10-06
  tasks: 3
  files: 12
actuals:
  tokens: 12000
  tasks: 3
  commits: 3
status: complete
---

# Quick Task 261006-oy9: Selectable resume sections at export + per-experience skills Summary

**One-liner:** Section+item-level PDF export selection flowing through the payload so the parse-back gate verifies exactly the filtered document, plus per-experience `skills` in the master profile feeding the LLM facts as a `tecnologias:` line — generation contract and PDF layout untouched.

## What Was Built

### Task 1 — Per-experience skills (D-03, D-04) — commit `38f7f37`
- `Experience.skills: list[str] = []` (Project.technologies precedent; extra=forbid schema extended FIRST so the YAML edit loads).
- `serialize_profile_facts` emits `tecnologias: {', '.join(exp.skills)}` inside each experience block — only when non-empty, after `descrição:`, before impacts (project-block order).
- `content/profile.md`: locked skills lists on all 5 experiences — Group Software (LangGraph, RAG, OpenRouter, LLMs, IA Generativa, Integração WhatsApp), H&P (IA Generativa, Bancos de dados relacionais, RAG, Embeddings, LLMs, Governança de dados), The Brooklyn Brothers (React, Context API, JavaScript (ES6+), HTML5, CSS3, SEO, Acessibilidade, Scrum), Kenzie Academy Brasil (React, CSS, HTML, Git/GitHub, Context API, Redux, styled-components, Testes unitários), Red Lion honest `[]`. Every item grounded in that entry's own text; global `skills:` section untouched.
- Tests: skills round-trip + default + strict-mode (test_resume_schema.py); tecnologias line presence/order/absence (test_resume_grounding.py). Fresh `load_profile()` proof: 5 entries, Red Lion empty, Brooklyn order asserted.

### Task 2 — Export selection backend (D-01, D-02) — commit `1894178`
- `SelecaoExportacao`: strict (extra=forbid), seven default-True flags + `experiencias_indices`/`projetos_indices` (None = all); all-seven-false raises → FastAPI 422 (min_length house precedent).
- `ExportarRequest.selecao: SelecaoExportacao | None = None` — absent = export everything; today's payloads unchanged.
- `_aplicar_selecao` runs FIRST in the handler: filtered `_SecoesFiltradas` (resumo '' when off, index-filtered experiencias via enumerate membership — [99, -1] silently selects nothing, False section ignores its indices) + filtered profile via `model_copy(update={...})` (education/certifications/languages → [], projects → index subset). `perfil.experiences` NEVER filtered (positional date join). `_expected_doc` refactored to take the filtered views + idioma.
- `render.py`: zero-entry hiding extended to resumo/experiencias/habilidades — no-op under the min_length=1 floors, adapts automatically under a filtered payload because `rendered_section_keys`/`iter_rendered_strings` traverse the SAME `_sections_content` (CR-01 intact).
- Tests (6 new): explicit all-True ok envelope, real-render subset export (drops experience 2 + formacao off → green gate over the real Chromium PDF, `formacao` absent from ordem rows), all-false 422, unknown selecao key 422, out-of-range indices ok, False-section-ignores-indices ok.

### Task 3 — Frontend selection panel (D-01, D-02) — commit `be0c9cf`
- `client.ts`: `SelecaoExportacaoDTO` + `ExportarRequest.selecao?` + `ExperienceDTO.skills?` (tsc -b is the Pydantic↔TS drift gate).
- `ui.ts`: `SELECAO_TITLE`, `SELECAO_CAPTION`, `SELECAO_SECOES` (pt-BR = PREVIEW_SECTIONS values, en = render.py HEADINGS['en']), `SELECAO_SEM_SECAO`.
- `ExportSelection.tsx` (new): render-only bordered panel — 7 section checkboxes in D-05 render order; per-entry `company — title` checkboxes under experiencias; projetos grouped by scope (profissional first) with ResumeResult SCOPE_LABELS/tLang conventions. Item toggles maintain index arrays, dissolving to `undefined` when all items are selected; unchecked sections gray their items out. JSX text children only; no new deps.
- `CurriculoHome.tsx`: `selecao` state (module-local `SELECAO_TODOS`), panel mounted between `<ResumeResult>` and `<ExportZone>`, `selecao` rides `exportar.mutate`; WR-01 mirror derives `nenhumaSecaoSelecionada` and extends the CTA disable with the `SELECAO_SEM_SECAO` hint (the 422 is prevented at the source); selection resets to SELECAO_TODOS inside BOTH wholesale-swap onSuccess handlers (full gerar + per-section regenerar); selection changes never touch receipt/error state.

## Verification (all green)

| Gate | Result |
|------|--------|
| `pytest tests/test_resume_schema.py tests/test_resume_grounding.py -q` | 34 passed |
| fresh `load_profile()` skills assertions + tecnologias blob | SKILLS-OK |
| `pytest tests/test_export_api.py -q` | 21 passed (incl. real-render subset gate) |
| `pytest tests/test_export_gate.py -q` | 35 passed |
| `pytest -q` (full offline suite) | 443 passed, 9 deselected (llm) |
| `npm run build` (tsc -b + vite) | green |

## Deviations from Plan

**1. [Verification methodology — Task 1 ADDITIVE-OK sub-check]**
- **Found during:** Task 1 verify
- **Issue:** The plan's `ADDITIVE-OK` gate ran `git diff --numstat -- content/profile.md` against HEAD, which includes the OTHER session's pre-existing uncommitted deletions in that file (82 deleted lines of in-flight project/impact text rewraps — present before this task started, per the plan's own DIRTY-TREE WARNING). The check as written can only pass on a clean-for-that-file tree, which this repo explicitly does not have.
- **Resolution:** My five profile edits were verified insertions-only by direct diff inspection — every Edit preserved its old_string verbatim; all 82 deleted lines lie in pre-existing rewrap hunks untouched by this plan. SKILLS-OK + 34 green tests prove the YAML loads fresh. Recorded in the WINDOWS ledger as a `deviation` entry.
- **Commit:** 38f7f37 (the diff carries the shared file's mixed hunks per the q9v convention)

**2. [Constraint override — Task 3 commit scope]**
- **Found during:** Task 3 verify
- **Issue:** The plan's Task 3 verify command adds the task directory (`.planning/quick/261006-oy9-…`) to the commit; the orchestrator constraint forbids committing docs artifacts (PLAN/CONTEXT/SUMMARY live there; the orchestrator handles the docs commit).
- **Resolution:** Committed ONLY the plan's `files_modified` code/content files. Backend files were already committed atomically in Tasks 1–2, so Task 3's commit carries the 4 frontend files.

No bugs auto-fixed (no Rule 1 triggers), no missing critical functionality found (Rule 2 mitigations from the threat register were all implemented in-plan), no blocking issues (Rule 3).

## Threat Model Dispositions (all applied)

- **T-OY9-01** (tampering via selecao): extra=forbid 422 on unknown keys; enumerate-membership filtering (out-of-range/negative ignored, never blind-indexed); all-seven-false 422 — implemented + tested.
- **T-OY9-02** (filtered doc vs gate expectations): filter BEFORE join/render/gate; `_expected_doc` consumes the SAME filtered views; real-render subset test proves a green gate over the filtered PDF — implemented + tested.
- **T-OY9-03** (skills widen the facts blob): accepted — strings extracted from profile text already sent; runs.jsonl untouched.
- **T-OY9-04** (HTML injection): selection adds booleans/ints only; all rendered strings still pass `esc()` — traversal unchanged.

## Known Stubs

None.

## Self-Check: PASSED

- Files: all 12 `files_modified` exist (11 modified + `frontend/src/components/ExportSelection.tsx` created).
- Commits: `38f7f37`, `1894178`, `be0c9cf` all present on master (`git log` verified); plan ledger base `a11b440` → 3 commits measured (`git rev-list --count a11b440..HEAD` restricted to this task's window).
- Working tree: remaining modifications belong exclusively to the other session's in-flight work — untouched, per the q9v convention.
