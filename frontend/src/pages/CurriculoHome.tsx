import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  downloadPdf,
  exportarCurriculo,
  fetchProfile,
  fetchResumeLint,
  gerarCurriculo,
  type GerarResponse,
  type ResumeLanguage,
  type SelfCheckDTO,
} from '../api/client'
import { ErrorPanel } from '../components/ErrorPanel'
import { ExportZone } from '../components/ExportZone'
import { KeywordsPanel } from '../components/KeywordsPanel'
import { LintPanel, type LintOk } from '../components/LintPanel'
import { PlaceholderBanner } from '../components/PlaceholderBanner'
import { ResumeResult } from '../components/ResumeResult'
import { SelfCheckPanel } from '../components/SelfCheckPanel'
import { StatusLine } from '../components/StatusLine'
import {
  CURRICULO_CTA,
  CURRICULO_CTA_INFLIGHT,
  CURRICULO_EMPTY_BODY,
  CURRICULO_EMPTY_TITLE,
  CURRICULO_ERROR_HINT,
  CURRICULO_ERROR_RETRY,
  CURRICULO_ERROR_TITLE,
  CURRICULO_IDIOMA_LABEL,
  CURRICULO_IDIOMA_OPTIONS,
  CURRICULO_INFLIGHT_HINT,
  CURRICULO_LINT_FETCH_ERRO,
  CURRICULO_JD_LABEL,
  CURRICULO_JD_PLACEHOLDER,
  CURRICULO_JD_TOO_SHORT_HINT,
  CURRICULO_PAGE_TITLE,
  EXPORTAR_INFLIGHT_HINT,
  PERFIL_ERROR_TITLE,
  PERFIL_LOADING,
  PRIMARY_BUTTON_CLASSES,
} from '../constants/ui'

type GerarOk = Extract<GerarResponse, { status: 'ok' }>

const JD_MIN_CHARS = 80 // boundary: exactly 80 trimmed chars enable CTA + lint query
const DEBOUNCE_MS = 800 // one lint call per settled typing state (T-03-10 bound)

// Pinned class strings from the UI-SPEC Component conventions (plan 03-04).
// PRIMARY_BUTTON_CLASSES now lives in constants/ui.ts — single definition
// shared with ExportZone (IN-04).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
const SECONDARY_BUTTON_CLASSES =
  'min-h-10 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
const TEXTAREA_CLASSES =
  'min-h-40 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm leading-6 text-gray-900 placeholder:text-gray-400 focus-visible:border-blue-600 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600'
const IDIOMA_SELECTED_CLASSES =
  'cursor-pointer rounded bg-white px-3 py-1 text-sm font-semibold text-blue-600 shadow-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
const IDIOMA_UNSELECTED_CLASSES =
  'cursor-pointer rounded px-3 py-1 text-sm text-gray-600 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'

/**
 * The Currículo screen (plans 03-04 + 04-03): paste JD → choose language →
 * JD-tied lint (≥80 debounced chars) → generate → assembled result + honest
 * coverage → export + ATS self-check. State machine: idle → typing → in-flight
 * → result (zones 4–5; the form stays at top for edits) → exporting (controls
 * locked symmetrically) → result+checked (receipt + panel) or result+export-
 * error (prior checked state preserved). Failure never blanks the page — any
 * prior result stays mounted. Generated content and export state are React
 * state only (D-06/D-16 ephemeral); a refresh returns to idle/unexported. All
 * renders are JSX text children — no raw-HTML path (T-03-08 posture).
 */
export default function CurriculoHome() {
  // Profile gate — the SAME ['perfil'] query PerfilHome uses; React Query dedupes.
  const perfilQuery = useQuery({ queryKey: ['perfil'], queryFn: fetchProfile })

  // Zone 1 inputs: raw JD + run language. The debounced copy drives the lint query.
  const [jdText, setJdText] = useState('')
  const [debouncedJd, setDebouncedJd] = useState('')
  const [idioma, setIdioma] = useState<ResumeLanguage>('pt-BR')
  // Zone 4/5: last successful generate response — session state only (D-06).
  const [resultado, setResultado] = useState<GerarOk | null>(null)
  // Generation failure (erro envelope lines, or [] for a thrown fetch failure).
  const [gerarErros, setGerarErros] = useState<string[] | null>(null)
  // Zone 6 export state — React session state only (D-16 ephemeral, like D-06):
  // a refresh returns to the unexported result state.
  const [receiptFilename, setReceiptFilename] = useState<string | null>(null)
  const [selfcheck, setSelfcheck] = useState<SelfCheckDTO | null>(null)
  // Export failure (backend PT-BR lines, or [] for a thrown fetch failure).
  const [exportarErros, setExportarErros] = useState<string[] | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedJd(jdText), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [jdText])

  const trimmed = jdText.trim()
  const debouncedTrimmed = debouncedJd.trim()
  const lintReady = debouncedTrimmed.length >= JD_MIN_CHARS

  // Zone 2 query: fires only once the DEBOUNCED JD reaches 80 trimmed chars —
  // one real LLM call per settled state, never per keystroke.
  const lintQuery = useQuery({
    queryKey: ['resume-lint', debouncedTrimmed],
    queryFn: () => fetchResumeLint(debouncedTrimmed),
    enabled: lintReady,
  })

  const gerar = useMutation({
    mutationFn: gerarCurriculo,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        // Regeneration reset (UI-SPEC): the prior exported PDF no longer matches
        // the displayed resume — clear the receipt + self-check panel + export
        // errors BEFORE mounting the new result. The export CTA stays available.
        setReceiptFilename(null)
        setSelfcheck(null)
        setExportarErros(null)
        setResultado(data)
        setGerarErros(null)
      } else {
        // 200-envelope erro: backend PT-BR lines, rendered verbatim below.
        setGerarErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down): fail-loud panel + retry, prior
      // result stays mounted. Raw detail is in the uvicorn terminal only.
      setGerarErros([])
    },
  })

  // Zone 6 export (D-07/D-11/D-13): ONE POST drives all three effects — the
  // automatic download starts from this response's bytes, the green receipt
  // names the backend filename, the self-check panel mounts. Erro paths NEVER
  // clear receiptFilename/selfcheck (a failure never blanks prior checked state).
  const exportar = useMutation({
    mutationFn: exportarCurriculo,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        downloadPdf(data.pdf_base64, data.filename)
        setReceiptFilename(data.filename)
        setSelfcheck(data.selfcheck)
        setExportarErros(null)
      } else {
        // Gate failure (D-08): no file was delivered — backend PT-BR lines
        // naming the failed check, rendered verbatim by ExportZone.
        setExportarErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down): same panel, generic hint (the
      // erros=[] Phase 3 convention). Raw detail is terminal-only.
      setExportarErros([])
    },
  })

  function gerarAgora() {
    gerar.mutate({ jd_text: trimmed, language: idioma })
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

  const lintOk: LintOk | null =
    lintQuery.data && lintQuery.data.status === 'ok' ? lintQuery.data : null

  // Narrowed ok payload (guaranteed by the early returns above), captured as a
  // const so the Zone 6 export callback closes over a stable, typed value —
  // TS narrowing does not persist into closures over mutable query objects.
  const perfilOk = perfilQuery.data

  return (
    <div className="space-y-6">
      <StatusLine ok={true} />
      {perfilQuery.data.exemplo && <PlaceholderBanner />}
      <h2 className="text-xl font-semibold text-gray-900">{CURRICULO_PAGE_TITLE}</h2>

      {!resultado && !gerar.isPending && (
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-gray-900">{CURRICULO_EMPTY_TITLE}</h3>
          <p className="text-sm text-gray-600">{CURRICULO_EMPTY_BODY}</p>
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
            <label htmlFor="jd-textarea" className="block text-sm font-semibold text-gray-900">
              {CURRICULO_JD_LABEL}
            </label>
            <textarea
              id="jd-textarea"
              value={jdText}
              onChange={(event) => setJdText(event.target.value)}
              placeholder={CURRICULO_JD_PLACEHOLDER}
              className={TEXTAREA_CLASSES}
            />
            {trimmed.length < JD_MIN_CHARS && (
              <p className="text-xs text-gray-500">{CURRICULO_JD_TOO_SHORT_HINT}</p>
            )}
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
                    name="idioma"
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
            disabled={trimmed.length < JD_MIN_CHARS || gerar.isPending || exportar.isPending}
            className={PRIMARY_BUTTON_CLASSES}
          >
            {gerar.isPending ? CURRICULO_CTA_INFLIGHT : CURRICULO_CTA}
          </button>
        </div>
      </form>

      {/* Zone 2 — lint panel: pending renders nothing (the form stays primary). */}
      {lintReady && lintQuery.data && lintQuery.data.status === 'ok' && <LintPanel resultado={lintOk} />}
      {lintReady && lintQuery.data && lintQuery.data.status === 'erro' && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
          <ul className="list-disc pl-5 text-sm text-red-700">
            {lintQuery.data.erros.map((linha, i) => (
              <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
                {linha}
              </li>
            ))}
          </ul>
        </div>
      )}
      {/* WR-02: fetch-level failure (server down / non-200 → lintQuery.isError)
          renders the SAME fail-loud red-panel convention as gerar/exportar —
          generic PT-BR hint, raw detail terminal-only. Never silent. */}
      {lintReady && lintQuery.isError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{CURRICULO_LINT_FETCH_ERRO}</p>
        </div>
      )}

      {/* Zones 3/4/5/6 — one aria-live region: in-flight hints, error panels,
          result, export control + self-check. */}
      <div aria-live="polite" className="space-y-6">
        {gerar.isPending && <p className="text-sm text-gray-600">{CURRICULO_INFLIGHT_HINT}</p>}
        {exportar.isPending && <p className="text-sm text-gray-600">{EXPORTAR_INFLIGHT_HINT}</p>}

        {gerarErros !== null && !gerar.isPending && (
          <section
            aria-labelledby="gerar-error-title"
            className="rounded-md border border-red-300 bg-red-50 px-4 py-3"
          >
            <h3 id="gerar-error-title" className="font-semibold text-red-700">
              {CURRICULO_ERROR_TITLE}
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

        {resultado && (
          <>
            {/* Zone 4 — assembled card from the shared ['perfil'] data + the
                generate response; Zone 6 (export + self-check) stacks directly
                below the artifact it exports (D-09); Zone 5 closes the page. */}
            <ResumeResult
              perfil={perfilQuery.data.perfil}
              secoes={resultado.secoes}
              idioma={resultado.idioma}
              onRegenerar={gerarAgora}
              regenerando={gerar.isPending || exportar.isPending}
            />
            <ExportZone
              onExportar={() =>
                exportar.mutate({
                  perfil: perfilOk.perfil,
                  secoes: resultado.secoes,
                  keywords: resultado.keywords,
                  idioma: resultado.idioma,
                })
              }
              exporting={exportar.isPending}
              ctaDisabled={gerar.isPending || exportar.isPending}
              receiptFilename={receiptFilename}
              erros={exportarErros}
            />
            {selfcheck && (
              <SelfCheckPanel
                selfcheck={selfcheck}
                keywords={resultado.keywords}
                idioma={resultado.idioma}
              />
            )}
            <KeywordsPanel
              keywords={resultado.keywords}
              cobertura={resultado.cobertura}
              cobertura_resumo={resultado.cobertura_resumo}
              idioma={resultado.idioma}
            />
          </>
        )}
      </div>
    </div>
  )
}
