# Phase 6: LinkedIn Module + Bilingual Hardening - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning — ⚠ **SESSÃO AUTÔNOMA:** o usuário não respondeu ao prompt da Área 1 (convenção da run). As 4 áreas cinzas foram fechadas pelas opções recomendadas, marcadas `[auto — silence]` e ancoradas nas decisões travadas das Fases 1–5. Revisão do usuário pendente — re-edição deste arquivo é barata, ou `/gsd-discuss-phase 6`.

<domain>
## Phase Boundary

O usuário declara um objetivo de carreira uma única vez (texto livre + idioma) e recebe seções LinkedIn completas e dentro dos limites em PT-BR ou EN — headline (≤220), sobre (≤2600), descrições por experiência (≤2000 cada) e lista de skills priorizada — cada uma com contador de caracteres visível, nada truncado silenciosamente, todas copy-paste prontas via botão Copiar. Reusa o motor do currículo wholesale: mesmos estágios do gateway, novos arquivos de prompt e block types apenas. PT-BR hardening: glossário de terminologia aplicado deterministicamente, QA gate de English bleed (relatório não-bloqueante), e a suíte de fixtures bilíngues como definition-of-done para mudanças de prompt. Delivers LI-01..LI-05.

Not in this phase: auto-posting/sync LinkedIn (Out of Scope — ToS), extração de vaga por URL (Out of Scope), DOCX, cover letter. O QA gate bilíngue cobre a geração LinkedIn (o currículo já validado mantém sua suíte existente).

</domain>

<decisions>
## Implementation Decisions

### Entrada e fluxo (LI-01)
- **D-01:** `[auto — silence]` **Item "LinkedIn" na nav** (placeholder desabilitado já existe em `constants/ui.ts` NAV_ITEMS) → página própria com o padrão da tela Currículo (objetivo → idioma → avisos → gerar → resultado).
- **D-02:** `[auto — silence]` **Objetivo em texto livre único + seletor de idioma** (mesmo controle segmentado PT-BR/EN). Carga/senioridade/tecnologias-alvo são orientação no prompt (user message), não campos de formulário — menos atrito, o LLM estrutura o objetivo. Limite inferior de comprimento para habilitar o botão (como os 80 chars do JD; valor exato em planning/research).
- **D-03:** `[auto — silence]` **Lint não-bloqueante antes de gerar** — o motor de keywords é input-agnostic (D-12 Fase 2) e já aceita objetivos; avisos coerentes com a Fase 3 (D-03/D-04: ver, não obrigar).
- **D-04:** `[auto — silence]` **Uma execução gera todas as seções** (headline, sobre, experiências, skills); regeneração por seção via o mecanismo da Fase 5 (mesmo endpoint/padrão, estágios LinkedIn).

### Limites e contadores (LI-02, LI-03, LI-05)
- **D-05:** `[auto — silence]` **Limites em constantes de config do backend, verificados na pesquisa** (preocupação do STATE: 220/2,600/2,000 em fontes MEDIUM-confiança → research valida antes de fixar). Aplicação dupla: client (maxLength nos editores) + server (bounds no schema de saída + validação pós-geração).
- **D-06:** `[auto — silence]` **Contador ao vivo por campo** ("X/Y caracteres"), âmbar em ≥90% do limite, vermelho acima — coerente com a família de cores aprovada (âmbar=aviso, vermelho=erro).
- **D-07:** `[auto — silence]` **Nada truncado silenciosamente:** saída acima do limite é sinalizada no lugar e a regeneração por seção é o caminho de correção — truncamento automático rejeitado (SC2 literal).
- **D-08:** `[auto — silence]` **Botão "Copiar" por seção** (navigator.clipboard.writeText) com feedback "Copiado!" — o texto exibido é o que vai para a área de transferência (LI-05 copy-paste ready).

### Reuso do motor (wholesale)
- **D-09:** `[auto — silence]` **Novos estágios no `_STAGE_SCHEMAS`** espelhando o padrão do currículo (D-01 Fase 3): um arquivo de prompt por bloco de saída (headline, sobre, experiências, skills); descrições de experiência num único estágio retornando mapa por empresa (uma chamada, retry localizado por bloco).
- **D-10:** `[auto — silence]` **runs.jsonl intacto** — chamadas LinkedIn logadas pelo mecanismo existente (stage como string), sem campos novos (contrato D-13 Fase 2).
- **D-11:** `[auto — silence]` **Estado efêmero próprio da página LinkedIn** (mesmo padrão Currículo: React state, aviso efêmero, versões/regeneração via os mecanismos da Fase 5).

### PT-BR hardening (SC4)
- **D-12:** `[auto — silence]` **Glossário como arquivo versionado editável** (`prompts/glossario.md`, padrão D-05 Fase 2 — Markdown+YAML frontmatter, validado estrito): pares termo→termo preferido (ex.: "machine learning"→"aprendizado de máquina" quando o usuário preferir), lido fresco a cada execução.
- **D-13:** `[auto — silence]` **Aplicação do glossário determinística pós-geração** (substituições mecânicas termos→preferidos no texto PT-BR) + relatório do que foi alterado — não prompt-side only (não-determinístico não é auditável).
- **D-14:** `[auto — silence]` **QA gate não-bloqueante:** relatório de English bleed (detecção determinística: glossário + lista heurística de termos EN comuns em texto PT-BR) exibido como avisos — coerente com avisos não-bloqueantes (Fase 3 D-03); falha alta reservada a erros duros (schema/rede). Sem juiz LLM (custo + precisão falsa).
- **D-15:** `[auto — silence]` **Fixtures bilíngues LinkedIn como DoD:** o harness `pytest -m llm` ganha fixtures LinkedIn PT-BR/EN que rodam na suíte real-API; mudança de prompt sem fixture verde = não feito (SC4 literal). Suite offline continua 100% offline.

### Claude's Discretion
- Número/limites exatos dos estágios e nomes dos arquivos de prompt; schemas de saída por bloco (wire schema estrito padrão da Fase 2).
- Contrato do endpoint LinkedIn (um orquestrador vs estágios separados), bounds de validação do objetivo.
- Mecânica do contador ( componente compartilhado), agrupamento visual das seções, reuso de SectionEditor/Versões/Comparar na página LinkedIn.
- Estrutura do módulo backend (app/linkedin/ vs extensão de app/resume/), forma do glossário no schema, lista heurística de English bleed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — LinkedIn module = career-objective-driven (não vacancy-driven); Out of Scope (auto-posting, API sync)
- `.planning/REQUIREMENTS.md` — LI-01..LI-05 (esta fase)
- `.planning/ROADMAP.md` §Phase 6 — goal + 4 success criteria; reuso wholesale "(prompts and block types only)"

### Prior phase decisions this phase builds on
- `.planning/phases/02-llm-generation-core/02-CONTEXT.md` — D-05..D-08 (um prompt por estágio, formato, user-message), D-09 (PT↔EN no extraction), D-12 (motor input-agnostic), D-13/D-15 (runs.jsonl, harness -m llm)
- `.planning/phases/03-resume-vertical-slice/03-CONTEXT.md` — D-01 (um estágio por seção), D-03/D-04 (avisos não-bloqueantes), D-05 (montagem do resultado), D-06 (efêmero)
- `.planning/phases/05-review-flow-fact-safety/05-CONTEXT.md` — D-05/D-06 (regeneração por seção via gateway), D-08 (pilha de versões), D-12 (edição inline) — mecanismos a reusar na página LinkedIn
- `.planning/phases/01-foundation-scaffold-master-profile/01-CONTEXT.md` — D-05 (perfil único), D-09 (skills categorizadas — insumo da lista priorizada)
- `.planning/phases/04-pdf-export-ats-self-check/04-CONTEXT.md` — padrão de export não se aplica aqui (copy-paste, não PDF), mas o padrão de constantes de config (D-05) sim

### Research / STATE
- `.planning/STATE.md` §Blockers/Concerns — "Phase 6: LinkedIn character limits (220/2,600/2,000) rest on MEDIUM-confidence sources — verify at planning" → D-05 manda research verificar; §polish candidates ("atual" em EN, hífen no matcher) — candidatos, não escopo obrigatório

No external specs/ADRs — no user-referenced docs beyond the planning set above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/llm/gateway.py` — `run_stage` + `_STAGE_SCHEMAS`: novos estágios LinkedIn = novas entradas + novos prompts, zero mudança no gateway
- `backend/app/llm/prompts.py` — loader de `prompts/{stage}.md` fresco; o glossário segue o mesmo padrão de leitura
- `backend/app/resume/pipeline.py` — orquestração multi-estágio + cobertura: o esqueleto do pipeline LinkedIn
- `backend/app/resume/facts.py` — serialização dos fatos do perfil no user message
- `backend/tests/test_llm_harness.py` — harness real-API a estender com fixtures LinkedIn
- `frontend/src/pages/CurriculoHome.tsx` — padrão completo da página (objetivo→idioma→gerar→resultado)
- `frontend/src/components/SectionEditor.tsx`, `SectionVersionsPanel.tsx`, `ConfirmStrip.tsx` — edição/versões/confirmação reusáveis
- `frontend/src/constants/ui.ts` — NAV_ITEMS com o placeholder LinkedIn a habilitar; strings PT-BR

### Established Patterns
- Falha alta + envelope 200+{status,erros}; sync def; extra=forbid; rotas antes do mount SPA
- Efêmero + aviso permanente; falha-alta-sem-mágica; honestidade mecânica (sem juiz LLM)
- Testes offline por padrão; rede só sob `-m llm`; tsc -b como trava de drift

### Integration Points
- `backend/app/main.py` — router LinkedIn antes do mount SPA
- `_STAGE_SCHEMAS` + `prompts/` — novos estágios e o glossário
- `frontend/src/App.tsx` + `constants/ui.ts` — habilitar o item LinkedIn na nav
- `logs/runs.jsonl` — stage strings novos, contrato intacto
- `backend/tests/test_llm_harness.py` — fixtures LinkedIn PT-BR/EN

</code_context>

<specifics>
## Specific Ideas

- O goal diz "reusing the resume engine wholesale (prompts and block types only)" — a medida de sucesso arquitetural é quanta lógica NOVA existe: idealmente quase nenhuma além de schemas, prompts e a página.
- Copy-paste ready = o bloco de texto exibido É o entregável; contadores e limites são a promessa de "nada truncado silenciosamente".
- O PT-BR hardening fecha o compromisso da Fase 2 (D-09: glossário pode pinar traduções) e o SC4: fixture bilíngue verde = prompt mudado com confiança.

</specifics>

<deferred>
## Deferred Ideas

- Aplicar o QA gate/glossário também ao fluxo do currículo — o SC4 desta fase fala das saídas LinkedIn; estender ao currículo é aditivo depois.
- Polish candidates do STATE ("atual" em EN, hífen no matcher) — candidatos a incluir se a onda de execução permitir.

</deferred>

---

*Phase: 6-LinkedIn Module + Bilingual Hardening*
*Context gathered: 2026-09-29*
