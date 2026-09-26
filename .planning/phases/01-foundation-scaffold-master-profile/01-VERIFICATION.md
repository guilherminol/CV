---
phase: 01-foundation-scaffold-master-profile
verified: "2026-09-26T23:39:05Z"
status: human_needed
score: 7/12 must-haves verified
covered_files: [".env.example", ".gitignore", ".planning/REQUIREMENTS.md", ".planning/phases/01-foundation-scaffold-master-profile/01-01-PLAN.md", ".planning/phases/01-foundation-scaffold-master-profile/01-01-SUMMARY.md", ".planning/phases/01-foundation-scaffold-master-profile/01-02-PLAN.md", ".planning/phases/01-foundation-scaffold-master-profile/01-02-SUMMARY.md", ".planning/phases/01-foundation-scaffold-master-profile/01-03-PLAN.md", ".planning/phases/01-foundation-scaffold-master-profile/01-03-SUMMARY.md", "README.md", "backend/app/config.py", "backend/app/main.py", "backend/app/profile/completeness.py", "backend/app/profile/errors.py", "backend/app/profile/loader.py", "backend/app/profile/models.py", "backend/app/routes/profile.py", "backend/pyproject.toml", "backend/tests/conftest.py", "backend/tests/test_api.py", "backend/tests/test_loader.py", "backend/tests/test_schema.py", "backend/tests/test_secrets.py", "backend/uv.lock", "content/profile.md", "frontend/index.html", "frontend/package.json", "frontend/src/App.tsx", "frontend/src/api/client.ts", "frontend/src/components/CompletenessGrid.tsx", "frontend/src/components/ErrorPanel.tsx", "frontend/src/components/PlaceholderBanner.tsx", "frontend/src/components/ProfilePreview.tsx", "frontend/src/constants/ui.ts", "frontend/src/index.css", "frontend/src/main.tsx", "frontend/vite.config.ts"]
covered_digest: "v1:sha256:0a794905beace20a9c11f9c48ac40e19f6f0adfc25529d2304ec1012b15e5d0d"
behavior_unverified: 5
overrides_applied: 0
unverified-prohibition: "human review recommended — 3 judgment-tier prohibitions carry non-authoritative LLM-judge PASS verdicts re-checked against the current codebase (see Human Verification item 5); never silently passed"
mvp_user_story_guard: "FAILED — phase goal is not in 'As a..., I want..., so that...' format (user-story.validate returned false at initial verification). Verification proceeded goal-backward on the 5 explicit roadmap SCs instead of a User Flow Coverage table. Orchestrator may run /gsd mvp-phase 1 to formalize."
re_verification:
  previous_status: human_needed
  previous_score: 7/12
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Nav item LinkedIn renders as an enabled module"
    addressed_in: "Phase 6"
    evidence: "Phase 6 goal: 'LinkedIn Module + Bilingual Hardening'. The disabled LinkedIn nav placeholder is by-design (D-12), tracked open in .planning/WINDOWS.md entry 1. (The Currículo half of the previous deferred item is resolved: phase 3-04 enabled it and made it the default landing view.)"
behavior_unverified_items:
  - truth: "User starts the app locally and sees the PT-BR interface at localhost (SC1)"
    test: "npm run build, then uv run uvicorn app.main:app; open http://127.0.0.1:8000 (app now lands on the Currículo view per phase 3-04) and click 'Perfil' in the nav"
    expected: "PT-BR shell renders: 'Career Tailor' header, nav (Currículo + Perfil enabled, LinkedIn disabled), 'Perfil carregado' status line, completeness grid, resume preview"
    why_human: "DOM rendering of the React shell is runtime behavior; the repo still has no frontend test runner (scripts: dev/build/lint/preview only, unchanged by phase 3). HTTP-level serving IS test-proven in the current suite (test_get_serves_spa_index_html); the visual render is not."
  - truth: "The app visibly flags that placeholder data is in use (SC3 visual half; data half is fully proven)"
    test: "With content/profile.md carrying example: true, open the Perfil view at http://127.0.0.1:8000"
    expected: "Amber banner 'Dados de exemplo' with the explanatory subtitle is visible above the grid/preview"
    why_human: "Banner visibility is a browser-visual property; wiring is grep-proven on the current App.tsx (`{data.exemplo && <PlaceholderBanner />}`) but no test renders the DOM."
  - truth: "A broken profile is a rendered UI state: PT-BR error lines shown in-app, verbatim from the backend (plan-03 truth)"
    test: "Rename a key in content/profile.md (e.g. certifications -> certificacoes_typo), refresh the browser"
    expected: "ErrorPanel lists 'Erro no perfil: ...profile.md' plus the PT-BR line naming the exact key; app shell stays up; uvicorn terminal shows the raw extra_forbidden detail"
    why_human: "ErrorPanel rendering is DOM behavior; the backend erro-envelope half is integration-tested and green in the current suite (test_get_profile_erro_envelope_names_exact_key), the in-app render is not."
  - truth: "The preview renders localized fields with the base-language pt-BR value (plan-03 truth, D-04)"
    test: "Open the Perfil view with the healthy shipped profile and inspect experience titles/summary/impact text"
    expected: "pt-BR values shown ('Engenheira de IA Sênior', 'São Paulo...'), never English or raw {'pt-BR': ...} maps"
    why_human: "The pt-BR selection helper (t() in ProfilePreview.tsx) is code-verified and typechecked (build green this re-verification), but the rendered output is only observable in a browser."
  - truth: "Editing content/profile.md and refreshing the browser shows current data — no restart, no stale cache (plan-03 truth, D-15)"
    test: "With the app running, change a value in content/profile.md, refresh the browser, observe; restore"
    expected: "Refresh shows the new value immediately (fresh load per request); no server restart needed"
    why_human: "Server-side freshness is code-verified (loader.py unchanged since phase 1: no cache, call-time path; tests monkeypatch PROFILE_PATH proving per-call reads) but the end-to-end edit->browser-refresh invariant is an interactive runtime behavior no test exercises."
human_verification:
  - test: "SC1/SC3 browser smoke (prod mode; steps scripted in README 'Phase 1 smoke check'): npm run build, cd backend && uv run uvicorn app.main:app, open http://127.0.0.1:8000. Note: phase 3-04 made Currículo the default landing view — click 'Perfil' in the nav to reach the phase-1 Perfil home. Optionally repeat via the dev flow (two terminals) at http://127.0.0.1:5173."
    expected: "PT-BR shell with header/nav; after clicking Perfil: 'Perfil carregado' status, amber 'Dados de exemplo' banner, completeness grid (habilidades now shows '4 grupos · 15 itens' per the WR-04 fix), resume-style preview of Ana Exemplo (3 experiences, skills, projects)."
    why_human: "Visual layout, PT-BR text rendering, banner prominence, and the nav view switch are human-observable only."
  - test: "Broken-profile UI state: rename a key in content/profile.md, open the Perfil view at http://127.0.0.1:8000; check the uvicorn terminal; restore the file and refresh again."
    expected: "Red ErrorPanel names the exact file and key in PT-BR; app stays up (no crash/500 screen); terminal shows the raw technical detail; restore returns the healthy home without restart."
    why_human: "End-to-end error UX across file edit -> refresh -> panel -> recovery is interactive runtime behavior."
  - test: "Edit-refresh freshness (D-15): change a visible value in content/profile.md while the server runs, refresh, then restore."
    expected: "New value appears after browser refresh with no server restart."
    why_human: "Interactive freshness invariant; presence checks cannot observe cache-vs-fresh behavior."
  - test: "Preview base-language check (D-04): confirm every localized field in the Perfil preview shows the pt-BR value."
    expected: "No English-only rendering of localized fields, no raw language-map JSON in the page."
    why_human: "Visual confirmation of which map value renders."
  - test: "Flagged prohibition review (3 judgment-tier prohibitions carried with status unverified in PLAN frontmatter): (a) plan-01 — app starts with empty/missing OPENROUTER_API_KEY and phase-1 paths never require/call it (re-checked: config.py's tolerant read is unchanged; phase 2's gateway.py requires the key only AT CALL TIME with a loud PT-BR LLMError per its own D-03 — startup and all profile paths remain key-free, proven by the offline 183-test run); (b) plan-02 — backend never writes to content/ (re-checked: the only write in backend/app is llm/logging.py -> logs/runs.jsonl, gitignored); (c) plan-03 — UI offers no control over the example flag (re-checked: PlaceholderBanner.tsx unchanged, no interactive elements; App.tsx's new onClick handlers only switch the nav view, none touch the flag). Confirm or reject the LLM-judge PASS verdicts."
    expected: "Confirmations match the code evidence above."
    why_human: "Prohibitions are must-NOT statements whose full assurance requires human review per the judgment-tier soft gate; LLM-judge verdicts are non-authoritative."
  - test: "Package legitimacy spot-check (plan-01 T-01-SC end-of-phase human-check): spot-check npmjs.com/pypi.org for the pinned versions against the 01-RESEARCH.md Package Legitimacy Audit (react 19.3.0, vite 8.3.1, @tanstack/react-query 5.103.2, tailwindcss 4.3.3, fastapi 0.141.1, uvicorn 0.54.0, pydantic 2.13.5, python-frontmatter 1.3.0, python-dotenv 1.2.3, pytest 9.1.1, httpx 0.28.1). Phase 2 later added openai>=3.19.2 — audit it under phase 2's own gate."
    expected: "Maintainers/repos match the audit's Source Repo column; no package gained install scripts."
    why_human: "Supply-chain legitimacy requires human inspection of external registries (T-01-SC)."
---

# Phase 1: Foundation — Scaffold + Master Profile Verification Report

**Phase Goal:** The app runs locally with a PT-BR interface, and the master profile is a git-versioned, schema-validated source of truth ready to feed both generation modules.
**Verified:** 2026-09-26T23:39:05Z
**Status:** human_needed
**Re-verification:** Yes — after phases 2–3 modified shared files; validating phase-1 must-haves against the CURRENT codebase

**Why re-verified:** the initial 2026-09-26T01:07:02Z verdict predates phase 2 (LLM gateway) and phase 3 (resume vertical slice), which modified 13 phase-1 covered files — `backend/app/main.py` (resume router), `backend/app/config.py` (+LLM constants), `backend/app/profile/models.py` (date hardening), `frontend/src/App.tsx` (nav view switch), `frontend/src/api/client.ts` (+resume endpoints), `frontend/src/constants/ui.ts`, `frontend/src/components/CompletenessGrid.tsx`, `.gitignore`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/tests/{conftest,test_loader,test_schema}.py`. All 13 sit inside this report's covered_files list; the digest below is fresh.

**MVP-mode note (carried):** the phase has `mode: mvp` but its goal is not in User Story format (`user-story.validate` → false at initial verification). The User Flow Coverage table stays skipped per the format guard; verification proceeds goal-backward on the 5 explicit roadmap success criteria, which are themselves user-flow shaped.

## Goal Achievement

### Observable Truths

Roadmap SCs merged with PLAN must_haves truths (same T1–T12 set as the initial verification; statuses re-derived from the CURRENT codebase).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| T1 | SC1: User starts the app locally and sees the PT-BR interface at localhost (FastAPI-served after build, or dev servers) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Serving half re-proven on current code: `test_get_serves_spa_index_html` green in today's 183-test run; `npm run build` re-run green (fresh `frontend/dist`); current `main.py` (phase-3-modified) still registers both routers BEFORE the guarded StaticFiles mount. New since phase 3: Currículo is the default landing view; the Perfil home is one nav click away (NAV_ITEMS: Currículo+Perfil enabled, LinkedIn disabled). PT-BR shell intact. Browser-visual render → Human Verification 1 |
| T2 | SC2: Master profile loads + validates; a deliberately broken file produces a loud error naming the exact file and field, before any generation | ✓ VERIFIED | **Re-executed live this re-verification** on temp copies against the current loader/errors/schema: typo'd key → `Erro no perfil: ...profile.md` + `• certificacoes_typo — chave desconhecida — provável erro de digitação (chaves extras não são aceitas)`; broken YAML → loud error naming the exact file. Named tests green in the current suite: `test_malformed_yaml_is_loud_and_names_file`, `test_missing_file_names_path`, `test_non_utf8_bytes_loud_ptbr`, `test_typo_key_renders_ptbr_extra_forbidden`. Phase 3's `load_profile` consumers (facts.py, pipeline) all go through this same gate |
| T3 | SC3: Shipped example data covers experiences, projects, technologies, impacts; app visibly flags placeholder data | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Data half **re-proven live** on the current codebase: loaded file → exemplo=True, 3 experiences with 8 impacts, 2 projects, 4 skill groups, 0 localized maps missing pt-BR; `test_example_fully_bilingual` + `test_example_profile_validates` green. Banner wiring grep-proven on the current App.tsx (`{data.exemplo && <PlaceholderBanner />}`). Visual flagging → Human Verification 1 |
| T4 | SC4: Schema encodes the localization shape (parallel localized fields), demonstrated by bilingual example data | ✓ VERIFIED | `LocalizedText = dict[Literal["pt-BR","en"], str]` intact in the phase-3-modified models.py (diff is date-validation only); live walk of `model_dump()` found 0 localized maps missing pt-BR; shipped file still validates through the strengthened schema (quoted AAAA-MM dates pass the new `_DATE_RE` guard — full suite green) |
| T5 | SC5: OpenRouter API key lives only in a gitignored `.env` — nothing secret committed | ✓ VERIFIED | Re-executed this re-verification: `git check-ignore .env` exit 0; `git ls-files` shows only `.env.example`; `test_env_is_gitignored` + `test_env_is_not_tracked` green in the current suite. `.gitignore` gained `logs/` in phase 2 — `.env` entry untouched. config.py still reads the key tolerantly with empty default |
| T6 | GET /api/profile answers a fresh ok-envelope `{status, exemplo, perfil, completude}` per request; erro-envelope carries PT-BR lines (D-06/D-12/D-15) | ✓ VERIFIED | `routes/profile.py` unchanged since phase 1 (not in the phase-2/3 diff); all four envelope tests green in the current 183-test run (`test_get_profile_ok_envelope_includes_completude`, `test_get_profile_erro_envelope_names_exact_key`, `test_get_profile_erro_envelope_on_broken_yaml`, `test_erro_raw_detail_goes_to_terminal_log_only`) |
| T7 | Unknown keys rejected on EVERY model, nested included, each with its own test (D-10) | ✓ VERIFIED | `_Strict (extra="forbid")` intact in the current models.py; all 9 per-model forbid tests green in the current suite |
| T8 | Base language pt-BR required in every localized field; fallback policy encoded in the schema (D-03/D-04) | ✓ VERIFIED | **Re-executed live**: pt-BR → xx-BR swap in a temp copy → `• summary.xx-BR (chave) — valor fora das opções permitidas`; `_BaseLanguageMixin` + structural annotation equality unchanged; `test_base_language_required_on_{experience,impact,profile_summary}` green |
| T9 | PT-BR error lines render loc paths D-14-style from the five producible types; empty loc → "estrutura do perfil" (D-14) | ✓ VERIFIED | Re-executed live: `render_loc(("experiences",2,"data_fim")) == "experiences[2].data_fim"`, `render_loc(()) == "estrutura do perfil"`; observed rendered form `summary.xx-BR (chave)`; `test_render_loc_d14_paths`, `test_render_loc_language_key_marker`, `test_missing_base_language_renders_estrutura_do_perfil` green. Caveat carried from initial verification: WR-02 (Pydantic's English "Value error, " prefix leaks into one line's prose) — loc-path rendering, the truth's operative claim, holds; prose purity remains a tracked quality Warning. WR-03 (arbitrary date strings) was FIXED in phase 3: models.py now rejects non-AAAA-MM strings with a PT-BR message |
| T10 | Broken profile is a rendered UI state: PT-BR error lines in-app, verbatim from backend, UI never maps errors (D-13/D-14) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | ErrorPanel.tsx unchanged since phase 1 (verbatim `erros[]` text children, zero mapping); current App.tsx (nav-switch refactor) still renders `StatusLine ok={false}` + `<ErrorPanel erros={data.erros} />` on status erro. Backend half integration-tested green; DOM render → Human Verification 2 |
| T11 | Preview renders localized fields with the pt-BR base value (D-04) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | ProfilePreview.tsx unchanged since phase 1 (`t()` helper picks `map['pt-BR']` with defensive fallback); typechecked by today's green `npm run build`. Rendered output → Human Verification 4 |
| T12 | Editing content/profile.md + browser refresh shows current data — no restart (D-15) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | loader.py unchanged: per-call reads, no lru_cache/singleton; tests monkeypatch `loader.PROFILE_PATH` proving call-time resolution; end-to-end edit→refresh invariant → Human Verification 3 |

**Score:** 7/12 truths verified (5 present, behavior-unverified — all five are browser-visual or interactive invariants; the repo still has no frontend test runner, so no test can exercise them)

**Verdict change vs previous report: none.** All 7 previously VERIFIED truths re-verified against the current codebase; all 5 behavior-unverified truths remain behavior-unverified for the same reason (no automatable frontend test surface exists). No regressions from phases 2–3. Two evidence refreshes worth noting: T9's WR-03 caveat is now FIXED (phase 3 hardened dates), and T1's human-check steps changed (Currículo is now the default view).

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | LinkedIn nav item disabled | Phase 6 | Phase 6 goal: "LinkedIn Module + Bilingual Hardening"; D-12 designs the disabled placeholder; tracked in `.planning/WINDOWS.md` entry 1. (The Currículo half of the previous deferred item is RESOLVED — phase 3-04 enabled it.) |

### Required Artifacts

All 22 plan-01 + 10 plan-02 + 8 plan-03 artifact paths exist and are substantive on the CURRENT codebase (re-checked; the 13 files phase 2–3 touched were read, not assumed):

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `.gitignore` | ignores .env/node_modules/dist/.venv/__pycache__/outputs, committed first | ✓ VERIFIED | phase 2 appended `logs/`; `.env` entry intact; still predates all install artifacts |
| `backend/app/main.py` | /api routers first, guarded StaticFiles mount last | ✓ VERIFIED | read post-phase-3: profile_router + resume_router included before the `FRONTEND_DIST.exists()`-guarded mount; `test_get_serves_spa_index_html` green |
| `backend/app/profile/models.py` | full strict schema, `model_validator` | ✓ VERIFIED | phase-3 diff is additive date hardening (`_DATE_RE`, PT-BR failure message); `_Strict`, `_BaseLanguageMixin`, `_is_localized` unchanged |
| `backend/app/profile/errors.py` | `render_errors_ptbr` | ✓ VERIFIED | unchanged since phase 1; render_loc re-executed live |
| `backend/app/profile/loader.py` | fail-fast `load_profile`, `yaml.YAMLError` catch | ✓ VERIFIED | unchanged since phase 1; 4 catches, explicit UTF-8, no caching |
| `backend/app/profile/completeness.py` | `compute_completude` | ✓ VERIFIED | unchanged; `habilidades_itens_qtde` consumed by the WR-04 grid fix |
| `backend/app/routes/profile.py` | `/api/profile` status envelope | ✓ VERIFIED | unchanged; envelope tests green in current suite |
| `content/profile.md` | full bilingual persona, `experiences` | ✓ VERIFIED | unchanged since plan 02; validates live through the hardened schema (quoted dates pass) |
| `frontend/src/App.tsx` | PT-BR shell, three-state Perfil home | ✓ VERIFIED | read post-phase-3: PerfilHome keeps isPending/erro/ok three-state render; nav view switch added around it (phase 3-04); banner + grid + preview wired |
| `frontend/src/api/client.ts` | typed union incl. `completude` | ✓ VERIFIED | fetchProfile + profile union unchanged; resume types/functions appended by phase 3-04 |
| `frontend/src/components/ErrorPanel.tsx` | verbatim `erros` rendering | ✓ VERIFIED | unchanged |
| `frontend/src/components/CompletenessGrid.tsx` | `completude` at-a-glance grid | ✓ VERIFIED | WR-04 fix applied (shows groups AND items); still wired to real DTO |
| `frontend/src/components/ProfilePreview.tsx` | resume render, `pt-BR` selection | ✓ VERIFIED | unchanged; `t()` helper intact |
| `frontend/src/constants/ui.ts` | hardcoded PT-BR strings | ✓ VERIFIED | phase 3-04 appended resume strings; NAV_ITEMS now carries `enabled` flags; phase-1 strings intact |
| `.env` / `.env.example` / `README.md` / `backend/pyproject.toml` / `uv.lock` / `.python-version` / tests / `index.html` / `main.tsx` / `index.css` / `package.json` / `vite.config.ts` | scaffold + config + tests | ✓ VERIFIED | present; pyproject gained `openai` dep + `llm` marker (`addopts = -m 'not llm'` — offline default); frontend scripts unchanged (no test runner) |

### Key Link Verification

All 9 key links from the initial verification re-checked against the current code — none broken by phases 2–3.

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `frontend/src/api/client.ts` | `backend/app/routes/profile.py` | `fetch('/api/profile')` discriminated union | ✓ WIRED | fetchProfile unchanged; consumed via `useQuery({queryKey:['perfil'], queryFn: fetchProfile})` in the current App.tsx |
| `backend/app/profile/loader.py` | `content/profile.md` | `frontmatter.load(..., encoding="utf-8")` fresh per call | ✓ WIRED | loader unchanged; live-loaded the real file this re-verification |
| `backend/app/profile/loader.py` | `backend/app/profile/models.py` | `Profile.model_validate(post.metadata)` | ✓ WIRED | unchanged; hardened models still accept the shipped file |
| `backend/app/profile/errors.py` | `backend/app/profile/loader.py` | `render_errors_ptbr(exc, path)` | ✓ WIRED | unchanged; live-provoked ValidationError rendered PT-BR |
| `backend/app/routes/profile.py` | `backend/app/profile/completeness.py` | `compute_completude(profile)` in ok envelope | ✓ WIRED | unchanged; completude test green |
| `backend/app/main.py` | `frontend/dist` | `StaticFiles(html=True)` mount, registered last | ✓ WIRED | mount intact post-phase-3; dist fresh (build re-run); SPA test green |
| `frontend/src/App.tsx` | `frontend/src/api/client.ts` | useQuery → fetchProfile | ✓ WIRED | present in the refactored App.tsx |
| `frontend/src/components/ErrorPanel.tsx` | backend `erros[]` | verbatim list render | ✓ WIRED | `data.erros` passed from current App.tsx |
| `frontend/src/components/ProfilePreview.tsx` | validated `perfil` JSON | resume render | ✓ WIRED | `data.perfil` passed from current App.tsx |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| PerfilHome / ProfilePreview | `data.perfil` | `load_profile()` → frontmatter + Pydantic over `content/profile.md` | Yes (live-validated this re-verification: Ana Exemplo, 3 experiences) | ✓ FLOWING |
| CompletenessGrid | `data.completude` | `compute_completude(profile)` | Yes (real counts; WR-04 now shows both group and item counts) | ✓ FLOWING |
| ErrorPanel | `data.erros` | `render_errors_ptbr(ValidationError)` | Yes (live-provoked on temp copies this re-verification) | ✓ FLOWING |
| PlaceholderBanner | `data.exemplo` | frontmatter `example: true` → Pydantic bool | Yes | ✓ FLOWING |

No rendered value terminates in a static return or hardcoded literal; the only hardcoded strings are PT-BR UI labels (by design, constants module).

### Behavioral Spot-Checks

Full backend suite run ONCE this re-verification; live behavior re-executions done on temp copies (no state mutation of the repo; shipped file untouched).

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full backend suite on current codebase (run once) | `cd backend && uv run pytest -q` | 183 passed, 7 deselected (`llm` spend-marker tests correctly off by default) | ✓ PASS |
| Frontend gate on current codebase (run once) | `cd frontend && npm run build` | tsc + vite exit 0, fresh dist emitted | ✓ PASS |
| SC2: typo'd key → loud PT-BR error naming file+field | temp-copy `load_profile()` with `certificacoes_typo` | `Erro no perfil: ...profile.md` + `• certificacoes_typo — chave desconhecida...` | ✓ PASS |
| SC2/SC4: missing base language → field named | temp-copy with `xx-BR` in summary | `• summary.xx-BR (chave) — valor fora das opções permitidas` | ✓ PASS |
| SC2: broken YAML → loud, names file | temp-copy with `summary: [unclosed` | `Erro no perfil: ...p3.md — YAML do frontmatter inválido...` | ✓ PASS |
| SC3/SC4: healthy file validates, bilingual, all sections | `load_profile(content/profile.md)` + localized-map walk | exemplo=True; exp=3, impacts=8, projects=2, skills=4; 0 localized maps missing pt-BR | ✓ PASS |
| D-14 loc rendering units | `render_loc(("experiences",2,"data_fim"))`, `render_loc(())` | `experiences[2].data_fim` / `estrutura do perfil` | ✓ PASS |
| SC5: .env ignored/untracked | `git check-ignore .env`; `git ls-files` | exit 0; only `.env.example` tracked | ✓ PASS |
| Browser-visual rendering | — | needs a human at the running app | ? SKIP → Human Verification |

### Probe Execution

No probes declared in any phase-1 PLAN/SUMMARY and no `scripts/*/tests/probe-*.sh` exist in the current repo (re-checked). SKIPPED (nothing to run).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| PROFILE-01 | 01-01, 01-02, 01-03 (all declare it) | Master profile as Markdown/YAML in git, schema-validated, example data covering experiences/projects/technologies/impacts | ✓ SATISFIED | `content/profile.md` git-tracked and unchanged; strict-schema validation live-proven on the current code (T2/T7/T8); example data covers experiences (3, 8 impacts), projects (2), technologies (4 groups / 15 items); REQUIREMENTS.md maps PROFILE-01 → Phase 1 Complete |

No orphaned requirements: REQUIREMENTS.md maps only PROFILE-01 to Phase 1, and all three plans claim it. (Phases 2–3 later satisfied PROFILE-02/PROFILE-03 and RESUME-01..04 under their own plans — outside this verification's scope.)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| backend/app, frontend/src (current tree) | — | Debt markers (TBD/FIXME/XXX/HACK) | none found | — |
| backend/app, frontend/src (current tree) | — | Placeholder/"coming soon"/empty implementations | none found | — |
| frontend/src (all components incl. phase-3 additions) | — | dangerouslySetInnerHTML | none found (count 0 across 9 files) | — |
| backend/app | — | writes to content/ | none found (sole write is `llm/logging.py` → gitignored `logs/runs.jsonl`) | — |

### Phase 2–3 Regression Sweep (the reason for this re-verification)

| Shared file | Phase 2–3 change | Phase-1 must-have impact |
| ----------- | ---------------- | ------------------------ |
| `backend/app/main.py` | resume router added | None — both routers still precede the guarded SPA mount; SPA test green |
| `backend/app/config.py` | +PROMPTS_DIR/LOGS_DIR/LLM_MODEL/LLM_MAX_ATTEMPTS | None — tolerant `OPENROUTER_API_KEY` read unchanged at line 18 |
| `backend/app/profile/models.py` | date hardening (WR-03): non-AAAA-MM strings now fail with a PT-BR message | Strengthens SC2; shipped file (quoted dates) still validates; all forbid/base-language tests green |
| `backend/app/config.py` → `app/llm/gateway.py` | LLM calls now require the key at CALL time (phase 2 D-03) | None for phase-1 prohibition — startup and profile paths remain key-free (offline suite green proves it); prohibition wording is phase-1-scoped |
| `frontend/src/App.tsx` | nav view switch; Currículo default view; PerfilHome extracted | Perfil three-state render intact; only the human-smoke steps change (click Perfil) |
| `frontend/src/api/client.ts` | +resume endpoints/types | fetchProfile and profile union unchanged |
| `frontend/src/components/CompletenessGrid.tsx` | WR-04 fix | Improves truth T6's UI consumption; still real-DTO-driven |
| `frontend/src/constants/ui.ts` | +resume strings, NAV_ITEMS enabled flags | Phase-1 PT-BR strings intact |
| `.gitignore`, `pyproject.toml`, `uv.lock`, `tests/*` | +logs/, +openai, +llm marker, +grounding tests | None — `.env` ignore intact; offline default preserved; phase-1 tests unchanged and green |

### Human Verification Required

Six items (detailed in frontmatter `human_verification`): the SC1/SC3 browser smoke — now starting at the Currículo default view and clicking Perfil (steps scripted in README "Phase 1 smoke check"), the broken-profile UI round-trip, edit-refresh freshness, pt-BR preview rendering, confirmation of the 3 judgment-tier prohibition LLM-judge verdicts, and the package-legitimacy spot-check. Items 1–4 correspond one-to-one to the 5 behavior-unverified truths (the smoke covers two).

## Gaps Summary

No gaps. Phases 2–3 did not regress any phase-1 must-have: every previously machine-verified truth was re-proven against the current codebase (backend 183/183 non-llm tests green, frontend build green, and the loud-validation, base-language, bilingual-data, loc-rendering, and secrets behaviors re-executed live during this re-verification — not taken from SUMMARY claims). The five browser-visual/interactive truths remain PRESENT_BEHAVIOR_UNVERIFIED for the same reason as the initial verification: the repo still has no frontend test runner, so they route to the end-of-phase human checkpoint exactly as `human_verify_mode: end-of-phase` intended.

---

_Verified: 2026-09-26T23:39:05Z_
_Verifier: Claude (gsd-verifier)_
