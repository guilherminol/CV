---
status: testing
phase: 07-application-tracker-pipeline-follow-up
source: [07-VERIFICATION.md]
started: 2026-11-11T12:20:00Z
updated: 2026-11-11T12:20:00Z
---

## Current Test

number: 1
name: Kanban drag + persistence + empty-column drop (D-14)
expected: |
  Create 2-3 candidaturas across stages; drag a card from one stage column to another; reload the page: the card renders in the new column (persisted, not optimistic-only); drag a card into an EMPTY column: the drop is accepted and persists; same-stage visual sorts do not fire writes.
awaiting: user response

## Tests

### 1. Kanban drag + persistence + empty-column drop (D-14)
expected: Persisted stage after reload (not optimistic-only); empty-column drop accepted; same-stage visual sorts do not fire writes.
result: [pending]

### 2. Keyboard-only DnD + click survival (D-14 / Pitfall 4)
expected: Tab to a card's drag handle, activate, arrow-key it to another column, release — same persistence as check 1; then click a card body: its detail opens (clicks survive the distance-8 pointer sensor).
result: [pending]

### 3. Amber/red prazo highlights (D-09/D-11)
expected: One candidatura prazo 2 days out, one prazo last week: overview shows "vence em 2 dias" (amber family) and "venceu há 1 dia" (red family); sr-only suffix present; the overdue item triggered NO automatic stage change or archival.
result: [pending]

### 4. Follow-up lifecycle click-through (D-10/D-12)
expected: Schedule a follow-up dated tomorrow (pendente chip), execute it from the panel (becomes a dated event in EventosPanel); confirm the "Considerar follow-up" badge appears on a candidatura whose last event is 7+ days old.
result: [pending]

### 5. Door 2 click-through — Currículo prefill (D-13)
expected: Generate a resume on the Currículo page, click "Registrar candidatura" on the result, land on the Rastreador form with the JD prefilled; navigate away and back via the nav: the form is clean (prefill consumed exactly once; empresa/cargo empty for the user to type).
result: [pending]

### 6. Door 3 click-through — Respostas association (D-13/D-08)
expected: Submit an answer on the Respostas page, pick a candidatura in the "Associar à candidatura" picker, confirm; open that candidatura's EventosPanel: "Resposta" event listed with today's date, the answer's language, and the fixed note "Resposta registrada via módulo Respostas"; no question/answer text anywhere; contadores/kanban refresh via ['tracker'] invalidation.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps
