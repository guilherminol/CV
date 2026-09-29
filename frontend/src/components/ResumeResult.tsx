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
  HINT_INPUT_CLASSES,
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
} from '../constants/ui'
import { SectionEditor, textoEditorValido, type SecaoEditorState } from './SectionEditor'

// Pinned UI-SPEC class strings (Component conventions, plan 03-04).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white px-6 py-5 shadow-sm'
const SECONDARY_BUTTON_CLASSES =
  'min-h-10 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'

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

/** Badge origin for GENERATED sections (D-04): 'editado' after an inline
 *  save or the restore of an edited version; 'gerado' at mount/regen. */
export type OrigemBadge = 'gerado' | 'editado'

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
 * A generated section with the Phase 5 action row (D-05 + plan 05-02 D-12):
 * "Editar seção" (quiet; hidden for Experiência — its per-entry
 * "Editar entrada" controls live on each entry article) + "Adicionar dica" +
 * "Regenerar seção" (05-01). Editing replaces the section's content with the
 * SectionEditor textarea (D-12 — no modal, no separate view); the
 * section-level text block also responds to click as a redundant pointer
 * affordance (the button is the accessible affordance). One editor at a time:
 * while ANY editor is open (or a long op is pending) the edit control
 * disables (locksEdicao). In-flight/error behavior unchanged from 05-01.
 * No comparison/version controls here yet — Task 2/3 of 05-02 and 05-03 own
 * those.
 */
function GeneratedSection({
  title,
  secao,
  children,
  badge,
  onEditarSecao,
  locksEdicao,
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
  /** Section-level edit control; null for Experiência (per-entry controls). */
  onEditarSecao: (() => void) | null
  /** An editor is open (any section) OR a long op is pending. */
  locksEdicao: boolean
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
            className={HINT_INPUT_CLASSES}
          />
        </div>
      )}
      {children}
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
  onCancelarEdicao: () => void
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
 * gets per-entry "Editar entrada" instead), "Adicionar dica" + "Regenerar
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
  dicaAberta,
  onDicaToggle,
  origens,
  editor,
  locksEdicao,
  onAbrirEditor,
  onDraftChange,
  onSalvarEdicao,
  onCancelarEdicao,
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
              disabled={regenerando}
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

        <div className="mt-4 space-y-5">
          <GeneratedSection
            title={headings.resumo}
            secao="resumo"
            badge={origens.resumo}
            onEditarSecao={() => onAbrirEditor('resumo')}
            locksEdicao={locksEdicao}
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.resumo}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.resumo}
            onDicaToggle={onDicaToggle}
          >
            {editor?.secao === 'resumo' ? (
              <SectionEditor
                secao="resumo"
                draft={editor.draft}
                dirty={editor.draft !== editor.inicial}
                canSave={textoEditorValido('resumo', editor.draft)}
                onDraftChange={onDraftChange}
                onSave={onSalvarEdicao}
                onCancel={onCancelarEdicao}
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
            onEditarSecao={null}
            locksEdicao={locksEdicao}
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.experiencias}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.experiencias}
            onDicaToggle={onDicaToggle}
          >
            {editor?.secao === 'experiencias' ? (
              <SectionEditor
                secao="experiencias"
                draft={editor.draft}
                dirty={editor.draft !== editor.inicial}
                canSave={textoEditorValido('experiencias', editor.draft)}
                onDraftChange={onDraftChange}
                onSave={onSalvarEdicao}
                onCancel={onCancelarEdicao}
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
                        {dateRange(ed.start_date ?? '', ed.end_date)}
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
            onEditarSecao={() => onAbrirEditor('habilidades')}
            locksEdicao={locksEdicao}
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.habilidades}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.habilidades}
            onDicaToggle={onDicaToggle}
          >
            {editor?.secao === 'habilidades' ? (
              <SectionEditor
                secao="habilidades"
                draft={editor.draft}
                dirty={editor.draft !== editor.inicial}
                canSave={textoEditorValido('habilidades', editor.draft)}
                onDraftChange={onDraftChange}
                onSave={onSalvarEdicao}
                onCancel={onCancelarEdicao}
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
