---
phase: 03-resume-vertical-slice
plan: 05
subsystem: testing
tags: [pytest, grounding, llm-harness, openrouter, invention-detection, pt-br, offline-tests]

# Dependency graph
requires:
  - phase: 03-01/03-03 (resume prompts + pipeline)
    provides: prompts/resume-*.md grounding rules, facts.serialize_profile_facts, run_resume_pipeline single call path, runs.jsonl audit
  - phase: 02-llm-generation-core
    provides: gateway run_stage, -m llm marker + offline addopts, harness discipline (no catch-and-pass, no bespoke clients)
provides:
  - extract_numerals/assert_invention_free — mechanical SC3 invention check importable by any future test (Phases 4-6 can reuse)
  - Offline grounding-discipline suite pinning prompt rules, budgets, and facts purity
  - Real-API bilingual full-pipeline harness (EN/PT-BR) with per-stage runs.jsonl audit and live invention policing
affects: [phase 4 pdf export, phase 5 review flow (fact-vs-generated diff), phase 6 linkedin, verify-work]

# Actuals (#2632)
actuals:
  tokens: 5361
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: [] # no new packages — vitest deliberately NOT adopted (server-side tally decision, plan 03-03)
  patterns: [numeral-allowlist invention detection, marker-gated spend harness at pipeline scale]

key-files:
  created:
    - backend/tests/test_resume_grounding.py
  modified:
    - backend/tests/test_llm_harness.py

key-decisions:
  - "Invention detector lives in the test module (not app code): extract_numerals + assert_invention_free require every numeral/date/percentage in generated text to exist in serialize_profile_facts output, substring semantics — importable by the harness"
  - "Detector runs LIVE in the -m llm harness over the composed generated text — an invented 87% or unknown date fails the real-API run loudly (SC3 mechanics)"
  - "Budget floors pinned as >= (2000/4000/2000) with temperature <= 0.5 — the Pitfall 5 truncation guard survives future budget raises"
  - "Harness pipeline tests monkeypatch PROFILE_PATH to the shipped example profile (invention detectable there) — test persona == shipped persona"

patterns-established:
  - "Grounding triad: prompt rule + facts purity + numeral detector — three independent offline layers proving SC3"
  - "Pipeline-scale real-API test: run_resume_pipeline(jd, language, runs_log=tmp) with client=None; per-stage audit asserted, never a bespoke SDK client"

requirements-completed: [RESUME-03, RESUME-01]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Prompt discipline pinned offline: all three resume prompts carry the FATOS DO PERFIL anchor, the never-invent rule (NUNCA co-occurring with the facts reference in one rules paragraph), the injection clause, and non-truncating budgets (max_tokens >= 2000/4000/2000, temperature <= 0.5)"
    requirement: RESUME-03
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_grounding.py#test_prompt_body_carries_grounding_contract + test_prompt_frontmatter_non_truncating_budget (14 passed offline)"
      - kind: unit
        ref: "cd backend && uv run pytest tests/test_resume_grounding.py -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "Facts purity proven mechanically: serialize_profile_facts carries the fixture's own metric/certification and never contains absent probes (Snowflake, PMP, Kubernetes, 2019) in both languages"
    requirement: RESUME-03
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_grounding.py#test_facts_blob_contains_fixture_metric_and_certification + test_facts_blob_never_contains_absent_probes"
        status: pass
    human_judgment: false
  - id: D3
    description: "Invention detector works: extract_numerals (dates whole, percentages with sign, identifier-guard) + assert_invention_free raising AssertionError naming the offending token; wired into an offline pipeline run"
    requirement: RESUME-03
    verification:
      - kind: unit
        ref: "backend/tests/test_resume_grounding.py#test_assert_invention_free_raises_naming_the_token + test_pipeline_run_passes_the_invention_detector"
        status: pass
    human_judgment: false
  - id: D4
    description: "Real-API bilingual full-pipeline harness green: JD_EN/en and JD_PT/pt-BR each return the ok envelope through run_resume_pipeline client=None on the shipped profile — non-empty sections, cobertura consistency, assert_invention_free over live generated text, per-stage runs.jsonl audit (all four stages), PT-BR accent probe"
    requirement: RESUME-01
    verification:
      - kind: e2e
        ref: "backend/tests/test_llm_harness.py#test_real_run_resume_pipeline_bilingual (uv run pytest -m llm -v → 7 passed incl. pipeline-EN + pipeline-PT)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Default suite stays 100% offline: pytest -q green with no network; real-API tests marker-gated (llm) and skipif-guarded on OPENROUTER_API_KEY"
    verification:
      - kind: unit
        ref: "cd backend && uv run pytest -q → 183 passed, 7 deselected"
        status: pass
    human_judgment: false
  - id: D6
    description: "Generated PT-BR and EN sections read naturally, non-machine-translated (VALIDATION.md manual row)"
    requirement: RESUME-01
    verification: []
    human_judgment: true
    rationale: "Prose quality is human judgment; the executor ran the harness (7/7 green) but no human has read the generated sections yet — read the harness output or re-run pytest -m llm at end-of-phase verification"
  - id: D7
    description: "Browser walkthrough of the Currículo screen confirming SC1-SC5 per 03-UI-SPEC: lint panel at >= 80 chars, Gerado/Do perfil badges, 4 fixed coverage categories with chips, plain tally line (no numeric score), ephemeral notice, Gerar novamente, prior result survives a failed re-run, 30+ keyword JD keeps the panel readable (backstop)"
    verification: []
    human_judgment: true
    rationale: "Visual UI verification needs a human in the browser — the executor is a subagent without browser tooling; routed to end-of-phase human verification per human_verify_mode=end-of-phase (recorded in WINDOWS.md)"

# Metrics
duration: 12min
completed: 2026-09-26
status: complete
---

# Phase 3 Plan 5: Grounding Proof + Bilingual Harness Summary

**SC3 no-invention bar enforced by three offline layers (prompt rules, facts purity, numeral detector) plus a live bilingual full-pipeline harness — real-API 7/7 green including invention-free EN and PT-BR runs on the shipped profile**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-26T22:28:55Z
- **Completed:** 2026-09-26T22:41:32Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Offline grounding discipline pinned in `backend/tests/test_resume_grounding.py` (14 tests): prompt contract (anchor + never-invent rule + injection clause), Pitfall 5 budget floors 2000/4000/2000 with temperature <= 0.5, facts purity probes, and the `extract_numerals`/`assert_invention_free` detector unit-tested and wired into an offline pipeline run
- Real-API bilingual pipeline harness extended in `backend/tests/test_llm_harness.py`: `test_real_run_resume_pipeline_bilingual` over (JD_EN, en) and (JD_PT, pt-BR) drives the FULL pipeline through `run_resume_pipeline` with `client=None` on the shipped example profile, asserting the ok envelope, section substance, cobertura consistency, live invention-free text, per-stage runs.jsonl audit, and the PT-BR accent probe
- Phase gate executed: full offline suite 183 passed; frontend `npm run build` (tsc) green; real-API harness `pytest -m llm -v` 7 passed in 102s — including both bilingual pipeline runs where the invention detector held against live model output

## Task Commits

Each task was committed atomically:

1. **Task 1: Offline grounding discipline (prompt rules, facts purity, invention detector)** - `9e3cb06` (feat)
2. **Task 2: Real-API bilingual pipeline harness (marker-gated)** - `7e5ada9` (feat)
3. **Task 3: End-of-phase verification (gates run, no code changes needed)** - no commit (verification-only; all gates green; human-check routed to end-of-phase)

**Plan metadata:** docs commit (see completion report)

## Files Created/Modified
- `backend/tests/test_resume_grounding.py` - Prompt-discipline + facts-purity tests and the extract_numerals/assert_invention_free invention detector (offline, importable)
- `backend/tests/test_llm_harness.py` - Parametrized bilingual real-API pipeline tests (@_llm_guard + @pytest.mark.llm) with per-stage runs.jsonl audit assertions

## Decisions Made
- Invention detector lives in the test module (not app code) per the plan's artifacts spec — a mechanical SC3 check with substring semantics over `serialize_profile_facts` output
- Detector runs LIVE in the harness over the composed generated text (resumo + bullets + habilidades recomputed exactly as the pipeline does)
- Budget assertions pin floors (`>=`) rather than equality, so the truncation guard survives future budget raises
- Harness pipeline tests point `PROFILE_PATH` at the shipped example profile — invention is detectable on the example persona (D-07)

## Deviations from Plan

None - plan executed exactly as written.

---

**Total deviations:** 0 auto-fixed
**Impact on plan:** No unplanned work; the Pitfall 4 fix path (wire-schema shape / prompt nudge) prepared for the harness run was never needed — both bilingual runs passed first try.

## Issues Encountered
- Task 2's precondition named `backend/.env`, but the key actually lives in the repo-root `.env` (loaded by `backend/app/config.py` via `load_dotenv(REPO_ROOT / ".env")`). Precondition met in substance — key present (presence + length verified, never printed); no action needed.
- Task 3's human-check (Currículo browser walkthrough per 03-UI-SPEC + PT-BR/EN prose quality read per 03-VALIDATION.md) is not executable by the executor subagent (no browser tooling for subagents). Routed to end-of-phase human verification per `human_verify_mode: end-of-phase` — run `/gsd:verify-work 3`. Also recorded in `.planning/WINDOWS.md` (unrun-verify).

## User Setup Required

None - no external service configuration required (OPENROUTER_API_KEY already configured in the local `.env`).

## Next Phase Readiness
- Phase 3's automated gate is fully green: offline suite 183 passed / 7 deselected, frontend tsc build green, real-API bilingual harness 7/7 (spend ~102s of live calls) including invention-free full-pipeline EN and PT-BR runs
- Remaining before phase close (human): the browser walkthrough (SC1-SC5 zones/badges/chips/ephemeral notice/Gerar novamente, 30+ keyword backstop) and the prose quality read — `/gsd:verify-work 3`
- Phase 4 (PDF export + ATS parse-back) can start: the D-05 resume assembly (3 generated sections + profile passthrough) that Phase 4 renders as PDF is complete and contract-tested

---
*Phase: 03-resume-vertical-slice*
*Completed: 2026-09-26*

## Self-Check: PASSED

- backend/tests/test_resume_grounding.py exists on disk
- backend/tests/test_llm_harness.py extended and committed
- Commits 9e3cb06 (Task 1) and 7e5ada9 (Task 2) found in git log
- Offline suite 183 passed / 7 deselected; -m llm harness 7 passed; frontend build green
