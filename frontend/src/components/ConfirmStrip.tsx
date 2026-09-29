import {
  COMPACT_SECONDARY_BUTTON_CLASSES,
  QUIET_BUTTON_CLASSES,
} from '../constants/ui'

interface ConfirmStripProps {
  /** The strip's question line — rendered after the aria-hidden ⚠ glyph. */
  message: string
  /** Optional muted note line under the question (e.g. the D-14 promise). */
  note?: string
  /** What is KEPT (quiet) — the safe choice, rendered first. */
  cancelLabel: string
  /** What PROCEEDS (compact secondary) — the speed-bump action. */
  confirmLabel: string
  onCancel: () => void
  onConfirm: () => void
}

/**
 * The ONE shared inline amber confirm strip (UI-SPEC "panels, not modals" —
 * load-bearing): all three Phase 5 confirmations (dirty-cancel edit, section
 * regen over edits, full regen with edits) render THIS component inline in
 * the page flow. No browser dialogs, no toasts, no modal overlays — browser
 * dialogs are banned for the whole phase. Amber means "pay attention, you
 * decide" (suspicion/attention only — never an error verdict; red stays
 * failure-only). The strips are speed bumps, not danger guards: the
 * "discarded" text is always stacked into Versões before anything proceeds
 * (D-14), so nothing is ever irrecoverable. All content renders as JSX text
 * children — no raw-HTML injection path (T-01-08 posture).
 */
export function ConfirmStrip({
  message,
  note,
  cancelLabel,
  confirmLabel,
  onCancel,
  onConfirm,
}: ConfirmStripProps) {
  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800">
      <p>
        <span aria-hidden>⚠</span> {message}
      </p>
      {note && <p className="mt-1 text-xs text-amber-700">{note}</p>}
      <div className="mt-2 flex flex-wrap gap-2">
        <button type="button" onClick={onCancel} className={QUIET_BUTTON_CLASSES}>
          {cancelLabel}
        </button>
        <button type="button" onClick={onConfirm} className={COMPACT_SECONDARY_BUTTON_CLASSES}>
          {confirmLabel}
        </button>
      </div>
    </div>
  )
}
