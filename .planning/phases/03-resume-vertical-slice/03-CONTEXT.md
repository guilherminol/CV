# Phase 3: Resume Vertical Slice - Context

**Gathered:** 2026-09-26
**Status:** Ready for planning — ⚠ **SESSÃO AUTÔNOMA:** as quatro áreas cinzas foram decididas por auto-seleção das opções recomendadas (sem interação do usuário). Cada decisão abaixo está marcada com `[auto]`. O usuário DEVE revisar `03-CONTEXT.md` antes ou depois do planejamento; qualquer decisão pode ser trocada com re-edição deste arquivo (barata) ou re-executando `/gsd:discuss-phase 3`.

<domain>
## Phase Boundary

O fluxo Currículo ponta a ponta: o usuário cola a descrição da vaga, escolhe PT-BR ou EN para a execução, e o app extrai e exibe as keywords da vaga (motor da Fase 2), roda um lint de completude que amarra gaps do perfil à vaga (PROFILE-02), gera as seções de currículo fundamentadas nos fatos do perfil (resumo, bullets de experiência, skills — RESUME-01/RESUME-03), e mostra o checklist honesto de cobertura de keywords (RESUME-04). Toda geração atravessa o gateway da Fase 2 (logado, schema-validado, meta-prompts editáveis em `prompts/`). A tela de resultado monta o currículo completo (geradas + passthrough do perfil) — a montagem que a Fase 4 renderiza como PDF.

Not in this phase: PDF export e ATS self-check (Fase 4); regenerar seção individual, edição inline, diff fato-vs-gerado e política de write-back (Fase 5); LinkedIn (Fase 6); PT-BR hardening/glossário (Fase 6).

</domain>

<decisions>
## Implementation Decisions

> ⚠ Todas as decisões desta fase foram **auto-selecionadas** (`[auto]`) numa sessão autônoma — o usuário não respondeu aos prompts. Cada uma segue a opção recomendada, ancorada nas decisões travadas das Fases 1–2. Nenhuma representa preferência declarada do usuário.

### Formato da geração
- **D-01:** `[auto]` **Uma chamada LLM por seção** (três estágios — resumo, experiências, skills — no mapa `_STAGE_SCHEMAS` do gateway), orquestrados como uma única execução "gerar currículo". A regeneração por seção que a REVIEW-01 (Fase 5) exige já nasce aqui; schemas estritos menores por chamada dão retry localizado (um retry de bullets não re-roleia o resumo); o gateway é orientado a estágios por construção (Fase 2 D-05: um arquivo de prompt por estágio). Custo de rodar 3 chamadas vs 1 é aceito — a Fase 2 (D-02) já despriorizou micro-otimização de tokens em escala pessoal. — **Reversibility:** reversible — consolidar estágios depois seria merge local de prompts/schemas/orquestração; o schema da linha runs.jsonl (D-13 Fase 2) trata `stage` como valor de string, não quebra contrato.

### Cobertura de keywords (RESUME-04)
- **D-02:** `[auto]` **Classificação covered/absent por matching determinístico no código** — forma canônica OU qualquer alias (D-11 Fase 2), comparação case/pontuação-insensitive com word-boundary, sobre o texto gerado, no idioma da execução (usa `pt`/`en` do Keyword conforme a língua). O estado `adjacente` (hook SC4 da Fase 2) permanece no modelo e pode ser preenchido por heurística leve (stem/substring normalizada) ou ficar vazio nesta fase — researcher/planner detalham. **Sem juiz LLM:** checklist honesto = mecânica auditável (o usuário vê a string que marcou o match); julgamento semântico reintroduz a "precisão falsa" que REQUIREMENTS exclui explicitamente. — **Reversibility:** reversible — função pura sobre o texto gerado; um classificador semântico pode ser adicionado depois de forma aditiva.

### Lint de completude (PROFILE-02)
- **D-03:** `[auto]` **Avisos não-bloqueantes:** o usuário vê o lint e pode gerar mesmo com gaps. Bloqueio duro fica reservado a erros de schema do perfil (já existentes, Fase 1). A SC5 diz "user sees a completeness lint" — ver, não obrigatoriamente resolver; coerente com "never blocks the user" (Fase 1 D-03) e com falha-alta-sem-mágica (Fase 2 D-03). — **Reversibility:** reversible.
- **D-04:** `[auto]` **Checagens mínimas amarradas à vaga:** (a) keywords do JD nas categorias competências/ferramentas ausentes do perfil (comparação canônico+alias contra skills/technologies do perfil); (b) experiências sem impactos/métricas; (c) resumo ausente. A lista pode ser refinada em pesquisa/planejamento mantendo o espírito SC5: gaps do perfil vs o que o JD pede (ex.: "JD exige skill Y ausente do perfil", "sem métricas para o job X"). — **Reversibility:** reversible.

### Escopo na tela
- **D-05:** `[auto]` **A tela de resultado monta o currículo completo:** as 3 seções geradas em destaque (visualmente marcadas como geradas) + seções passthrough do perfil (contato, educação, certificações, idiomas — e projetos conforme o formato Google definido no prompt/layout). É a montagem que a Fase 4 renderiza como PDF, e o ProfilePreview (Fase 1 D-12) já estabelece o layout estilo-currículo e a ordem visual que o template de impressão usará. SC1 exige as 3 seções geradas — elas ficam em destaque. — **Reversibility:** reversible — apenas apresentação.

### Fluxo e persistência
- **D-06:** `[auto]` **Conteúdo gerado é efêmero** (estado de sessão no frontend; nada gravado em arquivo nesta fase). Atualizar a página perde o resultado — aceitável no slice. A política de edição/write-back ao perfil é decisão explícita da Fase 5 (compromisso registrado em STATE.md) — esta fase não a predefine. — **Reversibility:** reversible.
- **D-07:** `[auto]` **Barra da SC3 (no-invention) nesta fase:** restrição dura prompt-side + verificação por testes (fixtures com o perfil de exemplo, onde invenção é detectável, offline + harness `-m llm` bilíngue). O diff estrutural lado-a-lado fato-vs-gerado é a Fase 5 (REVIEW) — não é escopo daqui. — **Reversibility:** reversible.

### Claude's Discretion
- Ordem/roteamento: um endpoint que orquestra keyword-extraction → lint → estágios de seção vs endpoints separados; assinaturas das rotas (registro antes do mount SPA — Pitfall 5).
- Nomes exatos dos estágios e arquivos de prompt (ex.: `prompts/resume-summary.md`), estrutura de pacote backend (ex.: `app/resume/`), mecânica exata do matcher (normalização, stemming, word-boundary).
- Serialização dos fatos do perfil no user message (padrão D-07 Fase 2), composição dos prompts por seção, temperature/max_tokens no frontmatter de cada prompt.
- UI: componentes React, ordem dos blocos na tela (colar JD → idioma → lint → gerar → keywords → cobertura → currículo), onde o item de nav "Currículo" é habilitado (`constants/ui.ts`).
- Testes: cliente mockado offline (D-16 Fase 2) + extensão do harness `pytest -m llm` com fixtures de geração nos dois idiomas.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — constraints (OpenRouter only, localhost, JS frontend/Python backend, arquivo-based store), out-of-scope (sem score numérico de ATS, sem invenção de fatos)
- `.planning/REQUIREMENTS.md` — RESUME-01..04 + PROFILE-02 (esta fase); REVIEW-01..03 (Fases 4–5, consumidores futuros); tabela Out of Scope (checklist honesto, sem keyword stuffing)
- `.planning/ROADMAP.md` §Phase 3 — goal + 5 success criteria (a barra de aceitação); §Phase 4/§Phase 5 para as fronteiras deliberadas (PDF, review flow)

### Prior phase decisions this phase builds on
- `.planning/phases/02-llm-generation-core/02-CONTEXT.md` — D-05..D-08 (meta-prompts: um arquivo por estágio, formato, system/user split, sem cache), D-09..D-12 (keyword engine: PT↔EN, categorias fixas, canônico+alias, input-agnostic), D-01..D-04 (modelo, falha alta), D-13..D-16 (runs.jsonl, harness `-m llm`)
- `.planning/phases/01-foundation-scaffold-master-profile/01-CONTEXT.md` — D-01..D-04 (localized maps, base pt-BR, fallback), D-07 (conjunto completo de seções do currículo), D-08 (impactos embutidos por experiência — base do grounding), D-12..D-15 (UI Perfil, erros PT-BR, sem cache)

### Research (pinned patterns and risks)
- `.planning/research/STACK.md` — stack/versões pinadas; tabela What-NOT-to-use
- `.planning/research/ARCHITECTURE.md` — arquitetura de componentes; padrão fail-fast do loader
- `.planning/research/PITFALLS.md` — armadilhas citadas em comentários do código existente (ordem de registro de rotas, UTF-8, etc.)

No external specs/ADRs — no user-referenced docs beyond the planning set above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/llm/gateway.py` — `run_stage(stage, input_text, language, ...)` + mapa `_STAGE_SCHEMAS`: cada estágio de seção do currículo é uma nova entrada; retry/validação/logging vêm de graça
- `backend/app/llm/schemas.py` — base `_Strict` (extra="forbid") + padrão de wire schema estrito manual com drift-lock test: o modelo para cada seção gerada segue exatamente este padrão
- `backend/app/llm/prompts.py` — `load_prompt(stage)` lê `prompts/{stage}.md` fresco a cada chamada (SC1): novos estágios = novos arquivos, zero código
- `backend/app/profile/models.py` — `Profile`, `LocalizedText`, impactos embutidos por experiência (D-08): a fonte dos fatos serializada no user message
- `backend/app/profile/completeness.py` — hoje presença/contagem (D-12); o lint JD-tied (PROFILE-02) estende este módulo ou vive ao lado dele
- `backend/app/routes/profile.py` — padrão envelope de status (200 + status, nunca 500, raw detail só no terminal): template para as rotas desta fase
- `frontend/src/api/client.ts` — client tipado espelhando Pydantic, `tsc -b` como trava de drift
- `frontend/src/components/ProfilePreview.tsx` — layout estilo-currículo do perfil: base visual para a montagem do resultado (D-05)

### Established Patterns
- Falha alta: mensagem PT-BR ao usuário + raw detail só no terminal (Fase 1 D-13/D-14; Fase 2 D-03)
- Sem cache — re-leitura/validação fresca por request (Fase 1 D-15; prompts idem, Fase 2 D-08)
- Pydantic estrito `extra="forbid"` em todo modelo; wire `strict: true` nunca confiado
- Rotas registradas ANTES do mount SPA em `main.py` (Pitfall 5)
- Strings de UI PT-BR centralizadas em `frontend/src/constants/ui.ts` (NAV_ITEMS com flag `enabled` — item Currículo a habilitar)
- React Query v5 (`isPending`), Tailwind, layout `max-w-3xl`
- Testes 100% offline por padrão; rede só sob `pytest -m llm` (Fase 2 D-15/D-16)

### Integration Points
- `_STAGE_SCHEMAS` em `backend/app/llm/gateway.py` — registro dos estágios de geração do currículo
- `backend/app/main.py` — novo router antes do mount SPA
- `backend/app/llm/schemas.py` — `KeywordExtraction` é o contrato que alimenta keywords visíveis (RESUME-02), lint (D-04) e checklist de cobertura (RESUME-04); matching usa canônico+alias
- `logs/runs.jsonl` — toda chamada desta fase já é auditada pelo mecanismo existente; semente do run store (Fases 5/6)
- `content/profile.md` → loader — fonte dos fatos para lint, grounding e passthrough da montagem

</code_context>

<specifics>
## Specific Ideas

- **SESSÃO AUTÔNOMA:** o usuário não respondeu às perguntas de discussão (2 tentativas). As 4 áreas cinzas foram fechadas por auto-seleção das opções recomendadas, cada uma ancorada em decisões travadas das Fases 1–2. Revisão do usuário pendente — todas as decisões estão marcadas `[auto]` e nenhuma é cara de reverter.
- Preferência persistente das fases anteriores: discussões e UI em PT-BR; falha alta sem fallback silencioso; saídas honestas (sem precisão falsa — REQUIREMENTS exclui score numérico de ATS e keyword stuffing).
- O checklist honesto e o lint são a materialização do valor "visão honesta de cobertura" do goal da fase — a honestidade é mecanicamente auditável, não opinativa (D-02).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope (sem input do usuário; nenhuma ideia fora de escopo surgiu).

</deferred>

---

*Phase: 3-Resume Vertical Slice*
*Context gathered: 2026-09-26*
