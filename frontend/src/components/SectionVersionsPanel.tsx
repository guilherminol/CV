import type { ExperienciaGeradaDTO, SecaoId, SecoesDTO } from '../api/client'
import {
  BADGE_EDITADO,
  BADGE_EDITADO_CLASSES,
  BADGE_GERADO,
  BADGE_GERADO_CLASSES,
  QUIET_BUTTON_CLASSES,
  RESTAURAR_VERSAO_CTA,
  VERSOES_INTRO,
} from '../constants/ui'

/** Badge origin for generated-section text (D-04): 'editado' after an inline
 *  save or the restore of an edited version; 'gerado' at mount/regen. */
export type OrigemBadge = 'gerado' | 'editado'

/** A section's value in its own shape (Resumo string / Experiência entries /
 *  Habilidades list) — what version stacks store and restore wholesale. */
export type SectionValor = SecoesDTO[SecaoId]

/** One stored prior version: the displayed text + the badge origin it had. */
export interface SectionVersion {
  secao: SecaoId
  origem: OrigemBadge
  valor: SectionValor
}

/** Plain-text projection of a stored value — the version-row snippet. */
function textoSecaoValor(secao: SecaoId, valor: SectionValor): string {
  if (secao === 'resumo') return valor as string
  if (secao === 'habilidades') return (valor as string[]).join(', ')
  return (valor as ExperienciaGeradaDTO[]).flatMap((exp) => exp.bullets).join(' ')
}

interface SectionVersionsPanelProps {
  secao: SecaoId
  /** Newest first (CurriculoHome prepends on every stack push). */
  versoes: SectionVersion[]
  /** An editor is open or a long op is pending (derived lock). */
  restaurarDesabilitado: boolean
  onRestaurar: (indice: number) => void
}

/**
 * Per-section Versões panel (D-08, UI-SPEC "Versões" block): intro line, then
 * the section's prior versions NEWEST-FIRST — each row an origin badge
 * (Gerado/Editado per the version's recorded origem) + a "Restaurar versão"
 * quiet button + a line-clamp-2 plain-text snippet. In-memory session state
 * only — no persistence, no cap (single-user localhost session, D-01/D-08);
 * restoring always stacks the CURRENT displayed version first (CurriculoHome's
 * empilharVersaoAtual), so nothing is ever silently lost. All content renders
 * as JSX text children — no raw-HTML injection path (T-01-08 posture).
 */
export function SectionVersionsPanel({
  secao,
  versoes,
  restaurarDesabilitado,
  onRestaurar,
}: SectionVersionsPanelProps) {
  return (
    <div className="mt-3">
      <p className="text-xs text-gray-500">{VERSOES_INTRO}</p>
      <div className="mt-2 space-y-2">
        {versoes.map((versao, i) => (
          <div key={`${secao}-${i}`} className="rounded-md border border-gray-200 bg-white px-3 py-2">
            <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
              <span
                className={
                  versao.origem === 'gerado' ? BADGE_GERADO_CLASSES : BADGE_EDITADO_CLASSES
                }
              >
                {versao.origem === 'gerado' ? BADGE_GERADO : BADGE_EDITADO}
              </span>
              <button
                type="button"
                onClick={() => onRestaurar(i)}
                disabled={restaurarDesabilitado}
                className={QUIET_BUTTON_CLASSES}
              >
                {RESTAURAR_VERSAO_CTA}
              </button>
            </div>
            <p className="mt-1 line-clamp-2 text-sm text-gray-600">
              {textoSecaoValor(secao, versao.valor)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
