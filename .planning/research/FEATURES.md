# Feature Research

**Domain:** ATS resume tailoring + LinkedIn profile optimization (personal, LLM-powered, bilingual EN/PT-BR, single master profile)
**Researched:** 2026-09-25
**Confidence:** MEDIUM (competitor features cross-checked across official product pages and independent reviews; ATS/LinkedIn mechanics cross-checked across multiple guides)

## Feature Landscape

Context for reading the complexity ratings: this is a **single-user, localhost web app** (JS frontend, Python backend OK) where all content is LLM-generated via OpenRouter meta-prompts and all data lives in Markdown/YAML files in git. Complexity is rated for *that* context, not for a commercial SaaS.

### Table Stakes (Users Expect These)

Features every serious tool in this domain has (Jobscan, Teal, Rezi, Resume Worded, Kickresume all have them). Missing them makes the output unusable for real applications.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Master profile as single source of truth | Teal's "master work history" pattern: enter experiences once, generate every artifact from it. Rewriting from scratch per application is what users are trying to escape | MEDIUM | Schema design is the real work (experiences, projects, technologies, impacts, education, certs). YAML for structure + Markdown for free-text. Ship schema + example data first |
| Job description paste input | Every tool accepts the JD text; paste-text works with any job site (LinkedIn, Gupy) with zero scraping risk | LOW | One textarea + language selector. URL extraction already ruled out of scope |
| Keyword extraction from the JD | This IS the product category's core mechanic — Jobscan's entire business. ATS keyword screening is confirmed for Western ATS and for Gupy (dominant in Brazil) | MEDIUM | LLM call returning structured keyword list (skills, tools, titles, certs). Display the list so the user sees what the AI is targeting |
| Keyword coverage report (JD keywords present vs missing in the output) | Jobscan/Resume Worded both show match + missing keywords. Users don't trust generated output without seeing the gap closed | MEDIUM | Simple string/variant matching of extracted keywords against generated text. A checklist beats a vanity score (see anti-features) |
| Sectioned resume generation grounded in the master profile | Summary, experience bullets, skills tailored per vacancy. One-shot black-box generation is the #1 complaint about AI resume tools | MEDIUM | Meta-prompts per section; hard constraint: only rephrase facts present in the master profile (hallucination guard) |
| ATS-safe single-column output format | Research confirms: ATS parsers (e.g., Workday via Apache Tika) scramble two-column layouts and cannot read tables/text-boxes/icons. Single column, standard headers, standard fonts = the Google-recommended format this project already mandates | LOW | Fixed template is a *feature* — it deletes the template-engine problem. No gallery, no customization |
| PDF export with clean text layer | The final artifact must be sendable. Research caveat: DOCX parses most reliably, and a PDF with poor text extraction (wrong reading order, text-in-image) loses parsing fidelity | MEDIUM | Generate text-based PDF (e.g., ReportLab/WeasyPrint) and verify extraction order. Not a scanned/graphics-based PDF. Keep DOCX as a documented future escape hatch |
| Bilingual generation PT-BR / EN | User targets both markets; no mainstream tool does both well from one profile. Brazilian ATS screening is keyword-based (Gupy) | MEDIUM | Language as a generation parameter. Rule for prompts: keep tool/product names verbatim ("React", "Kubernetes") in both languages; translate role names and narrative text only |
| Per-section regenerate + inline edit before export | Kickresume's "regenerate any part until satisfied" is expected UX now; one-shot tools feel broken by comparison. Also the primary defense against LLM errors before a real application | LOW-MEDIUM | Section-level API calls + editable textareas. Already a stated requirement — treat as non-negotiable |
| LinkedIn section generation (headline, About, experience, skills) | Resume Worded's LinkedIn Review and Jobscan's LinkedIn tool both target exactly these four sections; they carry nearly all recruiter-search weight (headline > About > current experience > skills) | MEDIUM | Same master profile, but driven by an objective brief instead of a JD (see differentiators). Output as copy-paste blocks with LinkedIn's length limits enforced (headline 220 chars, About 2,600) |

### Differentiators (Competitive Advantage)

None of the commercial tools combine these — they are what make this project more than "Jobscan at home".

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Git-versioned master profile | Teal stores your history in their cloud; here every resume iteration is diffable and revertible in git. Real resume history without a database, aligned with the file-based constraint | LOW | Falls out of the architecture choice — but surface it: `git log` on the profile is a feature, not an implementation detail |
| Vacancy-driven resume + objective-driven LinkedIn from ONE profile | No tool does both from a shared source. Guarantees the LinkedIn presence matches what the resume claims — consistency recruiters actually check | MEDIUM | Keyword engine needs two input modes: JD text (resume) and objective brief (LinkedIn). Same extraction/prompts, different input semantics |
| Objective brief as first-class input (LinkedIn) | LinkedIn targets a *direction*, not one posting. Brief = target roles, seniority, industries, key technologies → derived keyword set | LOW | A small structured form (or YAML snippet) feeding the same keyword pipeline. This is the project's stated twist — build it deliberately |
| Honest keyword checklist instead of a 0–100 score | Commercial scores are marketing (they differ per vendor and mean nothing absolute). A "these 12 JD keywords are in / these 3 are missing" report is actionable and honest | LOW | Cheaper than scoring, more useful. Also avoids building a fake ATS simulator |
| ATS self-check on the exported PDF | Post-export verification: extract text from the generated PDF, confirm reading order (contact → summary → experience…), confirm target keywords survived export. Catches the single biggest real-world failure mode (bad PDF text layer) | MEDIUM | Python PDF text-extraction (pdfminer/PyMuPDF) + assertions. Nobody in the consumer space verifies their own output; this makes "ATS-optimized" a tested property, not a claim |
| Inspectable, editable meta-prompts | Prompts stored as versioned files the user can tune ("more metrics", "more concise PT-BR"). Commercial tools hide the prompt; a personal tool can expose it | LOW | Prompts in git next to the profile. Cheap to build, high leverage for output quality over time |
| Profile completeness lint before generation | Warn: "no metrics on job X", "no data for skill Y mentioned in the JD" — so gaps surface before an application goes out | MEDIUM | Rule-based pass over the master profile + JD keywords. Turns the tool into a coach, not just a writer |
| UI in Portuguese, output in PT-BR or EN per run | Commercial tools are EN-first; Brazilian tools are PT-only. Matches the user's stated setup | LOW | UI strings in PT; language selector per generation run |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Visual template gallery / design customization | Every commercial builder leads with "50+ templates" | Directly conflicts with the ATS goal (columns/tables/icons break parsers); a template engine is the biggest cost center of resume builders; the user already decided on Google single-column format | ONE fixed, tested, single-column template. The design decision is already made — that's a feature |
| Numeric ATS score ("Your resume: 87/100!") | Jobscan, Rezi, Resume Worded all gamify it; it feels reassuring | Fake precision: no tool can replicate a real ATS's proprietary scoring; scores differ per vendor and mislead. Cost of building a defensible one is high; trust cost when it's wrong is higher | Keyword presence checklist + explicit ATS-format checklist (single column, standard headers, text layer verified) |
| Keyword stuffing mode | "Match 100% of keywords" appeals to users anxious about filters | Reads terribly to human recruiters (who read after the ATS passes); modern LLMs integrate keywords naturally anyway; forced density is detectable | Prompts instructed to integrate JD terminology *where truthfully supported by the master profile*; coverage report shows what legitimately couldn't be included |
| Letting the LLM invent achievements/metrics | "Make my bullets sound more impressive" | Hallucinated experience = catastrophically wrong output sent to real employers; this is the domain's most dangerous failure | Hard prompt constraint: rephrase only facts present in the master profile; review-before-export flow as detection layer; completeness lint nudges the user to add real metrics |
| Job posting extraction from URL / browser extension | Paste-a-link is slicker; Teal's extension is popular | Job boards (LinkedIn, Gupy) block scraping and extensions violate ToS; already ruled out in PROJECT.md with sound reasoning | Paste-text input — works with every site, zero ToS risk |
| Auto-apply / application submission | Jobscan and others market it | High ToS/fragility risk, huge scope, and blind auto-applying is quality-negative for a personal search | The tool ends at "export sendable PDF"; the human sends it |
| Application tracker / CRM | Teal's most-praised feature | Different product; spreadsheets or Teal's free tier already cover it; zero relation to the core value (generating content) | Keep out; revisit as a trivial Markdown checklist only if the user actually feels the pain |
| Cover letters | Natural "while we're at it" feature | Explicitly out of scope in PROJECT.md; distinct prompt/format work; not needed for validation of the core | Revisit as a future module after both current modules are validated |
| DOCX export | "Some vacancies ask for Word" (research confirms DOCX parses most reliably) | Adds a second export pipeline to build and keep ATS-clean; PDF with verified text layer covers the need today | Documented future escape hatch: build only when a real vacancy demands it (matches PROJECT.md's own condition) |
| LinkedIn auto-posting / API sync / profile scraping | One-click profile update sounds magical | LinkedIn's API doesn't support profile-section writes for regular users; browser automation violates ToS and risks account restriction | Generate → user copy-pastes into LinkedIn. Plain text blocks, length-limit enforced |
| Multi-user, auth, cloud sync | Habit from commercial SaaS | Personal tool on localhost; auth and hosting are pure overhead with zero value for one user | File-based data in git; `.env` for the OpenRouter key |

## Feature Dependencies

```
[Master profile schema + example data]
    └──requires──> nothing (root of everything)
    └──required-by──> [Sectioned resume generation]
    └──required-by──> [LinkedIn generation]
    └──required-by──> [Profile completeness lint]

[JD paste input] ──requires──> nothing
    └──required-by──> [Keyword extraction]
                          └──required-by──> [Resume generation] (keywords steer prompts)
                          └──required-by──> [Keyword coverage report] (needs both extracted keywords AND generated text)

[Objective brief input] ──requires──> [Keyword extraction engine] (shared, two input modes)
    └──required-by──> [LinkedIn generation]

[Resume generation] ──requires──> [Review flow: per-section regenerate + inline edit]
    └──required-by──> [PDF export (clean text layer)]
                          └──required-by──> [ATS self-check of exported PDF]

[Bilingual generation] ──requires──> [Master profile] (language-neutral facts) + [Language parameter in meta-prompts]
    └──enhances──> both modules

[Inspectable meta-prompts] ──enhances──> [Resume generation] and [LinkedIn generation]
[Profile lint] ──enhances──> [Master profile] quality
```

### Dependency Notes

- **Both modules require the master profile:** this is the architectural root. Phase 1 must deliver schema + example data before any generation work is meaningful.
- **Coverage report requires generation, not the reverse:** extraction steers generation; the report is a cheap post-pass comparing extracted keywords to generated text. Never block generation on the report.
- **ATS self-check requires PDF export:** it verifies the actual output artifact, so it must come after export exists. It is the cheapest high-value QA feature in the plan.
- **LinkedIn module shares the keyword engine with the resume module** (two input modes: JD vs objective brief). Build the keyword engine input-agnostic from day one to avoid a rewrite.
- **Bilingual support conflicts with nothing but must not be bolted on:** language is a parameter of every prompt from the start; retrofitting it means re-testing every prompt in two languages.
- **Anti-feature conflict:** template gallery/ATS score would actively conflict with the fixed-format and honest-checklist decisions — documented to prevent scope re-entry.

## MVP Definition

### Launch With (v1) — Resume module end-to-end

Minimum to produce a real, sendable, tailored resume from a real vacancy.

- [ ] Master profile schema + example data in git — root dependency of everything
- [ ] JD paste input + language selector (PT-BR/EN) — the primary interaction
- [ ] Keyword extraction from JD with visible keyword list — core mechanic of the category
- [ ] Sectioned resume generation grounded in master profile (facts-only constraint) — the product's core value
- [ ] Review flow: regenerate individual sections + inline edit — quality control before real applications
- [ ] Keyword coverage checklist (present/missing) — closes the loop the category is built around
- [ ] Single-column Google-format PDF export with clean text layer — the sendable artifact

### Add After Validation (v1.x) — LinkedIn module + hardening

- [ ] LinkedIn module: headline, About, experience descriptions, skills from objective brief — trigger: resume module produces sendable output reliably
- [ ] ATS self-check on exported PDF (text extraction order + keyword survival) — trigger: first real applications sent
- [ ] Profile completeness lint — trigger: first time a generation reveals the profile lacked data
- [ ] Prompt library tuning (user-editable meta-prompts in git) — trigger: recurring output-quality nits

### Future Consideration (v2+)

- [ ] Cover letter module — why defer: explicitly out of scope; distinct prompt/format work with no bearing on core validation
- [ ] DOCX export — why defer: build only when a real vacancy demands it (pre-committed condition in PROJECT.md)
- [ ] Multiple profile variants (e.g., "IC" vs "leadership" emphasis toggles) — why defer: only valuable once the single-profile flow is proven
- [ ] Application history log (Markdown-based) — why defer: tracker is a different product; only if the user feels the pain

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Master profile schema + example data | HIGH | MEDIUM | P1 |
| JD paste + language selector | HIGH | LOW | P1 |
| Keyword extraction (JD and objective modes) | HIGH | MEDIUM | P1 |
| Sectioned resume generation (facts-only) | HIGH | MEDIUM | P1 |
| Review flow (per-section regenerate + edit) | HIGH | LOW-MEDIUM | P1 |
| Google-format PDF export (clean text layer) | HIGH | MEDIUM | P1 |
| Keyword coverage checklist | HIGH | LOW | P1 |
| LinkedIn module from objective brief | HIGH | MEDIUM | P2 |
| ATS self-check of exported PDF | MEDIUM-HIGH | MEDIUM | P2 |
| Profile completeness lint | MEDIUM | MEDIUM | P2 |
| Inspectable meta-prompts | MEDIUM | LOW | P2 |
| Cover letters | LOW (for now) | MEDIUM | P3 |
| DOCX export | LOW (conditional) | MEDIUM | P3 |
| Profile variants | LOW (for now) | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Jobscan (~$49.95/mo) | Teal | Rezi | Resume Worded | Kickresume | This Project |
|---------|----------------------|------|------|---------------|------------|--------------|
| Resume vs JD keyword match | Yes — match rate % + missing list | Yes — 15+ point analysis, ATS score | Yes — keyword targeting + Rezi Score | Yes — 0–100 score, line-by-line feedback | Partial — AI tailoring, weaker scoring | Yes — checklist, no vanity score |
| AI generation from master history | Partial (optimize existing) | Yes — master work history + per-job versions | Yes — AI writer | No (feedback-only) | Yes — AI writes from scratch | Yes — git-versioned master profile |
| Per-section regenerate + edit | Limited | Yes (editor) | Yes | No | Yes — regenerate any part | Yes — core UX requirement |
| LinkedIn optimization | Yes — profile keyword score | No | No | Yes — 0–100 profile review | Partial (headline/summary writer) | Yes — full section generation from objective |
| Objective-driven (non-vacancy) input | No | No | No | No | No | Yes — the project's twist |
| Bilingual EN/PT-BR | No | No | No | No | Partial (UI langs, not dual-market generation) | Yes — per-run language, one profile |
| Data ownership / versioning | Cloud | Cloud | Cloud | Cloud | Cloud | Git — user owns every diff |
| PDF text-layer self-verification | No | No | No | No | No | Planned (ATS self-check) |
| Template gallery | No | Yes | Yes | No | Yes (40+) | Deliberately none (fixed ATS format) |
| Tracker / auto-apply / interview prep | Yes (all three) | Yes (tracker) | Interview practice | No | No | Anti-feature — out of scope |

**Reading:** the commercial cluster is broad but shallow on this user's specific needs — none combine one shared master profile + both input modes (vacancy and objective) + bilingual output + data ownership. That intersection is the project's niche; it does not need to compete on trackers, templates, or scores.

## Sources

- [Jobscan — LinkedIn Optimization tool](https://www.jobscan.co/linkedin-optimization) and [Final Round AI Jobscan review](https://www.finalroundai.com/blog/jobscan-review-pros-cons) (feature set, pricing)
- [Teal HQ](https://www.tealhq.com) (15+ point analysis, ATS score, real-time recommendations) and [LoopCV Teal review](https://www.loopcv.pro)
- [Jobsolv vs Rezi comparison](https://jobsolv.com) (Rezi Score, keyword targeting, AI writer)
- [Resume Worded — Targeted Resume](https://resumeworded.com/targeted-resume) and [LinkedIn Review](https://resumeworded.com/linkedin-review) (scoring, line-by-line feedback)
- [Kickresume AI Resume Writer](https://www.kickresume.com/en/ai-resume-writer) and [AI Cover Letter Writer](https://www.kickresume.com/en/ai-cover-letter-writer) (regenerate-any-part UX)
- [Jobloo — How Workday's OCR parser reads resumes](https://jobloo.co) (Apache Tika, two-column interleaving failure)
- [Indeed ATS guidance], [Coursera resume keyword matching], [ATSalign parsing guide] (keyword categories, DOCX vs PDF parsing fidelity)
- [LinkedIn Talent Blog — profile summaries](https://www.linkedin.com/business/talent/blog/product-tips/linkedin-profile-summaries-that-we-love-and-how-to-boost-your-own), [Pursue Networking LinkedIn SEO guide](https://pursuenetworking.com/blog/linkedin-profile-keywords-seo-guide), [Future Work — LinkedIn Recruiter ranking](https://www.future-work.co.uk/news/top-11-tips-to-rank-higher-on-linkedin-recruiter-a-complete-guide-for-job-seekers) (keyword weight order: headline > About > experience > skills; 50 skill slots; pinned top 3)
- [Gupy/ATS brasileiro guides](https://stylingcv.com), [prepavaga.com.br](https://prepavaga.com.br), [resufit.com](https://resufit.com) (Gupy as dominant Brazilian ATS; automatic keyword screening; mirror vacancy vocabulary)
- Confidence: MEDIUM — all competitor claims cross-checked against at least an official product page plus one independent review; ATS/LinkedIn mechanics cross-checked across 3+ independent guides. No finding rests on a single source.

---
*Feature research for: personal ATS resume tailoring + LinkedIn optimization toolkit (Career Tailor)*
*Researched: 2026-09-25*
