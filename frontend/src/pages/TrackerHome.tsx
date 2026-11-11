import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  adiarFollowup,
  criarCandidatura,
  executarFollowup,
  fetchTrackerResumo,
  moverCandidatura,
  registrarEvento,
  type CandidaturaDTO,
  type EventoRegistroPayload,
  type ResumeLanguage,
} from '../api/client'
import { ErrorPanel } from '../components/ErrorPanel'
import { CandidaturaForm, type CandidaturaFormPayload } from '../components/tracker/CandidaturaForm'
import { ContadoresGrid } from '../components/tracker/ContadoresGrid'
import { EventosPanel } from '../components/tracker/EventosPanel'
import { KanbanBoard } from '../components/tracker/KanbanBoard'
import {
  RASTREADOR_ARQUIVADA_SUFIXO,
  RASTREADOR_DETALHE_VAZIO,
  RASTREADOR_FETCH_ERRO,
  RASTREADOR_FORM_TITLE,
  RASTREADOR_LABEL_CONTATO_RECRUTADOR,
  RASTREADOR_LABEL_DATA_APLICACAO,
  RASTREADOR_LABEL_FAIXA_SALARIAL,
  RASTREADOR_LABEL_FONTE,
  RASTREADOR_LABEL_JD_TEXTO,
  RASTREADOR_LABEL_LINK_VAGA,
  RASTREADOR_LABEL_MODALIDADE,
  RASTREADOR_LABEL_NOTAS,
  RASTREADOR_LABEL_PRAZO_RETORNO,
  RASTREADOR_LOADING,
  RASTREADOR_MODALIDADE_LABELS,
  RASTREADOR_OPERACAO_ERRO,
  RASTREADOR_PAGE_TITLE,
  RASTREADOR_PIPELINE_TITLE,
  RASTREADOR_SEM_CANDIDATURAS,
  RASTREADOR_SEM_ESTAGIO,
  RASTREADOR_VISAO_GERAL_TITLE,
} from '../constants/ui'

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

/** Loud-null for the detail grid (A-UI-2): null/blank payload fields render
 * the muted marker, never a silent blank cell. */
function valorOuVazio(valor: string | null): string | null {
  return valor && valor.trim() ? valor : null
}

/**
 * The Rastreador view (fifth nav view, the app's FIRST persistent state):
 * honest contadores, the server-sorted overview, the one-at-a-time detail
 * region (field grid + EventosPanel), and the full D-06 form — every
 * mutation flows through ONE shared ['tracker'] query key so the whole page
 * can never desynchronize (Pitfall 6). Plan 07-03 Tasks 2/3 complete the
 * assembly: the KanbanBoard mounts in the Pipeline slot, then the
 * EstagioManager + export sections.
 */
export default function TrackerHome({ prefill, onPrefillConsumida }: TrackerHomeProps) {
  const queryClient = useQueryClient()
  // React Query v5: single options object; initial-load state is isPending (Pitfall 9).
  const { data, isPending, isError } = useQuery({
    queryKey: ['tracker'],
    queryFn: fetchTrackerResumo,
  })

  const [abertaId, setAbertaId] = useState<number | null>(null)
  const [formKey, setFormKey] = useState(0)
  const [criarErros, setCriarErros] = useState<string[] | null>(null)
  const [eventosErros, setEventosErros] = useState<string[] | null>(null)
  const [moverErros, setMoverErros] = useState<string[] | null>(null)
  const [registroReset, setRegistroReset] = useState(0)

  // First persistent view in the app — ephemeral-state pages never needed
  // this (Pitfall 6): the shared ['tracker'] cache must refresh after EVERY
  // successful mutation or kanban/overview/contadores desynchronize.
  const invalidar = () => queryClient.invalidateQueries({ queryKey: ['tracker'] })

  const criar = useMutation({
    mutationFn: criarCandidatura,
    onSuccess: (resultado) => {
      if (resultado.status === 'ok') {
        setCriarErros(null)
        setFormKey((chave) => chave + 1) // fresh form for the next entry
        if (prefill) {
          onPrefillConsumida() // D-13: the JD went into the created candidatura
        }
        invalidar()
      } else {
        // Backend PT-BR lines verbatim; the form stays mounted.
        setCriarErros(resultado.erros)
      }
    },
    onError: () => setCriarErros([RASTREADOR_OPERACAO_ERRO]),
  })

  const mover = useMutation({
    mutationFn: ({ id, estagioId }: { id: number; estagioId: number }) =>
      moverCandidatura(id, estagioId),
    onSuccess: (resultado) => {
      if (resultado.status === 'ok') {
        setMoverErros(null)
        invalidar()
      } else {
        setMoverErros(resultado.erros)
      }
    },
    onError: () => setMoverErros([RASTREADOR_OPERACAO_ERRO]),
  })

  const registrar = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: EventoRegistroPayload }) =>
      registrarEvento(id, payload),
    onSuccess: (resultado) => {
      if (resultado.status === 'ok') {
        setEventosErros(null)
        setRegistroReset((chave) => chave + 1)
        invalidar()
      } else {
        setEventosErros(resultado.erros)
      }
    },
    onError: () => setEventosErros([RASTREADOR_OPERACAO_ERRO]),
  })

  const executar = useMutation({
    mutationFn: (id: number) => executarFollowup(id),
    onSuccess: (resultado) => {
      if (resultado.status === 'ok') {
        setEventosErros(null)
        invalidar()
      } else {
        setEventosErros(resultado.erros)
      }
    },
    onError: () => setEventosErros([RASTREADOR_OPERACAO_ERRO]),
  })

  const adiar = useMutation({
    mutationFn: ({ id, novaData }: { id: number; novaData: string }) =>
      adiarFollowup(id, novaData),
    onSuccess: (resultado) => {
      if (resultado.status === 'ok') {
        setEventosErros(null)
        invalidar()
      } else {
        setEventosErros(resultado.erros)
      }
    },
    onError: () => setEventosErros([RASTREADOR_OPERACAO_ERRO]),
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

  // The ONE open detail (house one-editor-at-a-time convention, A-UI-2).
  const aberta: CandidaturaDTO | null =
    abertaId === null
      ? null
      : (data.candidaturas.find((candidatura) => candidatura.id === abertaId) ?? null)

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">{RASTREADOR_PAGE_TITLE}</h2>

      {/* Contadores — honest, derived server-side from persisted events only
          (D-07): the UI renders the numbers, never recomputes. */}
      <ContadoresGrid contadores={data.contadores} />

      {/* Visão geral — the payload order IS the server-sorted order (prazo
          proximity first, NULL-prazo last, D-09): render in order, never
          re-sort client-side. */}
      <section aria-labelledby="rastreador-visao-geral-title">
        <h3 id="rastreador-visao-geral-title" className="text-base font-semibold text-gray-900">
          {RASTREADOR_VISAO_GERAL_TITLE}
        </h3>
        {data.candidaturas.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">{RASTREADOR_SEM_CANDIDATURAS}</p>
        ) : (
          <ul className="mt-2 space-y-2">
            {data.candidaturas.map((candidatura) => (
              <li key={candidatura.id}>
                <button
                  type="button"
                  onClick={() => setAbertaId(candidatura.id)}
                  aria-pressed={abertaId === candidatura.id}
                  className="w-full rounded-md border border-gray-200 bg-white p-4 text-left shadow-sm hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                >
                  <span className="text-sm font-semibold text-gray-900">
                    {candidatura.empresa} — {candidatura.cargo}
                  </span>
                  <span className="mt-1 block text-xs text-gray-500">
                    {nomePorEstagio.get(candidatura.estagio_id) ?? RASTREADOR_SEM_ESTAGIO}
                    {candidatura.arquivada && (
                      <span className="text-gray-400">{RASTREADOR_ARQUIVADA_SUFIXO}</span>
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Pipeline — the D-14 board: one column per stage in estagios ordem.
          The board is the ACTIVE pipeline: archived candidaturas stay out of
          the columns (archive is the closure path, D-04 — the overview above
          keeps the full history and the export carries it). Drops resolve
          through the mover mutation + ['tracker'] invalidation — no
          optimistic update (A8: the refetch is the truth). */}
      <section aria-labelledby="rastreador-pipeline-title">
        <h3 id="rastreador-pipeline-title" className="text-base font-semibold text-gray-900">
          {RASTREADOR_PIPELINE_TITLE}
        </h3>
        <div className="mt-2">
          <KanbanBoard
            estagios={data.estagios}
            candidaturas={data.candidaturas.filter((candidatura) => !candidatura.arquivada)}
            abertaId={abertaId}
            onAbrir={setAbertaId}
            onMover={(id, estagioId) => mover.mutate({ id, estagioId })}
          />
        </div>
        {moverErros && (
          <div className="mt-2">
            <ErrorPanel erros={moverErros} />
          </div>
        )}
      </section>

      {/* Detail region — exactly ONE candidatura open at a time: the aligned
          field grid with loud nulls (A-UI-2), link_vaga as the ONLY anchor
          (S10: rel="noreferrer", JSX-text-only posture), and the EventosPanel
          with the follow-up lifecycle controls. */}
      {aberta && (
        <section
          aria-labelledby="rastreador-detalhe-title"
          className="rounded-md border border-gray-200 bg-white shadow-sm p-4"
        >
          <h3 id="rastreador-detalhe-title" className="text-base font-semibold text-gray-900">
            {aberta.empresa} — {aberta.cargo}
          </h3>
          <p className="mt-1 text-xs text-gray-500">
            {nomePorEstagio.get(aberta.estagio_id) ?? RASTREADOR_SEM_ESTAGIO}
          </p>
          <dl className="mt-3 space-y-1 text-sm">
            {(
              [
                [RASTREADOR_LABEL_FONTE, valorOuVazio(aberta.fonte)],
                [RASTREADOR_LABEL_LINK_VAGA, valorOuVazio(aberta.link_vaga)],
                [RASTREADOR_LABEL_DATA_APLICACAO, valorOuVazio(aberta.data_aplicacao)],
                [RASTREADOR_LABEL_PRAZO_RETORNO, valorOuVazio(aberta.prazo_retorno)],
                [RASTREADOR_LABEL_FAIXA_SALARIAL, valorOuVazio(aberta.faixa_salarial)],
                [RASTREADOR_LABEL_CONTATO_RECRUTADOR, valorOuVazio(aberta.contato_recrutador)],
                [
                  RASTREADOR_LABEL_MODALIDADE,
                  aberta.modalidade ? RASTREADOR_MODALIDADE_LABELS[aberta.modalidade] : null,
                ],
                [RASTREADOR_LABEL_NOTAS, valorOuVazio(aberta.notas)],
                [RASTREADOR_LABEL_JD_TEXTO, valorOuVazio(aberta.jd_texto)],
              ] as [string, string | null][]
            ).map(([rotulo, valor]) => (
              <div key={rotulo} className="flex gap-2">
                <dt className="w-44 shrink-0 text-gray-500">{rotulo}</dt>
                {rotulo === RASTREADOR_LABEL_LINK_VAGA && valor ? (
                  <dd className="min-w-0 break-all text-blue-600">
                    <a href={valor} target="_blank" rel="noreferrer" className="hover:underline">
                      {valor}
                    </a>
                  </dd>
                ) : (
                  <dd className={valor ? 'min-w-0 whitespace-pre-wrap' : 'text-gray-400'}>
                    {valor ?? RASTREADOR_DETALHE_VAZIO}
                  </dd>
                )}
              </div>
            ))}
          </dl>
          <div className="mt-3">
            <EventosPanel
              candidatura={aberta}
              erros={eventosErros}
              registroPendente={registrar.isPending}
              followupPendente={executar.isPending || adiar.isPending}
              registroReset={registroReset}
              onRegistrarEvento={(payload) => registrar.mutate({ id: aberta.id, payload })}
              onExecutarFollowup={() => executar.mutate(aberta.id)}
              onAdiarFollowup={(novaData) => adiar.mutate({ id: aberta.id, novaData })}
            />
          </div>
        </section>
      )}

      {/* Full D-06 form — the 07-01 minimal skeleton replaced; the edit path
          (initial values + PATCH semantics) is wired by Task 3 alongside the
          detail-region controls. formKey remounts for a fresh form after a
          successful create. */}
      <CandidaturaForm
        key={formKey}
        titulo={RASTREADOR_FORM_TITLE}
        pendente={criar.isPending}
        erros={criarErros}
        valoresIniciais={{ jd_texto: prefill?.jd_texto ?? '' }}
        onSubmit={(payload: CandidaturaFormPayload) => criar.mutate(payload)}
      />
    </div>
  )
}
