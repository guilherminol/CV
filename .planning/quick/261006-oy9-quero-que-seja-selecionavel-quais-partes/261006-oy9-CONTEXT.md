# Quick Task 261006-oy9: Tornar selecionáveis as partes do currículo na versão final + skills por emprego no perfil - Context

**Gathered:** 2026-10-06
**Status:** Ready for planning

<domain>
## Task Boundary

quero que seja selecionavel quais partes de curriculo eu quero colocar na versão final, hoje tudo vem junto sem poder selecionar, além disso quero que no perfil, cada emprego tenho uma área de skills, pra que fique claro na hora da geração o que eu ja usei em cada empresa

Two features:
1. **Seleção de conteúdo na exportação** — the final PDF currently renders every section and every profile item (all 7 sections in fixed order). The user must be able to choose what goes into the final version.
2. **Skills por experiência no perfil** — each experience in `content/profile.md` gets its own skills list so the generation knows which technologies were used at each company.

</domain>

<decisions>
## Implementation Decisions

### Granularidade da seleção
- **Seções + itens individuais**: section-level toggles (Resumo, Experiência, Formação, Habilidades, Certificações, Idiomas, Projetos) PLUS item-level selection for experiences and projects (e.g., export without the Red Lion experience, without a specific personal project). Education/certifications/languages toggle as whole blocks only.

### Momento da seleção
- **Antes de exportar** (result screen): generation stays exactly as today (all-or-nothing, 3 sequential stages, whole profile facts). Selection happens on the result screen and controls what is rendered into the PDF at `POST /api/resume/exportar`. The generation pipeline contract is NOT touched.

### Skills por emprego — efeito
- **Só na geração**: the per-experience skills feed the profile facts the LLM receives (better-informed bullets and skills attribution per company). The PDF layout is unchanged — no per-job stack line rendered.

### Onde manter as skills por emprego
- **Só no YAML**: a new per-experience `skills` field in `content/profile.md`. The profile remains the single source; NO profile-editor UI in this task.

</decisions>

<specifics>
## Specific Ideas

- The pain is real and recent: commit history shows Red Lion (English instructor) had to be removed manually from a generated CV ("H&P opens page 2 via explicit pagebreak; Red Lion removed — clean 2-pager"). Item-level experience selection directly addresses this.
- `render.py` already hides zero-entry passthrough sections (ProfilePreview convention) — the selection mechanism can lean on that: an unselected item simply doesn't reach the render payload.
- Existing invariants to respect (from route/render docs):
  - `ExportarRequest` is strict (`extra=forbid`); `ExportarSecoes` has `min_length=1` on all three generated sections.
  - The parse-back gate (`_expected_doc`) derives expectations from the SAME payload the renderer uses — any selection must flow through the payload, never as a render-time bypass, or the gate diverges.
  - Coverage/self-check is computed over generated text at generation time; selection at export time is presentational and must not change the gerar response.
- Project schema already has a `scope` field (profissional/pessoal) rendered as groups — precedent for per-item attributes.
- The Brooklyn Brothers / Kenzie entries already encode tech in impact `context` strings — per-experience `skills` is the structured upgrade.

</specifics>

<canonical_refs>
## Canonical References

- `backend/app/routes/export.py` — ExportarRequest/ExportarSecoes shapes, gate ordering
- `backend/app/export/render.py` — section_keys order, HEADINGS, zero-entry hiding, _sections_content traversal
- `backend/app/resume/pipeline.py` — run_resume_pipeline / compose_stage_input (facts composition for generation)
- `backend/app/resume/facts.py` — serialize_profile_facts (where per-experience skills must enter the LLM facts)
- `backend/app/profile/models.py` — Profile/Experience Pydantic models (new skills field lands here)
- `content/profile.md` — master profile YAML (per-experience skills field added here)
- `frontend/src/pages/CurriculoHome.tsx` + `frontend/src/components/ResumeResult.tsx` — result screen where selection UI lands
- `frontend/src/components/ExportZone.tsx` — export trigger carrying the payload

</canonical_refs>
