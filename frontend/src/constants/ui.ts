// PT-BR UI strings — one user, one UI language; no i18n framework (STACK.md).

export const APP_TITLE = 'Career Tailor'

export const NAV_ITEMS = [
  { id: 'curriculo', label: 'Currículo', enabled: true },
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

export const COMPLETENESS_OK = 'preenchida'
export const COMPLETENESS_EMPTY = 'vazio'

// Section counts, PT-BR: "3 experiências", "8 impactos", …
export const COMPLETENESS_UNIT = {
  experiencias: 'experiência',
  experienciasPlural: 'experiências',
  impactos: 'impacto',
  impactosPlural: 'impactos',
  itens: 'item',
  itensPlural: 'itens',
  grupos: 'grupo', // WR-04: habilidades_qtde counts categorized groups
  gruposPlural: 'grupos',
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

// --- pinned class strings (UI-SPEC Component conventions) ---
// Single definition of the primary CTA classes — imported by CurriculoHome
// AND ExportZone (IN-04: the "never redefined" rule previously lived as two
// module-local copies that could silently drift).
export const PRIMARY_BUTTON_CLASSES =
  'min-h-10 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
// Phase 5 section-action-row controls (UI-SPEC Component conventions, plan 05-01)
// — promoted to constants for the same IN-04 single-definition rule.
export const QUIET_BUTTON_CLASSES =
  'rounded text-xs font-semibold text-gray-600 underline-offset-2 hover:text-gray-900 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
export const COMPACT_SECONDARY_BUTTON_CLASSES =
  'inline-flex min-h-9 items-center rounded-md border border-gray-300 bg-white px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
export const HINT_INPUT_CLASSES =
  'w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus-visible:border-blue-600 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600'

// --- currículo screen (UI-SPEC Copywriting Contract, plan 03-04) ---
export const CURRICULO_PAGE_TITLE = 'Currículo'
export const CURRICULO_EMPTY_TITLE = 'Comece pela vaga'
export const CURRICULO_EMPTY_BODY =
  'Cole a descrição da vaga e escolha o idioma — o currículo é gerado a partir do seu perfil.'
export const CURRICULO_JD_LABEL = 'Descrição da vaga'
export const CURRICULO_JD_PLACEHOLDER = 'Cole aqui o texto completo da vaga…'
export const CURRICULO_JD_TOO_SHORT_HINT =
  'Cole a descrição da vaga (mínimo 80 caracteres) para habilitar a geração.'
export const CURRICULO_IDIOMA_LABEL = 'Idioma do currículo'
export const CURRICULO_IDIOMA_OPTIONS = {
  'pt-BR': 'Português (BR)',
  en: 'English',
} as const
export const CURRICULO_CTA = 'Gerar currículo'
export const CURRICULO_CTA_INFLIGHT = 'Gerando currículo…'
export const CURRICULO_INFLIGHT_HINT =
  'As três seções são geradas em sequência — resumo, experiência, habilidades. Pode levar até um minuto.'

// Lint: aviso item LINES come from the backend and render verbatim (D-13/D-14)
// — no per-item constants live here, by design.
export const CURRICULO_LINT_TITLE = 'Lacunas do perfil para esta vaga'
export const CURRICULO_LINT_CLEAR = 'Nenhum gap relevante encontrado para esta vaga.'
export const CURRICULO_LINT_HINT =
  'Você pode gerar mesmo com avisos — resolvê-los antes deixa o resultado mais forte.'
// Zone 2 fetch-level failure (server down / non-200 → lintQuery.isError):
// generic PT-BR hint only — raw detail is terminal-only (D-08 split), the
// same fail-loud convention as the gerar/exportar erros=[] panels (WR-02).
export const CURRICULO_LINT_FETCH_ERRO =
  'Não foi possível verificar a vaga. Tente novamente — o detalhe técnico completo aparece no terminal onde o servidor está rodando.'

export const CURRICULO_RESULT_TITLE = 'Currículo gerado'
export const BADGE_GERADO = 'Gerado'
export const BADGE_DO_PERFIL = 'Do perfil'
export const CURRICULO_EPHEMERAL_NOTICE =
  'Este resultado existe apenas nesta página — atualizar ou fechar o navegador perde o conteúdo. Copie o que quiser guardar.'
export const CURRICULO_REGENERAR = 'Gerar novamente'

export const CURRICULO_KEYWORDS_TITLE = 'Keywords da vaga e cobertura'
// {covered}/{total} interpolation slots — plain factual tally ONLY:
// never a percentage, score, or progress meter (RESUME-04; REQUIREMENTS Out of Scope).
export const CURRICULO_COBERTURA_SINGULAR =
  '{covered} de {total} keyword da vaga aparece no currículo.'
export const CURRICULO_COBERTURA_PLURAL =
  '{covered} de {total} keywords da vaga aparecem no currículo.'
export const CURRICULO_KEYWORD_COBERTO = 'no currículo'
export const CURRICULO_KEYWORD_AUSENTE = 'ausente'
export const CURRICULO_KEYWORDS_EMPTY = 'Nenhuma keyword foi extraída desta vaga.'

// Category labels are UI-only renderings of the schema tokens (Phase 2 D-10);
// CATEGORY_ORDER pins the display order — empty categories are skipped, not shown.
export const CATEGORY_LABELS = {
  competencias: 'Competências',
  ferramentas: 'Ferramentas',
  titulos_de_vaga: 'Títulos de vaga',
  certificacoes: 'Certificações',
} as const
export const CATEGORY_ORDER = [
  'competencias',
  'ferramentas',
  'titulos_de_vaga',
  'certificacoes',
] as const

export const CURRICULO_ERROR_TITLE = 'Não foi possível gerar o currículo'
export const CURRICULO_ERROR_HINT =
  'Tente novamente. Se o problema persistir, o detalhe técnico completo aparece no terminal onde o servidor está rodando.'
export const CURRICULO_ERROR_RETRY = 'Tentar novamente'

// Generated-section headings in the run language (passthrough sections reuse
// the PREVIEW_SECTIONS PT-BR labels — UI language convention, D-04).
export const CURRICULO_GENERATED_SECTIONS = {
  'pt-BR': { resumo: 'Resumo', experiencias: 'Experiência', habilidades: 'Habilidades' },
  en: { resumo: 'Summary', experiencias: 'Experience', habilidades: 'Skills' },
} as const

// --- export + self-check (UI-SPEC Copywriting Contract, plan 04-03) ---
export const EXPORTAR_CTA = 'Exportar PDF'
export const EXPORTAR_CTA_INFLIGHT = 'Exportando PDF…'
export const EXPORTAR_CAPTION =
  'O download começa automaticamente após a verificação ATS do arquivo.'
export const EXPORTAR_INFLIGHT_HINT = 'Renderizando o PDF e executando a verificação ATS…'
// {filename} interpolation slot — the backend-generated download name (D-11),
// rendered as plain wrapped text (never truncated).
export const EXPORTAR_RECEIPT = 'PDF exportado e verificado — {filename}'
export const EXPORTAR_ERROR_TITLE = 'Não foi possível exportar o PDF'
// Backend gate-failure lines render VERBATIM between title and hint — no
// per-line frontend constants, by design (D-13/D-14 division of labor).
export const EXPORTAR_ERROR_HINT =
  'Tente exportar novamente. O detalhe técnico completo aparece no terminal onde o servidor está rodando.'

export const SELFCHECK_TITLE = 'Verificação ATS do PDF'
export const SELFCHECK_ORDEM_LABEL = 'Ordem das seções'
export const SELFCHECK_CONTATO_LABEL = 'Contato no topo'
// Map render.section_keys ids (plan 04-02: resumo, experiencias, formacao,
// habilidades, certificacoes, idiomas, projetos) → PT-BR labels; values copied
// from PREVIEW_SECTIONS + the Contato entry. Unknown ids render raw — never
// silently dropped (D-14).
export const SELFCHECK_ORDEM_LABELS = {
  contato: 'Contato no topo',
  resumo: 'Resumo',
  experiencias: 'Experiência',
  formacao: 'Formação',
  habilidades: 'Habilidades',
  certificacoes: 'Certificações',
  idiomas: 'Idiomas',
  projetos: 'Projetos',
} as const
export const SELFCHECK_SOBREVIVENCIA_LABEL = 'Sobrevivência de keywords'
// {survived}/{total} interpolation slots — plain factual tally ONLY:
// never a percentage, score, or progress meter (REQUIREMENTS Out of Scope).
export const SELFCHECK_SOBREVIVENCIA_SINGULAR =
  '{survived} de {total} keyword da vaga aparece no PDF exportado.'
export const SELFCHECK_SOBREVIVENCIA_PLURAL =
  '{survived} de {total} keywords da vaga aparecem no PDF exportado.'
export const SELFCHECK_KEYWORD_NO_PDF = 'no PDF'
export const SELFCHECK_KEYWORD_AUSENTE = 'ausente no PDF'
export const SELFCHECK_KEYWORDS_ZERO =
  'Nenhuma keyword foi extraída nesta execução — nada para verificar no PDF.'
export const SELFCHECK_GATE_FOOTER =
  'Antes do download, o gate automático também provou empresa, cargo e datas juntos em cada experiência e acentos intactos na camada de texto.'

// --- per-section regeneration (UI-SPEC Copywriting Contract, plan 05-01) ---
// {secao} interpolation slots — plain template replace, never a formatter
// library. The section name is the PT-BR label EVEN ON EN RUNS (UI language
// convention); backend erros[] lines render verbatim — no per-line constants.
export const REGEN_SECAO_LABELS = {
  resumo: 'Resumo',
  experiencias: 'Experiência',
  habilidades: 'Habilidades',
} as const
export const REGEN_SECTION_CTA = 'Regenerar seção'
export const REGEN_SECTION_INFLIGHT = 'Regenerando {secao}…'
export const REGEN_INFLIGHT_LINE =
  'Regenerando {secao}… as outras seções permanecem inalteradas.'
export const DICA_TOGGLE_ADD = 'Adicionar dica'
export const DICA_TOGGLE_HIDE = 'Ocultar dica'
export const DICA_LABEL = 'Dica para esta seção (opcional)'
export const DICA_PLACEHOLDER = 'Ex.: destacar experiência com métricas de impacto'
export const REGEN_ERROR_TITLE = 'Não foi possível regenerar {secao}'
export const REGEN_ERROR_HINT =
  'Tente regenerar novamente. O detalhe técnico completo aparece no terminal onde o servidor está rodando.'
