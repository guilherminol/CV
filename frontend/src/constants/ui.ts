// PT-BR UI strings — one user, one UI language; no i18n framework (STACK.md).

export const APP_TITLE = 'Career Tailor'

export const NAV_ITEMS = [
  { id: 'curriculo', label: 'Currículo', enabled: false },
  { id: 'perfil', label: 'Perfil', enabled: true },
  { id: 'linkedin', label: 'LinkedIn', enabled: false },
] as const

export const PERFIL_SECTION_TITLE = 'Perfil'

// --- load status (D-12: the home shows load status at a glance) ---
export const PERFIL_LOADING = 'Carregando perfil…'
export const PERFIL_STATUS_OK = 'Perfil carregado'
export const PERFIL_STATUS_ERRO = 'Perfil com erro'

// --- error panel (D-13/D-14): backend lines are rendered verbatim ---
export const PERFIL_ERROR_TITLE = 'Não foi possível carregar o perfil'
export const PERFIL_ERROR_HINT =
  'Corrija o arquivo content/profile.md no caminho indicado acima e atualize o navegador. O detalhe técnico completo aparece no terminal onde o servidor está rodando.'

// --- placeholder banner (D-11/D-12; purely informational — no dismiss) ---
export const BANNER_TITLE = 'Dados de exemplo'
export const BANNER_SUBTITLE =
  'Você está vendo dados fictícios. Substitua o conteúdo de content/profile.md pelos seus dados reais — este aviso desaparece quando a marcação example: true for removida do arquivo.'

// --- completeness grid (labels keyed to compute_completude sections, D-12) ---
export const COMPLETENESS_TITLE = 'Completude por seção'
export const COMPLETENESS_LABELS = {
  resumo: 'Resumo',
  experiencias: 'Experiência',
  educacao: 'Formação',
  habilidades: 'Habilidades',
  certificacoes: 'Certificações',
  idiomas: 'Idiomas',
  projetos: 'Projetos',
} as const

// Section counts, PT-BR: "3 experiências", "8 impactos", …
export const COMPLETENESS_UNIT = {
  experiencias: 'experiência',
  experienciasPlural: 'experiências',
  impactos: 'impacto',
  impactosPlural: 'impactos',
  itens: 'item',
  itensPlural: 'itens',
} as const

// --- profile preview (D-12: resume-style render of the profile) ---
export const PREVIEW_TITLE = 'Pré-visualização do perfil'
export const PREVIEW_SECTIONS = {
  resumo: 'Resumo',
  experiencia: 'Experiência',
  formacao: 'Formação',
  habilidades: 'Habilidades',
  certificacoes: 'Certificações',
  idiomas: 'Idiomas',
  projetos: 'Projetos',
} as const
export const PREVIEW_PRESENT = 'atual'
export const PREVIEW_CONTACT_SEPARATOR = ' · '
