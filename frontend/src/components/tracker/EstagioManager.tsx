import { useState } from 'react'
import type { EstagioDTO } from '../../api/client'
import { ErrorPanel } from '../ErrorPanel'
import {
  CANCELAR_EDICAO_CTA,
  COMPACT_SECONDARY_BUTTON_CLASSES,
  HINT_INPUT_CLASSES,
  QUIET_BUTTON_CLASSES,
  RASTREADOR_ESTAGIO_ADD_CTA,
  RASTREADOR_ESTAGIO_ADD_PLACEHOLDER,
  RASTREADOR_ESTAGIO_MOVER_BAIXO,
  RASTREADOR_ESTAGIO_MOVER_CIMA,
  RASTREADOR_ESTAGIO_REMOVER_CTA,
  RASTREADOR_ESTAGIO_RENOMEAR_CTA,
  RASTREADOR_LIMITE_ESTAGIO_NOME,
  SALVAR_ALTERACOES_CTA,
} from '../../constants/ui'

interface EstagioManagerProps {
  estagios: EstagioDTO[]
  /** Erro envelope lines (e.g. the blocked-removal refusal) rendered verbatim. */
  erros: string[] | null
  pendente: boolean
  onCriar: (nome: string) => void
  onRenomear: (id: number, nome: string) => void
  /** The COMPLETE stage id list in the new order (the server assigns 1..n). */
  onReordenar: (ordens: number[]) => void
  onRemover: (id: number) => void
}

/**
 * The user's stage vocabulary, fully manageable from the UI (D-05): add,
 * rename (inline), reorder (up/down over the whole id list), remove.
 * Removal is the HONEST flow: attempt → the backend refuses with its PT-BR
 * envelope while any candidatura references the stage → the lines render
 * verbatim through ErrorPanel. The UI never guesses about references (single
 * user, cheap call) and no cascade ever runs (D-05/D-04).
 */
export function EstagioManager({
  estagios,
  erros,
  pendente,
  onCriar,
  onRenomear,
  onReordenar,
  onRemover,
}: EstagioManagerProps) {
  const [novoNome, setNovoNome] = useState('')
  const [renomeandoId, setRenomeandoId] = useState<number | null>(null)
  const [rascunhoNome, setRascunhoNome] = useState('')

  const moverOrdem = (indice: number, delta: -1 | 1) => {
    const alvo = indice + delta
    if (alvo < 0 || alvo >= estagios.length) return
    // The complete id list in the NEW order — contiguity by construction.
    const ordens = estagios.map((estagio) => estagio.id)
    ;[ordens[indice], ordens[alvo]] = [ordens[alvo], ordens[indice]]
    onReordenar(ordens)
  }

  const confirmarRenomeio = () => {
    if (renomeandoId === null || !rascunhoNome.trim() || pendente) return
    onRenomear(renomeandoId, rascunhoNome.trim())
    setRenomeandoId(null)
    setRascunhoNome('')
  }

  return (
    <div>
      {erros && (
        <div className="mb-3">
          <ErrorPanel erros={erros} />
        </div>
      )}

      {/* Add — appends at the end of the board (ordem = max + 1, server-side). */}
      <form
        className="flex gap-2"
        aria-label={RASTREADOR_ESTAGIO_ADD_CTA}
        onSubmit={(event) => {
          event.preventDefault()
          if (!novoNome.trim() || pendente) return
          onCriar(novoNome.trim())
          setNovoNome('')
        }}
      >
        <input
          type="text"
          value={novoNome}
          maxLength={RASTREADOR_LIMITE_ESTAGIO_NOME}
          placeholder={RASTREADOR_ESTAGIO_ADD_PLACEHOLDER}
          onChange={(event) => setNovoNome(event.target.value)}
          className={HINT_INPUT_CLASSES}
        />
        <button
          type="submit"
          disabled={!novoNome.trim() || pendente}
          className={COMPACT_SECONDARY_BUTTON_CLASSES}
        >
          {RASTREADOR_ESTAGIO_ADD_CTA}
        </button>
      </form>

      <ul className="mt-3 space-y-2">
        {estagios.map((estagio, indice) => (
          <li
            key={estagio.id}
            className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2"
          >
            {renomeandoId === estagio.id ? (
              <div className="flex flex-wrap items-center gap-2">
                <input
                  type="text"
                  value={rascunhoNome}
                  maxLength={RASTREADOR_LIMITE_ESTAGIO_NOME}
                  onChange={(event) => setRascunhoNome(event.target.value)}
                  className={HINT_INPUT_CLASSES}
                  aria-label={RASTREADOR_ESTAGIO_RENOMEAR_CTA}
                />
                <button
                  type="button"
                  onClick={confirmarRenomeio}
                  disabled={!rascunhoNome.trim() || pendente}
                  className={COMPACT_SECONDARY_BUTTON_CLASSES}
                >
                  {SALVAR_ALTERACOES_CTA}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRenomeandoId(null)
                    setRascunhoNome('')
                  }}
                  disabled={pendente}
                  className={QUIET_BUTTON_CLASSES}
                >
                  {CANCELAR_EDICAO_CTA}
                </button>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium text-gray-900">
                  {indice + 1}. {estagio.nome}
                </span>
                <span className="ml-auto flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setRenomeandoId(estagio.id)
                      setRascunhoNome(estagio.nome)
                    }}
                    disabled={pendente}
                    className={QUIET_BUTTON_CLASSES}
                  >
                    {RASTREADOR_ESTAGIO_RENOMEAR_CTA}
                  </button>
                  <button
                    type="button"
                    onClick={() => onRemover(estagio.id)}
                    disabled={pendente}
                    className={QUIET_BUTTON_CLASSES}
                  >
                    {RASTREADOR_ESTAGIO_REMOVER_CTA}
                  </button>
                  <button
                    type="button"
                    onClick={() => moverOrdem(indice, -1)}
                    disabled={pendente || indice === 0}
                    className={COMPACT_SECONDARY_BUTTON_CLASSES}
                  >
                    {RASTREADOR_ESTAGIO_MOVER_CIMA}
                  </button>
                  <button
                    type="button"
                    onClick={() => moverOrdem(indice, 1)}
                    disabled={pendente || indice === estagios.length - 1}
                    className={COMPACT_SECONDARY_BUTTON_CLASSES}
                  >
                    {RASTREADOR_ESTAGIO_MOVER_BAIXO}
                  </button>
                </span>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
