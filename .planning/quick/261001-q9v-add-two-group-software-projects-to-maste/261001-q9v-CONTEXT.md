# Quick Task 261001-q9v: Add two Group Software projects (MCP orchestrator + product MCP server) - Context

**Gathered:** 2026-10-01
**Status:** Ready for planning

<domain>
## Task Boundary

Add two NEW Group Software projects to the master profile (`content/profile.md`) from user-pasted repo extractions (evidence: `261001-q9v-evidence-extractions.md` next to this file):

1. **gia-iebt** — the conversational MCP orchestrator (team project). NOTE: internally also called "GIA" but it is a DIFFERENT project from the "GIA — Plataforma de IA Group Software" entry already in the profile; the profile name must avoid that collision.
2. **mcp-com** — the condominium-management product's MCP server, on which the user works directly.

Same invariants as quick 261001-o9w: edits stay inside the YAML frontmatter schema (extra=forbid strict loader must stay green), bilingual pt-BR/en on every added narrative string, strict no-invention — every number comes from the evidence file. User decisions from chat (2026-10-01): rename the orchestrator entry to avoid GIA confusion; explicitly record that it was NOT built solo.

</domain>

<decisions>
## Implementation Decisions

### Orchestrator entry name (avoid GIA collision)
- **pt-BR name:** `Plataforma Conversacional Group Software (GIA IEBT)`
- **en name:** `Group Software Conversational Platform (GIA IEBT)`
- (Orchestrator default — user asked for a rename to avoid confusion; the recommended descriptive option was chosen after the confirmation question went unanswered.)

### Authorship framing (LOCKED by user in chat)
- gia-iebt was **not built by the user alone** — other devs involved. Impacts must use team-safe contribution verbs ("Atua no desenvolvimento de…", "Integra o time que…", "…do time") and team-attributed metrics must say "o time". NO attribution of specific subsystems to the user (no subsystem-level confirmation was obtained). Do NOT claim solo architecture ownership.
- mcp-com IS the user's direct work ("produto que estou atuando diretamente") — direct-authorship verbs allowed ("Desenvolveu", "Implementou").

### No production-traffic claims
- Both extractions explicitly state there is NO evidence of real production traffic in the repos. Status phrasing: gia-iebt "em desenvolvimento ativo" (in active development); mcp-com "ativo" with "19 tools no conjunto de produção" (production tool set) — but NO user counts, NO traffic volumes, NO revenue anywhere.

### New project entry 1 — Plataforma Conversacional Group Software (GIA IEBT)
- `scope: profissional`.
- Bilingual description: centralized MCP system that interprets the user's demand inside a conversation and routes dynamically to the right AI flow/agent based on conversation STATE (not a fixed intent tree); multichannel (3 WhatsApp paths — own integration, uazapi, Twilio — plus Telegram, internal chat API, and human-handoff channel); long-term memory between conversations (MemGPT-inspired, per-client/per-user scoping); canonical identity across accounts/products; LLM cost auditing per conversation/client/model; in active development since 2026-07 with delivery pipeline to 3 AWS environments (ECS, Terraform).
- `technologies` (repo facts, curated): Python 3.13, FastAPI, LangGraph, LangChain, OpenRouter, PostgreSQL (SQLAlchemy async + Alembic), Redis, Qdrant, Terraform (AWS ECS), OpenTelemetry, Langfuse, Docker, pytest, promptfoo.
- `impacts` (3, team-safe verbs, all numbers from evidence):
  1. Team-built multichannel conversational platform on a state-based dynamic-routing architecture — metric: "o time entregou 6 canais de entrada (3 vias de WhatsApp, Telegram, API interna e transbordo humano), 21 entidades de domínio e 120 migrations em ~3 meses de desenvolvimento ativo (408 commits)".
  2. Engineering quality bar — metric: "2.870 testes automatizados em 290 arquivos com gate mínimo de 90% de cobertura no CI; 28 especificações formais versionadas; arquitetura hexagonal com LangGraph/LangChain confinados à infraestrutura".
  3. Security and LLM operations — metric: "multi-tenancy resolvido no servidor (nunca aceito do canal), identidade canônica entre contas, red team automatizado com promptfoo (isolamento entre clientes, bypass de auth, injeção de instruções), observabilidade OpenTelemetry→Datadog + Langfuse self-hosted e auditoria de custo de LLM por conversa/cliente/modelo; modelos avaliados comparativamente via OpenRouter (GPT-5-mini, GPT-4.1-mini, Claude 3 Haiku, Gemini, Gemma)".

### New project entry 2 — Servidor MCP do Ecossistema Condominial (mcp-com)
- `scope: profissional`. Name pt-BR: `Servidor MCP do Ecossistema Condominial (mcp-com)`; en: `Condominium Ecosystem MCP Server (mcp-com)`.
- Bilingual description: MCP server exposing the condominium-management ecosystem's self-service APIs (login, unit data, boletos in PDF individual/aggregated, "nada consta" certificates, financial balancete, knowledge search) as AI-consumable tools; official MCP SDK; dual transport (stdio local + stateless HTTP remote); consumed by the company's conversational AI platform as a client; active since 2026-07.
- `technologies`: TypeScript, Node.js, MCP SDK (oficial), Fastify, Zod, Vitest, OpenTelemetry, Terraform, Docker.
- `impacts` (3, direct-authorship verbs, all numbers from evidence):
  1. Developed the production MCP tool set for the condominium ecosystem — metric: "19 tools MCP em produção com schemas Zod estritos de entrada/saída, truncamento e paginação consistentes nos dois transportes (stdio e HTTP remoto)".
  2. Two-layer auth + cryptographic request signing — metric: "autenticação em duas camadas (chave de API do cliente MCP + JWT do usuário final por chamada, nunca exposto como parâmetro aberto); assinatura RSA-SHA256 reimplementada em TypeScript com compatibilidade byte a byte com o protocolo Java legado, via engenharia reversa de protocolo sem especificação formal".
  3. Quality and delivery — metric: "250 testes automatizados (Vitest) em arquitetura DDD/hexagonal com registry composto de tools; CI/CD self-hosted com SonarQube, build Docker e deploy remoto controlado via Terraform".

### Skills section — NO additions
- The defensible-curation criterion (locked in 261001-o9w) requires the user's personal confirmation, which was NOT obtained for this batch (AWS, Terraform, OpenTelemetry, Qdrant, Fastify, etc.). Therefore the global `skills:` section is UNCHANGED. The new stacks appear only inside the two projects' `technologies` lists (repo facts, not personal claims). A follow-up task can promote technologies to skills after user confirmation.

### Ordering
- Professional projects grouped first, most recent major work first: GIA (original, untouched) → Plataforma Conversacional Group Software (GIA IEBT) → Servidor MCP do Ecossistema Condominial (mcp-com) → Nexus Agente → Financeiro → Termômetro da Massa. (Orchestrator default; confirmation question unanswered.)

### Existing GIA entry — UNTOUCHED
- The original "GIA — Plataforma de IA Group Software" entry keeps its name and content byte-for-byte. No edits, no cross-references.

### Out of scope
- No changes to experiences, certifications, languages, education, summary, or contact.
- No global skills changes (see above).
- Flex Diet stays out (prior decision); Motum stays out (prior decision).

</decisions>

<specifics>
## Specific Ideas

- Preserve existing YAML conventions: 2-space indent, single-quoted narrative scalars (doubled apostrophes) — the new descriptions contain ": " so they MUST be single-quoted; projects keyed `name` (LocalizedText), `scope`, `description` (LocalizedText), `technologies` (list), `impacts` (list of {action, metric, context?} LocalizedText pairs — context optional).
- Every number above is traceable to `261001-q9v-evidence-extractions.md`; team metrics carry "o time"; no traffic/user/revenue claims.
- The strict loader (`backend/app/profile/loader.py`) must stay green after edits.

</specifics>

<canonical_refs>
## Canonical References

- `261001-q9v-evidence-extractions.md` (this task dir) — verbatim repo extractions, the grounding source.
- `content/profile.md` — the file being edited.
- `backend/app/profile/models.py` + `backend/app/profile/loader.py` — schema contract.
- Prior precedent: `.planning/quick/261001-o9w-quero-melhorar-o-meu-profile-com-oq-eu-j/261001-o9w-SUMMARY.md` (verification pattern reused).

</canonical_refs>
