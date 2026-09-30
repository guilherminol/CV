---
phase: 06-linkedin-module-bilingual-hardening
reviewed: 2026-09-30T13:40:15Z
depth: standard
files_reviewed: 29
files_reviewed_list:
  - backend/app/linkedin/__init__.py
  - backend/app/linkedin/models.py
  - backend/app/linkedin/pipeline.py
  - backend/app/linkedin/qa.py
  - backend/app/llm/gateway.py
  - backend/app/llm/schemas.py
  - backend/app/config.py
  - backend/app/main.py
  - backend/app/resume/facts.py
  - backend/app/routes/linkedin.py
  - backend/tests/test_linkedin_api.py
  - backend/tests/test_linkedin_pipeline.py
  - backend/tests/test_linkedin_qa.py
  - backend/tests/test_linkedin_regen_pipeline.py
  - backend/tests/test_linkedin_schema.py
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
  - prompts/linkedin-headline.md
  - prompts/linkedin-sobre.md
  - prompts/linkedin-experiencias.md
  - prompts/linkedin-skills.md
findings:
  critical: 0
  warning: 6
  info: 3
  total: 9
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-09-30T13:40:15Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Summary

Reviewed the LinkedIn module end-to-end at standard depth: the backend package (`app/linkedin/`), the gateway/schema extensions, the route layer, the five offline test files, the LinkedIn frontend surface (page + five components + client + constants), and the five prompt/glossário files. Cross-file contracts (client↔server bounds mirrors 80/2000/220/2600/2000/500, `LinkedinLimitesDTO`↔`_build_limites`, wire-schema↔Pydantic drift locks, stage registrations, envelope key sets) were checked and hold.

The strong parts are real: strict wire schemas with a working drift-lock harness, envelope/raw-detail terminal split consistently enforced, prompt-injection posture (objetivo/dica as user-message data) held everywhere, no secrets/debug artifacts/raw-HTML paths found, and the loud-empty retry semantics are inherited cleanly from the gateway.

The defects found are concentrated in three places: (1) the regen path's QA step **mutates sibling sections through the glossário**, empirically breaking the documented sibling byte-identity contract (WR-01, confirmed by execution); (2) the experiência alignment machinery silently drops surplus LLM entries and, in its fallback mode, causes the frontend to render **mislabeled headers** over text generated for a different company (WR-02/WR-03); (3) a loud-empty asymmetry makes the whole module unusable for zero-experience profiles with a misleading error (WR-05, confirmed by execution). Three lower-severity quality findings round it out.

No `<structural_findings>` block was provided with this review request, so there is no fallow section.

## Warnings

### WR-01: Section-regen response mutates sibling text via the glossário — breaks the documented sibling byte-identity contract (D-04/SC1)

**File:** `backend/app/linkedin/pipeline.py:352-378` (merged dict + QA call), `backend/app/linkedin/qa.py:226-233` (mutating substitution loop)

**Issue:** `run_linkedin_section_regen` builds `merged` with siblings by reference and replaces only the target block, then calls `run_linkedin_qa(merged, ...)`, which applies glossário substitutions to **all** prose surfaces — including the siblings. The response's sibling text is therefore the post-glossary text, not what was submitted. Empirically confirmed: with a glossário pair `machine learning → aprendizado de maquina`, regenerating `headline` over a submitted `sobre` of `"Especialista em machine learning e dados."` returned `"Especialista em aprendizado de maquina e dados."` — the sibling the user did NOT regenerate silently changed. The client (`frontend/src/pages/LinkedInHome.tsx:479-489`) swaps `secoes` wholesale, so the user's displayed About text changes with no badge flip and no attribution. The existing byte-identity tests only pin the empty-glossário case (`test_linkedin_regen_pipeline.py:560` uses `_write_glossario(tmp_path, [])`), and the shipped glossário (`prompts/glossario.md`) has 3 live pairs, so this fires in production whenever a sibling contains a listed term (including after a user edits the glossário between gerar and regen — D-12's own edit-and-next-run feature). `qa.glossario` rows carry only `{de, para, ocorrencias}` with no surface label, so the change is not even attributable to a section.

**Fix:** Apply glossário substitutions only to the regenerated block while still *detecting* over the full merged state. Concretely, snapshot siblings before `run_linkedin_qa` and restore them after (mutation is then confined to the target), e.g.:

```python
snapshot = {k: merged[k] for k in ("headline", "sobre", "habilidades")}
if secao != "experiencias":
    pre_exp = [dict(e) for e in merged["experiencias"]]
qa = run_linkedin_qa(merged, language, prompts_dir=prompts_dir)
# restore non-target surfaces so siblings stay byte-identical
```

—or pass the target section id into `run_linkedin_qa` so it mutates only that surface. Either way, add a regen test with a **non-empty** glossário asserting sibling byte-identity (`envelope["secoes"]["sobre"] is submitted.sobre`), which currently cannot pass.

### WR-02: `_align_experiencias` silently drops surplus returned entries in the matched path

**File:** `backend/app/linkedin/pipeline.py:141-156`

**Issue:** When every profile experience pairs successfully, the function returns only the matched entries; any returned entries beyond the profile count are silently discarded. Empirically confirmed: 1 profile experience + 3 returned entries (one pairs by company) → output is exactly 1 entry; the other two generated texts vanish with no report row, no fallback, and no limites trace. This is asymmetric with the module's own stated philosophy — on a pairing *failure* the all-entries fallback deliberately keeps everything ("rather than crashing", line 151-153) — and the dropped entries are exactly the hallucination/duplicate case where auditability matters most. The loud-empty/limites reporting machinery would surface any other form of content loss; this one is invisible.

**Fix:** Keep unused returned entries in returned order after the matched ones, or flip to the all-entries fallback when `len(returned) != len(profile_experiences)`:

```python
matched.extend(returned[i] for i in range(len(returned)) if i not in used)
return [entry.model_dump() for entry in matched]
```

(at minimum, document and test the drop as intended behavior).

### WR-03: Frontend anchors experiência headers to profile facts by index even when the pipeline returned the fallback (returned-order) list

**File:** `frontend/src/pages/LinkedInHome.tsx:1168-1173`; contract source `backend/app/linkedin/pipeline.py:151-153`

**Issue:** `renderBlocoExperiencias` renders each entry's header from `perfilExps[i]` ("Index-aligned pairing (06-02 alignment contract)"). Index alignment holds only in the fold-match mode; when ANY company pairing fails, `_align_experiencias` returns ALL entries in **returned** order, so `entry[i]` no longer corresponds to `perfilExps[i]`. In that state the card shows profile company/title headers over a `descricao` generated for a different employer, and per-entry Copiar copies that text under the wrong company header — a real deliverable corruption if the user pastes it into LinkedIn. The comparison panel for the same entries uses fold-matching and shows the neutral fallback note, so the card and the panel visibly disagree. The backend does not surface which alignment mode was used, so the client cannot distinguish the two.

**Fix:** Either (a) have the pipeline report the alignment mode (e.g. `"experiencias_alinhadas": true|false` in the envelope) and let the client fall back to the entry's own `company`/`title` anchors when false, or (b) verify client-side before anchoring:

```tsx
const anchorOk = perfilExp && fold(perfilExp.company) === fold(entrada.company)
const company = anchorOk ? perfilExp.company : entrada.company
const title = anchorOk ? tLang(perfilExp.title, resultado.idioma) : entrada.title
```

### WR-04: Comparison panel pairs every same-company generated entry to the FIRST profile entry (no consumed-match tracking)

**File:** `frontend/src/components/LinkedinComparisonPanel.tsx:220-253`

**Issue:** The panel resolves each generated entry with `perfil.experiences.find((exp) => fold(exp.company) === fold(entrada.company))` — always the first match. The backend explicitly supports same-company duplicate entries (the LI-04/adjacency vector: profile `[Exemplo IA, Outra Corp, Exemplo IA]`) and consumes one distinct profile entry per generated entry (first-unused-match, `pipeline.py:141-156`). For two generated "Exemplo IA" entries the panel compares BOTH against profile entry 0's facts and renders profile entry 0 twice in the facts column — wrong grounding target and duplicated facts rows for a first-class supported vector, which can both under- and over-flag suspects.

**Fix:** Mirror the backend's consumption semantics:

```tsx
const used = new Set<number>()
const comparadas = (entradas ?? []).map((entrada) => {
  const idx = perfil.experiences.findIndex(
    (exp, i) => !used.has(i) && fold(exp.company) === fold(entrada.company))
  if (idx >= 0) used.add(idx)
  const alvo = idx >= 0 ? perfil.experiences[idx] : null
  ...
```

### WR-05: Zero-experience profiles can never generate — loud-empty asymmetry makes the documented "legitimate display state" unreachable and the error misleading

**File:** `backend/app/linkedin/pipeline.py:159-175` (no profile-aware exception) vs `pipeline.py:194-208` (habilidades IS profile-aware); `backend/app/linkedin/models.py:14-17`; `frontend/src/pages/LinkedInHome.tsx:1140-1148`

**Issue:** `_process_experiencias` raises on an empty returned list unconditionally, while `_process_habilidades` was deliberately made profile-aware ("fails ONLY when the profile HAS skills"). Empirically confirmed: a valid profile with `experiences: []` and a returned `{"experiencias": []}` fails the ENTIRE gerar (all-or-nothing — headline/sobre/habilidades are lost too) with `"O modelo devolveu uma lista de experiências vazia — regenere as seções"`, which instructs the user to regenerate something that can never succeed. This contradicts `models.py`'s own docstring ("a profile with zero experiences ... is a legitimate display state") and makes the frontend's `LINKEDIN_EXPERIENCIA_ZERO` line unreachable after gerar. Additionally, the frontend zero-line branch `perfilExps.length === 0 || entradas.length === 0` prints "Nenhuma experiência **no perfil**" even in the `entradas.length === 0` arm where the profile may well have experiences.

**Fix:** Make the guard profile-aware, mirroring `_process_habilidades`:

```python
if not returned and profile_experiences:
    raise LLMError(...)
```

…and differentiate the frontend zero-line text per cause (profile-empty vs list-empty), or keep it strictly profile-gated.

### WR-06: Section regen issues a dead-end 422 when the edited objetivo no longer meets the 80..2000 bound

**File:** `frontend/src/pages/LinkedInHome.tsx:626-635` (`regenerarSecaoAgora`) and `955-969` (`renderRegenerarBotao`)

**Issue:** Regen requests carry the CURRENT form `trimmed` objetivo, and the Regenerar buttons are gated only on `operacaoLongaPendente` — not on objective validity. If the user shortens or clears the objetivo after generating, every subsequent regen POST returns FastAPI's 422, `regenerarSecaoLinkedin` throws, and the block renders the generic fetch-failure panel ("Tente regenerar novamente... o detalhe técnico completo aparece no terminal") — misattributing a client-fixable validation failure to a server fault, and unfixable by retrying. This is precisely the "dead-end 422" class the phase's own WR-01 client mirrors exist to prevent (`constants/ui.ts:305-317`), and the min bound has no textarea cap to prevent it (unlike the max).

**Fix:** Gate the regen path on the objective bound — disable Regenerar buttons with `LINKEDIN_OBJETIVO_TOO_SHORT_HINT` when `trimmed.length < LINKEDIN_OBJETIVO_MIN_CHARS`, or map non-200 responses to a bound-specific message instead of the generic fetch-failure hint.

## Info

### IN-01: `ContadorLimite` is a component defined inside the LinkedInHome render body

**File:** `frontend/src/pages/LinkedInHome.tsx:869-880`

**Issue:** Defining a component inside another component gives it a fresh type identity every render, so React unmounts/remounts its whole subtree on each parent render. Benign today (the subtree is stateless), but it breaks reconciliation and is a footgun the moment state or refs are added inside.

**Fix:** Hoist to module scope next to `LinkedinLintPanel` (it needs no closure variables beyond its props).

### IN-02: QA bleed labels for experiências use the RETURNED entry's company string, not the profile-fact anchor the docstring claims

**File:** `backend/app/linkedin/qa.py:236-244`; frontend headers at `frontend/src/pages/LinkedInHome.tsx:1171-1173`

**Issue:** `run_linkedin_qa` labels experiência bleed rows with `entry["company"]` — the model-returned string, which the alignment contract explicitly allows to deviate ("EXEMPLO IA", "exemplo ia" ride into the displayed state per the pipeline's own test). The docstring calls it "the fixed profile-fact anchor the frontend renders as the sub-block header", but the frontend renders headers from PROFILE facts, so a QA row (`termo — EXEMPLO IA`) can disagree with the header rendered above the same text (`Exemplo IA`).

**Fix:** After alignment, overwrite each entry's `company` with the paired profile company (the display anchor is profile facts regardless), or label bleed rows from the profile side; at minimum correct the docstring to "the returned anchor string".

### IN-03: Per-entry version stacks can become unreachable after count-changing swaps

**File:** `frontend/src/pages/LinkedInHome.tsx:647-665`, `1150-1153`, `1214-1225`

**Issue:** Version stacks are keyed `experiencias-${i}` by index. After a gerar/regen that changes the entry count (or reorders under WR-03's fallback), stacks for indices beyond the new length remain in `versoes` but are neither counted by the group Versões toggle (which reduces over CURRENT `entradas` indices) nor rendered — stored versions silently become unreachable, contradicting the "never capped, never silently dropped" comment at line 300. Data is session-only, so impact is bounded.

**Fix:** Count the group toggle from the stacks themselves (`Object.keys(versoes).filter((k) => k.startsWith('experiencias-')).reduce(...)`) so stored versions stay visible, or prune orphaned `experiencias-N` keys on wholesale swaps.

---

_Reviewed: 2026-09-30T13:40:15Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
