---
phase: 05-review-flow-fact-safety
plan: 03
subsystem: fact-safety-comparison
tags: [fact-safety, comparison-panel, invention-highlights, deterministic-matching, d09, d10, d11, review-flow]
requires:
  - Task 1 comparison.ts exports (fold/suspectTokens/segmentText) consumed by Task 2's panel
  - coverage.py _fold/_term_pattern + test_resume_grounding.py numeral regex (the port sources)
  - 05-02 GeneratedSection action row (the Comparar slot joins it) + mounted PerfilDTO prop in ResumeResult
provides:
  - frontend/src/lib/comparison.ts — pure fold/termPattern/extractNumerals/foldContains/suspectTokens/segmentText (zero deps, zero fetch, no UI-framework imports)
  - frontend/src/components/ComparisonPanel.tsx — two-column D-09 panel with amber D-10 marks, D-11 legend / loud-zero line, company fold-match fallback
  - backend/tests/test_comparison_vectors.py — the canonical TS/Python shared vector table (each vector annotated with its expected TS-side result)
  - "Comparar com o perfil" / "Ocultar comparação" read-only toggle per generated section (aria-expanded)
affects:
  - 05-04 (UAT: amber marks + legend visible; editing away a suspect clears its mark; zero-suspects line on a grounded section)
tech-stack:
  added: [] # zero new dependencies — the port transcribes in-repo Python (RESEARCH §Package Legitimacy Audit)
  patterns:
    - mechanical port discipline — regex transcribed structurally from coverage.py/grounding prior art, never redesigned; lookarounds everywhere, never word-boundary anchors
    - detection as DATA — segmentText returns ordered {text, suspect} spans rendered as JSX children (no HTML string assembly, T-05-09)
    - per-section source-fact scopes — resumo: whole profile facts; experiências: strict per-entry (fold-matched company, all-entries fallback); habilidades: full skill inventory + project tech
    - read-only disclosure — comparison toggle is never disabled (usable during long ops / open editor, UI-SPEC locking matrix)
key-files:
  created:
    - frontend/src/lib/comparison.ts
    - frontend/src/components/ComparisonPanel.tsx
    - backend/tests/test_comparison_vectors.py
  modified:
    - frontend/src/components/ResumeResult.tsx
    - frontend/src/constants/ui.ts
decisions:
  - "resumo detection blob = the WHOLE profile facts (summary + experiences + skills + projects + certifications) while the LEFT COLUMN shows only the profile summary — a summary legitimately synthesizes the entire profile (RESEARCH Pattern 3 scope); the display contract stays exactly as pinned"
  - "entity/tech candidates are checked against the plan-pinned inventory (skill items, project technologies, certification names, companies, institutions, job titles); numerals are checked against the section's source-facts blob via folded SUBSTRING containment (assert_invention_free semantics)"
  - "candidate tokenizer keeps tech-shape punctuation (+ # . / -) but a plain hyphen is NOT a tech-shape marker and a leading dot survives only for the .NET all-caps shape — prose like 'e-mail' or ellipses must not fabricate suspects"
  - "comparison disclosure state is LOCAL to GeneratedSection (useState) — read-only session state with no cross-component coordination, keeping the plan's files_modified list exact (no CurriculoHome change)"
  - "D-11 legend/zero strings, toggle labels, sr-only suffix and the fallback note live in constants/ui.ts; pinned panel/grid/header/mark class strings are component-local with the UI-SPEC comment (SelfCheckPanel precedent — single consumer)"
metrics:
  duration: 11 min
  completed: 2026-09-29
status: complete
actuals:
  tokens: 9690 # chars/4 over the realized diff (38760 diff chars, 770+/12- lines)
  tasks: 2
  commits: 2 # MEASURED: git rev-list --count e0ba133..HEAD
plan_head_before: e0ba1332569153fa98e2bbde1341e38834ac8924
---

# Phase 5 Plan 03: Fact-vs-Generated Comparison + Deterministic Invention Highlights Summary

**One-liner:** Every generated section expands into a read-only two-column "Fatos do perfil | Texto no currículo" panel that recomputes client-side against the currently displayed text (post-edit, zero fetch) and wraps deterministic suspect tokens — numerals absent from the source facts plus named-entity/tech-shape tokens absent from the profile inventory — in amber `<mark>`s framed loudly as mechanical suspicion (D-11 legend, never a verdict), with the fold/numeral mechanics mechanically ported from the verified Python and pinned by a Python mirror vector test.

## What Was Built

- **`frontend/src/lib/comparison.ts`** (new, pure module) — the mechanical port, header-comment cross-referenced to `backend/app/resume/coverage.py:33-41` and `backend/tests/test_resume_grounding.py:146-157` with the never-word-boundary warning (Pitfall 1): `fold()` (toLowerCase + NFKD + strip combining marks — the documented JS casefold approximation), `termPattern()` (`(?<!\w)folded(?!\w)` lookarounds over the FOLDED term with `escapeRegExp`), `extractNumerals()` (SAME alternation order as the prior art: `AAAA-MM` date first, percentage with attached sign, plain/grouped/decimal numbers; lookarounds both sides so `utf8`/`v2` never leak), `foldContains()` (folded SUBSTRING containment — generated "2022" is grounded inside facts "2022-03"), `suspectTokens(sectionText, factsBlob, factInventory)` (numerals not fold-contained in the blob + capitalized-not-sentence-initial and tech-shape candidates not lookaround-matched in the profile-derived inventory), and `segmentText()` (ordered `{text, suspect}` spans covering the text exactly once, overlapping matches merged). No React import, no fetch, no I/O — grep-pinned.
- **`backend/tests/test_comparison_vectors.py`** (new) — the Python mirror: imports `_fold`/`_term_pattern` from `app.resume.coverage`, re-declares the numeral regex exactly as the grounding prior art, and pins the canonical vectors — `fold('Résumé')=='resume'`, `fold('Currículo')=='curriculo'`, accent/case-insensitive term matching, tech shapes (`C++`, `.NET`, `CI/CD` matched; `xC++`, `ASP.NET`, `CI/CDv2`, `v25` tails rejected), the mixed numeral set `{'40%','2022-03','1.234','7,5'}`, the identifier guard, and folded-containment both ways — every vector commented with its expected TS-side result so the UAT verifies the port against the same table (no JS test runner, held house contract).
- **`frontend/src/components/ComparisonPanel.tsx`** (new) — the D-09/D-10/D-11 panel: `mt-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3` shell, `grid grid-cols-1 gap-4 sm:grid-cols-2` (stacks under sm — never horizontal scroll). Left column per the scope contract: resumo → profile summary via `tLang`; experiências → the profile entry fold-matched by company (comparison.ts `fold` both sides) rendering description + impacts like the card's ImpactBullets, with the Pitfall 8 fallback — ALL profile entries under the neutral note when no entry fold-matches, never an empty panel; habilidades → skill items grouped under category sublabels as plain `text-sm` text (never chips — chips carry covered/absent verdicts). Right column: `segmentText` over the CURRENTLY displayed text with suspects from that section's source-facts blob + inventory; suspect spans render as `<mark className="rounded-sm bg-amber-100 text-amber-900 underline decoration-dotted decoration-amber-600 underline-offset-2">` + `<span className="sr-only"> (não consta no perfil)</span>` — ONLY inside this panel, never in the card body (SC2 export fidelity). Closes with the mandatory D-11 legend when ≥1 mark, the loud-zero line at zero. All strings from constants/ui.ts; all rendering JSX children — `grep -RIn "dangerouslySetInnerHTML" frontend/src` → zero matches.
- **`frontend/src/components/ResumeResult.tsx`** (modified) — each GeneratedSection gains the quiet `Comparar com o perfil` toggle (`aria-expanded`, swaps to `Ocultar comparação`, positioned in the action row per the UI-SPEC anatomy) and mounts the panel under the section content when open. The toggle is read-only per the locking matrix — never disabled, usable while a regen/export runs or an editor is open; the 05-02 strip placements and version behavior are untouched. Zero fetch: the panel computes from the `perfil` prop + `resultado.secoes` already mounted.
- **`frontend/src/constants/ui.ts`** (modified) — comparison copy: toggles, panel label (accessible name), column headers, sr-only suffix, D-11 legend, loud-zero line, fallback note.

## Verification

- `cd backend && uv run pytest tests/test_comparison_vectors.py tests/test_coverage.py -q` → **28 passed** (mirror vectors + existing primitives green)
- `cd frontend && npm run build` → **green** after each task (tsc -b + vite)
- `cd backend && uv run pytest -q` → **266 passed, 7 deselected** (full offline suite, zero regressions)
- Acceptance greps: no `\b` anchor anywhere in comparison.ts; no react import / fetch in comparison.ts; no `dangerouslySetInnerHTML` in frontend/src; legend + zero line imported from constants/ui.ts; no chip classes in the panel
- `npm run lint` → 4 pre-existing warnings in untouched files (KeywordsPanel/SelfCheckPanel/SectionEditor fast-refresh notices) — out of scope, unchanged
- Manual UAT (amber marks visible, edit-clears-mark, zero-suspects line, mixed marks) is **05-04's assigned scope** per this plan's verification section

## Deviations from Plan

None — plan executed exactly as written. (The resumo detection-blob scope follows RESEARCH Pattern 3's recorded recommendation — whole-profile facts for detection, summary-only for display — documented as a decision above, not a plan change.)

## Auth Gates

None.

## Known Stubs

None — every exported function is fully implemented and consumed; no placeholder text, no unwired data paths.

## Self-Check: PASSED

All 6 key files exist on disk; both task commits verified in git log (`693de6e` port + mirror vectors, `8fe2a9a` panel + wiring + copy).
