import type {
  ExperienciaGeradaDTO,
  LocalizedText,
  PerfilDTO,
  ProjectDTO,
  ResumeLanguage,
  SecoesDTO,
  SelecaoExportacaoDTO,
} from '../api/client'
import { SELECAO_CAPTION, SELECAO_SECOES, SELECAO_TITLE } from '../constants/ui'

// Pinned class strings (UI-SPEC Component conventions — the card base is the
// same family CurriculoHome/ResumeResult pin; no redefinition of shared
// constants, only this panel's local composition).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
const CHECKBOX_CLASSES =
  'h-4 w-4 rounded border-gray-300 text-blue-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed'
const SECTION_LABEL_CLASSES = 'flex items-center gap-2 text-sm font-medium text-gray-900'
const ITEM_LABEL_CLASSES = 'flex items-center gap-2 text-sm text-gray-700'

/** D-05 render order — the seven sections in the exact order the document
 *  prints them (render.py section_keys / PREVIEW order). */
const SECAO_ORDEM = [
  'resumo',
  'experiencias',
  'formacao',
  'habilidades',
  'certificacoes',
  'idiomas',
  'projetos',
] as const

type SecaoId = (typeof SECAO_ORDEM)[number]

/** Group labels for Project.scope — the ResumeResult convention (profissional
 *  first, run-language labels matching the PDF's SCOPE_LABELS). */
const SCOPE_LABELS: Record<'profissional' | 'pessoal', Record<ResumeLanguage, string>> = {
  profissional: { 'pt-BR': 'Projetos profissionais', en: 'Professional projects' },
  pessoal: { 'pt-BR': 'Projetos pessoais', en: 'Personal projects' },
}

/**
 * tLang convention (ResumeResult.tsx file-local copy): EN runs prefer `en`
 * falling back to the pt-BR base (schema-guaranteed); PT-BR runs keep
 * pt-BR-first. Plain-str fields pass through — a brand name is valid content.
 */
function tLang(
  map: LocalizedText | string | null | undefined,
  language: ResumeLanguage,
): string {
  if (!map) return ''
  if (typeof map === 'string') return map
  if (language === 'en') {
    return map.en ?? map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
  }
  return map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
}

function range(total: number): number[] {
  return Array.from({ length: total }, (_, i) => i)
}

/**
 * Item-toggle index math (mirrors the backend enumerate-membership filter):
 * unchecking an item of an "all" selection materializes the complement list;
 * re-checking until EVERY item is selected dissolves the list back to
 * undefined (the wire shape for "all", matching SelecaoExportacaoDTO).
 * Indices stay ascending — order is display order, never user intent.
 */
function proximosIndices(selecionados: number[], total: number, idx: number): number[] | undefined {
  const conjunto = new Set(selecionados)
  if (conjunto.has(idx)) {
    conjunto.delete(idx)
  } else {
    conjunto.add(idx)
  }
  if (conjunto.size === total) return undefined // all selected → omit the key
  return range(total).filter((i) => conjunto.has(i))
}

interface ExportSelectionProps {
  /** The mounted profile — source of the projects item list (the perfil DTO
   *  travels verbatim into the export payload). */
  perfil: PerfilDTO
  /** The generated sections — source of the experiencias item list. */
  secoes: SecoesDTO
  /** Run language — section labels localize like the PDF headings. */
  idioma: ResumeLanguage
  /** Current selection state (owned by CurriculoHome). */
  selecao: SelecaoExportacaoDTO
  /** Whole-object replacement on every toggle — the parent owns the state. */
  onChange: (next: SelecaoExportacaoDTO) => void
  /** Locked while any long operation runs or an editor is open (locksEdicao). */
  disabled: boolean
}

/**
 * Zone 6 export content selection (quick task 261006-oy9, D-01/D-02) — a
 * render-only presentational panel: no fetch, no mutation, no receipt/error
 * state of its own. Seven section toggles in render order; item-level
 * checkboxes nested under experiencias (company — title) and projetos
 * (grouped by scope, profissional first). Semantics mirror the backend
 * SelecaoExportacao exactly: an unchecked section excludes it wholesale (its
 * items gray out); a checked section with no explicit indices means ALL
 * items; toggling items maintains the index arrays, dissolving to
 * undefined when everything is selected again. All text renders as JSX text
 * children — no raw-HTML injection path (T-04-07 posture). No new deps.
 */
export function ExportSelection({
  perfil,
  secoes,
  idioma,
  selecao,
  onChange,
  disabled,
}: ExportSelectionProps) {
  const labels = SELECAO_SECOES[idioma]
  const expIndices = selecao.experiencias_indices ?? range(secoes.experiencias.length)
  const projIndices = selecao.projetos_indices ?? range(perfil.projects.length)

  const toggleSecao = (secao: SecaoId, checked: boolean) =>
    onChange({ ...selecao, [secao]: checked })

  const toggleExperiencia = (idx: number) =>
    onChange({
      ...selecao,
      experiencias_indices: proximosIndices(expIndices, secoes.experiencias.length, idx),
    })

  const toggleProjeto = (idx: number) =>
    onChange({
      ...selecao,
      projetos_indices: proximosIndices(projIndices, perfil.projects.length, idx),
    })

  return (
    <section className={CARD_CLASSES} aria-label={SELECAO_TITLE}>
      <h3 className="text-base font-semibold text-gray-900">{SELECAO_TITLE}</h3>
      <p className="mt-1 text-sm text-gray-600">{SELECAO_CAPTION}</p>

      <div className="mt-4 space-y-3">
        {SECAO_ORDEM.map((secao) => {
          const ligada = selecao[secao]
          const temItens = secao === 'experiencias' ? secoes.experiencias.length > 0 : secao === 'projetos' ? perfil.projects.length > 0 : false
          return (
            <div key={secao}>
              <label className={SECTION_LABEL_CLASSES}>
                <input
                  type="checkbox"
                  checked={ligada}
                  onChange={(event) => toggleSecao(secao, event.target.checked)}
                  disabled={disabled}
                  className={CHECKBOX_CLASSES}
                />
                {labels[secao]}
              </label>

              {/* Item granularity (D-01) — experiencias: one checkbox per
                  generated entry, grayed out while the section is off. */}
              {secao === 'experiencias' && temItens && (
                <div className={`ml-6 mt-1 space-y-1 ${ligada ? '' : 'opacity-50'}`}>
                  {secoes.experiencias.map((exp: ExperienciaGeradaDTO, idx: number) => (
                    <label key={`${idx}-${exp.company}`} className={ITEM_LABEL_CLASSES}>
                      <input
                        type="checkbox"
                        checked={expIndices.includes(idx)}
                        onChange={() => toggleExperiencia(idx)}
                        disabled={disabled || !ligada}
                        className={CHECKBOX_CLASSES}
                      />
                      {exp.company} — {exp.title}
                    </label>
                  ))}
                </div>
              )}

              {/* Item granularity (D-01) — projetos: grouped by scope
                  (profissional first), name resolved via tLang. */}
              {secao === 'projetos' && temItens && (
                <div className={`ml-6 mt-1 space-y-2 ${ligada ? '' : 'opacity-50'}`}>
                  {(['profissional', 'pessoal'] as const).map((scope) => {
                    const itens: { projeto: ProjectDTO; idx: number }[] = perfil.projects
                      .map((projeto, idx) => ({ projeto, idx }))
                      .filter(({ projeto }) => projeto.scope === scope)
                    if (itens.length === 0) return null
                    return (
                      <div key={scope}>
                        <p className="text-xs font-semibold text-gray-500">
                          {SCOPE_LABELS[scope][idioma]}
                        </p>
                        {itens.map(({ projeto, idx }) => (
                          <label key={idx} className={ITEM_LABEL_CLASSES}>
                            <input
                              type="checkbox"
                              checked={projIndices.includes(idx)}
                              onChange={() => toggleProjeto(idx)}
                              disabled={disabled || !ligada}
                              className={CHECKBOX_CLASSES}
                            />
                            {tLang(projeto.name, idioma)}
                          </label>
                        ))}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
