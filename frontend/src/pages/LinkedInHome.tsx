import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  fetchLinkedinLint,
  fetchProfile,
  gerarLinkedin,
  type LinkedinGerarResponse,
  type LinkedinLimiteDTO,
  type LinkedinLintResponse,
  type LinkedinSecaoId,
  type LocalizedText,
  type ResumeLanguage,
} from '../api/client'
import { CharacterCounter } from '../components/CharacterCounter'
import { CopiarButton } from '../components/CopiarButton'
import { ErrorPanel } from '../components/ErrorPanel'
import { PlaceholderBanner } from '../components/PlaceholderBanner'
import { StatusLine } from '../components/StatusLine'
import type { OrigemBadge } from '../components/SectionVersionsPanel'
import {
  BADGE_EDITADO,
  BADGE_EDITADO_CLASSES,
  BADGE_GERADO,
  BADGE_GERADO_CLASSES,
  CURRICULO_EPHEMERAL_NOTICE,
  CURRICULO_ERROR_HINT,
  CURRICULO_ERROR_RETRY,
  CURRICULO_IDIOMA_OPTIONS,
  CURRICULO_LINT_FETCH_ERRO,
  CURRICULO_LINT_HINT,
  formatarSkillsContagem,
  LINKEDIN_BLOCK_LABELS,
  LINKEDIN_CTA,
  LINKEDIN_CTA_INFLIGHT,
  LINKEDIN_EMPTY_BODY,
  LINKEDIN_EMPTY_TITLE,
  LINKEDIN_ERROR_TITLE,
  LINKEDIN_EXPERIENCIA_ZERO,
  LINKEDIN_IDIOMA_LABEL,
  LINKEDIN_INFLIGHT_HINT,
  LINKEDIN_LINT_CLEAR,
  LINKEDIN_LINT_TITLE,
  LINKEDIN_OBJETIVO_LABEL,
  LINKEDIN_OBJETIVO_MAX_CHARS,
  LINKEDIN_OBJETIVO_MIN_CHARS,
  LINKEDIN_OBJETIVO_PLACEHOLDER,
  LINKEDIN_OBJETIVO_TOO_LONG_HINT,
  LINKEDIN_OBJETIVO_TOO_SHORT_HINT,
  LINKEDIN_OVERLIMIT_FLAG,
  LINKEDIN_PAGE_TITLE,
  LINKEDIN_RESULT_TITLE,
  PERFIL_ERROR_TITLE,
  PERFIL_LOADING,
  POLICY_EDICAO,
  PREVIEW_CONTACT_SEPARATOR,
  PRIMARY_BUTTON_CLASSES,
  TEXTAREA_CLASSES,
} from '../constants/ui'

type LinkedinGerarOk = Extract<LinkedinGerarResponse, { status: 'ok' }>
type LinkedinLintOk = Extract<LinkedinLintResponse, { status: 'ok' }>

// The four blocks render in THIS fixed order (probe edge LI-01/ordering):
// the result card maps over this static array — never over completion or
// key order of the response object.
const BLOCOS_FIXOS: LinkedinSecaoId[] = ['headline', 'sobre', 'experiencias', 'habilidades']

const DEBOUNCE_MS = 800 // one lint call per settled typing state (T-03-10 bound)

// Pinned class strings from the UI-SPEC Component conventions (plan 06-01).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
const SECONDARY_BUTTON_CLASSES =
  'min-h-10 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
const IDIOMA_SELECTED_CLASSES =
  'cursor-pointer rounded bg-white px-3 py-1 text-sm font-semibold text-blue-600 shadow-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
const IDIOMA_UNSELECTED_CLASSES =
  'cursor-pointer rounded px-3 py-1 text-sm text-gray-600 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
// UI-SPEC Component conventions: generated-section headings reuse the card's
// bordered-uppercase pattern; block h4 stays the grandfathered pattern.
const BLOCK_HEADING_CLASSES = 'text-sm font-bold uppercase tracking-wide text-gray-500'

/** Badge origin for generated-section text (D-04): 'gerado' at mount/regen,
 *  'editado' after a save or the restore of an edited version. */
export type LinkedinOrigemBadge = OrigemBadge

/** Badge origin per block — experiências carries ONE badge PER ENTRY (entries
 *  are edited/restored independently; the group itself never shows a badge). */
interface LinkedinOrigens {
  headline: OrigemBadge
  sobre: OrigemBadge
  experiencias: OrigemBadge[]
  habilidades: OrigemBadge
}

function origensIniciais(secoes: LinkedinGerarOk['secoes']): LinkedinOrigens {
  return {
    headline: 'gerado',
    sobre: 'gerado',
    experiencias: secoes.experiencias.map(() => 'gerado'),
    habilidades: 'gerado',
  }
}

function Badge({ origem }: { origem: OrigemBadge }) {
  return (
    <span className={origem === 'gerado' ? BADGE_GERADO_CLASSES : BADGE_EDITADO_CLASSES}>
      {origem === 'gerado' ? BADGE_GERADO : BADGE_EDITADO}
    </span>
  )
}

/** Run-language display resolver — mirrored from ComparisonPanel (its private
 *  helpers are not imported across components). */
function tLang(map: LocalizedText | null | undefined, language: ResumeLanguage): string {
  if (!map) return ''
  if (language === 'en') {
    return map.en ?? map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
  }
  return map['pt-BR'] ?? (Object.values(map).find(Boolean) ?? '')
}

/**
 * Zone 2 — objective-tied lint (D-03), LintPanel structure verbatim with
 * LinkedIn-scoped title + clear line; the hint reuses the Currículo constant.
 * Backend avisos lines render VERBATIM as JSX text children — never parsed,
 * re-mapped, or translated (D-13/D-14). Zero warnings → the green clear-line,
 * never a silent empty panel.
 */
function LinkedinLintPanel({ resultado }: { resultado: LinkedinLintOk | null }) {
  if (!resultado) return null

  if (resultado.avisos.length === 0) {
    return (
      <p className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
        {LINKEDIN_LINT_CLEAR}
      </p>
    )
  }

  return (
    <section
      aria-labelledby="linkedin-lint-title"
      className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900"
    >
      <h3 id="linkedin-lint-title" className="text-sm font-semibold">
        {LINKEDIN_LINT_TITLE}
      </h3>
      <ul className="mt-2 list-disc pl-5 text-sm">
        {resultado.avisos.map((linha, i) => (
          <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
            {linha}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-amber-700">{CURRICULO_LINT_HINT}</p>
    </section>
  )
}

/**
 * The LinkedIn screen (plans 06-01 + 06-03): declare a career objective →
 * choose the run language → read the non-blocking lint (D-03) → generate ALL
 * FOUR blocks in fixed order (D-04) → copy any block/entry straight to
 * LinkedIn (D-08) with live counters and over-limit flags (D-06/D-07 —
 * nothing ever truncated). All result state is session React state (D-11
 * ephemeral) — a refresh returns to the empty form. A gerar success swaps the
 * result in WHOLESALE (probe edge LI-01/adjacency); an erro envelope renders
 * the backend PT-BR lines verbatim; a fetch-level failure renders the generic
 * hint path; a failed gerar keeps any prior result mounted (failure never
 * blanks). Experiência sub-block headers are anchored to PROFILE FACTS —
 * never the generated payload strings; per-entry Copiar copies that entry's
 * descricao ONLY. All content renders as JSX text children — no raw-HTML path
 * (T-06-05). Over-limit output is flagged in place, NEVER truncated (D-07);
 * Copiar stays enabled (the flag warns, the user decides).
 */
export default function LinkedInHome() {
  // Profile gate — the SAME ['perfil'] query the other pages use; a broken
  // profile blocks generation here too.
  const perfilQuery = useQuery({ queryKey: ['perfil'], queryFn: fetchProfile })

  // Zone 1 inputs: raw objetivo + run language. The debounced copy drives the
  // lint query (the exact Phase 3 mechanism — one call per settled state).
  const [objetivo, setObjetivo] = useState('')
  const [debouncedObjetivo, setDebouncedObjetivo] = useState('')
  const [idioma, setIdioma] = useState<ResumeLanguage>('pt-BR')
  // Last successful generate response — session state only (D-11).
  const [resultado, setResultado] = useState<LinkedinGerarOk | null>(null)
  // Generation failure (erro envelope lines, or [] for a thrown fetch failure).
  const [gerarErros, setGerarErros] = useState<string[] | null>(null)
  // Badge origin per block / per experiência entry (D-04 lifecycle).
  const [origens, setOrigens] = useState<LinkedinOrigens>({
    headline: 'gerado',
    sobre: 'gerado',
    experiencias: [],
    habilidades: 'gerado',
  })

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedObjetivo(objetivo), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [objetivo])

  const trimmed = objetivo.trim()
  const debouncedTrimmed = debouncedObjetivo.trim()
  // Zone 2 query (D-03): fires only once the DEBOUNCED objetivo reaches the
  // min trimmed chars — the same floor the backend's Field(min_length=80)
  // enforces (client mirror, WR-01). Pending lint renders nothing.
  const lintReady = debouncedTrimmed.length >= LINKEDIN_OBJETIVO_MIN_CHARS
  const lintQuery = useQuery({
    queryKey: ['linkedin-lint', debouncedTrimmed],
    queryFn: () => fetchLinkedinLint(debouncedTrimmed),
    enabled: lintReady,
  })

  // The CTA gate (D-02): trimmed objetivo >= min enables the CTA.
  const ctaHabilitado = trimmed.length >= LINKEDIN_OBJETIVO_MIN_CHARS

  const gerar = useMutation({
    mutationFn: gerarLinkedin,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        // D-11 wholesale swap: the response replaces the displayed state in
        // ONE assignment — never a client-side merge (runs are independent;
        // identical objectives across runs never merge).
        setResultado(data)
        setGerarErros(null)
        // Badge lifecycle (UI-SPEC): a fresh run resets every badge to Gerado.
        setOrigens(origensIniciais(data.secoes))
      } else {
        // 200-envelope erro: backend PT-BR lines, rendered verbatim below.
        setGerarErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down): generic hint path (erros=[]).
      // Raw detail is in the uvicorn terminal only; prior result stays mounted.
      setGerarErros([])
    },
  })

  function gerarAgora() {
    gerar.mutate({ objetivo: trimmed, language: idioma })
  }

  if (perfilQuery.isPending) {
    return <p className="text-gray-500">{PERFIL_LOADING}</p>
  }

  if (perfilQuery.isError || !perfilQuery.data) {
    return <p className="text-red-600">{PERFIL_ERROR_TITLE}</p>
  }

  if (perfilQuery.data.status === 'erro') {
    // Broken profile = rendered UI state (verbatim house pattern); generation
    // is unavailable until the profile loads.
    return (
      <div className="space-y-4">
        <StatusLine ok={false} />
        <ErrorPanel erros={perfilQuery.data.erros} />
      </div>
    )
  }

  const lintOk: LinkedinLintOk | null =
    lintQuery.data && lintQuery.data.status === 'ok' ? lintQuery.data : null
  // Narrowed ok payload (guaranteed by the early returns above) — the
  // experiência sub-block headers anchor to ITS facts.
  const perfilOk = perfilQuery.data

  // The counter + red over-limit flag pair for one {limite, tamanho, excesso}
  // record (D-06/D-07): per block / per entry — a compliant block shows a
  // normal counter while another is over; never a page-level verdict. The
  // flag never disables Copiar (it warns, the user decides).
  function ContadorLimite({ limite }: { limite: LinkedinLimiteDTO }) {
    return (
      <>
        <CharacterCounter count={limite.tamanho} limite={limite.limite} />
        {limite.excesso > 0 && (
          <p className="mt-1 text-xs text-red-600">
            {LINKEDIN_OVERLIMIT_FLAG.replace('{excesso}', String(limite.excesso))}
          </p>
        )}
      </>
    )
  }

  // --- Zone 3 block renderers — BLOCOS_FIXOS order, one function per shape ---

  // Headline / Sobre: plain prose blocks with the shared block anatomy.
  function renderBlocoProsa(bloco: 'headline' | 'sobre') {
    if (!resultado) return null
    const texto = resultado.secoes[bloco]
    const limite = resultado.limites[bloco]
    return (
      <div className="mt-4 border-t border-gray-200 pt-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS[bloco]}</h4>
          <Badge origem={origens[bloco]} />
        </div>
        {/* Action row (UI-SPEC): Copiar is FIRST — the phase's deliverable. */}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          <CopiarButton text={texto} />
        </div>
        <p className="mt-2 whitespace-pre-wrap text-sm text-gray-900">{texto}</p>
        <ContadorLimite limite={limite} />
      </div>
    )
  }

  // Experiência group (D-09): ONE group is the regen unit; one sub-block per
  // generated entry ALIGNED TO PROFILE ORDER, each header anchored to the
  // PROFILE FACTS (company — title, run language) — never the generated
  // payload strings. Per-entry footer row: counter first, then Copiar (that
  // entry's descricao ONLY) — Editar entrada joins in the editor wave.
  function renderBlocoExperiencias() {
    if (!resultado) return null
    const entradas = resultado.secoes.experiencias
    const perfilExps = perfilOk.perfil.experiences
    // Zero experiences (profile OR generated list — defensive on both sides)
    // renders the loud muted line — never an empty block (LI-04/empty).
    if (perfilExps.length === 0 || entradas.length === 0) {
      return (
        <div className="mt-4 border-t border-gray-200 pt-3">
          <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS.experiencias}</h4>
          <p className="mt-2 text-sm text-gray-500">{LINKEDIN_EXPERIENCIA_ZERO}</p>
        </div>
      )
    }
    return (
      <div className="mt-4 border-t border-gray-200 pt-3">
        <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS.experiencias}</h4>
        <div className="mt-2 space-y-4">
          {entradas.map((entrada, i) => {
            // Index-aligned pairing (06-02 alignment contract); the profile
            // facts win whenever the pairing exists — the LLM strings are
            // display anchors only (fallback for a defensive length drift).
            const perfilExp = perfilExps[i]
            const company = perfilExp ? perfilExp.company : entrada.company
            const title = perfilExp ? tLang(perfilExp.title, resultado.idioma) : entrada.title
            const limite = resultado.limites.experiencias[i]
            return (
              <article key={`experiencia-${i}`} className="break-inside-avoid">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h5 className="text-sm font-semibold text-gray-900">
                    {company}
                    {PREVIEW_CONTACT_SEPARATOR}
                    {title}
                  </h5>
                  {origens.experiencias[i] && <Badge origem={origens.experiencias[i]} />}
                </div>
                <p className="mt-1 whitespace-pre-wrap text-sm text-gray-900">
                  {entrada.descricao}
                </p>
                {limite && (
                  <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
                    <ContadorLimite limite={limite} />
                    <CopiarButton text={entrada.descricao} />
                  </div>
                )}
              </article>
            )
          })}
        </div>
      </div>
    )
  }

  // Habilidades (LI-05): ordered list — returned order IS priority order (no
  // client re-sort); the counter slot carries the honest count line via the
  // pure singular/plural functions (no fake "/Y" — D-05). Copiar emits all
  // skills one per line in priority order.
  function renderBlocoHabilidades() {
    if (!resultado) return null
    const skills = resultado.secoes.habilidades
    return (
      <div className="mt-4 border-t border-gray-200 pt-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS.habilidades}</h4>
          <Badge origem={origens.habilidades} />
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          <CopiarButton text={skills.join('\n')} />
        </div>
        {skills.length > 0 && (
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
            {skills.map((skill, i) => (
              <li key={`${i}-${skill}`}>{skill}</li>
            ))}
          </ol>
        )}
        {/* Count line in the counter slot (UI-SPEC skills-counter exception). */}
        <p className="mt-2 text-xs text-gray-500">{formatarSkillsContagem(skills.length)}</p>
      </div>
    )
  }

  // Fixed display order (probe edge LI-01/ordering): the map over the static
  // BLOCOS_FIXOS array is the ONLY thing deciding render order.
  function renderBloco(bloco: LinkedinSecaoId) {
    if (bloco === 'experiencias') return renderBlocoExperiencias()
    if (bloco === 'habilidades') return renderBlocoHabilidades()
    return renderBlocoProsa(bloco)
  }

  return (
    <div className="space-y-6">
      <StatusLine ok={true} />
      {perfilQuery.data.exemplo && <PlaceholderBanner />}
      <h2 className="text-xl font-semibold text-gray-900">{LINKEDIN_PAGE_TITLE}</h2>

      {!resultado && !gerar.isPending && (
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-gray-900">{LINKEDIN_EMPTY_TITLE}</h3>
          <p className="text-sm text-gray-600">{LINKEDIN_EMPTY_BODY}</p>
        </div>
      )}

      {/* Zone 1 — form card */}
      <form
        className={CARD_CLASSES}
        onSubmit={(event) => {
          event.preventDefault()
          gerarAgora()
        }}
      >
        <div className="space-y-4">
          <div className="space-y-1">
            <label
              htmlFor="linkedin-objetivo"
              className="block text-sm font-semibold text-gray-900"
            >
              {LINKEDIN_OBJETIVO_LABEL}
            </label>
            <textarea
              id="linkedin-objetivo"
              value={objetivo}
              onChange={(event) => setObjetivo(event.target.value)}
              placeholder={LINKEDIN_OBJETIVO_PLACEHOLDER}
              maxLength={LINKEDIN_OBJETIVO_MAX_CHARS}
              className={TEXTAREA_CLASSES}
            />
            {trimmed.length < LINKEDIN_OBJETIVO_MIN_CHARS && (
              <p className="text-xs text-gray-500">
                {LINKEDIN_OBJETIVO_TOO_SHORT_HINT.replace(
                  '{min}',
                  String(LINKEDIN_OBJETIVO_MIN_CHARS),
                )}
              </p>
            )}
            {objetivo.length >= LINKEDIN_OBJETIVO_MAX_CHARS && (
              <p className="text-xs text-gray-500">
                {LINKEDIN_OBJETIVO_TOO_LONG_HINT.replace(
                  '{max}',
                  String(LINKEDIN_OBJETIVO_MAX_CHARS),
                )}
              </p>
            )}
          </div>

          {/* Idioma segmented control — reused verbatim (same classes, same options). */}
          <fieldset>
            <legend className="text-sm font-semibold text-gray-900">{LINKEDIN_IDIOMA_LABEL}</legend>
            <div className="mt-2 inline-flex rounded-md border border-gray-300 bg-gray-50 p-1">
              {(Object.keys(CURRICULO_IDIOMA_OPTIONS) as ResumeLanguage[]).map((lang) => (
                <label
                  key={lang}
                  className={idioma === lang ? IDIOMA_SELECTED_CLASSES : IDIOMA_UNSELECTED_CLASSES}
                >
                  <input
                    type="radio"
                    name="idioma-linkedin"
                    value={lang}
                    checked={idioma === lang}
                    onChange={() => setIdioma(lang)}
                    className="sr-only"
                  />
                  {CURRICULO_IDIOMA_OPTIONS[lang]}
                </label>
              ))}
            </div>
          </fieldset>

          <button
            type="submit"
            disabled={!ctaHabilitado || gerar.isPending}
            className={PRIMARY_BUTTON_CLASSES}
          >
            {gerar.isPending ? LINKEDIN_CTA_INFLIGHT : LINKEDIN_CTA}
          </button>
        </div>
      </form>

      {/* Zone 2 — lint avisos (D-03, non-blocking): pending renders nothing —
          the form stays primary (Phase 3 mechanism). */}
      {lintReady && lintOk && <LinkedinLintPanel resultado={lintOk} />}
      {lintReady && lintQuery.data && lintQuery.data.status === 'erro' && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
          <ul className="list-disc pl-5 text-sm text-red-700">
            {lintQuery.data.erros.map((linha, i) => (
              <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
                {linha}
              </li>
            ))}
          </ul>
        </div>
      )}
      {/* Fetch-level failure (server down / non-200 → lintQuery.isError):
          the Currículo lint red-panel convention (CURRICULO_LINT_FETCH_ERRO) —
          generic PT-BR hint, raw detail terminal-only. Never silent. */}
      {lintReady && lintQuery.isError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{CURRICULO_LINT_FETCH_ERRO}</p>
        </div>
      )}

      {/* Zone 3 — one aria-live region: in-flight hints, error panels, result. */}
      <div aria-live="polite" className="space-y-6">
        {gerar.isPending && <p className="text-sm text-gray-600">{LINKEDIN_INFLIGHT_HINT}</p>}

        {gerarErros !== null && !gerar.isPending && (
          <section
            aria-labelledby="linkedin-gerar-error-title"
            className="rounded-md border border-red-300 bg-red-50 px-4 py-3"
          >
            <h3 id="linkedin-gerar-error-title" className="font-semibold text-red-700">
              {LINKEDIN_ERROR_TITLE}
            </h3>
            {gerarErros.length > 0 && (
              <ul className="mt-2 list-disc pl-5 text-sm text-red-700">
                {gerarErros.map((linha, i) => (
                  <li key={`${i}-${linha}`} className="whitespace-pre-wrap">
                    {linha}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-xs text-red-600">{CURRICULO_ERROR_HINT}</p>
            <button
              type="button"
              onClick={gerarAgora}
              disabled={gerar.isPending}
              className={`mt-3 ${SECONDARY_BUTTON_CLASSES}`}
            >
              {CURRICULO_ERROR_RETRY}
            </button>
          </section>
        )}

        {resultado && (
          <>
            {/* Ephemeral notice ABOVE the card (UI-SPEC Zone 3; Currículo copy verbatim). */}
            <p className="text-xs text-gray-500">{CURRICULO_EPHEMERAL_NOTICE}</p>
            <section className={CARD_CLASSES} aria-label={LINKEDIN_RESULT_TITLE}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-base font-semibold text-gray-900">{LINKEDIN_RESULT_TITLE}</h3>
                <p className="text-xs text-gray-500">
                  <span aria-hidden>⚠</span> {POLICY_EDICAO}
                </p>
              </div>

              {/* Four blocks in FIXED display order (static array — LI-01). */}
              {BLOCOS_FIXOS.map((bloco) => renderBloco(bloco))}
            </section>
          </>
        )}
      </div>
    </div>
  )
}
