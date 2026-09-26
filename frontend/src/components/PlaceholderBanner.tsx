import { BANNER_SUBTITLE, BANNER_TITLE } from '../constants/ui'

/**
 * Visible whenever the profile ships placeholder data (example: true, D-11).
 * The user must ALWAYS see when example data is in use (SC3).
 */
export function PlaceholderBanner() {
  return (
    <div
      role="status"
      className="mb-6 rounded-md border border-amber-400 bg-amber-100 px-4 py-3 text-amber-900"
    >
      <p className="font-semibold">{BANNER_TITLE}</p>
      <p className="mt-1 text-sm">{BANNER_SUBTITLE}</p>
    </div>
  )
}
