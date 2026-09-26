---
phase: 01-foundation-scaffold-master-profile
verified: "2026-09-26T01:07:02Z"
status: human_needed
score: 7/12 must-haves verified
covered_files: [".env.example", ".gitignore", ".planning/REQUIREMENTS.md", ".planning/phases/01-foundation-scaffold-master-profile/01-01-PLAN.md", ".planning/phases/01-foundation-scaffold-master-profile/01-01-SUMMARY.md", ".planning/phases/01-foundation-scaffold-master-profile/01-02-PLAN.md", ".planning/phases/01-foundation-scaffold-master-profile/01-02-SUMMARY.md", ".planning/phases/01-foundation-scaffold-master-profile/01-03-PLAN.md", ".planning/phases/01-foundation-scaffold-master-profile/01-03-SUMMARY.md", "README.md", "backend/app/config.py", "backend/app/main.py", "backend/app/profile/completeness.py", "backend/app/profile/errors.py", "backend/app/profile/loader.py", "backend/app/profile/models.py", "backend/app/routes/profile.py", "backend/pyproject.toml", "backend/tests/conftest.py", "backend/tests/test_api.py", "backend/tests/test_loader.py", "backend/tests/test_schema.py", "backend/tests/test_secrets.py", "backend/uv.lock", "content/profile.md", "frontend/index.html", "frontend/package.json", "frontend/src/App.tsx", "frontend/src/api/client.ts", "frontend/src/components/CompletenessGrid.tsx", "frontend/src/components/ErrorPanel.tsx", "frontend/src/components/PlaceholderBanner.tsx", "frontend/src/components/ProfilePreview.tsx", "frontend/src/constants/ui.ts", "frontend/src/index.css", "frontend/src/main.tsx", "frontend/vite.config.ts"]
covered_digest: "v1:sha256:c6698cfe121dc069dc46efa6adddac41f89d89d8f48e0878db21ae5bb8f026b6"
behavior_unverified: 5
overrides_applied: 0
unverified-prohibition: "human review recommended — 3 judgment-tier prohibitions carry non-authoritative LLM-judge PASS verdicts (see Human Verification items 5a-5c); never silently passed"
mvp_user_story_guard: "FAILED — phase goal is not in 'As a..., I want..., so that...' format (user-story.validate returned false). Verification proceeded goal-backward on the 5 explicit roadmap SCs instead of a User Flow Coverage table. Orchestrator may run /gsd mvp-phase 1 to formalize."
deferred:
  - truth: "Nav items Currículo and LinkedIn render as enabled modules"
    addressed_in: "Phase 3 and Phase 6"
    evidence: "Phase 3 goal: 'Paste JD -> ... resume sections'; Phase 6 goal: 'LinkedIn Module + Bilingual Hardening'. Disabled nav placeholders are by-design (D-12), tracked open in .planning/WINDOWS.md entry 1."
behavior_unverified_items:
  - truth: "User starts the app locally and sees the PT-BR interface at localhost (SC1)"
    test: "npm run build, then uv run uvicorn app.main:app; open http://127.0.0.1:8000 (and/or the dev flow at http://127.0.0.1:5173)"
    expected: "PT-BR shell renders: 'Career Tailor' header, nav (Perfil enabled), 'Perfil carregado' status line, completeness grid, resume preview"
    why_human: "DOM rendering of the React shell is runtime behavior; the repo has no frontend test runner (scripts: dev/build/lint/preview only). HTTP-level serving IS test-proven (test_get_serves_spa_index_html); the visual render is not."
  - truth: "The app visibly flags that placeholder data is in use (SC3 visual half; data half is fully proven)"
    test: "With content/profile.md carrying example: true, load http://127.0.0.1:8000"
    expected: "Amber banner 'Dados de exemplo' with the explanatory subtitle is visible above the grid/preview"
    why_human: "Banner visibility is a browser-visual property; wiring is grep-proven (`{data.exemplo && <PlaceholderBanner />}` in App.tsx) but no test renders the DOM."
  - truth: "A broken profile is a rendered UI state: PT-BR error lines shown in-app, verbatim from the backend (plan-03 truth)"
    test: "Rename a key in content/profile.md (e.g. certifications -> certificacoes_typo), refresh the browser"
    expected: "ErrorPanel lists 'Erro no perfil: ...profile.md' plus the PT-BR line naming the exact key; app shell stays up; uvicorn terminal shows the raw extra_forbidden detail"
    why_human: "ErrorPanel rendering is DOM behavior; the backend erro-envelope half is integration-tested (test_get_profile_erro_envelope_names_exact_key passed), the in-app render is not."
  - truth: "The preview renders localized fields with the base-language pt-BR value (plan-03 truth, D-04)"
    test: "Load the home with the healthy shipped profile and inspect experience titles/summary/impact text"
    expected: "pt-BR values shown ('Engenheira de IA Sênior', 'São Paulo...'), never English or raw {'pt-BR': ...} maps"
    why_human: "The pt-BR selection helper (t() in ProfilePreview.tsx) is code-verified and typechecked, but the rendered output is only observable in a browser."
  - truth: "Editing content/profile.md and refreshing the browser shows current data — no restart, no stale cache (plan-03 truth, D-15)"
    test: "With the app running, change a value in content/profile.md, refresh the browser, observe; restore"
    expected: "Refresh shows the new value immediately (fresh load per request); no server restart needed"
    why_human: "Server-side freshness is code-verified (loader has no cache; tests monkeypatch PROFILE_PATH proving per-call reads) but the end-to-end edit->browser-refresh invariant is an interactive runtime behavior no test exercises."
human_verification:
  - test: "SC1/SC3 browser smoke (prod mode; steps scripted in README 'Phase 1 smoke check'): npm run build, cd backend && uv run uvicorn app.main:app, open http://127.0.0.1:8000. Optionally repeat via the dev flow (two terminals) at http://127.0.0.1:5173."
    expected: "PT-BR shell with header/nav, 'Perfil carregado' status, amber 'Dados de exemplo' banner, 7-section completeness grid, resume-style preview of Ana Exemplo (3 experiences, skills, projects)."
    why_human: "Visual layout, PT-BR text rendering, and banner prominence are human-observable only."
  - test: "Broken-profile UI state: rename a key in content/profile.md, refresh http://127.0.0.1:8000; check the uvicorn terminal; restore the file and refresh again."
    expected: "Red ErrorPanel names the exact file and key in PT-BR; app stays up (no crash/500 screen); terminal shows the raw technical detail; restore returns the healthy home without restart."
    why_human: "End-to-end error UX across file edit -> refresh -> panel -> recovery is interactive runtime behavior."
  - test: "Edit-refresh freshness (D-15): change a visible value in content/profile.md while the server runs, refresh, then restore."
    expected: "New value appears after browser refresh with no server restart."
    why_human: "Interactive freshness invariant; presence checks cannot observe cache-vs-fresh behavior."
  - test: "Preview base-language check (D-04): confirm every localized field in the preview shows the pt-BR value."
    expected: "No English-only rendering of localized fields, no raw language-map JSON in the page."
    why_human: "Visual confirmation of which map value renders."
  - test: "Flagged prohibition review (3 judgment-tier prohibitions carried with status unverified in PLAN frontmatter): (a) plan-01 — app starts with empty/missing OPENROUTER_API_KEY and never requires/calls it; (b) plan-02 — backend never writes to content/; (c) plan-03 — UI offers no control over the example flag. Confirm or reject the LLM-judge PASS verdicts."
    expected: "Confirmations match the code evidence: (a) config.py reads tolerantly with empty default and no other reference exists; (b) zero write/open calls in backend/app; (c) PlaceholderBanner and App.tsx contain no onClick/button/dismiss and the client only GETs."
    why_human: "Prohibitions are must-NOT statements whose full assurance requires human review per the judgment-tier soft gate; LLM-judge verdicts are non-authoritative."
  - test: "Package legitimacy spot-check (plan-01 T-01-SC end-of-phase human-check): spot-check npmjs.com/pypi.org for the pinned versions against the 01-RESEARCH.md Package Legitimacy Audit (react 19.3.0, vite 8.3.1, @tanstack/react-query 5.103.2, tailwindcss 4.3.3, fastapi 0.141.1, uvicorn 0.54.0, pydantic 2.13.5, python-frontmatter 1.3.0, python-dotenv 1.2.3, pytest 9.1.1, httpx 0.28.1)."
    expected: "Maintainers/repos match the audit's Source Repo column; no package gained install scripts."
    why_human: "Supply-chain legitimacy requires human inspection of external registries (T-01-SC)."
---

# Phase 1: Foundation — Scaffold + Master Profile Verification Report

**Phase Goal:** The app runs locally with a PT-BR interface, and the master profile is a git-versioned, schema-validated source of truth ready to feed both generation modules.
**Verified:** 2026-09-26T01:07:02Z
**Status:** human_needed
**Re-verification:** No — initial verification

**MVP-mode note:** the phase has `mode: mvp` but its goal is not in User Story format (`user-story.validate` → false). The User Flow Coverage table was skipped per the format guard; verification proceeded goal-backward on the 5 explicit roadmap success criteria, which are themselves user-flow shaped ("User starts the app...", "User sees..."). Surface to the user: consider `/gsd mvp-phase 1` if the User Story framing is wanted for UAT.

## Goal Achievement

### Observable Truths

Roadmap SCs merged with PLAN must_haves truths (plan truths that merely restate an SC keep the SC wording; plan-specific detail is added as T6–T12).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| T1 | SC1: User starts the app locally and sees the PT-BR interface at localhost (FastAPI-served after build, or dev servers) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Serving half proven: `test_get_serves_spa_index_html` passed (35-test suite), `frontend/dist` exists (build re-run green this verification), `main.py` mounts StaticFiles guarded + last. Dev-proxy loop live-verified by executor (plan-01 Task 3, curl evidence). Browser-visual render → Human Verification 1 |
| T2 | SC2: Master profile loads + validates; a deliberately broken file produces a loud error naming the exact file and field, before any generation | ✓ VERIFIED | **Re-executed live this verification** on temp copies: typo'd key → `Erro no perfil: ...profile.md` + `• certificacoes_typo — chave desconhecida — provável erro de digitação (chaves extras não são aceitas)`; broken YAML → loud error naming the exact file. Named tests in the passing 35: `test_malformed_yaml_is_loud_and_names_file`, `test_missing_file_names_path`, `test_non_utf8_bytes_loud_ptbr`, `test_typo_key_renders_ptbr_extra_forbidden`. No generation code exists in Phase 1; `load_profile()` is the sole gate every future consumer inherits |
| T3 | SC3: Shipped example data covers experiences, projects, technologies, impacts; app visibly flags placeholder data | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Data half **proven live**: loaded file → exemplo=True, 3 experiences with 8 impacts, 2 projects with technologies, 4 skill groups, education/certs/languages populated; `test_example_fully_bilingual` + `test_example_profile_validates` pass. Banner wiring grep-proven (`{data.exemplo && <PlaceholderBanner />}`). Visual flagging → Human Verification 1 |
| T4 | SC4: Schema encodes the localization shape (parallel localized fields), demonstrated by bilingual example data | ✓ VERIFIED | `LocalizedText = dict[Literal["pt-BR","en"], str]` on every narrative field; shipped file has 36 `pt-BR` keys, every localized map carries both languages (live walk of `model_dump()` + passing test). No per-language files exist — the map encoding is the single shape |
| T5 | SC5: OpenRouter API key lives only in a gitignored `.env` — nothing secret committed | ✓ VERIFIED | Re-executed: `git check-ignore .env` exit 0; `git ls-files` shows only `.env.example`; `.env` on disk with empty value; `test_env_is_gitignored` + `test_env_is_not_tracked` pass; `.gitignore` commit `94c4821` predates all install artifacts (`ef506ef`); `OPENROUTER_API_KEY` referenced only in `config.py` (tolerant get, default "") |
| T6 | GET /api/profile answers a fresh ok-envelope `{status, exemplo, perfil, completude}` per request; erro-envelope carries PT-BR lines (D-06/D-12/D-15) | ✓ VERIFIED | Route code read (no cache; completude computed fresh); passing tests: `test_get_profile_ok_envelope_includes_completude`, `test_get_profile_erro_envelope_names_exact_key`, `test_get_profile_erro_envelope_on_broken_yaml`, `test_erro_raw_detail_goes_to_terminal_log_only` |
| T7 | Unknown keys rejected on EVERY model, nested included, each with its own test (D-10) | ✓ VERIFIED | All 9 models inherit `_Strict (extra="forbid")` (models.py read); 9 named forbid tests collected and passing (profile, experience, impact, contact, education_entry, skill_group, certification_entry, language_entry, project) |
| T8 | Base language pt-BR required in every localized field; fallback policy encoded in the schema (D-03/D-04) | ✓ VERIFIED | `_BaseLanguageMixin` model_validator read (structural annotation equality); **re-executed live**: missing pt-BR → `• summary.xx-BR (chave) — valor fora das opções permitidas`; `test_base_language_required_on_{experience,impact,profile_summary}` pass |
| T9 | PT-BR error lines render loc paths D-14-style from the five producible types; empty loc → "estrutura do perfil" (D-14) | ✓ VERIFIED | Live: loc paths render `experiences[2].data_fim`-style (`summary.xx-BR (chave)` observed); `test_render_loc_d14_paths`, `test_render_loc_language_key_marker`, `test_missing_base_language_renders_estrutura_do_perfil` pass. Caveat: review WR-02 found Pydantic's English "Value error, " prefix leaks into the value_error line's prose (see Review Cross-Check) — the truth's operative claim (loc-path rendering) holds; prose purity is a tracked Warning, not an SC failure |
| T10 | Broken profile is a rendered UI state: PT-BR error lines in-app, verbatim from backend, UI never maps errors (D-13/D-14) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | ErrorPanel.tsx read: renders `erros[]` as text children, zero mapping logic; App.tsx three-state render wired (isPending / erro / ok). Backend half integration-tested; DOM render → Human Verification 2 |
| T11 | Preview renders localized fields with the pt-BR base value (D-04) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `t()` helper in ProfilePreview.tsx picks `map['pt-BR']` with defensive fallback; typechecked by `npm run build` (green, re-run). Rendered output → Human Verification 4 |
| T12 | Editing content/profile.md + browser refresh shows current data — no restart (D-15) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Loader re-reads per call (no lru_cache/singleton — code read); tests monkeypatch `loader.PROFILE_PATH` proving call-time path resolution; end-to-end edit→refresh invariant → Human Verification 3 |

**Score:** 7/12 truths verified (5 present, behavior-unverified — all five are browser-visual or interactive invariants; the repo has no frontend test runner, so no test can exercise them)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Nav items Currículo/LinkedIn disabled | Phase 3 / Phase 6 | Roadmap goals for those phases deliver the modules; D-12 designs the disabled placeholders; tracked in `.planning/WINDOWS.md` entry 1 |

### Required Artifacts

All 22 plan-01 + 10 plan-02 + 8 plan-03 artifact paths exist and are substantive (no stubs, no placeholders in the deliverable sense):

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `.gitignore` | ignores .env/node_modules/dist/.venv/__pycache__/outputs, committed first | ✓ VERIFIED | commit 94c4821 predates ef506ef (all install artifacts) |
| `backend/app/main.py` | /api router first, guarded StaticFiles mount last | ✓ VERIFIED | read; mount guarded on `FRONTEND_DIST.exists()` |
| `backend/app/profile/models.py` | full strict schema, `model_validator` | ✓ VERIFIED | 9 models + `_Strict` + `_BaseLanguageMixin`; 152 lines |
| `backend/app/profile/errors.py` | `render_errors_ptbr` | ✓ VERIFIED | five-type map, `render_loc`, D-14 paths |
| `backend/app/profile/loader.py` | fail-fast `load_profile`, `yaml.YAMLError` catch | ✓ VERIFIED | 4 catches, explicit UTF-8, no caching |
| `backend/app/profile/completeness.py` | `compute_completude` | ✓ VERIFIED | 15-key PT-BR presence/count map |
| `backend/app/routes/profile.py` | `/api/profile` status envelope | ✓ VERIFIED | ok/erro envelope, raw → logger only |
| `content/profile.md` | full bilingual persona, `experiences` | ✓ VERIFIED | all D-07 sections; 36 pt-BR keys; exemplo: true |
| `frontend/src/App.tsx` | PT-BR shell, three-state Perfil home | ✓ VERIFIED | isPending/erro/ok; banner + grid + preview wired |
| `frontend/src/api/client.ts` | typed union incl. `completude` | ✓ VERIFIED | PerfilDTO/CompletudeDTO mirror the Pydantic dump |
| `frontend/src/components/ErrorPanel.tsx` | verbatim `erros` rendering | ✓ VERIFIED | text children only, no mapping logic |
| `frontend/src/components/CompletenessGrid.tsx` | `completude` at-a-glance grid | ✓ VERIFIED | 7 sections, present/neutral states (WR-04 labeling caveat below) |
| `frontend/src/components/ProfilePreview.tsx` | resume render, `pt-BR` selection | ✓ VERIFIED | `t()` helper; text children only; no dangerouslySetInnerHTML |
| `frontend/src/constants/ui.ts` | hardcoded PT-BR strings | ✓ VERIFIED | all UI strings incl. `Perfil`, banner copy, error hint |
| `frontend/vite.config.ts` | `127.0.0.1:8000` proxy, host pinned | ✓ VERIFIED | host + target both 127.0.0.1 |
| `.env` / `.env.example` / `README.md` / `backend/pyproject.toml` / `uv.lock` / `.python-version` / tests / `index.html` / `main.tsx` / `index.css` / `package.json` | scaffold + config + tests | ✓ VERIFIED | present; Python 3.12 pin; pytest config; 35 tests |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `frontend/src/api/client.ts` | `backend/app/routes/profile.py` | `fetch('/api/profile')` discriminated union | ✓ WIRED | `fetchProfile()` typed to the envelope; consumed via `useQuery({queryKey:['perfil'], queryFn: fetchProfile})` in App.tsx |
| `backend/app/profile/loader.py` | `content/profile.md` | `frontmatter.load(..., encoding="utf-8")` fresh per call | ✓ WIRED | PROFILE_PATH = CONTENT_DIR / "profile.md"; call-time default |
| `backend/app/profile/loader.py` | `backend/app/profile/models.py` | `Profile.model_validate(post.metadata)` | ✓ WIRED | ValidationError funneled to ProfileError via mapper |
| `backend/app/profile/errors.py` | `backend/app/profile/loader.py` | `render_errors_ptbr(exc, path)` | ✓ WIRED | imported and called in the ValidationError branch |
| `backend/app/routes/profile.py` | `backend/app/profile/completeness.py` | `compute_completude(profile)` in ok envelope | ✓ WIRED | computed fresh per request |
| `backend/app/main.py` | `frontend/dist` | `StaticFiles(html=True)` mount, registered last | ✓ WIRED | dist exists (build re-run); `test_get_serves_spa_index_html` passes |
| `frontend/src/App.tsx` | `frontend/src/api/client.ts` | useQuery → fetchProfile | ✓ WIRED | three-state render |
| `frontend/src/components/ErrorPanel.tsx` | backend `erros[]` | verbatim list render | ✓ WIRED | `data.erros` passed from App.tsx |
| `frontend/src/components/ProfilePreview.tsx` | validated `perfil` JSON | resume render | ✓ WIRED | `data.perfil` passed from App.tsx |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| PerfilHome / ProfilePreview | `data.perfil` | `load_profile()` → frontmatter + Pydantic over `content/profile.md` | Yes (live-validated: Ana Exemplo, 3 experiences) | ✓ FLOWING |
| CompletenessGrid | `data.completude` | `compute_completude(profile)` | Yes (15 keys, real counts) | ✓ FLOWING |
| ErrorPanel | `data.erros` | `render_errors_ptbr(ValidationError)` | Yes (live-provoked on temp copies) | ✓ FLOWING |
| PlaceholderBanner | `data.exemplo` | frontmatter `example: true` → Pydantic bool | Yes | ✓ FLOWING |

No rendered value terminates in a static return or hardcoded literal; the only hardcoded strings are PT-BR UI labels (by design, constants module).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| SC2: typo'd key → loud PT-BR error naming file+field | temp-copy `load_profile()` with `certificacoes_typo` | `Erro no perfil: ...profile.md` + `• certificacoes_typo — chave desconhecida...`; raw kept out of message | ✓ PASS |
| SC2/SC4: missing base language → field named | temp-copy with `xx-BR` key | `• summary.xx-BR (chave) — valor fora das opções permitidas` | ✓ PASS |
| SC2: broken YAML → loud, names file | temp-copy with `summary: [unclosed` | `Erro no perfil: ...p3.md — YAML do frontmatter inválido...` | ✓ PASS |
| SC3/SC4: healthy file validates, bilingual, all sections | `load_profile(content/profile.md)` + localized-map walk | exemplo=True; exp=3, edu=1, skills=4, certs=1, lang=2, proj=2; every localized map has pt-BR | ✓ PASS |
| Full backend suite (run once) | `uv run pytest -q` | 35 passed, 1 upstream warning | ✓ PASS |
| Frontend gate (run once) | `npm run build` | tsc + vite exit 0 | ✓ PASS |
| SC5: .env ignored/untracked | `git check-ignore .env`; `git ls-files` | exit 0; only `.env.example` tracked | ✓ PASS |
| Browser-visual rendering | — | needs a human at the running app | ? SKIP → Human Verification |

### Probe Execution

No probes declared in any PLAN/SUMMARY and no `scripts/*/tests/probe-*.sh` exist. SKIPPED (nothing to run). The plan-02 "specless probe fallback" reference is a planning-time artifact; its unresolved concurrency edge is properly **surfaced** in plan-02 frontmatter `flagged_assumptions` (with the read-only-freshness rationale) — not silently passed. Verified.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| PROFILE-01 | 01-01, 01-02, 01-03 (all declare it) | Master profile as Markdown/YAML in git, schema-validated, example data covering experiences/projects/technologies/impacts | ✓ SATISFIED | `content/profile.md` git-tracked; strict-schema validation live-proven (T2/T7/T8); example data covers experiences (3, 8 impacts), projects (2, technologies), technologies (4 groups / 15 items); REQUIREMENTS.md maps PROFILE-01 → Phase 1 Complete |

No orphaned requirements: REQUIREMENTS.md maps only PROFILE-01 to Phase 1, and all three plans claim it. `requirements-completed: [PROFILE-01]` declared by plan 03 (the shared-ID gate deferred the mark until 01-03 closed, as documented).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| backend/app, frontend/src | — | Debt markers (TBD/FIXME/XXX/HACK) | none found | — |
| backend/app, frontend/src | — | Empty implementations / console-only handlers | none found | — |
| frontend/src/components/* | — | dangerouslySetInnerHTML | none found (grep count 0) | — |

### Phase Review Findings Cross-Check (01-REVIEW.md: 4 Warning, 5 Info, 0 Critical)

Checked each finding against the must-haves — none overturns a roadmap SC or fails a truth as worded; all are tracked in the phase review with `status: issues_found`:

- **WR-01/WR-02** (English Pydantic prose leaks into some error lines, incl. the "Value error, " prefix on the value_error type): T9's operative claim — D-14 loc-path rendering, loud file+field naming — was re-proven live and holds; SC2 holds. Prose purity is a quality defect for a follow-up fix. Related IN-03 (OS-level errors → 500) narrows the "never 500" contract to broken-profile inputs, which is what the truths claim.
- **WR-03** (date fields accept arbitrary strings): the truths require loud *schema* errors, not date-format lint; unquoted-date coercion (Pitfall 1) is tested and passing. Quality follow-up.
- **WR-04** (grid shows group count where item count is expected): the grid is wired to the real completude DTO (T6 holds); it is a labeling bug, Warning severity.
- **IN-04/IN-05** etc.: operational notes; no truth contradicted.

## Human Verification Required

Six items (detailed in frontmatter `human_verification`): the SC1/SC3 browser smoke at 127.0.0.1:8000 (steps scripted in README "Phase 1 smoke check"), the broken-profile UI round-trip, edit-refresh freshness, pt-BR preview rendering, confirmation of the 3 judgment-tier prohibition LLM-judge verdicts, and the package-legitimacy spot-check. Items 1–4 correspond one-to-one to the 5 behavior-unverified truths (the smoke covers two).

## Gaps Summary

No gaps. Every roadmap success criterion is either machine-verified (SC2, SC4, SC5 fully; SC1/SC3 at the HTTP and data layers) or routed to the end-of-phase human checkpoint exactly as the plans' `human_verify_mode: end-of-phase` intended — the executor's own coverage entries D7/D10 routed the browser-visual smoke to the human, and this verification independently confirms those items cannot be machine-checked (no frontend test runner exists). Backend behavior is fully proven: 35/35 tests pass, and the loud-validation, base-language, and bilingual-data behaviors were re-executed live during this verification, not taken from SUMMARY claims.

---
_Verified: 2026-09-26T01:07:02Z_
_Verifier: Claude (gsd-verifier)_
