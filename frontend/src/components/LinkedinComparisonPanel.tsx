import type { ReactNode } from 'react'
import type {
  ExperienceDTO,
  ImpactDTO,
  LinkedinExperienciaEntryDTO,
  LinkedinSecaoId,
  LocalizedText,
  PerfilDTO,
  ResumeLanguage,
} from '../api/client'
import {
  COMPARACAO_FALLBACK_NOTA,
  COMPARACAO_HEADER_FATOS,
  COMPARACAO_MARK_SR_ONLY,
  COMPARACAO_PANEL_LABEL,
  COMPARACAO_ZERO_SUSPEITOS,
  LINKEDIN_COMPARACAO_HEADER_TEXTO,
  LINKEDIN_COMPARACAO_LEGENDA,
  PREVIEW_CONTACT_SEPARATOR,
} from '../constants/ui'
import { fold, segmentText, suspectTokens } from '../lib/comparison'

// Pinned UI-SPEC class strings (Component conventions, plan 05-03 — reused
// verbatim; amber is reserved EXCLUSIVELY for mechanical suspicion inside
// this panel, never in the card body).
const PANEL_CLASSES = 'mt-3 rounded-md border border-gray-200 bg-gray-50 px-4 py-3'
const PANEL_GRID_CLASSES = 'mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2'
const PANEL_HEADER_CLASSES = 'text-xs font-semibold uppercase tracking-wide text-gray-500'
const MARK_CLASSES =
  'rounded-sm bg-amber-100 text-amber-900 underline decoration-dotted decoration-amber-600 underline-offset-2'

/**
 * Run-language display resolver — mirrored from ComparisonPanel (its private
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
 *  impact lines (action — metric (context)). */
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
 * The profile-derived inventory (plan 05-03 Task 2 port): skill items,
 * project technologies, certification names, companies, institutions, job
 * titles — extracted FROM the profile, so entity/tech checks are always
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
 * Source-facts blob for headline/sobre: the WHOLE profile facts — a headline
 * or an About section legitimately synthesizes the entire profile (the
 * 05-RESEARCH §Pattern 3 scope precedent for the resume summary), so numerals
 * are checked against all of it. The FACTS COLUMN still shows the profile
 * summary (UI-SPEC facts mapping) — the blob is the grounding corpus only.
 */
function fatosDoPerfilInteiro(perfil: PerfilDTO, idioma: ResumeLanguage): string {
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
 *  + impacts rendered like the card's impact lines). */
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

interface LinkedinComparisonPanelProps {
  bloco: LinkedinSecaoId
  /** The block's CURRENTLY displayed text (headline/sobre whole string;
   *  habilidades the skills joined one per line) — marks recompute against it
   *  on every render, zero fetch (D-10). Unused for experiências. */
  texto: string
  /** Experiência only: the displayed generated entries (per-entry alignment
   *  against the profile — 06-02 index-aligned to profile order). */
  entradas: LinkedinExperienciaEntryDTO[] | null
  perfil: PerfilDTO
  idioma: ResumeLanguage
}

/**
 * The LinkedIn fact-vs-generated comparison panel (plan 06-03 — the Phase 5
 * D-09/D-10/D-11 pattern on LinkedIn blocks): "Fatos do perfil" left, the
 * CURRENTLY displayed text right under the adapted `Texto no LinkedIn`
 * header, in a two-column grid that stacks under sm (never horizontal
 * scroll). Facts column per the UI-SPEC mapping: headline/sobre → the
 * profile summary; experiências → the matching entry's description + impacts
 * (company fold-match, ALL-entries fallback + the neutral note when pairing
 * fell back); habilidades → profile skills grouped under category sublabels
 * as PLAIN TEXT (never chips — chips would fake a covered/absent verdict on
 * profile facts). The comparison.ts fold/numeral mechanics are reused AS-IS
 * — LinkedIn blocks feed them the same shape. Deterministic amber <mark>
 * highlights only render here, never in the card body. Read-only — stays
 * usable while long ops run (UI-SPEC locking matrix). Legend adapted to this
 * phase's deliverable ("Confira você mesmo antes de copiar."); at zero marks
 * the loud zero line replaces it — never a silently unmarked panel.
 */
export function LinkedinComparisonPanel({
  bloco,
  texto,
  entradas,
  perfil,
  idioma,
}: LinkedinComparisonPanelProps) {
  const inventario = inventarioDoPerfil(perfil, idioma)

  let fatos: ReactNode
  let textoAtual: ReactNode
  let totalMarcas = 0

  if (bloco === 'experiencias') {
    // Per-entry alignment: each generated entry is fold-matched to the profile
    // entry by company (comparison.ts fold both sides — Pitfall 8). Source
    // facts are strict per-entry (description + impacts); when ANY pairing
    // fails, the fallback scope is ALL profile entries under the neutral note
    // — never an empty facts column (UI-SPEC all-entries fallback note).
    const comparadas = (entradas ?? []).map((entrada) => {
      const alvo =
        perfil.experiences.find((exp) => fold(exp.company) === fold(entrada.company)) ?? null
      return {
        entrada,
        alvo,
        suspects: suspectTokens(
          entrada.descricao,
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
            <p className="mt-1 text-sm text-gray-700">
              <SegmentedText texto={item.entrada.descricao} suspects={item.suspects} />
            </p>
          </article>
        ))}
      </div>
    )
    totalMarcas = comparadas.reduce(
      (total, item) => total + contarMarcas(item.entrada.descricao, item.suspects),
      0,
    )
  } else if (bloco === 'habilidades') {
    // Facts grouped under category sublabels as plain text — never chips.
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
    // headline / sobre — facts column is the profile summary in the run
    // language; suspects are grounded against the WHOLE profile facts (a
    // headline/About legitimately synthesizes the entire profile).
    const suspects = suspectTokens(texto, fatosDoPerfilInteiro(perfil, idioma), inventario)
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
          <h5 className={PANEL_HEADER_CLASSES}>{LINKEDIN_COMPARACAO_HEADER_TEXTO}</h5>
          {textoAtual}
        </div>
      </div>
      {/* D-11: the legend is MANDATORY whenever any mark exists; at zero marks
          the loud zero line replaces it — never a silently unmarked panel. */}
      <p className="mt-3 text-xs text-gray-500">
        {totalMarcas > 0 ? LINKEDIN_COMPARACAO_LEGENDA : COMPARACAO_ZERO_SUSPEITOS}
      </p>
    </section>
  )
}
