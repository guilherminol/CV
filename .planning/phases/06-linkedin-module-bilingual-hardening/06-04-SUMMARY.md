---
phase: "06"
plan: "04"
subsystem: linkedin-bilingual-qa
tags: [linkedin, qa, glossary, bilingual, deterministic, pt-br]
requires:
  - 06-02 pipeline/envelope shape (run_linkedin_pipeline + run_linkedin_section_regen, the surfaces the qa key joins)
  - app.resume.coverage _fold/_term_pattern (the one matcher, imported — never re-implemented)
  - app.llm.prompts load_prompt fail-fast ladder (copied verbatim for load_glossario)
provides:
  - prompts/glossario.md — git-versioned, strictly-validated Markdown+YAML pair list, read fresh on every execution (D-12)
  - app/linkedin/qa.py — load_glossario (fresh-read seam), apply_glossario (deterministic case-preserving substitution + per-pair occurrence report, D-13), EN_BLEED_TERMS (curated static list), detect_english_bleed (fold+lookaround, mechanical, D-14), run_linkedin_qa (glossary-before-bleed orchestration, pt-BR gate)
  - the `qa` envelope key contract: pt-BR ok envelopes always carry {"glossario": [...], "bleed": [...]}; en ok envelopes always carry null — full run AND per-section regen both recompute over the full PT-BR state
affects:
  - 06-05 (frontend QA panel "Verificação de idioma" renders this payload verbatim; DoD harness asserts the qa keys)
tech-stack:
  added: []
  patterns:
    - "glossary-before-bleed order contract: substitution MUTATES the returned secoes, bleed runs on the post-glossary text (the report describes exactly the copied text)"
    - "match on the ORIGINAL text (re.IGNORECASE + lookarounds + re.escape); fold machinery for bleed MATCHING only, never rewriting"
    - "case-preserving replacement: ALL-CAPS → upper para, Capitalized → capitalized para, else para as written"
    - "habilidades are bleed-detected but NEVER rewritten (substituting inside a skill name would silently alter the deliverable list)"
    - "loader fail-fast ladder reuse: FileNotFoundError/yaml.YAMLError/UnicodeDecodeError/ValidationError → PromptError with PT-BR message + raw terminal-only split"
key-files:
  created:
    - prompts/glossario.md
    - backend/app/linkedin/qa.py
    - backend/tests/test_linkedin_qa.py
  modified:
    - backend/app/linkedin/__init__.py
    - backend/app/linkedin/pipeline.py
    - backend/tests/test_linkedin_pipeline.py
    - backend/tests/test_linkedin_regen_pipeline.py
    - backend/tests/test_linkedin_api.py
decisions:
  - "EN_BLEED_TERMS curated conservatively: multi-word constructions + EN action verbs/first-person forms + only no-PT-collision short tokens ('and', 'with', 'from'); 'for' deliberately DROPPED — it is a real PT-BR verb ('se for necessário') and would false-positive on every such sentence; the drop is pinned by a vector."
  - "ParGlossario carries min_length=1 on de/para [Rule 2]: an empty `de` would substitute at every word boundary (whole-text corruption) and an empty `para` would silently delete the term — a malformed pair can never reach the substitution engine (T-06-10)."
  - "prompts_dir seam threaded through BOTH pipeline functions to load_glossario (same offline-injection discipline as client/runs_log/PROFILE_PATH); production resolves the repo-root prompts/ fresh per execution."
  - "Bleed row labels: experiências rows carry the entry's company (the fixed profile-fact anchor the frontend renders as the sub-block header); habilidade rows carry the skill string itself — precise location, rendered verbatim as `{termo} — {seção}` per UI-SPEC."
  - "limites computed AFTER the glossary substitution so the character counters describe the final (post-glossary) text."
metrics:
  duration: 11 min
  completed: 2026-09-29
actuals:
  tokens: 14133 # chars/4 over the realized diff (56533 diff chars)
  tasks: 2
  commits: 2 # measured: git rev-list --count 8e68a863..HEAD
plan_head_before: 8e68a863cfb0e6c7341d4142aed93c76f9da548e
status: complete
---

# Phase 6 Plan 4: PT-BR Bilingual QA Core Summary

**One-liner:** deterministic post-generation QA is live on every LinkedIn generation success — a user-editable git-versioned glossário applied as case-preserving mechanical substitutions with a per-pair occurrence report, plus curated static English-bleed detection, both computed over the post-glossary text the user copies and returned as the non-blocking `qa` envelope key (pt-BR dict / en null), zero LLM judge.

## What Was Built

- **Glossário + qa module (Task 1):** `prompts/glossario.md` (D-12) ships 3 conservative seed pairs (machine learning → aprendizado de máquina, data governance → governança de dados, data science → ciência de dados) in YAML frontmatter with an edit-and-next-run discipline body (consolidated tech terms without a good equivalent must NOT be listed — bleed flags, never rewrites). `backend/app/linkedin/qa.py`: `load_glossario` copies the load_prompt fail-fast ladder verbatim (strict `GlossarioSpec`/`ParGlossario` extra=forbid, fresh read, call-time `prompts_dir` seam, PromptError with PT-BR message + raw terminal-only split); `apply_glossario` substitutes case-insensitively over the ORIGINAL text with lookaround bounds and re.escape (never folded copies, never `\b`), preserving the match's case shape and reporting every pair with count > 0; `EN_BLEED_TERMS` is a curated static tuple owned in code (multi-word constructions, EN action verbs, first-person forms, three no-PT-collision short tokens); `detect_english_bleed` imports the coverage `_fold`/`_term_pattern` primitives (one matcher, many inputs) and returns `{"termo", "secao"}` rows; `run_linkedin_qa` is the orchestration seam — glossary FIRST on the prose surfaces (headline, sobre, each experiência descricao, mutated in place), then bleed over the POST-glossary text, habilidades detected but never rewritten, `en` returns None before the file is even read. The package `__init__` re-exports the QA surface. 48 offline vectors pin all of it (case shapes, lookaround boundaries, UTF-8 accent intactness byte-for-byte, occurrence counts, zero-match no-op, escaped-literal injection safety, the full loader ladder, fresh-read seam, one positive vector per shipped bleed term, accented PT-BR negative controls, the tech-noun exclusion, the orchestration order contract, the language gate, the loud-empty payload, and a signature pin proving no qa function takes a client).
- **Pipeline wiring (Task 2):** both `run_linkedin_pipeline` and `run_linkedin_section_regen` recompute QA over the FULL PT-BR state on every generation success: glossary applied first — MUTATING the returned secoes, so the displayed text IS the post-glossary text the user copies (D-13 + research constraint #4) — then bleed detection over that post-glossary text; `limites` computed after the substitution so the counters describe the final text. The envelope contract lands additively: pt-BR ok envelopes carry `qa: {"glossario": [...], "bleed": [...]}` (loud-empty lists when clean), EN ok envelopes carry `qa: null`. The regen response's QA describes the whole merged artifact (Pitfall 4 truthfulness — a submitted sibling's EN term is flagged alongside the regenerated block's). A glossário load failure during gerar surfaces as the erro envelope end-to-end (PromptError → PT-BR lines, raw detail terminal-only). The suite stays 100% offline: `prompts_dir` threaded through both pipeline functions as the injection seam, canned texts proven clean.

## Tasks Completed

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | glossário file + qa module (loader, deterministic apply, bleed detection) + vectors | 51154ed |
| 2 | Wire QA into both pipelines (PT-BR only, glossary-before-bleed) + envelope qa key | 6a85784 |

## Verification

- `cd backend && uv run pytest tests/test_linkedin_qa.py tests/test_linkedin_pipeline.py tests/test_linkedin_regen_pipeline.py tests/test_linkedin_api.py -q` → **113 passed**
- `cd backend && uv run pytest -q` (full offline suite) → **403 passed, 7 deselected** (397 pre-plan + 6 new wiring tests + 48 → 42 net-new qa vectors; suite stays 100% offline — no client anywhere in the QA path, provable by signatures)
- Every shipped EN_BLEED_TERMS term has a positive vector; the PT-BR negative-control test passes (including the "for"-verb curation proof) and consolidated tech proper nouns (Python, Kubernetes, machine learning) are pinned as non-flagging
- The fresh-read seam is proven at three levels: loader (mutated fixture between two calls), orchestration (`prompts_dir` seam), and the API path (the real shipped glossário flows through default `run_linkedin_qa`); the plan's manual check ("edit the file → next run picks it up") is automated by `test_glossario_is_read_fresh_between_calls`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing validation] `min_length=1` on ParGlossario fields**
- **Found during:** Task 1 (design of the strict spec)
- **Issue:** The plan's `{de, para}` spec allowed empty strings; an empty `de` reaching the substitution engine would match at every word boundary and corrupt the whole text (an empty `para` would silently delete the term) — violating T-06-10's "a malformed pair can never reach the substitution engine".
- **Fix:** `Field(min_length=1)` on both fields; a malformed empty pair now fails the loader with a PromptError naming the file, pinned by `test_malformed_empty_pair_fails_before_the_substitution_engine`.
- **Files modified:** backend/app/linkedin/qa.py, backend/tests/test_linkedin_qa.py
- **Commit:** 51154ed

**2. [Plan-completion] `prompts_dir` seam threaded through the pipeline functions**
- **Found during:** Task 2 (test design)
- **Issue:** The plan gave `load_glossario` the call-time seam but left the pipeline functions calling QA with only the real file; hermetic offline vectors for the wiring (glossary term in the sobre, EN-gate zero-substitution with a reachable glossário) needed the same injection discipline the plan mandates for `client`/`runs_log`.
- **Fix:** optional `prompts_dir` kwarg on `run_linkedin_pipeline` + `run_linkedin_section_regen`, threaded to `run_linkedin_qa`; production default unchanged (repo-root prompts/, fresh per execution).
- **Files modified:** backend/app/linkedin/pipeline.py
- **Commit:** 6a85784

**3. [Test-authoring fix — no behavior change]** One vector expectation typo in Task 1 (`e-commerce` substitution omitted "loja" from the expected string; the implementation was right). Fixed in the same commit.

## Auth Gates

None — fully offline execution, no credentials touched.

## Known Stubs

None created by this plan. (Carried forward from 06-01/06-03: the frontend QA panel for this payload is 06-05 scope — the backend envelope contract it renders is now complete and pinned.)

## Notes for 06-05 / 06-06

- The `qa` payload shape is final: `{"glossario": [{"de", "para", "ocorrencias"}], "bleed": [{"termo", "secao"}]}` — bleed `secao` is `"headline"`, `"sobre"`, the experiência entry's company, or the habilidade string itself; rows render verbatim as `{termo} — {seção}` (amber) and `{origem} → {preferido}` (gray) per UI-SPEC. Clean runs carry EMPTY lists — render the loud zero lines; en runs carry null — render the neutral note.
- Truthfulness: the panel swaps ONLY on generation success (full or regen — both recompute server-side); edits/restores keep the last report.
- Any `prompts/glossario.md` edit is "not done" until `uv run pytest -m llm` is green (D-15 DoD — the bilingual LinkedIn harness tests land in 06-05/06-06).
- Deferred-idea fence held: the resume flow's QA is untouched (LinkedIn pipeline only).

## Self-Check: PASSED

- Created files verified on disk: prompts/glossario.md, backend/app/linkedin/qa.py, backend/tests/test_linkedin_qa.py; modified files verified via git diff (5 more, all in the task file lists + the two documented fixes).
- Commits verified in git log: 51154ed, 6a85784.
- `git rev-list --count 8e68a863..HEAD` = 2 (matches the commits ledger; working tree clean of plan-related changes).
