import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { responderCandidatura, type CandidaturaRespostaResponse, type ResumeLanguage } from '../api/client'
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
  CURRICULO_IDIOMA_LABEL,
  CURRICULO_IDIOMA_OPTIONS,
  PRIMARY_BUTTON_CLASSES,
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
  const [pergunta, setPergunta] = useState('')
  const [vagaTexto, setVagaTexto] = useState('')
  const [idioma, setIdioma] = useState<ResumeLanguage>('pt-BR')
  const [resultado, setResultado] = useState<RespostaOk | null>(null)
  const [erros, setErros] = useState<string[] | null>(null)

  const responder = useMutation({
    mutationFn: responderCandidatura,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        setResultado(data)
        setErros(null)
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
        </section>
      )}
    </div>
  )
}
