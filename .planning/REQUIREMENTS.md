# Requirements: Career Tailor

**Defined:** 2026-09-25
**Core Value:** Paste a job description (or state a career objective for LinkedIn) and get polished, ATS-optimized, keyword-targeted output in English or Portuguese that the user would actually send or post — without manual rewriting from scratch.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Perfil Base

- [x] **PROFILE-01**: User can maintain a master profile as Markdown/YAML files in git, validated against a schema, shipped with example data covering experiences, projects, technologies, and impacts
- [x] **PROFILE-02**: User sees a completeness lint before generating (e.g., "no metrics for job X", "JD requires skill Y missing from profile")
- [x] **PROFILE-03**: User can edit meta-prompts as versioned files in git to tune generation behavior (e.g., "more metrics", "more concise PT-BR")

### Currículo

- [x] **RESUME-01**: User can paste a job description and choose the output language (PT-BR or EN) per generation run
- [x] **RESUME-02**: User can see the keywords extracted from the job description (skills, tools, titles, certs) that the generation is targeting
- [x] **RESUME-03**: User gets a sectioned resume (summary, experience bullets, skills) generated strictly from master-profile facts — the AI rephrases but never invents achievements, metrics, or technologies
- [x] **RESUME-04**: User sees a keyword coverage checklist showing which JD keywords made it into the resume and which did not (no vanity 0–100 score)

### Revisão e Export

- [ ] **REVIEW-01**: User can regenerate individual resume sections and edit generated text inline in the app before exporting
- [x] **REVIEW-02**: User can export the resume as a single-column Google-format PDF with a clean, selectable text layer (ATS-parseable reading order)
- [ ] **REVIEW-03**: User can run an ATS self-check that extracts the text from the exported PDF and verifies section order and keyword survival, in both languages

### LinkedIn

- [ ] **LI-01**: User can state a career objective (target roles, seniority, key technologies) and choose the output language (PT-BR or EN) as the input driving all LinkedIn generation
- [ ] **LI-02**: User gets a headline (≤220 chars) optimized with keywords for the stated objective
- [ ] **LI-03**: User gets an About section (≤2600 chars) rewritten and optimized for the stated objective
- [ ] **LI-04**: User gets rewritten descriptions for each experience entry (≤2000 chars each) with action verbs and objective-relevant keywords
- [ ] **LI-05**: User gets a prioritized skills list to feature on the profile, with all outputs as copy-paste text blocks enforcing LinkedIn length limits

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Módulos futuros

- **COVER-01**: Cover letter generation from vacancy + master profile — deferred until both v1 modules are validated
- **EXPORT-01**: DOCX export — build only when a real vacancy demands it (pre-committed condition)
- **PROFILE-10**: Multiple profile emphasis variants (e.g., IC vs leadership toggles) — only after single-profile flow is proven
- **HIST-01**: Application history log (Markdown-based) — only if the user feels the tracker pain

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Job posting extraction from URL / browser extension | Job boards block scraping; extensions violate ToS; paste-text works with every site |
| Numeric ATS score (0–100) | Fake precision — no tool can replicate a proprietary ATS; honest checklist is actionable |
| Visual template gallery / design customization | Conflicts with the ATS goal; the fixed Google single-column format is a deliberate feature |
| Keyword stuffing mode | Reads badly to human recruiters; forced density is detectable; keywords integrated only where truthfully supported |
| AI-invented achievements or metrics | Catastrophic failure mode for real applications; hard facts-only constraint is non-negotiable |
| Auto-apply / application submission | ToS/fragility risk and quality-negative; the tool ends at "export sendable PDF" |
| Application tracker / CRM | Different product; the user owns a git history already |
| LinkedIn auto-posting / API sync | LinkedIn API does not support profile writes for regular users; automation violates ToS |
| Multi-user, auth, cloud hosting | Personal tool on localhost; pure overhead for one user |
| Real-time collaboration or comments | Single-user tool; no basis for the feature |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROFILE-01 | Phase 1 | Complete |
| PROFILE-02 | Phase 3 | Complete |
| PROFILE-03 | Phase 2 | Complete |
| RESUME-01 | Phase 3 | Complete |
| RESUME-02 | Phase 3 | Complete |
| RESUME-03 | Phase 3 | Complete |
| RESUME-04 | Phase 3 | Complete |
| REVIEW-01 | Phase 5 | Pending |
| REVIEW-02 | Phase 4 | Complete |
| REVIEW-03 | Phase 4 | Pending |
| LI-01 | Phase 6 | Pending |
| LI-02 | Phase 6 | Pending |
| LI-03 | Phase 6 | Pending |
| LI-04 | Phase 6 | Pending |
| LI-05 | Phase 6 | Pending |

**Coverage:**

- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-25*
*Last updated: 2026-09-25 after roadmap creation*
