import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  fetchProfile,
  gerarLinkedin,
  type LinkedinGerarResponse,
  type ResumeLanguage,
} from '../api/client'
import { CharacterCounter } from '../components/CharacterCounter'
import { ErrorPanel } from '../components/ErrorPanel'
import { PlaceholderBanner } from '../components/PlaceholderBanner'
import { StatusLine } from '../components/StatusLine'
import {
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CURRICULO_ERROR_HINT,
  CURRICULO_ERROR_RETRY,
  CURRICULO_EPHEMERAL_NOTICE,
  CURRICULO_IDIOMA_OPTIONS,
  LINKEDIN_BLOCK_LABELS,
  LINKEDIN_CTA,
  LINKEDIN_CTA_INFLIGHT,
  LINKEDIN_COPIAR,
  LINKEDIN_COPIADO,
  LINKEDIN_COPIAR_FALHA,
  LINKEDIN_EMPTY_BODY,
  LINKEDIN_EMPTY_TITLE,
  LINKEDIN_ERROR_TITLE,
  LINKEDIN_IDIOMA_LABEL,
  LINKEDIN_INFLIGHT_HINT,
  LINKEDIN_OBJETIVO_LABEL,
  LINKEDIN_OBJETIVO_MAX_CHARS,
  LINKEDIN_OBJETIVO_MIN_CHARS,
  LINKEDIN_OBJETIVO_PLACEHOLDER,
  LINKEDIN_OBJETIVO_TOO_LONG_HINT,
  LINKEDIN_OBJETIVO_TOO_SHORT_HINT,
  LINKEDIN_OVERLIMIT_FLAG,
  LINKEDIN_PAGE_TITLE,
  LINKEDIN_RESULT_TITLE,
  PERFIL_ERROR_TITLE,
  PERFIL_LOADING,
  POLICY_EDICAO,
  PRIMARY_BUTTON_CLASSES,
  TEXTAREA_CLASSES,
} from '../constants/ui'

type LinkedinGerarOk = Extract<LinkedinGerarResponse, { status: 'ok' }>

// Tracer scope (plan 06-01): the LinkedIn page skeleton with the HEADLINE
// block as the proven slice. Waves 2+ extend the result card additively
// (Sobre/Experiência/Habilidades blocks, then the QA panel) — the form, the
// profile gate, the mutation contract and the wholesale-swap mechanism below
// are final from day one.

// Tracer locking booleans: no regen/export/editor surfaces exist yet, so the
// "no long op pending" and "no editor open" CTA conditions reduce to the
// gerar flight itself (the wave-2 expansion re-derives them from the full
// locking matrix without changing the CTA gate shape).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
const SECONDARY_BUTTON_CLASSES =
  'min-h-10 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
const IDIOMA_SELECTED_CLASSES =
  'cursor-pointer rounded bg-white px-3 py-1 text-sm font-semibold text-blue-600 shadow-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
const IDIOMA_UNSELECTED_CLASSES =
  'cursor-pointer rounded px-3 py-1 text-sm text-gray-600 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
// UI-SPEC Component conventions: generated-section headings reuse the card's
// bordered-uppercase pattern; block h4 stays the grandfathered pattern.
const BLOCK_HEADING_CLASSES = 'text-sm font-bold uppercase tracking-wide text-gray-500'

/**
 * The LinkedIn screen (plan 06-01 tracer): declare a career objective →
 * choose the run language → generate → the headline block with a live
 * character counter and a Copiar button (D-01/D-02/D-08). All result state is
 * session React state (D-11 ephemeral) — a refresh returns to the empty form.
 * A gerar success swaps the result in WHOLESALE (probe edge LI-01/adjacency:
 * identical objectives across runs never merge); an erro envelope renders the
 * backend PT-BR lines verbatim; a fetch-level failure renders the generic
 * hint path. A failed gerar keeps any prior result mounted (failure never
 * blanks). All content renders as JSX text children — no raw-HTML path
 * (T-06-05). Over-limit output is flagged in place, NEVER truncated (D-07);
 * Copiar stays enabled (the flag warns, the user decides).
 */
export default function LinkedInHome() {
  // Profile gate — the SAME ['perfil'] query the other pages use; a broken
  // profile blocks generation here too.
  const perfilQuery = useQuery({ queryKey: ['perfil'], queryFn: fetchProfile })

  // Zone 1 inputs: raw objetivo + run language.
  const [objetivo, setObjetivo] = useState('')
  const [idioma, setIdioma] = useState<ResumeLanguage>('pt-BR')
  // Last successful generate response — session state only (D-11).
  const [resultado, setResultado] = useState<LinkedinGerarOk | null>(null)
  // Generation failure (erro envelope lines, or [] for a thrown fetch failure).
  const [gerarErros, setGerarErros] = useState<string[] | null>(null)
  // D-08 copy feedback (tracer: the headline block only): Copiado! label swap
  // for ~2 s via setTimeout cleared on unmount; the failure line persists
  // until the next successful copy.
  const [copiado, setCopiado] = useState(false)
  const [copiarFalhou, setCopiarFalhou] = useState(false)
  const copiadoTimerRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (copiadoTimerRef.current !== null) clearTimeout(copiadoTimerRef.current)
    }
  }, [])

  const trimmed = objetivo.trim()
  // The CTA gate (D-02): trimmed objetivo >= min enables the CTA (the same
  // floor the backend's Field(min_length=80) enforces — client mirror, WR-01).
  const ctaHabilitado = trimmed.length >= LINKEDIN_OBJETIVO_MIN_CHARS

  const gerar = useMutation({
    mutationFn: gerarLinkedin,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        // D-11 wholesale swap: the response replaces the displayed state in
        // ONE assignment — never a client-side merge (runs are independent;
        // identical objectives across runs never merge).
        setResultado(data)
        setGerarErros(null)
        // A replaced result resets the copy affordances with it.
        setCopiado(false)
        setCopiarFalhou(false)
      } else {
        // 200-envelope erro: backend PT-BR lines, rendered verbatim below.
        setGerarErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down): generic hint path (erros=[]).
      // Raw detail is in the uvicorn terminal only; prior result stays mounted.
      setGerarErros([])
    },
  })

  function gerarAgora() {
    gerar.mutate({ objetivo: trimmed, language: idioma })
  }

  // D-08: the text EXACTLY as displayed is what goes to the clipboard.
  function copiarHeadline() {
    if (!resultado) return
    const texto = resultado.secoes.headline
    navigator.clipboard
      .writeText(texto)
      .then(() => {
        setCopiarFalhou(false)
        setCopiado(true)
        if (copiadoTimerRef.current !== null) clearTimeout(copiadoTimerRef.current)
        copiadoTimerRef.current = window.setTimeout(() => setCopiado(false), 2000)
      })
      .catch(() => {
        setCopiado(false)
        setCopiarFalhou(true) // persists until the next successful copy
      })
  }

  if (perfilQuery.isPending) {
    return <p className="text-gray-500">{PERFIL_LOADING}</p>
  }

  if (perfilQuery.isError || !perfilQuery.data) {
    return <p className="text-red-600">{PERFIL_ERROR_TITLE}</p>
  }

  if (perfilQuery.data.status === 'erro') {
    // Broken profile = rendered UI state (verbatim house pattern); generation
    // is unavailable until the profile loads.
    return (
      <div className="space-y-4">
        <StatusLine ok={false} />
        <ErrorPanel erros={perfilQuery.data.erros} />
      </div>
    )
  }

  const limitesHeadline = resultado?.limites.headline ?? null
  const excesso = limitesHeadline?.excesso ?? 0

  return (
    <div className="space-y-6">
      <StatusLine ok={true} />
      {perfilQuery.data.exemplo && <PlaceholderBanner />}
      <h2 className="text-xl font-semibold text-gray-900">{LINKEDIN_PAGE_TITLE}</h2>

      {!resultado && !gerar.isPending && (
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-gray-900">{LINKEDIN_EMPTY_TITLE}</h3>
          <p className="text-sm text-gray-600">{LINKEDIN_EMPTY_BODY}</p>
        </div>
      )}

      {/* Zone 1 — form card */}
      <form
        className={CARD_CLASSES}
        onSubmit={(event) => {
          event.preventDefault()
          gerarAgora()
        }}
      >
        <div className="space-y-4">
          <div className="space-y-1">
            <label
              htmlFor="linkedin-objetivo"
              className="block text-sm font-semibold text-gray-900"
            >
              {LINKEDIN_OBJETIVO_LABEL}
            </label>
            <textarea
              id="linkedin-objetivo"
              value={objetivo}
              onChange={(event) => setObjetivo(event.target.value)}
              placeholder={LINKEDIN_OBJETIVO_PLACEHOLDER}
              maxLength={LINKEDIN_OBJETIVO_MAX_CHARS}
              className={TEXTAREA_CLASSES}
            />
            {trimmed.length < LINKEDIN_OBJETIVO_MIN_CHARS && (
              <p className="text-xs text-gray-500">
                {LINKEDIN_OBJETIVO_TOO_SHORT_HINT.replace(
                  '{min}',
                  String(LINKEDIN_OBJETIVO_MIN_CHARS),
                )}
              </p>
            )}
            {objetivo.length >= LINKEDIN_OBJETIVO_MAX_CHARS && (
              <p className="text-xs text-gray-500">
                {LINKEDIN_OBJETIVO_TOO_LONG_HINT.replace(
                  '{max}',
                  String(LINKEDIN_OBJETIVO_MAX_CHARS),
                )}
              </p>
            )}
          </div>

          {/* Idioma segmented control — reused verbatim (same classes, same options). */}
          <fieldset>
            <legend className="text-sm font-semibold text-gray-900">{LINKEDIN_IDIOMA_LABEL}</legend>
            <div className="mt-2 inline-flex rounded-md border border-gray-300 bg-gray-50 p-1">
              {(Object.keys(CURRICULO_IDIOMA_OPTIONS) as ResumeLanguage[]).map((lang) => (
                <label
                  key={lang}
                  className={idioma === lang ? IDIOMA_SELECTED_CLASSES : IDIOMA_UNSELECTED_CLASSES}
                >
                  <input
                    type="radio"
                    name="idioma-linkedin"
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

          <button
            type="submit"
            disabled={!ctaHabilitado || gerar.isPending}
            className={PRIMARY_BUTTON_CLASSES}
          >
            {gerar.isPending ? LINKEDIN_CTA_INFLIGHT : LINKEDIN_CTA}
          </button>
        </div>
      </form>

      {/* Zone 3 — one aria-live region: in-flight hints, error panels, result. */}
      <div aria-live="polite" className="space-y-6">
        {gerar.isPending && <p className="text-sm text-gray-600">{LINKEDIN_INFLIGHT_HINT}</p>}

        {gerarErros !== null && !gerar.isPending && (
          <section
            aria-labelledby="linkedin-gerar-error-title"
            className="rounded-md border border-red-300 bg-red-50 px-4 py-3"
          >
            <h3 id="linkedin-gerar-error-title" className="font-semibold text-red-700">
              {LINKEDIN_ERROR_TITLE}
            </h3>
            {gerarErros.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-sm text-red-700">
                {gerarErros.map((linha, i) => (
                  <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
                    {linha}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-xs text-red-600">{CURRICULO_ERROR_HINT}</p>
            <button
              type="button"
              onClick={gerarAgora}
              disabled={gerar.isPending}
              className={`mt-3 ${SECONDARY_BUTTON_CLASSES}`}
            >
              {CURRICULO_ERROR_RETRY}
            </button>
          </section>
        )}

        {resultado && limitesHeadline && (
          <>
            {/* Ephemeral notice ABOVE the card (UI-SPEC Zone 3; Currículo copy verbatim). */}
            <p className="text-xs text-gray-500">{CURRICULO_EPHEMERAL_NOTICE}</p>
            <section className={CARD_CLASSES} aria-label={LINKEDIN_RESULT_TITLE}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-base font-semibold text-gray-900">{LINKEDIN_RESULT_TITLE}</h3>
                <p className="text-xs text-gray-500">{POLICY_EDICAO}</p>
              </div>

              {/* Headline block (tracer slice): Copiar FIRST in the action row (D-08). */}
              <div className="mt-4 border-t border-gray-200 pt-3">
                <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS.headline}</h4>
                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
                  <button
                    type="button"
                    onClick={copiarHeadline}
                    aria-live="polite"
                    className={COMPACT_SECONDARY_BUTTON_CLASSES}
                  >
                    {copiado ? LINKEDIN_COPIADO : LINKEDIN_COPIAR}
                  </button>
                </div>
                <p className="mt-2 whitespace-pre-wrap text-sm text-gray-900">
                  {resultado.secoes.headline}
                </p>
                <CharacterCounter count={limitesHeadline.tamanho} limite={limitesHeadline.limite} />
                {excesso > 0 && (
                  <p className="mt-1 text-xs text-red-600">
                    {LINKEDIN_OVERLIMIT_FLAG.replace('{excesso}', String(excesso))}
                  </p>
                )}
                {copiarFalhou && <p className="mt-2 text-xs text-red-600">{LINKEDIN_COPIAR_FALHA}</p>}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  )
}
