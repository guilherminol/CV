# Phase 5: Review Flow + Fact Safety - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning — ⚠ **SESSÃO AUTÔNOMA:** o usuário não respondeu aos prompts desta run (silêncio no AskUserQuestion da Área 1). As 4 áreas cinzas foram fechadas pelas opções recomendadas, cada uma marcada `[auto — silence]` e ancorada nas decisões travadas das Fases 1–4. Nenhuma é cara de reverter; o usuário pode re-editar este arquivo ou rodar `/gsd-discuss-phase 5`.

<domain>
## Phase Boundary

O usuário é o controle de qualidade antes do export: regenera seções individuais sem afetar as outras (opcionalmente com uma dica de direcionamento), edita qualquer texto gerado inline na tela, e vê exatamente o que a IA mudou relativo aos fatos do perfil — comparação lado a lado com invenções destacadas deterministicamente. Regenerar nunca destrói silenciosamente edições: versões anteriores de cada seção permanecem acessíveis e a política de edição é explícita na UI. Delivers REVIEW-01.

Not in this phase: LinkedIn (Fase 6); PT-BR hardening/glossário (Fase 6); write-back de edições aos arquivos do perfil (decidido FORA de escopo desta fase — política efêmera); candidatos de polish registrados no STATE.md ("atual" em EN, normalização de hífen no matcher).

</domain>

<decisions>
## Implementation Decisions

### Política de edição (a decisão travada do STATE.md — "sem ambiguidade")
- **D-01:** `[auto — silence]` **Edições vivem em estado efêmero da sessão** (React state, coerente com D-06 Fase 3 e D-16 Fase 4). Atualizar a página descarta — com aviso visível. Write-back aos arquivos do perfil rejeitado: mutaria a fonte da verdade que o schema/lint/grounding da Fase 1 validam, e o usuário edita o perfil "no editor dele" (PROJECT.md). localStorage rejeitado: criaria duas verdades efêmeras. — **Reversibility:** reversible — migrar para write-back depois é aditivo (um botão "salvar no perfil" pode nascer quando o módulo real existir).
- **D-02:** `[auto — silence]` **Política explícita na UI:** aviso permanente junto ao texto editável — "Edições valem apenas para esta execução — atualizar a página descarta" — no padrão do aviso efêmero existente (CURRICULO_EPHEMERAL_NOTICE). SC4 atendido literalmente.
- **D-03:** `[auto — silence]` **Edições fluem automaticamente para export e self-check** — a Fase 4 já exporta o estado exibido (D-10 Fase 4); nenhum passo "aplicar" extra. O PDF e a verificação ATS sempre refletem a versão editada.
- **D-04:** `[auto — silence]` **Terceiro estado de badge: Editado** (Gerado / Do perfil / Editado) — edição é visível de relance, sem ambiguidade sobre a origem do texto na tela.

### Regeneração por seção (REVIEW-01)
- **D-05:** `[auto — silence]` **Dica de direcionamento opcional por seção** (SC1 "optionally steering with a hint"): campo de texto exibido sob demanda, anexado ao user message da chamada de regeneração (padrão D-07 Fase 2 — dados no user message, nunca no system prompt).
- **D-06:** `[auto — silence]` **Regeneração = run_stage do estágio da seção** via gateway existente (`_STAGE_SCHEMAS`), merge do resultado no estado montado. Retry localizado, custo só da seção — a arquitetura de 3 estágios da Fase 3 (D-01) nasceu para isso.
- **D-07:** `[auto — silence]` **Seções irmãs intactas** (SC1 literal). Cobertura de keywords recalculada sobre o texto montado inteiro após o merge (matcher determinístico, D-02 Fase 3).
- **D-08:** `[auto — silence]` **Pilha de versões por seção em memória de sessão:** cada regeneração empilha a versão anterior; painel "versões" da seção lista as anteriores com ação de restaurar (SC4 "prior versions remain accessible"). Sem persistência em arquivo (coerente com D-01).

### Fato vs gerado (SC3)
- **D-09:** `[auto — silence]` **Painel de comparação por seção gerada**, expansível ("Comparar com o perfil"): duas colunas — fatos do perfil | texto gerado. Experiências comparadas por campo (descrição/bullets gerados vs description/impacts do perfil).
- **D-10:** `[auto — silence]` **Destaques de invenção determinísticos:** entidades/métricas/tecnologias nomeadas no texto gerado ausentes dos fatos da fonte, marcadas visualmente. Sem juiz LLM (REQUIREMENTS exclui precisão falsa; coerente com D-02 Fase 3). Reusa as primitivas de fold/normalização do matcher (coverage.py).
- **D-11:** `[auto — silence]` **O highlight é suspeita, não sentença:** a UI deixa claro que a comparação mecânica destaca candidatos a invenção (paráfrases legítimas podem ser destacadas); o julgamento final é do usuário — exatamente o papel de "quality gate" do goal.

### Fluxo e integração
- **D-12:** `[auto — silence]` **Edição inline no card de resultado:** clique para editar transforma a seção em textarea; salvar retorna ao texto com badge Editado. Sem modal, sem modo separado.
- **D-13:** `[auto — silence]` **Perfil view intocado** — a Fase 5 toca apenas a tela de resultado (CurriculoHome/ResumeResult e novos componentes).
- **D-14:** `[auto — silence]` **Regenerar sobre edição não salva pede confirmação leve** ("isso vai descartar sua edição — continuar?") — SC4 proíbe destruição *silenciosa*; a versão editada é empilhada antes da regeneração, então nada se perde mesmo sem confirmar.
- **D-15:** `[auto — silence]` **runs.jsonl intocado:** regeneração loga como qualquer chamada de estágio (D-13/D-14 Fase 2); sem campos novos.

### Claude's Discretion
- Mecânica exata do editor inline (textarea vs contentEditable), estados de foco/atalhos, acessibilidade do fluxo de edição.
- Formato exato dos destaques de invenção (sublinhado/realce/fundo), tokens comparados (métricas numéricas, nomes próprios, tecnologias — detalhe no research/planning).
- Estrutura do backend: endpoint único de regeneração vs reuso direto do endpoint existente por estágio; forma do hint no payload (estrito, extra="forbid").
- Estrutura da pilha de versões no frontend (hook/componente), limites de versões em memória.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — constraints (localhost, file-based store, review-before-export), "Review-in-app flow matters" no Context, Out of Scope (sem invenção de fatos)
- `.planning/REQUIREMENTS.md` — REVIEW-01 (esta fase); REVIEW-02/03 (consumidas do estado montado); tabela Out of Scope
- `.planning/ROADMAP.md` §Phase 5 — goal + 4 success criteria (a barra de aceitação)

### Prior phase decisions this phase builds on
- `.planning/phases/03-resume-vertical-slice/03-CONTEXT.md` — D-01 (3 estágios por seção: a base da regeneração localizada), D-02 (matcher determinístico), D-05 (montagem do resultado), D-06 (efêmero + política da Fase 5 explícita — resolvida aqui em D-01)
- `.planning/phases/04-pdf-export-ats-self-check/04-CONTEXT.md` — D-10 (exporta o estado exibido — edições fluem para o PDF), D-13/D-16 (self-check automático, efêmero)
- `.planning/phases/02-llm-generation-core/02-CONTEXT.md` — D-05..D-08 (um arquivo de prompt por estágio, hint no user message), D-13/D-14 (runs.jsonl)
- `.planning/phases/01-foundation-scaffold-master-profile/01-CONTEXT.md` — D-08 (impactos embutidos por experiência — a fonte do lado "fatos" da comparação)

### Research / STATE
- `.planning/STATE.md` §Accumulated Context — "Phase 5: must make the in-app edit policy explicit (ephemeral-with-warning vs write-back to profile files) — no ambiguity" → resolvida em D-01/D-02; §Blockers/Concerns — polish candidates da Fase 4 (fora de escopo aqui)

No external specs/ADRs — no user-referenced docs beyond the planning set above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/llm/gateway.py` — `run_stage(stage, ...)` + `_STAGE_SCHEMAS`: regeneração por seção é uma chamada por estágio (retry localizado de graça)
- `backend/app/resume/coverage.py` — matcher determinístico (canônico+alias, fold/lookaround): primitivas para os destaques de invenção (D-10)
- `backend/app/resume/pipeline.py` — orquestração dos 3 estágios + montagem: ponto de reuso para regenerar-um-estágio-e-remontar
- `frontend/src/components/ResumeResult.tsx` — montagem D-05 com badges Gerado/Do perfil (Badge component) — o terceiro estado Editado estende este padrão
- `frontend/src/components/StatusLine.tsx`, `ErrorPanel.tsx`, `ExportZone.tsx`, `SelfCheckPanel.tsx` — componentes compartilhados do fluxo de resultado
- `frontend/src/api/client.ts` — client tipado; `tsc -b` trava drift
- `frontend/src/constants/ui.ts` — strings PT-BR centralizadas (inclui CURRICULO_EPHEMERAL_NOTICE — padrão do aviso D-02)

### Established Patterns
- Falha alta: envelope 200+{status,erros}, PT-BR na UI, raw detail no terminal
- Sync `def` nas rotas bloqueantes (LLM) — threadpool
- Pydantic estrito `extra="forbid"` em todo request
- Conteúdo gerado = React state efêmero; badge tri-estado estende o padrão existente
- Testes 100% offline; LLM real só sob `pytest -m llm`
- Rotas antes do mount SPA; strings PT-BR em constants/ui.ts

### Integration Points
- `backend/app/routes/resume.py` — rota de regeneração por seção (ou reuso do gerar por estágio) antes do mount SPA
- `_STAGE_SCHEMAS` em gateway.py — os 3 estágios já registrados; hint via user message
- Tela de resultado — edição inline, painel de versões, comparação fato-vs-gerado como novos blocos por seção
- Export/self-check (Fase 4) — consumindo o estado montado pós-edição sem mudança de contrato
- `logs/runs.jsonl` — chamadas de regeneração logadas pelo mecanismo existente

</code_context>

<specifics>
## Specific Ideas

- O goal da fase transforma o usuário no quality gate: regenerar/editar/comparar são os três poderes; a política explícita (D-01/D-02) é a condição de confiança — o STATE.md exigia "no ambiguity".
- Honestidade mecânica em tudo: destaques de invenção são determinísticos e declarados como suspeita (D-10/D-11), nunca julgamento de IA sobre IA.
- SC4 é behavioral: regenerar com edição pendente empilha antes, confirma antes — "nunca silenciosamente" é testável.

</specifics>

<deferred>
## Deferred Ideas

- Write-back de edições ao perfil ("salvar no perfil") — aditivo quando o usuário quiser; fora do escopo efêmero desta fase (D-01).
- Normalização de hífen no matcher de cobertura e localização do marcador "atual" em EN — polish candidates registrados no STATE.md (Fase 6 ou follow-up).

</deferred>

---

*Phase: 5-Review Flow + Fact Safety*
*Context gathered: 2026-09-27*
