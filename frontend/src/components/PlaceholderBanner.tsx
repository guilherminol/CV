import { BANNER_SUBTITLE, BANNER_TITLE } from '../constants/ui'

/**
 * Prominent placeholder notice (SC3), visible whenever the profile ships
 * example data (example: true, D-11). Purely informational BY DESIGN: the
 * UI offers no dismiss and no way to change the flag — the placeholder
 * state flips only when the user edits content/profile.md themselves.
 */
export function PlaceholderBanner() {
  return (
    <div
      role="status"
      className="rounded-md border-2 border-amber-400 bg-amber-100 px-4 py-3 text-amber-900"
    >
      <p className="flex items-center gap-2 font-semibold">
        <span aria-hidden>⚠</span>
        {BANNER_TITLE}
      </p>
      <p className="mt-1 text-sm">{BANNER_SUBTITLE}</p>
    </div>
  )
}
