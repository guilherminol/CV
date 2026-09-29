import { useEffect, useRef, useState } from 'react'

import {
  COMPACT_SECONDARY_BUTTON_CLASSES,
  LINKEDIN_COPIADO,
  LINKEDIN_COPIAR,
  LINKEDIN_COPIAR_FALHA,
} from '../constants/ui'

interface CopiarButtonProps {
  /** The text EXACTLY as displayed — what lands on the clipboard (D-08:
   *  the displayed block IS the deliverable, so the parent passes the same
   *  string it renders; per experiência entry that is the entry's
   *  descricao ONLY — company/title stay out, LinkedIn has separate fields). */
  text: string
  /** Override label (default "Copiar"); the success swap is always "Copiado!". */
  label?: string
}

/**
 * The D-08 copy affordance (plan 06-03): navigator.clipboard.writeText of the
 * displayed text with in-place label feedback — "Copiado!" for ~2 s via a
 * setTimeout cleared on unmount, announced through aria-live="polite" (status
 * never conveyed by color/visual alone). On rejection the pinned red
 * manual-select line renders under the button and persists until the NEXT
 * successful copy — never a browser dialog, never silent. No codebase analog
 * existed (06-PATTERNS "No Analog"): the failure path follows the
 * downloadPdf convention of an exported helper owning one browser API.
 * User-initiated only; copies exactly the reviewed text (T-06-06 accepted).
 * All content renders as JSX text children — no raw-HTML path (T-06-05).
 */
export function CopiarButton({ text, label = LINKEDIN_COPIAR }: CopiarButtonProps) {
  const [copiado, setCopiado] = useState(false)
  const [falhou, setFalhou] = useState(false)
  const timerRef = useRef<number | null>(null)

  // Clear the pending "Copiado!" timer on unmount — never leak a setState
  // into an unmounted component (house 06-01 precedent).
  useEffect(() => {
    return () => {
      if (timerRef.current !== null) clearTimeout(timerRef.current)
    }
  }, [])

  function copiar() {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        // The failure line persists until the next SUCCESSFUL copy (UI-SPEC).
        setFalhou(false)
        setCopiado(true)
        if (timerRef.current !== null) clearTimeout(timerRef.current)
        timerRef.current = window.setTimeout(() => setCopiado(false), 2000)
      })
      .catch(() => {
        setCopiado(false)
        setFalhou(true)
      })
  }

  return (
    <span className="inline-flex flex-col items-start">
      <button
        type="button"
        onClick={copiar}
        aria-live="polite"
        className={COMPACT_SECONDARY_BUTTON_CLASSES}
      >
        {copiado ? LINKEDIN_COPIADO : label}
      </button>
      {falhou && <p className="mt-2 text-xs text-red-600">{LINKEDIN_COPIAR_FALHA}</p>}
    </span>
  )
}
