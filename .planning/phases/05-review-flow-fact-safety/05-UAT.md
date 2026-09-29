---
status: testing
phase: 5-Review Flow + Fact Safety
source: [05-VERIFICATION.md]
started: 2026-09-29T00:00:00Z
updated: 2026-09-29T00:00:00Z
---

> **Validation mode:** agent-executed UAT (autonomous run convention, per Phase 4). The five
> areas are exercised by the orchestrator via real browser automation against the live app;
> re-run `/gsd-verify-work 5` anytime to re-validate by hand.

## Tests

### 1. SC4 locking matrix — edit → strip → confirm → regenerate; restore; locks
expected: Editing a section then clicking "Regenerar seção" shows the amber ConfirmStrip ("Manter edição" / "Regenerar mesmo assim"); confirming stacks the edited version (visible in "Versões"), regenerates ONLY that section, and siblings are untouched; "Restaurar versão" brings a prior version back (stacking current first); controls lock while a regeneration is in flight.
result: [pending]

### 2. SC3 comparison framing — amber suspicion marks + legend
expected: "Comparar com o perfil" opens a two-column panel; inventions (metrics/names/technologies not in the profile facts) carry amber marks with the legend declaring them suspicion, not verdicts; editing text to remove a suspect clears its mark; a section with no suspects shows the loud zero line; unmatched company falls back to showing all profile entries.
result: [pending]

### 3. SC2 edits → export + self-check
expected: An edited section's text is exactly what the exported PDF and the self-check panel show.
result: [pending]

### 4. Policy visibility + refresh behavior
expected: The policy line ("Edições valem apenas para esta execução — atualizar a página descarta") is permanently visible near editable content; refreshing the page returns to the pre-result state (ephemeral, D-01).
result: [pending]

### 5. Backstop — disclosures-open readability
expected: With editor, versions panel, and comparison panel all open, the page stays readable — zones separated, vertical growth only.
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
