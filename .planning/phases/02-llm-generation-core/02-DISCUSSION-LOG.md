# Phase 2: LLM Generation Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 2-LLM Generation Core
**Areas discussed:** Política de modelos, Meta-prompt files, Keywords PT↔EN, Logs & fixtures

---

## Política de modelos

| Option | Description | Selected |
|--------|-------------|----------|
| Claude Sonnet | Família claude-* — forte em structured outputs (json_schema estrito) e PT-BR; custo médio-alto por run | ✓ |
| GPT (OpenAI) | Família gpt-* — sólida em json_schema nativo; PT-BR bom | |
| Gemini | Família gemini-* — melhor custo-benefício (Flash barato e rápido) | |
| Outro modelo | DeepSeek, Llama, Mistral… | |

**User's choice:** Claude Sonnet
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Global único | Um slug único no config para tudo; trocar = editar 1 linha | ✓ |
| Por estágio | Slug global + override opcional por estágio | |

**User's choice:** Global único
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Falhar alto | Erro claro + log completo; sem fallback automático — coerente com o fail-fast do Phase 1 | ✓ |
| Fallback secundário | Tenta modelo secundário do config antes de falhar | |

**User's choice:** Falhar alto
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Travas no config | max_tokens por estágio + teto de retries (ex.: 2) fixados no config | ✓ |
| Sem trava | Sem limites explícitos; custo por run imprevisível | |

**User's choice:** Travas no config
**Notes:** —

---

## Meta-prompt files

| Option | Description | Selected |
|--------|-------------|----------|
| 1 arquivo/estágio | prompts/keyword-extraction.md etc.; cada estágio isolado; Fase 3+ só adiciona arquivos | ✓ |
| Arquivo único | Um arquivo com todos os prompts por seções | |

**User's choice:** 1 arquivo/estágio
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Markdown puro | Só o texto do prompt; zero mágica | |
| MD + frontmatter | YAML frontmatter (id, params) + corpo MD; Pydantic strict extra=forbid, typo falha alto como o perfil | ✓ |

**User's choice:** MD + frontmatter
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| System + user message | Arquivo = system prompt; vaga/perfil/idioma na user message montada pelo gateway; sem parser de template | ✓ |
| Variáveis {{template}} | Placeholders substituídos pelo gateway; controla onde cada input aparece, mas templating a manter | |

**User's choice:** System + user message
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| prompts/ na raiz | Irmã de content/ — prompts são conteúdo versionado, fora do código; leitura fresh por run (D-15) | ✓ |
| Dentro do backend | backend/app/prompts/ — mistura código com conteúdo editável | |

**User's choice:** prompts/ na raiz
**Notes:** —

---

## Keywords PT↔EN

| Option | Description | Selected |
|--------|-------------|----------|
| LLM na mesma chamada | Extração retorna cada keyword com forma {en, pt}; termos técnicos idênticos; glossário da Fase 6 corrige depois | ✓ |
| Glossário estático agora | Arquivo glossário PT↔EN mantido à mão desde já | |
| Híbrido | LLM mapeia + glossário opcional como override desde a Fase 2 | |

**User's choice:** LLM na mesma chamada
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Categorias fixas | Competências, ferramentas, títulos de vaga, certificações (ROADMAP SC4/RESUME-02) | ✓ |
| Lista plana | Sem classificação; Fase 3 re-classificaria | |

**User's choice:** Categorias fixas
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Canônica + aliases | Canonical "Kubernetes" + aliases "k8s"; cobertura conta canônica OU alias | ✓ |
| Literal | k8s e Kubernetes seriam keywords distintas | |

**User's choice:** Canônica + aliases
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| 1 prompt único | Instruções que servem para JD ou objetivo — "input-agnostic" literal do roadmap | ✓ |
| 2 prompts afinados | Mesmo schema, instruções por tipo de input | |

**User's choice:** 1 prompt único
**Notes:** —

---

## Logs & fixtures

| Option | Description | Selected |
|--------|-------------|----------|
| JSONL + resumo | logs/runs.jsonl (gitignored), uma linha por chamada (estágio, modelo, tokens, custo, latência, idioma) + resumo no terminal; alicerce do run store 5/6 | ✓ |
| Terminal only | Só uvicorn; sem histórico consultável | |

**User's choice:** JSONL + resumo
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Por chamada | Cada tentativa vira uma linha com nº da tentativa; audita retries e custo exato | ✓ |
| Por estágio | Uma linha por estágio após retries; mais limpo, esconde custo por tentativa | |

**User's choice:** Por chamada
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| pytest -m llm | Testes marcados que chamam a API real sob demanda: uv run pytest -m llm | ✓ |
| Script CLI | Comando próprio fora do pytest com saída amigável | |
| Ambos | Gate no pytest + CLI para inspecionar saída | |

**User's choice:** pytest -m llm
**Notes:** —
| Option | Description | Selected |
|--------|-------------|----------|
| Mocks offline | Suíte regular 100% offline simulando o OpenRouter; API real só no -m llm | ✓ |
| Parcialmente real | Alguns testes regulares chamam a API real | |

**User's choice:** Mocks offline
**Notes:** —

## Claude's Discretion

- Slug exato do Claude Sonnet (validado pelo fixture harness antes de pinar; vive no config)
- Mecânica do cliente OpenRouter (SDK OpenAI-compatível vs httpx cru, enforcement de structured outputs, retry/backoff)
- Schema das linhas JSONL (nomes de campos), formato do resumo no terminal, rotação de log
- Conjunto exato de chaves do frontmatter dos prompts e o modelo Pydantic correspondente
- Layout do pacote app/llm/, serialização dos fatos do perfil na user message
- Biblioteca/técnica de mock offline; textos dos fixtures (JD + objetivo realistas, ambos os idiomas)

## Deferred Ideas

None — a discussão ficou dentro do escopo da fase. (Glossário PT↔EN é trabalho da Fase 6, já agendado no roadmap.)
