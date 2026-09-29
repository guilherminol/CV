// Typed client for GET /api/profile — mirrors the finalized plan-02 backend
// contract (backend/app/routes/profile.py + backend/app/profile/models.py).
// Native fetch only — no axios (STACK.md). The backend owns the strict
// schema; tsc -b is the gate that catches Pydantic↔TS drift (STACK.md).

/** Localized map (D-01): language → text. Base language pt-BR (D-04). */
export type LocalizedText = { 'pt-BR': string; en?: string }

export interface ImpactDTO {
  action: LocalizedText
  metric: LocalizedText
  context?: LocalizedText | null
}

export interface ContactDTO {
  email: string
  location?: string | null
  phone?: string | null
  linkedin?: string | null
}

export interface ExperienceDTO {
  company: string // single-value per D-02: proper noun
  title: LocalizedText // D-02: job titles ARE localized
  location?: string | null
  start_date: string
  end_date?: string | null
  description: LocalizedText
  impacts: ImpactDTO[] // D-08: embedded per experience
}

export interface EducationEntryDTO {
  institution: string
  degree: string
  start_date?: string | null
  end_date?: string | null
}

export interface SkillGroupDTO {
  category: string // D-09: categorized group of plain tech names
  items: string[]
}

export interface CertificationEntryDTO {
  name: string
  issuer?: string | null
  year?: string | null
}

export interface LanguageEntryDTO {
  name: string
  level: string
}

export interface ProjectDTO {
  name: string
  description: LocalizedText
  technologies: string[]
  impacts: ImpactDTO[]
}

/** Mirror of the Pydantic `Profile` model_dump() — the full D-07 section set. */
export interface PerfilDTO {
  example: boolean // D-11 placeholder flag (part of the dump)
  name: string
  contact: ContactDTO
  summary: LocalizedText
  experiences: ExperienceDTO[]
  education: EducationEntryDTO[]
  skills: SkillGroupDTO[]
  certifications: CertificationEntryDTO[]
  languages: LanguageEntryDTO[]
  projects: ProjectDTO[]
}

/** Section presence/counts from compute_completude
 *  (backend/app/profile/completeness.py) — D-12, NOT the PROFILE-02 lint. */
export interface CompletudeDTO {
  resumo: boolean
  experiencias: boolean
  experiencias_qtde: number
  experiencias_impactos_qtde: number
  educacao: boolean
  educacao_qtde: number
  habilidades: boolean
  habilidades_qtde: number
  habilidades_itens_qtde: number
  certificacoes: boolean
  certificacoes_qtde: number
  idiomas: boolean
  idiomas_qtde: number
  projetos: boolean
  projetos_qtde: number
}

/** Status envelope (Pattern 4): always 200; a broken profile is the "erro"
 *  state the UI renders — never an HTTP failure (D-12/D-13). */
export type ProfileResponse =
  | { status: 'ok'; exemplo: boolean; perfil: PerfilDTO; completude: CompletudeDTO }
  | { status: 'erro'; erros: string[] }

export async function fetchProfile(): Promise<ProfileResponse> {
  const resp = await fetch('/api/profile')
  if (!resp.ok) {
    throw new Error(`GET /api/profile falhou: ${resp.status}`)
  }
  return (await resp.json()) as ProfileResponse
}

// --- resume endpoints (plan 03-04) — mirrors the NORMATIVE response contract
// in .planning/phases/03-resume-vertical-slice/03-03-PLAN.md, implemented by
// backend/app/routes/resume.py. Change BOTH together; tsc -b is the drift gate.

export type ResumeLanguage = 'pt-BR' | 'en'

/** Schema keyword category (Phase 2 D-10); display labels live in constants/ui.ts. */
export type KeywordCategory = 'competencias' | 'ferramentas' | 'titulos_de_vaga' | 'certificacoes'

export interface KeywordDTO {
  canonical: string
  aliases: string[]
  pt: string | null
  en: string | null
  category: KeywordCategory
}

export interface ExperienciaGeradaDTO {
  company: string
  title: string
  bullets: string[]
}

/** The 3 generated sections (D-01 stage order: resumo → experiências → habilidades). */
export interface SecoesDTO {
  resumo: string
  experiencias: ExperienciaGeradaDTO[]
  habilidades: string[]
}

/** One keyword's honest coverage verdict; termo is the auditable matched string (D-02). */
export interface CoberturaItemDTO {
  canonical: string
  category: KeywordCategory
  termo: string | null
  status: 'coberto' | 'ausente'
}

export type LintResponse =
  | { status: 'ok'; keywords: KeywordDTO[]; avisos: string[] }
  | { status: 'erro'; erros: string[] }

export type GerarResponse =
  | {
      status: 'ok'
      idioma: ResumeLanguage
      keywords: KeywordDTO[]
      avisos: string[]
      secoes: SecoesDTO
      cobertura: CoberturaItemDTO[]
      cobertura_resumo: { cobertos: number; total: number }
    }
  | { status: 'erro'; erros: string[] }

/** Pre-generate lint/extract (SC5): keyword extraction + JD-tied profile gaps. */
export async function fetchResumeLint(jdText: string): Promise<LintResponse> {
  const resp = await fetch('/api/resume/lint', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jd_text: jdText }),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/resume/lint falhou: ${resp.status}`)
  }
  return (await resp.json()) as LintResponse
}

/** One-shot generate: extraction → lint → 3 sequential section stages → coverage. */
export async function gerarCurriculo(payload: {
  jd_text: string
  language: ResumeLanguage
}): Promise<GerarResponse> {
  const resp = await fetch('/api/resume/gerar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/resume/gerar falhou: ${resp.status}`)
  }
  return (await resp.json()) as GerarResponse
}

// --- export + self-check endpoints (plan 04-03) — mirrors the NORMATIVE envelope
// contract pinned in .planning/phases/04-pdf-export-ats-self-check/04-02-SUMMARY.md,
// implemented by backend/app/routes/export.py (plan 04-02). Change BOTH together;
// tsc -b is the drift gate. Key names pdf_base64/selfcheck/ordem/sobrevivencia/gate
// must match the backend exactly.

/** The honest ATS self-check over the extracted PDF text (D-14/D-15): order rows
 *  (contato first, then one per rendered section), per-keyword survival verdicts
 *  (SAME shape as the Phase 3 coverage chips — D-15), and the gate booleans the
 *  download was conditioned on (D-06/D-07 — surfaced as the panel's footer). */
export interface SelfCheckDTO {
  ordem: { id: string; ok: boolean }[]
  sobrevivencia: CoberturaItemDTO[]
  gate: { coocorrencia: boolean; acentos: boolean }
}

/** 04-02 envelope: ok carries filename + bytes + selfcheck; the erro branch
 *  carries ONLY erros — no filename/pdf_base64/selfcheck key EVER (D-07/D-08:
 *  a failed gate never delivers bytes as if they were good). */
export type ExportarResponse =
  | { status: 'ok'; filename: string; pdf_base64: string; selfcheck: SelfCheckDTO }
  | { status: 'erro'; erros: string[] }

/** The displayed mounted state (D-10) travels verbatim to the export — field
 *  names lifted from GerarResponse + the perfilQuery payload so the caller
 *  passes exactly what the screen shows, with no refetch or recomputation. */
export interface ExportarRequest {
  perfil: PerfilDTO
  secoes: SecoesDTO
  keywords: KeywordDTO[] // may be [] — zero-keyword runs are legitimate
  idioma: ResumeLanguage // REQUIRED — the PDF follows the run language (D-12)
}

/** One-shot export: render → PDF → parse-back gate → self-check in ONE request. */
export async function exportarCurriculo(payload: ExportarRequest): Promise<ExportarResponse> {
  const resp = await fetch('/api/resume/exportar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/resume/exportar falhou: ${resp.status}`)
  }
  return (await resp.json()) as ExportarResponse
}

// --- per-section regeneration (plan 05-01) — mirrors the NORMATIVE envelope
// contract implemented by backend/app/routes/resume.py (RegenerarRequest +
// run_section_regen). Change BOTH together; tsc -b is the drift gate.

/** Section id — matches the backend's Literal['resumo','experiencias','habilidades']. */
export type SecaoId = 'resumo' | 'experiencias' | 'habilidades'

/** Strict-body mirror of RegenerarRequest. `secoes` is the displayed state
 *  verbatim (the ExportarSecoes shape the export endpoint already posts). */
export interface RegenerarRequest {
  jd_text: string
  language: ResumeLanguage
  secao: SecaoId
  secoes: SecoesDTO
  keywords: KeywordDTO[] // may be [] — zero-keyword runs are legitimate
  dica?: string // optional steering hint — NEVER sent as an empty key
}

/** 05-01 envelope: ok carries the FULL merged secoes + recomputed coverage
 *  (the client replaces its state wholesale — no client-side merge); the
 *  erro branch carries ONLY erros (200-envelope house rule). */
export type RegenerarResponse =
  | {
      status: 'ok'
      idioma: ResumeLanguage
      secoes: SecoesDTO
      cobertura: CoberturaItemDTO[]
      cobertura_resumo: { cobertos: number; total: number }
    }
  | { status: 'erro'; erros: string[] }

/** One section's regen: exactly ONE gateway stage runs server-side. The dica
 *  key is OMITTED from the body when empty/whitespace — the backend model is
 *  extra=forbid, and `dica: ""` would be a useless key (blank normalizes to
 *  None backend-side; here it simply never travels). */
export async function regenerarSecao(payload: RegenerarRequest): Promise<RegenerarResponse> {
  const { dica, ...rest } = payload
  const body = dica && dica.trim() ? { ...rest, dica } : rest
  const resp = await fetch('/api/resume/regenerar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) {
    throw new Error(`POST /api/resume/regenerar falhou: ${resp.status}`)
  }
  return (await resp.json()) as RegenerarResponse
}

/** D-11: the browser's native download UI. Bytes come from the same export
 *  response (atob → Uint8Array → Blob); the filename is the backend-generated
 *  `curriculo-{idioma}-{data}.pdf` — NEVER recomposed client-side. No new deps
 *  (STACK.md): object URL + detached anchor click, URL revoked on a subsequent
 *  task (IN-03 — revoking in the same task as click() can abort the download
 *  in non-Chromium engines; Chromium, the documented target, is unaffected),
 *  bytes never stored in module state. */
export function downloadPdf(pdfBase64: string, filename: string): void {
  const bytes = Uint8Array.from(atob(pdfBase64), (c) => c.charCodeAt(0))
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 0)
}
