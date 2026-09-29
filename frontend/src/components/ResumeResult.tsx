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
  BADGE_GERADO,
  COMPACT_SECONDARY_BUTTON_CLASSES,
  CURRICULO_EPHEMERAL_NOTICE,
  CURRICULO_GENERATED_SECTIONS,
  CURRICULO_REGENERAR,
  CURRICULO_RESULT_TITLE,
  DICA_LABEL,
  DICA_PLACEHOLDER,
  DICA_TOGGLE_ADD,
  DICA_TOGGLE_HIDE,
  HINT_INPUT_CLASSES,
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

type BadgeKind = 'gerado' | 'perfil'

/** D-05 badges: Gerado (accent — this phase's product) vs Do perfil (muted). */
function Badge({ kind }: { kind: BadgeKind }) {
  return (
    <span
      className={
        kind === 'gerado'
          ? 'normal-case rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700'
          : 'normal-case rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-xs font-semibold text-gray-500'
      }
    >
      {kind === 'gerado' ? BADGE_GERADO : BADGE_DO_PERFIL}
    </span>
  )
}

/** ProfilePreview Section pattern (bordered uppercase heading) + a D-05 badge. */
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
 * A generated section with the Phase 5 action row (plan 05-01, D-05/D-07):
 * "Adicionar dica" — the ALWAYS-visible quiet toggle that reveals the labeled
 * one-line hint input on demand — plus "Regenerar seção" (compact secondary;
 * one stage per call). In flight: this section's controls disable, the button
 * label swaps to "Regenerando {seção}…", and the sibling-reassurance line
 * renders (the card sits inside CurriculoHome's shared aria-live region) —
 * the displayed text stays fully mounted, never blanked. A failed regen
 * renders the section-scoped red panel (ErrorPanel structure + classes
 * verbatim) with the backend erros[] lines VERBATIM plus the retry hint;
 * shown only for this section's last failed attempt (cleared on its next
 * success) — prior text stays mounted. No editor/comparison/version controls
 * here — 05-02 and 05-03 own those.
 */
function GeneratedSection({
  title,
  secao,
  children,
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
    <Section title={title} badge="gerado">
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
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

/** Generated experience entry (ExperienceEntry visual pattern; plain strings from the backend). */
function ExperienciaGeradaEntry({ exp }: { exp: ExperienciaGeradaDTO }) {
  return (
    <article className="break-inside-avoid">
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
}

/**
 * Zone 4 — the assembled resume card (D-05): the 3 generated sections badged
 * "Gerado" (resumo, experiências, habilidades — always rendered; the backend
 * envelope is all-or-nothing) + passthrough perfil sections badged "Do perfil"
 * in ProfilePreview section order, with the name/contact header. Zero-entry
 * passthrough sections stay hidden (ProfilePreview convention). The neutral
 * ephemeral notice (D-06) renders directly ABOVE the card with role="status".
 * "Gerar novamente" re-runs with current inputs and replaces the ephemeral
 * result without confirmation (copy contract: no destructive confirmations).
 * Generated sections carry the Phase 5 action row — "Adicionar dica" (always
 * visible on-demand hint toggle, D-05) + "Regenerar seção" (one stage per
 * call; in-flight label swap + sibling reassurance line; a failure renders a
 * section-scoped red panel with backend lines verbatim and the prior text
 * still mounted — failure never blanks). Passthrough sections get NO new
 * controls. ALL content (LLM output included) renders exclusively as JSX text
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

        <div className="mt-4 space-y-5">
          <GeneratedSection
            title={headings.resumo}
            secao="resumo"
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.resumo}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.resumo}
            onDicaToggle={onDicaToggle}
          >
            <p className="text-sm text-gray-700">{secoes.resumo}</p>
          </GeneratedSection>

          <GeneratedSection
            title={headings.experiencias}
            secao="experiencias"
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.experiencias}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.experiencias}
            onDicaToggle={onDicaToggle}
          >
            {secoes.experiencias.map((exp, i) => (
              <ExperienciaGeradaEntry key={`${i}-${exp.company}`} exp={exp} />
            ))}
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
            onRegenerarSecao={onRegenerarSecao}
            secaoRegenerando={secaoRegenerando}
            regenerando={regenerando}
            regenErros={regenErros}
            dica={dicas.habilidades}
            onDicaChange={onDicaChange}
            dicaAberta={dicaAberta.habilidades}
            onDicaToggle={onDicaToggle}
          >
            <p className="text-sm text-gray-700">{secoes.habilidades.join(', ')}</p>
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
