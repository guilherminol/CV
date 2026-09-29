/**
 * Deterministic suspect-token mechanics for the fact-vs-generated comparison
 * (D-10/D-11, plan 05-03) — PURE functions only: no UI-framework imports,
 * no network calls, no I/O. Output is segmentation DATA (ordered spans),
 * which the
 * ComparisonPanel renders as JSX children — never an HTML string (T-05-09).
 *
 * This module is a mechanical port of the project's already-verified matching
 * mechanics — transcribed, not redesigned (05-PATTERNS §comparison.ts):
 *
 * 1. fold: backend/app/resume/coverage.py lines 33-41 — casefold + NFKD
 *    accent-fold (drop combining marks), applied to BOTH sides, once. JS has
 *    no casefold; toLowerCase is the documented PT-BR/EN approximation.
 * 2. term boundary: coverage.py lines 39-41 — lookaround-bounded
 *    `(?<!\w)term(?!\w)` over the FOLDED term. NEVER word-boundary anchors
 *    (Pitfall 1 of 05-RESEARCH): word-boundary transitions verifiably
 *    false-negative the special-character tech terms ATS users care most
 *    about (C++, C#, .NET, CI/CD) — a term ending in a non-word character
 *    has no such transition against a following space. This is the
 *    empirically verified probe-table conclusion recorded in coverage.py's
 *    docstring; the Python mirror vectors live in
 *    backend/tests/test_comparison_vectors.py.
 * 3. numerals: backend/tests/test_resume_grounding.py lines 146-157 — the
 *    SAME alternation order and boundary structure: AAAA-MM date shape first
 *    (kept whole), then percentages with the sign attached, then plain /
 *    decimal / thousand-grouped numbers; lookarounds both sides so
 *    identifier tails (utf8, v2) never leak phantom numerals.
 *
 * Detection output (suspectTokens) is deterministic suspicion ONLY (D-11) —
 * legitimate paraphrases WILL be flagged, and the user is the judge.
 * Containment semantics follow the grounding prior art
 * (test_resume_grounding.py lines 165-181): folded SUBSTRING containment,
 * not token equality — a generated "2022" is grounded inside facts
 * "2022-03". Canonical vectors (both sides of the port) are pinned in
 * backend/tests/test_comparison_vectors.py.
 */

/** coverage.py `_fold` mirror: fold case + accents (both sides, once). */
export function fold(text: string): string {
  return text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '')
}

/** Python `re.escape` mirror — make every regex metacharacter literal. */
export function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * coverage.py `_term_pattern` mirror: a case-insensitive, lookaround-bounded
 * pattern over the FOLDED term. Lookarounds, never word-boundary anchors
 * (module header — Pitfall 1).
 */
export function termPattern(term: string): RegExp {
  return new RegExp(`(?<!\\w)${escapeRegExp(fold(term))}(?!\\w)`, 'i')
}

/**
 * The grounding prior art's numeral regex (test_resume_grounding.py lines
 * 146-157), transcribed structurally: SAME alternation order (AAAA-MM date
 * first, percentage with the sign attached, plain/grouped/decimal numbers)
 * and the SAME lookarounds both sides — never word-boundary anchors.
 */
const NUMERAL_RE = /(?<!\w)(?:\d{4}-\d{2}|\d+(?:[.,]\d+)*%|\d+(?:[.,]\d+)*)(?!\w)/g

/** Every numeric token: dates whole, % attached, identifier-tail guard. */
export function extractNumerals(text: string): Set<string> {
  return new Set(Array.from(text.matchAll(NUMERAL_RE), (match) => match[0]))
}

/**
 * The grounding prior art's containment semantics (assert_invention_free):
 * folded SUBSTRING containment — a generated "2022" is grounded inside the
 * facts "2022-03". `factsFolded` is fold(factsBlob) computed once by the
 * caller; `token` is folded here (both sides folded exactly once, like
 * coverage.py).
 */
export function foldContains(factsFolded: string, token: string): boolean {
  return factsFolded.includes(fold(token))
}

// --- suspect-token categories (05-RESEARCH §Pattern 3, D-10) ---

/**
 * One candidate token: an optional leading dot (the ".NET" shape), then a
 * letter/digit head, then letters/digits plus the tech-shape punctuation
 * (+ # . / -), e.g. "C++", "CI/CD", "Node.js", "pós-graduação".
 */
const CANDIDATE_TOKEN_RE = /\.?[\p{L}\p{N}][\p{L}\p{N}+#./-]*/gu

const SENTENCE_BOUNDARY_CHARS = new Set(['.', '!', '?', ':', ';', '\n'])

function isSentenceInitial(text: string, start: number): boolean {
  if (start === 0) return true
  let i = start - 1
  while (i >= 0 && /\s/.test(text.charAt(i))) i -= 1
  if (i < 0) return true
  return SENTENCE_BOUNDARY_CHARS.has(text.charAt(i))
}

/**
 * Tech-shape: letters mixed with digits or the tech punctuation (+ # . /) —
 * the C++ / .NET / CI/CD / utf8 shapes. A plain hyphen does NOT qualify
 * (hyphenated prose like "e-mail" would fabricate suspects).
 */
function isTechShape(token: string): boolean {
  return /\p{L}/u.test(token) && /[\d+#./]/.test(token)
}

/**
 * Trim trailing sentence punctuation and keep a leading dot ONLY for the
 * ".NET" all-caps shape — a stray sentence period or ellipsis before a word
 * must not fabricate a phantom token.
 */
function normalizeCandidate(raw: string): string {
  let token = raw
  while (token.length > 1 && /[.\-/]$/.test(token)) token = token.slice(0, -1)
  if (token.startsWith('.')) {
    const rest = token.slice(1)
    if (!/^\p{Lu}+$/u.test(rest)) token = rest
  }
  return token
}

interface CandidateToken {
  token: string
  candidate: boolean
}

function candidateTokens(text: string): CandidateToken[] {
  const out: CandidateToken[] = []
  for (const match of text.matchAll(CANDIDATE_TOKEN_RE)) {
    const token = normalizeCandidate(match[0])
    if (!token) continue
    const nomeProprio = /^\p{Lu}/u.test(token) && !isSentenceInitial(text, match.index ?? 0)
    out.push({ token, candidate: nomeProprio || isTechShape(token) })
  }
  return out
}

/**
 * The section's deterministic suspect set (D-10): numerals not fold-contained
 * in `factsBlob` (the section's source-facts blob) plus named-entity
 * candidates (capitalized tokens that are not sentence-initial) and
 * tech-shape tokens not fold-matched in `factInventory` — the profile-derived
 * inventory (skill items, project technologies, certification names,
 * companies, institutions, job titles). No LLM judge anywhere (D-10); the
 * output is suspicion, never a verdict (D-11).
 */
export function suspectTokens(
  sectionText: string,
  factsBlob: string,
  factInventory: string,
): Set<string> {
  const suspects = new Set<string>()
  if (!sectionText) return suspects
  const factsFolded = fold(factsBlob)
  const inventoryFolded = fold(factInventory)

  // Category 1 — numerals: folded SUBSTRING containment against the source
  // facts (assert_invention_free semantics).
  for (const token of extractNumerals(sectionText)) {
    if (!foldContains(factsFolded, token)) suspects.add(token)
  }

  // Categories 2+3 — entities/tech vs the inventory: lookaround-bounded fold
  // matching (coverage.py mechanics; word-boundary anchors would silently
  // miss C++/.NET/CI-CD).
  for (const { token, candidate } of candidateTokens(sectionText)) {
    if (!candidate) continue
    if (!termPattern(token).test(inventoryFolded)) suspects.add(token)
  }
  return suspects
}

/** One ordered span of the segmented text. */
export interface TextSegment {
  text: string
  suspect: boolean
}

/**
 * Ordered {text, suspect} spans covering `text` exactly once: every
 * occurrence of every suspect token becomes one suspect segment (adjacent/
 * overlapping occurrences merge). Matching uses the same lookaround-bounded
 * mechanics over the ORIGINAL text (suspects are extracted from it), so
 * segments carry the verbatim source characters — segmentation DATA for JSX
 * rendering, never an HTML string (T-05-09).
 */
export function segmentText(text: string, suspects: Iterable<string>): TextSegment[] {
  if (!text) return []
  const ranges: Array<[number, number]> = []
  for (const suspect of suspects) {
    if (!suspect) continue
    const pattern = new RegExp(`(?<!\\w)${escapeRegExp(suspect)}(?!\\w)`, 'gi')
    for (const match of text.matchAll(pattern)) {
      const start = match.index ?? 0
      ranges.push([start, start + match[0].length])
    }
  }
  if (ranges.length === 0) return [{ text, suspect: false }]
  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1])
  const segments: TextSegment[] = []
  let cursor = 0
  for (const [start, end] of ranges) {
    if (end <= cursor) continue
    const from = Math.max(start, cursor)
    if (from > cursor) segments.push({ text: text.slice(cursor, from), suspect: false })
    segments.push({ text: text.slice(from, end), suspect: true })
    cursor = end
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), suspect: false })
  return segments
}
