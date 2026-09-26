---
phase: 01-foundation-scaffold-master-profile
plan: 02
subsystem: backend/profile
tags: [pydantic, strict-schema, validation, pt-br, i18n, yaml-frontmatter, fastapi, fail-fast, tdd]

# Dependency graph
requires:
  - phase: 01-foundation-scaffold-master-profile
    provides: plan-01 tracer slice (uv backend, _Strict/LocalizedText/Experience/Impact/Profile skeleton, interim loader, GET /api/profile envelope)
provides:
  - Full v1 strict profile schema — every D-07 section model with extra=forbid and base-language enforcement (_BaseLanguageMixin)
  - PT-BR error localization (errors.py): _PTBR_BY_TYPE over the five producible types, render_loc D-14 paths, render_errors_ptbr
  - Finalized fail-fast load_profile() — all four failure modes loud, raw detail terminal-only, no caching (D-15)
  - compute_completude section presence/counts (D-12; NOT the PROFILE-02 lint) wired into the ok envelope
  - content/profile.md fully bilingual D-16 example persona (example: true), validating through the strict schema
  - Test suite covering the research test map (schema forbid per model, loader failure modes, bilingual proof, API envelopes)
affects: [01-03 Perfil UI (consumes completude + PT-BR error lines + perfil preview data), phase 2 LLM gateway (Profile contract and load_profile call sites)]

# Actuals (#2632)
actuals:
  tokens: 11800        # chars/4 over the realized diff (47,183 bytes, 10 files, +954/-29)
  tasks: 3
  commits: 5           # MEASURED: git rev-list --count 83968b4..HEAD
plan_head_before: 83968b409e40f337a3363f093434ee2c3ab3c074

# Tech tracking
tech-stack:
  added: []
  patterns: [strict-schema-with-shared-_Strict-base, base-language model_validator mixin, structural-annotation-equality (Pydantic alias gotcha), five-type PT-BR error map with D-14 loc rendering, call-time default path for testable loader, PT-BR completude map in status envelope]

key-files:
  created:
    - backend/app/profile/errors.py
    - backend/app/profile/completeness.py
    - backend/tests/conftest.py
    - backend/tests/test_schema.py
    - backend/tests/test_loader.py
  modified:
    - backend/app/profile/models.py
    - backend/app/profile/loader.py
    - backend/app/routes/profile.py
    - backend/tests/test_api.py
    - content/profile.md

key-decisions:
  - "_is_localized compares annotations structurally (==): Pydantic FieldInfo returns equal-but-not-identical generic alias objects, so an identity check silently skipped every required localized field — caught immediately by the RED base-language test (assumption A4's designed catch)"
  - "load_profile default path resolves at call time (path: Path | None = None) — tests retarget loader.PROFILE_PATH without mutating the real content/ file; production behavior unchanged (D-15 fresh load)"
  - "_BaseLanguageMixin applied to ALL profile models (no-op where no localized fields) — uniform inheritance keeps future localized fields covered; empty-loc value_error is the verified Pitfall 8 shape"
  - "compute_completude uses PT-BR keys with presence bools + *_qtde counts (habilidades carries group and item counts); explicitly NOT the PROFILE-02 JD-tied completeness lint (Phase 3)"

requirements-completed: []   # PROFILE-01 shared with 01-03 — deferred by the shared-ID gate until 01-03 finishes

coverage:
  - id: full-v1-strict-schema
    description: "Full D-07 strict schema: every model extra=forbid with a per-model test, base language enforced on every localized field, dates coerced, example flag round-trips"
    requirement: PROFILE-01
    verification:
      - kind: unit
        ref: "backend/tests/test_schema.py#test_unknown_key_rejected_on_{profile,experience,impact,contact,education_entry,skill_group,certification_entry,language_entry,project}"
        status: pass
      - kind: unit
        ref: "backend/tests/test_schema.py#test_base_language_required_on_{experience,impact,profile_summary}"
        status: pass
      - kind: unit
        ref: "backend/tests/test_schema.py#test_unknown_language_key_is_literal_error + test_date_coercion_accepts_unquoted_yaml_dates + test_example_flag_round_trips"
        status: pass
    human_judgment: false
  - id: ptbr-error-localization
    description: "The five producible error types map to PT-BR phrases; loc tuples render D-14-style (experiences[2].data_fim; '(chave)'; 'estrutura do perfil' for empty loc)"
    requirement: PROFILE-01
    verification:
      - kind: unit
        ref: "backend/tests/test_loader.py#test_render_loc_d14_paths + test_render_loc_language_key_marker"
        status: pass
      - kind: other
        ref: "command: python -c \"assert render_loc(('experiences',2,'data_fim'))=='experiences[2].data_fim' and render_loc(())=='estrutura do perfil'\""
        status: pass
    human_judgment: false
  - id: fail-fast-loader
    description: "Every load failure is a loud ProfileError naming the exact file: broken YAML, missing file, non-UTF-8, ValidationError; raw channel preserved for the terminal"
    requirement: PROFILE-01
    verification:
      - kind: unit
        ref: "backend/tests/test_loader.py#test_malformed_yaml_is_loud_and_names_file + test_missing_file_names_path + test_non_utf8_bytes_loud_ptbr + test_raw_keeps_full_error_detail"
        status: pass
    human_judgment: false
  - id: bilingual-example-persona
    description: "Shipped content/profile.md is the D-16 example persona and every localized field carries both pt-BR and en (SC4/D-17); validates clean through the strict schema (SC3 data half)"
    requirement: PROFILE-01
    verification:
      - kind: unit
        ref: "backend/tests/test_loader.py#test_example_profile_validates + backend/tests/test_schema.py#test_example_fully_bilingual"
        status: pass
      - kind: other
        ref: "command: grep -c 'pt-BR' content/profile.md -> 36"
        status: pass
    human_judgment: false
  - id: completude-envelope
    description: "GET /api/profile ok-envelope carries completude presence/counts; erro-envelope carries PT-BR lines naming the exact key; never HTTP 500"
    requirement: PROFILE-01
    verification:
      - kind: integration
        ref: "backend/tests/test_api.py#test_get_profile_ok_envelope_includes_completude + test_get_profile_erro_envelope_names_exact_key + test_get_profile_erro_envelope_on_broken_yaml + test_erro_raw_detail_goes_to_terminal_log_only"
        status: pass
    human_judgment: false
  - id: sc2-loud-validation-demo
    description: "Live SC2 demo against a real uvicorn server: typo'd key introduced in the shipped file, curl /api/profile returned the erro envelope ('experiance — chave desconhecida — provável erro de digitação'), uvicorn log carried the raw extra_forbidden detail, file restored byte-identical (diff-verified)"
    requirement: PROFILE-01
    verification:
      - kind: other
        ref: "command: uvicorn 127.0.0.1:8017 + curl /api/profile with broken content/profile.md (2026-09-26, recorded in Accomplishments)"
        status: pass
    human_judgment: false

# Metrics
duration: 19 min
completed: 2026-09-26
status: complete
---

# Phase 1 Plan 02: Profile Contract — Full Schema, PT-BR Error Mapper, Bilingual Persona Summary

**Full v1 strict Pydantic schema with base-language enforcement, a fail-fast loader whose failures render as PT-BR D-14 lines naming the exact file and field, and the fully bilingual example persona flowing through GET /api/profile's completude envelope — SC2 and SC4 proven.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-09-26T00:12:55Z
- **Completed:** 2026-09-26T00:32:00Z
- **Tasks:** 3 (Tasks 1–2 TDD: RED → GREEN; Task 3 standard)
- **Files:** 10 changed (5 created, 5 modified; +954/−29)

## Accomplishments

- **Full v1 strict schema** (models.py): Contact, Impact, Experience, EducationEntry, SkillGroup, CertificationEntry, LanguageEntry, Project, Profile — every model inheriting `_Strict (extra="forbid")` with one shared ConfigDict; localized maps (`dict[Literal["pt-BR","en"], str]`) on summary, titles, descriptions, and impacts; date coercion (Pitfall 1) on Experience and EducationEntry; `example: bool = False` declared (D-11)
- **Base-language enforcement** (D-03/D-04): `_BaseLanguageMixin` model_validator fires on every localized field (including Optional), raising a ValueError naming the field; surfaces as `value_error` with the model-level loc shape (empty direct, nested-model prefix through Profile — Pitfall 8)
- **PT-BR error localization** (errors.py, D-14): `_PTBR_BY_TYPE` over the exactly five producible types, `render_loc` (`experiences[2].data_fim`, `" (chave)"` for language-key errors, `"estrutura do perfil"` for empty loc), `render_errors_ptbr` (`"Erro no perfil: {path}"` + bullet lines); raw pydantic detail confined to `ProfileError.raw` → terminal (D-13, T-01-07)
- **Finalized fail-fast loader** (loader.py): four catches (FileNotFoundError / yaml.YAMLError / UnicodeDecodeError / ValidationError), explicit `encoding="utf-8"` (Pitfall 7), zero caching (D-15); ValidationError branch routes through the mapper
- **compute_completude** (completeness.py): PT-BR presence/counts map (resumo, experiencias + impactos, educação, habilidades groups + itens, certificações, idiomas, projetos) wired into the ok envelope fresh per request
- **Full bilingual example persona** (content/profile.md, D-16/D-17): senior AI engineer with generative-AI focus plus backend, frontend, and light infra — 3 experiences with 8 embedded impacts, 4 skill groups (15 techs), 2 projects, education/certifications/languages populated; every localized field carries both pt-BR and en (36 pt-BR occurrences); dates quoted
- **SC2 proven live**: with a typo'd key injected into the shipped file, a real uvicorn server answered `{"status":"erro","erros":["Erro no perfil: …\\content\\profile.md","  • experiance — chave desconhecida — provável erro de digitação (chaves extras não são aceitas)"]}` while the uvicorn log carried the raw `extra_forbidden` detail; the file was restored byte-identical (diff-verified). No 500, no silent skip.
- **Test suite**: 4 → 35 passing tests covering the research test map (per-model forbid, base-language, literal_error, date coercion, loader failure modes, D-14 rendering, bilingual proof, API ok/erro envelopes, raw-detail channeling)

## Task Commits

Each task was committed atomically (Tasks 1–2 follow RED → GREEN):

1. **Task 1 (RED): base-language RED tests + schema fixtures** — `17bec72` (test)
2. **Task 1 (GREEN): full strict schema** — `0d616dc` (feat)
3. **Task 2 (RED): loader PT-BR rendering tests** — `d6cdbfc` (test)
4. **Task 2 (GREEN): errors.py + finalized loader** — `86c4cff` (feat)
5. **Task 3: bilingual persona + completude + envelope tests** — `a78326d` (feat)

**TDD gate compliance:** both TDD tasks have `test(01-02)` RED commits preceding their `feat(01-02)` GREEN commits; RED failures were intentional (DID NOT RAISE / missing PT-BR phrase), never import or collection errors.

## Files Created/Modified
- `backend/app/profile/models.py` — full v1 schema: 9 models, `_BaseLanguageMixin`, structural annotation equality
- `backend/app/profile/errors.py` — `_PTBR_BY_TYPE`, `render_loc`, `render_errors_ptbr`
- `backend/app/profile/completeness.py` — `compute_completude` (presence/counts, not the PROFILE-02 lint)
- `backend/app/profile/loader.py` — finalized four-catch loader routed through the mapper; call-time default path
- `backend/app/routes/profile.py` — ok-envelope gains `completude`
- `backend/tests/conftest.py` — minimal/full profile dicts + tmp_path file variants (typo'd top-level, nested typo, missing pt-BR, broken YAML, non-UTF-8) + shipped-file fixture
- `backend/tests/test_schema.py` — 9 forbid tests + base-language + literal_error + date coercion + example flag + bilingual proof (17 tests)
- `backend/tests/test_loader.py` — failure modes, PT-BR rendering, render_loc units, shipped-file validation (11 tests)
- `backend/tests/test_api.py` — completude ok-envelope, erro-envelope key-naming, raw-detail-terminal-only (7 tests)
- `content/profile.md` — full bilingual D-16 example persona replacing the tracer-minimal slice

## Decisions Made
- `_is_localized` compares annotations **structurally** (`==`): Pydantic's FieldInfo returns equal-but-not-identical generic alias objects — the identity check silently skipped every required localized field. The RED base-language test caught it on the first GREEN run (assumption A4's designed catch worked exactly as planned).
- `load_profile` default path resolves at **call time** (`path: Path | None = None`) so API tests retarget `loader.PROFILE_PATH` via monkeypatch without touching the real `content/` file; production behavior identical (D-15 fresh load per request).
- Base-language mixin is inherited by **all** profile models (no-op where no localized fields exist) — uniform coverage for future fields.
- Model-level (mixin) error loc shapes documented in tests: empty loc when the model is validated directly; the nested-model path prefix (`('experiences', 0)`) when raised through Profile — the renderer treats both correctly ("estrutura do perfil" via render_loc of the FULL Profile-level error, which is empty at Profile level).
- `compute_completude` keys are PT-BR (`resumo`, `habilidades_qtde`, …) matching the PT-BR UI; explicitly NOT the PROFILE-02 JD-tied completeness lint (Phase 3).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Identity check in `_is_localized` silently disabled base-language enforcement**
- **Found during:** Task 1 (GREEN run)
- **Issue:** `field.annotation is LocalizedText` was False for required localized fields — Pydantic stores an equal-but-not-identical generic alias object; the mixin loop found zero localized fields and never raised
- **Fix:** Structural comparison (`annotation == LocalizedText or LocalizedText in get_args(annotation)`); the RED test caught it immediately (A4's designed catch)
- **Files modified:** backend/app/profile/models.py
- **Verification:** test_base_language_required_* green; 15 schema tests pass
- **Committed in:** 0d616dc

**2. [Rule 1 - Bug] Two Task-1/2 tests asserted the wrong verified shapes**
- **Found during:** Task 1 (GREEN run) and Task 2 planning
- **Issue:** (a) LanguageEntry forbid test took `errors()[0]`, which was the `missing` error (level absent) rather than `extra_forbidden`; (b) the base-language test asserted empty loc for an error raised through Profile, but nested model-level errors carry the `('experiences', 0)` path prefix
- **Fix:** Filter for `extra_forbidden` specifically; assert the verified nested loc prefix (direct-validation empty loc is asserted in the Impact test)
- **Files modified:** backend/tests/test_schema.py
- **Verification:** full schema suite green
- **Committed in:** 0d616dc

**3. [Rule 2 - Missing critical] Loader default path was def-time bound, making API erro-envelope tests require mutating the real content/ file**
- **Found during:** Task 2 (GREEN)
- **Issue:** `path: Path = PROFILE_PATH` binds at def time; tests could not retarget the loader without rewriting the shipped file (fragile try/finally swaps)
- **Fix:** `path: Path | None = None` resolved at call time; tests monkeypatch `loader.PROFILE_PATH`
- **Files modified:** backend/app/profile/loader.py
- **Verification:** test_get_profile_erro_envelope_* + test_erro_raw_detail_goes_to_terminal_log_only green; production call sites unchanged
- **Committed in:** 86c4cff

---
**Total deviations:** 3 auto-fixed (2 bugs, 1 missing-critical). **Impact:** all fixes caught by the plan's own RED tests or required by the planned test map; no scope creep. Routes/profile.py stayed as plan-01 built it (envelope + raw-to-terminal), as the plan anticipated.

## Issues Encountered
- Starlette TestClient httpx-deprecation warning persists (pre-existing, upstream, out of scope)
- `requirements.ready-ids` reported PROFILE-01 as 0/1 ready: sibling plan 01-03 also declares PROFILE-01 and has no SUMMARY yet — the shared-ID gate (#2388) correctly deferred `requirements mark-complete` to 01-03's close-out

## Known Stubs
None. All wired: completude flows to the envelope, error lines flow to the erro envelope, the shipped file validates through the strict schema. (Plan-01's documented placeholders — disabled nav items, Perfil completeness grid/preview UI — are plan-03 scope, not this plan's files.)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for 01-03 (Perfil UI): the envelope now carries `perfil`, `completude`, `exemplo`, and PT-BR `erros` lines — everything D-12's Perfil home and preview render
- The schema/loader contract Phases 2–6 consume is final: `Profile` model_validate over frontmatter metadata, loud ProfileError before any generation (SC2), bilingual maps with base language (SC4)
- Phase UAT (end-of-phase) covers the browser-visual checks: erro panel rendering, completude grid, resume-style preview, placeholder banner

---
*Phase: 01-foundation-scaffold-master-profile*
*Completed: 2026-09-26*

## Self-Check: PASSED

All 10 key files exist on disk; all 5 commit hashes found in git log; plan-level verification re-run green (35 backend tests passed; `grep -c "pt-BR" content/profile.md` = 36; live SC2 demo recorded with byte-identical file restore).
