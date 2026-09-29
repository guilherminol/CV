---
phase: "06"
plan: "05"
subsystem: linkedin-qa-panel-dod-harness
tags: [linkedin, qa-panel, react, bilingual, dod, real-api-harness, openrouter]
requires:
  - 06-04 qa envelope contract: pt-BR ok envelopes carry {"glossario": [{de, para, ocorrencias}], "bleed": [{termo, secao}]}, en ok envelopes carry null — rendered verbatim, no re-mapping
  - 06-03 result card + both mutation onSuccess paths (the only qa swap points) + the shared aria-live region
  - 02-04 harness mechanics: @_llm_guard skipif, @pytest.mark.llm, parametrize over llm_fixtures OBJECTIVE_PT/OBJECTIVE_EN, shipped_profile_path, per-run tmp runs.jsonl
provides:
  - frontend/src/components/LinkedinQaPanel.tsx — the "Verificação de idioma" panel (glossary rows {de} → {para}, amber bleed rows {termo} — {seção}, loud zero lines, always-on non-blocking legend, EN-run neutral note)
  - the qa key on the frontend LinkedIn envelope types (gerar + regen share the type) with change-BOTH-together drift comments
  - test_real_run_linkedin_pipeline_bilingual — the SC4 definition-of-done gate (D-15): any prompts/*.md (glossario.md included) edit is not done until `uv run pytest tests/test_llm_harness.py -m llm -q` is green
affects:
  - /gsd:verify-work (SC4 phase gate: offline green + -m llm green)
  - any future prompt/glossário edit (the DoD gate now exists and applies)
tech-stack:
  added: []
  patterns:
    - payload rendered verbatim as JSX text children — no client-side qa recomputation anywhere (Pitfall 4 truthfulness)
    - qa lives INSIDE the result state and swaps wholesale in exactly the two mutation onSuccess paths; edits/restores never reference it
    - limit-or-flag assertions pin the D-07 contract against the config constants (surfaced, never truncated)
    - runs.jsonl stage-set equality on a fresh per-run tmp log + a D-10 content-key guard (messages/input/input_text/response/output must never appear)
key-files:
  created:
    - frontend/src/components/LinkedinQaPanel.tsx
  modified:
    - frontend/src/api/client.ts
    - frontend/src/constants/ui.ts
    - frontend/src/pages/LinkedInHome.tsx
    - backend/tests/test_llm_harness.py
decisions:
  - "Rule 3 (blocking plan-example bug): the research/plan DoD example asserts envelope[\"status\"] == \"ok\" on the DIRECT pipeline call, but run_linkedin_pipeline returns {idioma, secoes, limites, qa} WITHOUT the status key — the gerar route adds {\"status\": \"ok\", **result} (pinned offline in test_linkedin_api.py). The harness asserts the direct-call envelope shape instead; a literal copy would KeyError every run."
  - "The plan's OPTIONAL secondary glossary test was deliberately not written: the pt-BR parametrization already runs with the shipped glossario.md (prompts_dir=None) and asserts qa.glossario is list-valued — a second 4-stage real-API run would re-buy zero new assertions (T-06-16 spend discipline: 8 stage calls per full LinkedIn run is the bounded spend)."
  - "Legend renders in BOTH branches (dict and null) — UI-SPEC says always; the EN neutral note replaces only the two blocks."
  - "QA-panel block labels use h4 under the h3 title (heading hierarchy); classes verbatim per the UI-SPEC Component conventions table."
metrics:
  duration: 21 min
  completed: 2026-09-29
actuals:
  tokens: 4647 # chars/4 over the realized diff (18588 diff chars)
  tasks: 2
  commits: 2 # measured: git rev-list --count f48d6b4e727eeaa4d658c48541aed79ec7fc2be4..HEAD
plan_head_before: f48d6b4e727eeaa4d658c48541aed79ec7fc2be4
status: complete
---

# Phase 6 Plan 5: QA Panel + Bilingual DoD Harness Summary

**One-liner:** the "Verificação de idioma" panel now renders the deterministic QA payload verbatim below the LinkedIn result card (substitutions, amber bleed rows, loud zero lines, always-on legend, EN neutral note — swapped only by generation success), and the SC4 definition-of-done is operational: parametrized bilingual real-API LinkedIn fixtures in `pytest -m llm` asserting the limit-or-flag contract, the qa envelope contract, the four-stage runs.jsonl audit, and the UTF-8 probe.

## What Was Built

- **Task 1 — QA panel (frontend):** `LinkedinQaPayload` types on the client (glossario rows carry `ocorrencias` for auditability; bleed rows `{termo, secao}`; `qa: payload | null` on the ok envelope — regen shares the gerar type). `QA_*` constants block per the UI-SPEC copy table (title, block labels, loud zero lines, legend, EN-run note). New `LinkedinQaPanel`: bare `section` directly below the result card inside the shared aria-live region, title `h3 text-base font-semibold text-gray-900`, block labels `mt-4 text-sm font-semibold`, glossary rows `text-sm text-gray-700` as `{de} → {para}` (plain-text arrow), bleed rows `text-sm text-amber-800` as `{termo} — {seção}`, zero lines `text-sm text-gray-500`, legend `mt-4 text-xs text-gray-500` ALWAYS rendered, `qa === null` → the neutral EN note instead of the two blocks. All rows render backend payload data verbatim — zero client-side recomputation exists (no matching logic imported into the frontend). Wiring: the panel reads `resultado.qa`; the full-gerar onSuccess swaps wholesale via `setResultado(data)`; the regen onSuccess adds `qa: data.qa` to its wholesale swap — exactly the two generation-success paths touch qa; edits/restores go through `comSecoes` and never reference it (no useMemo, truthfulness rule).
- **Task 2 — DoD harness (backend):** `LINKEDIN_PIPELINE_STAGES` (the four linkedin stage strings — no extraction stage) and `test_real_run_linkedin_pipeline_bilingual` (`@_llm_guard` + `@pytest.mark.llm`, parametrized over the EXISTING `OBJECTIVE_PT`/`OBJECTIVE_EN`, labels linkedin-PT/linkedin-EN; shipped persona via `PROFILE_PATH` monkeypatch; per-run tmp `runs.jsonl`; `run_linkedin_pipeline(..., client=None)` — the real path). Assertions: direct-call envelope shape; idioma match; D-07 limit-or-flag for headline/sobre/per-entry descrições against the config constants (with `limites.limite` pinned to the constants and experiências index-alignment checked); habilidades non-empty when the profile has skills + sanity-record consistency; pt-BR `qa` dict with list-valued `glossario`/`bleed` + sobre UTF-8 accent probe; en `qa is None`; runs.jsonl stage set == exactly the four linkedin stages with model/language/attempt fields and a D-10 content-key guard (`messages`/`input`/`input_text`/`response`/`output` must never appear).

## Tasks Completed

| Task | Name | Commit |
| ---- | ---- | ------ |
| 1 | "Verificação de idioma" QA panel (frontend) | feb53cc |
| 2 | DoD harness — bilingual real-API LinkedIn fixtures (-m llm) | ba5076c |

## Verification

- `cd frontend && npm run build` → **green** (tsc -b; 85 modules — the panel is the +1)
- `cd backend && uv run pytest -q` → **403 passed, 9 deselected** (the exact 06-04 baseline + the 2 new marker-gated tests; offline suite untouched, marker discipline intact per the marker-less collection check)
- **Real-API spend (the SC4 DoD):** `uv run pytest tests/test_llm_harness.py -m llm -q -k linkedin` → **2 passed, 12 deselected in 64.10s — BOTH LinkedIn labels (linkedin-PT, linkedin-EN) PASSED, no skips**, with every new assertion live (stage audit, limit-or-flag, qa contract, UTF-8 probe).
- ⚠ **The full-file command `uv run pytest tests/test_llm_harness.py -m llm -q` could not complete green: OpenRouter returned 402 `Payment Required` mid-run — the account's credit balance ran out ("You requested up to 3000 tokens, but can only afford 2490", `in_flight_budget_exhausted`).** Two full-file attempts failed on the same 402 class (first on linkedin-skills, then progressively: linkedin-sobre + one PRE-EXISTING resume-pipeline test). This is an account-level spend blocker, loudly surfaced by design (no catch-and-pass, D-03) — it also fails pre-existing harness tests, so no code change can or should mask it. **Recorded honestly per the plan's own rule: a skipped/failed harness run is NOT green — the full-file green remains to be claimed after topping up credits at https://openrouter.ai/settings/credits, then re-running `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q`.** The blocker is logged in `.planning/WINDOWS.md` (entry 10, unrun-verify) and in STATE.md blockers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking plan-example bug] `status` assertion adapted for the direct pipeline call**
- **Found during:** Task 2 (test authoring against the real signature)
- **Issue:** The research DoD example (and the plan's "status == ok" line) asserts `envelope["status"] == "ok"` on the result of `run_linkedin_pipeline(...)` — but the pipeline returns `{idioma, secoes, limites, qa}` WITHOUT the status key; the gerar route adds it via `{"status": "ok", **result}`. A literal copy would KeyError on every run.
- **Fix:** Assert the direct-call envelope shape `set(envelope) == {"idioma", "secoes", "limites", "qa"}` with a comment pointing at the offline-pinned route wrap; reaching the assertions at all proves no stage raised (all-or-nothing).
- **Files modified:** backend/tests/test_llm_harness.py
- **Commit:** ba5076c

### Deliberate Scope Decisions

- The plan's OPTIONAL secondary glossary test was not written: the pt-BR parametrization already runs against the shipped glossário and asserts `qa["glossario"]` is list-valued; a duplicate real-API run adds no new assertion and doubles the bounded spend (T-06-16).

## Auth / Spend Gates

- **OpenRouter credit exhaustion (402 Payment Required)** — surfaced during the full-file `-m llm` run. The key itself is present and valid (loaded from the root `.env`; the dedicated LinkedIn run succeeded moments earlier). Required user action: add credits at https://openrouter.ai/settings/credits, then re-run `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q` to claim the full-file DoD green. NOT mocked to green (the plan and the orchestrator instruction both forbid it).

## Known Stubs

None created by this plan. (The QA panel is fully wired to the live 06-04 payload; the DoD gate exists with both LinkedIn fixtures proven green on the real API in the dedicated run — the open item is the credit-blocked FULL-FILE re-verification, tracked as WINDOWS.md entry 10, not a stub.)

## Notes for /gsd:verify-work

- Offline gate: 403 passed, 9 deselected. Build gate: green.
- Real-API gate: LinkedIn fixtures proven green (dedicated run, both labels, no skips, 64.10s) BEFORE the credit wall; the full-file `-m llm` green is pending the credit top-up + one re-run command. Until then the SC4 DoD is "mechanism proven, full-file run pending credits" — verify-work should treat WINDOWS.md entry 10 as the open item.
- The qa swap points are exactly `gerar.onSuccess` (wholesale `setResultado(data)`) and `regenerar.onSuccess` (`qa: data.qa` in the spread) — code-inspection provable; edits/restores never reference qa.

## Self-Check: PASSED

- Created file verified on disk: frontend/src/components/LinkedinQaPanel.tsx; modified files verified via git diff (4 total, all in the task file lists).
- Commits verified in git log: feb53cc, ba5076c.
- `git rev-list --count f48d6b4e727eeaa4d658c48541aed79ec7fc2be4..HEAD` = 2 (matches the commits ledger; working tree clean of plan-related code changes).
