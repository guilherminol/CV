# Phase 2: LLM Generation Core - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** 11 (new/modified)
**Analogs found:** 8 / 9 code files (all Phase 1 files verified git-tracked via `git ls-files`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/llm/__init__.py` | package marker | — | `backend/app/profile/` (package convention) | exact |
| `backend/app/llm/prompts.py` (prompt loader) | service (file I/O + validation) | file-I/O | `backend/app/profile/loader.py` | exact |
| `backend/app/llm/schemas.py` (keyword schema + strict JSON Schema dict) | model | transform | `backend/app/profile/models.py` | exact |
| `backend/app/llm/errors.py` (LLMError + PT-BR rendering) | utility | — | `backend/app/profile/loader.py:22-27` (ProfileError) + `backend/app/profile/errors.py` | exact |
| `backend/app/llm/gateway.py` (OpenRouter call + retry loop) | service | request-response | none — new capability; error/retry skeleton from RESEARCH.md Pattern 3 | none |
| `backend/app/llm/logging.py` (JSONL writer) | utility | file-I/O (append) | `backend/app/config.py` path pattern; no existing writer | partial |
| `backend/app/config.py` (MODIFY: model slug, PROMPTS_DIR, RUNS_LOG, retry cap) | config | — | itself (`backend/app/config.py:13-21`) | exact |
| `backend/pyproject.toml` (MODIFY: `llm` marker + addopts) + `.gitignore` (MODIFY: `logs/`) | config | — | itself (`backend/pyproject.toml:14-16`) | exact |
| `prompts/keyword-extraction.md` | content (user-edited) | file-I/O | `content/profile.md` format (frontmatter + body), via loader | role-match |
| `backend/tests/test_prompt_loader.py`, `test_gateway.py`, `test_keyword_schema.py` | test | — | `backend/tests/test_loader.py` + `backend/tests/conftest.py` | exact |
| `backend/tests/test_llm_harness.py` (`-m llm`) | test (integration) | request-response (real API) | `backend/tests/test_secrets.py` (repo-root guard pattern); skipif per RESEARCH Pattern 6 | role-match |

No new FastAPI routes are expected (RESEARCH Open Question 2 recommends none) — if one is added, `backend/app/routes/profile.py` is the exact envelope analog and `backend/app/main.py:15-16` fixes registration order.

## Pattern Assignments

### `backend/app/llm/prompts.py` (service, file-I/O)

**Analog:** `backend/app/profile/loader.py` (mirror it structurally — D-08/RESEARCH Pattern 4)

**Imports pattern** (loader.py lines 9-17):
```python
from pathlib import Path

import frontmatter
import yaml
from pydantic import ValidationError

from app.config import CONTENT_DIR
from app.profile.errors import render_errors_ptbr
```
For prompts.py: `from app.config import PROMPTS_DIR` plus the new `PromptError` from `app/llm/errors.py`.

**Fail-fast core pattern** (loader.py lines 29-54) — copy this exact try/except ladder, swapping Profile→Prompt frontmatter model and the PT-BR message prefix:
```python
def load_profile(path: Path | None = None) -> Profile:
    """Read + validate content/profile.md. Fresh on every call (D-15).

    The default path resolves at CALL time (not def time) so tests can retarget
    the loader without touching the real content/ directory.
    """
    if path is None:
        path = PROFILE_PATH
    try:
        post = frontmatter.load(str(path), encoding="utf-8")  # Pitfall 7: explicit UTF-8
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
        return Profile.model_validate(post.metadata)
    except ValidationError as exc:
        raw = "\n".join(str(e) for e in exc.errors(include_url=False))
        raise ProfileError(render_errors_ptbr(exc, path), raw)
```
Key carry-overs: (1) explicit `encoding="utf-8"` (Pitfall 7, Windows); (2) default-path-at-call-time so tests retarget via `tmp_path`; (3) NO caching — fresh read per call (D-08/SC1). Difference: for prompt files the Markdown **body IS the payload** (system prompt, D-07), not just frontmatter — return both validated frontmatter model and `post.content`.

---

### `backend/app/llm/schemas.py` (model, transform)

**Analog:** `backend/app/profile/models.py`

**Reuse verbatim** (models.py lines 24-32):
```python
Language = Literal["pt-BR", "en"]
BASE_LANGUAGE: Language = "pt-BR"  # D-04
LocalizedText = dict[Language, str]  # D-01


class _Strict(BaseModel):
    """Base for ALL profile models — unknown keys fail loudly (D-10)."""

    model_config = ConfigDict(extra="forbid")
```
Import `Language`/`LocalizedText` from `app.profile.models`; re-declare `_Strict` locally (or import if exposed) so every new model inherits `extra="forbid"` (D-06). Keyword shape per RESEARCH Code Examples: `Keyword(canonical: str, aliases: list[str] = [], pt: str | None = None, en: str | None = None)` and `KeywordExtraction` with the D-10 fixed category set (`competencias | ferramentas | titulos_de_vaga | certificacoes` — exact tokens are a planner decision, A6). Module docstring style: models.py lines 1-16 documents every decision ID — mirror that convention.

**Second artifact in this file:** the hand-maintained strict JSON Schema dict (RESEARCH Pattern 2) plus a drift-lock test asserting the dict matches `KeywordExtraction.model_json_schema()` properties. Do NOT send `model_json_schema()` raw (anti-pattern; Pitfall 1).

---

### `backend/app/llm/errors.py` (utility)

**Analog:** `backend/app/profile/loader.py:22-27` (error class) + `backend/app/profile/errors.py` (rendering)

**Error class shape** — copy exactly, rename:
```python
class ProfileError(Exception):
    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw  # terminal-only detail (D-13/D-14)
```

**PT-BR rendering reuse** (errors.py lines 23-38 and 69-74): `_PTBR_BY_TYPE` map + `_UNKNOWN_TYPE_TEMPLATE` fallback + `render_errors_ptbr` bullet-line output. For LLM responses the same Pydantic types recur (`extra_forbidden`, `missing`, `string_type`, `list_type`, `literal_error`) — either import `render_errors_ptbr`/`_ptbr_message` directly or extend the map with a "Erro na geração" header variant. Never let English Pydantic prose reach the UI path (WR-02: strip "Value error, " prefix — errors.py lines 41-47).

---

### `backend/app/llm/gateway.py` (service, request-response) — NO ANALOG

No existing code calls external APIs. Build from RESEARCH.md Patterns 1 and 3 (openai SDK, `base_url="https://openrouter.ai/api/v1"`, `response_format={"type": "json_schema", "strict": True, ...}`, `extra_body={"provider": {"require_parameters": True}}` — body field, NOT header). Constraints pinned by decisions: model slug from config only (D-01/D-02), prompt body as system message + composed runtime inputs as user message (D-07), retry on ValidationError only with assistant output + PT-BR correction request appended before retrying (D-03/D-04, Pitfall 7), log line per attempt (D-14), loud `LLMError(message_ptbr, raw)` at exhaustion. Offline tests monkeypatch the SDK client — no new mocking dependency (A3).

---

### `backend/app/llm/logging.py` (utility, file-I/O append) — PARTIAL ANALOG

No existing file-writer in the codebase (backend is read-only over `content/`). Follow: explicit `encoding="utf-8"` on open (Pitfall 7 — same discipline as loader.py:38), `json.dumps(..., ensure_ascii=False)`, append mode, create `logs/` on first write, gitignore `logs/` in the same task (Pitfall 8). Field set is discretion (D-13): `ts, stage, model, language, attempt, status, prompt_tokens, completion_tokens, total_tokens, cost, latency_ms, error` — metadata only, no prompt/response content (A5).

---

### `backend/app/config.py` (MODIFY — config)

**Analog:** itself, lines 12-21 — extend the existing block, same style:
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CONTENT_DIR = REPO_ROOT / "content"
```
Additions (RESEARCH Code Examples): `PROMPTS_DIR = REPO_ROOT / "prompts"`, `LOGS_DIR`/`RUNS_LOG`, `LLM_MODEL` (env-overridable slug, default per A1), `LLM_MAX_ATTEMPTS = 3` (D-04). Keep the tolerant key read as-is (harness guards with skipif, not config).

---

### `backend/pyproject.toml` (MODIFY — pytest markers) and `.gitignore` (MODIFY)

**Analog:** `backend/pyproject.toml:14-16`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```
Add (RESEARCH Pattern 6, Pitfall 6): `markers = ["llm: real OpenRouter API calls (spend) — run explicitly with -m llm"]` and `addopts = "-m 'not llm'"`. Dependency: `uv add --project backend openai`. `.gitignore`: add `logs/` (currently absent — RESEARCH Pitfall 8 verified).

---

### `prompts/keyword-extraction.md` (content file)

**Analog:** `content/profile.md` format (frontmatter + Markdown), parsed identically. Frontmatter keys (discretion per D-06): `id`, `temperature`, `max_tokens` — strict-validated so typo'd keys fail loudly naming the key. Body = system prompt verbatim, no `{{template}}` variables, no volatile data (D-07).

---

### Test files: `test_prompt_loader.py`, `test_keyword_schema.py`, `test_gateway.py`

**Analog:** `backend/tests/test_loader.py` + `backend/tests/conftest.py`

**Test structure pattern** (test_loader.py lines 23-29) — pytest.raises with dual assertions on both error channels:
```python
def test_malformed_yaml_is_loud_and_names_file(broken_yaml_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(broken_yaml_profile_path)
    msg = excinfo.value.message_ptbr
    assert "YAML do frontmatter inválido" in msg
    assert str(broken_yaml_profile_path) in msg  # SC2: the exact file is named
    assert excinfo.value.raw  # terminal-only detail preserved
```
Also mirror: section-divider comments per behavior, decision-ID comments on each assert, explicit `-> None` annotations.

**Fixture pattern** (conftest.py lines 98-108, 123-126) — write file variants into `tmp_path`, never the real `prompts/` directory; fresh deep copies per test:
```python
def _write_profile(directory: Path, meta: dict) -> Path:
    text = (
        "---\n"
        + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
        + "---\n\n"
        + "Perfil de teste.\n"
    )
    path = directory / "profile.md"
    path.write_text(text, encoding="utf-8")
    return path
```
Gateway tests: inject/monkeypatch a fake SDK client returning canned `json_schema` responses (happy, malformed→recovered, malformed→exhausted) and assert JSONL lines written per attempt.

### `test_llm_harness.py` (test, real API)

**Analog (structure):** `backend/tests/test_secrets.py:11` — `REPO_ROOT = Path(__file__).resolve().parents[2]` for repo-root-relative paths. Marker + skipif guard per RESEARCH Pattern 6:
```python
@pytest.mark.llm
@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY ausente")
```
Fixtures: realistic sample JD + career objective in BOTH EN and PT-BR (SC2). Wave 0 should include a slug-probe test (Open Question 1).

## Shared Patterns

### Fail-loud error contract (PT-BR message + raw terminal detail)
**Source:** `backend/app/profile/loader.py:22-27`, consumed at `backend/app/routes/profile.py:23-25`
**Apply to:** `llm/errors.py`, gateway, every raise in `app/llm/` (D-03, D-13, D-14):
```python
except ProfileError as exc:
    logger.error("Falha ao carregar perfil:\n%s", exc.raw)  # raw detail → terminal (D-13)
    return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
```

### Strict Pydantic `extra="forbid"` everywhere
**Source:** `backend/app/profile/models.py:29-32`
**Apply to:** prompt frontmatter model, Keyword/KeywordExtraction schema — every model inherits `_Strict` (D-06/D-10).

### Explicit UTF-8 discipline
**Source:** `backend/app/profile/loader.py:38` ("Pitfall 7" comment)
**Apply to:** prompt loader reads, JSONL writer (`encoding="utf-8"`, `ensure_ascii=False`) — Pitfall 5 in this phase's research.

### No caching — fresh read per call
**Source:** `backend/app/profile/loader.py:29-36` docstring, `backend/app/routes/profile.py:22`
**Apply to:** prompt file loading (D-08/SC1) and profile loading before composing user messages.

### Config via `.env` + module constants, paths from REPO_ROOT
**Source:** `backend/app/config.py:12-21`
**Apply to:** all new config (slug, PROMPTS_DIR, RUNS_LOG, retry cap); key stays tolerant, required-in-practice only at real-call time.

### Router registration order (only if a route is added)
**Source:** `backend/app/main.py:15-16` — `app.include_router(...)` BEFORE the SPA StaticFiles mount (Pitfall 5).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/app/llm/gateway.py` | service | request-response | First external-API caller in the codebase — build from RESEARCH.md Patterns 1/3 (SDK call shape, retry loop) |
| `backend/app/llm/logging.py` | utility | file-I/O append | First file-writer (backend is read-only today) — only conventions (UTF-8, gitignore) carry over |

## Metadata

**Analog search scope:** `backend/app/**`, `backend/tests/**`, `backend/pyproject.toml`, `.gitignore`, repo root
**Files scanned:** 12 (8 tracked analogs verified via `git ls-files`)
**Pattern extraction date:** 2026-09-25
