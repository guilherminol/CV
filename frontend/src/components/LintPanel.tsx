import type {
  LintGapDTO,
  LintResponse,
  PerfilDTO,
} from '../api/client'
import { fold } from '../lib/comparison'
import {
  CURRICULO_LINT_CLEAR,
  CURRICULO_LINT_HINT,
  CURRICULO_LINT_TITLE,
  CURRICULO_KEYWORD_ADD_ARIA,
  CURRICULO_KEYWORD_ADD_LABEL,
  CURRICULO_KEYWORD_ADICIONANDO,
  CURRICULO_KEYWORD_NO_PERFIL,
} from '../constants/ui'
import { nomesNoPerfil } from './KeywordsPanel'

/** The lint ok-envelope (keywords + avisos + gaps) as produced by POST /api/resume/lint. */
export type LintOk = Extract<LintResponse, { status: 'ok' }>

interface LintPanelProps {
  /** Ok envelope from the lint query; null renders nothing. */
  resultado: LintOk | null
  /** The owner's live profile — present names show "no perfil" instead of the
   * add button (vaga → perfil acceptance, same semantics as KeywordsPanel). */
  perfil?: PerfilDTO
  onAdicionar?: (gap: LintGapDTO) => void
  /** Canonical of the keyword currently being added (button spinner state). */
  adicaoPendente?: string | null
}

/**
 * Zone 2 — JD-tied completeness lint (PROFILE-02), non-blocking (D-03).
 * Backend avisos lines render VERBATIM as JSX text children — never parsed,
 * re-mapped, or translated (D-13/D-14). Zero warnings → the green clear-line,
 * never a silent empty panel. Text-only render: no raw-HTML injection path.
 *
 * Vaga → perfil: when the acceptance props are present, the structured gap
 * rows render FIRST, each carrying its backend-owned aviso line verbatim next
 * to a "+ Perfil" button; the remaining (non-gap) avisos keep the plain list.
 * Identity-exclusion only — a line never has its content parsed or rebuilt.
 */
export function LintPanel({ resultado, perfil, onAdicionar, adicaoPendente }: LintPanelProps) {
  if (!resultado) return null

  if (resultado.avisos.length === 0) {
    return (
      <p className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
        {CURRICULO_LINT_CLEAR}
      </p>
    )
  }

  const gaps = resultado.gaps ?? []
  const aceita = Boolean(onAdicionar && perfil) && gaps.length > 0
  const noPerfil = perfil ? nomesNoPerfil(perfil) : new Set<string>()
  const gapAvisos = new Set(gaps.map((gap) => gap.aviso))
  const outrasAvisos = resultado.avisos.filter((linha) => !gapAvisos.has(linha))

  return (
    <section
      aria-labelledby="lint-panel-title"
      className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900"
    >
      <h3 id="lint-panel-title" className="text-sm font-semibold">
        {CURRICULO_LINT_TITLE}
      </h3>
      {aceita && (
        <ul className="mt-2 space-y-1 text-sm">
          {gaps.map((gap) => {
            const presente = noPerfil.has(fold(gap.canonical)) || noPerfil.has(fold(gap.pt ?? '')) || noPerfil.has(fold(gap.en ?? ''))
            return (
              <li key={gap.canonical} className="whitespace-pre-wrap">
                {gap.aviso}
                {presente ? (
                  <span className="ml-2 text-xs text-amber-700">{CURRICULO_KEYWORD_NO_PERFIL}</span>
                ) : (
                  <button
                    type="button"
                    title={CURRICULO_KEYWORD_ADD_ARIA}
                    disabled={adicaoPendente != null}
                    onClick={() => onAdicionar?.(gap)}
                    className="ml-2 rounded-full border border-blue-200 bg-white px-2 py-0.5 text-[11px] font-medium text-blue-700 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {adicaoPendente === gap.canonical
                      ? CURRICULO_KEYWORD_ADICIONANDO
                      : CURRICULO_KEYWORD_ADD_LABEL}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
      )}
      {outrasAvisos.length > 0 && (
        <ul className={`list-disc pl-5 text-sm ${aceita ? 'mt-2' : 'mt-2'}`}>
          {outrasAvisos.map((linha, i) => (
            <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
              {linha}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-xs text-amber-700">{CURRICULO_LINT_HINT}</p>
    </section>
  )
}
