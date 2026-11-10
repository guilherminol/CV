import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  criarCandidatura,
  fetchTrackerResumo,
  type ResumeLanguage,
} from '../api/client'
import { ErrorPanel } from '../components/ErrorPanel'
import {
  HINT_INPUT_CLASSES,
  PRIMARY_BUTTON_CLASSES,
  RASTREADOR_CANDIDATURAS_TITLE,
  RASTREADOR_CTA,
  RASTREADOR_CTA_INFLIGHT,
  RASTREADOR_CONTADORES_LABELS,
  RASTREADOR_FETCH_ERRO,
  RASTREADOR_FORM_TITLE,
  RASTREADOR_LABEL_CARGO,
  RASTREADOR_LABEL_EMPRESA,
  RASTREADOR_LOADING,
  RASTREADOR_PAGE_TITLE,
  RASTREADOR_PLACEHOLDER_CARGO,
  RASTREADOR_PLACEHOLDER_EMPRESA,
  RASTREADOR_SEM_CANDIDATURAS,
  RASTREADOR_SEM_ESTAGIO,
} from '../constants/ui'

// Client mirrors of the backend request bounds (tracker/models.py
// Field(max_length) — 422 is "a client bug, not a UI state"): the inputs cap
// at the same bound so an oversized entry is prevented, never retried into a
// dead-end 422 (WR-01 pattern).
const EMPRESA_MAX_CHARS = 200
const CARGO_MAX_CHARS = 200

// Contadores render order — Enviadas / Entrevistas / Ativas (labels from
// constants; the numbers come from the payload, derived server-side, D-07).
const CONTADORES_ORDEM = ['enviados', 'entrevistas', 'ativas'] as const

// D-13 seam (declared in 07-01; the "Registrar candidatura" button lands in
// 07-04): the Currículo result view hands the JD text + generation language
// over via App state.
export interface TrackerPrefill {
  jd_texto: string
  language: ResumeLanguage
}

interface TrackerHomeProps {
  /** Pending JD prefill — null when the user came in through the nav. */
  prefill: TrackerPrefill | null
  /** App-level clear: the prefill is consumed once, by one candidatura. */
  onPrefillConsumida: () => void
}

/**
 * Rastreador skeleton view (plan 07-01) — the fifth nav view and the app's
 * FIRST persistent state: query ['tracker'] with the house isPending/erro/ok
 * branches, contadores row, candidaturas list, and the minimal creation
 * form. Plan 07-03 replaces the form with the full CandidaturaForm without
 * architectural change (same mutation, same query key).
 */
export default function TrackerHome({ prefill, onPrefillConsumida }: TrackerHomeProps) {
  const queryClient = useQueryClient()
  // React Query v5: single options object; initial-load state is isPending (Pitfall 9).
  const { data, isPending, isError } = useQuery({
    queryKey: ['tracker'],
    queryFn: fetchTrackerResumo,
  })

  const [empresa, setEmpresa] = useState('')
  const [cargo, setCargo] = useState('')
  const [erros, setErros] = useState<string[] | null>(null)

  const podeEnviar = empresa.trim().length > 0 && cargo.trim().length > 0

  const criar = useMutation({
    mutationFn: criarCandidatura,
    onSuccess: (resultado) => {
      if (resultado.status === 'ok') {
        setErros(null)
        setEmpresa('')
        setCargo('')
        // First persistent view in the app — ephemeral-state pages never
        // needed this (Pitfall 6): the shared ['tracker'] cache must refresh
        // or the new row would only appear after a manual reload.
        if (prefill) {
          onPrefillConsumida() // D-13: the JD went into the created candidatura
        }
        queryClient.invalidateQueries({ queryKey: ['tracker'] })
      } else {
        // Backend PT-BR lines verbatim; the form stays mounted.
        setErros(resultado.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down) — generic PT-BR hint path.
      setErros([RASTREADOR_FETCH_ERRO])
    },
  })

  if (isPending) {
    return <p className="text-gray-500">{RASTREADOR_LOADING}</p>
  }

  if (isError || !data) {
    return <p className="text-red-600">{RASTREADOR_FETCH_ERRO}</p>
  }

  if (data.status === 'erro') {
    // Backend answered the erro envelope — the PT-BR lines render verbatim.
    return (
      <div className="space-y-4">
        <ErrorPanel erros={data.erros} />
      </div>
    )
  }

  // Estágio nome via the estagios lookup (the row itself carries estagio_id;
  // D-05 keeps the vocabulary user-owned).
  const nomePorEstagio = new Map<number, string>(
    data.estagios.map((estagio) => [estagio.id, estagio.nome] as const),
  )

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">{RASTREADOR_PAGE_TITLE}</h2>

      {/* Contadores — honest, derived server-side from persisted events only
          (D-07): the UI renders the numbers, never recomputes. */}
      <dl className="grid grid-cols-3 gap-2">
        {CONTADORES_ORDEM.map((chave) => (
          <div key={chave} className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
            <dt className="text-sm font-medium text-gray-800">
              {RASTREADOR_CONTADORES_LABELS[chave]}
            </dt>
            <dd className="mt-0.5 text-lg font-semibold text-gray-900">
              {data.contadores[chave]}
            </dd>
          </div>
        ))}
      </dl>

      <section aria-labelledby="rastreador-candidaturas-title">
        <h3 id="rastreador-candidaturas-title" className="text-base font-semibold text-gray-900">
          {RASTREADOR_CANDIDATURAS_TITLE}
        </h3>
        {data.candidaturas.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">{RASTREADOR_SEM_CANDIDATURAS}</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {data.candidaturas.map((candidatura) => (
              <li
                key={candidatura.id}
                className="rounded-md border border-gray-200 bg-white shadow-sm p-4"
              >
                <p className="text-sm font-semibold text-gray-900">
                  {candidatura.empresa} — {candidatura.cargo}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {nomePorEstagio.get(candidatura.estagio_id) ?? RASTREADOR_SEM_ESTAGIO}
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Minimal creation form — the plan-07-03 CandidaturaForm replaces this
          block without architectural change (same mutation, same query key). */}
      <form
        className="rounded-md border border-gray-200 bg-white shadow-sm p-4"
        onSubmit={(event) => {
          event.preventDefault()
          if (!podeEnviar || criar.isPending) return
          setErros(null)
          criar.mutate({
            empresa: empresa.trim(),
            cargo: cargo.trim(),
            ...(prefill ? { jd_texto: prefill.jd_texto } : {}),
          })
        }}
      >
        <h3 className="text-base font-semibold text-gray-900">{RASTREADOR_FORM_TITLE}</h3>
        <div className="mt-3 space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_EMPRESA}</span>
            <input
              type="text"
              value={empresa}
              maxLength={EMPRESA_MAX_CHARS}
              placeholder={RASTREADOR_PLACEHOLDER_EMPRESA}
              onChange={(event) => setEmpresa(event.target.value)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_CARGO}</span>
            <input
              type="text"
              value={cargo}
              maxLength={CARGO_MAX_CHARS}
              placeholder={RASTREADOR_PLACEHOLDER_CARGO}
              onChange={(event) => setCargo(event.target.value)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
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
          disabled={!podeEnviar || criar.isPending}
          className={`mt-3 ${PRIMARY_BUTTON_CLASSES}`}
        >
          {criar.isPending ? RASTREADOR_CTA_INFLIGHT : RASTREADOR_CTA}
        </button>
      </form>
    </div>
  )
}
