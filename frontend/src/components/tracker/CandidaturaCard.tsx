import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { CandidaturaDTO } from '../../api/client'
import {
  RASTREADOR_CARD_CLASSES,
  RASTREADOR_CARD_HANDLE_CLASSES,
  RASTREADOR_FOLLOWUP_BADGE,
  RASTREADOR_FOLLOWUP_BADGE_CLASSES,
  RASTREADOR_MODALIDADE_LABELS,
  RASTREADOR_PRAZO_AMBAR_CLASSES,
  RASTREADOR_PRAZO_NEUTRO_CLASSES,
  RASTREADOR_PRAZO_SR_PROXIMO,
  RASTREADOR_PRAZO_SR_VENCIDO,
  RASTREADOR_PRAZO_VERMELHO_CLASSES,
  formatarPrazoContagem,
} from '../../constants/ui'

interface CandidaturaCardProps {
  candidatura: CandidaturaDTO
  estagioNome: string
  aberta: boolean
  onAbrir: (candidaturaId: number) => void
}

/**
 * Prazo chip — classes chosen PURELY from the payload's server-computed
 * dias_para_prazo (null → no chip at all); amber = 0..3, red = negative,
 * neutral otherwise (the D-09 family). The sr-only suffix keeps status from
 * ever being color-alone (S6). Exported for the overview rows too.
 */
export function PrazoChip({ dias }: { dias: number | null }) {
  if (dias === null) return null
  const classes =
    dias < 0
      ? RASTREADOR_PRAZO_VERMELHO_CLASSES
      : dias <= 3
        ? RASTREADOR_PRAZO_AMBAR_CLASSES
        : RASTREADOR_PRAZO_NEUTRO_CLASSES
  const sufixo =
    dias < 0 ? RASTREADOR_PRAZO_SR_VENCIDO : dias <= 3 ? RASTREADOR_PRAZO_SR_PROXIMO : null
  return (
    <span className={classes}>
      {formatarPrazoContagem(dias)}
      {sufixo && <span className="sr-only">{sufixo}</span>}
    </span>
  )
}

/**
 * The deterministic "considerar follow-up" badge (D-12) — renders iff the
 * payload says sugerir_followup; the badge text is its own accessible name.
 */
export function FollowupBadge({ sugerir }: { sugerir: boolean }) {
  if (!sugerir) return null
  return <span className={RASTREADOR_FOLLOWUP_BADGE_CLASSES}>{RASTREADOR_FOLLOWUP_BADGE}</span>
}

/**
 * One kanban card (D-14): useSortable for the drag mechanics, a dedicated
 * drag-handle region (the card HEADER) carrying listeners+attributes — never
 * the whole card, never a nested button — and a real body button that opens
 * the detail (clicks survive the pointer sensor's distance-8 activation,
 * Pitfall 4). ALL content renders as JSX text children (S10: no raw-HTML
 * path; link_vaga renders only in the detail view).
 */
export function CandidaturaCard({ candidatura, estagioNome, aberta, onAbrir }: CandidaturaCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: candidatura.id,
  })
  const style = { transform: CSS.Transform.toString(transform), transition }

  return (
    <div ref={setNodeRef} style={style} className={RASTREADOR_CARD_CLASSES}>
      {/* Drag handle = header region only (listeners + a11y attributes). */}
      <div {...attributes} {...listeners} className={RASTREADOR_CARD_HANDLE_CLASSES}>
        <p className="text-sm font-semibold text-gray-900">
          {candidatura.empresa} — {candidatura.cargo}
        </p>
      </div>
      {/* Body button — opens the detail region; carries NO drag listeners. */}
      <button
        type="button"
        onClick={() => onAbrir(candidatura.id)}
        aria-pressed={aberta}
        className="mt-2 block w-full text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        <span className="flex flex-wrap items-center gap-1">
          <PrazoChip dias={candidatura.dias_para_prazo} />
          <FollowupBadge sugerir={candidatura.sugerir_followup} />
        </span>
        <span className="mt-1 block text-xs text-gray-500">{estagioNome}</span>
        {candidatura.modalidade && (
          <span className="mt-0.5 block text-xs text-gray-500">
            {RASTREADOR_MODALIDADE_LABELS[candidatura.modalidade]}
          </span>
        )}
      </button>
    </div>
  )
}
