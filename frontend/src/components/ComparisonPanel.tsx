import type { ReactNode } from 'react'
import type {
  ExperienciaGeradaDTO,
  ExperienceDTO,
  ImpactDTO,
  LocalizedText,
  PerfilDTO,
  ResumeLanguage,
  SecaoId,
} from '../api/client'
import {
  COMPARACAO_FALLBACK_NOTA,
  COMPARACAO_HEADER_FATOS,
  COMPARACAO_HEADER_TEXTO,
  COMPARACAO_LEGENDA,
  COMPARACAO_MARK_SR_ONLY,
  COMPARACAO_PANEL_LABEL,
  COMPARACAO_ZERO_SUSPEITOS,
  PREVIEW_CONTACT_SEPARATOR,
} from '../constants/ui'
import { fold, segmentText, suspectTokens } from '../lib/comparison'

// Pinned UI-SPEC class strings (Component conventions, plan 05-03). Amber is
// reserved EXCLUSIVELY for mechanical suspicion inside this panel — it never
// appears in the result card body (the card is the export-fidelity preview,
// SC2) and never in chips (chips carry covered/absent semantics).
const PANEL_CLASSES = 'mt-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3'
const PANEL_GRID_CLASSES = 'mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2'
const PANEL_HEADER_CLASSES = 'text-xs font-semibold uppercase tracking-wide text-gray-500'
const MARK_CLASSES =
  'rounded-sm bg-amber-100 text-amber-900 underline decoration-dotted decoration-amber-600 underline-offset-2'

/**
 * Run-language display resolver — mirrored from ResumeResult (its private
 * helpers are not imported across components; SelfCheckPanel precedent).
 */
function tLang(map: LocalizedText | null | undefined, language: ResumeLanguage): string {
  if (!map) return ''
  if (language === 'en') {
    return map.en ?? map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
  }
  return map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
}

/** Plain-string rendering of one impact — the facts-blob mirror of the card's
 *  ImpactBullets line (action — metric (context)). */
function impactoTexto(impact: ImpactDTO, idioma: ResumeLanguage): string {
  const context = tLang(impact.context, idioma)
  return `${tLang(impact.action, idioma)} — ${tLang(impact.metric, idioma)}${context ? ` (${context})` : ''}`
}

/** One profile experience's facts text: description + impacts (run language). */
function textoExperienciaFatos(exp: ExperienceDTO, idioma: ResumeLanguage): string {
  return [
    tLang(exp.description, idioma),
    ...exp.impacts.map((impact) => impactoTexto(impact, idioma)),
  ]
    .filter(Boolean)
    .join('\n')
}

/**
 * The profile-derived inventory (plan 05-03 Task 2): skill items, project
 * technologies, certification names, companies, institutions, job titles —
 * extracted FROM the profile, so entity/tech checks are always
 * profile-derived (D-10).
 */
function inventarioDoPerfil(perfil: PerfilDTO, idioma: ResumeLanguage): string {
  const itens: string[] = []
  for (const grupo of perfil.skills) itens.push(...grupo.items)
  for (const projeto of perfil.projects) itens.push(...projeto.technologies)
  for (const cert of perfil.certifications) itens.push(cert.name)
  for (const exp of perfil.experiences) {
    itens.push(exp.company)
    itens.push(tLang(exp.title, idioma))
  }
  for (const ed of perfil.education) itens.push(ed.institution)
  return itens.filter(Boolean).join('\n')
}

/**
 * Source-facts blob for the resumo section: the WHOLE profile facts (summary,
 * experience descriptions/impacts, skills, project tech/descriptions,
 * certifications) — a summary legitimately synthesizes the entire profile
 * (05-RESEARCH §Pattern 3 scope), so numerals are checked against all of it.
 */
function fatosDoResumo(perfil: PerfilDTO, idioma: ResumeLanguage): string {
  const linhas: string[] = [tLang(perfil.summary, idioma)]
  for (const exp of perfil.experiences) linhas.push(textoExperienciaFatos(exp, idioma))
  for (const grupo of perfil.skills) linhas.push(...grupo.items)
  for (const projeto of perfil.projects) {
    linhas.push(...projeto.technologies)
    linhas.push(tLang(projeto.description, idioma))
  }
  for (const cert of perfil.certifications) linhas.push(cert.name)
  return linhas.filter(Boolean).join('\n')
}

/** Source-facts blob for habilidades: the full profile skill inventory. */
function fatosDasHabilidades(perfil: PerfilDTO): string {
  return [
    ...perfil.skills.flatMap((grupo) => grupo.items),
    ...perfil.projects.flatMap((projeto) => projeto.technologies),
  ]
    .filter(Boolean)
    .join('\n')
}

/** Mark count over one text — drives the legend vs loud-zero line (D-11). */
function contarMarcas(texto: string, suspects: Set<string>): number {
  let total = 0
  for (const segment of segmentText(texto, suspects)) {
    if (segment.suspect) total += 1
  }
  return total
}

/**
 * One segmented text: unmarked text renders as plain JSX children, suspect
 * segments as <mark> with the dual visual cue (amber fill + dotted underline)
 * plus the sr-only suffix — status never conveyed by color alone (UI-SPEC).
 * Segmentation output is DATA rendered as JSX children — never an HTML string
 * (T-05-09 posture).
 */
function SegmentedText({ texto, suspects }: { texto: string; suspects: Set<string> }) {
  return (
    <>
      {segmentText(texto, suspects).map((segment, i) =>
        segment.suspect ? (
          <mark key={i} className={MARK_CLASSES}>
            {segment.text}
            <span className="sr-only">{COMPARACAO_MARK_SR_ONLY}</span>
          </mark>
        ) : (
          <span key={i}>{segment.text}</span>
        ),
      )}
    </>
  )
}

/** Left-column facts for one profile experience (company — title, description
 *  + impacts rendered like the card's ImpactBullets). */
function FatosExperiencia({ exp, idioma }: { exp: ExperienceDTO; idioma: ResumeLanguage }) {
  return (
    <article>
      <h6 className="text-sm font-semibold text-gray-900">
        {exp.company}
        {PREVIEW_CONTACT_SEPARATOR}
        {tLang(exp.title, idioma)}
      </h6>
      <p className="mt-1 text-sm text-gray-700">{tLang(exp.description, idioma)}</p>
      {exp.impacts.length > 0 && (
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
          {exp.impacts.map((impact, i) => {
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
      )}
    </article>
  )
}

interface ComparisonPanelProps {
  secao: SecaoId
  /** The section's CURRENTLY displayed text (from resultado.secoes —
   *  post-edit, post-restore): marks recompute against it on every render,
   *  zero fetch (D-10). */
  texto: string
  /** Experiência only: the displayed generated entries (per-entry alignment
   *  against the profile). */
  entradas: ExperienciaGeradaDTO[] | null
  perfil: PerfilDTO
  idioma: ResumeLanguage
}

/**
 * D-09/D-10/D-11 — the read-only fact-vs-generated comparison panel (plan
 * 05-03): "Fatos do perfil" left, the CURRENTLY displayed text right, in a
 * two-column grid that stacks to one column under sm (never horizontal
 * scroll). Left column per the section scope contract: resumo → the profile
 * summary; experiências → the profile entry fold-matched by company
 * (fallback: ALL profile entries + the neutral note — never an empty panel);
 * habilidades → skill items grouped under their category sublabels as PLAIN
 * text (never chips — chips carry covered/absent verdicts). Suspect spans
 * render ONLY here, never in the card body. Everything computes from the
 * mounted props on every render — zero fetch (D-10), and the panel is
 * read-only so it stays usable while long ops run (UI-SPEC locking matrix).
 */
export function ComparisonPanel({
  secao,
  texto,
  entradas,
  perfil,
  idioma,
}: ComparisonPanelProps) {
  const inventario = inventarioDoPerfil(perfil, idioma)

  let fatos: ReactNode
  let textoAtual: ReactNode
  let totalMarcas = 0

  if (secao === 'experiencias') {
    // Per-entry alignment: each generated entry is fold-matched to the profile
    // entry by company (comparison.ts fold both sides — Pitfall 8). Source
    // facts are strict per-entry (description + impacts); when no entry
    // fold-matches, the fallback scope is ALL profile entries — and the left
    // column renders them under the neutral note (never empty).
    const comparadas = (entradas ?? []).map((entrada) => {
      const alvo =
        perfil.experiences.find((exp) => fold(exp.company) === fold(entrada.company)) ?? null
      return {
        entrada,
        alvo,
        suspects: suspectTokens(
          entrada.bullets.join('\n'),
          alvo
            ? textoExperienciaFatos(alvo, idioma)
            : perfil.experiences
                .map((exp) => textoExperienciaFatos(exp, idioma))
                .join('\n'),
          inventario,
        ),
      }
    })
    const casamentoFalhou = comparadas.some((item) => item.alvo === null)
    fatos = casamentoFalhou ? (
      <div className="space-y-3">
        <p className="text-sm text-gray-600">{COMPARACAO_FALLBACK_NOTA}</p>
        {perfil.experiences.map((exp, i) => (
          <FatosExperiencia key={`${i}-${exp.company}`} exp={exp} idioma={idioma} />
        ))}
      </div>
    ) : (
      <div className="space-y-3">
        {comparadas.map((item, i) =>
          item.alvo ? (
            <FatosExperiencia key={`${i}-${item.alvo.company}`} exp={item.alvo} idioma={idioma} />
          ) : null,
        )}
      </div>
    )
    textoAtual = (
      <div className="space-y-3">
        {comparadas.map((item, i) => (
          <article key={`${i}-${item.entrada.company}`}>
            <h6 className="text-sm font-semibold text-gray-900">
              {item.entrada.company}
              {PREVIEW_CONTACT_SEPARATOR}
              {item.entrada.title}
            </h6>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-gray-700">
              {item.entrada.bullets.map((bullet, j) => (
                <li key={j}>
                  <SegmentedText texto={bullet} suspects={item.suspects} />
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    )
    totalMarcas = comparadas.reduce(
      (total, item) =>
        total +
        item.entrada.bullets.reduce((soma, bullet) => soma + contarMarcas(bullet, item.suspects), 0),
      0,
    )
  } else if (secao === 'habilidades') {
    // Plain text under category sublabels — never chips (they would fake a
    // covered/absent verdict on profile facts).
    const suspects = suspectTokens(texto, fatosDasHabilidades(perfil), inventario)
    totalMarcas = contarMarcas(texto, suspects)
    fatos = (
      <div className="space-y-2">
        {perfil.skills.map((grupo, i) => (
          <div key={`${i}-${grupo.category}`}>
            <h6 className="text-xs text-gray-500">{grupo.category}</h6>
            <p className="text-sm text-gray-700">{grupo.items.join(', ')}</p>
          </div>
        ))}
      </div>
    )
    textoAtual = (
      <p className="text-sm text-gray-700">
        <SegmentedText texto={texto} suspects={suspects} />
      </p>
    )
  } else {
    // resumo — facts column is the profile summary in the run language.
    const suspects = suspectTokens(texto, fatosDoResumo(perfil, idioma), inventario)
    totalMarcas = contarMarcas(texto, suspects)
    fatos = <p className="text-sm text-gray-700">{tLang(perfil.summary, idioma)}</p>
    textoAtual = (
      <p className="text-sm text-gray-700">
        <SegmentedText texto={texto} suspects={suspects} />
      </p>
    )
  }

  return (
    <section aria-label={COMPARACAO_PANEL_LABEL} className={PANEL_CLASSES}>
      <div className={PANEL_GRID_CLASSES}>
        <div>
          <h5 className={PANEL_HEADER_CLASSES}>{COMPARACAO_HEADER_FATOS}</h5>
          {fatos}
        </div>
        <div>
          <h5 className={PANEL_HEADER_CLASSES}>{COMPARACAO_HEADER_TEXTO}</h5>
          {textoAtual}
        </div>
      </div>
      {/* D-11: the legend is MANDATORY whenever any mark exists; at zero marks
          the loud zero line replaces it — never a silently unmarked panel. */}
      <p className="mt-3 text-xs text-gray-500">
        {totalMarcas > 0 ? COMPARACAO_LEGENDA : COMPARACAO_ZERO_SUSPEITOS}
      </p>
    </section>
  )
}
