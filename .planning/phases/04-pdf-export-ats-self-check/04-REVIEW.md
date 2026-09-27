---
phase: 04-pdf-export-ats-self-check
reviewed: 2026-09-27T12:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/app/export/__init__.py
  - backend/app/export/errors.py
  - backend/app/export/render.py
  - backend/app/export/pdf.py
  - backend/app/export/gate.py
  - backend/app/export/selfcheck.py
  - backend/app/routes/export.py
  - backend/app/main.py
  - backend/pyproject.toml
  - backend/tests/test_export_gate.py
  - backend/tests/test_export_api.py
  - frontend/src/components/ExportZone.tsx
  - frontend/src/components/SelfCheckPanel.tsx
  - frontend/src/api/client.ts
  - frontend/src/constants/ui.ts
  - frontend/src/pages/CurriculoHome.tsx
findings:
  critical: 2
  warning: 2
  info: 7
  total: 11
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-09-27T12:00:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

The export pipeline is well-engineered in its seams: strict `extra=forbid` request validation, the html-escape-everything discipline (pinned by `test_render_html_escapes_hostile_strings`), the pdf_base64-only-after-gate.ok ordering, the sync-`def`/Playwright seam, the D-15 no-LLM structural pins, and the D-03 single-source HEADINGS map are all real and verified against the cross-module code (coverage.py, profile/models.py, llm/schemas.py).

However, the parse-back gate has two defects that **reject valid exports outright**, both masked by the test fixture: the persona (`conftest.full_profile()`) populates every D-07 section and uses only lowercase accented text, so the shipped tests never exercise a profile with an empty passthrough section or uppercase accented text. Both failure modes were reproduced empirically against `check_extracted_text` during this review:

1. Any profile with an empty `education`/`certifications`/`languages`/`projects` list (all default to `[]` in `Profile`) produces a PDF without the corresponding heading — which the gate then demands unconditionally — so **every export fails** with "Seção X fora de ordem no PDF."
2. A legitimate uppercase "Ã" (e.g., "SÃO PAULO" in the contact line — common in Brazilian addresses) trips the mojibake sentinel, so byte-perfect extractions fail with "Acentos corrompidos."

Since the gate is an unconditional wall (T-04-04: bytes never cross on gate failure), either defect makes the product unusable for the affected profiles, with a misleading error message.

## Critical Issues

### CR-01: Gate demands all 7 section headings but the template hides empty passthrough sections — profiles missing education/certifications/languages/projects can never export

**File:** `backend/app/routes/export.py:109` (root cause spans `backend/app/export/render.py:222-273` and `backend/app/export/gate.py:143-149`)

**Issue:** `_expected_doc` builds the heading expectation for **all** `section_keys` unconditionally:

```python
headings=tuple((key, labels[key]) for key in section_keys),
```

But `_sections_content` (render.py) only renders passthrough sections when their source list is non-empty (`if perfil.education:`, `if perfil.certifications:`, `if perfil.languages:`, `if perfil.projects:` — lines 221, 239, 249, 261), and `Profile` defaults all four to `[]`. For such a profile the PDF legitimately lacks e.g. the "Formação" heading, `_scan_headings` returns `(None, "formacao")`, and the gate rejects with `Seção formacao fora de ordem no PDF.` — no PDF is ever delivered. Reproduced during review:

```
ok: False | erros: ['Seção formacao fora de ordem no PDF.']
```

The tests cannot catch this because `conftest.full_profile()` populates all 7 sections; `test_gate_passes_real_pdf` and the real-envelope route test therefore pass while every real partial profile fails. Note the frontend contract itself disagrees with the route: `SelfCheckPanel.tsx:95-97` documents "one row per **present** section — never empty," confirming the all-7 `ExpectedDoc` is the drift.

**Fix:** Derive the expected headings from the same presence logic the template uses. Export a pure helper from render.py (single source of truth) and use it in both consumers:

```python
# render.py
def rendered_section_keys(perfil, secoes) -> tuple[str, ...]:
    keys: list[str] = ["resumo", "experiencias"]  # generated: always render
    if perfil.education:
        keys.append("formacao")
    keys.append("habilidades")  # generated: always render
    if perfil.certifications:
        keys.append("certificacoes")
    if perfil.languages:
        keys.append("idiomas")
    if perfil.projects:
        keys.append("projetos")
    return tuple(keys)
```

Then in `routes/export.py::_expected_doc`:

```python
rendered = rendered_section_keys(payload.perfil, payload.secoes)
headings=tuple((key, labels[key]) for key in rendered),
```

Better still, refactor `_sections_content` to iterate `(key, blocks)` pairs and derive both the HTML and `rendered_section_keys` from that one traversal so template and gate cannot drift. Update `test_export_api.py:360` (`[row["id"] for row in selfcheck["ordem"][1:]] == list(section_keys)`) and `_PASSING_GATE.ordem_rows` to the filtered set, and add a failing-profile regression test (persona minus education/certifications must export ok).

### CR-02: Mojibake sentinel "Ã" false-positives on legitimate uppercase accented text — byte-perfect exports rejected as corrupted

**File:** `backend/app/export/gate.py:60` (checked at `gate.py:292-294`)

**Issue:** `_MOJIBAKE_SENTINELS = ("\ufffd", "Ã", "â€")` treats any standalone "Ã" (U+00C3) as proof of UTF-8→Latin-1 mangling. But "Ã" also occurs legitimately as the uppercase form of "ã" in all-caps Portuguese text — "SÃO PAULO", company names, addresses written in caps. Chromium's extraction preserves case, so the sentinel fires on perfectly intact text. Reproduced during review with a clean extraction containing `SÃO PAULO, SP`:

```
ok: False | erros: ['Acentos corrompidos na camada de texto do PDF.']
```

Because the gate is an unconditional wall, a profile containing one uppercase accented word (extremely common in address lines) can never be exported, and the PT-BR message wrongly tells the user the accents are corrupted. The real mojibake signature is "Ã" **followed by another non-ASCII byte-mapping char** ("ão" → "Ã£o", where Ã precedes "£"); a legit uppercase Ã is followed by an ASCII letter.

**Fix:** Replace the bare-substring sentinel with the contextual pattern:

```python
_MOJIBAKE_A_TILDE = re.compile(r"Ã(?![A-Za-z])")  # Ã followed by non-letter = mangling
```

(Keep `\ufffd` and `â€` as-is — they never occur in legit PT-BR/EN text.) Add a regression test: `"SÃO PAULO, SP"` in the extracted text must pass check 4, while `"SÃ£o Paulo"` must still fail.

## Warnings

### WR-01: `join_experience_dates` collapses multiple stints at the same company to the last one — PDF prints wrong dates

**File:** `backend/app/export/render.py:127-136`

**Issue:** The join builds `dates_by_folded_company` as a dict keyed by folded company, so when the profile has two experiences at the same employer (career progression at one company — a normal resume shape), the comprehension silently keeps only the **last** entry's dates. Every generated entry for that company then renders the later stint's dates, and the earlier stint's real dates are silently replaced with factually wrong ones on a sendable document. This violates the module's own "no invented dates, ever" contract (it substitutes *someone else's* dates instead). The same keying means two `secoes.experiencias` entries with an identical company string also receive identical dates.

**Fix:** Group date ranges per folded company as a list and match positionally to the generated entries in order; leave an entry dateless when the match is ambiguous:

```python
from collections import defaultdict
ranges = defaultdict(list)
for exp in perfil.experiences:
    ranges[_fold(exp.company.strip())].append((exp.start_date, exp.end_date))
joined: dict[str, tuple[str, str | None]] = {}
consumed: dict[str, int] = defaultdict(int)
for exp in secoes.experiencias:
    bucket = ranges.get(_fold(exp.company.strip()))
    if bucket:
        idx = consumed[_fold(exp.company.strip())]
        if idx < len(bucket):
            joined[exp.company] = bucket[idx]
            consumed[_fold(exp.company.strip())] += 1
```

Add a test with two same-company profile entries asserting distinct dates per generated entry.

### WR-02: Lint fetch-level failure renders nothing — no panel, no hint, unlike gerar/exportar

**File:** `frontend/src/pages/CurriculoHome.tsx:258-269` (pre-existing phase-3 code, inside the reviewed file)

**Issue:** The lint zone handles only the 200-envelope branch (`lintQuery.data.status === 'erro'`). When the `fetchResumeLint` call **throws** (server down, non-200 → `lintQuery.isError`), `lintQuery.data` stays `undefined` and nothing renders — the user gets silent no feedback in Zone 2. Both mutations in the same file handle fetch-level failure with the `erros=[]` panel convention (`gerar.onError`, `exportar.onError`), so the failure surface is inconsistent.

**Fix:**

```tsx
{lintReady && lintQuery.isError && (
  <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
    <p className="text-sm text-red-700">{/* generic hint line; raw detail is terminal-only */}</p>
  </div>
)}
```

## Info

### IN-01: `html_to_pdf` blames the browser install for every failure

**File:** `backend/app/export/pdf.py:58-59`

**Issue:** The single `except Exception` maps *all* failures — including `set_content` timeouts and `page.pdf()` errors — to "O navegador de renderização não está instalado. Execute `uv run playwright install chromium`…". A user hitting a non-launch failure is told to run an install that will not help; the real cause is terminal-only (D-08), so the envelope's remediation advice is wrong for that class.

**Fix:** Either branch the message on the failure stage (launch vs. render) or soften to a general "Falha ao renderizar o PDF — verifique o terminal" with the install hint reserved for lookup/launch errors (`exc` type or message sniffing for `Executable doesn't exist`).

### IN-02: Contact check misattributes a missing first heading to a contact failure

**File:** `backend/app/export/gate.py:193-197`

**Issue:** `contato_primeiro` requires `first_heading_pos >= 0`; if the *Resumo* heading is absent from the extraction while the contact is present and genuinely first, the gate returns `MSG_CONTATO_FORA_DO_TOPO` — naming the wrong check (the heading-order check is the real failure). Diagnostic-accuracy issue only; the export is still correctly rejected.

**Fix:** Only apply the `min(contact_positions) < first_heading_pos` comparison when `first_heading_pos >= 0`; otherwise skip to the heading check (which will fail with the correct `msg_secao_fora_de_ordem` line).

### IN-03: `downloadPdf` revokes the object URL synchronously after `click()`

**File:** `frontend/src/api/client.ts:251`

**Issue:** `URL.revokeObjectURL(url)` runs in the same task as `anchor.click()`. This works in Chromium (the documented single-user target) but revocation before the download commits is known to abort downloads in other engines (historically Firefox). Low risk given the Chromium-only posture.

**Fix:** Defer revocation: `setTimeout(() => URL.revokeObjectURL(url), 0)` (or revoke on a subsequent task) to be engine-safe.

### IN-04: `PRIMARY_BUTTON_CLASSES` duplicated despite a "never redefined" comment

**File:** `frontend/src/components/ExportZone.tsx:12-13` (duplicate of `frontend/src/pages/CurriculoHome.tsx:49-50`)

**Issue:** The comment says the CTA "reuses CurriculoHome's PRIMARY_BUTTON_CLASSES verbatim (never redefined)" — but the string is copy-pasted into a second module-local constant. Two identical 200-char class strings can drift silently.

**Fix:** Move the constant to `constants/ui.ts` (alongside the other pinned class conventions) and import it in both files.

### IN-05: Router-order test depends on `frontend/dist` existing

**File:** `backend/tests/test_export_api.py:289-297` (with `backend/app/main.py:24`)

**Issue:** `test_export_router_registered_before_spa_mount` asserts a Mount exists at `/`, but `main.py` only mounts when `FRONTEND_DIST.exists()`. On a fresh clone (no frontend build) the test fails for an environment reason, not a code regression. Passes in this working copy only because `frontend/dist` happens to exist.

**Fix:** `@pytest.mark.skipif(not FRONTEND_DIST.exists(), reason="SPA not built")` (importing `FRONTEND_DIST` from `app.config`), or guarantee the build in CI before backend tests.

### IN-06: Wire bounds exist only for `resumo`; experience/skills strings unbounded

**File:** `backend/app/routes/export.py:81-83`

**Issue:** `ExportarSecoes` floors the three sections at `min_length=1` and caps only `resumo` (`max_length=8000`). `company`, `title`, `bullets`, and `habilidades` items have no length caps, and neither do `Perfil` fields — arbitrary client JSON can push multi-megabyte strings into the Chromium render. Acceptable risk for a localhost single-user tool, but inconsistent with the stated JD_MAX_LENGTH "wire-bound guards" precedent.

**Fix:** Add generous `max_length` caps on `ExperienciaGerada` fields and `habilidades` items (or a request-level size guard), mirroring the RESUMO_MAX_LENGTH rationale.

### IN-07: `test_pdf_bytes_never_written_to_disk` checks a narrower property than it pins

**File:** `backend/tests/test_export_gate.py:192-195`

**Issue:** The assertion is `'"wb"' not in source`, which misses `Path(...).write_bytes(...)`, `open(..., 'wb')` with single quotes, or `tempfile` writes. The pinned invariant ("PDF bytes stay in memory") is broader than what the check can catch, giving false confidence in a structural test.

**Fix:** Assert absence of a small denylist of write primitives in `app/export/` sources: `"write_bytes"`, `"shutil"`, `"open("`, `".pdf\""` path construction — or accept the limitation and note it in the docstring.

---

_Verified clean during this review (no action needed): every data-string interpolation in `build_resume_html` passes through `esc()` (pinned by test); `pdf_base64` is only placed in the response after `gate.ok` (pinned); raw gate/exception detail reaches only the terminal log (pinned via caplog); router-before-mount and sync-handler structural pins work against the FastAPI ≥0.141 nesting; `_fold`/`_term_pattern` are imported, not re-implemented; `LocalizedText` is a plain dict so `_tlang`'s `.get()` chain is valid; `atob → Uint8Array` byte handling in `downloadPdf` is correct._

_Reviewed: 2026-09-27T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
