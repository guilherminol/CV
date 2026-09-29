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
  type LinkedinSecoesDTO,
  type LocalizedText,
  type ResumeLanguage,
} from '../api/client'
import { CharacterCounter } from '../components/CharacterCounter'
import { CopiarButton } from '../components/CopiarButton'
import { ErrorPanel } from '../components/ErrorPanel'
import { LinkedinComparisonPanel } from '../components/LinkedinComparisonPanel'
import {
  LinkedinSectionEditor,
  type LinkedinEditorState,
} from '../components/LinkedinSectionEditor'
import { PlaceholderBanner } from '../components/PlaceholderBanner'
import { StatusLine } from '../components/StatusLine'
import { dividirLinhas } from '../components/SectionEditor'
import type { OrigemBadge } from '../components/SectionVersionsPanel'
import {
  BADGE_EDITADO,
  BADGE_EDITADO_CLASSES,
  BADGE_GERADO,
  BADGE_GERADO_CLASSES,
  COMPARACAO_TOGGLE,
  COMPARACAO_TOGGLE_HIDE,
  CURRICULO_EPHEMERAL_NOTICE,
  CURRICULO_ERROR_HINT,
  CURRICULO_ERROR_RETRY,
  CURRICULO_IDIOMA_OPTIONS,
  CURRICULO_LINT_FETCH_ERRO,
  CURRICULO_LINT_HINT,
  DICA_LABEL,
  DICA_PLACEHOLDER,
  DICA_TOGGLE_ADD,
  DICA_TOGGLE_HIDE,
  EDITAR_ENTRADA_CTA,
  EDITAR_SECAO_CTA,
  EDIT_SAVE_GUARD,
  formatarSkillsContagem,
  HINT_INPUT_CLASSES,
  LINKEDIN_BLOCK_LABELS,
  LINKEDIN_CTA,
  LINKEDIN_CTA_INFLIGHT,
  LINKEDIN_DICA_MAX_CHARS,
  LINKEDIN_EDIT_OVERLIMIT_HINT,
  LINKEDIN_EMPTY_BODY,
  LINKEDIN_EMPTY_TITLE,
  LINKEDIN_ERROR_TITLE,
  LINKEDIN_EXPERIENCIA_MAX_CHARS,
  LINKEDIN_EXPERIENCIA_ZERO,
  LINKEDIN_HEADLINE_MAX_CHARS,
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
  LINKEDIN_SOBRE_MAX_CHARS,
  PERFIL_ERROR_TITLE,
  PERFIL_LOADING,
  POLICY_EDICAO,
  PREVIEW_CONTACT_SEPARATOR,
  PRIMARY_BUTTON_CLASSES,
  QUIET_BUTTON_CLASSES,
  RESTAURAR_VERSAO_CTA,
  TEXTAREA_CLASSES,
  VERSOES_INTRO,
  VERSOES_TOGGLE,
  VERSOES_TOGGLE_COUNT,
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

/** Version-stack identity: one stack per block — Experiência: per ENTRY
 *  (keyed `experiencias-{i}`, aligned to profile order). */
type LinkedinVersionKey = LinkedinSecaoId | `experiencias-${number}`

/** A stored prior version: the displayed value (string, or the skills list
 *  for habilidades; entries store their descricao string) + its badge origin. */
interface LinkedinVersao {
  chave: LinkedinVersionKey
  origem: OrigemBadge
  valor: string | string[]
}

function Badge({ origem }: { origem: OrigemBadge }) {
  return (
    <span className={origem === 'gerado' ? BADGE_GERADO_CLASSES : BADGE_EDITADO_CLASSES}>
      {origem === 'gerado' ? BADGE_GERADO : BADGE_EDITADO}
    </span>
  )
}

/** One stored version row (D-08): origin badge + Restaurar versão + the
 *  line-clamp-2 plain-text snippet. Newest first (the page prepends). */
function LinkedinVersaoRow({
  versao,
  desabilitado,
  onRestaurar,
}: {
  versao: LinkedinVersao
  desabilitado: boolean
  onRestaurar: () => void
}) {
  const trecho = Array.isArray(versao.valor) ? versao.valor.join(', ') : versao.valor
  return (
    <div className="rounded-md border border-gray-200 bg-white px-3 py-2">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <span
          className={versao.origem === 'gerado' ? BADGE_GERADO_CLASSES : BADGE_EDITADO_CLASSES}
        >
          {versao.origem === 'gerado' ? BADGE_GERADO : BADGE_EDITADO}
        </span>
        <button
          type="button"
          onClick={onRestaurar}
          disabled={desabilitado}
          className={QUIET_BUTTON_CLASSES}
        >
          {RESTAURAR_VERSAO_CTA}
        </button>
      </div>
      <p className="mt-1 line-clamp-2 text-sm text-gray-600">{trecho}</p>
    </div>
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
 * nothing ever truncated), then edit inline (D-12, one editor at a time),
 * compare against the profile, and restore prior versions (D-08). Every
 * destructive write is preceded by a stack push onto `versoes`
 * (stack-before-mutate); state swaps happen WHOLESALE from responses — never
 * a client-side merge. All result state is session React state (D-11
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
  // The ONE open inline editor (D-12): which block (+ which experiência
  // entry) + the textarea draft. Dirty is DERIVED (draft !== inicial). The
  // draft lives at page level so the regen-over-edit confirm (regen wave) can
  // stack it before the editor closes.
  const [editor, setEditor] = useState<LinkedinEditorState | null>(null)
  // Per-key version stacks (D-08, session-only): EVERY destructive path —
  // edit save, regen success, restore, confirmed full regen — pushes the
  // current displayed value + badge origin here FIRST via empilharValor.
  // Newest first; never capped, never silently dropped.
  const [versoes, setVersoes] = useState<Record<string, LinkedinVersao[]>>({})
  // Per-block disclosure state — read-only disclosures stay usable while a
  // long op is pending (UI-SPEC locking matrix).
  const [versoesAbertas, setVersoesAbertas] = useState<Record<LinkedinSecaoId, boolean>>({
    headline: false,
    sobre: false,
    experiencias: false,
    habilidades: false,
  })
  const [comparacaoAbertas, setComparacaoAbertas] = useState<Record<LinkedinSecaoId, boolean>>({
    headline: false,
    sobre: false,
    experiencias: false,
    habilidades: false,
  })
  // Per-block steering hint (D-05) + its on-demand toggle — the dica feeds
  // the regen mutations (regen wave) and persists across that block's regens
  // until the result is replaced.
  const [dicas, setDicas] = useState<Record<LinkedinSecaoId, string>>({
    headline: '',
    sobre: '',
    experiencias: '',
    habilidades: '',
  })
  const [dicaAbertas, setDicaAbertas] = useState<Record<LinkedinSecaoId, boolean>>({
    headline: false,
    sobre: false,
    experiencias: false,
    habilidades: false,
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

  // The CTA gate (D-02 + UI-SPEC interaction rules): trimmed objetivo >= min
  // AND no long op pending AND no editor open. `operacaoLongaPendente` and
  // `locksEdicao` are derived ONCE below (after the mutations), never scattered.
  const ctaHabilitado = trimmed.length >= LINKEDIN_OBJETIVO_MIN_CHARS

  const gerar = useMutation({
    mutationFn: gerarLinkedin,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        // D-11 wholesale swap: the response replaces the displayed state in
        // ONE assignment — never a client-side merge (runs are independent;
        // identical objectives across runs never merge). The version stacks
        // SURVIVE the swap (session state, D-11).
        setResultado(data)
        setGerarErros(null)
        // Badge lifecycle (UI-SPEC): a fresh run resets every badge to Gerado.
        setOrigens(origensIniciais(data.secoes))
        // A replaced result invalidates the per-block UI state (UI-SPEC hint
        // lifecycle + disclosures close).
        setDicas({ headline: '', sobre: '', experiencias: '', habilidades: '' })
        setDicaAbertas({
          headline: false,
          sobre: false,
          experiencias: false,
          habilidades: false,
        })
        setVersoesAbertas({
          headline: false,
          sobre: false,
          experiencias: false,
          habilidades: false,
        })
        setComparacaoAbertas({
          headline: false,
          sobre: false,
          experiencias: false,
          habilidades: false,
        })
        setEditor(null)
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

  // Derived locking booleans (UI-SPEC interaction table — the single source;
  // no ad-hoc scattered disabled logic):
  //  - operacaoLongaPendente: ANY long op (full gerar; section regen joins in
  //    the regen wave) disables edit controls / Restaurar versão / dica
  //    toggles+inputs, while Comparar and Versões toggles and every Copiar
  //    stay usable read-only/instant.
  //  - locksEdicao: additionally, an open editor disables every edit
  //    affordance + the CTA + Gerar novamente, while the editor's own
  //    Salvar/Cancelar freeze during any flight via `locked`.
  const operacaoLongaPendente = gerar.isPending
  const locksEdicao = editor !== null || operacaoLongaPendente

  function gerarAgora() {
    gerar.mutate({ objetivo: trimmed, language: idioma })
  }

  // --- displayed-state write helpers (the single source: resultado.secoes) ---

  function comSecoes(fn: (secoes: LinkedinSecoesDTO) => LinkedinSecoesDTO) {
    setResultado((prev) => (prev ? { ...prev, secoes: fn(prev.secoes) } : prev))
  }

  // --- SC4/D-08 stack-before-mutate helpers: ONE helper at the top of every
  // destructive path pushes the CURRENT displayed value + badge origin onto
  // its version stack before any write, so nothing is ever silently destroyed.

  function empilharValor(chave: LinkedinVersionKey, valor: string | string[], origem: OrigemBadge) {
    setVersoes((prev) => ({ ...prev, [chave]: [{ chave, origem, valor }, ...prev[chave] ?? []] }))
  }

  function empilharBloco(bloco: 'headline' | 'sobre' | 'habilidades') {
    if (!resultado) return
    if (bloco === 'habilidades') {
      empilharValor('habilidades', resultado.secoes.habilidades, origens.habilidades)
    } else {
      empilharValor(bloco, resultado.secoes[bloco], origens[bloco])
    }
  }

  function empilharEntrada(i: number) {
    if (!resultado) return
    const entrada = resultado.secoes.experiencias[i]
    if (!entrada) return
    empilharValor(`experiencias-${i}`, entrada.descricao, origens.experiencias[i] ?? 'gerado')
  }

  // --- inline editing (D-12) ---

  /** The block's limit client mirror (D-05) — the SAME constant the counter
   *  flags with; undefined for habilidades (no character limit exists). */
  function limiteDeBloco(bloco: LinkedinSecaoId): number | undefined {
    if (bloco === 'headline') return LINKEDIN_HEADLINE_MAX_CHARS
    if (bloco === 'sobre') return LINKEDIN_SOBRE_MAX_CHARS
    if (bloco === 'experiencias') return LINKEDIN_EXPERIENCIA_MAX_CHARS
    return undefined
  }

  interface LinkedinEditorEstado {
    canSave: boolean
    guardHint: string
    maxLength: number | undefined
  }

  /** Save-guard evaluation (WR-01): over-limit drafts (the real case — the
   *  backend can deliver over-limit text, D-07 flagged never truncated, so
   *  the editor pre-fill can START over) are unsavable with the reduce-first
   *  hint; Habilidades needs ≥1 non-empty line (EDIT_SAVE_GUARD); prose
   *  blocks need non-whitespace content (the backend's min_length=1 floors). */
  function estadoEditor(editorLocal: LinkedinEditorState): LinkedinEditorEstado {
    const limite = limiteDeBloco(editorLocal.bloco)
    const excesso = limite !== undefined ? Math.max(0, editorLocal.draft.length - limite) : 0
    if (excesso > 0) {
      return {
        canSave: false,
        guardHint: LINKEDIN_EDIT_OVERLIMIT_HINT.replace('{excesso}', String(excesso)),
        maxLength: limite,
      }
    }
    if (editorLocal.bloco === 'habilidades') {
      if (dividirLinhas(editorLocal.draft).length === 0) {
        return { canSave: false, guardHint: EDIT_SAVE_GUARD, maxLength: undefined }
      }
    } else if (editorLocal.draft.trim().length === 0) {
      return { canSave: false, guardHint: EDIT_SAVE_GUARD, maxLength: limite }
    }
    return { canSave: true, guardHint: '', maxLength: limite }
  }

  // Open the inline editor (D-12) pre-filled from the DISPLAYED text, at the
  // UI-SPEC granularity: Headline/Sobre whole string; Experiência per entry
  // (the entry's descricao); Habilidades one skill per line. One at a time.
  function abrirEditor(bloco: LinkedinSecaoId, entryIdx: number | null = null) {
    if (!resultado || editor) return
    let inicial: string
    if (bloco === 'headline') inicial = resultado.secoes.headline
    else if (bloco === 'sobre') inicial = resultado.secoes.sobre
    else if (bloco === 'habilidades') inicial = resultado.secoes.habilidades.join('\n')
    else inicial = resultado.secoes.experiencias[entryIdx ?? 0]?.descricao ?? ''
    setEditor({ bloco, entryIdx, draft: inicial, inicial })
  }

  // Edit save (D-12/D-04): stack the pre-edit version FIRST (SC4), write the
  // edited value into resultado.secoes, flip the badge to Editado, close.
  function salvarEdicao() {
    if (!editor || !resultado) return
    // CR-01 belt-and-braces: never write the displayed state under an
    // in-flight wholesale swap (the editor's buttons are already locked;
    // this guards the handler itself).
    if (operacaoLongaPendente) return
    if (!estadoEditor(editor).canSave) return // guard paranoia (button already disabled)
    const { bloco, entryIdx, draft } = editor
    if (bloco === 'experiencias') {
      const alvo = entryIdx ?? 0
      empilharEntrada(alvo)
      comSecoes((s) => ({
        ...s,
        experiencias: s.experiencias.map((e, i) =>
          i === alvo ? { ...e, descricao: draft } : e,
        ),
      }))
      setOrigens((prev) => ({
        ...prev,
        experiencias: prev.experiencias.map((o, i) => (i === alvo ? 'editado' : o)),
      }))
    } else if (bloco === 'habilidades') {
      empilharBloco('habilidades')
      comSecoes((s) => ({ ...s, habilidades: dividirLinhas(draft) }))
      setOrigens((prev) => ({ ...prev, habilidades: 'editado' }))
    } else if (bloco === 'headline') {
      empilharBloco('headline')
      comSecoes((s) => ({ ...s, headline: draft }))
      setOrigens((prev) => ({ ...prev, headline: 'editado' }))
    } else {
      empilharBloco('sobre')
      comSecoes((s) => ({ ...s, sobre: draft }))
      setOrigens((prev) => ({ ...prev, sobre: 'editado' }))
    }
    setEditor(null)
  }

  // Confirmed dirty-discard (WR-02): the strip's confirmed path stacks the
  // dirty draft FIRST as an 'editado' version (nothing of value is lost) —
  // THEN closes, making ConfirmStrip's stack-first contract literally true.
  function descartarEdicao() {
    if (editor && resultado && editor.draft !== editor.inicial && estadoEditor(editor).canSave) {
      const { bloco, entryIdx, draft } = editor
      if (bloco === 'experiencias') {
        empilharValor(`experiencias-${entryIdx ?? 0}`, draft, 'editado')
      } else if (bloco === 'habilidades') {
        empilharValor('habilidades', dividirLinhas(draft), 'editado')
      } else {
        empilharValor(bloco, draft, 'editado')
      }
    }
    setEditor(null)
  }

  // Restore (D-08/SC4): stack the CURRENT displayed version FIRST, then mount
  // the chosen version (removed from the stack — not duplicated) and adopt
  // its origin badge.
  function restaurarBloco(bloco: 'headline' | 'sobre' | 'habilidades', indice: number) {
    if (!resultado) return
    const pilha = versoes[bloco] ?? []
    const alvo = pilha[indice]
    if (!alvo) return
    empilharBloco(bloco)
    // empilharBloco PREPENDS, shifting the restored entry down by one —
    // remove it at indice + 1 (queued updaters apply in order).
    setVersoes((prev) => ({
      ...prev,
      [bloco]: (prev[bloco] ?? []).filter((_, i) => i !== indice + 1),
    }))
    if (bloco === 'habilidades') {
      comSecoes((s) => ({ ...s, habilidades: alvo.valor as string[] }))
    } else if (bloco === 'headline') {
      comSecoes((s) => ({ ...s, headline: alvo.valor as string }))
    } else {
      comSecoes((s) => ({ ...s, sobre: alvo.valor as string }))
    }
    setOrigens((prev) => ({ ...prev, [bloco]: alvo.origem }))
  }

  function restaurarEntrada(i: number, indice: number) {
    if (!resultado) return
    const chave: LinkedinVersionKey = `experiencias-${i}`
    const pilha = versoes[chave] ?? []
    const alvo = pilha[indice]
    if (!alvo) return
    empilharEntrada(i)
    setVersoes((prev) => ({
      ...prev,
      [chave]: (prev[chave] ?? []).filter((_, j) => j !== indice + 1),
    }))
    comSecoes((s) => ({
      ...s,
      experiencias: s.experiencias.map((e, j) =>
        j === i ? { ...e, descricao: alvo.valor as string } : e,
      ),
    }))
    setOrigens((prev) => ({
      ...prev,
      experiencias: prev.experiencias.map((o, j) => (j === i ? alvo.origem : o)),
    }))
  }

  // --- disclosure toggle helpers (derived-once, never scattered) ---

  function toggleComparacao(bloco: LinkedinSecaoId) {
    setComparacaoAbertas((prev) => ({ ...prev, [bloco]: !prev[bloco] }))
  }

  function toggleVersoes(bloco: LinkedinSecaoId) {
    setVersoesAbertas((prev) => ({ ...prev, [bloco]: !prev[bloco] }))
  }

  function toggleDica(bloco: LinkedinSecaoId) {
    setDicaAbertas((prev) => ({ ...prev, [bloco]: !prev[bloco] }))
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

  // The dica block (D-05): labeled one-line input, revealed by the
  // Adicionar dica toggle; disabled (toggle + input) while a long op runs.
  function renderDica(bloco: LinkedinSecaoId) {
    if (!dicaAbertas[bloco]) return null
    const inputId = `linkedin-dica-input-${bloco}`
    return (
      <div className="space-y-1">
        <label htmlFor={inputId} className="block text-xs font-semibold text-gray-900">
          {DICA_LABEL}
        </label>
        <input
          id={inputId}
          type="text"
          value={dicas[bloco]}
          onChange={(event) => setDicas((prev) => ({ ...prev, [bloco]: event.target.value }))}
          placeholder={DICA_PLACEHOLDER}
          disabled={operacaoLongaPendente}
          maxLength={LINKEDIN_DICA_MAX_CHARS}
          className={HINT_INPUT_CLASSES}
        />
      </div>
    )
  }

  // Shared quiet toggle: Comparar com o perfil (read-only — never disabled;
  // usable while long ops run / an editor is open, UI-SPEC locking matrix).
  function renderCompararToggle(bloco: LinkedinSecaoId) {
    return (
      <button
        type="button"
        onClick={() => toggleComparacao(bloco)}
        aria-expanded={comparacaoAbertas[bloco]}
        className={QUIET_BUTTON_CLASSES}
      >
        {comparacaoAbertas[bloco] ? COMPARACAO_TOGGLE_HIDE : COMPARACAO_TOGGLE}
      </button>
    )
  }

  // Shared quiet toggle: Versões ({count}) when > 0, disabled at 0 — no ghost
  // panel; read-only disclosure (usable while long ops run).
  function renderVersoesToggle(bloco: LinkedinSecaoId, count: number) {
    return (
      <button
        type="button"
        onClick={() => toggleVersoes(bloco)}
        aria-expanded={versoesAbertas[bloco]}
        disabled={count === 0}
        className={QUIET_BUTTON_CLASSES}
      >
        {count > 0 ? VERSOES_TOGGLE_COUNT.replace('{count}', String(count)) : VERSOES_TOGGLE}
      </button>
    )
  }

  function renderDicaToggle(bloco: LinkedinSecaoId) {
    return (
      <button
        type="button"
        onClick={() => toggleDica(bloco)}
        aria-expanded={dicaAbertas[bloco]}
        disabled={operacaoLongaPendente}
        className={QUIET_BUTTON_CLASSES}
      >
        {dicaAbertas[bloco] ? DICA_TOGGLE_HIDE : DICA_TOGGLE_ADD}
      </button>
    )
  }

  /** The inline editor for the block/entry currently being edited, or null. */
  function renderEditorAqui(
    bloco: LinkedinSecaoId,
    entryIdx: number | null,
  ) {
    if (!editor || editor.bloco !== bloco) return null
    if (bloco === 'experiencias' && editor.entryIdx !== entryIdx) return null
    const estado = estadoEditor(editor)
    return (
      <LinkedinSectionEditor
        secaoLabel={LINKEDIN_BLOCK_LABELS[bloco]}
        draft={editor.draft}
        dirty={editor.draft !== editor.inicial}
        canSave={estado.canSave}
        guardHint={estado.guardHint}
        maxLength={estado.maxLength}
        locked={operacaoLongaPendente}
        onDraftChange={(valor) =>
          setEditor((prev) => (prev ? { ...prev, draft: valor } : prev))
        }
        onSave={salvarEdicao}
        onCancel={() => setEditor(null)}
        onDescartar={descartarEdicao}
      />
    )
  }

  /** Per-block versions panel (headline/sobre/habilidades). */
  function renderVersoesBloco(bloco: 'headline' | 'sobre' | 'habilidades') {
    const pilha = versoes[bloco] ?? []
    if (!versoesAbertas[bloco] || pilha.length === 0) return null
    return (
      <div className="mt-3">
        <p className="text-xs text-gray-500">{VERSOES_INTRO}</p>
        <div className="mt-2 space-y-2">
          {pilha.map((versao, i) => (
            <LinkedinVersaoRow
              key={`${bloco}-${i}`}
              versao={versao}
              desabilitado={locksEdicao}
              onRestaurar={() => restaurarBloco(bloco, i)}
            />
          ))}
        </div>
      </div>
    )
  }

  // --- Zone 3 block renderers — BLOCOS_FIXOS order, one function per shape ---

  // Headline / Sobre: plain prose blocks with the shared block anatomy.
  function renderBlocoProsa(bloco: 'headline' | 'sobre') {
    if (!resultado) return null
    const texto = resultado.secoes[bloco]
    const limite = resultado.limites[bloco]
    const pilha = versoes[bloco] ?? []
    return (
      <div className="mt-4 border-t border-gray-200 pt-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS[bloco]}</h4>
          <Badge origem={origens[bloco]} />
        </div>
        {/* Action row (UI-SPEC): Copiar FIRST — the phase's deliverable. */}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          <CopiarButton text={texto} />
          <button
            type="button"
            onClick={() => abrirEditor(bloco)}
            disabled={locksEdicao}
            className={QUIET_BUTTON_CLASSES}
          >
            {EDITAR_SECAO_CTA}
          </button>
          {renderCompararToggle(bloco)}
          {renderVersoesToggle(bloco, pilha.length)}
          {renderDicaToggle(bloco)}
        </div>
        {renderDica(bloco)}
        {editor && editor.bloco === bloco ? (
          renderEditorAqui(bloco, null)
        ) : (
          <p className="mt-2 whitespace-pre-wrap text-sm text-gray-900">{texto}</p>
        )}
        <ContadorLimite limite={limite} />
        {comparacaoAbertas[bloco] && (
          <LinkedinComparisonPanel
            bloco={bloco}
            texto={texto}
            entradas={null}
            perfil={perfilOk.perfil}
            idioma={resultado.idioma}
          />
        )}
        {renderVersoesBloco(bloco)}
      </div>
    )
  }

  // Experiência group (D-09): ONE group action row (the group is the regen
  // unit — one regen call); one sub-block per generated entry ALIGNED TO
  // PROFILE ORDER, each header anchored to the PROFILE FACTS (company —
  // title, run language) — never the generated payload strings. Per-entry
  // footer row: counter first, then Copiar (that entry's descricao ONLY) +
  // Editar entrada. Version stacks are PER ENTRY; the group's single Versões
  // toggle counts them all.
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
    const grupoVersoesCount = entradas.reduce(
      (total, _, i) => total + (versoes[`experiencias-${i}`]?.length ?? 0),
      0,
    )
    return (
      <div className="mt-4 border-t border-gray-200 pt-3">
        <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS.experiencias}</h4>
        {/* ONE group action row — the group is the regen unit. */}
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          {renderCompararToggle('experiencias')}
          {renderVersoesToggle('experiencias', grupoVersoesCount)}
          {renderDicaToggle('experiencias')}
        </div>
        {renderDica('experiencias')}
        <div className="mt-2 space-y-4">
          {entradas.map((entrada, i) => {
            // Index-aligned pairing (06-02 alignment contract); the profile
            // facts win whenever the pairing exists — the LLM strings are
            // display anchors only (fallback for a defensive length drift).
            const perfilExp = perfilExps[i]
            const company = perfilExp ? perfilExp.company : entrada.company
            const title = perfilExp ? tLang(perfilExp.title, resultado.idioma) : entrada.title
            const limite = resultado.limites.experiencias[i]
            const pilhaEntrada = versoes[`experiencias-${i}`] ?? []
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
                {editor &&
                editor.bloco === 'experiencias' &&
                editor.entryIdx === i ? (
                  renderEditorAqui('experiencias', i)
                ) : (
                  <p className="mt-1 whitespace-pre-wrap text-sm text-gray-900">
                    {entrada.descricao}
                  </p>
                )}
                {limite && (
                  <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
                    <CharacterCounter count={limite.tamanho} limite={limite.limite} />
                    <CopiarButton text={entrada.descricao} />
                    <button
                      type="button"
                      onClick={() => abrirEditor('experiencias', i)}
                      disabled={locksEdicao}
                      className={QUIET_BUTTON_CLASSES}
                    >
                      {EDITAR_ENTRADA_CTA}
                    </button>
                  </div>
                )}
                {limite && limite.excesso > 0 && (
                  <p className="mt-1 text-xs text-red-600">
                    {LINKEDIN_OVERLIMIT_FLAG.replace('{excesso}', String(limite.excesso))}
                  </p>
                )}
                {versoesAbertas.experiencias && pilhaEntrada.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {pilhaEntrada.map((versao, j) => (
                      <LinkedinVersaoRow
                        key={`experiencias-${i}-${j}`}
                        versao={versao}
                        desabilitado={locksEdicao}
                        onRestaurar={() => restaurarEntrada(i, j)}
                      />
                    ))}
                  </div>
                )}
              </article>
            )
          })}
        </div>
        {comparacaoAbertas.experiencias && (
          <LinkedinComparisonPanel
            bloco="experiencias"
            texto=""
            entradas={entradas}
            perfil={perfilOk.perfil}
            idioma={resultado.idioma}
          />
        )}
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
    const pilha = versoes.habilidades ?? []
    return (
      <div className="mt-4 border-t border-gray-200 pt-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h4 className={BLOCK_HEADING_CLASSES}>{LINKEDIN_BLOCK_LABELS.habilidades}</h4>
          <Badge origem={origens.habilidades} />
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          <CopiarButton text={skills.join('\n')} />
          <button
            type="button"
            onClick={() => abrirEditor('habilidades')}
            disabled={locksEdicao}
            className={QUIET_BUTTON_CLASSES}
          >
            {EDITAR_SECAO_CTA}
          </button>
          {renderCompararToggle('habilidades')}
          {renderVersoesToggle('habilidades', pilha.length)}
          {renderDicaToggle('habilidades')}
        </div>
        {renderDica('habilidades')}
        {editor && editor.bloco === 'habilidades' ? (
          renderEditorAqui('habilidades', null)
        ) : (
          <>
            {skills.length > 0 && (
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
                {skills.map((skill, i) => (
                  <li key={`${i}-${skill}`}>{skill}</li>
                ))}
              </ol>
            )}
            {/* Count line in the counter slot (UI-SPEC skills-counter exception). */}
            <p className="mt-2 text-xs text-gray-500">
              {formatarSkillsContagem(skills.length)}
            </p>
          </>
        )}
        {comparacaoAbertas.habilidades && (
          <LinkedinComparisonPanel
            bloco="habilidades"
            texto={skills.join('\n')}
            entradas={null}
            perfil={perfilOk.perfil}
            idioma={resultado.idioma}
          />
        )}
        {renderVersoesBloco('habilidades')}
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
            disabled={!ctaHabilitado || locksEdicao}
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
