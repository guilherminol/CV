---
status: complete
phase: 07-application-tracker-pipeline-follow-up
source: [07-VERIFICATION.md]
started: 2026-11-11T12:20:00Z
updated: 2026-11-11T12:51:29.946Z
---

## Current Test

[testing complete]

## Tests

### 1. Kanban drag + persistence + empty-column drop (D-14)
expected: Persisted stage after reload (not optimistic-only); empty-column drop accepted; same-stage visual sorts do not fire writes.
result: pass
source: browser-automation
evidence: |
  Ponteiro sintético (PointerEvents na pipeline dnd-kit): Beta arrastado Pesquisando→Enviado e depois Enviado→Entrevista (coluna VAZIA aceitou o drop, hint "Arraste uma candidatura para cá" substituída pelo cartão). Persistência confirmada com reload após CADA move: Enviado (1) e Entrevista (1) com Beta no reload seguinte. Contadores Ativas=2 estáveis.

### 2. Keyboard-only DnD + click survival (D-14 / Pitfall 4)
expected: Tab/focus no cartão, Space ativa, setas movem para outra coluna, Space solta — mesma persistência; clique no corpo do cartão abre o detalhe (clicks sobrevivem ao sensor distance-8).
result: pass
source: browser-automation
evidence: |
  KeyboardSensor end-to-end: Space elevou o cartão Beta ([active][pressed], live region "Draggable item 2 was moved over droppable area estagio-2"), ArrowRight moveu sobre a coluna Enviado, Space soltou — Beta renderizado em Enviado (1) e persistido. Clique no body button do cartão Alpha abriu a região de detalhe (Arquivar, campos D-06, EventosPanel).

### 3. Amber/red prazo highlights (D-09/D-11)
expected: "vence em 2 dias" (âmbar) e "venceu há 7 dias" (vermelho); sr-only suffix; overdue NÃO arquivado nem movido automaticamente.
result: pass
source: browser-automation
evidence: |
  Screenshot confirma as famílias de cores: chip âmbar "Vence em 2 dias" (Alpha), chip vermelho "Venceu há 7 dias" (Beta). Árvore ARIA mostra os sufixos sr-only "(próximo do prazo)" e "(vencido)". Beta permaneceu ativa em seu estágio — nenhuma ação automática de estágio/arquivamento (D-11: vencido = destaque, sem mágica). Overview ordenado por proximidade (vencido primeiro).

### 4. Follow-up lifecycle click-through (D-10/D-12)
expected: Follow-up datado amanhã → pendente; Executar → evento datado; badge "Considerar follow-up" em candidatura 7+ dias sem evento.
result: pass
source: browser-automation
evidence: |
  Alpha: follow-up 2026-11-12 registrado → linha "Follow-up pendente para 2026-11-12." com botões Executar/Adiar; Executar → virou evento datado "Follow-up — 2026-11-11" (pendente sumiu). Badge "Considerar follow-up" renderizado no Beta (data_aplicacao 2026-11-02, 9 dias ≥ N=7).

### 5. Door 2 click-through — Currículo prefill (D-13)
expected: Gerar currículo → "Registrar candidatura" no resultado → Rastreador com JD pré-preenchida; navegar away/back → form limpo (consumido exatamente uma vez).
result: pass
source: browser-automation
evidence: |
  Geração funcionou (LLM ativo); botão "Registrar candidatura" no resultado trocou para o Rastreador com o "Texto da JD" pré-preenchido verbatim e empresa/cargo vazios (usuário digita). Após navegar Perfil→Rastreador, o form está limpo — prefill consumido exatamente uma vez.

### 6. Door 3 click-through — Respostas association (D-13/D-08)
expected: Gerar resposta → "Associar à candidatura" → evento 'Resposta' com data de hoje, idioma, nota fixa; SEM o texto da resposta; invalidation atualiza o tracker.
result: pass
source: browser-automation
evidence: |
  Resposta gerada (LLM ativo); seletor listou as candidaturas; associada ao Alpha → feedback "Resposta registrada na candidatura."; EventosPanel do Alpha mostra "Resposta — 2026-11-11 · pt-BR · Resposta registrada via módulo Respostas" SEM o texto da resposta (metadata-only, D-08). Dados do tracker já atualizados ao abrir (invalidation ['tracker'] funcionou).

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
