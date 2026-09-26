# Phase 3: Resume Vertical Slice - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-26
**Phase:** 3-Resume Vertical Slice
**Areas discussed:** Formato da geração, Cobertura de keywords, Lint de completude, Escopo na tela

> ⚠ **SESSÃO AUTÔNOMA.** O `AskUserQuestion` foi apresentado duas vezes e retornou vazio nas duas (usuário ausente). Seguindo a semântica de auto-mode do próprio workflow, as 4 áreas foram auto-selecionadas para discussão e cada decisão tomada como a opção recomendada, ancorada nas decisões travadas das Fases 1–2. Nenhuma seleção abaixo representa preferência declarada do usuário; todas estão marcadas `[auto]` no CONTEXT.md e são baratas de reverter após revisão.

---

## Formato da geração

| Option | Description | Selected |
|--------|-------------|----------|
| Uma chamada única para todas as seções | Um prompt gerando resumo+bullets+skills num único JSON estrito; menos custo/latência total e coerência cross-seção num passe só | |
| Uma chamada por seção (estágios no gateway) | Três estágios no `_STAGE_SCHEMAS`, orquestrados numa execução; regeneração por seção da Fase 5 fica quase grátis; schemas menores, retry localizado | ✓ |

**User's choice:** *(auto-selecionado — sem resposta)* Uma chamada por seção.
**Notes:** Rationale: REVIEW-01 (Fase 5) exige regeneração por seção de qualquer forma; o gateway é orientado a estágios por construção (Fase 2 D-05); custo extra de tokens já foi despriorizado na Fase 2 (D-02, escala pessoal).

---

## Cobertura de keywords

| Option | Description | Selected |
|--------|-------------|----------|
| Matching determinístico no código (canônico/alias) | Forma canônica OU alias, case/pontuação-insensitive com word-boundary, no idioma da execução; auditável e grátis; paráfrases fora dos aliases aparecem como absent | ✓ |
| Julgamento semântico via LLM | Pega sinônimos fora da lista de aliases, mas o veredito é opinião de modelo — reintroduz a precisão falsa que REQUIREMENTS exclui, e custa uma chamada extra | |

**User's choice:** *(auto-selecionado — sem resposta)* Matching determinístico.
**Notes:** Estado `adjacente` (hook SC4 Fase 2) permanece no modelo, preenchível por heurística leve ou vazio na Fase 3. D-11 (canônico+alias) existe exatamente para evitar falsos negativos do matching mecânico.

---

## Lint de completude

| Option | Description | Selected |
|--------|-------------|----------|
| Aviso não-bloqueante, gerar mesmo com gaps | Usuário vê os avisos e decide; coerente com "never blocks the user" (Fase 1 D-03) e falha-alta (Fase 2 D-03) | ✓ |
| Bloqueia a geração até resolver | Força perfil completo antes de gastar tokens; frustra quando o gap não é resolúvel na hora | |

**User's choice:** *(auto-selecionado — sem resposta)* Aviso não-bloqueante.
**Notes:** Checagens mínimas (SC5): skills/ferramentas do JD ausentes do perfil (canônico+alias), experiências sem impactos/métricas, resumo ausente. Lista refinável em pesquisa/planejamento.

---

## Escopo na tela

| Option | Description | Selected |
|--------|-------------|----------|
| Só as 3 seções geradas | Slice mínimo: resumo, bullets e skills na tela, sem contexto do currículo inteiro | |
| Currículo completo (geradas + passthrough) | 3 seções geradas em destaque (marcadas como geradas) + contato/educação/certs/idiomas passthrough do perfil — a montagem que a Fase 4 renderiza como PDF | ✓ |

**User's choice:** *(auto-selecionado — sem resposta)* Currículo completo.
**Notes:** ProfilePreview (Fase 1 D-12) já estabelece o layout estilo-currículo e a ordem visual que o template de impressão da Fase 4 usará; a prova de valor é mais forte vendo o documento que se enviaria.

---

## Claude's Discretion

*(registrados no CONTEXT.md)* Ordem/roteamento dos endpoints, nomes dos estágios e arquivos de prompt, estrutura de pacote backend, mecânica exata do matcher (normalização/stemming), serialização dos fatos no user message, composição da UI, estratégia de testes (offline mockado + `-m llm` bilíngue).

## Deferred Ideas

Nenhuma — sem input do usuário, nada fora de escopo surgiu.
