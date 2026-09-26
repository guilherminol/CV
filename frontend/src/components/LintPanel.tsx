import type { LintResponse } from '../api/client'
import { CURRICULO_LINT_CLEAR, CURRICULO_LINT_HINT, CURRICULO_LINT_TITLE } from '../constants/ui'

/** The lint ok-envelope (keywords + avisos) as produced by POST /api/resume/lint. */
export type LintOk = Extract<LintResponse, { status: 'ok' }>

interface LintPanelProps {
  /** Ok envelope from the lint query; null renders nothing. */
  resultado: LintOk | null
}

/**
 * Zone 2 — JD-tied completeness lint (PROFILE-02), non-blocking (D-03).
 * Backend avisos lines render VERBATIM as JSX text children — never parsed,
 * re-mapped, or translated (D-13/D-14). Zero warnings → the green clear-line,
 * never a silent empty panel. Text-only render: no raw-HTML injection path.
 */
export function LintPanel({ resultado }: LintPanelProps) {
  if (!resultado) return null

  if (resultado.avisos.length === 0) {
    return (
      <p className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
        {CURRICULO_LINT_CLEAR}
      </p>
    )
  }

  return (
    <section
      aria-labelledby="lint-panel-title"
      className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900"
    >
      <h3 id="lint-panel-title" className="text-sm font-semibold">
        {CURRICULO_LINT_TITLE}
      </h3>
      <ul className="mt-2 list-disc pl-5 text-sm">
        {resultado.avisos.map((linha, i) => (
          <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
            {linha}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-amber-700">{CURRICULO_LINT_HINT}</p>
    </section>
  )
}
