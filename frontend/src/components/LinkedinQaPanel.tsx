import type { LinkedinQaPayload } from '../api/client'
import {
  QA_BLEED_LABEL,
  QA_BLEED_ZERO,
  QA_EN_NOTE,
  QA_GLOSSARIO_LABEL,
  QA_GLOSSARIO_ZERO,
  QA_LEGENDA,
  QA_PANEL_TITLE,
} from '../constants/ui'

interface LinkedinQaPanelProps {
  /** The LATEST generation response's qa payload (06-04 contract): the dict
   *  on pt-BR runs (loud-empty lists when clean), null on EN runs. Swapped
   *  wholesale ONLY by a generation success — never recomputed client-side
   *  (truthfulness rule, Pitfall 4). */
  qa: LinkedinQaPayload | null
}

/**
 * "Verificação de idioma" (D-13/D-14 — the phase's new UI surface, plan 06-05).
 * Bare section rendered directly below the result card (it verifies the
 * artifact above it — the SelfCheckPanel role), never a new card style.
 *
 * - Glossário aplicado (D-13): one row per deterministic substitution,
 *   `{de} → {para}` (plain-text arrow). Zero substitutions → the loud zero
 *   line — never a silently empty block.
 * - Inglês em texto em português (D-14): one amber row per bleed finding,
 *   `{termo} — {seção}` (amber = attention-without-failure). Zero findings →
 *   the loud zero line.
 * - Legend ALWAYS renders with the non-blocking framing — the panel is
 *   advisory and never gates Copiar (D-14).
 * - qa === null (EN runs) → the neutral note instead of the two blocks —
 *   never silently absent (D-14/SC4).
 *
 * All rows render the backend payload VERBATIM as JSX text children — no
 * frontend re-mapping or re-computation of glossary/bleed anywhere (Pitfall
 * 4; T-06-05: text-only render, no raw-HTML path).
 */
export function LinkedinQaPanel({ qa }: LinkedinQaPanelProps) {
  return (
    <section aria-labelledby="linkedin-qa-title">
      <h3 id="linkedin-qa-title" className="text-base font-semibold text-gray-900">
        {QA_PANEL_TITLE}
      </h3>
      {qa === null ? (
        <p className="mt-2 text-sm text-gray-500">{QA_EN_NOTE}</p>
      ) : (
        <>
          <h4 className="mt-4 text-sm font-semibold text-gray-900">{QA_GLOSSARIO_LABEL}</h4>
          {qa.glossario.length === 0 ? (
            <p className="text-sm text-gray-500">{QA_GLOSSARIO_ZERO}</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {qa.glossario.map((row, i) => (
                <li key={`${i}-${row.de}`} className="text-sm text-gray-700">
                  {row.de} → {row.para}
                </li>
              ))}
            </ul>
          )}
          <h4 className="mt-4 text-sm font-semibold text-gray-900">{QA_BLEED_LABEL}</h4>
          {qa.bleed.length === 0 ? (
            <p className="text-sm text-gray-500">{QA_BLEED_ZERO}</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {qa.bleed.map((row, i) => (
                <li key={`${i}-${row.termo}`} className="text-sm text-amber-800">
                  {row.termo} — {row.secao}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <p className="mt-4 text-xs text-gray-500">{QA_LEGENDA}</p>
    </section>
  )
}
