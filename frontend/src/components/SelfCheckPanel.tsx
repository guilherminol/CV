import type { KeywordDTO, ResumeLanguage, SelfCheckDTO } from '../api/client'
import {
  CATEGORY_LABELS,
  CATEGORY_ORDER,
  SELFCHECK_CONTATO_LABEL,
  SELFCHECK_GATE_FOOTER,
  SELFCHECK_KEYWORDS_ZERO,
  SELFCHECK_KEYWORD_AUSENTE,
  SELFCHECK_KEYWORD_NO_PDF,
  SELFCHECK_ORDEM_LABEL,
  SELFCHECK_ORDEM_LABELS,
  SELFCHECK_SOBREVIVENCIA_LABEL,
  SELFCHECK_SOBREVIVENCIA_PLURAL,
  SELFCHECK_SOBREVIVENCIA_SINGULAR,
  SELFCHECK_TITLE,
} from '../constants/ui'

// Pinned UI-SPEC class strings (Component conventions, plan 04-03).
const GREEN_CHIP_CLASSES =
  'rounded-full border border-green-200 bg-green-50 px-2 py-1 text-xs text-green-700'
const GRAY_CHIP_CLASSES =
  'rounded-full border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-500'

interface SelfCheckPanelProps {
  selfcheck: SelfCheckDTO
  /** The run's extracted keywords — lookup for run-language chip display
   *  (UI-SPEC: mirrors KeywordsPanel's pt/en display with canonical fallback). */
  keywords: KeywordDTO[]
  idioma: ResumeLanguage
}

/**
 * Pure copy picker (mirrors KeywordsPanel's resumoCoberturaCopy): the plain
 * factual survival tally — singular "1 de 1 keyword … aparece" vs plural
 * "{n} de {m} keywords … aparecem". NEVER a percentage, score, or progress
 * meter (REQUIREMENTS Out of Scope). Unit-testable offline by design
 * (no-new-deps contract).
 */
export function resumoSobrevivenciaCopy(survived: number, total: number): string {
  const template = total === 1 ? SELFCHECK_SOBREVIVENCIA_SINGULAR : SELFCHECK_SOBREVIVENCIA_PLURAL
  return template.replace('{survived}', String(survived)).replace('{total}', String(total))
}

/**
 * Run-language display mirror of KeywordsPanel's module-private keywordDisplay
 * (source: frontend/src/components/KeywordsPanel.tsx — kept local, its private
 * helpers are not imported): pt for pt-BR runs, en for EN runs, canonical fallback.
 */
function keywordDisplay(
  kw: KeywordDTO | undefined,
  canonical: string,
  idioma: ResumeLanguage,
): string {
  if (!kw) return canonical
  const primary = idioma === 'pt-BR' ? kw.pt : kw.en
  return primary ?? canonical
}

/** One ordem row: ✓/✗ glyph is aria-hidden and ALWAYS paired with visible row
 *  text (KeywordsPanel pairing mirrored) — never glyph or color alone. */
function OrdemRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <li className="text-sm text-gray-700">
      <span aria-hidden className={ok ? 'text-green-700' : 'text-red-700'}>
        {ok ? '✓' : '✗'}
      </span>{' '}
      {label}
    </li>
  )
}

/**
 * Zone 6 — the honest ATS self-check panel (D-13/D-14/D-15): renders ONLY after
 * a successful export (the receipt + this panel mount together, one POST). The
 * ordem block always renders (contato row first + one row per present section —
 * never empty); a zero-keyword run renders the loud zero line instead of a
 * silent empty checklist. Mixed verdicts render per item — never masked to
 * all-ok. Survival chips reuse the Phase 3 chip semantics verbatim: absence is
 * honest information (neutral gray ○), NOT failure (never red). Text-only
 * render — no raw-HTML path (T-04-07 posture).
 */
export function SelfCheckPanel({ selfcheck, keywords, idioma }: SelfCheckPanelProps) {
  const byCanonical = new Map(keywords.map((kw) => [kw.canonical, kw]))
  const sobrevivencia = selfcheck.sobrevivencia
  const survived = sobrevivencia.filter((item) => item.status === 'coberto').length
  // Record lookup for the raw-id fallback (unknown ordem ids render raw — D-14).
  const ordemLabels: Record<string, string> = SELFCHECK_ORDEM_LABELS

  return (
    <section aria-labelledby="selfcheck-panel-title">
      <h3 id="selfcheck-panel-title" className="text-base font-semibold text-gray-900">
        {SELFCHECK_TITLE}
      </h3>

      {/* Ordem das seções — one row per ordem entry IN PAYLOAD ORDER (the backend
          sends the contato row first); unknown ids render their raw id, never
          silently dropped. One-per-present-section → the block never renders empty. */}
      <h4 className="mt-4 text-sm font-semibold text-gray-900">{SELFCHECK_ORDEM_LABEL}</h4>
      <ul className="mt-1 space-y-1">
        {selfcheck.ordem.map((row, i) => (
          <OrdemRow
            key={`${i}-${row.id}`}
            label={i === 0 ? SELFCHECK_CONTATO_LABEL : (ordemLabels[row.id] ?? row.id)}
            ok={row.ok}
          />
        ))}
      </ul>

      {/* Sobrevivência de keywords — zero-keyword runs get the loud zero line
          (the ordem block above still renders); otherwise the factual tally
          line, then chips grouped by the fixed CATEGORY_ORDER with empty
          categories hidden, flex-wrap only (panel grows vertically). */}
      <h4 className="mt-4 text-sm font-semibold text-gray-900">{SELFCHECK_SOBREVIVENCIA_LABEL}</h4>
      {sobrevivencia.length === 0 ? (
        <p className="mt-2 text-sm text-gray-700">{SELFCHECK_KEYWORDS_ZERO}</p>
      ) : (
        <>
          <p className="mt-2 text-sm text-gray-700">
            {resumoSobrevivenciaCopy(survived, sobrevivencia.length)}
          </p>
          <div className="mt-4 space-y-3">
            {CATEGORY_ORDER.map((category) => {
              const items = sobrevivencia.filter((item) => item.category === category)
              if (items.length === 0) return null // empty categories stay hidden
              return (
                <div key={category}>
                  <h5 className="text-xs text-gray-500">{CATEGORY_LABELS[category]}</h5>
                  <ul className="mt-1 flex flex-wrap gap-2">
                    {items.map((item, i) => {
                      const sobreviveu = item.status === 'coberto'
                      return (
                        <li
                          key={`${i}-${item.canonical}`}
                          className={sobreviveu ? GREEN_CHIP_CLASSES : GRAY_CHIP_CLASSES}
                        >
                          <span aria-hidden>{sobreviveu ? '✓' : '○'}</span>{' '}
                          {keywordDisplay(byCanonical.get(item.canonical), item.canonical, idioma)}
                          <span className="sr-only">
                            {sobreviveu ? SELFCHECK_KEYWORD_NO_PDF : SELFCHECK_KEYWORD_AUSENTE}
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

      {/* Gate footer (D-06/D-07): the panel shows order + survival; this line
          surfaces the server-side checks the download was conditioned on as a
          guarantee — mounted only after a gate-ok export. */}
      <p className="mt-4 text-xs text-gray-500">{SELFCHECK_GATE_FOOTER}</p>
    </section>
  )
}
