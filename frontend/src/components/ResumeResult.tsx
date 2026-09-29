import { useState } from 'react'
import type {
  ExperienciaGeradaDTO,
  ImpactDTO,
  LocalizedText,
  PerfilDTO,
  ResumeLanguage,
  SecoesDTO,
  SecaoId,
} from '../api/client'
import {
  BADGE_DO_PERFIL,
  BADGE_EDITADO,
  BADGE_EDITADO_CLASSES,
  BADGE_GERADO,
  BADGE_GERADO_CLASSES,
  COMPARACAO_TOGGLE,
  COMPARACAO_TOGGLE_HIDE,
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CURRICULO_EPHEMERAL_NOTICE,
  CURRICULO_GENERATED_SECTIONS,
  CURRICULO_REGENERAR,
  CURRICULO_RESULT_TITLE,
  DICA_LABEL,
  DICA_PLACEHOLDER,
  DICA_TOGGLE_ADD,
  DICA_TOGGLE_HIDE,
  EDITAR_ENTRADA_CTA,
  EDITAR_SECAO_CTA,
  GERAR_COM_EDICOES_MESSAGE,
  GERAR_MESMO_ASSIM_CTA,
  HINT_INPUT_CLASSES,
  MANTER_EDICAO_CTA,
  MANTER_EDICOES_CTA,
  POLICY_EDICAO,
  PREVIEW_CONTACT_SEPARATOR,
  PREVIEW_PRESENT,
  PREVIEW_SECTIONS,
  QUIET_BUTTON_CLASSES,
  REGEN_ERROR_HINT,
  REGEN_ERROR_TITLE,
  REGEN_INFLIGHT_LINE,
  REGEN_SECTION_CTA,
  REGEN_SECTION_INFLIGHT,
  REGEN_SECAO_LABELS,
  REGEN_SOBE_EDICAO_MESSAGE,
  REGEN_SOBE_EDICAO_NOTE,
  REGEN_MESMO_ASSIM_CTA,
  VERSOES_TOGGLE,
  VERSOES_TOGGLE_COUNT,
} from '../constants/ui'
import { SectionEditor, textoEditorValido, type SecaoEditorState } from './SectionEditor'
import { ComparisonPanel } from './ComparisonPanel'
import { ConfirmStrip } from './ConfirmStrip'
import { SectionVersionsPanel, type OrigemBadge, type SectionVersion } from './SectionVersionsPanel'

// Pinned UI-SPEC class strings (Component conventions, plan 03-04).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white px-6 py-5 shadow-sm'
const SECONDARY_BUTTON_CLASSES =
  'min-h-10 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
// WR-01 client mirror of the backend's RegenerarRequest.dica bound
// (routes/resume.py Field(max_length=500) — 422 is a client bug, not a UI
// state): the dica input caps at the same bound so an oversized hint is
// prevented at the source, never retried into a dead-end 422.
const DICA_MAX_CHARS = 500

/**
 * Run-language display convention (extends ProfilePreview's D-04 `t()`): EN
 * runs render the `en` value when present, falling back to the pt-BR base
 * (schema-guaranteed); PT-BR runs keep the pt-BR-first convention. The final
 * fallback to any other available value is purely defensive.
 */
function tLang(map: LocalizedText | null | undefined, language: ResumeLanguage): string {
  if (!map) return ''
  if (language === 'en') {
    return map.en ?? map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
  }
  return map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
}

/** Open date ranges show "atual" (ProfilePreview convention). */
function dateRange(start: string, end: string | null | undefined): string {
  return end ? `${start} – ${end}` : `${start} – ${PREVIEW_PRESENT}`
}

type BadgeKind = 'gerado' | 'perfil' | 'editado'

/**
 * D-04 tri-state badges: Gerado (soft blue — LLM product), Do perfil (muted
 * passthrough), Editado (solid blue-600/white — provenance readable at a
 * glance without a new hue). Class strings live in constants/ui.ts (IN-04)
 * so SectionVersionsPanel's origin rows reuse the exact same states.
 */
function Badge({ kind }: { kind: BadgeKind }) {
  const classes =
    kind === 'gerado'
      ? BADGE_GERADO_CLASSES
      : kind === 'editado'
        ? BADGE_EDITADO_CLASSES
        : 'normal-case rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-xs font-semibold text-gray-500'
  const label = kind === 'gerado' ? BADGE_GERADO : kind === 'editado' ? BADGE_EDITADO : BADGE_DO_PERFIL
  return <span className={classes}>{label}</span>
}

/** ProfilePreview Section pattern (bordered uppercase heading) + a badge. */
function Section({
  title,
  badge,
  children,
}: {
  title: string
  badge: BadgeKind
  children: React.ReactNode
}) {
  return (
    <section className="break-inside-avoid">
      <h4 className="flex flex-wrap items-center justify-between gap-x-3 border-b border-gray-200 pb-1 text-sm font-bold uppercase tracking-wide text-gray-500">
        <span>{title}</span>
        <Badge kind={badge} />
      </h4>
      <div className="mt-2 space-y-3">{children}</div>
    </section>
  )
}

/**
 * A generated section with the Phase 5 action row (D-05 + plan 05-02 D-12 +
 * plan 05-03 D-09): "Editar seção" (quiet; hidden for Experiência — its
 * per-entry "Editar entrada" controls live on each entry article) +
 * "Comparar com o perfil" (quiet, aria-expanded; swaps to "Ocultar
 * comparação") + "Adicionar dica" + "Regenerar seção" (05-01). Editing
 * replaces the section's content with the SectionEditor textarea (D-12 — no
 * modal, no separate view); the section-level text block also responds to
 * click as a redundant pointer affordance (the button is the accessible
 * affordance). One editor at a time: while ANY editor is open (or a long op
 * is pending) the edit control disables (locksEdicao). The comparison toggle
 * is READ-ONLY (UI-SPEC locking matrix): usable even while a long op runs or
 * an editor is open, and never disabled. The open ComparisonPanel
 * (D-09/D-10/D-11) mounts under the section content and computes from the
 * CURRENTLY displayed text — zero fetch; suspect marks render ONLY inside the
 * panel, never in the card body (the card is the export-fidelity preview,
 * SC2). In-flight/error behavior unchanged from 05-01.
 */
function GeneratedSection({
  title,
  secao,
  children,
  badge,
  perfil,
  idioma,
  panelTexto,
  panelEntradas,
  editandoAqui,
  onEditarSecao,
  locksEdicao,
  stripPendente,
  onConfirmarStripRegen,
  onCancelarStripRegen,
  versoes,
  versoesAberta,
  onVersoesToggle,
  onRestaurar,
  onRegenerarSecao,
  secaoRegenerando,
  regenerando,
  regenErros,
  dica,
  onDicaChange,
  dicaAberta,
  onDicaToggle,
}: {
  title: string
  secao: SecaoId
  children: React.ReactNode
  badge: OrigemBadge
  perfil: PerfilDTO
  idioma: ResumeLanguage
  /** The section's CURRENTLY displayed text (post-edit) — the comparison
   *  panel's right column (D-09/D-10). */
  panelTexto: string
  /** Experiência only: the displayed generated entries (per-entry alignment). */
  panelEntradas: ExperienciaGeradaDTO[] | null
  editandoAqui: boolean
  /** Section-level edit control; null for Experiência (per-entry controls). */
  onEditarSecao: (() => void) | null
  /** An editor is open (any section) OR a long op is pending. */
  locksEdicao: boolean
  /** D-14 pending confirm for THIS section's regen (amber strip). */
  stripPendente: boolean
  onConfirmarStripRegen: () => void
  onCancelarStripRegen: () => void
  /** Prior versions of this section (newest first) + their disclosure state. */
  versoes: SectionVersion[]
  versoesAberta: boolean
  onVersoesToggle: () => void
  onRestaurar: (indice: number) => void
  onRegenerarSecao: (secao: SecaoId) => void
  secaoRegenerando: SecaoId | null
  regenerando: boolean
  regenErros: Partial<Record<SecaoId, string[]>>
  dica: string
  onDicaChange: (secao: SecaoId, valor: string) => void
  dicaAberta: boolean
  onDicaToggle: (secao: SecaoId) => void
}) {
  const label = REGEN_SECAO_LABELS[secao]
  const pending = secaoRegenerando === secao
  const erros = regenErros[secao]
  const inputId = `dica-input-${secao}`
  // D-09 comparison disclosure — local, read-only session state (usable even
  // while a long op is pending or an editor is open; UI-SPEC locking matrix).
  const [comparacaoAberta, setComparacaoAberta] = useState(false)
  return (
    <Section title={title} badge={badge}>
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
        {onEditarSecao && (
          <button
            type="button"
            onClick={onEditarSecao}
            disabled={locksEdicao}
            className={QUIET_BUTTON_CLASSES}
          >
            {EDITAR_SECAO_CTA}
          </button>
        )}
        {/* Comparar toggle (D-09, plan 05-03): read-only disclosure — never
            disabled (usable while long ops run / an editor is open, UI-SPEC
            locking matrix); aria-expanded per the UI-SPEC. */}
        <button
          type="button"
          onClick={() => setComparacaoAberta((aberta) => !aberta)}
          aria-expanded={comparacaoAberta}
          className={QUIET_BUTTON_CLASSES}
        >
          {comparacaoAberta ? COMPARACAO_TOGGLE_HIDE : COMPARACAO_TOGGLE}
        </button>
        {/* Versoes toggle (D-08): read-only disclosure — usable even while a
            long op is pending; disabled with NO count suffix at zero versions
            (no ghost panel). */}
        <button
          type="button"
          onClick={onVersoesToggle}
          aria-expanded={versoesAberta}
          disabled={versoes.length === 0}
          className={QUIET_BUTTON_CLASSES}
        >
          {versoes.length > 0
            ? VERSOES_TOGGLE_COUNT.replace('{count}', String(versoes.length))
            : VERSOES_TOGGLE}
        </button>
        <button
          type="button"
          onClick={() => onDicaToggle(secao)}
          aria-expanded={dicaAberta}
          disabled={regenerando}
          className={QUIET_BUTTON_CLASSES}
        >
          {dicaAberta ? DICA_TOGGLE_HIDE : DICA_TOGGLE_ADD}
        </button>
        <button
          type="button"
          onClick={() => onRegenerarSecao(secao)}
          disabled={regenerando}
          className={COMPACT_SECONDARY_BUTTON_CLASSES}
        >
          {pending ? REGEN_SECTION_INFLIGHT.replace('{secao}', label) : REGEN_SECTION_CTA}
        </button>
      </div>
      {dicaAberta && (
        <div className="space-y-1">
          <label htmlFor={inputId} className="block text-xs font-semibold text-gray-900">
            {DICA_LABEL}
          </label>
          <input
            id={inputId}
            type="text"
            value={dica}
            onChange={(event) => onDicaChange(secao, event.target.value)}
            placeholder={DICA_PLACEHOLDER}
            disabled={regenerando}
            maxLength={DICA_MAX_CHARS}
            className={HINT_INPUT_CLASSES}
          />
        </div>
      )}
      {/* D-14 amber strip (plan 05-02): directly under the action row —
          under the editor when one is open on this section. The strips are
          the phase's ONLY confirmations; the "discarded" text is always
          stacked first, so these are speed bumps, not danger guards. */}
      {stripPendente && !editandoAqui && (
        <ConfirmStrip
          message={REGEN_SOBE_EDICAO_MESSAGE}
          note={REGEN_SOBE_EDICAO_NOTE}
          cancelLabel={MANTER_EDICAO_CTA}
          confirmLabel={REGEN_MESMO_ASSIM_CTA}
          onCancel={onCancelarStripRegen}
          onConfirm={onConfirmarStripRegen}
        />
      )}
      {children}
      {stripPendente && editandoAqui && (
        <ConfirmStrip
          message={REGEN_SOBE_EDICAO_MESSAGE}
          note={REGEN_SOBE_EDICAO_NOTE}
          cancelLabel={MANTER_EDICAO_CTA}
          confirmLabel={REGEN_MESMO_ASSIM_CTA}
          onCancel={onCancelarStripRegen}
          onConfirm={onConfirmarStripRegen}
        />
      )}
      {/* D-09 comparison panel (plan 05-03): under the section content; marks
          recompute against the CURRENTLY displayed text on every render —
          zero fetch (D-10) — and render ONLY here, never in the card body. */}
      {comparacaoAberta && (
        <ComparisonPanel
          secao={secao}
          texto={panelTexto}
          entradas={panelEntradas}
          perfil={perfil}
          idioma={idioma}
        />
      )}
      {versoesAberta && versoes.length > 0 && (
        <SectionVersionsPanel
          secao={secao}
          versoes={versoes}
          restaurarDesabilitado={locksEdicao}
          onRestaurar={onRestaurar}
        />
      )}
      {pending && (
        <p className="text-sm text-gray-600">{REGEN_INFLIGHT_LINE.replace('{secao}', label)}</p>
      )}
      {erros && (
        <section
          aria-labelledby={`regen-error-title-${secao}`}
          className="rounded-md border border-red-300 bg-red-50 px-4 py-3"
        >
          <h5 id={`regen-error-title-${secao}`} className="font-semibold text-red-700">
            {REGEN_ERROR_TITLE.replace('{secao}', label)}
          </h5>
          {erros.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-sm text-red-700 whitespace-pre-wrap">
              {erros.map((linha, i) => (
                <li key={`${i}-${linha}`}>{linha}</li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-red-600">{REGEN_ERROR_HINT}</p>
        </section>
      )}
    </Section>
  )
}

function ImpactBullets({ impacts, idioma }: { impacts: ImpactDTO[]; idioma: ResumeLanguage }) {
  if (impacts.length === 0) return null
  return (
    <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
      {impacts.map((impact, i) => {
        const context = tLang(impact.context, idioma)
        return (
          <li key={i}>
            {tLang(impact.action, idioma)} —{' '}
            <span className="font-medium">{tLang(impact.metric, idioma)}</span>
            {context && <span className="text-gray-500"> ({context})</span>}
          </li>
        )
      })}
    </ul>
  )
}

/**
 * Generated experience entry (ExperienceEntry visual pattern; plain strings
 * from the backend) + the per-entry "Editar entrada" quiet control (D-12
 * Experiência granularity: bullets one per line — company/title stay fixed).
 * The entry text block also opens the editor on click (redundant pointer
 * affordance; the button is the accessible path).
 */
function ExperienciaGeradaEntry({
  exp,
  onEditar,
  desabilitado,
}: {
  exp: ExperienciaGeradaDTO
  onEditar?: () => void
  desabilitado?: boolean
}) {
  const clicavel = Boolean(onEditar) && !desabilitado
  return (
    <article
      className={clicavel ? 'break-inside-avoid cursor-pointer rounded hover:bg-gray-50' : 'break-inside-avoid'}
      onClick={clicavel ? onEditar : undefined}
    >
      <h5 className="text-sm font-semibold text-gray-900">
        {exp.company}
        {PREVIEW_CONTACT_SEPARATOR}
        {exp.title}
      </h5>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
        {exp.bullets.map((bullet, i) => (
          <li key={i}>{bullet}</li>
        ))}
      </ul>
      {onEditar && (
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation()
            if (!desabilitado) onEditar()
          }}
          disabled={desabilitado}
          className={`mt-1 ${QUIET_BUTTON_CLASSES}`}
        >
          {EDITAR_ENTRADA_CTA}
        </button>
      )}
    </article>
  )
}

interface ResumeResultProps {
  perfil: PerfilDTO
  secoes: SecoesDTO
  idioma: ResumeLanguage
  onRegenerar: () => void
  /** ANY long op pending (full gerar, section regen, export) — the shared lock. */
  regenerando: boolean
  // --- per-section regeneration (plan 05-01, SC1/D-05) ---
  onRegenerarSecao: (secao: SecaoId) => void
  /** The section whose regen is in flight (null = none) — drives the in-flight
   *  line + that button's label swap; displayed text stays fully mounted. */
  secaoRegenerando: SecaoId | null
  /** Per-section last failed regen: backend PT-BR erros[] verbatim, or [] for
   *  a fetch-level failure (generic hint path). Cleared on that section's
   *  next success; never blanks the prior text. */
  regenErros: Partial<Record<SecaoId, string[]>>
  // --- per-section dica UI state (D-05: on-demand steering hint) ---
  dicas: Record<SecaoId, string>
  onDicaChange: (secao: SecaoId, valor: string) => void
  dicaAberta: Record<SecaoId, boolean>
  onDicaToggle: (secao: SecaoId) => void
  // --- D-14 confirm strips (plan 05-02 Task 3) ---
  /** Section whose regen-over-edit strip is pending (null = none). */
  stripRegen: SecaoId | null
  onConfirmarStripRegen: (secao: SecaoId) => void
  onCancelarStripRegen: () => void
  /** Full-regen-with-edits strip under the card header. */
  stripGerarCompleta: boolean
  onConfirmarGerarCompleta: () => void
  onCancelarGerarCompleta: () => void
  // --- per-section version stack (plan 05-02, D-08) ---
  /** Prior versions per section, newest first (session memory only). */
  versoes: Record<SecaoId, SectionVersion[]>
  /** Per-section Versoes disclosure state. */
  versoesAbertas: Record<SecaoId, boolean>
  onVersoesToggle: (secao: SecaoId) => void
  /** Restore = stack current FIRST, then mount the chosen version (D-08). */
  onRestaurar: (secao: SecaoId, indice: number) => void
  // --- inline editing (plan 05-02, D-02/D-04/D-12) ---
  /** Badge origin per generated section: 'gerado' at mount/regen, 'editado'
   *  after a save or an editado-origem restore. */
  origens: Record<SecaoId, OrigemBadge>
  /** The ONE open editor (null = none) — replaces that section's content. */
  editor: SecaoEditorState | null
  /** Derived lock: an editor is open (any section) OR a long op is pending —
   *  disables every edit affordance (one editor at a time, UI-SPEC). */
  locksEdicao: boolean
  onAbrirEditor: (secao: SecaoId, entryIdx?: number) => void
  onDraftChange: (valor: string) => void
  onSalvarEdicao: () => void
  /** Clean cancel + close. The DIRTY-cancel strip's confirmed path goes to
   *  onDescartarEdicao, which stacks the draft before closing (WR-02). */
  onCancelarEdicao: () => void
  onDescartarEdicao: () => void
}

/**
 * Zone 4 — the assembled resume card (D-05): the 3 generated sections badged
 * "Gerado" (resumo, experiências, habilidades — always rendered; the backend
 * envelope is all-or-nothing) + passthrough perfil sections badged "Do
 * perfil" in ProfilePreview section order, with the name/contact header. The
 * permanent D-02 edit-policy line renders directly under the card header
 * (text-xs text-gray-600, ⚠ aria-hidden) whenever a result is mounted — the
 * ephemeral edit contract is explicit in the UI at all times (SC4). The
 * neutral ephemeral notice (D-06) stays directly ABOVE the card.
 *
 * "Gerar novamente" re-runs with current inputs and replaces the ephemeral
 * result (Phase 3 contract; the D-14 edited-state confirm lands in Task 3).
 * Generated sections carry the Phase 5 action row: "Editar seção" (Experiência
 * gets per-entry "Editar entrada" instead), "Comparar com o perfil" (05-03 —
 * opens the read-only ComparisonPanel; suspect marks never render in this
 * card body, SC2), "Adicionar dica" + "Regenerar
 * seção" (05-01). Editing (D-12) replaces the section's content with the
 * SectionEditor textarea; save flips that badge to "Editado" (state handled
 * in CurriculoHome). Passthrough sections get NO new controls (D-13). ALL
 * content (LLM output, edited text included) renders exclusively as JSX text
 * children — no raw-HTML injection path (T-01-08 posture inherited from
 * ProfilePreview).
 */
export function ResumeResult({
  perfil,
  secoes,
  idioma,
  onRegenerar,
  regenerando,
  onRegenerarSecao,
  secaoRegenerando,
  regenErros,
  dicas,
  onDicaChange,
  stripRegen,
  onConfirmarStripRegen,
  onCancelarStripRegen,
  stripGerarCompleta,
  onConfirmarGerarCompleta,
  onCancelarGerarCompleta,
  dicaAberta,
  onDicaToggle,
  versoes,
  versoesAbertas,
  onVersoesToggle,
  onRestaurar,
  origens,
  editor,
  locksEdicao,
  onAbrirEditor,
  onDraftChange,
  onSalvarEdicao,
  onCancelarEdicao,
  onDescartarEdicao,
}: ResumeResultProps) {
  const headings = CURRICULO_GENERATED_SECTIONS[idioma]
  const contactLine = [
    perfil.contact.email,
    perfil.contact.location,
    perfil.contact.phone,
    perfil.contact.linkedin,
  ]
    .filter(Boolean)
    .join(PREVIEW_CONTACT_SEPARATOR)

  return (
    <div className="space-y-4">
      <div
        role="status"
        className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700"
      >
        <span aria-hidden>⚠</span> {CURRICULO_EPHEMERAL_NOTICE}
      </div>

      <article aria-labelledby="resume-result-title" className={CARD_CLASSES}>
        <header>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 id="resume-result-title" className="text-base font-semibold text-gray-900">
              {CURRICULO_RESULT_TITLE}
            </h3>
            <button
              type="button"
              onClick={onRegenerar}
              disabled={locksEdicao}
              className={SECONDARY_BUTTON_CLASSES}
            >
              {CURRICULO_REGENERAR}
            </button>
          </div>
          <div className="mt-3 flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <p className="text-2xl font-bold text-gray-900">{perfil.name}</p>
            <Badge kind="perfil" />
          </div>
          {contactLine && <p className="mt-1 text-sm text-gray-600">{contactLine}</p>}
        </header>

        {/* D-02 permanent edit-policy line — always visible while a result is
            mounted; the only permanent notice (it is NOT a second gray bordered
            block competing with the ephemeral notice above the card). */}
        <p className="mt-2 text-xs text-gray-600">
          <span aria-hidden>⚠</span> {POLICY_EDICAO}
        </p>
        {/* D-14 full-regen-with-edits strip (plan 05-02): the once-per-action
            ask when any section carries edits — inline, never a dialog. */}
        {stripGerarCompleta && (
          <div className="mt-2">
            <ConfirmStrip
              message={GERAR_COM_EDICOES_MESSAGE}
              cancelLabel={MANTER_EDICOES_CTA}
              confirmLabel={GERAR_MESMO_ASSIM_CTA}
              onCancel={onCancelarGerarCompleta}
              onConfirm={onConfirmarGerarCompleta}
            />
          </div>
        )}

        <div className="mt-4 space-y-5">
          <GeneratedSection
            title={headings.resumo}
            secao="resumo"
            badge={origens.resumo}
            perfil={perfil}
            idioma={idioma}
            panelTexto={secoes.resumo}
            panelEntradas={null}
            editandoAqui={editor?.secao === 'resumo'}
            onEditarSecao={() => onAbrirEditor('resumo')}
            locksEdicao={locksEdicao}
            stripPendente={stripRegen === 'resumo'}
            onConfirmarStripRegen={() => onConfirmarStripRegen('resumo')}
            onCancelarStripRegen={onCancelarStripRegen}
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.resumo}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.resumo}
            onDicaToggle={onDicaToggle}
            versoes={versoes.resumo}
            versoesAberta={versoesAbertas.resumo}
            onVersoesToggle={() => onVersoesToggle('resumo')}
            onRestaurar={(indice) => onRestaurar('resumo', indice)}
          >
            {editor?.secao === 'resumo' ? (
              <SectionEditor
                secao="resumo"
                draft={editor.draft}
                dirty={editor.draft !== editor.inicial}
                canSave={textoEditorValido('resumo', editor.draft)}
                locked={regenerando}
                onDraftChange={onDraftChange}
                onSave={onSalvarEdicao}
                onCancel={onCancelarEdicao}
                onDescartar={onDescartarEdicao}
              />
            ) : (
              <div
                className="cursor-pointer rounded hover:bg-gray-50"
                onClick={() => {
                  if (!locksEdicao) onAbrirEditor('resumo')
                }}
              >
                <p className="text-sm text-gray-700">{secoes.resumo}</p>
              </div>
            )}
          </GeneratedSection>

          <GeneratedSection
            title={headings.experiencias}
            secao="experiencias"
            badge={origens.experiencias}
            perfil={perfil}
            idioma={idioma}
            panelTexto={secoes.experiencias.map((exp) => exp.bullets.join('\n')).join('\n\n')}
            panelEntradas={secoes.experiencias}
            editandoAqui={editor?.secao === 'experiencias'}
            onEditarSecao={null}
            locksEdicao={locksEdicao}
            stripPendente={stripRegen === 'experiencias'}
            onConfirmarStripRegen={() => onConfirmarStripRegen('experiencias')}
            onCancelarStripRegen={onCancelarStripRegen}
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.experiencias}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.experiencias}
            onDicaToggle={onDicaToggle}
            versoes={versoes.experiencias}
            versoesAberta={versoesAbertas.experiencias}
            onVersoesToggle={() => onVersoesToggle('experiencias')}
            onRestaurar={(indice) => onRestaurar('experiencias', indice)}
          >
            {editor?.secao === 'experiencias' ? (
              <SectionEditor
                secao="experiencias"
                draft={editor.draft}
                dirty={editor.draft !== editor.inicial}
                canSave={textoEditorValido('experiencias', editor.draft)}
                locked={regenerando}
                onDraftChange={onDraftChange}
                onSave={onSalvarEdicao}
                onCancel={onCancelarEdicao}
                onDescartar={onDescartarEdicao}
              />
            ) : (
              secoes.experiencias.map((exp, i) => (
                <ExperienciaGeradaEntry
                  key={`${i}-${exp.company}`}
                  exp={exp}
                  desabilitado={locksEdicao}
                  onEditar={() => onAbrirEditor('experiencias', i)}
                />
              ))
            )}
          </GeneratedSection>

          {perfil.education.length > 0 && (
            <Section title={PREVIEW_SECTIONS.formacao} badge="perfil">
              {perfil.education.map((ed, i) => (
                <article key={`${i}-${ed.institution}`} className="break-inside-avoid">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                    <h5 className="text-sm font-semibold text-gray-900">
                      {ed.degree}
                      {PREVIEW_CONTACT_SEPARATOR}
                      {ed.institution}
                    </h5>
                    {(ed.start_date || ed.end_date) && (
                      <p className="text-xs text-gray-500">
                        {/* IN-03: start_date is optional — with only an end
                            present, render just the end (never a malformed
                            " – 2019" from an empty start placeholder). */}
                        {ed.start_date
                          ? dateRange(ed.start_date, ed.end_date)
                          : (ed.end_date ?? '')}
                      </p>
                    )}
                  </div>
                </article>
              ))}
            </Section>
          )}

          <GeneratedSection
            title={headings.habilidades}
            secao="habilidades"
            badge={origens.habilidades}
            perfil={perfil}
            idioma={idioma}
            panelTexto={secoes.habilidades.join(', ')}
            panelEntradas={null}
            editandoAqui={editor?.secao === 'habilidades'}
            onEditarSecao={() => onAbrirEditor('habilidades')}
            locksEdicao={locksEdicao}
            stripPendente={stripRegen === 'habilidades'}
            onConfirmarStripRegen={() => onConfirmarStripRegen('habilidades')}
            onCancelarStripRegen={onCancelarStripRegen}
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.habilidades}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.habilidades}
            onDicaToggle={onDicaToggle}
            versoes={versoes.habilidades}
            versoesAberta={versoesAbertas.habilidades}
            onVersoesToggle={() => onVersoesToggle('habilidades')}
            onRestaurar={(indice) => onRestaurar('habilidades', indice)}
          >
            {editor?.secao === 'habilidades' ? (
              <SectionEditor
                secao="habilidades"
                draft={editor.draft}
                dirty={editor.draft !== editor.inicial}
                canSave={textoEditorValido('habilidades', editor.draft)}
                locked={regenerando}
                onDraftChange={onDraftChange}
                onSave={onSalvarEdicao}
                onCancel={onCancelarEdicao}
                onDescartar={onDescartarEdicao}
              />
            ) : (
              <div
                className="cursor-pointer rounded hover:bg-gray-50"
                onClick={() => {
                  if (!locksEdicao) onAbrirEditor('habilidades')
                }}
              >
                <p className="text-sm text-gray-700">{secoes.habilidades.join(', ')}</p>
              </div>
            )}
          </GeneratedSection>

          {perfil.certifications.length > 0 && (
            <Section title={PREVIEW_SECTIONS.certificacoes} badge="perfil">
              {perfil.certifications.map((cert, i) => (
                <p key={`${i}-${cert.name}`} className="text-sm text-gray-700">
                  <span className="font-medium">{cert.name}</span>
                  {cert.issuer && ` — ${cert.issuer}`}
                  {cert.year && ` (${cert.year})`}
                </p>
              ))}
            </Section>
          )}

          {perfil.languages.length > 0 && (
            <Section title={PREVIEW_SECTIONS.idiomas} badge="perfil">
              {perfil.languages.map((lang, i) => (
                <p key={`${i}-${lang.name}`} className="text-sm text-gray-700">
                  <span className="font-medium">{lang.name}</span> — {lang.level}
                </p>
              ))}
            </Section>
          )}

          {perfil.projects.length > 0 && (
            <Section title={PREVIEW_SECTIONS.projetos} badge="perfil">
              {perfil.projects.map((proj, i) => (
                <article key={`${i}-${proj.name}`} className="break-inside-avoid">
                  <h5 className="text-sm font-semibold text-gray-900">{proj.name}</h5>
                  <p className="mt-1 text-sm text-gray-700">{tLang(proj.description, idioma)}</p>
                  {proj.technologies.length > 0 && (
                    <p className="mt-1 text-xs text-gray-500">
                      {proj.technologies.join(PREVIEW_CONTACT_SEPARATOR)}
                    </p>
                  )}
                  <ImpactBullets impacts={proj.impacts} idioma={idioma} />
                </article>
              ))}
            </Section>
          )}
        </div>
      </article>
    </div>
  )
}
