import { useState } from 'react'

import {
  CANCELAR_EDICAO_CTA,
  CANCELAR_SUJA_MESSAGE,
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CONTINUAR_EDITANDO_CTA,
  DESCARTAR_ALTERACOES_CTA,
  EDITAR_ARIA_LABEL,
  POLICY_EDICAO,
  QUIET_BUTTON_CLASSES,
  SALVAR_ALTERACOES_CTA,
  TEXTAREA_CLASSES,
} from '../constants/ui'
import { ConfirmStrip } from './ConfirmStrip'

/**
 * The LinkedIn one-at-a-time editor atom (D-12, plan 06-03): which block
 * (and which Experiência entry) is being edited plus the textarea draft.
 * `inicial` is the pre-fill from the displayed text — dirty is DERIVED as
 * `draft !== inicial` (never stored, so it cannot drift). SIBLING, not a
 * modification: the shipped SectionEditor's bounds are Currículo-typed
 * (`textoEditorValido` pins the resume resumo ceiling), and the UI-SPEC
 * scope fence forbids touching shipped Currículo behavior — the visuals and
 * the ConfirmStrip contract are pinned identical here instead.
 */
export interface LinkedinEditorState {
  bloco: LinkedinEditorBloco
  /** Experiência only: which entry's descricao is being edited. */
  entryIdx: number | null
  draft: string
  inicial: string
}

export type LinkedinEditorBloco = 'headline' | 'sobre' | 'experiencias' | 'habilidades'

interface LinkedinSectionEditorProps {
  /** The PT-BR block label for the textarea's aria-label ({secao} slot). */
  secaoLabel: string
  draft: string
  /** Derived by the parent: draft !== inicial. */
  dirty: boolean
  /** False disables Salvar alterações and shows `guardHint`. */
  canSave: boolean
  /** The guard line shown while !canSave: the over-limit reduce-first hint
   *  (WR-01) or the zero-items EDIT_SAVE_GUARD (Habilidades granularity). */
  guardHint: string
  /** The block's limit client mirror (D-05) — maxLength blocks growth.
   *  undefined for Habilidades (no character limit exists). The over-limit
   *  guard is still real: backend output can legitimately arrive OVER the
   *  limit (D-07 flagged, never truncated), so the pre-fill can start over. */
  maxLength: number | undefined
  /** CR-01: a long op is pending — BOTH footer buttons freeze for the flight
   *  (a regen response swaps secoes wholesale; a mid-flight save would be
   *  silently destroyed by that swap). The draft itself stays editable. */
  locked: boolean
  onDraftChange: (valor: string) => void
  onSave: () => void
  /** Discard + close. Only reached directly when clean; when dirty the
   *  internal ConfirmStrip gates it (Continuar editando / Descartar). */
  onCancel: () => void
  /** Dirty-discard + close — the ConfirmStrip's confirmed path ONLY. The
   *  parent stacks the dirty draft into Versões BEFORE closing, so the
   *  strip's stack-first contract holds on this path too (WR-02/D-08). */
  onDescartar: () => void
}

/**
 * The inline LinkedIn block editor (D-12): replaces the block's content in
 * place — no modal, no separate view. Granularity (UI-SPEC): Headline/Sobre
 * one textarea for the whole string; Experiência one per entry (the entry's
 * descricao only — company/title stay fixed, they are the profile-fact
 * anchor); Habilidades one skill per line (the parent splits/trims/drops on
 * save). Footer: Salvar alterações (compact secondary, disabled with the
 * guard hint while unsavable) · Cancelar edição (quiet) + the D-02 policy
 * line repeated. Cancel on a clean editor reverts immediately; on a dirty
 * editor swaps to the inline amber ConfirmStrip — never a browser dialog.
 * All content renders as JSX text children (T-06-05 posture).
 */
export function LinkedinSectionEditor({
  secaoLabel,
  draft,
  dirty,
  canSave,
  guardHint,
  maxLength,
  locked,
  onDraftChange,
  onSave,
  onCancel,
  onDescartar,
}: LinkedinSectionEditorProps) {
  // Local-only: whether the dirty-cancel confirm strip is showing. The
  // component unmounts when the editor closes, so this resets naturally.
  const [confirmandoDescarte, setConfirmandoDescarte] = useState(false)

  return (
    <div className="mt-2 space-y-2">
      <textarea
        aria-label={EDITAR_ARIA_LABEL.replace('{secao}', secaoLabel)}
        value={draft}
        onChange={(event) => onDraftChange(event.target.value)}
        maxLength={maxLength}
        className={TEXTAREA_CLASSES}
      />
      {!confirmandoDescarte && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <button
            type="button"
            onClick={onSave}
            disabled={!canSave || locked}
            className={COMPACT_SECONDARY_BUTTON_CLASSES}
          >
            {SALVAR_ALTERACOES_CTA}
          </button>
          <button
            type="button"
            onClick={() => (dirty ? setConfirmandoDescarte(true) : onCancel())}
            disabled={locked}
            className={QUIET_BUTTON_CLASSES}
          >
            {CANCELAR_EDICAO_CTA}
          </button>
        </div>
      )}
      {!canSave && (
        <p className="text-xs text-gray-500" role="status">
          {guardHint}
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
          onConfirm={onDescartar}
        />
      )}
    </div>
  )
}
