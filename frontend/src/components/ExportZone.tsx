import {
  EXPORTAR_CAPTION,
  EXPORTAR_CTA,
  EXPORTAR_CTA_INFLIGHT,
  EXPORTAR_ERROR_HINT,
  EXPORTAR_ERROR_TITLE,
  EXPORTAR_RECEIPT,
  PRIMARY_BUTTON_CLASSES,
} from '../constants/ui'

interface ExportZoneProps {
  /** Fires the one export POST — the caller (CurriculoHome) owns the mutation
   *  and the downloadPdf trigger; this component is render-only for bytes. */
  onExportar: () => void
  /** Export POST in flight — swaps the CTA label. */
  exporting: boolean
  /** Disabled while ANY long operation runs (export pending OR gerar pending —
   *  symmetric locking; JD/language edits do NOT disable it). */
  ctaDisabled: boolean
  /** Backend download filename after a success — null pre-export. Failure
   *  paths NEVER clear it (a failed export never blanks prior checked state). */
  receiptFilename: string | null
  /** Export error lines (backend PT-BR verbatim, or [] for a fetch failure) —
   *  null when no export error is showing. */
  erros: string[] | null
}

/**
 * Zone 6 — export control (D-09/D-11/D-13): primary CTA below the result card,
 * expectation caption, green success receipt (role="status"), and the gate-
 * failure red panel (ErrorPanel discipline — backend lines VERBATIM, never
 * parsed/re-mapped; no separate retry button — the CTA above IS the retry
 * path). No modal, no toast — inline blocks only. All text renders as JSX
 * text children (T-04-07 posture: no raw-HTML injection path).
 */
export function ExportZone({
  onExportar,
  exporting,
  ctaDisabled,
  receiptFilename,
  erros,
}: ExportZoneProps) {
  return (
    <div>
      <button type="button" onClick={onExportar} disabled={ctaDisabled} className={PRIMARY_BUTTON_CLASSES}>
        {exporting ? EXPORTAR_CTA_INFLIGHT : EXPORTAR_CTA}
      </button>
      <p className="mt-2 text-xs text-gray-500">{EXPORTAR_CAPTION}</p>

      {receiptFilename !== null && (
        <p
          role="status"
          className="mt-4 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700"
        >
          {EXPORTAR_RECEIPT.replace('{filename}', receiptFilename)}
        </p>
      )}

      {/* Hidden while a retry is in flight (house `!gerar.isPending` discipline
          from CurriculoHome) — the in-flight hint takes over the live region. */}
      {erros !== null && !exporting && (
        <section
          aria-labelledby="exportar-error-title"
          className="mt-4 rounded-md border border-red-300 bg-red-50 px-4 py-3"
        >
          <h3 id="exportar-error-title" className="font-semibold text-red-700">
            {EXPORTAR_ERROR_TITLE}
          </h3>
          {erros.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-sm text-red-700">
              {erros.map((linha, i) => (
                <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
                  {linha}
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-red-600">{EXPORTAR_ERROR_HINT}</p>
        </section>
      )}
    </div>
  )
}
