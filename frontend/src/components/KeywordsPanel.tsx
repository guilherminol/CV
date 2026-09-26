import type { CoberturaItemDTO, KeywordDTO, ResumeLanguage } from '../api/client'
import {
  CATEGORY_LABELS,
  CATEGORY_ORDER,
  CURRICULO_COBERTURA_PLURAL,
  CURRICULO_COBERTURA_SINGULAR,
  CURRICULO_KEYWORDS_EMPTY,
  CURRICULO_KEYWORDS_TITLE,
  CURRICULO_KEYWORD_AUSENTE,
  CURRICULO_KEYWORD_COBERTO,
} from '../constants/ui'

interface KeywordsPanelProps {
  keywords: KeywordDTO[]
  cobertura: CoberturaItemDTO[]
  cobertura_resumo: { cobertos: number; total: number }
  idioma: ResumeLanguage
}

/**
 * Pure copy picker (UI-SPEC zero-one-many row): the plain factual tally line —
 * singular "1 de 1 keyword … aparece" vs plural "{n} de {m} keywords … aparecem".
 * NEVER a percentage, score, or progress meter (RESUME-04; REQUIREMENTS Out of
 * Scope). Unit-testable offline by design (no-new-deps contract).
 */
export function resumoCoberturaCopy(cobertos: number, total: number): string {
  const template = total === 1 ? CURRICULO_COBERTURA_SINGULAR : CURRICULO_COBERTURA_PLURAL
  return template.replace('{covered}', String(cobertos)).replace('{total}', String(total))
}

/** D-02 run-language display text: pt for pt-BR runs, en for EN runs, canonical fallback. */
function keywordDisplay(
  kw: KeywordDTO | undefined,
  canonical: string,
  idioma: ResumeLanguage,
): string {
  if (!kw) return canonical
  const primary = idioma === 'pt-BR' ? kw.pt : kw.en
  return primary ?? canonical
}

/**
 * Zone 5 — one honest keywords + coverage panel (RESUME-02 + RESUME-04).
 * Chips group by the fixed CATEGORY_ORDER, empty categories hidden, flex-wrap
 * only (panel grows vertically — never horizontal scroll, never a table).
 * Chip status is a ✓/○ glyph (aria-hidden) ALWAYS paired with a visually
 * hidden text label — never glyph or color alone. Text-only render.
 */
export function KeywordsPanel({ keywords, cobertura, cobertura_resumo, idioma }: KeywordsPanelProps) {
  const byCanonical = new Map(keywords.map((kw) => [kw.canonical, kw]))

  return (
    <section aria-labelledby="keywords-panel-title">
      <h3 id="keywords-panel-title" className="text-base font-semibold text-gray-900">
        {CURRICULO_KEYWORDS_TITLE}
      </h3>

      {keywords.length === 0 ? (
        <p className="mt-2 text-sm text-gray-700">{CURRICULO_KEYWORDS_EMPTY}</p>
      ) : (
        <>
          <p className="mt-2 text-sm text-gray-700">
            {resumoCoberturaCopy(cobertura_resumo.cobertos, cobertura_resumo.total)}
          </p>
          <div className="mt-4 space-y-3">
            {CATEGORY_ORDER.map((category) => {
              const items = cobertura.filter((item) => item.category === category)
              if (items.length === 0) return null // empty categories stay hidden
              return (
                <div key={category}>
                  <h4 className="text-xs text-gray-500">{CATEGORY_LABELS[category]}</h4>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {items.map((item, i) => {
                      const coberto = item.status === 'coberto'
                      return (
                        <li
                          key={`${i}-${item.canonical}`}
                          className={
                            coberto
                              ? 'rounded-full border border-green-200 bg-green-50 px-2 py-1 text-xs text-green-700'
                              : 'rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-500'
                          }
                        >
                          <span aria-hidden>{coberto ? '✓' : '○'}</span>{' '}
                          {keywordDisplay(byCanonical.get(item.canonical), item.canonical, idioma)}
                          <span className="sr-only">
                            {coberto ? CURRICULO_KEYWORD_COBERTO : CURRICULO_KEYWORD_AUSENTE}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              )
            })}
          </div>
        </>
      )}
    </section>
  )
}
