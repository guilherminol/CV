import { useState } from 'react'
import type { TrackerModalidade } from '../../api/client'
import { ErrorPanel } from '../ErrorPanel'
import {
  CANCELAR_EDICAO_CTA,
  HINT_INPUT_CLASSES,
  PRIMARY_BUTTON_CLASSES,
  RASTREADOR_CTA,
  RASTREADOR_CTA_INFLIGHT,
  RASTREADOR_LABEL_CARGO,
  RASTREADOR_LABEL_CONTATO_RECRUTADOR,
  RASTREADOR_LABEL_DATA_APLICACAO,
  RASTREADOR_LABEL_EMPRESA,
  RASTREADOR_LABEL_FAIXA_SALARIAL,
  RASTREADOR_LABEL_FONTE,
  RASTREADOR_LABEL_JD_TEXTO,
  RASTREADOR_LABEL_LINK_VAGA,
  RASTREADOR_LABEL_MODALIDADE,
  RASTREADOR_LABEL_NOTAS,
  RASTREADOR_LABEL_PRAZO_RETORNO,
  RASTREADOR_PLACEHOLDER_CARGO,
  RASTREADOR_PLACEHOLDER_EMPRESA,
  RASTREADOR_PLACEHOLDER_FONTE,
  RASTREADOR_PLACEHOLDER_JD_TEXTO,
  RASTREADOR_PLACEHOLDER_NOTAS,
  RASTREADOR_LIMITE_CONTATO_RECRUTADOR,
  RASTREADOR_LIMITE_CARGO,
  RASTREADOR_LIMITE_EMPRESA,
  RASTREADOR_LIMITE_FAIXA_SALARIAL,
  RASTREADOR_LIMITE_FONTE,
  RASTREADOR_LIMITE_JD_TEXTO,
  RASTREADOR_LIMITE_LINK_VAGA,
  RASTREADOR_LIMITE_NOTAS,
  RASTREADOR_MODALIDADE_LABELS,
  SALVAR_ALTERACOES_CTA,
  TEXTAREA_CLASSES,
} from '../../constants/ui'

// Pill idiom for the sr-only radio fieldset — the CandidaturaHome/CurriculoHome
// precedent (module-local constants there; same posture here).
const MODALIDADE_SELECTED_CLASSES =
  'cursor-pointer rounded bg-white px-3 py-1 text-sm font-semibold text-blue-600 shadow-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
const MODALIDADE_UNSELECTED_CLASSES =
  'cursor-pointer rounded px-3 py-1 text-sm text-gray-600 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'

/** Optional initial values — the edit path (and the 07-04 prefill seam:
 * jd_texto initializable from props; the create wire contract carries no
 * idioma key, so the prefill's language part stays 07-04's concern). */
export interface CandidaturaFormValores {
  empresa?: string
  cargo?: string
  fonte?: string | null
  link_vaga?: string | null
  data_aplicacao?: string | null
  prazo_retorno?: string | null
  faixa_salarial?: string | null
  contato_recrutador?: string | null
  modalidade?: TrackerModalidade | null
  notas?: string | null
  jd_texto?: string | null
}

/** What the form hands its owner: required fields always present; optional
 * fields present ONLY when non-empty (omitted keys mean "untouched" on the
 * edit path and null on the create path — an empty string would either 422
 * on the date pattern or silently clear a field the edit semantics never
 * intended). */
export interface CandidaturaFormPayload {
  empresa: string
  cargo: string
  fonte?: string
  link_vaga?: string
  data_aplicacao?: string
  prazo_retorno?: string
  faixa_salarial?: string
  contato_recrutador?: string
  modalidade?: TrackerModalidade
  notas?: string
  jd_texto?: string
}

interface CandidaturaFormProps {
  titulo: string
  pendente: boolean
  onSubmit: (payload: CandidaturaFormPayload) => void
  /** Edit mode: submit swaps to "Salvar alterações" and a cancel appears. */
  modoEdicao?: boolean
  valoresIniciais?: CandidaturaFormValores
  onCancelar?: () => void
  erros?: string[] | null
}

/**
 * The full D-06 candidatura form (plan 07-03): presentational + local state —
 * every mutation lives in TrackerHome and bubbles back through onSubmit.
 * Every maxLength mirrors the backend Field bound (WR-01 "Change BOTH
 * together" with models.py named at each field); the stage is NOT a form
 * field — kanban drops own stage changes (server defaults to the first stage
 * on create, 07-01 pin).
 */
export function CandidaturaForm({
  titulo,
  pendente,
  onSubmit,
  modoEdicao = false,
  valoresIniciais,
  onCancelar,
  erros,
}: CandidaturaFormProps) {
  const [empresa, setEmpresa] = useState(valoresIniciais?.empresa ?? '')
  const [cargo, setCargo] = useState(valoresIniciais?.cargo ?? '')
  const [fonte, setFonte] = useState(valoresIniciais?.fonte ?? '')
  const [linkVaga, setLinkVaga] = useState(valoresIniciais?.link_vaga ?? '')
  const [dataAplicacao, setDataAplicacao] = useState(valoresIniciais?.data_aplicacao ?? '')
  const [prazoRetorno, setPrazoRetorno] = useState(valoresIniciais?.prazo_retorno ?? '')
  const [faixaSalarial, setFaixaSalarial] = useState(valoresIniciais?.faixa_salarial ?? '')
  const [contatoRecrutador, setContatoRecrutador] = useState(
    valoresIniciais?.contato_recrutador ?? '',
  )
  const [modalidade, setModalidade] = useState<TrackerModalidade | null>(
    valoresIniciais?.modalidade ?? null,
  )
  const [notas, setNotas] = useState(valoresIniciais?.notas ?? '')
  const [jdTexto, setJdTexto] = useState(valoresIniciais?.jd_texto ?? '')

  const podeEnviar = empresa.trim().length > 0 && cargo.trim().length > 0

  return (
    <form
      className="rounded-md border border-gray-200 bg-white shadow-sm p-4"
      aria-label={titulo}
      onSubmit={(event) => {
        event.preventDefault()
        if (!podeEnviar || pendente) return
        // Trimmed text in; empty optionals OMITTED (see CandidaturaFormPayload).
        onSubmit({
          empresa: empresa.trim(),
          cargo: cargo.trim(),
          ...(fonte.trim() ? { fonte: fonte.trim() } : {}),
          ...(linkVaga.trim() ? { link_vaga: linkVaga.trim() } : {}),
          ...(dataAplicacao ? { data_aplicacao: dataAplicacao } : {}),
          ...(prazoRetorno ? { prazo_retorno: prazoRetorno } : {}),
          ...(faixaSalarial.trim() ? { faixa_salarial: faixaSalarial.trim() } : {}),
          ...(contatoRecrutador.trim() ? { contato_recrutador: contatoRecrutador.trim() } : {}),
          ...(modalidade ? { modalidade } : {}),
          ...(notas.trim() ? { notas: notas.trim() } : {}),
          ...(jdTexto.trim() ? { jd_texto: jdTexto.trim() } : {}),
        })
      }}
    >
      <h3 className="text-base font-semibold text-gray-900">{titulo}</h3>
      <div className="mt-3 space-y-3">
        <label className="block">
          <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_EMPRESA}</span>
          <input
            type="text"
            value={empresa}
            maxLength={RASTREADOR_LIMITE_EMPRESA}
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
            maxLength={RASTREADOR_LIMITE_CARGO}
            placeholder={RASTREADOR_PLACEHOLDER_CARGO}
            onChange={(event) => setCargo(event.target.value)}
            className={`mt-1 ${HINT_INPUT_CLASSES}`}
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_FONTE}</span>
          <input
            type="text"
            value={fonte}
            maxLength={RASTREADOR_LIMITE_FONTE}
            placeholder={RASTREADOR_PLACEHOLDER_FONTE}
            onChange={(event) => setFonte(event.target.value)}
            className={`mt-1 ${HINT_INPUT_CLASSES}`}
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_LINK_VAGA}</span>
          <input
            type="url"
            value={linkVaga}
            maxLength={RASTREADOR_LIMITE_LINK_VAGA}
            onChange={(event) => setLinkVaga(event.target.value)}
            className={`mt-1 ${HINT_INPUT_CLASSES}`}
          />
        </label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-gray-800">
              {RASTREADOR_LABEL_DATA_APLICACAO}
            </span>
            <input
              type="date"
              value={dataAplicacao}
              onChange={(event) => setDataAplicacao(event.target.value)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-800">
              {RASTREADOR_LABEL_PRAZO_RETORNO}
            </span>
            <input
              type="date"
              value={prazoRetorno}
              onChange={(event) => setPrazoRetorno(event.target.value)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
            />
          </label>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-gray-800">
              {RASTREADOR_LABEL_FAIXA_SALARIAL}
            </span>
            <input
              type="text"
              value={faixaSalarial}
              maxLength={RASTREADOR_LIMITE_FAIXA_SALARIAL}
              onChange={(event) => setFaixaSalarial(event.target.value)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-gray-800">
              {RASTREADOR_LABEL_CONTATO_RECRUTADOR}
            </span>
            <input
              type="text"
              value={contatoRecrutador}
              maxLength={RASTREADOR_LIMITE_CONTATO_RECRUTADOR}
              onChange={(event) => setContatoRecrutador(event.target.value)}
              className={`mt-1 ${HINT_INPUT_CLASSES}`}
            />
          </label>
        </div>
        <fieldset>
          <legend className="text-sm font-semibold text-gray-900">
            {RASTREADOR_LABEL_MODALIDADE}
          </legend>
          <div className="mt-2 inline-flex rounded-md border border-gray-300 bg-gray-50 p-1">
            {(Object.keys(RASTREADOR_MODALIDADE_LABELS) as TrackerModalidade[]).map((valor) => (
              <label
                key={valor}
                className={
                  modalidade === valor ? MODALIDADE_SELECTED_CLASSES : MODALIDADE_UNSELECTED_CLASSES
                }
              >
                <input
                  type="radio"
                  name="modalidade"
                  value={valor}
                  checked={modalidade === valor}
                  onChange={() => setModalidade(valor)}
                  className="sr-only"
                />
                {RASTREADOR_MODALIDADE_LABELS[valor]}
              </label>
            ))}
          </div>
        </fieldset>
        <label className="block">
          <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_NOTAS}</span>
          <textarea
            value={notas}
            maxLength={RASTREADOR_LIMITE_NOTAS}
            placeholder={RASTREADOR_PLACEHOLDER_NOTAS}
            onChange={(event) => setNotas(event.target.value)}
            className={`mt-1 ${TEXTAREA_CLASSES} min-h-24`}
          />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-gray-800">{RASTREADOR_LABEL_JD_TEXTO}</span>
          <textarea
            value={jdTexto}
            maxLength={RASTREADOR_LIMITE_JD_TEXTO}
            placeholder={RASTREADOR_PLACEHOLDER_JD_TEXTO}
            onChange={(event) => setJdTexto(event.target.value)}
            className={`mt-1 ${TEXTAREA_CLASSES}`}
          />
        </label>
      </div>
      {erros && (
        <div className="mt-3">
          <ErrorPanel erros={erros} />
        </div>
      )}
      <div className="mt-3 flex items-center gap-3">
        <button
          type="submit"
          disabled={!podeEnviar || pendente}
          className={PRIMARY_BUTTON_CLASSES}
        >
          {modoEdicao
            ? SALVAR_ALTERACOES_CTA
            : pendente
              ? RASTREADOR_CTA_INFLIGHT
              : RASTREADOR_CTA}
        </button>
        {modoEdicao && onCancelar && (
          <button
            type="button"
            onClick={onCancelar}
            disabled={pendente}
            className="text-sm font-semibold text-gray-600 underline-offset-2 hover:text-gray-900 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {CANCELAR_EDICAO_CTA}
          </button>
        )}
      </div>
    </form>
  )
}
