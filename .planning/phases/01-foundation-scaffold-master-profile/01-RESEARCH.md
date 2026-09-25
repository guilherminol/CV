# Phase 1: Foundation — Scaffold + Master Profile - Research

**Researched:** 2026-09-25
**Domain:** Vite+React+TS / FastAPI scaffold mechanics; git-versioned YAML-frontmatter profile validated by Pydantic with loud PT-BR error surfacing
**Confidence:** HIGH (every load-bearing claim dual-verified: official docs fetched AND empirically reproduced this session by running the exact package versions via uv on this machine)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Implementation Decisions (locked)

**Bilingual schema shape (the flagged Phase 1 decision)**
- **D-01:** Localized content is encoded as **localized maps** — one field holding a language→text map (e.g., `summary: {pt-BR: …, en: …}`). Single source of truth; Pydantic validates all language variants side by side; adding a language later is trivial. — Reversibility: one-way (retrofitting later is the expensive path).
- **D-02:** **What gets localized:** narrative fields (summary, experience descriptions, project descriptions, impacts) AND job titles (e.g., "Senior Software Engineer" / "Engenheiro de Software Sênior"). Company names, tech/skill names, dates, and contact info stay single-value.
- **D-03:** **Fallback policy:** base + fallback — schema requires exactly one declared base language per localized field; other languages optional; generation falls back to base text when the run's language is missing; never blocks the user.
- **D-04:** **Declared base language: PT-BR.**

**Profile file layout**
- **D-05:** **Single `content/profile.md`** — one file to edit, commit, and validate. Markdown body stays minimal/unused.
- **D-06:** **All content lives in YAML frontmatter** — structured data AND bilingual narrative as localized maps; one parser, everything Pydantic-validated.
- **D-07:** **Full resume section set in v1 schema:** contact, summary, experiences (with embedded impacts), education, skills, certifications, languages, projects.
- **D-08:** **Impacts embedded per experience** — each experience entry carries its own impacts array (action + metric + context).
- **D-09:** **Skills as categorized groups** (linguagens, frameworks, ferramentas, cloud, …), each entry a plain tech name.
- **D-10:** **Unknown keys are rejected loudly** (Pydantic `extra='forbid'`) — a typo like `experiance:` fails validation naming the exact key and location.
- **D-11:** **Placeholder tracking via `example: true` flag in frontmatter** — the shipped file IS the example; the placeholder banner shows while the flag is set.

**Phase 1 UI scope**
- **D-12:** **App shell + Perfil status home + rendered profile preview.** Shell has header and nav placeholders for future modules. The Perfil home shows load status, validation errors in-app, section completeness at a glance, and the placeholder-data banner. Additionally, a preview renders the profile formatted like a resume page.
- **D-13:** **Validation errors surface in-app AND in the terminal.** A broken profile blocks the app; the UI shows the error in PT-BR; uvicorn logs keep the full raw Pydantic output.
- **D-14:** **Error style:** UI shows a PT-BR friendly message carrying the exact file/field path (e.g., "Erro no perfil: experiences[2].data_fim — data esperada, encontrado texto"); raw Pydantic detail lives in the terminal only.
- **D-15:** **No profile caching — validate on every load.** Backend re-reads and re-validates `content/profile.md` on every request.

**Example data persona**
- **D-16:** Persona mirrors the user's actual shape: **senior AI engineer focused on generative AI, also doing backend and frontend plus a bit of infra for those services.** Realistic, demonstrably fake via the `example: true` banner.
- **D-17:** **Example data is fully bilingual** — every localized field carries both `{pt-BR, en}`.

### Claude's Discretion
- Exact scaffold mechanics: package versions/pins per `.planning/research/STACK.md`, ESLint/Prettier flat config, ports, Vite proxy setup, FastAPI StaticFiles mounting order.
- Schema key naming language (English snake_case keys with bilingual values recommended — matches code conventions; example values in PT-BR/EN).
- Pydantic model file organization, loader module structure, test framework and fixtures for the validation path.
- UI implementation details (React Query setup, Tailwind styling, component breakdown) within the decided scope.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROFILE-01 | User can maintain a master profile as Markdown/YAML files in git, validated against a schema, shipped with example data covering experiences, projects, technologies, and impacts | Verified loader pattern (python-frontmatter → Pydantic `model_validate`), `extra='forbid'` mechanics with exact error shapes, localized-map schema pattern with base-language enforcement, placeholder `example: true` flag, bilingual example-data requirements, and the full v1 section set (D-07) |
</phase_requirements>

## Summary

This phase is greenfield scaffold plus one real design artifact: the profile contract. The stack is already pinned and registry-verified in `.planning/research/STACK.md` (fetched 2026-09-25, re-confirmed by `npm view` / `pip index` this session — all versions match). What this research adds is the Phase-1-specific mechanics the planner needs: (1) empirically verified Pydantic v2 behavior for `extra='forbid'`, error `loc` paths, and the localized-map-with-base-language pattern; (2) empirically verified python-frontmatter and PyYAML behavior on this Windows machine (malformed YAML exception type, UTF-8 default encoding, silent YAML 1.1 coercions); (3) scaffold-order pitfalls that only bite on Windows/uv (Python version pinning, `.gitignore`-before-first-commit, `127.0.0.1` vs `localhost` in the Vite proxy, StaticFiles mount ordering).

The single most important finding: the loud-validation behavior demanded by SC2 is fully achievable with verified primitives — `frontmatter.load()` raises `yaml.parser.ParserError` on broken YAML (caught before Pydantic), and Pydantic's `errors()` returns `type`/`loc` tuples precise enough to render D-14's exact file/field messages in PT-BR ("experiences[2].data_fim"). The base-language rule (D-03/D-04) fits naturally as a Pydantic validator over `dict[Literal["pt-BR","en"], str]` maps; a violation surfaces as `literal_error` naming the exact offending language key.

**Primary recommendation:** Scaffold in this order — `.gitignore` first (before any install), backend via uv with a pinned Python 3.12, frontend via `npm create vite -- --template react-ts`, then the schema/loader/error-mapper trio in `backend/app/profile/`, then the Perfil UI. Ship `content/profile.md` with fully bilingual example data and `example: true`. Use classic `app.mount("/", StaticFiles(...))` mounted last; `app.frontend()` exists in FastAPI 0.141.1 but its exact behavior is less documented — revisit later.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Profile storage + versioning | Repo (`content/profile.md` in git) | — | File-based store is a project constraint; git IS the store (no database) |
| Profile parsing + schema validation | API/Backend (Pydantic) | — | Single validator owned by backend; frontend consumes the verdict, never re-parses the file |
| PT-BR error message rendering (mapping `loc`+`type` → text) | API/Backend | Frontend (display only) | Backend owns the mapping so the terminal (D-13) and API carry the same canonical messages |
| Load status / errors / completeness / placeholder flag display | Frontend | — | Pure projection of `GET /api/profile`; React Query fetch + render |
| Resume-style profile preview | Frontend | — | Renders from validated JSON the backend already produced |
| Static serving of built SPA | API/Backend (StaticFiles) | Vite dev server (dev only) | Single process at localhost after build; dev proxy during development |
| Secret storage (`OPENROUTER_API_KEY`) | Repo config (`.env`, gitignored) | — | Constraint: key lives only in gitignored `.env`; Phase 1 scaffolds it, never uses it |

## Standard Stack

Pinned in `.planning/research/STACK.md` (registry-verified 2026-09-25) and **re-confirmed via `npm view` / `pip index` this session** — identical versions. Install exactly these.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vite | 8.3.1 [VERIFIED: npm view] | Frontend build + dev server with `/api` proxy | Zero-config dev loop; `server.proxy` kills CORS friction [CITED: vite.dev/config/server-options] |
| react / react-dom | 19.3.0 [VERIFIED: npm view] | UI (shell, Perfil home, preview) | Deepest ecosystem; user constraint "JS frontend" |
| typescript | ~5.9 (pin 5.x; npm `latest` is 7.0.2) [VERIFIED: npm view] | Types mirroring the Pydantic schema | Vite doesn't typecheck; `tsc -b` in build catches Pydantic↔TS contract drift |
| @vitejs/plugin-react | 6.1.1 [VERIFIED: npm view] | React plugin for Vite | Official pairing for Vite 8 + React 19 |
| FastAPI | 0.141.1 [VERIFIED: PyPI, empirically run] | Local API (`/api/profile`) + serves built SPA | Pydantic-native; `app.mount` StaticFiles pattern doc-verified; `app.frontend()` confirmed present in this exact version |
| uvicorn | 0.54.0 [VERIFIED: PyPI, empirically run] | ASGI server | `uv run uvicorn app.main:app --reload` is the whole dev backend story |
| pydantic | 2.13.5 [VERIFIED: PyPI, empirically run] | Profile schema, `extra='forbid'`, error localization | `errors()` gives `type`/`loc`/`msg`/`input` — exactly what D-10/D-14 need (verified below) |
| python-frontmatter | 1.3.0 [VERIFIED: PyPI; empirically run] | Parse `content/profile.md` frontmatter + body | `frontmatter.load(path, encoding='utf-8')` → `post.metadata` + `post.content` [VERIFIED: readthedocs API + empirical run] |
| uv | 0.12.5 installed (0.12.19 latest) [VERIFIED: local probe] | Backend env + deps | `.venv` next to pyproject, `uv.lock` committed, `uv add`/`uv run` [CITED: docs.astral.sh/uv/concepts/projects/layout] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyYAML | 6.0.3 [VERIFIED: PyPI, empirically run] | YAML layer under python-frontmatter | Transitive; do not hand-parse YAML elsewhere |
| python-dotenv | 1.2.3 [VERIFIED: PyPI] | Load `.env` (`OPENROUTER_API_KEY` present but unused in Phase 1) | `config.py` reads it tolerantly — app must run without the key |
| @tanstack/react-query | 5.103.2 [VERIFIED: npm view] | Server-state for the profile status query | Documented v5 setup: `QueryClient` + `QueryClientProvider` + `useQuery` [CITED: tanstack.com/query quick-start] |
| tailwindcss + @tailwindcss/vite | 4.3.3 [VERIFIED: npm view] | Styling; PT-BR strings hardcoded in a constants module | Official v4 Vite plugin; no `tailwind.config.js` [CITED: tailwindcss.com/docs/installation/using-vite] |
| zod | 4.6.5 [VERIFIED: npm view] | Optional frontend re-validation | Defense-in-depth only; backend Pydantic is the gate — skippable in Phase 1 |
| pytest | 9.1.1 [VERIFIED: pip index] | Backend test framework (loader/schema/error-mapper) | See Validation Architecture |
| httpx | current [ASSUMED] | Required by Starlette `TestClient` for API smoke tests | Dev dependency; fallback = skip TestClient tests, test loader only |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `app.mount("/", StaticFiles(html=True))` | `app.frontend()` (exists in 0.141.1) | `app.frontend()` handles client-side routing, but Phase 1 has a single route; classic mount is the fully documented pattern. Revisit when SPA routes grow |
| `frontmatter` + Pydantic | `pydantic-settings`-style YAML model, ruamel.yaml | ruamel (YAML 1.2) would kill the `yes/on` coercion class, but python-frontmatter is the pinned, verified path; coercion is handled by validators instead |
| RootModel-based `LocalizedText` type | `dict[Literal["pt-BR","en"], str]` + per-model validator | Alias + validator is the empirically verified pattern; RootModel variant unverified — don't use without checking |

**Installation:**
```bash
# 0. FIRST — repo root .gitignore (before ANY install or commit) — see Pitfall 2
# Frontend
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install && npm install @tanstack/react-query
npm install -D tailwindcss @tailwindcss/vite
# Backend  (see Pitfall 6 for the Python pin)
uv python pin 3.12          # writes backend/.python-version
uv init backend --app && cd backend   # verify flags; fallback: plain `uv init backend` + delete stray README
uv add fastapi "uvicorn[standard]" pydantic python-frontmatter python-dotenv
uv add --dev pytest httpx
# Secret scaffold (never committed)
echo "OPENROUTER_API_KEY=" > .env          # repo root, gitignored
cp .env .env.example                        # committed, empty value
```

## Package Legitimacy Audit

> Seam verdicts from `gsd-tools query package-legitimacy check` this session. All signals below were returned by the seam.

| Package | Registry | Age signal | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----------|-----------|-------------|---------|-------------|
| react / react-dom | npm | published 2026-09-09 | 169M / 160M per wk | github.com/react/react | SUS ("too-new") | Approved — canonical package; SUS is a recency heuristic (weekly release cadence), signals show official repo + massive downloads |
| vite | npm | published 2026-09-24 | 169M/wk | github.com/vitejs/vite | SUS ("too-new") | Approved — same heuristic artifact |
| @vitejs/plugin-react | npm | published 2026-08-28 | 87M/wk | github.com/vitejs/vite-plugin-react | SUS ("too-new") | Approved |
| typescript | npm | published 2026-07-08 | 271M/wk | github.com/microsoft/TypeScript | OK | Approved (pin ~5.9, not `latest` 7.0.2) |
| @tanstack/react-query | npm | published 2026-09-21 | 63M/wk | github.com/TanStack/query | SUS ("too-new") | Approved |
| zod | npm | published 2026-09-13 | 274M/wk | github.com/colinhacks/zod | SUS ("too-new") | Approved (optional dep) |
| tailwindcss / @tailwindcss/vite | npm | published 2026-07-16 | 122M / 45M per wk | github.com/tailwindlabs/tailwindcss | OK | Approved |
| fastapi | PyPI | published 2026-07-29 | unknown to seam | github.com/fastapi/fastapi | SUS ("unknown-downloads") | Approved — official repo; PyPI has no download-stats API for the seam |
| uvicorn | PyPI | published 2026-09-25 | unknown to seam | github.com/Kludex/uvicorn | SUS ("too-new","unknown-downloads") | Approved — official repo |
| pydantic | PyPI | published 2026-08-28 | unknown to seam | github.com/pydantic/pydantic | SUS | Approved — official repo |
| python-frontmatter | PyPI | published 2026-05-20 | unknown to seam | (PyPI metadata lacks repo URL; canonical repo is github.com/eyeseast/python-frontmatter) [CITED: python-frontmatter.readthedocs.io] | SUS ("no-repository") | Approved — missing metadata field, not a missing project; pinned in STACK.md |
| python-dotenv / pyyaml / pytest | PyPI | recent publishes | unknown to seam | github.com/theskumar/python-dotenv, pyyaml.org, github.com/pytest-dev/pytest | SUS ("unknown-downloads") | Approved — canonical packages |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** all of the above carry `pkg-name` [WARNING: flagged as suspicious — verify before using.] — every flag is a seam heuristic artifact (`too-new` = recent publish by an actively-maintained canonical package; `unknown-downloads` = PyPI provides no download stats). Recommendation: planner inserts **one** `checkpoint:human-verify` task covering the whole install batch (confirm versions match the table above), rather than nine noisy per-package checkpoints. No package has a postinstall script (seam: `postinstall: null` across the board) [VERIFIED: seam signals].

## Architecture Patterns

### System Architecture Diagram

```
                     EDIT TIME                              RUNTIME
 ┌────────────────────────────────┐   ┌────────────────────────────────────────────────┐
 │ User edits content/profile.md  │   │  Browser (localhost:5173 dev / :8000 prod)     │
 │ in own editor; commits to git  │   │  React shell (PT-BR strings)                   │
 └──────────────┬─────────────────┘   │  ├─ Perfil home: status, errors, completude,   │
                │ file on disk        │  │  banner (example:true), resume preview      │
                ▼                     │  └─ useQuery(['perfil']) → fetch /api/profile  │
 ┌────────────────────────────────┐   └───────────────────┬────────────────────────────┘
 │ backend/app/profile/loader.py  │                       │ /api (Vite proxy in dev)
 │  frontmatter.load(path)        │                       ▼
 │   ├─ yaml.YAMLError ───────────┼──▶ loud ProfileError  │
 │   └─ post.metadata             │                       │
 │        ▼                       │   ┌───────────────────▼────────────────────────┐
 │  Profile.model_validate(dict)  │   │ FastAPI (localhost:8000)                   │
 │   ├─ extra='forbid'            │   │  GET /api/profile                          │
 │   │   → extra_forbidden        │   │   ├─ ok:    {status, exemplo, perfil,      │
 │   ├─ literal/lang/base checks  │   │   │         completude}                    │
 │   │   → literal_error          │   │   └─ error: {status:"erro", erros:[{caminho,│
 │   └─ ValidationError.errors()  │   │              mensagem_ptbr}]} + FULL raw   │
 │        → type/loc/input        │   │              Pydantic detail in terminal   │
 └────────────────────────────────┘   │  API routes FIRST                          │
                                      │  app.mount("/", StaticFiles(dist, html=True)) LAST
                                      └────────────────────────────────────────────┘
```

Primary use case trace: user edits `profile.md` → refreshes browser → React Query refetches `/api/profile` (D-15: no caching) → backend re-reads + re-validates → either the Perfil home renders status/completeness/preview, or the error panel renders PT-BR messages and the terminal holds raw detail. There is no path to generation: every future phase-2+ route calls the same loader, which raises before any generation code runs (SC2's "before any generation can run").

### Recommended Project Structure

```
career-tailor/
├── .gitignore                  # written FIRST (Pitfall 2): .env, node_modules/, dist/, .venv, __pycache__
├── .env                        # OPENROUTER_API_KEY only — gitignored, scaffolded empty
├── .env.example                # committed, empty value
├── content/
│   └── profile.md              # YAML frontmatter (all content, D-06) + minimal body (D-05)
├── backend/
│   ├── .python-version         # "3.12" — pinned (Pitfall 6)
│   ├── pyproject.toml          # uv-managed; uv.lock committed
│   ├── app/
│   │   ├── main.py             # FastAPI app: /api routes first, SPA mount LAST
│   │   ├── config.py           # paths (CONTENT_DIR, FRONTEND_DIST), tolerant .env read
│   │   ├── profile/
│   │   │   ├── models.py       # Pydantic schema: Profile, Experience, Impact, ... (extra='forbid' everywhere)
│   │   │   ├── loader.py       # frontmatter.load → model_validate → Profile | ProfileError
│   │   │   └── errors.py       # FieldError list + type→PT-BR message map (D-14)
│   │   └── routes/
│   │       └── profile.py      # GET /api/profile
│   └── tests/
│       ├── conftest.py         # fixtures: valid example profile, typo'd profile, broken YAML (tmp_path)
│       ├── test_loader.py
│       ├── test_schema.py
│       └── test_api.py         # TestClient GET /api/profile ok + error shapes
└── frontend/
    ├── vite.config.ts          # react() + tailwindcss() plugins; server.proxy /api → 127.0.0.1:8000
    ├── src/
    │   ├── main.tsx            # QueryClientProvider wrapper
    │   ├── App.tsx             # shell: header, nav placeholders, Perfil home
    │   ├── api/client.ts       # typed fetch of /api/profile
    │   ├── constants/ui.ts     # all PT-BR UI strings, hardcoded (no i18n framework)
    │   └── components/
    │       ├── PlaceholderBanner.tsx   # example:true → "dados de exemplo"
    │       ├── ErrorPanel.tsx          # PT-BR validation errors in-app (D-13/D-14)
    │       ├── CompletenessGrid.tsx    # section completeness at a glance (D-12)
    │       └── ProfilePreview.tsx      # resume-like rendering (D-12)
    └── dist/                   # build output, gitignored, served by FastAPI in prod mode
```

### Pattern 1: Localized-Map Schema with Base-Language Enforcement (D-01…D-04)

**What:** Every localized field is `dict[Literal["pt-BR","en"], str]`; a validator enforces the base language `pt-BR` is present (D-03); unknown language keys are rejected by the `Literal` key type.
**When to use:** All narrative fields + job titles (D-02). Single-value fields (company, tech names, dates, contact) stay plain `str`.
**Verified behavior (empirical run, pydantic 2.13.5):** `{"pt-BR": "ola", "en": "hi"}` validates; a `pt-PT` key fails with `type='literal_error'`, `loc=('values', 'pt-PT', '[key]')`, msg `"Input should be 'pt-BR' or 'en'"` — the offending key is named exactly. A missing base language raised via `model_validator(mode="after")` surfaces as `type='value_error'`.

```python
# Source: empirical verification run (uv, pydantic 2.13.5, this session)
from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator

Language = Literal["pt-BR", "en"]
BASE_LANGUAGE: Language = "pt-BR"          # D-04
LocalizedText = dict[Language, str]        # D-01

class _BaseLanguageMixin(BaseModel):
    @model_validator(mode="after")
    def _base_language_present(self) -> "Self":
        for name, field in type(self).model_fields.items():
            if field.annotation is LocalizedText:
                values = getattr(self, name)
                if BASE_LANGUAGE not in values:
                    raise ValueError(
                        f"idioma base '{BASE_LANGUAGE}' ausente no campo localizado "
                        f"'{name}' — adicione ao menos a chave '{BASE_LANGUAGE}'"
                    )
        return self

class Experience(_BaseLanguageMixin):
    model_config = ConfigDict(extra="forbid")   # D-10 — on EVERY model
    company: str                                 # single-value (D-02): proper noun
    title: LocalizedText                         # D-02: job titles ARE localized
    start_date: str                              # see Pitfall 1 (date coercion)
    end_date: str | None = None
    description: LocalizedText
    impacts: list[Impact]                        # D-08: embedded per experience
```

*Mixin-inheritance of validators is standard Pydantic but was not exercised in the empirical run — [ASSUMED]; fallback is duplicating the validator in each model (verified pattern).*

### Pattern 2: Fail-Fast Loader with Typed Error Capture

**What:** One function owns read+validate; every failure mode is caught and converted to a structured error list naming the exact file and field path. Verified exception surfaces:
- malformed YAML → `yaml.parser.ParserError` (a `yaml.YAMLError` subclass) — **caught before Pydantic** [VERIFIED: empirical run]
- `frontmatter.load(path, encoding='utf-8')` — filename or file object; `post.metadata` dict + `post.content` body; UTF-8 default [VERIFIED: readthedocs API + empirical run]

```python
# Source: python-frontmatter readthedocs (api.html) + empirical run this session
import yaml, frontmatter
from pydantic import ValidationError

class ProfileError(Exception):
    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw                       # terminal-only detail (D-13/D-14)

def load_profile(path: Path = CONTENT_DIR / "profile.md") -> Profile:
    try:
        post = frontmatter.load(str(path))   # encoding='utf-8' is the verified default
    except FileNotFoundError:
        raise ProfileError(f"Perfil não encontrado: {path}", f"FileNotFoundError: {path}")
    except yaml.YAMLError as exc:
        raise ProfileError(
            f"Erro no perfil: {path} — YAML do frontmatter inválido (verifique indentação e dois-pontos)",
            f"{type(exc).__name__}: {exc}",
        )
    except UnicodeDecodeError as exc:
        raise ProfileError(f"Erro no perfil: {path} — arquivo não é UTF-8 válido", repr(exc))
    try:
        return Profile.model_validate(post.metadata)   # D-06: frontmatter holds everything
    except ValidationError as exc:
        raw = "\n".join(str(e) for e in exc.errors(include_url=False))
        raise ProfileError(render_errors_ptbr(exc), raw)
```

### Pattern 3: PT-BR Error Localization (D-14) — the verified `type` vocabulary

**What:** Map the five error types Phase 1 can produce to PT-BR phrases; render `loc` tuples as `experiences[2].data_fim`-style paths. **All five types below were produced and observed in the empirical run** (pydantic 2.13.5): `missing`, `extra_forbidden` (with `loc=('experiences', 0, 'salario')`), `string_type` (msg `'Input should be a valid string'` for an int input), `literal_error` (msg `"Input should be 'pt-BR' or 'en'"`), `value_error` (custom validator message; empty `loc` = model-level — label it "estrutura do perfil").

```python
# Source: empirical run outputs (quoted verbatim above) — pydantic 2.13.5
_PTBR_BY_TYPE = {
    "missing":         "campo obrigatório ausente",
    "extra_forbidden": "chave desconhecida — provável erro de digitação (chaves extras não são aceitas)",
    "string_type":     "texto esperado, encontrado valor de outro tipo",
    "literal_error":   "valor fora das opções permitidas",
    "value_error":     None,   # use the validator's own message (already PT-BR)
}

def render_loc(loc: tuple) -> str:
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        elif part == "[key]":            # literal_error on a dict key (verified loc shape)
            out += " (chave)"
        else:
            out += f"{'' if not out else '.'}{part}"
    return out or "estrutura do perfil"

def render_errors_ptbr(exc: ValidationError) -> str:
    lines = [f"Erro no perfil: {PROFILE_PATH}"]
    for e in exc.errors(include_url=False):
        msg = _PTBR_BY_TYPE.get(e["type"], e["msg"])
        lines.append(f"  • {render_loc(e['loc'])} — {msg or e['msg']}")
    return "\n".join(lines)
```

### Pattern 4: API Contract — Status Object, Not 500s (D-12/D-13/D-15)

**What:** `GET /api/profile` always answers 200 with a status envelope; the broken profile is a *state the UI renders*, not an HTTP failure. The backend logs the full raw detail; the API carries only the PT-BR rendering. No caching: the route calls `load_profile()` on every request.

```python
# API routes FIRST — the SPA mount (Pattern 5) comes after ALL route definitions
@app.get("/api/profile")
def get_profile():
    try:
        profile = load_profile()
    except ProfileError as exc:
        logger.error("Falha ao carregar perfil:\n%s", exc.raw)   # full raw Pydantic output → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {
        "status": "ok",
        "exemplo": profile.example,                              # D-11 placeholder flag
        "perfil": profile.model_dump(),
        "completude": compute_completeness(profile),             # section presence/counts (D-12; NOT the PROFILE-02 lint)
    }
```

### Pattern 5: Serving the Frontend — Dev Proxy + Mount-Last

**Dev (two processes):** Vite on 5173 proxies `/api` to FastAPI; **daily use (one process):** `npm run build` once, FastAPI serves `frontend/dist` via StaticFiles. Mount at `"/"` matches every path, so it must be the last registration or it swallows `/api/*` [CITED: fastapi.tiangolo.com/tutorial/static-files; Starlette route-matching order]. `html=True` (Starlette option) serves `index.html` at directory roots [CITED: same page, deferring to Starlette docs].

```typescript
// frontend/vite.config.ts — Source: vite.dev/config/server-options (CITED)
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // 127.0.0.1, NOT localhost — Node dns ordering (::1 vs 127.0.0.1) can make
      // 'localhost' targets unreachable; docs warn about resolved-address mismatch [CITED: vite.dev]
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
```

```python
# backend/app/main.py (tail) — Source: fastapi.tiangolo.com/tutorial/static-files (CITED)
from fastapi.staticfiles import StaticFiles
if FRONTEND_DIST.exists():   # build output may not exist in dev-only sessions
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="spa")
```

### Pattern 6: Placeholder Flag + Bilingual Example Data (D-11/D-16/D-17)

**What:** `example: true` is a declared schema field (`example: bool = False` — it MUST be declared or `extra='forbid'` rejects it, Pitfall 3). The shipped `content/profile.md` IS the example: a senior AI engineer persona (generative-AI focus, backend+frontend, some infra) with every localized field carrying both `pt-BR` and `en`.

```yaml
# content/profile.md (frontmatter skeleton — keys English snake_case per discretion; values bilingual)
example: true
name: "Ana Exemplo"                # persona: senior AI engineer, generative AI + full-stack + light infra
contact:
  email: "ana.exemplo@example.com"
  location: "São Paulo, SP"
summary:
  pt-BR: "Engenheira de software sênior focada em IA generativa..."
  en: "Senior software engineer focused on generative AI..."
experiences:
  - company: "Exemplo IA"          # single-value (D-02)
    title: { pt-BR: "Engenheira de Software Sênior", en: "Senior Software Engineer" }
    start_date: "2022-03"          # QUOTED — see Pitfall 1
    end_date: null
    description: { pt-BR: "...", en: "..." }
    impacts:
      - action:  { pt-BR: "Implementou pipeline RAG...", en: "Implemented RAG pipeline..." }
        metric:  { pt-BR: "-40% no tempo de resposta", en: "-40% response time" }
        context: { pt-BR: "...", en: "..." }
skills:                              # D-09: categorized groups
  - category: "linguagens"
    items: ["Python", "TypeScript"]
projects:
  - name: "Projeto Exemplo"
    description: { pt-BR: "...", en: "..." }
    technologies: ["FastAPI", "React"]
    impacts: []
education: []
certifications: []
languages:
  - name: "Português"
    level: "nativo"
```

### Anti-Patterns to Avoid

- **Caching the parsed profile** (lru_cache, module-level singleton): violates D-15; edit-refresh must see current data. Load per request — it's a local file, it's cheap.
- **HTTP 500 on broken profile:** turns a user-input problem into an app crash; the UI can't render PT-BR field errors from an error envelope. Use the status object (Pattern 4).
- **Raw `str(exc)` of a ValidationError in the UI:** a multi-line English dump; map `errors()` instead (Pattern 3).
- **Markdown-body-as-content:** D-05/D-06 put everything in frontmatter; don't split content between YAML and body "because frontmatter files usually do."
- **An i18n framework for the UI:** one user, one UI language; hardcoded PT-BR constants module (STACK.md What-NOT-to-use).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frontmatter parsing | Regex split on `---` | python-frontmatter `frontmatter.load` | Handles delimiters, YAML safe-mode handler, encoding; verified exception surfaces |
| Schema validation + error aggregation | Hand-rolled key checks | Pydantic v2 `ConfigDict(extra="forbid")` + `errors()` | Nested loc paths, all error types aggregated in one pass — verified |
| Localized-map base-language rule | Ad-hoc `if "pt-BR" in d` scattered | One `model_validator(mode="after")` (Pattern 1) | Single enforcement point; scales to new localized fields |
| Dev proxy/CORS | CORS middleware + absolute URLs | Vite `server.proxy` | Zero CORS code; same-origin in prod via StaticFiles |
| SPA static serving | Custom catch-all route returning index.html | `StaticFiles(html=True)` mounted last | Documented; catch-all hand-rolled routes shadow API paths when ordered wrong |
| PT-BR validation prose | Generating natural-language explanations per field | Type→phrase map over `errors()` | Deterministic, testable, covers exactly the five producible types |
| Env loading | Manual `.env` parser | python-dotenv + os.environ | Standard; `.env` gitignored before first commit |

**Key insight:** every "clever" part of this phase (parsing, validation, error paths, proxying, serving) is a solved problem with verified behavior — the phase's real work is the schema shape (D-01…D-11) and the example data.

## Common Pitfalls

### Pitfall 1: YAML 1.1 silent coercion corrupts hand-edited values
**What goes wrong:** Empirically verified with PyYAML 6.0.3 on this machine: `on: remote` → the **key** becomes boolean `True`; `remoto: yes` → `True`; `versao: 3.10` → float `3.1` (trailing zero silently stripped); `start_date: 2022-03-15` → `datetime.date` object. Only full `YYYY-MM-DD` become dates — `2022-03` stays a string.
**Why it happens:** PyYAML implements YAML 1.1 implicit typing; `safe` refers to object construction, not type resolution.
**How to avoid:** Quote ambiguous values in the shipped example (dates, versions); type date fields as `str` with a `field_validator(mode="before")` coercing `datetime.date` → ISO string so both quoted and unquoted dates validate; schema keys are fixed English snake_case so the `on`-key trap can't hit schema keys.
**Warning signs:** A validation error saying "texto esperado" (string_type) on a date field the user wrote unquoted; `example` flag flipping to `True`/`False` mysteriously if someone writes `example: on`.

### Pitfall 2: `.env` (or `node_modules`) committed because `.gitignore` came last
**What goes wrong:** Scaffold order is seductive: run `npm create vite`, `uv add`, then commit — and the first commit already contains junk; later `.env` with a real key gets committed in Phase 2.
**Why it happens:** Install commands create files before ignore rules exist.
**How to avoid:** Write `.gitignore` (with `.env`, `node_modules/`, `dist/`, `.venv/`, `__pycache__/`, `outputs/`) as the repo's first commit. Add an automated test asserting `git check-ignore .env` exits 0 (see Validation Architecture). uv's `.venv` is auto-excluded by uv's internal gitignore [CITED: docs.astral.sh/uv] but explicit is still better.
**Warning signs:** `git status` shows `node_modules/` or `.env` as untracked-but-addable.

### Pitfall 3: `extra='forbid'` missing on one nested model — or the placeholder flag undeclared
**What goes wrong:** Forbid must be set on **every** model (`Experience`, `Impact`, nested contact...); one forgotten model silently accepts typos again (defeating D-10). And `example: true` in frontmatter is itself a key — if not a declared field, the shipped file fails its own validation.
**Why it happens:** `model_config` is per-class, not inherited from a parent app config.
**How to avoid:** A shared base model (`class _Strict(BaseModel): model_config = ConfigDict(extra="forbid")`) that every profile model inherits; declare `example: bool = False` in `Profile`.
**Warning signs:** A test asserting a typo'd key inside each nested model raises `extra_forbidden` — one test per model.

### Pitfall 4: Vite proxy target `localhost` → IPv6 `::1` → ECONNREFUSED
**What goes wrong:** uvicorn binds `127.0.0.1`; Node ≥17 resolves `localhost` as `::1` first; the dev proxy then can't reach the backend. The Vite docs explicitly warn that resolved addresses can differ from the listening address [CITED: vite.dev/config/server-options].
**How to avoid:** `'http://127.0.0.1:8000'` as the proxy target — never `localhost`. Document `npm run dev` + `uv run uvicorn app.main:app --reload` as the two-terminal dev flow.
**Warning signs:** Browser shows proxy errors while `curl http://127.0.0.1:8000/api/profile` works.

### Pitfall 5: StaticFiles mount swallows the API
**What goes wrong:** `app.mount("/", ...)` matches every path; any API route defined *after* the mount is unreachable [CITED: fastapi.tiangolo.com/tutorial/static-files — mounting = an independent app owning all sub-paths].
**How to avoid:** Register `/api/*` routes first, mount the SPA last; guard with `if FRONTEND_DIST.exists()` so dev-only sessions don't crash at import (StaticFiles raises on a missing directory — `check_dir` behavior [ASSUMED]).
**Warning signs:** `/api/profile` returns index.html.

### Pitfall 6: uv picks its own Python, not the system one
**What goes wrong:** `uv run` in this environment resolved **Python 3.14.7** (uv-managed), even though system Python is 3.12.10 — STACK.md's compatibility table was verified against 3.12.10.
**How to avoid:** `uv python pin 3.12` in `backend/` (writes `.python-version`; `uv python find 3.12` confirmed resolvable to the system 3.12.10 install). Set `requires-python = ">=3.12"` in pyproject.
**Warning signs:** `uv run python -V` prints 3.14.x inside backend/.

### Pitfall 7: Windows encoding — cp1252 sneaking in around the UTF-8 file
**What goes wrong:** `content/profile.md` is UTF-8 with accents; on Windows any side-channel read with a locale default (cp1252) mojibakes or raises. `frontmatter.load` defaults to UTF-8 (verified), but hand-written `open(path)` elsewhere does not.
**How to avoid:** Always `open(..., encoding="utf-8")`; pass `encoding="utf-8"` explicitly to `frontmatter.load` anyway for self-documentation; never print raw profile content through subprocess pipes without UTF-8 handling.
**Warning signs:** `ç`/`ã` rendered wrong in one display path but fine in another.

### Pitfall 8: `str(ValidationError)` dumped into the UI / model-level errors with empty `loc`
**What goes wrong:** The default exception string is a long English dump (D-14 violation). Also, `model_validator` failures surface with an **empty `loc` tuple** (verified) — a renderer that assumes `loc` is non-empty crashes on exactly the base-language error.
**How to avoid:** Pattern 3's mapper; `render_loc(())` → "estrutura do perfil".
**Warning signs:** English text in the UI error panel; IndexError in the error renderer when a language is missing.

### Pitfall 9: React Query v5 API drift
**What goes wrong:** v5 tutorials show `isLoading`; v5 uses `isPending` for initial-load state; `useQuery` takes a single options object. Copying v4 snippets fails typecheck.
**How to avoid:** Follow the v5 quick-start shape (documented setup: `new QueryClient()` → `QueryClientProvider` → `useQuery({ queryKey, queryFn })`) [CITED: tanstack.com/query quick-start]; with `tsc -b` in the build, drift fails loudly.
**Warning signs:** TypeScript errors on query result destructuring right after install.

## Code Examples

### Profile schema skeleton (verified primitives)

```python
# Source: empirical verification run (pydantic 2.13.5) — see Patterns 1 & 3 for verified behaviors
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date

Language = Literal["pt-BR", "en"]
LocalizedText = dict[Language, str]

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")            # D-10 — inherited by ALL models

class Impact(_Strict):
    action: LocalizedText
    metric: LocalizedText
    context: LocalizedText | None = None

def _date_to_str(v: object) -> object:
    return v.isoformat()[:7] if isinstance(v, date) else v   # Pitfall 1: unquoted YAML dates arrive as date

class Experience(_Strict):
    company: str
    title: LocalizedText
    location: str | None = None
    start_date: str
    end_date: str | None = None
    description: LocalizedText
    impacts: list[Impact] = []
    _norm_dates = field_validator("start_date", "end_date", mode="before")(_date_to_str)

class Profile(_Strict):
    example: bool = False                                # D-11 — must be declared
    name: str
    contact: dict[str, str]
    summary: LocalizedText
    experiences: list[Experience]
    education: list[dict] = []
    skills: list[dict] = []                              # {category, items[]} (D-09) — split into models
    certifications: list[dict] = []
    languages: list[dict] = []
    projects: list[dict] = []
```

*(Educational/skills/certs/languages/projects shown as dicts for brevity — split into proper `_Strict` models in implementation; each needs its own `extra_forbidden` test per Pitfall 3.)*

### React Query setup (v5, documented shape)

```tsx
// Source: tanstack.com/query/latest/docs/framework/react/quick-start (CITED)
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'

const queryClient = new QueryClient()

function useProfile() {
  return useQuery({
    queryKey: ['perfil'],
    queryFn: () => fetch('/api/profile').then((r) => r.json()),
  })
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* shell: header + nav placeholders + Perfil home (D-12) */}
    </QueryClientProvider>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI: hand-rolled SPA catch-all or mount | `app.frontend()` helper (uses StaticFiles underneath, handles client-side routing) — **present in 0.141.1** (verified via `hasattr`) | current docs | Not needed for Phase 1's single page; revisit when SPA routing grows |
| Tailwind v3 + config file + PostCSS | v4 CSS-first: `@tailwindcss/vite` plugin + `@import "tailwindcss"`, no config file | v4 | Simpler scaffold; theme via CSS variables |
| TypeScript 5.x default | npm `latest` is 7.0.2 (Go-native) | 2026 | Still pin `~5.9` (STACK.md pin advice, MEDIUM) until lint tooling supports TS 7 |
| zod 3 (`zod/v4` subpath bridge) | zod 4: `import { z } from "zod"` IS the v4 API | 4.x | Ignore older tutorials mentioning subpath imports |
| pip/venv dance | uv project workflow (`.venv` beside pyproject, committed `uv.lock`) | current | Pin Python via `.python-version` or uv picks its managed newest (Pitfall 6) |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `httpx` is required by Starlette `TestClient` for `test_api.py` | Standard Stack / Validation Architecture | TestClient import fails → add httpx (1-line dev dep) or drop API tests, keep loader tests |
| A2 | `uv init backend --app` flags / `uv add` auto-creates `pyproject.toml` in an empty dir | Installation | Minor friction at scaffold; fallback documented (write minimal `[project]` table manually, then `uv add`) |
| A3 | `StaticFiles` raises at mount time if `directory` is missing (`check_dir`) | Pattern 5 / Pitfall 5 | Crash at import in dev-only sessions → the `exists()` guard prevents it either way |
| A4 | Pydantic validators compose through a mixin base class (`_BaseLanguageMixin`) | Pattern 1 | Base-language check silently absent → fallback: duplicate validator per model (verified primitive); the dedicated test (missing `pt-BR` fails loudly) catches this immediately |
| A5 | Vite react-ts template build script is `tsc -b && vite build` | Validation Architecture | Frontend gate command differs → check `frontend/package.json` at scaffold |
| A6 | Seam SUS verdicts on all canonical packages are recency/metadata heuristics, not real risk | Package Legitimacy Audit | One `checkpoint:human-verify` for the install batch covers it; no package removed |

## Open Questions (RESOLVED)

1. **`app.frontend()` exact signature/behavior** — **RESOLVED (2026-09-25, at planning):**
   - What we know: exists in FastAPI 0.141.1 (verified `hasattr`); docs say it wraps StaticFiles and handles client-side routing
   - What's unclear: exact options (fallback behavior for unknown paths)
   - Recommendation: use the classic documented mount for Phase 1; revisit `app.frontend()` if/when the SPA gains real routes
   - Resolution: classic documented `StaticFiles(html=True)` mount adopted — implemented by plan 01 Task 2 (main.py, mounted last after /api routes); `app.frontend()` stays unresearched and unused in Phase 1. No open question remains for this phase.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite dev/build | ✓ | v22.16.0 (Vite 8 needs ≥22.12 — STACK.md) | — |
| npm | frontend deps | ✓ | 10.9.2 | — |
| Python | backend runtime | ✓ | 3.12.10 system; **uv defaults to managed 3.14.7** → pin (Pitfall 6) | — |
| uv | backend env/deps | ✓ | 0.12.5 (latest 0.12.19; not required) | — |
| git | profile versioning | ✓ | 2.49.0.windows.1 | — |
| Chromium (Playwright) | Phase 4 only | not needed | — | deferred to Phase 4 |

**Missing dependencies with no fallback:** none — everything Phase 1 needs is installed.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (verified via `pip index`); httpx dev dep for TestClient (A1) |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options] testpaths=["tests"]`) — Wave 0 |
| Quick run command | `cd backend && uv run pytest -q` |
| Full suite command | `cd backend && uv run pytest` + `cd frontend && npm run build` (tsc + vite = frontend gate, A5) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROFILE-01 / SC2 | Valid shipped `content/profile.md` validates; bilingual example loads | unit | `uv run pytest tests/test_loader.py::test_example_profile_validates -q` | ❌ Wave 0 |
| PROFILE-01 / SC2 | Typo'd key (`experiance:`) → loud error naming file + exact key (`extra_forbidden`, loc names key) | unit | `uv run pytest tests/test_schema.py::test_unknown_key_rejected -q` | ❌ Wave 0 |
| PROFILE-01 / SC2 | Broken YAML frontmatter → `ProfileError` (not a stack trace), names the file | unit | `uv run pytest tests/test_loader.py::test_malformed_yaml_loud -q` | ❌ Wave 0 |
| PROFILE-01 / SC4 | Missing base language `pt-BR` in any localized field → loud field-named error | unit | `uv run pytest tests/test_schema.py::test_base_language_required -q` | ❌ Wave 0 |
| PROFILE-01 / SC4 | Every localized field in shipped example carries both `pt-BR` and `en` (D-17) | unit | `uv run pytest tests/test_schema.py::test_example_fully_bilingual -q` | ❌ Wave 0 |
| PROFILE-01 / SC3 | `example: true` exposed by API; unknown-key rejection per nested model (Pitfall 3) | unit/API | `uv run pytest tests/test_api.py tests/test_schema.py -q` | ❌ Wave 0 |
| SC5 | `.env` is gitignored: `git check-ignore .env` exits 0 | unit (subprocess) | `uv run pytest tests/test_secrets.py::test_env_gitignored -q` | ❌ Wave 0 |
| SC1 | App serves PT-BR interface at localhost | manual | `npm run build` + `uv run uvicorn app.main:app` → browser at 127.0.0.1:8000; dev mode via two terminals | manual (UI safety gate covers) |

### Sampling Rate
- **Per task commit:** `cd backend && uv run pytest -q`
- **Per wave merge:** full pytest suite + `cd frontend && npm run build`
- **Phase gate:** full suite green + manual run (SC1 smoke) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/conftest.py` — fixtures writing valid/typo'd/broken-YAML `profile.md` variants to `tmp_path`
- [ ] `backend/pyproject.toml` pytest config + `uv add --dev pytest httpx`
- [ ] Frontend unit tests: intentionally none in Phase 1 (UI is fetch-and-render projection of a fully tested backend; browser check via manual SC1 smoke + UI safety gate)

## Security Domain

`security_enforcement: true`, ASVS level 1 (`security_block_on: high`). Phase 1 is localhost-only, single-user, no auth by explicit project constraint — most ASVS categories are n/a by design, not by omission.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Single-user localhost tool (PROJECT.md constraint) |
| V3 Session Management | no | No sessions exist |
| V4 Access Control | no | No multi-user surface |
| V5 Input Validation | yes | Pydantic `extra='forbid'` at every model; `GET /api/profile` takes no user input; schema re-validated on every request |
| V6 Cryptography | no | No crypto in Phase 1 |
| V12 Files & Resources | yes (read-only) | App never writes to `content/`; no uploads; paths fixed under `CONTENT_DIR` (no traversal surface) |
| V14 Configuration | **yes — the phase's security core** | `OPENROUTER_API_KEY` in gitignored `.env`; `.env.example` committed with empty value; `git check-ignore` automated test; key never read/required by Phase 1 code |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API key committed to git (drains OpenRouter account in Phase 2+) | Information Disclosure | `.gitignore` written as the first commit; automated `git check-ignore .env` test; if ever leaked: rotate + purge history (PITFALLS.md recovery) |
| Supply-chain (malicious dependency) | Tampering | Package Legitimacy Audit above — all canonical packages, official repos, no postinstall scripts |
| Sensitive data in logs | Information Disclosure | Terminal logs carry profile validation detail (fine — local); must never carry the API key (Phase 2 concern, noted for the gateway) |

## Sources

### Primary (HIGH confidence — dual-verified: docs + empirical run this session)
- Empirical verification runs (`uv run` with pydantic 2.13.5, python-frontmatter, fastapi 0.141.1, PyYAML 6.0.3, uvicorn 0.54.0 on this machine): `extra_forbidden`/`missing`/`string_type`/`literal_error`/`value_error` error shapes and loc structures; `yaml.parser.ParserError` on malformed frontmatter; frontmatter metadata/content split; PyYAML coercions (`on:`→`True` key, `yes`→`True`, `3.10`→`3.1` float, `2020-03-01`→`date`, `2020-03`→str, `pt-BR` keys→str); `app.frontend()` present; `StaticFiles(html=...)` param exists; resolved versions
- https://docs.pydantic.dev/latest/errors/errors/ (via pydantic.dev/docs/validation) — `type: 'missing'` example output
- https://python-frontmatter.readthedocs.io/en/latest/ + /api.html — `frontmatter.load(fd, encoding='utf-8', handler=None)`, YAMLHandler safe-mode default, metadata/content
- https://fastapi.tiangolo.com/tutorial/static-files/ — `app.mount(path, StaticFiles(...))`, mount-owns-sub-paths semantics, `app.frontend()` recommendation

### Secondary (MEDIUM confidence)
- https://vite.dev/config/server-options.html — `server.proxy` shape, `changeOrigin`, `rewrite`, dns/IPv6 mismatch warning [config shape CITED; the 127.0.0.1 recommendation follows directly from the docs' own warning]
- https://tailwindcss.com/docs/installation/using-vite — v4 plugin install, `@import "tailwindcss"`, no config file
- https://tanstack.com/query/latest/docs/framework/react/quick-start — v5 QueryClientProvider/useQuery setup
- https://docs.astral.sh/uv/concepts/projects/layout/ — `.venv` beside pyproject, committed universal `uv.lock`, `uv run` auto-sync
- WebSearch corroboration for YAML 1.1 coercion gotchas (Stack Overflow "PyYAML automatically converting certain keys to boolean", YAML 1.1 Norway-problem references) — underlying behavior independently verified empirically

### Tertiary (LOW confidence)
- None material; all remaining low-confidence items are explicitly tagged [ASSUMED] in the Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions re-confirmed against npm/PyPI this session; matches STACK.md pins exactly
- Architecture (schema/loader/error mapping): HIGH — every mechanism empirically reproduced with the exact package versions on this machine
- Pitfalls: HIGH for 1,2,3,6,7,8 (verified); MEDIUM for 4,5 (doc-cited, standard behavior)
- Scaffold mechanics (uv init flags, TestClient deps): MEDIUM — tagged [ASSUMED] with fallbacks

**Research date:** 2026-09-25
**Valid until:** 2026-10-25 (stable pin set; re-check `uvicorn`/`react` publishes only if scaffolding slips past ~2 weeks)
