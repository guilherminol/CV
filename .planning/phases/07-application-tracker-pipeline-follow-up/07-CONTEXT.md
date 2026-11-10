# Phase 7: Application Tracker — Pipeline & Follow-up - Context

**Gathered:** 2026-11-10
**Status:** Ready for planning — usuário respondeu todas as 4 áreas cinzas (discussão interativa via texto puro; as caixas AskUserQuestion voltavam vazias nesta sessão). ROADMAP.md ainda tem o goal "[To be planned]" — o plan-phase deve preencher goal/success criteria a partir deste CONTEXT.

<domain>
## Phase Boundary

O usuário acompanha seus processos seletivos de ponta a ponta: cria candidaturas (uma candidatura = uma vaga), move cada uma por estágios de pipeline customizáveis num kanban, registra eventos datados (envio de currículo, entrevista, retorno), agenda follow-ups com data futura e vê prazos de retorno com destaques visuais — tudo persistido em SQLite, com contadores globais derivados mecanicamente dos eventos. O tracker é 100% determinístico: nenhuma chamada LLM, funciona sem API key/créditos OpenRouter. Integra com o que existe: botão "Registrar candidatura" na tela de resultado do Currículo (pré-preenche JD/idioma), associação na tela de Respostas de candidatura, e novo item "Rastreador" na nav.

Not in this phase: notificações ativas (browser/e-mail), exclusão de candidaturas (só arquivar), restore/import do export, qualquer recurso gerado por LLM (resumo semanal etc. — todos anotados em Deferred). Continuam Out of Scope do projeto: extração de vaga por URL, auto-apply, multi-usuário. O conteúdo dos currículos enviados continua efêmero — o tracker registra que um envio aconteceu (metadados), nunca o texto gerado.

</domain>

<decisions>
## Implementation Decisions

### Persistência (a reversão deliberada da restrição file-based)
- **D-01:** **SQLite local para os dados do tracker** — reversão PONTUAL, só para este módulo, da restrição "file-based (Markdown/YAML in git), not a database" do PROJECT.md; o perfil mestre continua em Markdown/YAML. — **Reversibility:** costly — desfazer toca a camada de armazenamento inteira (rotas CRUD, schema, path/bind-mount do .db); migrar de volta para arquivos reescreveria todos os call sites de leitura/escrita.
- **D-02:** **Homelab é a fonte da verdade** — o .db vive num bind mount próprio no container (como content/ e logs/ hoje); a instância local serve só para desenvolvimento, com banco descartável.
- **D-03:** **Export na UI** — botão que exporta tudo (JSON completo + CSV para planilha); zero infra nova; restore/import fica para fase futura.
- **D-04:** **Só arquivar, nunca apagar** — candidatura encerrada (rejeitada/desistiu) fica no banco com estágio final + data; o histórico alimenta as contagens; NENHUM caminho destrutivo nesta fase (exclusão é deferred).

### Estágios & campos
- **D-05:** **Estágios customizáveis** (o usuário rejeitou o enum fixo recomendado) — tabela de estágios no banco + gestão pela UI; o vocabulário é pessoal e as contagens por estágio refletem isso. — **Reversibility:** costly — migrar para enum fixo depois exigiria migração de dados de todas as candidaturas existentes + remoção da UI de gestão.
- **D-06:** **Campos por candidatura — essencial + detalhes:** empresa, cargo, fonte (onde viu), link da vaga, estágio atual, datas (aplicação, eventos, prazo de retorno), notas livres, texto da JD opcional; MAIS faixa salarial, contato do recrutador e modalidade (remoto/híbrido/presencial).
- **D-07:** **Contagens derivadas dos eventos** — cada envio de currículo e cada entrevista é um evento datado na candidatura; contadores calculados mecanicamente dos eventos, nunca números digitados à mão (honestidade mecânica das fases anteriores).
- **D-08:** **Uma candidatura = uma vaga; eventos guardam só metadados** (data, tipo, idioma, observação) — o conteúdo do currículo enviado continua efêmero, fora do banco; reenvio na mesma vaga = evento novo na mesma candidatura.

### Prazos & follow-ups
- **D-09:** **Prazos passivos na UI** — visão geral ordena por proximidade de prazo e destaca "vence em X dias" na família de cores aprovada (âmbar=aviso, vermelho=erro); sem notificações ativas nesta fase.
- **D-10:** **Follow-up agendado** — evento com data futura + nota; aparece como pendente até a data; ao registrar que executou, vira evento datado normal.
- **D-11:** **Vencido = destaque, sem mágica** — "venceu há X dias" em vermelho até o usuário registrar retorno ou adiar; nenhuma ação automática de estágio/arquivamento ao vencer.
- **D-12:** **Sugestão mecânica de follow-up** (o usuário escolheu ter, contra o recomendado) — badge determinístico "considerar follow-up" quando a candidatura fica N dias sem evento; limiar em constante de config (valor exato pinado no planejamento).

### Criação & visão geral
- **D-13:** **Integração máxima** — três portas de entrada: formulário manual na página do tracker; botão "Registrar candidatura" na tela de resultado do Currículo (pré-preenche o texto da JD e o idioma da geração; empresa/cargo o usuário digita — extração mecânica de JD não é confiável); associação na tela de Respostas de candidatura.
- **D-14:** **Kanban por estágio com componente PRONTO** (o usuário foi explícito: "pega um componente pronto sem criar do 0") — lib de drag-and-drop escolhida no planejamento; candidata `@dnd-kit/core` (mantida, React 19); `react-beautiful-dnd` deprecada, evitar. **Exceção deliberada** à convenção no-new-frontend-deps — contida a UMA lib; sem runner de testes JS novo (tsc -b continua a trava). — **Reversibility:** reversible — trocar de lib depois é custo localizado na UI do kanban.
- **D-15:** **Sem LLM no tracker** — 100% determinístico (CRUD + eventos + contagens + prazos); independe de créditos OpenRouter (esgotados desde a Fase 6).
- **D-16:** **Novo item "Rastreador" na nav** — quinto item em NAV_ITEMS; o label "Candidatura" (módulo de respostas) permanece intocado — zero risco de quebrar strings/testes existentes.

### Claude's Discretion
- Mecanism técnicos: driver SQLite (stdlib `sqlite3` recomendado — zero dependência nova no backend), versionamento/migração de schema do banco, path do .db em `app/config.py` (env-overridável para o compose), contrato das rotas CRUD, DTOs Pydantic estritos.
- Escolha final da lib de kanban e o padrão de integração dela com React 19 + Tailwind.
- Métrica exata dos contadores globais (enviadas, entrevistas, ativas) e a semântica de cada tipo de evento.
- Detalhes de deploy do compose no homelab (bind mount do .db) e do export CSV (encoding, colunas).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — Constraints ("file-based, not a database" — REVERTIDA PONTUALMENTE para o tracker por D-01; registrar a reversão na tabela Key Decisions); Out of Scope ("Application tracker / CRM" — SUPERSEDADO pela Fase 7, decisão do usuário no commit 498e01d; "Auto-apply" e "Job posting extraction from URL" continuam valendo)
- `.planning/REQUIREMENTS.md` — v2 "HIST-01: Application history log (Markdown-based) — only if the user feels the tracker pain" (a dor foi sentida; a Fase 7 materializa o HIST-01, agora em SQLite); tabela Out of Scope
- `.planning/ROADMAP.md` §Phase 7 — goal "[To be planned]", requirements TBD, depends on Phase 6
- `.planning/STATE.md` §Roadmap Evolution — a descrição original da fase ("vagas, estágios do pipeline, contagens de currículos enviados e entrevistas feitas, prazos de retorno e follow-ups")

### Prior phase decisions this phase builds on
- `.planning/phases/05-review-flow-fact-safety/05-CONTEXT.md` — D-14 ( ConfirmStrip/confirmação em caminhos destrutivos — aqui NÃO há caminho destrutivo por D-04); padrões de UI de resultado
- `.planning/phases/06-linkedin-module-bilingual-hardening/06-CONTEXT.md` — D-08 (loud-empty), D-09/D-11 (estado efêmero por página; envelope 200+status), D-13/D-14 (QA determinístico — espírito que o tracker inteiro carrega)
- `.planning/phases/03-resume-vertical-slice/03-CONTEXT.md` — D-05 (montagem do resultado — onde entra o botão "Registrar candidatura", D-13); D-06 (efêmero)
- `.planning/phases/01-foundation-scaffold-master-profile/01-CONTEXT.md` — padrão de nav/view switch e erro PT-BR

### Code / deploy
- `backend/app/routes/candidatura.py` + `backend/app/candidatura/pipeline.py` — o módulo de Respostas que D-13 associa às candidaturas (envelope 200, extra=forbid, sync def)
- `frontend/src/App.tsx` + `frontend/src/constants/ui.ts` — view switch sem router + NAV_ITEMS (D-16 entra aqui); strings PT-BR centralizadas
- `frontend/src/pages/CurriculoHome.tsx` + `frontend/src/components/ResumeResult.tsx` — tela de resultado que recebe o botão "Registrar candidatura" (D-13)
- `frontend/src/pages/CandidaturaHome.tsx` — tela de Respostas que recebe a associação (D-13)
- `Dockerfile` + `backend/app/config.py` — resolução de paths via REPO_ROOT; content/ e logs/ sombreados por bind mount no homelab — o .db segue o mesmo padrão (D-02)

No external specs/ADRs — no user-referenced docs beyond the planning set above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/App.tsx` + `NAV_ITEMS` (constants/ui.ts) — o view switch sem router aceita um quinto estado; padrão já validado 4 vezes
- `frontend/src/api/client.ts` — client tipado; `tsc -b` trava drift Pydantic↔TS (o CRUD do tracker adiciona vários DTOs novos)
- `frontend/src/components/` — ErrorPanel, StatusLine, ConfirmStrip (se um dia houver caminho destrutivo), CompletenessGrid (padrão de grade de contadores), CopiarButton
- `frontend/src/pages/CandidaturaHome.tsx` / `CurriculoHome.tsx` / `LinkedInHome.tsx` — padrão completo de página (form → mutation → resultado)
- `backend/app/routes/*` — padrão de router (envelope 200+{status,erros}, extra=forbid, sync def, registro antes do mount SPA em main.py)
- `backend/tests/` — suíte offline (pytest markers); testes do tracker são 100% offline por natureza (sem LLM)

### Established Patterns
- Falha alta: envelope 200+{status,erros}, PT-BR na UI, raw detail só no terminal
- Pydantic estrito `extra="forbid"` em todo request; rotas ANTES do mount SPA
- React Query v5; Tailwind; layout `max-w-3xl`; conteúdo = React state efêmero (o tracker é a PRIMEIRA exceção persistente — por design)
- Testes 100% offline; sem deps novas no frontend EXCETO a lib de kanban (D-14, exceção deliberada)

### Integration Points
- `backend/app/main.py` — novo router do tracker antes do mount SPA
- `backend/app/config.py` — TRACKER_DB path (env-overridável) + constantes do tracker (limiar de sugestão de follow-up, D-12)
- `App.tsx`/`constants/ui.ts` — item "Rastreador" na nav (D-16)
- `ResumeResult.tsx` — botão "Registrar candidatura" (D-13)
- `CandidaturaHome.tsx` — associação resposta↔candidatura (D-13)
- Homelab compose — bind mount do .db (D-02)

</code_context>

<specifics>
## Specific Ideas

- O usuário foi explícito no kanban: "pega um componente pronto sem criar do 0" — construir drag-and-drop manualmente está fora de questão; a lib é escolha do planning dentro do contorno D-14.
- O tracker nasce no contexto de busca ativa: o usuário está aplicando de verdade (ver .planning/quick/ — BEON, Factored, Sierra) e o homelab é o uso diário — por isso a fonte da verdade é o container (D-02).
- Os créditos OpenRouter estão esgotados (STATE.md) — o tracker determinístico (D-15) garante que a fase não trava nisso.
- Contadores honestos é a regra da casa: nada de métrica vaidosa; tudo derivado de eventos auditáveis (D-07), como o matcher da Fase 3.

</specifics>

<deferred>
## Deferred Ideas

- Restore/import do export JSON+CSV — só o export nasce nesta fase (D-03)
- Exclusão de candidaturas com confirmação — se o "só arquivar" (D-04) um dia doer
- Notificações ativas de prazo (Notification API / e-mail) — D-09 deixou passivo de propósito
- Resumo do pipeline gerado por LLM (ex.: semanal) — D-15 manteve o tracker sem LLM
- Sugestões de melhoria do vocabulário de estágios / relatórios avançados — kanban + contadores cobrem o essencial

None folded from todos — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-Application Tracker — Pipeline & Follow-up*
*Context gathered: 2026-11-10*
