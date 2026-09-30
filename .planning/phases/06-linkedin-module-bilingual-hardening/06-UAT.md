---
status: testing
phase: 6-LinkedIn Module + Bilingual Hardening
source: [06-VERIFICATION.md]
started: 2026-09-30T00:00:00Z
updated: 2026-09-30T00:00:00Z
---

> **Validation mode:** agent-executed UAT (autonomous run convention, per Phases 4/5). Exercised
> by the orchestrator via real browser automation against the live app (restarted on the
> phase-6 build). Re-run `/gsd-verify-work 6` anytime to re-validate by hand.

## Tests

### 1. Copy-paste UX — clipboard equality per block
expected: "Copiar" on a block puts exactly the displayed text on the clipboard; feedback "Copiado!" shows.
result: [pending]

### 2. Counters + over-limit path
expected: Live counter "X/Y caracteres" per limited block; amber ≥90%, red over limit; an over-limit edit is flagged and the save is guarded — nothing silently truncated.
result: [pending]

### 3. QA panel framing — "Verificação de idioma"
expected: PT-BR generation shows the QA panel with glossário/bleed blocks (loud zero lines when clean), non-blocking framing; EN runs show the neutral note.
result: [pending]

### 4. Page-flow smoke — refresh returns to clean start
expected: The policy/ephemeral line is visible; refreshing returns to the pre-result state (no persistence).
result: [pending]

### 5. Max-volume readability backstop
expected: With editor/comparison/QA disclosures open the page stays readable — zones separated, vertical growth only.
result: [pending]

### 6. OPERATOR ITEM (not agent-executable): full-file `-m llm` DoD re-run
expected: With OpenRouter credits topped up, `cd backend && uv run pytest tests/test_llm_harness.py -m llm -q` runs the full harness green. The phase's own bilingual LinkedIn DoD fixtures already PASSED (06-05, both labels, 64s); the full-file re-run failed on 402 Payment Required (credits exhausted) — WINDOWS.md entry 10.
result: [pending — requires user credit top-up: https://openrouter.ai/settings/credits]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
