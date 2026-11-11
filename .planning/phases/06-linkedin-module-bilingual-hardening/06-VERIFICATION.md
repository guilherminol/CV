---
phase: 06-linkedin-module-bilingual-hardening
verified: 2026-09-30T14:17:13Z
status: human_needed
score: 28/55 must-haves verified
covered_files:
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-01-PLAN.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-01-SUMMARY.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-02-PLAN.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-02-SUMMARY.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-03-PLAN.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-03-SUMMARY.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-04-PLAN.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-04-SUMMARY.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-05-PLAN.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-05-SUMMARY.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-06-PLAN.md
  - .planning/phases/06-linkedin-module-bilingual-hardening/06-06-SUMMARY.md
  - backend/app/config.py
  - backend/app/linkedin/__init__.py
  - backend/app/linkedin/models.py
  - backend/app/linkedin/pipeline.py
  - backend/app/linkedin/qa.py
  - backend/app/llm/gateway.py
  - backend/app/llm/schemas.py
  - backend/app/main.py
  - backend/app/resume/facts.py
  - backend/app/routes/linkedin.py
  - backend/tests/test_linkedin_api.py
  - backend/tests/test_linkedin_pipeline.py
  - backend/tests/test_linkedin_qa.py
  - backend/tests/test_linkedin_regen_pipeline.py
  - backend/tests/test_linkedin_schema.py
  - backend/tests/test_llm_harness.py
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/components/CharacterCounter.tsx
  - frontend/src/components/CopiarButton.tsx
  - frontend/src/components/LinkedinComparisonPanel.tsx
  - frontend/src/components/LinkedinQaPanel.tsx
  - frontend/src/components/LinkedinSectionEditor.tsx
  - frontend/src/constants/ui.ts
  - frontend/src/pages/LinkedInHome.tsx
  - prompts/glossario.md
  - prompts/linkedin-experiencias.md
  - prompts/linkedin-headline.md
  - prompts/linkedin-skills.md
  - prompts/linkedin-sobre.md
covered_digest: "v1:sha256:782c2aead7d8332b543a0bb3d87df85b1d1bd9114511abfe25daeb6ca64a1ffd"
behavior_unverified: 27 # present + wired truths whose interactive/browser or real-API behavior no test in this repo exercises (no JS test runner by design); each maps into the 6 human verification areas below
overrides_applied: 0
re_verification: null
behavior_unverified_items:
  - truth: "06-01 #5/#6/#7 — empty-state render at first paint; in-flight CTA swap + aria-live hint; a failed gerar keeps prior result mounted with the red erros[] panel"
    test: "Open the LinkedIn page fresh; run a gerar; force a failure (stop backend / invalid state) with a result mounted"
    expected: "Empty-state heading+body with the form present; CTA label swaps with the in-flight hint during flight; on failure the red panel renders backend lines verbatim and the prior result stays mounted"
    why_human: "Runtime UI states in a browser — the project has no JS test runner by design; the backend erro envelope is test-verified but the panel mount is not"
  - truth: "06-03 #1 — a skills-less profile shows the lint aviso and the skills block renders the loud count line, never a silent empty block"
    test: "Load a profile with no skills, generate"
    expected: "Lint aviso (non-blocking) + `0 skills em ordem de prioridade.` loud line in the skills block"
    why_human: "Rendered state under a specific profile fixture; backend half (skills-less run completes) is test-pinned"
  - truth: "06-03 #4 — experiência sub-blocks render one per profile experience in profile order with per-entry counter/Copiar/badge; zero experiences renders the loud muted line"
    test: "Generate and inspect the experiência group; repeat against a zero-experience profile"
    expected: "One sub-block per profile experience with WR-03-verified anchors; `Nenhuma experiência no perfil` line on a zero-experience profile"
    why_human: "Browser rendering of a group keyed to profile data; anchor logic itself is code-verified (fold-match guard at LinkedInHome.tsx:1222-1225)"
  - truth: "06-03 #5/#7 — per-block counter independence; over-limit draft shows red flag + disabled Salvar with the reduce-first hint; nothing ever truncated"
    test: "Force a draft past a limit in the editor; watch counters turn amber (>=90%) then red"
    expected: "Red counter + flag naming the excess; Salvar alterações disabled with the hint; the underlying text never truncated"
    why_human: "Interactive editing states; the server-side never-truncated contract is test-pinned (oversize guards), the UI behavior is not"
  - truth: "06-03 #6 — Copiar puts exactly the displayed text on the clipboard (per-entry: descricao only), shows Copiado! ~2 s, and the failure line on rejection"
    test: "Click Copiar on Headline, Sobre, each Experiência entry, Habilidades; paste into a text editor"
    expected: "Pasted text equals displayed text; per-entry paste = that entry's descricao only; Copiado! feedback on each click"
    why_human: "OS clipboard interaction — navigator.clipboard is wired (CopiarButton.tsx) but only a human paste can prove content equality"
  - truth: "06-03 #8/#9 — versions stack per block/per entry with restore; one editor at a time; the full locking matrix during flights"
    test: "Edit/restore across blocks; open an editor and trigger a regen; inspect every control's disabled state during flight"
    expected: "Stack-before-mutate on every destructive path; Comparar/Versões toggles and Copiar stay usable while CTA/regen/edit controls lock"
    why_human: "Multi-control interaction matrix observable only in a running browser"
  - truth: "06-03 #10 — a failed section regen renders the red panel inside the owning block with prior text intact"
    test: "Force a regen failure (backend error) with a result mounted"
    expected: "Red panel scoped inside the owning block; prior block text stays mounted (failure never blanks)"
    why_human: "Failure-state rendering is browser runtime; the regen erro envelope is test-verified"
  - truth: "06-03 #11 — comparison renders two columns with deterministic amber marks, adapted legend, zero-suspects line, and the fallback note"
    test: "Open Comparar com o perfil on each block type; include a fallback-mode experiência"
    expected: "Profile facts left / Texto no LinkedIn right; amber suspicion marks; all-entries fallback note when pairing fell back"
    why_human: "Visual rendering of fold-matched facts; the WR-04 consumption fix (used-Set findIndex) is code-verified but its rendered output is not"
  - truth: "06-03 #12/#13 — long text never clips (paragraphs wrap, page grows); all state is session-only (refresh returns to the empty form)"
    test: "Generate a long result and resize/scroll; then refresh the page"
    expected: "No clipping; refresh resets to the empty form (ephemeral D-11)"
    why_human: "Visual layout and session-lifecycle behavior"
  - truth: "06-03 backstop — full page at max volume stays readable (2.600-char Sobre, several 2.000-char experiências, all disclosures open, QA panel mounted)"
    test: "Generate max-volume content, open every disclosure"
    expected: "Blocks clearly separated, no cramping"
    why_human: "Readability is an inherently visual judgment (verification: backstop — abstains on presence alone)"
  - truth: "06-04 #8 / 06-05 #2/#3 — zero substitutions and zero bleed findings render loud zero lines; mixed findings render per-item rows"
    test: "Generate a clean PT-BR result; then one with glossary/bleed findings"
    expected: "Loud zero lines when clean; one row per substitution ({de} → {para}) and one amber row per bleed finding ({termo} — {seção})"
    why_human: "Rendered states; the backend loud-empty payload is test-pinned, the browser rendering is not"
  - truth: "06-05 #1 — the QA panel holds the LATEST generation response's payload; edits and restores keep the last computed report"
    test: "Generate, then edit/restore a block; observe the QA panel"
    expected: "Panel content unchanged by edits/restores (swapped only by the two generation-success onSuccess handlers)"
    why_human: "State-persistence invariant under interaction; the two-swap-point structure is code-verified (LinkedInHome.tsx:424, 523) but persistence is browser-observable only"
  - truth: "06-05 #5 — EN runs render the neutral QA note (never a silently absent panel)"
    test: "Switch idioma to English and generate"
    expected: "Neutral note replaces the two QA blocks; legend still renders"
    why_human: "Language-switched browser render; the qa:null backend contract is test-pinned"
  - truth: "06-05 #6/#7 — the bilingual real-API fixture suite is green (both linkedin-PT and linkedin-EN PASSED on OpenRouter) as the SC4 DoD"
    test: "With OpenRouter credits topped up: cd backend && uv run pytest tests/test_llm_harness.py -m llm -q (full file)"
    expected: "Both LinkedIn parametrizations pass with every live assertion (limit-or-flag, qa contract, four-stage runs.jsonl audit, UTF-8 probe)"
    why_human: "Costs real API spend; the dedicated -k linkedin run passed both labels (recorded in 06-05-SUMMARY) but the full-file run is blocked by account-level 402 — an operator item (WINDOWS.md entry 10), not re-runnable here without spend"
  - truth: "06-06 #1 — copy-paste UX proven end-to-end (LI-05)"
    test: "06-VALIDATION Manual-Only check 1 (copy every block/entry, paste, compare)"
    expected: "Pasted text equals displayed text everywhere; Copiado! feedback each time"
    why_human: "The 06-06 checkpoint resolved deferred-with-UAT per the run convention — clipboard equality is human-only"
  - truth: "06-06 #2 — counter behavior proven by a human (live updates, amber/red, over-limit save guard, regen as the correction path)"
    test: "06-VALIDATION Manual-Only check 2"
    expected: "Counters live-update; red flag names the excess; Salvar disabled with the reduce-first hint; section regen recovers"
    why_human: "Deferred UAT — interactive editing states"
  - truth: "06-06 #3 — QA panel framing proven by a human (findings without blocking, zero lines, legend, EN note)"
    test: "06-VALIDATION Manual-Only check 3"
    expected: "Verificação de idioma lists findings without gating Copiar; zero lines loud; legend visible; EN note on EN runs"
    why_human: "Deferred UAT — visual/interaction framing"
  - truth: "06-06 #4 — max-volume readability backstop"
    test: "06-06 checkpoint check 4 (long Sobre + several experiências + all disclosures open)"
    expected: "Page stays readable, blocks separated, no cramping"
    why_human: "Deferred UAT — visual judgment"
  - truth: "06-06 #5 — the end-to-end flow works as one story (objetivo + idioma → avisos → gerar → four blocks → copy into LinkedIn)"
    test: "Walk the full page flow on dev servers"
    expected: "LI-01..LI-05 experienced in sequence without dead ends"
    why_human: "Deferred UAT — whole-page interaction narrative"
human_verification:
  - test: "Copy-paste UX — generate in PT-BR; click Copiar on Headline, Sobre, each Experiência entry, and Habilidades; paste into a text editor"
    expected: "Pasted text equals the displayed text (per-entry paste = that entry's descricao only); each click showed Copiado!"
    why_human: "OS clipboard content equality cannot be proven by grep, build, or backend tests"
  - test: "Counters + over-limit path — watch counters update while editing (amber >= 90%, red over); force a draft past a limit"
    expected: "Red flag names the excess; Salvar alterações disables with the reduce-first hint; regen the section to recover; nothing ever truncated"
    why_human: "Live interactive editing states; only the server-side never-truncated contract is test-pinned"
  - test: "QA panel framing — on a PT-BR result inspect Verificação de idioma (substitutions, bleed avisos, zero lines, legend); repeat on an EN run"
    expected: "Findings listed WITHOUT blocking Copiar; loud zero lines when clean; legend always visible; neutral note on EN"
    why_human: "Visual panel states across both language branches"
  - test: "Page-flow smoke — fresh page, generate, edit/save/restore, regen a block, force a failure, refresh"
    expected: "Empty state renders; in-flight swaps work; failure never blanks prior content; locking matrix holds; refresh returns to the empty form"
    why_human: "Whole-page interaction narrative across runtime states"
  - test: "Max-volume backstop — long Sobre (~2.600 chars), several experiências, all disclosures open, QA panel mounted"
    expected: "Page stays readable: blocks clearly separated, no cramping"
    why_human: "Readability is an inherently visual judgment"
  - test: "OpenRouter operator item — top up credits at https://openrouter.ai/settings/credits, then re-run `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q` (full file) and confirm exit 0"
    expected: "Full-file DoD run passes including both linkedin-PT and linkedin-EN labels, no skips (WINDOWS.md entry 10 closed)"
    why_human: "Costs real API spend; the account hit 402 Payment Required mid-run — an environmental/operator blocker honestly recorded, not a code gap; the dedicated -k linkedin run already passed both labels green (64.10s) before the wall"
---

# Phase 6: LinkedIn Module + Bilingual Hardening — Verification Report

**Phase Goal:** State a career objective once and get complete, length-compliant LinkedIn sections in PT-BR or EN — copy-paste ready — by reusing the resume engine wholesale (prompts and block types only).
**Verified:** 2026-09-30T14:17:13Z
**Status:** human_needed
**Re-verification:** No — initial verification

**MVP mode note:** the phase carries `mode: mvp` but its goal is not in `As a…, I want to…, so that….` format (`user-story.validate` → false). Per this project's own convention (phases 1–5, all `mode: mvp` with imperative goals, all fully verified), verification proceeded goal-backward against the ROADMAP success criteria rather than refusing.

## Goal Achievement

### Roadmap Success Criteria (the contract)

| #  | Success Criterion                                                                                                                              | Status                          | Evidence                                                                                                                                                                                                 |
| -- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | User states an objective, chooses the language, and all LinkedIn outputs are generated from it                                                  | ✓ VERIFIED (structure)          | `LinkedinGerarRequest` (objetivo 80..2000 + language Literal) → `run_linkedin_pipeline` composes FATOS DO PERFIL + OBJETIVO as user-message DATA → 4 sequential stages; 422/loud-empty/stage-order tests green |
| 2  | Headline ≤220, About ≤2600, per-experience ≤2000, prioritized skills — each with a visible counter; nothing silently truncated                   | ✓ VERIFIED (server half)        | `_build_limites` code-unit counts; oversize-guard tests (500/3000/2500/150-item) pass; CharacterCounter amber/red classes; over-limit flagged (`excesso>0`), never cut; visible counter is browser state → UAT area 2 |
| 3  | All outputs are copy-paste text blocks                                                                                                          | ✓ VERIFIED (wiring)             | `CopiarButton` → `navigator.clipboard.writeText(displayedText)` mounted on every block/entry; build green; clipboard equality is human-only → UAT area 1                                                  |
| 4  | PT-BR outputs pass the language QA gate (glossary applied, no EN bleed), and the both-language fixture suite is the DoD for every prompt change   | ✓ VERIFIED (mechanism)          | `app/linkedin/qa.py` deterministic glossary + curated `EN_BLEED_TERMS`, glossary-before-bleed, pt-BR dict / en null — 48+ vectors green; bilingual harness tests exist, marker-gated, dedicated run passed both labels; full-file re-run pending credits → human item 6 |

### Observable Truths (merged PLAN must_haves; roadmap SCs dedupe into the clusters above)

**06-01 — Tracer (LI-01, LI-02)**

| #  | Truth                                                                              | Status                          | Evidence                                                                                                                                                             |
| -- | ---------------------------------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | Sub-80 objetivo: CTA gated client-side + 422 server-side; never runs on empty       | ✓ VERIFIED                      | Field(min 80/max 2000) + 422 tests; client mirror LINKEDIN_OBJETIVO_MIN_CHARS=80 gates CTA (`objetivoCurto`)                                                           |
| 2  | Empty headline fails loud; never rendered                                          | ✓ VERIFIED                      | `_require_non_empty` → LLMError; scripted blank-headline tests green                                                                                                   |
| 3  | Code-unit counts agree client/server                                               | ✓ VERIFIED                      | `_limite_entry` uses Python `len`; CharacterCounter uses JS `.length` on the same string; limites tests green                                                          |
| 4  | Runs independent; wholesale swap; identical objectives never merge                  | ✓ VERIFIED                      | fresh `load_profile()` per run; `setResultado(data)` single-call swap (LinkedInHome.tsx:424); no cache anywhere                                                           |
| 5  | Empty-state heading+body renders with form present                                  | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Branch exists in code + build green; first-paint render is browser state — UAT area 4                                                                                  |
| 6  | In-flight CTA swap + aria-live hint                                                 | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Mutation pending states wired; observable only in flight — UAT area 4                                                                                                  |
| 7  | Failed gerar keeps prior result + verbatim erros[] red panel; fetch failure generic hint | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Server erro envelope (no secoes key, raw terminal-only) test-pinned; panel mount is browser — UAT area 4                                                                   |
| 8  | Erro envelope PT-BR only; raw detail terminal-only                                  | ✓ VERIFIED                      | caplog assertions in test_linkedin_api.py (suite green)                                                                                                                 |
| 9  | runs.jsonl logs stages, zero new fields (D-10)                                      | ✓ VERIFIED                      | Stage strings via existing mechanism; D-10 content-key guard in harness; offline audit tests green                                                                       |
| 10 | >220 headline never truncated — flagged (`excesso > 0`)                             | ✓ VERIFIED                      | Oversize guards validate cleanly at LLM layer; pipeline keeps full text + excesso; test-pinned                                                                          |

**06-02 — Full generation backend (LI-03, LI-04, LI-05)**

| #  | Truth                                                                              | Status     | Evidence                                                                                                          |
| -- | ---------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| 1  | Empty sobre fails loud                                                             | ✓ VERIFIED | Scripted blank-sobre → LLMError test green                                                                           |
| 2  | Zero-entry experiências / blank descricao fails loud (profile-aware, WR-05)         | ✓ VERIFIED | Named test `test_zero_entry_experiencias_ok_on_experience_less_profile` PASSED (re-run here); blank-descricao vector green; guard `if not returned and profile_experiences:` (pipeline.py:186) |
| 3  | Sobre/experiência counts are the same code-unit contract                            | ✓ VERIFIED | `_build_limites` over all three surfaces; tests green                                                                |
| 4  | Positional mapping profile-order; same-company never merge (first-unused-match)     | ✓ VERIFIED | `_align_experiencias` fold-match + used-set; same-company + partial-match vectors green                              |
| 5  | Display order = profile order                                                       | ✓ VERIFIED | Alignment returns profile-ordered matched entries; test-pinned                                                        |
| 6  | Duplicate skills dedupe deterministically (fold, first occurrence wins)             | ✓ VERIFIED | `_dedupe_habilidades` + unsorted-vector test green                                                                   |
| 7  | Skills list keeps LLM order — no re-sort anywhere                                   | ✓ VERIFIED | No sort call (grep); order-preservation test with deliberately unsorted list green                                   |
| 8  | One gerar = all four stages in D-09 order; bad About never re-rolls headline        | ✓ VERIFIED | Stage-order assertion (client.calls sequence) green; same composed input per stage                                    |
| 9  | Lint = verbatim `run_lint_only` reuse, non-blocking                                 | ✓ VERIFIED | routes/linkedin.py imports + calls `run_lint_only` verbatim; api tests green                                          |
| 10 | Regen = exactly ONE stage, merge over SUBMITTED state, siblings byte-identical      | ✓ VERIFIED | One-stage-per-secao assertions (client.calls); WR-01 named test `test_regen_glossario_never_mutates_siblings_byte_identity_through_qa` PASSED (re-run here) with `is` identity assertions through a live glossário pair |
| 11 | Dica joins user message as DATA only (messages[1]); system + log untouched          | ✓ VERIFIED | `append_dica_block` shared framing; dica-travels-as-data test green                                                   |

**06-03 — Frontend product surface (LI-02..LI-05)**

| #  | Truth                                                                              | Status                          | Evidence                                                                                                                     |
| -- | ---------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1  | Skills-less profile: lint aviso + loud count line, never silent empty               | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Backend half test-pinned (skills-less run ok); rendered aviso/count line is browser — UAT area 3/4                                |
| 2  | Skills count line counts entries, no fake `/Y`                                      | ✓ VERIFIED                      | Pure singular/plural constants (`LINKEDIN_SKILLS_CONTAGEM_*`, no `/Y`); wired in the count slot                                     |
| 3  | Blocks render in fixed order regardless of completion order                         | ✓ VERIFIED                      | Static `BLOCOS_FIXOS` array (LinkedInHome.tsx:114) — no completion-order dependency                                                  |
| 4  | Experiência sub-blocks per profile entry in profile order with per-entry controls   | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Group rendering + WR-03 anchor guard code-verified; browser rendering — UAT area 4                                                  |
| 5  | Counters are per block/entry, never a page-level verdict                            | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Per-block CharacterCounter wiring verified; live independence is browser — UAT area 2                                               |
| 6  | Copiar copies exactly the displayed text; Copiado!; failure path                    | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | `navigator.clipboard.writeText` + 2 s timer + aria-live wired (CopiarButton.tsx); clipboard equality is human — UAT area 1           |
| 7  | Over-limit display: red counter + flag; editor maxLength; disabled save + hint; no truncation | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Save-guard + maxLength mirror code-verified; interactive state — UAT area 2                                                    |
| 8  | Versões stack per block/entry; count 0 = disabled toggle                            | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Stack-before-mutate order provable in code; interaction — UAT area 4                                                                |
| 9  | One editor at a time; locking matrix during flights                                 | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | `operacaoLongaPendente`/`locksEdicao` derived-once, wired to the right control sets; interaction — UAT area 4                        |
| 10 | Failed regen renders red panel inside owning block; prior text intact               | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Failure-never-blanks structure verified; runtime failure rendering — UAT area 4                                                      |
| 11 | Comparison: two columns, amber marks, legend, zero-suspects line, fallback note     | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | WR-04 consumption fix verified in code (used-Set findIndex, LinkedinComparisonPanel.tsx:226-229); rendered output — UAT area 4        |
| 12 | Long text never clips; wraps and grows                                              | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | No overflow-clipped containers per conventions; visual — UAT area 4/5                                                                |
| 13 | Session-only state; refresh returns to empty form                                   | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | No persistence path exists (grep); refresh behavior — UAT area 4                                                                     |
| B  | Backstop: max-volume readability                                                    | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | `verification: backstop` — abstains absent observed behavior; UAT area 5                                                             |

**06-04 — Deterministic QA core (SC4)**

| #  | Truth                                                                              | Status                          | Evidence                                                                                                |
| -- | ---------------------------------------------------------------------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 1  | Glossário git-versioned, strict-validated, fresh-read; malformed pair fails fast PT-BR | ✓ VERIFIED                    | `prompts/glossario.md` (3 seed pairs); `GlossarioSpec` extra=forbid; loader ladder + fresh-read seam tests green |
| 2  | Deterministic case-preserving substitution on ORIGINAL text, each reported          | ✓ VERIFIED                      | re.escape + lookarounds + re.IGNORECASE (qa.py:128); case-shape vectors, accent-intactness, occurrence counts green |
| 3  | Glossary BEFORE bleed; report describes the copied text                             | ✓ VERIFIED                      | `run_linkedin_qa` order contract; substitution mutates secoes then bleed over post-glossary text; test-pinned |
| 4  | Mechanical bleed detection, no LLM judge                                            | ✓ VERIFIED                      | Static `EN_BLEED_TERMS` in code; signature-pin test proves no client in the QA path; fold primitives imported, not re-implemented |
| 5  | QA non-blocking; Copiar never gated; hard failures only for schema/network          | ✓ VERIFIED                      | Findings are payload rows, nothing raises; no QA condition touches Copiar in the frontend (code)             |
| 6  | PT-BR only; EN carries qa: null                                                     | ✓ VERIFIED                      | Language gate short-circuits before file read; EN null vectors in pipeline + regen + api tests green         |
| 7  | Every generation success recomputes QA over the full merged PT-BR state             | ✓ VERIFIED                      | `test_regen_qa_recomputed_over_the_full_merged_state` green; both pipeline functions call run_linkedin_qa    |
| 8  | Zero substitutions/bleed render loud zero lines                                     | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Backend loud-empty lists test-pinned; browser zero-line rendering — UAT area 3                               |

**06-05 — QA panel + DoD harness**

| #  | Truth                                                                              | Status                          | Evidence                                                                                                     |
| -- | ---------------------------------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 1  | QA panel holds latest generation response; swapped only by the two onSuccess paths; never recomputed client-side | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Two swap points verified in code (LinkedInHome.tsx:424 wholesale, :523 `qa: data.qa`); edits go through comSecoes; no matching logic in frontend; persistence under edits is browser — UAT area 3 |
| 2  | Zero findings render loud zero lines                                                | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | QA_GLOSSARIO_ZERO/QA_BLEED_ZERO branches in LinkedinQaPanel; browser — UAT area 3                                |
| 3  | Mixed findings render per-item rows ({de} → {para} / {termo} — {seção})              | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Row rendering maps payload verbatim; browser — UAT area 3                                                        |
| 4  | Legend always renders; panel never gates Copiar                                     | ✓ VERIFIED                      | Legend outside the null branch (LinkedinQaPanel.tsx:76, renders in both); no gating of Copiar anywhere            |
| 5  | EN runs render the neutral note, never silently absent                              | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | `qa === null` branch verified in code; EN-branch render — UAT area 3                                              |
| 6  | Bilingual real-API fixture suite is the DoD for prompt changes                      | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Mechanism VERIFIED: `test_real_run_linkedin_pipeline_bilingual` exists (enumerated, both labels), marker-gated; the green full-file run is credit-blocked — human item 6 |
| 7  | Real-API runs assert ok / limit-or-flag / qa keys / four-stage runs.jsonl / UTF-8   | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | All assertions present in test code (read); their passing execution on the live API pending the credits re-run   |

**06-06 — End-of-phase UAT checkpoint**

| #  | Truth                                                                              | Status                          | Evidence                                   |
| -- | ---------------------------------------------------------------------------------- | ------------------------------- | -------------------------------------------- |
| 1  | Copy-paste UX proven by a human                                                     | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Deferred-with-record per run convention — UAT area 1 |
| 2  | Counter behavior proven by a human                                                  | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Deferred — UAT area 2                          |
| 3  | QA panel framing proven by a human                                                  | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Deferred — UAT area 3                          |
| 4  | Max-volume readability                                                              | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Deferred — UAT area 5                          |
| 5  | End-to-end flow works as one story                                                  | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED  | Deferred — UAT area 4                          |

**Score:** 28/55 truths verified (27 present, behavior-unverified — all routed to the 6 human verification areas)

**Constraint hold (explicit check):** stage output models are plain `str` — zero `max_length`/`Field(` occurrences in the LinkedIn output-model block of `backend/app/llm/schemas.py` (grep count: 0); the asymmetric-bounds rule (inputs bounded 80..2000, outputs unbounded + flagged) held through the review fixes.

**Review fixes re-proven (9/9 landed, all commits ancestors of HEAD):** WR-01 sibling byte-identity through the glossário — named regression test re-run PASSED here (`machine learning` vector, `is` identity assertions, zero glossário rows, detection still covers the merged state); WR-05 zero-experience gerar completes — named regression test re-run PASSED here; WR-02 surplus-entries test and WR-03/WR-04/WR-06/IN-01/IN-02/IN-03 fixes verified present in code.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/app/linkedin/pipeline.py` | 4-stage orchestration + regen + limites + QA wiring | ✓ VERIFIED | Substantive (429 lines); all contracts test-pinned |
| `backend/app/linkedin/qa.py` | Glossary loader/apply + bleed + orchestration | ✓ VERIFIED | Substantive; no client in signatures; 48 vectors |
| `backend/app/linkedin/models.py` | LinkedinSecoes submitted-state model | ✓ VERIFIED | Strict, floors on headline/sobre, empty lists legitimate |
| `backend/app/linkedin/__init__.py` | Package exports | ✓ VERIFIED | Wired by routes/tests |
| `backend/app/routes/linkedin.py` | lint/gerar/regenerar routes | ✓ VERIFIED | Strict bodies, sync defs, 200-envelope, raw terminal-only |
| `backend/app/llm/schemas.py` (LinkedIn models) | 4 output models + wire schemas, plain str | ✓ VERIFIED | Drift-locked in test_linkedin_schema.py |
| `backend/app/llm/gateway.py` | 4 stage registrations | ✓ VERIFIED | Lines 69-72, one entry per stage |
| `backend/app/config.py` | LINKEDIN_* constants | ✓ VERIFIED | 220/2600/2000/100 + 80/2000 with confidence notes |
| `backend/app/main.py` | Router before SPA mount | ✓ VERIFIED | include_router precedes StaticFiles mount |
| `prompts/linkedin-{headline,sobre,experiencias,skills}.md` | PT-BR prompts, strict JSON blocks | ✓ VERIFIED | Frontmatter verified (experiencias max_tokens 6000, in band) |
| `prompts/glossario.md` | User-editable pair list | ✓ VERIFIED | 3 real pairs, D-12 discipline body |
| `backend/tests/test_linkedin_{schema,pipeline,api,regen_pipeline,qa}.py` | Offline vector families | ✓ VERIFIED | All green in the 407-test run |
| `backend/tests/test_llm_harness.py` (LinkedIn addition) | Bilingual DoD fixtures | ✓ VERIFIED (mechanism) | Both parametrizations enumerated, marker-gated, assertions live |
| `frontend/src/pages/LinkedInHome.tsx` | Full page surface | ✓ VERIFIED (wiring) | 1600+ lines; all mutations/locks/branches wired; build green |
| `frontend/src/components/{CharacterCounter,CopiarButton,LinkedinSectionEditor,LinkedinComparisonPanel,LinkedinQaPanel}.tsx` | Page components | ✓ VERIFIED | All substantive and imported by the page |
| `frontend/src/api/client.ts` | Typed LinkedIn client | ✓ VERIFIED | gerar/regenerar/lint + full DTO shapes incl. qa union |
| `frontend/src/constants/ui.ts` | LINKEDIN_*/QA_* copy + mirrors | ✓ VERIFIED | NAV item enabled; mirrors match backend constants |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `_STAGE_SCHEMAS` entries | Linkedin* models ↔ LINKEDIN_*_STRICT_SCHEMA | drift-lock test | ✓ WIRED | 4 registrations (gateway.py:69-72); drift-lock suite green |
| POST /api/linkedin/gerar | run_linkedin_pipeline → run_stage | injectable client/runs_log | ✓ WIRED | Offline suite 100% offline proves the seam |
| POST /api/linkedin/lint | run_lint_only (verbatim) | import from app.resume.pipeline | ✓ WIRED | Zero new lint logic |
| POST /api/linkedin/regenerar | run_linkedin_section_regen | SECTION_STAGE_BY_ID (4 ids) | ✓ WIRED | One stage per call, pinned per secao value |
| frontend gerarLinkedin/regenerarSecaoLinkedin/fetchLinkedinLint | backend envelopes | typed DTOs + tsc -b | ✓ WIRED | Build green; qa union type on both response types |
| envelope `qa` payload | LinkedinQaPanel rows | rendered verbatim | ✓ WIRED | No frontend re-mapping (no matching logic imported) |
| pipeline post-gen | apply_glossario → detect_english_bleed → qa | order contract | ✓ WIRED | Glossary-before-bleed pinned by tests |
| prompts/glossario.md | GlossarioSpec | load_glossario fresh-read | ✓ WIRED | prompts_dir seam threaded through both pipelines |
| coverage `_fold`/`_term_pattern` | qa.py matcher | import, never re-implement | ✓ WIRED | qa.py:56 |
| limites payload | CharacterCounter + over-limit flag | per block/entry | ✓ WIRED | Index-aligned experiências limites consumed |
| stack-before-mutate | versoes state → version rows | Phase 5 mechanism | ✓ WIRED | Code order provable; orphaned-stack IN-03 fix landed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| LinkedInHome result card | `resultado` | POST /api/linkedin/gerar → run_linkedin_pipeline → 4 real LLM stages | Yes | ✓ FLOWING |
| LinkedinQaPanel | `resultado.qa` | run_linkedin_qa over post-glossary secoes (server) | Yes | ✓ FLOWING |
| CharacterCounter / flags | `resultado.limites` | `_build_limites` over the returned secoes | Yes | ✓ FLOWING |
| Lint zone | avisos | POST /api/linkedin/lint → run_lint_only (real engine) | Yes | ✓ FLOWING |
| Comparison panel facts | `perfil` | GET profile (Phase 1 loader) | Yes | ✓ FLOWING |

No static fallbacks, hardcoded literals, or mock-fed renders found on any rendered path.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full offline suite | `cd backend && uv run pytest -q` | 407 passed, 9 deselected in 9.47s (re-proven this verification; matches the post-review-fix claim) | ✓ PASS |
| WR-01 sibling byte-identity through glossário | `uv run pytest tests/test_linkedin_regen_pipeline.py::test_regen_glossario_never_mutates_siblings_byte_identity_through_qa` (named) | 2 passed (with WR-05 below) in 1.05s | ✓ PASS |
| WR-05 zero-experience gerar completes | `uv run pytest tests/test_linkedin_pipeline.py::test_zero_entry_experiencias_ok_on_experience_less_profile` (named) | same run, passed | ✓ PASS |
| Frontend build | `cd frontend && npm run build` | tsc -b + vite green, 85 modules | ✓ PASS |
| DoD harness LinkedIn tests exist, marker-gated | `uv run pytest tests/test_llm_harness.py --collect-only -q -m llm` | Both linkedin-PT and linkedin-EN parametrizations collected; 9 llm-marked, marker discipline intact | ✓ PASS (existence) |
| DoD full-file real-API run | `uv run pytest tests/test_llm_harness.py -m llm -q` | NOT RUN — OpenRouter 402 credit exhaustion (account-level; recorded WINDOWS.md entry 10). Re-running would spend credits and fail on balance | ? SKIP → human item 6 |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No probes declared in any 06-xx-PLAN.md and no conventional `scripts/*/tests/probe-*.sh` exist in this repo | SKIP (none declared) |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
| ----------- | -------------- | ----------- | ------ | -------- |
| LI-01 | 06-01, 06-06 | Objective (roles/seniority/technologies) + language drive all LinkedIn generation | ✓ SATISFIED | LinkedinGerarRequest objetivo+language → compose → 4 stages; segmented PT-BR/EN control; 422 bounds pinned |
| LI-02 | 06-01, 06-03, 06-04, 06-05, 06-06 | Headline ≤220 keyword-optimized | ✓ SATISFIED | linkedin-headline stage; limites.headline flag-or-comply; oversize never truncated |
| LI-03 | 06-02, 06-03, 06-04, 06-05, 06-06 | About ≤2600 rewritten for the objective | ✓ SATISFIED | linkedin-sobre stage (max_tokens 3000); limites.sobre; loud-empty |
| LI-04 | 06-02, 06-03, 06-04, 06-05, 06-06 | Per-experience descriptions ≤2000, action verbs, objective-relevant | ✓ SATISFIED | linkedin-experiencias stage (max_tokens 6000); profile-order alignment + WR-02/WR-03/WR-04 fixes; per-entry limites |
| LI-05 | 06-02, 06-03, 06-04, 06-05, 06-06 | Prioritized skills list + copy-paste-ready outputs within limits | ✓ SATISFIED | Order-is-priority (no sort) + dedupe pinned; CopiarButton on every block/entry (clipboard UX in UAT area 1) |

**Orphaned requirements:** none — REQUIREMENTS.md maps exactly LI-01..LI-05 to Phase 6 and every ID appears in at least one plan's `requirements` field.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| test_linkedin_schema.py | LI-02..05 | yes | 0 (marker-deselected only) | no | value (drift-lock dicts + oversize guards) | PROVES |
| test_linkedin_pipeline.py | LI-03/04/05 | yes | 0 | no | behavioral (stage order, alignment, dedupe, loud-empty) | PROVES |
| test_linkedin_regen_pipeline.py | LI-02..05 (D-04) | yes | 0 | no | behavioral (one-stage, `is` byte-identity, dica DATA) | PROVES |
| test_linkedin_qa.py | SC4 | yes | 0 | no | value (case shapes, boundaries, accents, ladder, fresh-read) | PROVES |
| test_linkedin_api.py | LI-01..05 | yes | 0 | no | status + value (envelopes, 422, caplog terminal-only) | PROVES |
| test_llm_harness.py (LinkedIn) | SC4 DoD | marker-gated (deselected offline by design) | 0 skips when run | no (asserts against config constants, not self-generated values) | behavioral (live limit-or-flag, qa contract, stage audit) | PROVES (when run with credits) |

**Disabled tests on requirements:** 0 (the 9 offline-deselected tests are `llm`-marker DoD tests — the project's designed spend gate, not hidden skips).
**Circular patterns detected:** 0. **Insufficient assertions:** 0.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No TBD/FIXME/XXX/HACK/PLACEHOLDER markers, no empty implementations, no console-log-only paths, no hardcoded-empty props on any phase file | none | Clean (the `placeholder=` matches are textarea placeholder attributes) |

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts: 15/15 honored, 0 not honored (D-01..D-15, including the wholesale engine reuse measure, D-07 no-truncation, D-12..D-14 QA discipline, D-15 DoD).

### Human Verification Required

Six areas (five deferred UAT areas from 06-06 + one operator item). Full procedures in the frontmatter `human_verification` list and 06-VALIDATION.md:

1. **Copy-paste UX** — clipboard equality per block/entry + Copiado! feedback.
2. **Counters + over-limit path** — live amber/red, red flag + disabled save with hint, regen recovers, nothing truncated.
3. **QA panel framing** — findings without blocking, loud zero lines, legend, EN neutral note.
4. **Page-flow smoke** — empty state, in-flight, failure-never-blanks, locking matrix, refresh reset, whole-story flow.
5. **Max-volume backstop** — readability at full volume.
6. **OpenRouter credits re-run (operator)** — top up at https://openrouter.ai/settings/credits, then `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q` must exit 0 (closes WINDOWS.md entry 10).

### Gaps Summary

No gaps. Every code-level must-have is present, substantive, and wired; the full offline suite (407 tests), the frontend build, and the WR-01/WR-05 named regression tests were re-proven in this verification. The two open items are both human-side, not code-side: the five deferred UAT areas (the project has no JS test runner by design, so interactive/visual truths cannot be automated) and the credit-blocked full-file real-API DoD re-run (environmental; the dedicated bilingual LinkedIn run already passed both labels green before the 402 wall). Status is `human_needed` per the decision tree — automated checks all pass; the phase awaits human/UAT and the operator re-run.

---

_Verified: 2026-09-30T14:17:13Z_
_Verifier: Claude (gsd-verifier)_
