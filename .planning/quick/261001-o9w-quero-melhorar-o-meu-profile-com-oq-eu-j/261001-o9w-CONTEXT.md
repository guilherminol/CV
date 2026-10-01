# Quick Task 261001-o9w: Deep-dive enrichment of master profile from projects and past work - Context

**Gathered:** 2026-10-01
**Status:** Ready for planning

<domain>
## Task Boundary

Enrich the Career Tailor master profile (`content/profile.md`) by diving deep into Guilhermino's projects and past work — surfacing more skills, technologies, and metric-backed impacts. All changes stay inside the existing YAML frontmatter schema (backend/app/profile/models.py, extra=forbid); bilingual (pt-BR base + en mirror) on every added narrative string; strict no-invention policy — every metric is either user-supplied (marked approximate where the user said so) or grounded in a repository artifact. The full interview evidence lives in `interview-notes.md` next to this file.

</domain>

<decisions>
## Implementation Decisions

### Skills criterion (locked)
- **Curadoria defensável**: only technologies the user defends in an interview enter the global skills section. The exact list below was APPROVED by the user — no additions beyond it.

### Group Software — experience impact 2 metric REPLACED
- Old metric "Alta precisão na recuperação de contextos complexos" (en: "High precision in retrieving complex contexts") is replaced by the user-supplied dual-adoption metric:
  - pt-BR: "Adoção em duas frentes: moradores consultam documentos do condomínio subidos ao RAG via WhatsApp e via site/app; times de suporte adotaram a plataforma como base de conhecimento central, consultando os documentos antes de responder — redução de até 80% no tempo de resposta do suporte"
  - en mirror: "Dual adoption: residents consult condo documents uploaded to the RAG via WhatsApp and via site/app; support teams adopted the platform as their central knowledge base, consulting documents before answering — up to 80% reduction in support response time"
- Action/context lines of that impact stay unchanged.

### Group Software — GIA project technologies enriched
- GIA `technologies` list gains: `Redis (filas)`, `Azure (containers + PostgreSQL gerenciado)`, `Azure OpenAI` (en equivalents in parentheses per existing convention — keep list pt-first like existing entries).
- User-supplied grounding: Redis is used in GIA as a queue; Azure hosts the whole app in containers + managed PostgreSQL; models come from Azure OpenAI.

### H&P — 90-table impact gains time-saving estimate
- Impact 1 metric ("90 tabelas redesenhadas, com aumento de performance de 70%...") gains: "economia estimada de ~60% do tempo de manutenção das bases" (en: "estimated ~60% saving in database-maintenance time"). Mark as estimate in phrasing exactly like that — do NOT present as measured.

### The Brooklyn Brothers — performance added, SEO number KEPT
- Keep existing "Melhoria de 23% no SEO" / "23% SEO improvement" EXACTLY as is.
- Add performance to that same metric: pt-BR "...; melhoria de ~30% em performance" / en "...; ~30% performance improvement". The user's "+10 pontos" recollection is DROPPED (decided 2026-10-01).

### Nexus Agente — honest status + stack
- Description rewritten to learning-project framing (no commercial traction implied):
  - pt-BR: "Projeto pessoal de aprendizado: agente de IA para WhatsApp focado em agendamentos para os setores de saúde e beleza (AI Appointment Setter), no ar em AgendaFacilitada.com em VPS própria. Integra LLMs (LangChain/LangGraph) com APIs de calendário e processamento de linguagem natural para conversas fluidas via WhatsApp (Evolution API)."
  - en mirror accordingly ("personal learning project", "live at AgendaFacilitada.com on a self-hosted VPS", "WhatsApp (Evolution API)").
- `technologies` gains: `Evolution API`.
- `impacts` STAYS `[]` — project was never sold; nothing invented.

### Financeiro — description enriched + 4 NEW repo-grounded impacts
- Description gains: market-quote sources (brapi, CoinGecko, yfinance as fallback) consolidated into one portfolio; multi-user family use; automated backups on the VPS.
- New impacts (all repo-verifiable, bilingual):
  1. **35-tool finance MCP server with bearer auth** — action: exposes budgets/goals/transactions/investments/fixed income/dividends/shared groups to AI clients; metric: "35 tools MCP em produção; autenticação bearer; clientes de IA operam as finanças em linguagem natural" (source: `app/mcp/tools/`, 14 modules).
  2. **Real multi-user family platform** — metric: "em uso diário pela família do autor; grupos compartilhados multiusuário; VPS própria com Docker Compose + Caddy + backups automatizados; 1.3k+ commits desde 2026-08".
  3. **Automated market quotes** — metric: "cotações agendadas de 3 fontes (brapi, CoinGecko, yfinance como fallback) consolidadas em portfólio único de ações, cripto e renda fixa" (source: `app/quotes/`).
  4. **Engineering quality** — metric: "667 testes automatizados (pytest/asyncio) cobrindo regras financeiras, autenticação e tools MCP" (source: `tests/`).

### Termômetro da Massa — NEW project entry (scope: pessoal)
- Bilingual description: academic ABSA (aspect-based sentiment analysis) pipeline from PUC Minas text-mining coursework measuring Atlético Mineiro fans' perception of each player from public X (Twitter) and Instagram comments; Apify collection (cache-first with cost ledger); raw→silver→gold data layers with dedup and sanitized mirror; LLM-based aspect extraction (OpenAI); gold dataset with inter-annotator kappa; Streamlit annotation app; 7 matches collected; in development.
- `technologies`: Python 3.12, Apify, OpenAI, pandas, PyArrow (Parquet), scikit-learn, Streamlit, pytest, uv.
- Impacts (repo-grounded, bilingual):
  1. End-to-end ABSA pipeline with raw→silver→gold layers and 453 automated tests.
  2. Cache-first Apify collection with per-run cost ledger — 7 curated matches across X and Instagram without unbounded spend.
  3. Gold-set discipline: Streamlit annotation app with sampling, manifest, and inter-annotator kappa.
- Position: after Financeiro (last in projects list).

### Skills additions (APPROVED list — exactly these, nothing more)
- IA Generativa: `Azure OpenAI`
- Frameworks: `SQLAlchemy`, `NiceGUI`
- Dados: `Power BI`, `pandas`, `Redis`, `Excel`
- Ferramentas: `Docker`
- Competências: `CI/CD`, `Testes automatizados (pytest)`

### Out of scope (explicitly decided)
- Flex Diet project: IGNORED (user decision 2026-10-01, overrides earlier inclusion).
- Motum PDF: just a generated CV for a company — no profile content from it.
- Lab/Arquiba folders: not projects for the profile.
- Hadoop/Spark/Hive skills: ignored (user decision).
- Certifications: only the existing 5 Anthropic ones; no additions.
- Nexus Agente sales metrics: none exist — impacts stay empty.

</decisions>

<specifics>
## Specific Ideas

- Existing profile conventions to preserve: 2-space YAML indent, single-quoted narrative values (apostrophes doubled), bilingual `pt-BR`/`en` pairs on every localized field, projects ordered GIA → Nexus → Financeiro → (new) Termômetro, skills items in plain sequence (first-occurrence-wins dedupe downstream, no sort).
- Grounding evidence for every number is recorded in `interview-notes.md` (repo paths + user attributions). The strict loader (`backend/app/profile/loader.py`) must stay green after edits.

</specifics>

<canonical_refs>
## Canonical References

- `interview-notes.md` (this task dir) — full interview transcript, repo-mining evidence, and user attributions per number.
- `content/profile.md` — the file being edited.
- `backend/app/profile/models.py` + `backend/app/profile/loader.py` — schema contract the edits must satisfy.

</canonical_refs>
