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
