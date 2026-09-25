# Pitfalls Research

**Domain:** LLM-powered ATS resume tailoring + LinkedIn optimization (personal tool, PT-BR/EN, PDF output, OpenRouter, Markdown/YAML master profile)
**Researched:** 2026-09-25
**Confidence:** HIGH for PDF/ATS mechanics, structured-output behavior, prompt-chaining, and multilingual findings (official docs + peer-reviewed papers); MEDIUM for keyword-stuffing penalties and LinkedIn limits (multiple independent secondary sources); LOW for hallucination-in-resume specifics (practitioner consensus, few direct studies — flagged inline).

Phase names below use a suggested logical decomposition — map them to the actual roadmap phases: **P1** Master profile & schema, **P2** Generation core (OpenRouter + prompts + structured output), **P3** Resume module (template + PDF export), **P4** Keyword optimization, **P5** LinkedIn module, **P6** Review flow & QA gates.

## Critical Pitfalls

### Pitfall 1: The PDF looks perfect on screen but extracts as garbage in the ATS

**What goes wrong:**
ATS parsers do not "see" the page — they extract the PDF text layer in content-stream creation order, which is whatever order the generating engine emitted glyphs, not visual reading order (PyMuPDF docs, HIGH confidence). Consequences with common resume layouts:
- **Two-column / sidebar layouts:** extraction is a global sort (y, then x) with no column awareness — left-column section headers interleave with right-column body text. A "Skills" heading gets glued to a job bullet from the other column.
- **Tables:** cell boundaries are dropped; cells flatten into run-on text, scrambling roles, dates, and skills.
- **Headers/footers:** repeated page headers/footers get injected mid-document or duplicated, polluting parsed name/phone/email fields.
- **Text as images/icons:** logos, icon fonts for contact symbols (the phone/email glyphs), charts, and skill-bar graphics carry no extractable text at all.
- **Creative section headings** ("My Journey", "Where I've Been"): the ATS looks for canonical headings (Work Experience, Education, Skills) and misclassifies or skips anything else (Novoresume/Indeed, MEDIUM confidence).
- **PT-BR-specific:** fonts without proper Latin-ext glyph subsets or with aggressive ligature/encoding handling can mangle ç, ã, õ, é on extraction even when they render fine — an English resume can pass a parse test while the PT-BR one silently corrupts.

**Why it happens:**
Developers validate the PDF visually ("it looks right in the browser") instead of validating what a text extractor returns. The PDF format simply has no concept of reading order; every layout decision that looks good in print is a bet that the extraction engine reconstructs it.

**How to avoid:**
1. **Enforce the Google-style constraints in the template itself, not just in docs:** single column, no tables, no text boxes, no header/footer regions, standard section headings, standard fonts (e.g., Roboto/Liberation Sans with Latin-ext coverage for PT-BR).
2. **Generate with a text-first PDF engine** (e.g., WeasyPrint/fpdf2/ReportLab in Python) where the text emission order is the template order — headless-Chrome print-to-PDF reorders via CSS layout and z-order and is riskier.
3. **Build an automated parse-back gate:** after every PDF export, extract text (pypdf/pdfplumber) and assert: contact fields appear first and once; each canonical section heading present; every job's company/title/dates co-occur; zero missing PT-BR accented characters; no text lost vs. the source JSON. Fail the export loudly if assertions break.
4. Run the parse-back test **in both languages** — PT-BR accents are a distinct failure surface.

**Warning signs:**
- Export preview looks right but copy-pasting from a PDF reader yields reordered text or missing accents.
- You can't answer "what does pdftotext return for this file?" without trying it.
- Template work happens in a visual editor (Chrome print CSS) before anyone writes an extraction test.

**Phase to address:**
P3 (Resume module / PDF export) — but define the parse-back test in P3's first task, before styling work starts.

---

### Pitfall 2: The LLM embellishes — inventing metrics, tools, titles, or dates not in the master profile

**What goes wrong:**
Asked to "optimize this experience for the job description," LLMs routinely add plausible-sounding specifics: a percentage improvement that was never measured, a technology the user merely touched, a scope inflation ("led" for "contributed to"), or an invented certification. The user reviews for tone, not fact-checkability, and sends a resume containing claims they can't defend in an interview. Employers do verify claims; fabricated content in professional documents has documented real-world consequences. (Confidence: LOW for direct resume-domain studies — this is practitioner consensus extrapolated from documented LLM hallucination behavior. Treat the risk as real regardless.)

**Why it happens:**
Instruction to "make it stronger/more relevant" conflicts with factual grounding; the model optimizes for persuasive text, not for truthfulness to source. It has no way to know which numbers are real, so it produces confident ones.

**How to avoid:**
1. **Ground generation in profile facts only:** the prompt passes only profile-derived bullets/claims for the target role, with an explicit rule "rephrase and recombine; never add numbers, technologies, dates, or responsibilities absent from the source."
2. **Post-generation fact diff:** programmatically compare generated bullets against the source profile claims — flag numbers, tech names, and superlatives that don't appear in the source, and surface them in the review UI as "not in your profile — verify or remove."
3. **Never ask the model for metrics.** If the user wants quantified impact, it comes from the master profile's `impacts` fields (the PROJECT.md schema already plans for impacts — make them first-class).
4. Keep the in-app reviewer as a **quality gate, not a formality**: show source-vs-generated side by side, not just the generated text.

**Warning signs:**
- Generated bullets contain numbers (%, R$, users, teams) you don't remember writing.
- Prompt logs show generic instructions like "improve this experience" without the source bullets attached.
- The review UI renders only the output, with no view of what the generation was grounded in.

**Phase to address:**
P2 (prompt design rules) + P6 (review flow with fact-diff surfacing).

---

### Pitfall 3: Keyword stuffing that reads as spam to recruiters and gains nothing with modern ATS

**What goes wrong:**
The obvious "optimization" is to inject every JD keyword at maximum density — cramming a skills line with 40 technologies, repeating "Kubernetes" in every bullet, or appending an invisible keyword dump. Modern ATS match contextually, not on raw frequency (MEDIUM confidence, Indeed/Novoresume), so stuffing adds no score; but the recruiter who reads the resume after the ATS filter sees unnatural text and rejects it — Indeed explicitly warns stuffed keywords "might be nonsensical" to the human reviewer. Hidden-text tricks are a red flag if ever detected.

**Why it happens:**
Keyword optimization is a stated requirement, and the naive implementation of "target extracted keywords" is "insert them everywhere." Without a coverage-vs-density model, the prompt over-fits.

**How to avoid:**
1. **Prompt for coverage, not density:** each priority JD keyword should appear naturally *at least once* in a truthful context (skills section or a bullet where the user actually used it); cap repetitions; forbid keyword lists that aren't mirrored in real experience.
2. **Only match keywords the profile can support:** keyword extraction step outputs JD keywords; a second step classifies each as covered (in profile — weave in) / adjacent (skill the user plausibly has — ask the user) / absent (do not insert). Never let the LLM insert an absent keyword.
3. **Include the exact JD phrasing variants** where legitimate (e.g., "CI/CD" and "continuous integration") — spelled-out plus acronym, per ATS guidance.
4. The parse-back/review flow (Pitfall 1/2) also catches this: a human reads the final text before export.

**Warning signs:**
- The generated skills section is longer than a work-experience entry.
- A term appears in 6+ bullets when the user used it in 1 role.
- The keyword module has no link between extracted JD keywords and profile evidence.

**Phase to address:**
P4 (keyword optimization) — design the coverage/absent classification into the pipeline, not as a later patch.

---

### Pitfall 4: PT-BR output quality — instruction drift, English bleed, and PT-PT/BR inconsistency

**What goes wrong:**
Multilingual instruction-following degradation is well documented: Marco-Bench-MIF measures a 25–35% instruction-following accuracy gap between high- and low-resource languages; M-IFEval and Multi-IF show adherence varies widely by language and degrades across turns (HIGH confidence, peer-reviewed). Practical failure modes for this project: the model writes the About section in PT-BR but slips into English mid-text; ignores format constraints (bullet counts, section order, character limits) more often in Portuguese; mixes PT-PT forms ("utilização", "telemóvel") with PT-BR ("uso", "celular"); or literal-translates tech jargon that Brazilian recruiters expect in English ("DevOps", "feature flag", "pair programming").
Secondary effect (HIGH confidence): tokenizer disparity — non-English text encodes to substantially more tokens (up to 15x across language pairs; PT typically ~1.5–2x English), so PT-BR runs cost more, are slower, and hit context limits sooner, silently truncating the JD or profile.

**Why it happens:**
Models are strongest in English; instruction-tuning is English-centric and cross-lingual transfer degrades factuality and format adherence. Prompts written and tested only in English get deployed untested against PT-BR.

**How to avoid:**
1. **Treat language as a structured input**, not a sentence in the prompt: a `language: "pt-BR"` field, plus few-shot examples *in the target language* (PT-BR examples for PT-BR runs).
2. **Keep a terminology glossary in the master profile:** which terms stay in English (technologies, methodologies) vs. translate; pass it into every generation call.
3. **Language QA gate:** post-generation checks — detect English sentences in PT-BR output (and vice versa); assert PT-BR orthographic forms (a small blocklist of PT-PT markers catches most leaks).
4. **Test both languages on every prompt change** with a fixed fixture set (same profile + same JD, EN and PT-BR). A prompt change that passes in English can regress in Portuguese.
5. Budget context for the token multiplier: PT-BR runs need the same effective headroom, so trim the JD/profile payload accordingly.

**Warning signs:**
- Prompts are developed and validated only in English.
- Generated PT-BR text contains English sentences or PT-PT spellings; nobody notices because review is quick.
- Context-window errors or quality drops appear first on PT-BR runs (they encode longer).

**Phase to address:**
P2 (bilingual prompt design + fixtures) and every subsequent module phase's definition-of-done (both languages tested).

---

### Pitfall 5: Unstructured LLM output breaks the resume template — or silently corrupts it

**What goes wrong:**
The pipeline parses free-text LLM responses into sections/bullets for the PDF template. Failure modes: markdown fences and preambles around JSON ("Here is your resume: ```json..."); missing or extra sections; a different number of bullets than the template expects; invented section names; stray newlines and smart quotes that shift layout; PT-BR accents breaking a naive ASCII-safe pipeline. Worst case is not a crash — it's a **silently wrong resume**: a bullet dropped, a section relabeled, rendering only discovered when the user reads the PDF (or worse, after sending).
OpenRouter specifics (official docs, HIGH confidence): `json_schema` enforcement **varies by provider** — some treat the schema as "a strong hint"; support is **per-endpoint, not per-model**; compliance is "not guaranteed on every endpoint"; strict modes may restrict schema features. So "OpenRouter supports structured outputs" is not a guarantee for whatever model the user picks this week.

**Why it happens:**
Teams rely on the provider feature without app-level validation, and route to whichever endpoint OpenRouter picks. One model swap breaks parsing in ways tests don't catch because tests only run the default model.

**How to avoid:**
1. **Always request `response_format: json_schema` with `strict: true`** and set `require_parameters: true` in provider preferences so requests never land on non-supporting endpoints; enable the Response Healing plugin as a belt-and-suspenders for invalid JSON.
2. **Validate at the app layer regardless** (pydantic/zod against your resume schema) and **retry with the validation error appended** to the prompt — Anthropic's docs note structured outputs are reliable "especially if implemented with retries" (HIGH confidence).
3. **Render only from validated JSON — never from raw text.** The template takes typed fields; there is no code path where model text hits the template directly.
4. Constrain the schema: enums for section names, fixed bullet-count ranges, `maxLength` per field (which also enforces LinkedIn limits, Pitfall 8).
5. Pin a default model, but run the fixture set against a second OpenRouter model periodically — model-agnostic code with model-specific prompts is a trap (see Pitfall 7).

**Warning signs:**
- JSON parsing is `response.split("```json")` anywhere in the codebase.
- A model swap changes failure rates (crashes, retries, odd sections) and nobody can say why.
- The template renderer accepts strings that were never schema-validated.

**Phase to address:**
P2 (generation core) — schema + validation + retry belongs in the first vertical slice of generation, not after the UI.

---

### Pitfall 6: Master profile drift — the profile stops being the truth, or was never filled in

**What goes wrong:**
Three related failure modes: (1) **Edit-in-app, forget-in-git** — the user fixes wording in the review UI, exports, and the correction never returns to the Markdown/YAML profile; the next generation regresses it. Every regeneration silently reverts accumulated improvements. (2) **Schema rot** — the YAML schema ships without validation; a typo'd date or renamed field is ignored (or crashes generation) months later. (3) **Example-data leak** — the initial fake example data gets shipped in a real resume because the profile was never fully replaced and nothing flags placeholder content.
Note (HIGH confidence): the JSON Resume standard explicitly has **no localized-content support** — this project's EN + PT-BR profile needs its own schema decision (per-field translations vs. per-language profile files) made *early*, because retrofitting localization into a filled profile is painful.

**Why it happens:**
File-based stores have no UI affordance for "sync back"; git discipline works for code but fails for content edited outside the editor; validation is "boring" and gets deferred.

**How to avoid:**
1. **Decide the localization shape in P1:** either parallel localized fields per entry (`summary_en` / `summary_ptbr`) or separate per-language profile files sharing IDs — pick one before any generation exists.
2. **Validate on load:** schema validation (pydantic) with loud failures for missing dates, empty impacts, unknown fields — run at generation time, not only in CI.
3. **Treat in-app edits explicitly:** either (a) edits are ephemeral and the UI says "export now or copy back to the profile file," or (b) implement write-back to the source files in git. Choose deliberately; don't leave it ambiguous.
4. **Placeholder detection:** the fake example profile is flagged in the UI (banner: "you are generating from EXAMPLE data") until the user confirms real data.

**Warning signs:**
- The review UI's edits vanish after the next "Regenerate all."
- `git log` on the profile files shows no commits after the initial fill.
- A generated resume contains "Example Corp" or the example engineer's name.

**Phase to address:**
P1 (schema + localization shape + validation) — cheapest to get right before generation code exists; P6 (edit write-back decision in the review flow).

---

### Pitfall 7: Prompt pipeline brittleness — one fragile meta-prompt, no logging, silent regressions on model swaps

**What goes wrong:**
The natural build is one big meta-prompt: "here's the profile + JD, output the full resume." Failure modes: long inputs (full profile + full JD) degrade instruction-following and blow context (PT-BR worse — Pitfall 4); multi-step chains propagate errors silently (bad keyword extraction poisons every downstream section); prompts encode hidden assumptions about one model's style, and switching models via OpenRouter — the whole point of the choice — changes format, tone, and adherence with zero code diff; nothing is logged, so when output quality drops on Tuesday you can't compare Tuesday's calls to Monday's.
Anthropic's chaining guidance (HIGH confidence): chain deliberately when you need to inspect intermediate outputs; the value of separate calls is that each is "logged, evaluated, or branched"; validate at each step.

**Why it happens:**
One big prompt is fastest to write; logging feels like infra overhead for a personal tool; OpenRouter's model menu invites frequent model swaps without a regression harness.

**How to avoid:**
1. **Decompose by section:** separate calls for keyword extraction, summary, each experience block, skills — small inputs, inspectable outputs, parallelizable, and a bad section doesn't poison the others.
2. **Log every call** (model, prompt, response, latency, retries) to local files — this is a debugging life-saver the first time a model behaves differently.
3. **Version prompts as files in git**, separate from code; a prompt change is a diff you can review and revert.
4. **Fixture regression set:** 1–2 (profile, JD, objective) fixtures; a script that runs all prompts against them for EN+PT-BR; run it whenever switching the default model. This is what makes "model flexibility" real instead of theoretical.
5. **Validate between steps:** keyword list validated against profile evidence (Pitfall 3); section JSON validated against schema (Pitfall 5) before it feeds the next step.

**Warning signs:**
- A single prompt string over 500 lines / pasting the whole profile into one call.
- "Works with model X" is the only quality evidence; switching models is manual re-testing by feel.
- Debugging a bad output means re-running and hoping, with no stored call to inspect.

**Phase to address:**
P2 (generation core) — architecture decision (decomposed calls, logging, prompt files, fixtures) is P2's foundation; re-verified whenever models change thereafter.

---

### Pitfall 8: LinkedIn-specific traps — silent truncation at character limits and resume/profile claim mismatch

**What goes wrong:**
Generated LinkedIn copy that looks fine in the app gets **silently truncated** on paste: headline limit is 220 characters (only ~60–70 visible in search previews — front-load), About 2,600, experience descriptions 2,000 (MEDIUM confidence, multiple secondary sources). Separately, the LinkedIn module is objective-driven rather than vacancy-driven (per PROJECT.md), which invites the LLM to *aspirational* writing — the profile claims skills and directions the resume doesn't support; recruiters compare the two.

**Why it happens:**
The generator optimizes for persuasive copy; it doesn't know the destination field's limits unless the schema enforces them, and the objective prompt lacks the grounding discipline the vacancy-driven resume prompt has.

**How to avoid:**
1. **Enforce limits in the schema** (`maxLength` per field) and show live character counters in the review UI against LinkedIn's real limits (headline, About, per-experience).
2. **Front-load rule for headlines:** prompt + UI check that the first ~70 characters carry the value proposition.
3. **Same grounding rules as resumes:** LinkedIn sections generate from the master profile only; the objective steers emphasis and ordering, not new facts.
4. **No automation beyond generation:** copy-paste output only — no posting/scraping automation against LinkedIn (ToS risk is entirely avoidable for a generation tool).

**Warning signs:**
- The review UI has no character counters.
- Generated headline ends mid-clause when pasted into LinkedIn.
- The About section references technologies absent from the resume's skills.

**Phase to address:**
P5 (LinkedIn module) — schema limits and counters are part of the module, not polish.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| One big meta-prompt for the whole resume | Working demo in a day | Untestable, unloggable, section failures poison everything, context limits with PT-BR | Prototype only; never as the P2 architecture |
| Parsing free-text LLM output with string manipulation instead of schema validation | No schema design upfront | Breaks on every model swap; silently wrong resumes | Never — schema validation is cheap and foundational |
| Visual-only PDF verification (eyeball the export) | No extraction test to write | Ships ATS-breaking PDFs confidently | Never — parse-back test is ~50 lines |
| No call logging ("it's a personal tool") | Less code | Every quality regression is undebuggable | Never for generation calls; 10 lines of local file logging |
| Prompt strings inline in route handlers | Fast iteration | No versioning/diffing; PT-BR and EN variants tangled in code | Never — prompt files from day one |
| Single-language testing ("PT-BR will behave the same") | Half the fixtures | Language regressions discovered by the user's real applications | Never for this project — bilingual is a core requirement |
| Editing generated content only in-app, never writing back | No write-back complexity | Master profile drifts; every regeneration reverts fixes | Acceptable short-term if the UI states it explicitly; resolve in P6 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenRouter structured outputs | Assuming `json_schema` guarantees compliance on every endpoint/model | `strict: true` + `require_parameters: true` in provider prefs + Response Healing plugin + app-level schema validation with retry |
| OpenRouter model switching | Treating prompts as portable across models | Pin a default; fixture regression suite run on every model change; record model per generation |
| PDF generation library | Choosing headless-Chrome print-to-PDF for visual fidelity | Text-first engine (WeasyPrint/fpdf2/ReportLab) where emission order = reading order; verify with extraction |
| Fonts for PT-BR | Default font subsets lacking Latin-ext glyphs | Ship/verify a font with full PT-BR coverage; assert accented characters survive extraction |
| Git + YAML profile | No schema validation on load; edits bypass git | pydantic validation at generation time; in-app edit policy (ephemeral-with-warning or write-back) decided explicitly |
| Character limits (LinkedIn) | Treating generated length as "close enough" | `maxLength` in schema + live counters (220/2,600/2,000) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Whole profile + whole JD in every call | Slow generations, context overflow on long JDs, PT-BR worse (token multiplier) | Per-section calls with only relevant profile slices | Immediately on long profiles; worse in PT-BR |
| Sequential per-section generation | 60s+ waits for a full resume in the review flow | Parallelize independent section calls | First full resume generation |
| Re-extracting keywords / re-generating summary on every review edit | Regeneration feels random; costs accumulate | Regenerate only the edited section; cache JD keyword extraction per vacancy | First regeneration session |
| No retry/backoff on OpenRouter calls | Crashes on rate limits/free-tier models; partial resumes | Retry with backoff + validation-error retries; surface model errors in UI | First busy period or weaker model |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| API key committed with the profile repo | OpenRouter account drained | Key in `.env` (per constraints); `.gitignore` from first commit; key never in prompt logs |
| Full call logging of profile + JD content in shared/synced folders | PII (yours) and application context leak via log files kept forever | Log to a local, gitignored dir; rotate/prune; never log the API key or full profile in error traces |
| Sending the master profile to arbitrary OpenRouter models | Personal data routed to third-party providers you didn't vet | This is inherent to the design — mitigate by conscious model choice and knowing OpenRouter routing; note it in the profile repo README so it stays a decision, not an accident |
| Generated resumes accumulating in a public/shared folder | Old drafts with real data floating around | Output dir inside the project, gitignored or deliberately committed only for final versions |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Regenerate replaces text with no diff or history | User loses a good edit chasing a better one | Keep per-section version history in-session; diff view old-vs-new |
| One-shot "generate everything" with a spinner | 60s+ of nothing; no trust in output | Stream/generate per section; show progress; allow early edits on finished sections |
| Review UI shows only generated text | Hallucinated facts pass unnoticed (Pitfall 2) | Side-by-side source claim vs. generated bullet; flag untraceable specifics |
| Language switch resets everything | Testing both languages is painful, so PT-BR goes untested in practice | Keep JD/keywords cached per vacancy; language is a toggle that regenerates cheaply |
| No character counters on LinkedIn fields | Silent truncation discovered on LinkedIn itself | Live counters against real limits (220/2,600/2,000) |
| Fake example data indistinguishable from real | User accidentally sends "Example Corp" | Persistent banner until profile confirmed real |

## "Looks Done But Isn't" Checklist

- [ ] **PDF export:** Often missing the parse-back test — verify extracted text has contact-first ordering, all canonical sections, co-occurring company/title/dates, and intact PT-BR accents, in both languages
- [ ] **Structured generation:** Often missing retry-with-validation-error — verify behavior when a model returns non-conforming JSON (force one bad response in testing)
- [ ] **Keyword optimization:** Often missing the profile-evidence link — verify every inserted keyword traces to a profile claim; verify absent keywords are never inserted
- [ ] **Fact integrity:** Often missing the fact diff — verify generated numbers/tech names all appear in the source profile fields
- [ ] **Bilingual support:** Often missing PT-BR prompt testing — verify identical fixtures pass format/length/language checks in EN and PT-BR
- [ ] **LinkedIn module:** Often missing character-limit enforcement — verify headline ≤220, About ≤2,600, experience ≤2,000, with ~70-char front-load check on the headline
- [ ] **Master profile:** Often missing load-time validation — verify a typo'd date or missing impacts field fails loudly at generation time
- [ ] **Model flexibility:** Often missing regression fixtures — verify the fixture suite runs green after a default-model switch
- [ ] **Call logging:** Often missing entirely — verify every generation is inspectable afterward (model, prompt, response, retries)

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| ATS-breaking PDF discovered after applications | MEDIUM | Fix template/engine; re-run parse-back gate; re-export and re-apply to missed opportunities |
| Hallucinated fact sent to an employer | MEDIUM–HIGH (reputational) | Corrected resume to recruiter immediately; add the fact-diff gate before next export |
| Profile drift (regressions compounding) | LOW–MEDIUM | Diff recent outputs against profile; port surviving edits back; adopt the explicit edit policy |
| Model swap breaks output format | LOW | Fixture suite pinpoints broken prompts; fix prompts; keep the passing model as fallback |
| PT-BR quality regression | LOW | Fixture suite catches it; terminology glossary + language QA gate before regeneration |
| Unstructured output corrupted a rendered section | LOW | Validation + retry already limits it; if shipped, regenerate the section and re-export |
| API key leaked to the profile repo | MEDIUM | Rotate key immediately; purge from git history (filter-repo); verify .gitignore |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1. PDF parses as garbage | P3 (parse-back gate before styling) | Extraction assertions pass for EN + PT-BR on every export |
| 2. LLM embellishment | P2 (grounding rules) + P6 (fact-diff UI) | Generated claims trace to profile fields; fact-diff flags anything untraceable |
| 3. Keyword stuffing | P4 (coverage/absent classification) | Every keyword evidenced in profile; skills section sane; repetition capped |
| 4. PT-BR quality drift | P2 (bilingual fixtures, glossary) + every module's DoD | Fixture suite green in EN + PT-BR; language QA gate detects bleed |
| 5. Unstructured output breaks template | P2 (schema + validation + retry) | Forced bad JSON is caught and retried; template renders only validated data |
| 6. Master profile drift | P1 (schema, localization shape, validation) + P6 (edit policy) | Load-time validation fails loudly; edit policy explicit in UI |
| 7. Prompt pipeline brittleness | P2 (decomposed calls, logging, prompt files, fixtures) | Fixture suite runs on every model change; every call inspectable in logs |
| 8. LinkedIn truncation/mismatch | P5 (schema maxLength + counters + grounding) | Counters show real limits; LinkedIn claims traceable to profile |

## Sources

- [PyMuPDF TextPage docs — extraction order, sort limitations, column behavior](https://pymupdf.readthedocs.io/en/latest/textpage.html) (HIGH)
- [OpenRouter docs — Structured Outputs](https://openrouter.ai/docs/features/structured-outputs) (HIGH, official)
- [Anthropic docs — Chaining prompts](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/chain-prompts) (HIGH, official)
- [Marco-Bench-MIF, arXiv:2507.11882 — 25–35% multilingual instruction-following gap](https://arxiv.org/abs/2507.11882) (HIGH, peer-reviewed)
- [Multi-IF, arXiv:2410.15553](https://arxiv.org/abs/2410.15553); [M-IFEval, arXiv:2502.04688](https://arxiv.org/abs/2502.04688); [cross-lingual transfer, arXiv:2402.14778](https://arxiv.org/abs/2402.14778) (HIGH)
- [Language Model Tokenizers Introduce Unfairness Between Languages, arXiv:2305.15425, NeurIPS 2023](https://arxiv.org/abs/2305.15425) (HIGH)
- [JSON Resume schema](https://jsonresume.org/schema) (HIGH, official standard)
- [Indeed Career Guide — ATS resumes](https://www.indeed.com/career-advice/resumes-cover-letters/ats-resume) and [Novoresume — ATS resume guide](https://novoresume.com/career-blog/ats-resume) (MEDIUM, cross-checked)
- LinkedIn character limits: multiple secondary sources in agreement (espirian.co.uk, prepnplaced.com and others) (MEDIUM)
- Hallucination-in-resume specifics: practitioner consensus; no direct studies found (LOW — flagged inline at Pitfall 2)

---
*Pitfalls research for: LLM-powered ATS resume tailoring + LinkedIn optimization (Career Tailor)*
*Researched: 2026-09-25*
