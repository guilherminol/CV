import { PERFIL_ERROR_HINT, PERFIL_ERROR_TITLE } from '../constants/ui'

interface ErrorPanelProps {
  /** Backend erros[] lines — already PT-BR with the exact file/field path. */
  erros: string[]
}

/**
 * Renders the backend's erros[] lines VERBATIM (D-13/D-14): the backend
 * produces PT-BR messages naming the exact file/field path — this panel must
 * not parse, re-map, or translate them (D-13 division of labor). A broken
 * profile is a rendered UI state, not a crash: the app stays up around it.
 */
export function ErrorPanel({ erros }: ErrorPanelProps) {
  return (
    <section
      aria-labelledby="error-panel-title"
      className="rounded-md border border-red-300 bg-red-50 px-4 py-3"
    >
      <h2 id="error-panel-title" className="font-semibold text-red-700">
        {PERFIL_ERROR_TITLE}
      </h2>
      <ul className="mt-2 list-disc pl-5 text-sm text-red-700">
        {erros.map((linha, i) => (
          <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
            {linha}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-red-600">{PERFIL_ERROR_HINT}</p>
    </section>
  )
}
