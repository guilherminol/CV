# Phase 7: Application Tracker — Pipeline & Follow-up - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-10
**Phase:** 07-Application Tracker — Pipeline & Follow-up
**Areas discussed:** Persistência, Estágios & campos, Prazos & follow-ups, Criação & visão geral

**Nota da sessão:** as caixas AskUserQuestion voltaram vazias duas vezes nesta sessão — a discussão continuou em texto puro (perguntas numeradas), com todas as respostas digitadas pelo usuário. Nenhuma decisão foi autopreenchida (`[auto — silence]` não ocorre neste arquivo).

---

## Persistência

| Option | Description | Selected |
|--------|-------------|----------|
| Um arquivo por vaga em content/candidaturas/ (Recomendado) | Markdown+frontmatter por candidatura; diffs limpos, padrão profile.md | |
| Um YAML único | Lista inteira num arquivo; leitura única, diffs crescem | |
| SQLite local | Banco em arquivo; quebra a restrição file-based | ✓ |

**User's choice:** SQLite local
**Notes:** usuário informou a reversão com ciência do conflito com PROJECT.md; o CONTEXT registra a reversão como pontual (só tracker; perfil continua Markdown/YAML).

| Option | Description | Selected |
|--------|-------------|----------|
| Homelab é a fonte (Recomendado) | .db em bind mount próprio no container; local = dev descartável | ✓ |
| Máquina local é a fonte | .db gitignored local; homelab não guarda candidaturas | |
| Mesmo banco nos dois | Um .db compartilhado (cuidado com SQLite em rede) | |

**User's choice:** Homelab é a fonte da verdade

| Option | Description | Selected |
|--------|-------------|----------|
| Export na UI (Recomendado) | Botão JSON+CSV; zero infra; restore no futuro | ✓ |
| Só backup do volume | Nada construído; backup é o dos volumes | |
| Snapshot Markdown no git | Dump periódico versionado; segunda fonte de verdade | |

**User's choice:** Export na UI (JSON completo + CSV)

| Option | Description | Selected |
|--------|-------------|----------|
| Só arquivar, nunca apagar (Recomendado) | Estádio final + data; sem caminho destrutivo | ✓ |
| Arquivar + excluir com confirmação | ConfirmStrip; mais um caminho destrutivo | |
| Você decide | Agente escolhe no planejamento | |

**User's choice:** Só arquivar, nunca apagar — confirmado em texto puro ("1") após o usuário pedir "tenta novamente" e a caixa voltar vazia duas vezes.

---

## Estágios & campos

| Option | Description | Selected |
|--------|-------------|----------|
| Enum fixo no backend (Recomendado) | Estágios canônicos em constante; contagens triviais | |
| Estágios customizáveis | Tabela própria + gestão pela UI; vocabulário pessoal | ✓ |
| Você decide | Agente escolhe no planejamento | |

**User's choice:** Estágios customizáveis (contra o recomendado — registrado como exceção com reversibilidade costly no CONTEXT)

| Option | Description | Selected |
|--------|-------------|----------|
| Essencial (Recomendado) | Empresa, cargo, fonte, link, estágio, datas, notas, JD opcional | |
| Mínimo | Empresa, cargo, estágio, datas | |
| Essencial + detalhes | Essencial + salário, contato do recrutador, modalidade | ✓ |

**User's choice:** Essencial + detalhes

| Option | Description | Selected |
|--------|-------------|----------|
| Derivadas dos eventos (Recomendado) | Envios/entrevistas = eventos datados; contagens mecânicas | ✓ |
| Contadores manuais | Campos numéricos incrementados à mão | |
| Você decide | | |

**User's choice:** Derivadas dos eventos

| Option | Description | Selected |
|--------|-------------|----------|
| Uma candidatura = uma vaga (Recomendado) | Reenvio = evento novo na mesma candidatura; eventos só metadados | ✓ |
| Uma candidatura = uma empresa | Agrupa vagas da mesma empresa | |
| Você decide | | |

**User's choice:** Uma candidatura = uma vaga; currículo enviado continua efêmero

---

## Prazos & follow-ups

| Option | Description | Selected |
|--------|-------------|----------|
| Passivo na UI (Recomendado) | Ordenação por prazo + destaques; sem notificações | ✓ |
| Notificações ativas | Notification API / e-mail; infra nova | |
| Você decide | | |

**User's choice:** Passivo na UI

| Option | Description | Selected |
|--------|-------------|----------|
| Follow-up agendado (Recomendado) | Evento com data futura; pendente até executar | ✓ |
| Só nota em evento | Sem pendentes/agendados | |
| Você decide | | |

**User's choice:** Follow-up agendado

| Option | Description | Selected |
|--------|-------------|----------|
| Destaque, sem mágica (Recomendado) | Vermelho até registrar retorno/adiar; sem ação automática | ✓ |
| Ação automática ao vencer | Sistema move estágio/arquiva sozinho | |
| Você decide | | |

**User's choice:** Destaque sem mágica

| Option | Description | Selected |
|--------|-------------|----------|
| Sem sugestão (Recomendado) | Só exibe o que foi agendado; fase enxuta | |
| Sugestão mecânica | Badge determinístico "considerar follow-up" (N dias sem evento) | ✓ |
| Você decide | | |

**User's choice:** Sugestão mecânica (contra o recomendado; limiar em constante de config, pinado no planejamento)

---

## Criação & visão geral

| Option | Description | Selected |
|--------|-------------|----------|
| Só formulário manual | Zero acoplamento com outros módulos | |
| Formulário + registrar no Currículo (Recomendado) | Pré-preenche JD/idioma da geração | |
| Formulário + registrar no Currículo e nas Respostas | Integração máxima | ✓ |

**User's choice:** Integração máxima

| Option | Description | Selected |
|--------|-------------|----------|
| Lista única + contadores no topo (Recomendado) | Tabela ordenada por prazo; filtros por estágio | |
| Kanban por estágio | Colunas por estágio com drag-and-drop | ✓ (com ressalva) |

**User's choice:** Kanban por estágio — com instrução explícita do usuário: **"mas pega um componente pronto sem criar do 0"** → lib de drag-and-drop no planejamento (@dnd-kit candidata); exceção deliberada ao no-new-frontend-deps, contida a uma lib.

| Option | Description | Selected |
|--------|-------------|----------|
| Sem LLM (Recomendado) | 100% determinístico; funciona sem créditos | ✓ |
| Com LLM opcional | Recursos gerados (resumo semanal etc.) | |
| Você decide | | |

**User's choice:** Sem LLM

| Option | Description | Selected |
|--------|-------------|----------|
| Novo item "Rastreador" (Recomendado) | Quinto item na nav; labels existentes intocados | ✓ |
| Renomear os dois | "Candidatura"→"Respostas"; tracker="Candidaturas" | |
| Você decide | | |

**User's choice:** Novo item "Rastreador"

---

## the agent's Discretion

O usuário não escolheu "você decide" em nenhuma pergunta; os detalhes técnicos delegados implicitamente ao agente estão listados no CONTEXT (driver sqlite3, migração de schema, path do .db, contratos de rotas, escolha final da lib de kanban, semântica dos tipos de evento, encoding do CSV).

## Deferred Ideas

- Restore/import do export JSON+CSV — só o export nasce nesta fase
- Exclusão de candidaturas com confirmação — se o "só arquivar" um dia doer
- Notificações ativas de prazo (Notification API / e-mail)
- Resumo do pipeline gerado por LLM (ex.: semanal)
- Relatórios avançados / sugestões de vocabulário de estágios
