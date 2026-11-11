import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchTrackerResumo,
  registrarEvento,
  responderCandidatura,
  type CandidaturaRespostaResponse,
  type ResumeLanguage,
} from '../api/client'
import { CopiarButton } from '../components/CopiarButton'
import { ErrorPanel } from '../components/ErrorPanel'
import { StatusLine } from '../components/StatusLine'
import {
  CANDIDATURA_CTA,
  CANDIDATURA_CTA_INFLIGHT,
  CANDIDATURA_EPHEMERAL_NOTICE,
  CANDIDATURA_HINT,
  CANDIDATURA_PAGE_TITLE,
  CANDIDATURA_PERGUNTA_LABEL,
  CANDIDATURA_PERGUNTA_PLACEHOLDER,
  CANDIDATURA_RESULT_TITLE,
  CANDIDATURA_VAGA_LABEL,
  CANDIDATURA_VAGA_PLACEHOLDER,
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CURRICULO_IDIOMA_LABEL,
  CURRICULO_IDIOMA_OPTIONS,
  HINT_INPUT_CLASSES,
  PRIMARY_BUTTON_CLASSES,
  RASTREADOR_ARQUIVADA_SUFIXO,
  RASTREADOR_ASSOCIACAO_CTA,
  RASTREADOR_ASSOCIACAO_ERRO,
  RASTREADOR_ASSOCIACAO_INFLIGHT,
  RASTREADOR_ASSOCIACAO_LABEL,
  RASTREADOR_ASSOCIACAO_OK,
  RASTREADOR_ASSOCIACAO_PLACEHOLDER,
  RASTREADOR_ASSOCIACAO_SEM_CANDIDATURAS,
  RASTREADOR_FETCH_ERRO,
  RASTREADOR_LOADING,
  RASTREADOR_RESPOSTA_OBSERVACAO,
  TEXTAREA_CLASSES,
} from '../constants/ui'

const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
const IDIOMA_SELECTED_CLASSES =
  'cursor-pointer rounded px-3 py-1 text-sm font-medium text-blue-700 bg-white shadow-sm'
const IDIOMA_UNSELECTED_CLASSES = 'cursor-pointer rounded px-3 py-1 text-sm text-gray-600'

// Mirrors the backend request bound (routes/candidatura.py Field(max_length)).
const PERGUNTA_MAX_CHARS = 2000
const VAGA_MAX_CHARS = 20000

type RespostaOk = Extract<CandidaturaRespostaResponse, { status: 'ok' }>

/** Today as a zero-padded LOCAL-parts string (UI-SPEC / Pitfall 7 posture):
 * the association's data_evento is assembled from getFullYear/getMonth/
 * getDate — NEVER toISOString(), which would UTC-shift the date for
 * non-UTC machines. */
function hojeLocalIso(): string {
  const agora = new Date()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  return `${agora.getFullYear()}-${mes}-${dia}`
}

/**
 * The Candidatura screen (vaga → perfil follow-on): paste ONE open
 * application-form question (+ optional job description) → one grounded
 * LLM answer from the profile facts. Same 200-envelope discipline as the
 * Currículo/LinkedIn screens: backend PT-BR error lines render verbatim,
 * a fetch-level failure renders the generic hint path, and a prior good
 * answer stays mounted while the next one is in flight. The answer is
 * session state only (D-06/D-16 ephemeral) — a refresh returns to the empty
 * form; the copy affordance is what carries the text away.
 */
export default function CandidaturaHome() {
  const queryClient = useQueryClient()
  const [pergunta, setPergunta] = useState('')
  const [vagaTexto, setVagaTexto] = useState('')
  const [idioma, setIdioma] = useState<ResumeLanguage>('pt-BR')
  const [resultado, setResultado] = useState<RespostaOk | null>(null)
  const [erros, setErros] = useState<string[] | null>(null)

  // D-13 door 3 (plan 07-04): the association picker SHARES the ['tracker']
  // cache with the Rastreador view — same query key, so a candidatura created
  // there appears here without a remount, and an association registered here
  // invalidates what the board/contadores see.
  const resumo = useQuery({ queryKey: ['tracker'], queryFn: fetchTrackerResumo })

  // Association state — session-only like the answer itself. idiomaResposta
  // pins THE ANSWER'S generation language (captured from the submitted
  // payload, not the live selector, which the user may change afterwards).
  const [candidaturaSelecionada, setCandidaturaSelecionada] = useState('')
  const [idiomaResposta, setIdiomaResposta] = useState<ResumeLanguage>('pt-BR')
  const [associacaoOk, setAssociacaoOk] = useState(false)
  const [associacaoErros, setAssociacaoErros] = useState<string[] | null>(null)

  const responder = useMutation({
    mutationFn: responderCandidatura,
    onSuccess: (data, variaveis) => {
      if (data.status === 'ok') {
        setResultado(data)
        setErros(null)
        // A NEW answer is a fresh association opportunity: reset the control
        // and pin this answer's generation language from the submitted payload.
        setIdiomaResposta(variaveis.language)
        setCandidaturaSelecionada('')
        setAssociacaoOk(false)
        setAssociacaoErros(null)
      } else {
        // Backend PT-BR lines verbatim; the prior answer stays mounted.
        setErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down) — generic PT-BR hint path.
      setErros([
        'Não foi possível gerar a resposta — o detalhe técnico completo aparece no terminal onde o servidor está rodando.',
      ])
    },
  })

  // D-08/A9 metadata-only association: the ONLY fields sent are tipo,
  // data_evento (today, local parts), idioma (the answer's generation
  // language) and observacao bound to the FIXED constant — the question and
  // the answer text never leave this page's ephemeral state (no schema
  // column exists to receive them).
  const associar = useMutation({
    mutationFn: ({ candidaturaId, idiomaEvento }: { candidaturaId: number; idiomaEvento: ResumeLanguage }) =>
      registrarEvento(candidaturaId, {
        tipo: 'resposta',
        data_evento: hojeLocalIso(),
        idioma: idiomaEvento,
        observacao: RASTREADOR_RESPOSTA_OBSERVACAO,
      }),
    onSuccess: (resultadoAssociacao) => {
      if (resultadoAssociacao.status === 'ok') {
        setAssociacaoOk(true)
        setAssociacaoErros(null)
        // The 'resposta' event feeds the contadores and the follow-up
        // suggestion anchor server-side — the shared ['tracker'] cache must
        // refresh or kanban/contadores desynchronize (Pitfall 6).
        queryClient.invalidateQueries({ queryKey: ['tracker'] })
      } else {
        // Backend PT-BR lines verbatim; the answer + picker stay mounted.
        setAssociacaoOk(false)
        setAssociacaoErros(resultadoAssociacao.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down) — generic PT-BR hint path.
      setAssociacaoOk(false)
      setAssociacaoErros([RASTREADOR_ASSOCIACAO_ERRO])
    },
  })

  const perguntaTrimmed = pergunta.trim()
  const podeEnviar = perguntaTrimmed.length >= 5

  return (
    <div className="space-y-6">
      <StatusLine ok={true} />
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-gray-900">{CANDIDATURA_PAGE_TITLE}</h2>
        <p className="text-sm text-gray-600">{CANDIDATURA_HINT}</p>
      </div>

      <form
        className={CARD_CLASSES}
        onSubmit={(event) => {
          event.preventDefault()
          if (!podeEnviar || responder.isPending) return
          setErros(null)
          responder.mutate({
            pergunta: perguntaTrimmed,
            vaga_texto: vagaTexto.trim() ? vagaTexto.trim() : null,
            language: idioma,
          })
        }}
      >
        <div className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="pergunta-textarea" className="block text-sm font-semibold text-gray-900">
              {CANDIDATURA_PERGUNTA_LABEL}
            </label>
            <textarea
              id="pergunta-textarea"
              value={pergunta}
              onChange={(event) => setPergunta(event.target.value)}
              placeholder={CANDIDATURA_PERGUNTA_PLACEHOLDER}
              maxLength={PERGUNTA_MAX_CHARS}
              className={TEXTAREA_CLASSES}
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="vaga-textarea" className="block text-sm font-semibold text-gray-900">
              {CANDIDATURA_VAGA_LABEL}
            </label>
            <textarea
              id="vaga-textarea"
              value={vagaTexto}
              onChange={(event) => setVagaTexto(event.target.value)}
              placeholder={CANDIDATURA_VAGA_PLACEHOLDER}
              maxLength={VAGA_MAX_CHARS}
              className={TEXTAREA_CLASSES}
            />
          </div>

          <fieldset>
            <legend className="text-sm font-semibold text-gray-900">{CURRICULO_IDIOMA_LABEL}</legend>
            <div className="mt-2 inline-flex rounded-md border border-gray-300 bg-gray-50 p-1">
              {(Object.keys(CURRICULO_IDIOMA_OPTIONS) as ResumeLanguage[]).map((lang) => (
                <label
                  key={lang}
                  className={idioma === lang ? IDIOMA_SELECTED_CLASSES : IDIOMA_UNSELECTED_CLASSES}
                >
                  <input
                    type="radio"
                    name="idioma-candidatura"
                    value={lang}
                    checked={idioma === lang}
                    onChange={() => setIdioma(lang)}
                    className="sr-only"
                  />
                  {CURRICULO_IDIOMA_OPTIONS[lang]}
                </label>
              ))}
            </div>
          </fieldset>

          <button type="submit" disabled={!podeEnviar || responder.isPending} className={PRIMARY_BUTTON_CLASSES}>
            {responder.isPending ? CANDIDATURA_CTA_INFLIGHT : CANDIDATURA_CTA}
          </button>
        </div>
      </form>

      {erros && erros.length > 0 && <ErrorPanel erros={erros} />}

      {resultado && (
        <section aria-labelledby="candidatura-resposta-title" className={CARD_CLASSES}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 id="candidatura-resposta-title" className="text-base font-semibold text-gray-900">
              {CANDIDATURA_RESULT_TITLE}
            </h3>
            <CopiarButton text={resultado.resposta} />
          </div>
          <p className="mt-3 whitespace-pre-wrap text-sm text-gray-700">{resultado.resposta}</p>
          <p className="mt-3 text-xs text-gray-500">{CANDIDATURA_EPHEMERAL_NOTICE}</p>

          {/* D-13 door 3 (plan 07-04): associate the answer with a candidatura
              — a metadata-only 'resposta' event (D-08/A9). Zero candidaturas
              renders the loud-empty line instead of an empty select; erro
              envelopes render verbatim through ErrorPanel, fetch-level
              failures take the generic PT-BR hint. */}
          <div className="mt-4 space-y-2 border-t border-gray-200 pt-4">
            <label
              htmlFor="associar-candidatura"
              className="block text-sm font-medium text-gray-800"
            >
              {RASTREADOR_ASSOCIACAO_LABEL}
            </label>
            {resumo.isPending ? (
              <p className="text-sm text-gray-500">{RASTREADOR_LOADING}</p>
            ) : resumo.isError ? (
              <p className="text-sm text-red-600">{RASTREADOR_FETCH_ERRO}</p>
            ) : resumo.data && resumo.data.status === 'erro' ? (
              <ErrorPanel erros={resumo.data.erros} />
            ) : resumo.data &&
              resumo.data.status === 'ok' &&
              resumo.data.candidaturas.length === 0 ? (
              <p className="text-sm text-gray-600">{RASTREADOR_ASSOCIACAO_SEM_CANDIDATURAS}</p>
            ) : (
              resumo.data &&
              resumo.data.status === 'ok' && (
                <div className="space-y-2">
                  <select
                    id="associar-candidatura"
                    value={candidaturaSelecionada}
                    onChange={(event) => setCandidaturaSelecionada(event.target.value)}
                    className={`mt-1 ${HINT_INPUT_CLASSES}`}
                  >
                    <option value="">{RASTREADOR_ASSOCIACAO_PLACEHOLDER}</option>
                    {resumo.data.candidaturas.map((candidatura) => (
                      <option key={candidatura.id} value={candidatura.id}>
                        {candidatura.empresa} — {candidatura.cargo}
                        {candidatura.arquivada ? RASTREADOR_ARQUIVADA_SUFIXO : ''}
                      </option>
                    ))}
                  </select>
                  <div>
                    <button
                      type="button"
                      onClick={() =>
                        associar.mutate({
                          candidaturaId: Number(candidaturaSelecionada),
                          idiomaEvento: idiomaResposta,
                        })
                      }
                      disabled={!candidaturaSelecionada || associar.isPending}
                      className={COMPACT_SECONDARY_BUTTON_CLASSES}
                    >
                      {associar.isPending ? RASTREADOR_ASSOCIACAO_INFLIGHT : RASTREADOR_ASSOCIACAO_CTA}
                    </button>
                  </div>
                  {associacaoOk && (
                    <p className="text-sm text-gray-700" role="status">
                      {RASTREADOR_ASSOCIACAO_OK}
                    </p>
                  )}
                  {associacaoErros && associacaoErros.length > 0 && (
                    <ErrorPanel erros={associacaoErros} />
                  )}
                </div>
              )
            )}
          </div>
        </section>
      )}
    </div>
  )
}
