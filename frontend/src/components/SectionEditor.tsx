import { useState } from 'react'
import type { SecaoId } from '../api/client'
import {
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CANCELAR_EDICAO_CTA,
  CANCELAR_SUJA_MESSAGE,
  CONTINUAR_EDITANDO_CTA,
  DESCARTAR_ALTERACOES_CTA,
  EDITAR_ARIA_LABEL,
  EDIT_SAVE_GUARD,
  POLICY_EDICAO,
  QUIET_BUTTON_CLASSES,
  REGEN_SECAO_LABELS,
  SALVAR_ALTERACOES_CTA,
  TEXTAREA_CLASSES,
} from '../constants/ui'
import { ConfirmStrip } from './ConfirmStrip'

/**
 * The CurriculoHome one-at-a-time editor atom (D-12): which section (and
 * which Experiência entry) is being edited plus the textarea draft. `inicial`
 * is the pre-fill from the displayed text — dirty is DERIVED as
 * `draft !== inicial` (never stored, so it cannot drift). The draft lives at
 * page level because the D-14 regen-over-edit confirm must stack the dirty
 * draft BEFORE the editor closes (UI-SPEC D-14).
 */
export interface SecaoEditorState {
  secao: SecaoId
  /** Experiência only: which entry's bullets are being edited. */
  entryIdx: number | null
  draft: string
  inicial: string
}

/** Save parser contract (UI-SPEC): split on newlines, trim, drop empties —
 *  matches the export envelope's min_length=1 for list sections. */
export function dividirLinhas(texto: string): string[] {
  return texto
    .split('\n')
    .map((linha) => linha.trim())
    .filter((linha) => linha.length > 0)
}

/** Client min_length guard (must-have: empty/whitespace-only saves are
 *  rejected client-side; the server re-validates strictly). Resumo needs any
 *  non-whitespace text; Experiência/Habilidades need ≥1 non-empty line. */
export function textoEditorValido(secao: SecaoId, draft: string): boolean {
  if (secao === 'resumo') return draft.trim().length > 0
  return dividirLinhas(draft).length > 0
}

interface SectionEditorProps {
  secao: SecaoId
  draft: string
  /** Derived by the parent: draft !== inicial. */
  dirty: boolean
  /** False disables Salvar alterações and shows the save-guard hint. */
  canSave: boolean
  onDraftChange: (valor: string) => void
  onSave: () => void
  /** Discard + close. Only reached directly when clean; when dirty the
   *  internal ConfirmStrip gates it (Continuar editando / Descartar). */
  onCancel: () => void
}

/**
 * The inline per-section textarea editor (D-12): replaces the section's
 * content in place — no modal, no separate view. Granularity (UI-SPEC):
 * Resumo one textarea for the whole string; Experiência one per entry
 * (bullets one per line — company/title stay fixed); Habilidades one skill
 * per line. Footer: Salvar alterações (compact secondary, disabled with the
 * save-guard hint while empty) · Cancelar edição (quiet) + the D-02 policy
 * line repeated. Cancel on a clean editor reverts immediately; on a dirty
 * editor swaps to the inline amber ConfirmStrip — never a browser dialog.
 * All content renders as JSX text children (T-01-08 posture).
 */
export function SectionEditor({
  secao,
  draft,
  dirty,
  canSave,
  onDraftChange,
  onSave,
  onCancel,
}: SectionEditorProps) {
  // Local-only: whether the dirty-cancel confirm strip is showing. The
  // component unmounts when the editor closes, so this resets naturally.
  const [confirmandoDescarte, setConfirmandoDescarte] = useState(false)

  return (
    <div className="mt-2 space-y-2">
      <textarea
        aria-label={EDITAR_ARIA_LABEL.replace('{secao}', REGEN_SECAO_LABELS[secao])}
        value={draft}
        onChange={(event) => onDraftChange(event.target.value)}
        className={TEXTAREA_CLASSES}
      />
      {!confirmandoDescarte && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <button
            type="button"
            onClick={onSave}
            disabled={!canSave}
            className={COMPACT_SECONDARY_BUTTON_CLASSES}
          >
            {SALVAR_ALTERACOES_CTA}
          </button>
          <button
            type="button"
            onClick={() => (dirty ? setConfirmandoDescarte(true) : onCancel())}
            className={QUIET_BUTTON_CLASSES}
          >
            {CANCELAR_EDICAO_CTA}
          </button>
        </div>
      )}
      {!canSave && (
        <p className="text-xs text-gray-500" role="status">
          {EDIT_SAVE_GUARD}
        </p>
      )}
      <p className="text-xs text-gray-500">
        <span aria-hidden>⚠</span> {POLICY_EDICAO}
      </p>
      {confirmandoDescarte && (
        <ConfirmStrip
          message={CANCELAR_SUJA_MESSAGE}
          cancelLabel={CONTINUAR_EDITANDO_CTA}
          confirmLabel={DESCARTAR_ALTERACOES_CTA}
          onCancel={() => setConfirmandoDescarte(false)}
          onConfirm={onCancel}
        />
      )}
    </div>
  )
}
