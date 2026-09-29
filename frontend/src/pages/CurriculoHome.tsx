import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  downloadPdf,
  exportarCurriculo,
  fetchProfile,
  fetchResumeLint,
  gerarCurriculo,
  regenerarSecao,
  type ExperienciaGeradaDTO,
  type GerarResponse,
  type ResumeLanguage,
  type SecaoId,
  type SecoesDTO,
  type SelfCheckDTO,
} from '../api/client'
import { ErrorPanel } from '../components/ErrorPanel'
import { ExportZone } from '../components/ExportZone'
import { KeywordsPanel } from '../components/KeywordsPanel'
import { LintPanel, type LintOk } from '../components/LintPanel'
import { PlaceholderBanner } from '../components/PlaceholderBanner'
import { ResumeResult } from '../components/ResumeResult'
import { SelfCheckPanel } from '../components/SelfCheckPanel'
import { StatusLine } from '../components/StatusLine'
import type { OrigemBadge, SectionVersion } from '../components/SectionVersionsPanel'
import { dividirLinhas, textoEditorValido, type SecaoEditorState } from '../components/SectionEditor'
import {
  CURRICULO_CTA,
  CURRICULO_CTA_INFLIGHT,
  CURRICULO_EMPTY_BODY,
  CURRICULO_EMPTY_TITLE,
  CURRICULO_ERROR_HINT,
  CURRICULO_ERROR_RETRY,
  CURRICULO_ERROR_TITLE,
  CURRICULO_IDIOMA_LABEL,
  CURRICULO_IDIOMA_OPTIONS,
  CURRICULO_INFLIGHT_HINT,
  CURRICULO_LINT_FETCH_ERRO,
  CURRICULO_JD_LABEL,
  CURRICULO_JD_PLACEHOLDER,
  CURRICULO_JD_TOO_SHORT_HINT,
  CURRICULO_PAGE_TITLE,
  EXPORTAR_INFLIGHT_HINT,
  PERFIL_ERROR_TITLE,
  PERFIL_LOADING,
  PRIMARY_BUTTON_CLASSES,
  TEXTAREA_CLASSES,
} from '../constants/ui'

type GerarOk = Extract<GerarResponse, { status: 'ok' }>

// --- inline editing / version stack (plan 05-02, D-01/D-04/D-08/D-12) ---
// Session React state ONLY — no persistence layer, no shadow copy of
// resultado.secoes (D-01); a refresh returns to the last generated result.

const JD_MIN_CHARS = 80 // boundary: exactly 80 trimmed chars enable CTA + lint query
const DEBOUNCE_MS = 800 // one lint call per settled typing state (T-03-10 bound)

// Pinned class strings from the UI-SPEC Component conventions (plan 03-04).
// PRIMARY_BUTTON_CLASSES + TEXTAREA_CLASSES live in constants/ui.ts — single
// definitions shared with ExportZone / SectionEditor (IN-04).
const CARD_CLASSES = 'rounded-md border border-gray-200 bg-white shadow-sm p-4'
const SECONDARY_BUTTON_CLASSES =
  'min-h-10 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50'
const IDIOMA_SELECTED_CLASSES =
  'cursor-pointer rounded bg-white px-3 py-1 text-sm font-semibold text-blue-600 shadow-sm has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'
const IDIOMA_UNSELECTED_CLASSES =
  'cursor-pointer rounded px-3 py-1 text-sm text-gray-600 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-blue-600'

type SectionValor = SecoesDTO[SecaoId]

/**
 * Editor draft → the section's stored value shape (UI-SPEC D-12 granularity):
 * Resumo replaces the string whole; Experiência replaces ONLY entry
 * `entryIdx`'s bullets (company/title stay fixed — they are the profile-fact
 * anchor of the comparison); Habilidades is one skill per line. Lines are
 * split, trimmed, and emptied-out to match the export envelope's
 * min_length=1 contract. The draft never touches profile files (D-01).
 */
function valorDeRascunho(
  secoes: SecoesDTO,
  secao: SecaoId,
  entryIdx: number | null,
  draft: string,
): SectionValor {
  if (secao === 'resumo') return draft
  if (secao === 'habilidades') return dividirLinhas(draft)
  const alvo = entryIdx ?? 0
  return secoes.experiencias.map((exp, i) =>
    i === alvo ? { ...exp, bullets: dividirLinhas(draft) } : exp,
  )
}

/** Write a stored value back into the displayed secoes (typed per section). */
function secoesComValor(secoes: SecoesDTO, secao: SecaoId, valor: SectionValor): SecoesDTO {
  if (secao === 'resumo') return { ...secoes, resumo: valor as string }
  if (secao === 'habilidades') return { ...secoes, habilidades: valor as string[] }
  return { ...secoes, experiencias: valor as ExperienciaGeradaDTO[] }
}

/**
 * The Currículo screen (plans 03-04 + 04-03): paste JD → choose language →
 * JD-tied lint (≥80 debounced chars) → generate → assembled result + honest
 * coverage → export + ATS self-check. State machine: idle → typing → in-flight
 * → result (zones 4–5; the form stays at top for edits) → exporting (controls
 * locked symmetrically) → result+checked (receipt + panel) or result+export-
 * error (prior checked state preserved). Failure never blanks the page — any
 * prior result stays mounted. Generated content and export state are React
 * state only (D-06/D-16 ephemeral); a refresh returns to idle/unexported. All
 * renders are JSX text children — no raw-HTML path (T-03-08 posture).
 */
export default function CurriculoHome() {
  // Profile gate — the SAME ['perfil'] query PerfilHome uses; React Query dedupes.
  const perfilQuery = useQuery({ queryKey: ['perfil'], queryFn: fetchProfile })

  // Zone 1 inputs: raw JD + run language. The debounced copy drives the lint query.
  const [jdText, setJdText] = useState('')
  const [debouncedJd, setDebouncedJd] = useState('')
  const [idioma, setIdioma] = useState<ResumeLanguage>('pt-BR')
  // Zone 4/5: last successful generate response — session state only (D-06).
  const [resultado, setResultado] = useState<GerarOk | null>(null)
  // Generation failure (erro envelope lines, or [] for a thrown fetch failure).
  const [gerarErros, setGerarErros] = useState<string[] | null>(null)
  // Zone 6 export state — React session state only (D-16 ephemeral, like D-06):
  // a refresh returns to the unexported result state.
  const [receiptFilename, setReceiptFilename] = useState<string | null>(null)
  const [selfcheck, setSelfcheck] = useState<SelfCheckDTO | null>(null)
  // Export failure (backend PT-BR lines, or [] for a thrown fetch failure).
  const [exportarErros, setExportarErros] = useState<string[] | null>(null)
  // Zone 4 per-section regen state (plan 05-01, session-only like D-06):
  // the steering hint (D-05) + its on-demand toggle live per section and
  // persist across that section's regens until the result is replaced.
  const [dicas, setDicas] = useState<Record<SecaoId, string>>({
    resumo: '',
    experiencias: '',
    habilidades: '',
  })
  const [dicaAberta, setDicaAberta] = useState<Record<SecaoId, boolean>>({
    resumo: false,
    experiencias: false,
    habilidades: false,
  })
  // Per-section last failed regen: backend PT-BR lines verbatim, or [] for a
  // fetch-level failure (generic hint path). Key absent/undefined = no error.
  const [regenErros, setRegenErros] = useState<Partial<Record<SecaoId, string[]>>>({})
  // Per-section version stacks (D-08, session-only like D-01/D-06): EVERY
  // destructive path — edit save, section regen success, restore, confirmed
  // full regen — pushes the current displayed text + badge origin here FIRST
  // via empilharVersaoAtual. Newest first; never capped (single-user
  // localhost session), never silently dropped.
  const [versoes, setVersoes] = useState<Record<SecaoId, SectionVersion[]>>({
    resumo: [],
    experiencias: [],
    habilidades: [],
  })
  // Per-section Versoes disclosure state (read-only — usable even while a
  // long op is pending, per the UI-SPEC locking matrix).
  const [versoesAbertas, setVersoesAbertas] = useState<Record<SecaoId, boolean>>({
    resumo: false,
    experiencias: false,
    habilidades: false,
  })
  // Badge origin per generated section (D-04 tri-state): 'gerado' at
  // mount/regen, 'editado' after a save or the restore of an edited version.
  const [origens, setOrigens] = useState<Record<SecaoId, OrigemBadge>>({
    resumo: 'gerado',
    experiencias: 'gerado',
    habilidades: 'gerado',
  })
  // The ONE open inline editor (D-12): which section/entry + the textarea
  // draft. Dirty is DERIVED (draft !== inicial) — never stored. The draft
  // lives at page level so the D-14 regen-over-edit confirm can stack it
  // before the editor closes.
  const [editor, setEditor] = useState<SecaoEditorState | null>(null)
  // Pending D-14 confirm strips (plan 05-02 Task 3): which section's
  // regen-over-edit strip is showing + whether the full-regen-with-edits
  // strip is showing. The amber strips ARE the confirmation UI — never a
  // browser dialog.
  const [stripRegen, setStripRegen] = useState<SecaoId | null>(null)
  const [stripGerarCompleta, setStripGerarCompleta] = useState(false)
  // Transient flag carried from the strip confirm to gerar's onSuccess: the
  // confirmed full regen stacks EVERY section's current text before the
  // wholesale swap. Reset on every terminal path (ok/erro/fetch-error).
  const gerarConfirmadoRef = useRef(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedJd(jdText), DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [jdText])

  const trimmed = jdText.trim()
  const debouncedTrimmed = debouncedJd.trim()
  const lintReady = debouncedTrimmed.length >= JD_MIN_CHARS

  // Zone 2 query: fires only once the DEBOUNCED JD reaches 80 trimmed chars —
  // one real LLM call per settled state, never per keystroke.
  const lintQuery = useQuery({
    queryKey: ['resume-lint', debouncedTrimmed],
    queryFn: () => fetchResumeLint(debouncedTrimmed),
    enabled: lintReady,
  })

  const gerar = useMutation({
    mutationFn: gerarCurriculo,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        // D-14 (confirmed full regen): stack EVERY section's current
        // displayed text + badge origin FIRST — each version stays guardada
        // em Versões across the wholesale swap (the stacks persist; the
        // badges reset to Gerado below).
        if (gerarConfirmadoRef.current) {
          gerarConfirmadoRef.current = false
          empilharVersaoAtual('resumo')
          empilharVersaoAtual('experiencias')
          empilharVersaoAtual('habilidades')
        }
        // Regeneration reset (UI-SPEC): the prior exported PDF no longer matches
        // the displayed resume — clear the receipt + self-check panel + export
        // errors BEFORE mounting the new result. The export CTA stays available.
        setReceiptFilename(null)
        setSelfcheck(null)
        setExportarErros(null)
        setResultado(data)
        setGerarErros(null)
        // A replaced result invalidates the per-section regen state (UI-SPEC
        // hint lifecycle: the dica persists until cleared or replaced).
        setDicas({ resumo: '', experiencias: '', habilidades: '' })
        setDicaAberta({ resumo: false, experiencias: false, habilidades: false })
        setVersoesAbertas({ resumo: false, experiencias: false, habilidades: false })
        setRegenErros({})
        // Badge lifecycle (UI-SPEC): full regen sets all three to Gerado.
        setOrigens({ resumo: 'gerado', experiencias: 'gerado', habilidades: 'gerado' })
        // No editor can be open (the action disables itself) and no strip
        // survives a concluded full regen — clear defensively anyway.
        setEditor(null)
        setStripRegen(null)
        setStripGerarCompleta(false)
      } else {
        // 200-envelope erro: backend PT-BR lines, rendered verbatim below.
        gerarConfirmadoRef.current = false
        setGerarErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down): fail-loud panel + retry, prior
      // result stays mounted. Raw detail is in the uvicorn terminal only.
      gerarConfirmadoRef.current = false
      setGerarErros([])
    },
  })

  // Per-section regeneration (plan 05-01, SC1/D-06/D-07): the response's FULL
  // merged secoes replaces the displayed state WHOLESALE — no client-side
  // merge — and the recomputed cobertura/cobertura_resumo swap into Zone 5
  // from the same response (chips never silently stale after a regen).
  const regenerar = useMutation({
    mutationFn: regenerarSecao,
    onSuccess: (data, variables) => {
      // The pending D-14 confirm (if any) concluded with this attempt.
      setStripRegen(null)
      if (data.status === 'ok') {
        // SC4 (plan 05-02, D-08): stack the pre-regen displayed version FIRST
        // — the swap below is destructive, and the prior text + its badge
        // origin must already be on the version stack when it happens.
        empilharVersaoAtual(variables.secao)
        // Export-state reset FIRST (UI-SPEC, mirrors the gerar pattern): the
        // prior exported PDF no longer matches the displayed resume — clear
        // the receipt + self-check panel + export errors BEFORE mounting the
        // new displayed state.
        setReceiptFilename(null)
        setSelfcheck(null)
        setExportarErros(null)
        setResultado((prev) =>
          prev
            ? {
                ...prev,
                secoes: data.secoes,
                cobertura: data.cobertura,
                cobertura_resumo: data.cobertura_resumo,
              }
            : prev,
        )
        // Badge lifecycle (UI-SPEC): regen success → 'gerado'.
        setOrigens((prev) => ({ ...prev, [variables.secao]: 'gerado' }))
        // The regen replaced the section under any editor open on it — close
        // that editor rather than let it save a stale draft over the new
        // text (a silent-overwrite hazard).
        setEditor((prev) => (prev && prev.secao === variables.secao ? null : prev))
        setRegenErros((prev) => ({ ...prev, [variables.secao]: undefined }))
      } else {
        // 200-envelope erro: the PT-BR lines surface inside the OWNING
        // section (section-scoped red panel); prior text stays mounted.
        setRegenErros((prev) => ({ ...prev, [variables.secao]: data.erros }))
      }
    },
    onError: (_error, variables) => {
      // Fetch-level failure (server down): same section-scoped panel with the
      // generic erros=[] hint. Raw detail is in the uvicorn terminal only.
      setRegenErros((prev) => ({ ...prev, [variables.secao]: [] }))
    },
  })

  // Zone 6 export (D-07/D-11/D-13): ONE POST drives all three effects — the
  // automatic download starts from this response's bytes, the green receipt
  // names the backend filename, the self-check panel mounts. Erro paths NEVER
  // clear receiptFilename/selfcheck (a failure never blanks prior checked state).
  const exportar = useMutation({
    mutationFn: exportarCurriculo,
    onSuccess: (data) => {
      if (data.status === 'ok') {
        downloadPdf(data.pdf_base64, data.filename)
        setReceiptFilename(data.filename)
        setSelfcheck(data.selfcheck)
        setExportarErros(null)
      } else {
        // Gate failure (D-08): no file was delivered — backend PT-BR lines
        // naming the failed check, rendered verbatim by ExportZone.
        setExportarErros(data.erros)
      }
    },
    onError: () => {
      // Fetch-level failure (server down): same panel, generic hint (the
      // erros=[] Phase 3 convention). Raw detail is terminal-only.
      setExportarErros([])
    },
  })

  function gerarAgora() {
    gerar.mutate({ jd_text: trimmed, language: idioma })
  }

  // D-14 gate for the FULL regen (header button + Zone 1 form CTA — both
  // replace the mounted result): with any Editado section it asks ONCE via
  // the amber strip under the card header; unchanged no-confirm behavior
  // when nothing is Editado and no editor is open (Phase 3 contract). While
  // any editor is open the action is disabled outright — it would replace
  // sections under the open editor (the button is disabled; guard here too).
  function tentarGerarCompleta() {
    if (editor) return
    const temEdicao =
      origens.resumo === 'editado' ||
      origens.experiencias === 'editado' ||
      origens.habilidades === 'editado'
    if (temEdicao) {
      setStripGerarCompleta(true)
      return
    }
    gerarAgora()
  }

  // Confirmed full regen: the flag rides to gerar.onSuccess, which stacks
  // every section's current text before the swap (nothing silently lost).
  function confirmarGerarCompleta() {
    gerarConfirmadoRef.current = true
    setStripGerarCompleta(false)
    gerarAgora()
  }

  function cancelarGerarCompleta() {
    setStripGerarCompleta(false)
  }

  // D-14 gate (plan 05-02 Task 3): Regenerar seção on a section whose badge
  // is Editado, or whose open editor is DIRTY, renders the inline amber
  // confirm strip first — never a browser dialog. A clean open editor or a
  // Gerado badge regenerates directly.
  function tentarRegenerarSecao(secao: SecaoId) {
    if (!resultado) return
    const suja = editor !== null && editor.secao === secao && editor.draft !== editor.inicial
    if (origens[secao] === 'editado' || suja) {
      setStripRegen(secao)
      return
    }
    regenerarSecaoAgora(secao)
  }

  // Regenerar mesmo assim: a dirty open draft is stacked FIRST as an
  // 'editado' version (it would otherwise be lost when the editor closes —
  // empty drafts are skipped: nothing of value), then the editor closes and
  // the request issues; the regen-success handler stacks the DISPLAYED text
  // before its swap.
  function confirmarRegenSobreEdicao(secao: SecaoId) {
    if (!resultado) return
    if (
      editor &&
      editor.secao === secao &&
      editor.draft !== editor.inicial &&
      textoEditorValido(editor.secao, editor.draft)
    ) {
      empilharValor(secao, valorDeRascunho(resultado.secoes, editor.secao, editor.entryIdx, editor.draft), 'editado')
    }
    setEditor(null)
    setStripRegen(null)
    regenerarSecaoAgora(secao)
  }

  function cancelarStripRegen() {
    setStripRegen(null)
  }

  // Regenerate ONE section from the CURRENT displayed state + form inputs
  // (jd_text/language) + that section's persisted dica (D-05). The response's
  // merged secoes replaces the state wholesale in onSuccess — nothing merges
  // client-side. (An empty dica key is dropped inside regenerarSecao.)
  function regenerarSecaoAgora(secao: SecaoId) {
    if (!resultado) return
    regenerar.mutate({
      jd_text: trimmed,
      language: idioma,
      secao,
      secoes: resultado.secoes,
      keywords: resultado.keywords,
      dica: dicas[secao],
    })
  }

  // Which section's regen is in flight (null = none) — the mutation carries
  // exactly one request at a time (UI-SPEC: one long operation at a time).
  const secaoRegenerando: SecaoId | null =
    regenerar.isPending && regenerar.variables ? regenerar.variables.secao : null

  // --- inline editing + SC4 version stack (plan 05-02) ---

  // SC4/D-08 stack-before-mutate invariant: ONE helper at the TOP of every
  // destructive path (edit save below, section regen success in the regenerar
  // mutation, restore, confirmed full regen) — pushes the section's CURRENT
  // displayed text + badge origin onto its version stack before any write,
  // so nothing is ever silently destroyed. Long-op locks guarantee the
  // displayed state cannot change between mutate() and onSuccess, so the
  // closure reads below are always the texts being replaced.
  function empilharValor(secao: SecaoId, valor: SectionValor, origem: OrigemBadge) {
    setVersoes((prev) => ({ ...prev, [secao]: [{ secao, origem, valor }, ...prev[secao]] }))
  }

  function empilharVersaoAtual(secao: SecaoId) {
    if (!resultado) return
    empilharValor(secao, resultado.secoes[secao], origens[secao])
  }

  // Open the inline editor (D-12) pre-filled from the DISPLAYED text, at the
  // UI-SPEC granularity: Resumo whole string; Experiência per entry (bullets
  // one per line); Habilidades one skill per line. One editor at a time.
  function abrirEditor(secao: SecaoId, entryIdx: number | null = null) {
    if (!resultado || editor) return
    let inicial: string
    if (secao === 'resumo') inicial = resultado.secoes.resumo
    else if (secao === 'habilidades') inicial = resultado.secoes.habilidades.join('\n')
    else inicial = resultado.secoes.experiencias[entryIdx ?? 0]?.bullets.join('\n') ?? ''
    setEditor({ secao, entryIdx, draft: inicial, inicial })
  }

  // Edit save (D-12/D-04): stack the pre-edit version FIRST (SC4), run the
  // export-state reset triple (the prior PDF no longer matches), write the
  // edited text into resultado.secoes (the single displayed-state source —
  // export and self-check consume it with zero extra steps, D-03), flip the
  // badge to Editado, close the editor. Cobertura chips stay untouched
  // (gerar-time snapshot rule — only regen success swaps them).
  function salvarEdicao() {
    if (!editor || !resultado) return
    if (!textoEditorValido(editor.secao, editor.draft)) return // guard paranoia (button already disabled)
    const { secao, entryIdx, draft } = editor
    empilharVersaoAtual(secao)
    setReceiptFilename(null)
    setSelfcheck(null)
    setExportarErros(null)
    const valor = valorDeRascunho(resultado.secoes, secao, entryIdx, draft)
    setResultado((prev) =>
      prev ? { ...prev, secoes: secoesComValor(prev.secoes, secao, valor) } : prev,
    )
    setOrigens((prev) => ({ ...prev, [secao]: 'editado' }))
    setEditor(null)
  }

  // Cancel/discard: the SectionEditor gates a DIRTY cancel behind its inline
  // ConfirmStrip; by the time this runs the user confirmed (or was clean).
  function fecharEditor() {
    setEditor(null)
  }

  // Restore (D-08/SC4): stack the CURRENT displayed version FIRST, then mount
  // the chosen version (removed from the stack — not duplicated) and adopt
  // its origin badge; then the export-state reset triple. Coverage chips stay
  // untouched (gerar-time snapshot rule — restores never recompute coverage).
  function restaurar(secao: SecaoId, indice: number) {
    if (!resultado) return
    const alvo = versoes[secao][indice]
    if (!alvo) return
    empilharVersaoAtual(secao)
    // empilharVersaoAtual PREPENDS the current text, shifting the restored
    // entry down by one — remove it at indice + 1 (queued updaters apply in
    // order: prepend, then filter).
    setVersoes((prev) => ({ ...prev, [secao]: prev[secao].filter((_, i) => i !== indice + 1) }))
    setResultado((prev) =>
      prev ? { ...prev, secoes: secoesComValor(prev.secoes, secao, alvo.valor) } : prev,
    )
    setOrigens((prev) => ({ ...prev, [secao]: alvo.origem }))
    setReceiptFilename(null)
    setSelfcheck(null)
    setExportarErros(null)
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

  const lintOk: LintOk | null =
    lintQuery.data && lintQuery.data.status === 'ok' ? lintQuery.data : null

  // Narrowed ok payload (guaranteed by the early returns above), captured as a
  // const so the Zone 6 export callback closes over a stable, typed value —
  // TS narrowing does not persist into closures over mutable query objects.
  const perfilOk = perfilQuery.data

  // Derived locking booleans (UI-SPEC interaction table — the single source;
  // no ad-hoc scattered disabled logic):
  //  - operacaoLongaPendente: ANY long op (full gerar, section regen, export)
  //    disables Regenerar seção / Gerar novamente / Exportar PDF / edit
  //    controls / Restaurar versão / dica toggle+input, while Comparar and
  //    Versões toggles stay usable read-only.
  //  - locksEdicao: additionally, an open editor disables every edit
  //    affordance + Exportar PDF + Gerar novamente + every Restaurar versão,
  //    while Regenerar seção stays enabled (own section routes through the
  //    D-14 strip; sibling regens do not touch the open editor).
  const operacaoLongaPendente = gerar.isPending || exportar.isPending || regenerar.isPending
  const locksEdicao = editor !== null || operacaoLongaPendente

  return (
    <div className="space-y-6">
      <StatusLine ok={true} />
      {perfilQuery.data.exemplo && <PlaceholderBanner />}
      <h2 className="text-xl font-semibold text-gray-900">{CURRICULO_PAGE_TITLE}</h2>

      {!resultado && !gerar.isPending && (
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-gray-900">{CURRICULO_EMPTY_TITLE}</h3>
          <p className="text-sm text-gray-600">{CURRICULO_EMPTY_BODY}</p>
        </div>
      )}

      {/* Zone 1 — form card */}
      <form
        className={CARD_CLASSES}
        onSubmit={(event) => {
          event.preventDefault()
          tentarGerarCompleta()
        }}
      >
        <div className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="jd-textarea" className="block text-sm font-semibold text-gray-900">
              {CURRICULO_JD_LABEL}
            </label>
            <textarea
              id="jd-textarea"
              value={jdText}
              onChange={(event) => setJdText(event.target.value)}
              placeholder={CURRICULO_JD_PLACEHOLDER}
              className={TEXTAREA_CLASSES}
            />
            {trimmed.length < JD_MIN_CHARS && (
              <p className="text-xs text-gray-500">{CURRICULO_JD_TOO_SHORT_HINT}</p>
            )}
          </div>

          <fieldset>
            <legend className="text-sm font-semibold text-gray-900">{CURRICULO_IDIOMA_LABEL}</legend>
            <div className="mt-2 inline-flex rounded-md border border-gray-300 bg-gray-50 p-1">
              {(Object.keys(CURRICULO_IDIOMA_OPTIONS) as ResumeLanguage[]).map((lang) => (
                <label
                  key={lang}
                  className={idioma === lang ? IDIOMA_SELECTED_CLASSES : IDIOMA_UNSELECTED_CLASSES}
                >
                  <input
                    type="radio"
                    name="idioma"
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
            disabled={trimmed.length < JD_MIN_CHARS || locksEdicao}
            className={PRIMARY_BUTTON_CLASSES}
          >
            {gerar.isPending ? CURRICULO_CTA_INFLIGHT : CURRICULO_CTA}
          </button>
        </div>
      </form>

      {/* Zone 2 — lint panel: pending renders nothing (the form stays primary). */}
      {lintReady && lintQuery.data && lintQuery.data.status === 'ok' && <LintPanel resultado={lintOk} />}
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
      {/* WR-02: fetch-level failure (server down / non-200 → lintQuery.isError)
          renders the SAME fail-loud red-panel convention as gerar/exportar —
          generic PT-BR hint, raw detail terminal-only. Never silent. */}
      {lintReady && lintQuery.isError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{CURRICULO_LINT_FETCH_ERRO}</p>
        </div>
      )}

      {/* Zones 3/4/5/6 — one aria-live region: in-flight hints, error panels,
          result, export control + self-check. */}
      <div aria-live="polite" className="space-y-6">
        {gerar.isPending && <p className="text-sm text-gray-600">{CURRICULO_INFLIGHT_HINT}</p>}
        {exportar.isPending && <p className="text-sm text-gray-600">{EXPORTAR_INFLIGHT_HINT}</p>}

        {gerarErros !== null && !gerar.isPending && (
          <section
            aria-labelledby="gerar-error-title"
            className="rounded-md border border-red-300 bg-red-50 px-4 py-3"
          >
            <h3 id="gerar-error-title" className="font-semibold text-red-700">
              {CURRICULO_ERROR_TITLE}
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
            {/* Zone 4 — assembled card from the shared ['perfil'] data + the
                generate response; Zone 6 (export + self-check) stacks directly
                below the artifact it exports (D-09); Zone 5 closes the page. */}
            <ResumeResult
              perfil={perfilQuery.data.perfil}
              secoes={resultado.secoes}
              idioma={resultado.idioma}
              onRegenerar={tentarGerarCompleta}
              regenerando={operacaoLongaPendente}
              onRegenerarSecao={tentarRegenerarSecao}
              stripRegen={stripRegen}
              onConfirmarStripRegen={confirmarRegenSobreEdicao}
              onCancelarStripRegen={cancelarStripRegen}
              stripGerarCompleta={stripGerarCompleta}
              onConfirmarGerarCompleta={confirmarGerarCompleta}
              onCancelarGerarCompleta={cancelarGerarCompleta}
              secaoRegenerando={secaoRegenerando}
              regenErros={regenErros}
              dicas={dicas}
              onDicaChange={(secao, valor) => setDicas((prev) => ({ ...prev, [secao]: valor }))}
              dicaAberta={dicaAberta}
              onDicaToggle={(secao) => setDicaAberta((prev) => ({ ...prev, [secao]: !prev[secao] }))}
              versoes={versoes}
              versoesAbertas={versoesAbertas}
              onVersoesToggle={(secao) => setVersoesAbertas((prev) => ({ ...prev, [secao]: !prev[secao] }))}
              onRestaurar={restaurar}
              origens={origens}
              editor={editor}
              locksEdicao={locksEdicao}
              onAbrirEditor={(secao, entryIdx) => abrirEditor(secao, entryIdx ?? null)}
              onDraftChange={(valor) => setEditor((prev) => (prev ? { ...prev, draft: valor } : prev))}
              onSalvarEdicao={salvarEdicao}
              onCancelarEdicao={fecharEditor}
            />
            <ExportZone
              onExportar={() =>
                exportar.mutate({
                  perfil: perfilOk.perfil,
                  secoes: resultado.secoes,
                  keywords: resultado.keywords,
                  idioma: resultado.idioma,
                })
              }
              exporting={exportar.isPending}
              ctaDisabled={locksEdicao}
              receiptFilename={receiptFilename}
              erros={exportarErros}
            />
            {selfcheck && (
              <SelfCheckPanel
                selfcheck={selfcheck}
                keywords={resultado.keywords}
                idioma={resultado.idioma}
              />
            )}
            <KeywordsPanel
              keywords={resultado.keywords}
              cobertura={resultado.cobertura}
              cobertura_resumo={resultado.cobertura_resumo}
              idioma={resultado.idioma}
            />
          </>
        )}
      </div>
    </div>
  )
}
