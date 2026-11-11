import { useState } from 'react'
import type {
  CandidaturaDTO,
  EventoRegistroPayload,
  ResumeLanguage,
  TrackerTipoEvento,
} from '../../api/client'
import { ErrorPanel } from '../ErrorPanel'
import {
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CURRICULO_IDIOMA_OPTIONS,
  HINT_INPUT_CLASSES,
  RASTREADOR_EVENTO_CTA,
  RASTREADOR_EVENTO_IDIOMA_NENHUM,
  RASTREADOR_EVENTO_LABEL_DATA,
  RASTREADOR_EVENTO_LABEL_IDIOMA,
  RASTREADOR_EVENTO_LABEL_OBSERVACAO,
  RASTREADOR_EVENTO_LABEL_TIPO,
  RASTREADOR_EVENTO_TIPO_LABELS,
  RASTREADOR_EVENTOS_TITLE,
  RASTREADOR_FOLLOWUP_ADIAR,
  RASTREADOR_FOLLOWUP_ADIAR_PARA,
  RASTREADOR_FOLLOWUP_EXECUTAR,
  RASTREADOR_FOLLOWUP_SR_VENCIDO,
  RASTREADOR_LIMITE_EVENTO_OBSERVACAO,
  RASTREADOR_SEM_EVENTOS,
  TEXTAREA_CLASSES,
  formatarFollowupPendente,
  formatarFollowupVencido,
} from '../../constants/ui'

interface EventosPanelProps {
  /** The payload row verbatim — the panel renders ONLY payload state. */
  candidatura: CandidaturaDTO
  /** Erro envelopes from the bubbled mutations, rendered via ErrorPanel. */
  erros: string[] | null
  registroPendente: boolean
  followupPendente: boolean
  /** Incremented by TrackerHome after every successful registro — the local
   * form clears when it changes (render-time derivation, no effect). */
  registroReset: number
  onRegistrarEvento: (payload: EventoRegistroPayload) => void
  onExecutarFollowup: () => void
  onAdiarFollowup: (novaData: string) => void
}

/**
 * The candidatura detail's event surface (D-08 metadata-only events + the
 * D-10/D-11 follow-up lifecycle): the events list, the registro form, and the
 * follow-up controls gated STRICTLY by the payload's server-computed flags —
 * the panel never decides overdue-ness itself (D-11: no magic — display
 * only), and no date math happens here (Pitfall 7: the pendente line's
 * {data} and the vencido line's {X} arrive server-computed).
 */
export function EventosPanel({
  candidatura,
  erros,
  registroPendente,
  followupPendente,
  registroReset,
  onRegistrarEvento,
  onExecutarFollowup,
  onAdiarFollowup,
}: EventosPanelProps) {
  const [tipo, setTipo] = useState<TrackerTipoEvento>('envio_curriculo')
  const [dataEvento, setDataEvento] = useState('')
  const [idioma, setIdioma] = useState<'' | ResumeLanguage>('')
  const [observacao, setObservacao] = useState('')
  const [adiando, setAdiando] = useState(false)
  const [novaData, setNovaData] = useState('')

  // Render-time reset when the panel's alvo follow-up changes (executar/adiar
  // succeeded server-side): the postpone draft closes with it.
  const [ultimoAlvo, setUltimoAlvo] = useState(candidatura.followup_pendente_data)
  if (candidatura.followup_pendente_data !== ultimoAlvo) {
    setUltimoAlvo(candidatura.followup_pendente_data)
    setAdiando(false)
    setNovaData('')
  }
  // Same pattern for the registro form: clear after a successful registro.
  const [ultimoReset, setUltimoReset] = useState(registroReset)
  if (registroReset !== ultimoReset) {
    setUltimoReset(registroReset)
    setDataEvento('')
    setIdioma('')
    setObservacao('')
  }

  return (
    <section aria-labelledby="rastreador-eventos-title">
      <h4 id="rastreador-eventos-title" className="text-sm font-semibold text-gray-900">
        {RASTREADOR_EVENTOS_TITLE}
      </h4>

      {/* Follow-up state — rendered ONLY from the payload (D-10/D-11). */}
      {candidatura.followup_vencido && candidatura.followup_vencido_dias !== null && (
        <p className="mt-2 text-sm font-semibold text-red-700">
          {formatarFollowupVencido(candidatura.followup_vencido_dias)}
          <span className="sr-only">{RASTREADOR_FOLLOWUP_SR_VENCIDO}</span>
        </p>
      )}
      {candidatura.followup_pendente && candidatura.followup_pendente_data && (
        <div className="mt-2">
          <p className="text-sm text-gray-700">
            {formatarFollowupPendente(candidatura.followup_pendente_data)}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={onExecutarFollowup}
              disabled={followupPendente}
              className={COMPACT_SECONDARY_BUTTON_CLASSES}
            >
              {RASTREADOR_FOLLOWUP_EXECUTAR}
            </button>
            <button
              type="button"
              onClick={() => setAdiando((aberto) => !aberto)}
              disabled={followupPendente}
              className={COMPACT_SECONDARY_BUTTON_CLASSES}
            >
              {RASTREADOR_FOLLOWUP_ADIAR}
            </button>
            {adiando && (
              <>
                {/* No min attribute — "hoje" is not sourced client-side (Pitfall
                    7); a past target returns the PT-BR erro envelope, which the
                    panel renders verbatim. */}
                <input
                  type="date"
                  value={novaData}
                  onChange={(event) => setNovaData(event.target.value)}
                  className={HINT_INPUT_CLASSES}
                  aria-label={RASTREADOR_FOLLOWUP_ADIAR_PARA}
                />
                <button
                  type="button"
                  onClick={() => {
                    if (!novaData || followupPendente) return
                    onAdiarFollowup(novaData)
                  }}
                  disabled={!novaData || followupPendente}
                  className={COMPACT_SECONDARY_BUTTON_CLASSES}
                >
                  {RASTREADOR_FOLLOWUP_ADIAR_PARA}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Event list — loud empty line, never a silently blank panel (D-08
          spirit). data_evento renders as the ISO string the payload carries. */}
      {candidatura.eventos.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">{RASTREADOR_SEM_EVENTOS}</p>
      ) : (
        <ul className="mt-2 space-y-1">
          {candidatura.eventos.map((evento) => (
            <li key={evento.id} className="text-sm text-gray-700">
              <span className="font-medium text-gray-900">
                {RASTREADOR_EVENTO_TIPO_LABELS[evento.tipo]}
              </span>{' '}
              — {evento.data_evento}
              {evento.idioma && <span className="text-gray-500"> · {evento.idioma}</span>}
              {evento.observacao && (
                <span className="block text-xs text-gray-500">{evento.observacao}</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Registro form — metadata only (D-08). */}
      <form
        className="mt-3 rounded-md border border-gray-200 bg-gray-50 p-3"
        aria-label={RASTREADOR_EVENTO_CTA}
        onSubmit={(event) => {
          event.preventDefault()
          if (!dataEvento || registroPendente) return
          onRegistrarEvento({
            tipo,
            data_evento: dataEvento,
            ...(idioma ? { idioma } : {}),
            ...(observacao.trim() ? { observacao: observacao.trim() } : {}),
          })
        }}
      >
        <div className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-gray-800">
              {RASTREADOR_EVENTO_LABEL_TIPO}
            </span>
            <select
              value={tipo}
              onChange={(event) => setTipo(event.target.value as TrackerTipoEvento)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
            >
              {(Object.keys(RASTREADOR_EVENTO_TIPO_LABELS) as TrackerTipoEvento[]).map((valor) => (
                <option key={valor} value={valor}>
                  {RASTREADOR_EVENTO_TIPO_LABELS[valor]}
                </option>
              ))}
            </select>
          </label>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-gray-800">
                {RASTREADOR_EVENTO_LABEL_DATA}
              </span>
              <input
                type="date"
                value={dataEvento}
                onChange={(event) => setDataEvento(event.target.value)}
                className={`mt-1 ${HINT_INPUT_CLASSES}`}
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-gray-800">
                {RASTREADOR_EVENTO_LABEL_IDIOMA}
              </span>
              <select
                value={idioma}
                onChange={(event) => setIdioma(event.target.value as '' | ResumeLanguage)}
                className={`mt-1 ${HINT_INPUT_CLASSES}`}
              >
                <option value="">{RASTREADOR_EVENTO_IDIOMA_NENHUM}</option>
                {(Object.keys(CURRICULO_IDIOMA_OPTIONS) as ResumeLanguage[]).map((valor) => (
                  <option key={valor} value={valor}>
                    {CURRICULO_IDIOMA_OPTIONS[valor]}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block">
            <span className="text-sm font-medium text-gray-800">
              {RASTREADOR_EVENTO_LABEL_OBSERVACAO}
            </span>
            <textarea
              value={observacao}
              maxLength={RASTREADOR_LIMITE_EVENTO_OBSERVACAO}
              onChange={(event) => setObservacao(event.target.value)}
              className={`mt-1 ${TEXTAREA_CLASSES} min-h-16`}
            />
          </label>
        </div>
        {erros && (
          <div className="mt-3">
            <ErrorPanel erros={erros} />
          </div>
        )}
        <button
          type="submit"
          disabled={!dataEvento || registroPendente}
          className={`mt-3 ${COMPACT_SECONDARY_BUTTON_CLASSES}`}
        >
          {RASTREADOR_EVENTO_CTA}
        </button>
      </form>
    </section>
  )
}
