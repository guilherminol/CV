import type { CompletudeDTO } from '../api/client'
import {
  COMPLETENESS_EMPTY,
  COMPLETENESS_LABELS,
  COMPLETENESS_OK,
  COMPLETENESS_TITLE,
  COMPLETENESS_UNIT,
} from '../constants/ui'

type SectionKey = keyof typeof COMPLETENESS_LABELS

function qtd(n: number, singular: string, plural: string): string {
  return `${n} ${n === 1 ? singular : plural}`
}

/** Presence + count line per section, straight from the completude DTO. */
function summarize(completude: CompletudeDTO, key: SectionKey): { present: boolean; detail: string | null } {
  switch (key) {
    case 'resumo':
      return { present: completude.resumo, detail: null }
    case 'experiencias':
      return {
        present: completude.experiencias,
        detail: `${qtd(completude.experiencias_qtde, COMPLETENESS_UNIT.experiencias, COMPLETENESS_UNIT.experienciasPlural)} · ${qtd(completude.experiencias_impactos_qtde, COMPLETENESS_UNIT.impactos, COMPLETENESS_UNIT.impactosPlural)}`,
      }
    case 'educacao':
      return {
        present: completude.educacao,
        detail: qtd(completude.educacao_qtde, COMPLETENESS_UNIT.itens, COMPLETENESS_UNIT.itensPlural),
      }
    case 'habilidades':
      return {
        present: completude.habilidades,
        detail: `${qtd(completude.habilidades_qtde, COMPLETENESS_UNIT.itens, COMPLETENESS_UNIT.itensPlural)}`,
      }
    case 'certificacoes':
      return {
        present: completude.certificacoes,
        detail: qtd(completude.certificacoes_qtde, COMPLETENESS_UNIT.itens, COMPLETENESS_UNIT.itensPlural),
      }
    case 'idiomas':
      return {
        present: completude.idiomas,
        detail: qtd(completude.idiomas_qtde, COMPLETENESS_UNIT.itens, COMPLETENESS_UNIT.itensPlural),
      }
    case 'projetos':
      return {
        present: completude.projetos,
        detail: qtd(completude.projetos_qtde, COMPLETENESS_UNIT.itens, COMPLETENESS_UNIT.itensPlural),
      }
  }
}

/**
 * Section presence/counts at a glance (D-12) — a pure projection of the
 * completude DTO. Empty optional sections are normal, so they get neutral
 * styling, not an error state.
 */
export function CompletenessGrid({ completude }: { completude: CompletudeDTO }) {
  const keys = Object.keys(COMPLETENESS_LABELS) as SectionKey[]
  return (
    <section aria-labelledby="completude-title">
      <h3 id="completude-title" className="text-base font-semibold text-gray-900">
        {COMPLETENESS_TITLE}
      </h3>
      <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {keys.map((key) => {
          const { present, detail } = summarize(completude, key)
          return (
            <div
              key={key}
              className={
                present
                  ? 'rounded-md border border-green-200 bg-green-50 px-3 py-2'
                  : 'rounded-md border border-gray-200 bg-gray-50 px-3 py-2'
              }
            >
              <dt className="text-sm font-medium text-gray-800">{COMPLETENESS_LABELS[key]}</dt>
              <dd className={`mt-0.5 text-xs ${present ? 'text-green-700' : 'text-gray-400'}`}>
                {present ? (detail ?? COMPLETENESS_OK) : COMPLETENESS_EMPTY}
              </dd>
            </div>
          )
        })}
      </dl>
    </section>
  )
}
