import type { ExperienceDTO, ImpactDTO, LocalizedText, PerfilDTO } from '../api/client'
import {
  PREVIEW_CONTACT_SEPARATOR,
  PREVIEW_PRESENT,
  PREVIEW_SECTIONS,
  PREVIEW_TITLE,
} from '../constants/ui'

/**
 * D-04 display convention: every localized map renders its pt-BR value (the
 * declared base language). The fallback to any other available value is
 * purely defensive — the schema already requires pt-BR to be present.
 * `str | LocalizedText` union fields (project names) pass through as-is.
 */
function t(map: LocalizedText | string | null | undefined): string {
  if (!map) return ''
  if (typeof map === 'string') return map
  return map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
}

/** Group labels for Project.scope — preview is the PT-BR Perfil view. */
const SCOPE_LABELS: Record<'profissional' | 'pessoal', string> = {
  profissional: 'Projetos profissionais',
  pessoal: 'Projetos pessoais',
}

/** Single-value date fields render as-is (D-02); open ranges show "atual". */
function dateRange(start: string, end: string | null | undefined): string {
  return end ? `${start} – ${end}` : `${start} – ${PREVIEW_PRESENT}`
}

function ImpactBullets({ impacts }: { impacts: ImpactDTO[] }) {
  if (impacts.length === 0) return null
  return (
    <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
      {impacts.map((impact, i) => {
        const context = t(impact.context)
        return (
          <li key={i}>
            {t(impact.action)} — <span className="font-medium">{t(impact.metric)}</span>
            {context && <span className="text-gray-500"> ({context})</span>}
          </li>
        )
      })}
    </ul>
  )
}

function ExperienceEntry({ exp }: { exp: ExperienceDTO }) {
  return (
    <article className="break-inside-avoid">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <h4 className="text-sm font-semibold text-gray-900">
          {exp.company}
          {PREVIEW_CONTACT_SEPARATOR}
          {t(exp.title)}
        </h4>
        <p className="text-xs text-gray-500">{dateRange(exp.start_date, exp.end_date)}</p>
      </div>
      {exp.location && <p className="text-xs text-gray-500">{exp.location}</p>}
      <p className="mt-1 text-sm text-gray-700">{t(exp.description)}</p>
      <ImpactBullets impacts={exp.impacts} />
    </article>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="break-inside-avoid">
      <h4 className="border-b border-gray-200 pb-1 text-sm font-bold uppercase tracking-wide text-gray-500">
        {title}
      </h4>
      <div className="mt-2 space-y-3">{children}</div>
    </section>
  )
}

/**
 * Resume-style render of the validated perfil (D-12): the user sees their
 * data exactly the way the app sees it. Text-only — profile strings render
 * exclusively as JSX text children; no raw-HTML injection path (T-01-08).
 */
export function ProfilePreview({ perfil }: { perfil: PerfilDTO }) {
  const contactLine = [
    perfil.contact.email,
    perfil.contact.location && t(perfil.contact.location),
    perfil.contact.phone && t(perfil.contact.phone),
    perfil.contact.linkedin,
  ]
    .filter(Boolean)
    .join(PREVIEW_CONTACT_SEPARATOR)

  return (
    <article
      aria-labelledby="preview-title"
      className="rounded-md border border-gray-200 bg-white px-6 py-5 shadow-sm"
    >
      <header>
        <h3 id="preview-title" className="text-base font-semibold text-gray-900">
          {PREVIEW_TITLE}
        </h3>
        <p className="mt-2 text-2xl font-bold text-gray-900">{perfil.name}</p>
        {contactLine && <p className="mt-1 text-sm text-gray-600">{contactLine}</p>}
      </header>

      <div className="mt-4 space-y-5">
        <Section title={PREVIEW_SECTIONS.resumo}>
          <p className="text-sm text-gray-700">{t(perfil.summary)}</p>
        </Section>

        {perfil.experiences.length > 0 && (
          <Section title={PREVIEW_SECTIONS.experiencia}>
            {perfil.experiences.map((exp, i) => (
              <ExperienceEntry key={`${i}-${exp.company}`} exp={exp} />
            ))}
          </Section>
        )}

        {perfil.education.length > 0 && (
          <Section title={PREVIEW_SECTIONS.formacao}>
            {perfil.education.map((ed, i) => (
              <article key={`${i}-${ed.institution}`} className="break-inside-avoid">
                <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                  <h4 className="text-sm font-semibold text-gray-900">
                    {t(ed.degree)}
                    {PREVIEW_CONTACT_SEPARATOR}
                    {ed.institution}
                  </h4>
                  {(ed.start_date || ed.end_date) && (
                    <p className="text-xs text-gray-500">{dateRange(ed.start_date ?? '', ed.end_date)}</p>
                  )}
                </div>
              </article>
            ))}
          </Section>
        )}

        {perfil.skills.length > 0 && (
          <Section title={PREVIEW_SECTIONS.habilidades}>
            {perfil.skills.map((group, i) => (
              <p key={`${i}-${group.category}`} className="text-sm text-gray-700">
                <span className="font-medium">{group.category}:</span> {group.items.join(', ')}
              </p>
            ))}
          </Section>
        )}

        {perfil.certifications.length > 0 && (
          <Section title={PREVIEW_SECTIONS.certificacoes}>
            {perfil.certifications.map((cert, i) => (
              <p key={`${i}-${cert.name}`} className="text-sm text-gray-700">
                <span className="font-medium">{cert.name}</span>
                {cert.issuer && ` — ${t(cert.issuer)}`}
                {cert.year && ` (${cert.year})`}
              </p>
            ))}
          </Section>
        )}

        {perfil.languages.length > 0 && (
          <Section title={PREVIEW_SECTIONS.idiomas}>
            {perfil.languages.map((lang, i) => (
              <p key={`${i}-${t(lang.name)}`} className="text-sm text-gray-700">
                <span className="font-medium">{t(lang.name)}</span> — {t(lang.level)}
              </p>
            ))}
          </Section>
        )}

        {perfil.projects.length > 0 && (
          <Section title={PREVIEW_SECTIONS.projetos}>
            {(['profissional', 'pessoal'] as const).map((scope) => {
              const group = perfil.projects.filter((proj) => proj.scope === scope)
              if (group.length === 0) return null
              return (
                <div key={scope} className={scope === 'pessoal' ? 'mt-4' : ''}>
                  <p className="text-xs font-semibold text-gray-500">{SCOPE_LABELS[scope]}</p>
                  {group.map((proj, i) => (
                    <article key={`${i}-${t(proj.name)}`} className="break-inside-avoid">
                      <h4 className="text-sm font-semibold text-gray-900">{t(proj.name)}</h4>
                      <p className="mt-1 text-sm text-gray-700">{t(proj.description)}</p>
                      {proj.technologies.length > 0 && (
                        <p className="mt-1 text-xs text-gray-500">{proj.technologies.join(PREVIEW_CONTACT_SEPARATOR)}</p>
                      )}
                      <ImpactBullets impacts={proj.impacts} />
                    </article>
                  ))}
                </div>
              )
            })}
          </Section>
        )}
      </div>
    </article>
  )
}
