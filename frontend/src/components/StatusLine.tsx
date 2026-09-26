import { PERFIL_STATUS_ERRO, PERFIL_STATUS_OK } from '../constants/ui'

/**
 * Load-status line (D-12): colored dot (aria-hidden) + PT-BR text label —
 * status is never conveyed by color alone. Extracted from App.tsx in plan
 * 03-04 so both homes share the exact same render.
 */
export function StatusLine({ ok }: { ok: boolean }) {
  return (
    <p className="flex items-center gap-2 text-sm text-gray-600">
      <span
        aria-hidden
        className={`h-2 w-2 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`}
      />
      {ok ? PERFIL_STATUS_OK : PERFIL_STATUS_ERRO}
    </p>
  )
}
