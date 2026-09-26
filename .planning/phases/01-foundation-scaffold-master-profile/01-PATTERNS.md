# Phase 1: Foundation — Scaffold + Master Profile - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** 26 (new files to create; zero existing source files modified)
**Analogs found:** 0 / 26 — **greenfield repo** (verified: `git ls-files` returns only `.claude/CLAUDE.md` and `.planning/*`; no `frontend/`, `backend/`, or `content/` exists)

## Greenfield Note

There are no existing code patterns to copy. Every file's pattern source is either:
1. **RESEARCH.md verified patterns** (`01-RESEARCH.md` in this phase directory — empirically reproduced this session with the exact pinned package versions on this machine), or
2. **Canonical framework conventions** (Vite react-ts template output, uv project layout, React Query v5 quick-start) cited in RESEARCH.md.

The excerpts below are the authoritative patterns for the planner. All were verified empirically (pydantic 2.13.5, python-frontmatter 1.3.0, fastapi 0.141.1, PyYAML 6.0.3, uvicorn 0.54.0 — see RESEARCH.md "Sources" section).

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `.gitignore` | config | — | none — greenfield | greenfield (Pitfall 2 convention) |
| `.env` | config | — | none — greenfield | greenfield (python-dotenv convention) |
| `.env.example` | config | — | none — greenfield | greenfield |
| `content/profile.md` | model (data artifact) | file-I/O | none — greenfield | greenfield (RESEARCH Pattern 6 skeleton) |
| `backend/.python-version` | config | — | none — greenfield | greenfield (uv convention, Pitfall 6) |
| `backend/pyproject.toml` | config | — | none — greenfield | greenfield (uv project layout) |
| `backend/app/main.py` | controller (app entrypoint) | request-response | none — greenfield | greenfield (RESEARCH Patterns 4+5) |
| `backend/app/config.py` | config | — | none — greenfield | greenfield (python-dotenv, tolerant read) |
| `backend/app/profile/models.py` | model | transform | none — greenfield | greenfield (RESEARCH Pattern 1 + schema skeleton) |
| `backend/app/profile/loader.py` | service | file-I/O + transform | none — greenfield | greenfield (RESEARCH Pattern 2) |
| `backend/app/profile/errors.py` | utility | transform | none — greenfield | greenfield (RESEARCH Pattern 3) |
| `backend/app/routes/profile.py` | route | request-response | none — greenfield | greenfield (RESEARCH Pattern 4) |
| `backend/tests/conftest.py` | test (fixtures) | — | none — greenfield | greenfield (pytest tmp_path convention) |
| `backend/tests/test_loader.py` | test | — | none — greenfield | greenfield |
| `backend/tests/test_schema.py` | test | — | none — greenfield | greenfield |
| `backend/tests/test_api.py` | test | request-response | none — greenfield | greenfield (Starlette TestClient) |
| `backend/tests/test_secrets.py` | test | — | none — greenfield | greenfield (`git check-ignore` subprocess) |
| `frontend/vite.config.ts` | config | — | none — greenfield | greenfield (RESEARCH Pattern 5) |
| `frontend/src/main.tsx` | provider (entrypoint) | — | none — greenfield | greenfield (React Query v5 quick-start) |
| `frontend/src/App.tsx` | component (shell) | request-response (via query) | none — greenfield | greenfield |
| `frontend/src/api/client.ts` | service | request-response | none — greenfield | greenfield (Pattern 4 contract) |
| `frontend/src/constants/ui.ts` | config (strings) | — | none — greenfield | greenfield (STACK.md: no i18n framework) |
| `frontend/src/components/PlaceholderBanner.tsx` | component | — | none — greenfield | greenfield |
| `frontend/src/components/ErrorPanel.tsx` | component | — | none — greenfield | greenfield |
| `frontend/src/components/CompletenessGrid.tsx` | component | — | none — greenfield | greenfield |
| `frontend/src/components/ProfilePreview.tsx` | component | — | none — greenfield | greenfield |

Scaffold-generated files (not hand-designed, template-owned): `frontend/package.json`, `tsconfig*.json`, `eslint.config.js`, `index.html`, `src/index.css`, `src/App.css`, `src/assets/`, `backend/uv.lock`, `.venv/` — pattern source is the Vite react-ts template and uv itself; planner should not hand-author these.

## Pattern Assignments

### `content/profile.md` (model, file-I/O)

**Pattern source:** RESEARCH.md Pattern 6 (lines 384–421) + decisions D-01…D-11, D-16, D-17

Frontmatter skeleton — keys English snake_case, localized values as `{pt-BR, en}` maps, dates QUOTED (Pitfall 1), `example: true` declares the placeholder state:

```yaml
example: true
name: "Ana Exemplo"                # persona: senior AI engineer, generative AI + full-stack + light infra (D-16)
contact:
  email: "ana.exemplo@example.com"
  location: "São Paulo, SP"
summary:
  pt-BR: "Engenheira de software sênior focada em IA generativa..."
  en: "Senior software engineer focused on generative AI..."
experiences:
  - company: "Exemplo IA"          # single-value (D-02): proper noun
    title: { pt-BR: "Engenheira de Software Sênior", en: "Senior Software Engineer" }   # D-02: titles ARE localized
    start_date: "2022-03"          # QUOTED — Pitfall 1
    end_date: null
    description: { pt-BR: "...", en: "..." }
    impacts:                       # D-08: embedded per experience
      - action:  { pt-BR: "Implementou pipeline RAG...", en: "Implemented RAG pipeline..." }
        metric:  { pt-BR: "-40% no tempo de resposta", en: "-40% response time" }
        context: { pt-BR: "...", en: "..." }
skills:                            # D-09: categorized groups, plain tech names
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

Hard requirements: every localized field carries BOTH `pt-BR` and `en` (D-17 — test SC4 asserts this); Markdown body stays minimal/unused (D-05); every key used here MUST be declared in `models.py` or `extra='forbid'` fails its own file (Pitfall 3).

---

### `backend/app/profile/models.py` (model, transform)

**Pattern source:** RESEARCH.md Pattern 1 (lines 225–263) + Code Examples schema skeleton (lines 499–540)

**Core pattern — strict base + localized maps + base-language enforcement** (all verified empirically on pydantic 2.13.5):

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date

Language = Literal["pt-BR", "en"]
BASE_LANGUAGE: Language = "pt-BR"          # D-04
LocalizedText = dict[Language, str]        # D-01

class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")            # D-10 — inherited by ALL models (Pitfall 3: EVERY model, no exceptions)

def _date_to_str(v: object) -> object:
    return v.isoformat()[:7] if isinstance(v, date) else v   # Pitfall 1: unquoted YAML dates arrive as date objects

class Impact(_Strict):
    action: LocalizedText
    metric: LocalizedText
    context: LocalizedText | None = None

class Experience(_Strict):
    company: str                                 # single-value (D-02)
    title: LocalizedText                         # D-02: job titles localized
    location: str | None = None
    start_date: str
    end_date: str | None = None
    description: LocalizedText
    impacts: list[Impact] = []                   # D-08 embedded
    _norm_dates = field_validator("start_date", "end_date", mode="before")(_date_to_str)
```

**Base-language rule (D-03)** — a model validator, empty `loc` on failure (Pitfall 8):

```python
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
```

Verified behaviors to preserve: unknown language key (`pt-PT`) fails with `type='literal_error'`, `loc=('values', 'pt-PT', '[key]')`; missing base language surfaces as `type='value_error'` with **empty loc**. Mixin validator composition is [ASSUMED] (A4) — the `test_base_language_required` test catches it immediately; fallback is duplicating the validator per model (verified primitive). The research skeleton left `education/skills/certifications/languages/projects` as `list[dict]` for brevity — **the planner must split these into proper `_Strict` models** (e.g., `SkillGroup{category: str, items: list[str]}`), each with its own `extra_forbidden` test per Pitfall 3.

---

### `backend/app/profile/loader.py` (service, file-I/O + transform)

**Pattern source:** RESEARCH.md Pattern 2 (lines 265–299)

Fail-fast loader — every failure mode caught, converted to `ProfileError` naming the exact file; NO caching (D-15: called fresh on every request):

```python
import yaml, frontmatter
from pydantic import ValidationError

class ProfileError(Exception):
    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw                       # terminal-only detail (D-13/D-14)

def load_profile(path: Path = CONTENT_DIR / "profile.md") -> Profile:
    try:
        post = frontmatter.load(str(path))   # encoding='utf-8' is the verified default (Pitfall 7: pass it explicitly anyway)
    except FileNotFoundError:
        raise ProfileError(f"Perfil não encontrado: {path}", f"FileNotFoundError: {path}")
    except yaml.YAMLError as exc:            # verified: yaml.parser.ParserError is a YAMLError subclass
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

Anti-pattern guard: no `lru_cache`, no module-level singleton — violates D-15.

---

### `backend/app/profile/errors.py` (utility, transform)

**Pattern source:** RESEARCH.md Pattern 3 (lines 301–332)

Type→PT-BR map over the exactly five producible error types (all observed empirically) plus `loc`-tuple rendering to `experiences[2].data_fim`-style paths (D-14):

```python
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
    return out or "estrutura do perfil"   # Pitfall 8: model_validator errors have EMPTY loc

def render_errors_ptbr(exc: ValidationError) -> str:
    lines = [f"Erro no perfil: {PROFILE_PATH}"]
    for e in exc.errors(include_url=False):
        msg = _PTBR_BY_TYPE.get(e["type"], e["msg"])
        lines.append(f"  • {render_loc(e['loc'])} — {msg or e['msg']}")
    return "\n".join(lines)
```

---

### `backend/app/routes/profile.py` + `backend/app/main.py` (route/controller, request-response)

**Pattern source:** RESEARCH.md Pattern 4 (lines 334–353) + Pattern 5 (lines 355–382)

**API contract — status object, never 500** (D-12/D-13/D-15). Broken profile is a UI-rendered state; raw detail goes to terminal only:

```python
@app.get("/api/profile")
def get_profile():
    try:
        profile = load_profile()             # D-15: fresh load per request, no cache
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

**Mount-last rule** (Pitfall 5 — `app.mount("/")` matches every path; API routes registered AFTER the mount become unreachable):

```python
from fastapi.staticfiles import StaticFiles
if FRONTEND_DIST.exists():   # guard so dev-only sessions don't crash at import
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="spa")
```

This tail belongs in `main.py` after ALL route registrations. Use the classic documented mount, not `app.frontend()` (exists in 0.141.1 but under-documented — RESEARCH Open Question 1).

---

### `backend/app/config.py` (config)

**Pattern source:** RESEARCH.md Stack table (python-dotenv row) + Stack pattern "profile store" note

Tolerant `.env` read — app must RUN without the key present (Phase 1 never uses it):

```python
from dotenv import load_dotenv   # loads repo-root .env if present; never required
import os
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")   # tolerant: empty is fine in Phase 1
CONTENT_DIR = REPO_ROOT / "content"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
```

Never crash on missing key; key is read nowhere else in Phase 1 (ASVS V14 — see RESEARCH Security Domain).

---

### `frontend/vite.config.ts` (config)

**Pattern source:** RESEARCH.md Pattern 5 (lines 359–375), doc-cited vite.dev/config/server-options

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // 127.0.0.1, NOT localhost — Node ≥17 may resolve localhost to ::1 first
      // and uvicorn binds 127.0.0.1 → ECONNREFUSED (Pitfall 4)
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
```

Tailwind v4 is CSS-first: `@tailwindcss/vite` plugin + `@import "tailwindcss"` in `src/index.css`; NO `tailwind.config.js`.

---

### `frontend/src/main.tsx` + `frontend/src/api/client.ts` (provider/service, request-response)

**Pattern source:** RESEARCH.md Code Examples (lines 544–566), React Query v5 quick-start (doc-cited)

v5 shape — `useQuery` takes a single options object; initial-load state is `isPending`, NOT `isLoading` (Pitfall 9):

```tsx
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

`client.ts` should type the response as a discriminated union mirroring Pattern 4's contract: `{status:"ok", exemplo, perfil, completude}` | `{status:"erro", erros: string[]}`. No axios (STACK.md What-NOT-to-use) — native fetch only.

---

### `frontend/src/App.tsx` + 4 components (component group)

**Pattern source:** D-12 scope + Pattern 4 contract. No i18n framework — all PT-BR strings hardcoded in `constants/ui.ts` (STACK.md What-NOT-to-use).

Component responsibilities (each a pure projection of `GET /api/profile`):
- `App.tsx` — shell: header, nav placeholders for future modules, Perfil home
- `PlaceholderBanner.tsx` — visible iff `exemplo === true` ("dados de exemplo")
- `ErrorPanel.tsx` — renders `erros[]` lines verbatim from backend (already PT-BR, D-13/D-14); the UI never maps errors itself
- `CompletenessGrid.tsx` — section presence/counts from `completude` (D-12)
- `ProfilePreview.tsx` — resume-like render of `perfil` (D-12); localized display: pick `pt-BR` value (base language) from each localized map

---

### `backend/tests/` (test group)

**Pattern source:** RESEARCH.md Validation Architecture "Phase Requirements → Test Map" (lines 620–631)

- `conftest.py` — fixtures writing valid / typo'd (`experiance:`) / broken-YAML `profile.md` variants to pytest `tmp_path`
- `test_loader.py` — `test_example_profile_validates` (shipped file is valid), `test_malformed_yaml_loud` (ProfileError, not stack trace, names the file)
- `test_schema.py` — `test_unknown_key_rejected` (`extra_forbidden` naming exact key), `test_base_language_required` (missing `pt-BR` fails loudly), `test_example_fully_bilingual` (D-17), one `extra_forbidden` test per nested model (Pitfall 3)
- `test_api.py` — Starlette TestClient (needs httpx dev dep, A1): ok-shape and erro-shape of `GET /api/profile`
- `test_secrets.py` — subprocess `git check-ignore .env` exits 0 (SC5 / Pitfall 2)

Config lives in `backend/pyproject.toml` under `[tool.pytest.ini_options] testpaths=["tests"]`. Run: `cd backend && uv run pytest -q`.

---

### Root config files (`.gitignore`, `.env`, `.env.example`, `backend/.python-version`, `backend/pyproject.toml`)

**Pattern source:** RESEARCH.md Installation (lines 114–128) + Pitfalls 2 and 6

- `.gitignore` is the **repo's FIRST commit** (before any install): `.env`, `node_modules/`, `dist/`, `.venv/`, `__pycache__/`, `outputs/`
- `.env` scaffolded empty (`OPENROUTER_API_KEY=`), gitignored; `.env.example` committed with empty value
- `uv python pin 3.12` writes `backend/.python-version`; `requires-python = ">=3.12"` in pyproject (Pitfall 6 — uv otherwise picks managed 3.14.7)

## Shared Patterns

### Loud validation fail-fast (ProfileError everywhere)
**Source:** RESEARCH.md Pattern 2 — applies to `loader.py`, `routes/profile.py`, `errors.py`, `main.py`
Every profile failure funnels through one exception type carrying `{message_ptbr, raw}`; API returns 200 + erro-envelope; terminal gets `raw`; UI renders `message_ptbr` lines. No HTTP 500 for user-input problems (anti-pattern list).

### `extra='forbid'` on every model
**Source:** RESEARCH.md Pattern 1 + Pitfall 3 — applies to ALL models in `models.py`
Shared `_Strict(BaseModel)` base with `ConfigDict(extra="forbid")`; every nested model inherits it. One forgotten model silently re-enables typo-tolerance. Each nested model gets its own `extra_forbidden` test.

### Localized-map convention (D-01…D-04)
**Source:** RESEARCH.md Pattern 1 — applies to `models.py`, `content/profile.md`, `ProfilePreview.tsx`
`LocalizedText = dict[Literal["pt-BR","en"], str]`, base `pt-BR` required; narrative fields AND job titles localized; company/tech/dates/contact single-value. Preview components pick the base-language value for display.

### UTF-8 discipline on Windows (Pitfall 7)
**Source:** RESEARCH.md Pitfall 7 — applies to `loader.py`, any hand-written `open()`
Always `open(..., encoding="utf-8")`; pass `encoding="utf-8"` to `frontmatter.load` explicitly for self-documentation.

### PT-BR strings as hardcoded constants
**Source:** STACK.md What-NOT-to-use — applies to all frontend components
No i18n framework; `frontend/src/constants/ui.ts` holds every user-facing string.

### Scaffold order (Pitfall 2 + 6)
**Source:** RESEARCH.md Installation — applies to the whole phase
`.gitignore` first commit → backend via uv (pinned 3.12) → frontend via Vite template → schema/loader/errors trio → Perfil UI. Frontend gate: `npm run build` (tsc -b + vite build, A5); backend gate: `uv run pytest -q`.

## No Analog Found

All 26 files are greenfield — no application source exists in the repo (verified via `git ls-files`: only `.claude/CLAUDE.md` + `.planning/*` are tracked). Every file's pattern source is stated per-file above; the authoritative excerpts are RESEARCH.md Patterns 1–6, each empirically verified this session with the exact pinned versions. Planner should use those excerpts directly and the canonical docs cited in RESEARCH.md "Sources" for anything not covered.

## Metadata

**Analog search scope:** entire repo (`git ls-files` + directory listing) — confirmed no `frontend/`, `backend/`, `content/`, or any source file exists
**Files scanned:** all 30 tracked files (`.planning/` artifacts + `.claude/CLAUDE.md`); zero application source files
**Pattern extraction date:** 2026-09-25
**Pattern authority:** `01-RESEARCH.md` Patterns 1–6 (empirically verified: pydantic 2.13.5, python-frontmatter 1.3.0, fastapi 0.141.1, PyYAML 6.0.3, uvicorn 0.54.0)
