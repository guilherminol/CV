import { RASTREADOR_CONTADORES_LABELS } from '../../constants/ui'

/** The honest global counters (D-07): derived SERVER-side from persisted
 * events only; this grid is a pure prop passthrough — zero computation. */
export interface ContadoresDTO {
  enviados: number
  entrevistas: number
  ativas: number
}

// Render order — Enviadas / Entrevistas / Ativas (labels from constants; the
// numbers come from the payload verbatim).
const CONTADORES_ORDEM = ['enviados', 'entrevistas', 'ativas'] as const

/**
 * The three honest numbers at a glance (CompletenessGrid pattern — same
 * tile shape, same dl-grid posture; the pinned 18px semibold numeral is the
 * UI-SPEC typography exception carried from the shipped 07-01 contadores).
 */
export function ContadoresGrid({ contadores }: { contadores: ContadoresDTO }) {
  return (
    <dl className="grid grid-cols-3 gap-2">
      {CONTADORES_ORDEM.map((chave) => (
        <div key={chave} className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
          <dt className="text-sm font-medium text-gray-800">
            {RASTREADOR_CONTADORES_LABELS[chave]}
          </dt>
          <dd className="mt-0.5 text-lg font-semibold text-gray-900">{contadores[chave]}</dd>
        </div>
      ))}
    </dl>
  )
}
