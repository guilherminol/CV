// PT-BR UI strings — one user, one UI language; no i18n framework (STACK.md).

export const APP_TITLE = 'Career Tailor'

export const NAV_ITEMS = [
  { id: 'curriculo', label: 'Currículo', enabled: true },
  { id: 'perfil', label: 'Perfil', enabled: true },
  { id: 'linkedin', label: 'LinkedIn', enabled: true },
  { id: 'candidatura', label: 'Candidatura', enabled: true },
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
// Promoted from CurriculoHome in plan 05-02 (UI-SPEC IN-04): the JD form
// textarea AND the SectionEditor textarea share this ONE definition so the
// editor can never drift from the form's visual base.
export const TEXTAREA_CLASSES =
  'min-h-40 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm leading-6 text-gray-900 placeholder:text-gray-400 focus-visible:border-blue-600 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600'
// Badge class strings (D-04 tri-state): the solid-blue Editado state is the
// phase's only new accent; Gerado's soft-blue classes were previously inline
// in ResumeResult and are promoted here so SectionVersionsPanel's origin
// badges reuse the exact same strings (IN-04).
export const BADGE_GERADO_CLASSES =
  'normal-case rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700'
export const BADGE_EDITADO_CLASSES =
  'normal-case rounded-full border border-blue-600 bg-blue-600 px-2 py-1 text-xs font-semibold text-white'

// --- currículo screen (UI-SPEC Copywriting Contract, plan 03-04) ---
export const CURRICULO_PAGE_TITLE = 'Currículo'
export const CURRICULO_EMPTY_TITLE = 'Comece pela vaga'
export const CURRICULO_EMPTY_BODY =
  'Cole a descrição da vaga e escolha o idioma — o currículo é gerado a partir do seu perfil.'
export const CURRICULO_JD_LABEL = 'Descrição da vaga'
export const CURRICULO_JD_PLACEHOLDER = 'Cole aqui o texto completo da vaga…'
export const CURRICULO_JD_TOO_SHORT_HINT =
  'Cole a descrição da vaga (mínimo 80 caracteres) para habilitar a geração.'
// WR-01: shown when the JD hits the client-side cap (textarea maxLength) —
// the backend rejects >20000 chars with an unretryable 422, so the input is
// capped at the same bound and the cap states itself instead of failing.
export const CURRICULO_JD_TOO_LONG_HINT =
  'Limite de 20.000 caracteres atingido — o texto excedente não faz parte da descrição.'
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
export const BADGE_EDITADO = 'Editado'
export const CURRICULO_EPHEMERAL_NOTICE =
  'Este resultado existe apenas nesta página — atualizar ou fechar o navegador perde o conteúdo. Copie o que quiser guardar.'
export const CURRICULO_REGENERAR = 'Gerar novamente'

export const CURRICULO_KEYWORDS_TITLE = 'Keywords da vaga e cobertura'// {covered}/{total} interpolation slots — plain factual tally ONLY:
// never a percentage, score, or progress meter (RESUME-04; REQUIREMENTS Out of Scope).
export const CURRICULO_COBERTURA_SINGULAR =
  '{covered} de {total} keyword da vaga aparece no currículo.'
export const CURRICULO_COBERTURA_PLURAL =
  '{covered} de {total} keywords da vaga aparecem no currículo.'
export const CURRICULO_KEYWORD_COBERTO = 'no currículo'
export const CURRICULO_KEYWORD_AUSENTE = 'ausente'
export const CURRICULO_KEYWORDS_EMPTY = 'Nenhuma keyword foi extraída desta vaga.'

// Vaga → perfil (keyword acceptance): the chip button adds the keyword to the
// owner's profile via POST /api/profile/adicionar; titles have no profile home.
export const CURRICULO_KEYWORD_ADD_LABEL = '+ Perfil'
export const CURRICULO_KEYWORD_ADD_ARIA = 'Adicionar ao meu perfil'
export const CURRICULO_KEYWORD_NO_PERFIL = 'Já está no seu perfil'
export const CURRICULO_KEYWORD_ADICIONANDO = 'Adicionando…'
export const CURRICULO_KEYWORD_ADD_ERRO =
  'Não foi possível adicionar ao perfil — tente novamente; o detalhe técnico aparece no terminal.'

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

// --- export content selection (quick task 261006-oy9, D-01/D-02): the
// presentational PDF filter on the result screen — nothing here changes the
// generated text. Section labels keyed by run language: pt-BR values match
// PREVIEW_SECTIONS exactly; en values match render.py HEADINGS['en'] (the
// PDF's own heading map) so the panel names sections the way the document
// prints them. ---
export const SELECAO_TITLE = 'Seleção do conteúdo do PDF'
export const SELECAO_CAPTION =
  'Escolha o que entra na versão final em PDF — nada aqui altera o texto gerado.'
export const SELECAO_SECOES = {
  'pt-BR': {
    resumo: 'Resumo',
    experiencias: 'Experiência',
    formacao: 'Formação',
    habilidades: 'Habilidades',
    certificacoes: 'Certificações',
    idiomas: 'Idiomas',
    projetos: 'Projetos',
  },
  en: {
    resumo: 'Summary',
    experiencias: 'Experience',
    formacao: 'Education',
    habilidades: 'Skills',
    certificacoes: 'Certifications',
    idiomas: 'Languages',
    projetos: 'Projects',
  },
} as const
// WR-01 client mirror: with every section unchecked the backend answers 422
// (SelecaoExportacao's all-false validator) — the export CTA is disabled at
// the source with this hint instead of ever reaching that dead end.
export const SELECAO_SEM_SECAO =
  'Selecione ao menos uma seção para exportar o PDF.'

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

// --- inline editing + version stack + confirm strips (UI-SPEC Copywriting
// Contract, plan 05-02): D-02 policy line, D-04 badge, D-12 editor, D-08
// versions, D-14 amber confirm strips. {secao} = PT-BR section label even on
// EN runs (UI language convention). ---
// D-02 permanent edit-policy line (card header + editor footer).
export const POLICY_EDICAO =
  'Edições valem apenas para esta execução — atualizar a página descarta.'
// D-12 section/entry edit controls.
export const EDITAR_SECAO_CTA = 'Editar seção'
export const EDITAR_ENTRADA_CTA = 'Editar entrada'
export const EDITAR_ARIA_LABEL = 'Editar {secao}'
export const SALVAR_ALTERACOES_CTA = 'Salvar alterações'
export const CANCELAR_EDICAO_CTA = 'Cancelar edição'
export const EDIT_SAVE_GUARD = 'Guarde pelo menos um item — a seção não pode ficar vazia.'
// Dirty-cancel confirm strip (inline amber — never a browser dialog).
export const CANCELAR_SUJA_MESSAGE = 'Descartar as alterações desta edição?'
export const CONTINUAR_EDITANDO_CTA = 'Continuar editando'
export const DESCARTAR_ALTERACOES_CTA = 'Descartar alterações'
// D-14 confirm strip: section regen over an edited/dirty section.
export const REGEN_SOBE_EDICAO_MESSAGE = 'Isso vai descartar sua edição — continuar?'
export const REGEN_SOBE_EDICAO_NOTE = 'A edição atual fica guardada em Versões.'
export const MANTER_EDICAO_CTA = 'Manter edição'
export const REGEN_MESMO_ASSIM_CTA = 'Regenerar mesmo assim'
// D-14 confirm strip: full regeneration with edited sections.
export const GERAR_COM_EDICOES_MESSAGE =
  'Isso vai substituir suas edições — cada versão atual fica guardada em Versões. Continuar?'
export const MANTER_EDICOES_CTA = 'Manter edições'
export const GERAR_MESMO_ASSIM_CTA = 'Gerar mesmo assim'
// D-08 per-section version stack (plan 05-02, Task 2).
export const VERSOES_TOGGLE = 'Versões'
export const VERSOES_TOGGLE_COUNT = 'Versões ({count})'
export const VERSOES_INTRO = 'Versões anteriores desta seção — mais recente primeiro.'
export const RESTAURAR_VERSAO_CTA = 'Restaurar versão'
// IN-03: per-ENTRY stacks orphaned by a count-changing swap (indices beyond
// the CURRENT experiências list) stay visible inside the group Versões
// panel — never silently unreachable ("never capped, never silently
// dropped"); Restaurar stays disabled because the indexed entry no longer
// exists to restore into.
export const VERSOES_EXPERIENCIA_ORFAAS_NOTA =
  'Versões de entradas de execuções anteriores — a entrada correspondente não existe mais nesta lista, então não podem ser restauradas.'

// --- fact-vs-generated comparison (UI-SPEC Copywriting Contract, plan 05-03):
// D-09 two-column panel, D-10 deterministic amber marks, D-11 "suspicion, not
// verdict" framing. ---
export const COMPARACAO_TOGGLE = 'Comparar com o perfil'
export const COMPARACAO_TOGGLE_HIDE = 'Ocultar comparação'
// Accessible name of the open panel (the UI-SPEC pins no visible panel title).
export const COMPARACAO_PANEL_LABEL = 'Comparação com o perfil'
export const COMPARACAO_HEADER_FATOS = 'Fatos do perfil'
export const COMPARACAO_HEADER_TEXTO = 'Texto no currículo'
// sr-only suffix per mark — status never conveyed by color alone (UI-SPEC).
export const COMPARACAO_MARK_SR_ONLY = ' (não consta no perfil)'
// D-11: the mandatory legend whenever ≥1 mark exists — mechanical suspicion,
// user judgment; paraphrases can legitimately be flagged.
export const COMPARACAO_LEGENDA =
  'Os destaques em âmbar são termos que não constam nos fatos do perfil. A comparação é mecânica — paráfrases legítimas podem ser destacadas. Confira você mesmo antes de exportar.'
// Loud zero line when the panel has zero marks — never a silently unmarked panel.
export const COMPARACAO_ZERO_SUSPEITOS =
  'Nenhum termo suspeito nesta seção — todo o texto casa com os fatos do perfil.'
// Neutral fallback note (05-RESEARCH Pitfall 8): when no profile entry
// fold-matches the generated company, the panel shows ALL profile entries —
// never an empty facts column.
export const COMPARACAO_FALLBACK_NOTA =
  'Nenhuma entrada do perfil casa com o nome desta empresa — todos os registros do perfil são mostrados para comparação.'

// --- LinkedIn screen (UI-SPEC Copywriting Contract, plan 06-01) ---
// WR-01 client mirrors of the backend config constants (backend/app/config.py
// Phase 6 block): LINKEDIN_OBJETIVO_MIN_LENGTH / LINKEDIN_OBJETIVO_MAX_LENGTH,
// LINKEDIN_HEADLINE_MAX_CHARS, LINKEDIN_SOBRE_MAX_CHARS,
// LINKEDIN_EXPERIENCIA_MAX_CHARS. Change BOTH together — the textarea caps,
// editor maxLengths and the CTA gate mirror the server bounds so an oversized
// input is prevented, never retried into a dead-end 422. No client mirror for
// the skills count: no per-list character limit exists (D-05 forbids
// inventing one — the count line is honest, never "/Y").
export const LINKEDIN_OBJETIVO_MIN_CHARS = 80
export const LINKEDIN_OBJETIVO_MAX_CHARS = 2000
export const LINKEDIN_HEADLINE_MAX_CHARS = 220
export const LINKEDIN_SOBRE_MAX_CHARS = 2600
export const LINKEDIN_EXPERIENCIA_MAX_CHARS = 2000

export const LINKEDIN_PAGE_TITLE = 'LinkedIn'
export const LINKEDIN_EMPTY_TITLE = 'Comece pelo objetivo'
export const LINKEDIN_EMPTY_BODY =
  'Descreva seu objetivo de carreira e escolha o idioma — as seções do LinkedIn são geradas a partir do seu perfil.'
export const LINKEDIN_OBJETIVO_LABEL = 'Objetivo de carreira'
export const LINKEDIN_OBJETIVO_PLACEHOLDER =
  'Ex.: crescer como engenheiro de dados sênior, com foco em Python, SQL e plataformas de dados em nuvem…'
// {min} / {max} interpolation slots — plain template replace (house pattern).
export const LINKEDIN_OBJETIVO_TOO_SHORT_HINT =
  'Descreva seu objetivo (mínimo {min} caracteres) para habilitar a geração.'
export const LINKEDIN_OBJETIVO_TOO_LONG_HINT =
  'Limite de {max} caracteres atingido — o texto excedente não faz parte do objetivo.'
export const LINKEDIN_IDIOMA_LABEL = 'Idioma das seções'
export const LINKEDIN_CTA = 'Gerar seções LinkedIn'
export const LINKEDIN_CTA_INFLIGHT = 'Gerando seções LinkedIn…'
export const LINKEDIN_INFLIGHT_HINT =
  'Quatro blocos são gerados em sequência — headline, sobre, experiências e habilidades. Pode levar até um minuto.'
export const LINKEDIN_ERROR_TITLE = 'Não foi possível gerar as seções LinkedIn'
// Gerar error hint + retry reuse the Currículo copy verbatim (UI-SPEC).
export const LINKEDIN_RESULT_TITLE = 'Seções LinkedIn geradas'
// Block labels are PT-BR UI labels EVEN ON EN RUNS (house convention).
export const LINKEDIN_BLOCK_LABELS = {
  headline: 'Headline',
  sobre: 'Sobre',
  experiencias: 'Experiência',
  habilidades: 'Habilidades',
} as const
// {count}/{limite} interpolation slot — the CharacterCounter formats it.
export const LINKEDIN_COUNTER = '{count}/{limite} caracteres'
// D-07 over-limit flag: nothing is ever truncated — the flag + per-section
// regen are the fix path; Copiar stays enabled (the flag warns, the user decides).
export const LINKEDIN_OVERLIMIT_FLAG =
  'Passou do limite em {excesso} caracteres — regenere a seção ou edite o texto para caber.'
// D-08 copy pair: the displayed text IS what goes to the clipboard.
export const LINKEDIN_COPIAR = 'Copiar'
export const LINKEDIN_COPIADO = 'Copiado!'
export const LINKEDIN_COPIAR_FALHA =
  'Não foi possível copiar automaticamente — selecione o texto da seção e copie manualmente.'

// Zone 2 lint (D-03): title + clear line are LinkedIn-scoped (the objective
// replaces the JD); backend avisos[] lines render VERBATIM — no per-line
// frontend constants, by design. The hint + fetch-failure line reuse the
// Currículo constants (UI-SPEC "reused" rows: CURRICULO_LINT_HINT /
// CURRICULO_LINT_FETCH_ERRO).
export const LINKEDIN_LINT_TITLE = 'Lacunas do perfil para este objetivo'
export const LINKEDIN_LINT_CLEAR = 'Nenhum gap relevante encontrado para este objetivo.'

// Experiência group zero line (probe edge LI-04/empty): loud muted — never a
// silent empty block. WR-05: the line is differentiated per CAUSE — the
// profile-empty arm (the documented legitimate display state, now reachable
// after gerar) vs the list-empty arm (generated list came back empty while
// the profile HAS experiences — unreachable after the backend's
// profile-aware guard, kept loud as a defensive state that never claims the
// profile is the cause).
export const LINKEDIN_EXPERIENCIA_ZERO =
  'Nenhuma experiência no perfil — nada para reescrever aqui.'
export const LINKEDIN_EXPERIENCIA_LISTA_ZERO =
  'Nenhuma experiência foi gerada nesta execução.'

// Skills count line (UI-SPEC skills-counter exception, honest-information
// rule): LinkedIn imposes no total character limit on the skills list and
// D-05 forbids inventing one, so the counter slot carries the pure ENTRY
// count — singular/plural via a pure function (offline-testable per house
// policy), never a fake "/Y".
export const LINKEDIN_SKILLS_CONTAGEM_SINGULAR = '1 skill em ordem de prioridade.'
export const LINKEDIN_SKILLS_CONTAGEM_PLURAL = '{n} skills em ordem de prioridade.'

/** Pure singular/plural formatter for the skills count line (0 is a legitimate
 *  skills-less-profile display state → plural). */
export function formatarSkillsContagem(n: number): string {
  return n === 1
    ? LINKEDIN_SKILLS_CONTAGEM_SINGULAR
    : LINKEDIN_SKILLS_CONTAGEM_PLURAL.replace('{n}', String(n))
}

// D-12 inline editor over-limit save guard (WR-01 mirror — an oversized save
// must never become a dead-end 422): Salvar alterações is disabled while the
// draft exceeds the block limit, with the reduce-first hint. {excesso} slot.
// The case that makes the guard real: backend output can legitimately arrive
// OVER the limit (D-07 — flagged, never truncated), so the editor pre-fill
// can start over-limit and must not be savable until reduced.
export const LINKEDIN_EDIT_OVERLIMIT_HINT =
  'O texto excede o limite em {excesso} caracteres — reduza antes de salvar.'

// WR-01 client mirror of the backend regen dica bound (routes/linkedin.py
// Field(max_length=500) on LinkedinRegenerarRequest.dica). Change BOTH
// together — the hint input caps at the same bound.
export const LINKEDIN_DICA_MAX_CHARS = 500

// Comparison LinkedIn variants (UI-SPEC copy table): the right-column header
// and the legend ending adapt to this phase's deliverable ("...antes de
// copiar."); the zero-suspects line, the fallback note, the sr-only mark
// suffix and the toggle labels reuse the Currículo constants verbatim.
export const LINKEDIN_COMPARACAO_HEADER_TEXTO = 'Texto no LinkedIn'
export const LINKEDIN_COMPARACAO_LEGENDA =
  'Os destaques em âmbar são termos que não constam nos fatos do perfil. A comparação é mecânica — paráfrases legítimas podem ser destacadas. Confira você mesmo antes de copiar.'

// --- QA panel "Verificação de idioma" (UI-SPEC Copywriting Contract, plan
// 06-05; backend payload from app/linkedin/qa.py via the 06-04 envelope).
// The panel renders payload rows VERBATIM — no per-row frontend constants,
// by design (same rule as backend avisos[]). The legend ALWAYS renders with
// the non-blocking framing — the panel never gates Copiar (D-14). On EN runs
// (qa === null) the neutral note replaces the two blocks — never silently
// absent (D-14/SC4).
export const QA_PANEL_TITLE = 'Verificação de idioma'
export const QA_GLOSSARIO_LABEL = 'Glossário aplicado'
export const QA_BLEED_LABEL = 'Inglês em texto em português'
// Loud zero lines (UI-SPEC empty states) — QA blocks are never silently empty.
export const QA_GLOSSARIO_ZERO =
  'Nenhum termo do glossário foi aplicado — as seções já usavam os termos preferidos.'
export const QA_BLEED_ZERO =
  'Nenhum termo em inglês foi detectado nas seções em português.'
// Legend (always rendered, mechanical + non-blocking framing).
export const QA_LEGENDA =
  'A verificação é mecânica e não bloqueia a cópia — termos técnicos consolidados em inglês podem ser sinalizados. Avalie você mesmo antes de copiar.'
// EN-run neutral note (qa === null — the 06-04 language gate).
export const QA_EN_NOTE =
  'A verificação de idioma se aplica às saídas em PT-BR — esta execução gerou conteúdo em inglês.'

// --- Candidatura (perguntas abertas de formulário de candidatura) ---
export const CANDIDATURA_PAGE_TITLE = 'Resposta de candidatura'
export const CANDIDATURA_HINT =
  'Cole a pergunta aberta do formulário — a resposta é gerada a partir do seu perfil, no idioma escolhido. Revise antes de usar: só o que está no seu perfil pode aparecer.'
export const CANDIDATURA_PERGUNTA_LABEL = 'Pergunta da candidatura'
export const CANDIDATURA_PERGUNTA_PLACEHOLDER =
  'Ex.: Descreva sua última experiência e o principal resultado que você entregou.'
export const CANDIDATURA_VAGA_LABEL = 'Descrição da vaga (opcional)'
export const CANDIDATURA_VAGA_PLACEHOLDER =
  'Cole a descrição da vaga para alinhar a resposta — pode deixar vazio.'
export const CANDIDATURA_CTA = 'Gerar resposta'
export const CANDIDATURA_CTA_INFLIGHT = 'Gerando resposta…'
export const CANDIDATURA_RESULT_TITLE = 'Resposta gerada'
export const CANDIDATURA_EPHEMERAL_NOTICE =
  'Esta resposta existe apenas nesta página — copie o que quiser guardar.'
