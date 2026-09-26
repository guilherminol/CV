---
phase: 03-resume-vertical-slice
reviewed: 2026-09-26T22:54:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - backend/app/llm/gateway.py
  - backend/app/llm/schemas.py
  - backend/app/main.py
  - backend/app/resume/__init__.py
  - backend/app/resume/coverage.py
  - backend/app/resume/facts.py
  - backend/app/resume/lint.py
  - backend/app/resume/pipeline.py
  - backend/app/routes/resume.py
  - backend/tests/test_coverage.py
  - backend/tests/test_llm_harness.py
  - backend/tests/test_resume_api.py
  - backend/tests/test_resume_grounding.py
  - backend/tests/test_resume_lint.py
  - backend/tests/test_resume_pipeline.py
  - backend/tests/test_resume_schema.py
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/components/KeywordsPanel.tsx
  - frontend/src/components/LintPanel.tsx
  - frontend/src/components/ResumeResult.tsx
  - frontend/src/components/StatusLine.tsx
  - frontend/src/constants/ui.ts
  - frontend/src/pages/CurriculoHome.tsx
  - prompts/resume-experiencias.md
  - prompts/resume-skills.md
  - prompts/resume-summary.md
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-09-26T22:54:00Z
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

Reviewed the Phase 3 resume vertical slice end to end: the LLM gateway and wire schemas, the resume pipeline (facts → lint → 3 section stages → coverage), the two API routes, the frontend Currículo screen, and the three prompt files. Cross-checked the backend envelope contract against `frontend/src/api/client.ts`, the prompt files against the grounding-discipline tests, and the coverage/lint matchers against their test tables.

Evidence gathered: the offline suite passes (183 passed, 7 llm-marked deselected via `uv run pytest`), `tsc -b` is clean, and pattern scans found no hardcoded secrets, debug artifacts, empty catches, or raw-HTML/eval paths. The security posture is solid: pasted JD flows only as user-message data (T-02-01), all LLM output renders as JSX text children, stage names are validated before any path is built, and runs.jsonl stays metadata-only. The all-or-nothing envelope contract is correctly implemented and tested.

The defects found are concentrated in two areas: (1) the frontend's React Query usage silently violates the phase's own lint spend bound (T-03-10) via library defaults the code never overrides, and (2) the honest coverage checklist under-reports because the coverage input excludes the generated experience `title`/`company` strings. Plus one avoidable paid-call ordering flaw in the lint pipeline path.

## Warnings

### WR-01: React Query defaults trigger unrequested paid lint calls on window focus and on failure

**File:** `frontend/src/main.tsx:8`, `frontend/src/pages/CurriculoHome.tsx:39,87-91`
**Issue:** The `QueryClient` is created with no `defaultOptions`, so TanStack Query v5 defaults apply to the lint query: `refetchOnWindowFocus: true`, `refetchOnReconnect: true`, `retry: 3`, `staleTime: 0`. `fetchResumeLint` is a real paid LLM call (keyword extraction on OpenRouter). Once the debounced JD reaches 80 chars, every alt-tab back into the browser refetches the (always-stale) lint query — a new paid extraction per window focus — and any thrown fetch failure is retried up to 3 more times (each retry re-running the gateway's own up-to-3-attempt loop server-side). This directly contradicts the code's own invariant, stated at `CurriculoHome.tsx:39`: "one lint call per settled typing state (T-03-10 bound)". StrictMode's dev double-mount adds a second call for the first settled state.
**Fix:** Disable the network-lifecycle refetches and retries for this query (or globally for paid queries):

```tsx
// CurriculoHome.tsx — scoped option is enough
const lintQuery = useQuery({
  queryKey: ['resume-lint', debouncedTrimmed],
  queryFn: () => fetchResumeLint(debouncedTrimmed),
  enabled: lintReady,
  retry: false,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
  staleTime: Infinity, // one fetch per distinct debounced JD
})
```

### WR-02: `run_lint_only` pays for extraction before checking the profile it depends on

**File:** `backend/app/resume/pipeline.py:51-55`
**Issue:** `run_lint_only` calls `run_stage(EXTRACTION_STAGE, ...)` (the paid OpenRouter call) first and only then calls `load_profile()` (line 55). With a broken/missing `content/profile.md`, the paid extraction completes and its result can never be delivered — `ProfileError` propagates and the route returns the erro envelope. The gerar path gets this right: `run_resume_pipeline` loads the profile first (`pipeline.py:75`) before any stage call. The inconsistency means POST `/api/resume/lint` is the only reachable path that spends money on a run that cannot succeed.
**Fix:** Load the profile before the extraction call:

```python
def run_lint_only(jd_text, runs_log=None, client=None) -> dict:
    profile = load_profile()  # fail fast before any spend
    extraction = run_stage(EXTRACTION_STAGE, jd_text, "pt-BR", runs_log=runs_log, client=client)
    keywords = extraction.keywords
    avisos = lint_jd_tied(profile, keywords)
    ...
```

### WR-03: Coverage checklist omits generated `title`/`company`, so title keywords read "ausente" while visibly present

**File:** `backend/app/resume/pipeline.py:103-107`
**Issue:** The generated-text corpus fed to `classify_coverage` is resumo + experience **bullets** + habilidades only. The `title` and `company` fields the experiencias stage generated — and that `ResumeResult` renders in the assembled card — are excluded. A `titulos_de_vaga` keyword (e.g. "Data Engineer") that the model faithfully echoed into the generated experience title is reported `ausente`, and the UI tells the user that keyword "does not appear in the currículo" while it is displayed on screen. This is a false negative in the honest checklist: the input still honors the "generated sections only" contract (titles/companies ARE generated content — including them does not reintroduce the profile-passthrough problem pinned at `test_resume_pipeline.py:446-458`), so the omission is not required by D-02. No test pins titles either way; the offline test's "Engenheiro de Dados" keyword silently reads `ausente` despite "Engenheira de Dados" being in the canned generated output.
**Fix:**

```python
generated_text = "\n".join(
    [summary.resumo]
    + [
        line
        for entry in experiencias.experiencias
        for line in (entry.title, entry.company, *entry.bullets)
    ]
    + list(skills.habilidades)
)
```

### WR-04: Lint query fetch-level failure is silently swallowed — the feature vanishes with no feedback

**File:** `frontend/src/pages/CurriculoHome.tsx:87-91,207-219`
**Issue:** The lint panel only renders when `lintQuery.data` exists (status `ok` or `erro` envelopes). When the fetch itself throws (server down, or a non-200 such as an unexpected backend exception), `lintQuery.data` stays undefined and `lintQuery.isError` is never consulted, so after retries exhaust, the Zone 2 lint region renders nothing at all. The user cannot distinguish "check passed, no avisos shown yet" from "the check failed" — for a feature whose entire output is user-facing avisos, a silent no-op failure is a missing error-handling path (the gerar path handles its fetch-level failure explicitly at lines 104-108; the lint path has no equivalent).
**Fix:** Render a minimal inline notice for the error state, mirroring the gerar pattern:

```tsx
{lintReady && lintQuery.isError && (
  <p className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
    Não foi possível analisar a vaga — o detalhe técnico aparece no terminal do servidor.
  </p>
)}
```

## Info

### IN-01: Gateway malformed-response guard does not cover `AttributeError` on the choice shape

**File:** `backend/app/llm/gateway.py:173-174`
**Issue:** The CR-01 containment extracts content via `choices[0].message.content if choices else None`. A non-empty `choices` whose elements lack `.message` (or a non-subscriptable `choices` object) raises an uncaught `AttributeError`/`TypeError` outside the try block. The real OpenAI SDK always provides the shape, so this is only reachable via non-conforming injected clients — but the comment claims the path "must NEVER escape as a raw IndexError/TypeError" while one such escape remains.
**Fix:** `content = getattr(getattr(choices[0], "message", None), "content", None) if isinstance(choices, list) and choices else None` (or wrap the extraction in the same containment path).

### IN-02: Education date range renders a leading separator when `start_date` is null

**File:** `frontend/src/components/ResumeResult.tsx:202-206`
**Issue:** `dateRange(ed.start_date ?? '', ed.end_date)` renders `" – 2017-12"` when only `end_date` exists. The backend facts serializer handles this exact case separately (`facts.py:106-110` emits `conclusão: {end}`); the frontend does not.
**Fix:** Branch like the backend: `ed.start_date ? dateRange(ed.start_date, ed.end_date) : ed.end_date`.

### IN-03: "Gerar novamente" bypasses the ≥80-character CTA gate

**File:** `frontend/src/components/ResumeResult.tsx:165-172` + `frontend/src/pages/CurriculoHome.tsx:111-113,262`
**Issue:** `onRegenerar={gerarAgora}` is only disabled while pending; it does not re-check `trimmed.length < JD_MIN_CHARS`. If the user shortens the JD below 80 chars while a result is mounted, clicking "Gerar novamente" sends an under-minimum body, gets a 422, and surfaces the generic fetch-failure panel with an empty `erros` list — while the form's own CTA is correctly disabled. Inconsistent gating, misleading error surface.
**Fix:** Gate the regenerate handler the same way (disable the button when `trimmed.length < JD_MIN_CHARS`, or no-op with the same hint).

### IN-04: Cross-module import of underscore-private matcher primitives

**File:** `backend/app/resume/lint.py:23`
**Issue:** `from app.resume.coverage import _fold, _term_pattern` reaches into `coverage`'s private namespace. The docstring documents this as deliberate (one matcher, two inputs), but the underscore contract means a future refactor of `coverage` internals can silently break the JD lint with no import-level signal.
**Fix:** Promote the two functions to public names (`fold_text`, `term_pattern`) in `coverage.py` (or extract to a small `matchers.py`) and update both importers.

---

_Verified during review: offline suite green (183 passed, 7 deselected), `tsc -b` clean, no secrets/debug artifacts/empty catches, prompt files satisfy the grounding-contract tests, and the backend envelope key sets match `client.ts` types exactly._

_Reviewed: 2026-09-26T22:54:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
