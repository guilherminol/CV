import type {
  ExperienciaGeradaDTO,
  ImpactDTO,
  LocalizedText,
  PerfilDTO,
  ResumeLanguage,
  SecoesDTO,
} from '../api/client'
import {
  BADGE_DO_PERFIL,
  BADGE_GERADO,
  CURRICULO_EPHEMERAL_NOTICE,
  CURRICULO_GENERATED_SECTIONS,
  CURRICULO_REGENERAR,
  CURRICULO_RESULT_TITLE,
  PREVIEW_CONTACT_SEPARATOR,
  PREVIEW_PRESENT,
  PREVIEW_SECTIONS,
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
  regenerando: boolean
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
 * ALL content (LLM output included) renders exclusively as JSX text children —
 * no raw-HTML injection path (T-01-08 posture inherited from ProfilePreview).
 */
export function ResumeResult({ perfil, secoes, idioma, onRegenerar, regenerando }: ResumeResultProps) {
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
          <Section title={headings.resumo} badge="gerado">
            <p className="text-sm text-gray-700">{secoes.resumo}</p>
          </Section>

          <Section title={headings.experiencias} badge="gerado">
            {secoes.experiencias.map((exp, i) => (
              <ExperienciaGeradaEntry key={`${i}-${exp.company}`} exp={exp} />
            ))}
          </Section>

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

          <Section title={headings.habilidades} badge="gerado">
            <p className="text-sm text-gray-700">{secoes.habilidades.join(', ')}</p>
          </Section>

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
