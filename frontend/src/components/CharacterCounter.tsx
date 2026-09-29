// D-06 live character counter (plan 06-01): "{count}/{limite} caracteres" —
// one shared component (IN-04), presentational only. Props are PURE NUMBERS —
// the string formatting lives in a pure function so it stays offline-testable
// per house policy (no JS test runner). Counts are CODE-UNIT counts: the
// caller passes the JS .length of the same string the server counted with
// Python len (probe edge LI-02/encoding). States (UI-SPEC Component
// conventions): gray normal, amber at >= 90% of the limit, red over limit —
// the approved amber-aviso / red-erro family; the count text itself means the
// state is never conveyed by color alone.

import { LINKEDIN_COUNTER } from '../constants/ui'

export function contadorClasses(count: number, limite: number): string {
  if (count > limite) return 'mt-2 text-xs text-red-700'
  if (limite > 0 && count >= limite * 0.9) return 'mt-2 text-xs text-amber-700'
  return 'mt-2 text-xs text-gray-500'
}

/** Pure formatter for "{count}/{limite} caracteres" (UI-SPEC counter format). */
export function formatarContador(count: number, limite: number): string {
  return LINKEDIN_COUNTER.replace('{count}', String(count)).replace('{limite}', String(limite))
}

interface CharacterCounterProps {
  count: number
  limite: number
}

export function CharacterCounter({ count, limite }: CharacterCounterProps) {
  return <p className={contadorClasses(count, limite)}>{formatarContador(count, limite)}</p>
}
