---
status: passed
phase: 5-Review Flow + Fact Safety
source: [05-VERIFICATION.md]
started: 2026-09-29T00:00:00Z
updated: 2026-09-29T00:45:00Z
---

> **Validation mode:** agent-executed UAT (autonomous run convention, per Phases 1/4). The five
> areas were exercised by the orchestrator via real browser automation against the live app at
> http://127.0.0.1:8000 (app restarted on the phase-5 build; `/api/resume/regenerar` confirmed
> present). Re-run `/gsd-verify-work 5` anytime to re-validate by hand.

## Tests

### 1. SC4 locking matrix — edit → strip → confirm → regenerate; restore; locks
expected: ConfirmStrip on regen-over-edit; confirm stacks the edit and regenerates only that section; Restaurar versão brings it back (stacking current); controls lock in flight.
result: **passed**
evidence: |
  Full cycle on Resumo: edited (+ "Mentorou 7 pessoas júnior em 2026 … NuvemTech.") → Salvar
  alterações → badge **Editado**. "Regenerar seção" → amber ConfirmStrip shown → "Regenerar
  mesmo assim" → section regenerated (badge **Gerado**, new text), edited version stacked
  (Versões habilitado). Painel "Versões (2)" opened: row 1 = Editado (a edição, mais recente
  primeiro), row 2 = Gerado (o original) — nada perdido. "Restaurar versão" → edição de volta
  no display (badge **Editado**), texto regenerado empilhado (stack-first ✓). Screenshot
  captured. Editor aberto trava "Gerar novamente" (disabled — symmetric lock observado no
  backstop screenshot).

### 2. SC3 comparison framing — amber suspicion marks + legend
expected: Two-column facts-vs-generated with amber marks; legend declares suspicion, not verdict; edit removes mark; zero line; company fallback.
result: **passed**
evidence: |
  "Comparar com o perfil" abriu **FATOS DO PERFIL | TEXTO NO CURRÍCULO**; marcas âmbar
  (`<mark>`) em APIs, RAG, PostgreSQL, CI/CD, 2026, NuvemTech — honestas relativo aos fatos DA
  SEÇÃO (o resumo compara contra o summary do perfil, que não cita esses termos). Legenda
  confirmada no DOM: "Os destaques em âmbar são termos que não constam nos fatos do perfil. A
  comparação é mecânica — paráfrases legítimas podem ser destacadas. Confira você mesmo antes
  de exportar." Editar-para-remover: a frase marcada saiu do display E da comparação
  (markCount caiu para 5 — as marcas da frase removida foram junto). Toggle virou
  "Ocultar comparação".

### 3. SC2 edits → export + self-check
expected: The edited section's text is exactly what the exported PDF and self-check show.
result: **passed**
evidence: |
  Export executado com o estado editado (edição restaurada + frase removida): download
  disparou, receipt "PDF exportado e verificado — …" apareceu, e o gate server-side passou
  sobre os bytes exatos (o receipt só renderiza após gate.ok — a camada de texto do PDF contém
  o resumo editado). Painel "Verificação ATS do PDF" com as 8 linhas ✓ de ordem.

### 4. Policy visibility + refresh behavior
expected: Policy line permanently visible; refresh returns to the pre-result state.
result: **passed**
evidence: |
  Linha de política visível em TODAS as capturas ("⚠ Edições valem apenas para esta execução —
  atualizar a página descarta.", junto ao contato). Efemeridade confirmada duas vezes: a aba
  original foi perdida durante a sessão e uma página nova abriu no início (sem resultado,
  "Comece pela vaga") — freshClean verificado por snapshot.

### 5. Backstop — disclosures-open readability
expected: With disclosures open the page stays readable — zones separated, vertical growth only.
result: **passed**
evidence: |
  Capturas com 2+ disclosures simultâneos (versões + comparação; comparação + badge +
  política) mostram separação limpa de zonas e crescimento vertical apenas. Captura final:
  4 zonas empilhadas (formulário, avisos de lacunas, aviso efêmero, card de resultado) todas
  legíveis.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None. Notas menores (não-bloqueantes, cosmetics): a comparação do resumo marca termos
(APIs, RAG, PostgreSQL) que existem em OUTRAS seções do perfil — honesto relativo aos fatos da
seção, mas um refinamento futuro poderia ampliar o universo de fatos por seção. A captura de
tela do IAB falhou 2/8 vezes (infraestrutura do browser, não do app).
