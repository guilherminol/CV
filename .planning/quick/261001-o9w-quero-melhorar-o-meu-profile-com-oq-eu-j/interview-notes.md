# Interview notes — quick 261001-o9w

Answers captured live from the user, one message at a time. Will be folded into CONTEXT.md.

## Decisions already locked (AskUserQuestion round)
- **Skills criterion**: Curadoria defensável — extract from code/relatos, show final curated list to user for approval BEFORE writing to profile.
- **Motum PDF**: just a CV generated for the company Motum — NOT an experience; nothing added from it.
- **Local projects in scope**: Flex Diet (yes), Termômetro da Massa (yes), Lab (no), Arquiba (no). Code digging authorized for the two yeses.
- **Interview format**: batch questions in chat, user answers over multiple messages.

## Repo findings (my own scan, 2026-10-01)
- **Flex Diet** (`Documents/Pessoal/Flex Diet`): TypeScript/Node ≥22 MCP server — meal logging with macro balance via WhatsApp (via "Hermes"). Deps: @modelcontextprotocol/express+node+server, better-sqlite3, Express 5, zod, dayjs, csv-parse, tsx; dev: vitest, biome, tsc; Dockerfile + docker-compose.
- **Termômetro da Massa** (`Documents/Pessoal/Termometro da Massa`): academic ABSA pipeline (text mining, PUC) — Atlético Mineiro fan perception per player from X/Instagram comments via Apify. Deps: apify-client, pydantic, pydantic-settings, pyyaml, pandas 3, pyarrow (Parquet), openai, scikit-learn, streamlit; dev: pytest; uv entry points: collect/preprocess/extract/funnel/gold/silver/kappa/annotate-app; cache-first Apify cost ledger; sanitized raw mirror; configs/matches.yaml curation.
- **resume_base.md**: fully mined by prior quick task 260930-sll. Known gaps: Group Software impact 2 weak metric; Nexus Agente impacts []; Financeiro impacts [].

## Round 1 answers (chat)

### A-1 — Group Software RAG ingestion platform metric (replaces weak "alta precisão")
Dual adoption, external + internal:
- **External**: condominiums upload files to the RAG; residents consult them via WhatsApp and via site/app.
- **Internal**: support teams upload their complete documentation and consult it before answering clients → **support response time down by up to 80%**.
- User-supplied metric, no invention needed.

### A-2 — extraction prompt requested
User wants a reusable prompt to run inside each of their other project repos (Nexus/AgendaFacilitada, Financeiro, etc.) so the agent there extracts resume-relevant facts; output gets pasted back into this chat.

### A-3 — additional tech evidence to capture
Azure, CI/CD, testes automatizados, FastAPI, React, Redis — the extraction prompt must also surface this kind of infra/framework evidence. User will paste results here.

## Still pending from interview
- (none — interview closed 2026-10-01; remaining items answered or explicitly ignored below)

## Round 2 answers (chat, 2026-10-01)

- **B-4 H&P stack**: PostgreSQL, Power BI, pandas, Excel.
- **B-5 H&P extra numbers**: no exact time; user's experience says the 90-table redesign saved ~60% of his time ("estava me salvando cerca de 60% do tempo" — user estimate, phrase as approximate). Study groups: AI in general, focused mostly on RAG.
- **C-6 Brooklyn Brothers**: performance improvement ~30%, SEO improvement +10 points (user recall; NOTE: profile currently claims "23% no SEO" — reconcile at approval round). Kenzie/Red Lion: nothing to add.
- **D-7 Nexus Agente**: projects were NOT sold — learning projects only (no sales metrics; keep impacts empty; description should not overstate commercial traction).
- **D-8 Nexus stack**: runs on VPS with **Evolution API** (WhatsApp).
- **E-9 Financeiro**: used by him and his family. Dig the repo for: number of exposed MCP tools + transactions. (User said "no repo tem acesso a vps" — do NOT touch any VPS; stick to repo-local evidence.)
- **E-10 Financeiro**: dig the project for interesting missing things; list main features.
- **F Flex Diet**: **IGNORE this project** — removed from scope (was previously selected; latest answer wins).
- **G Termômetro da Massa**: in development; data already collected via Apify; dig the repo — "tem coisas boas, tipo streamlit pra fazer mvp e etc".
- **H-13 certs**: only the 5 Anthropic ones already in profile.
- **H-14 Hadoop/Spark/Hive + H-15 cloud extras**: ignore; nothing more to add.
- **Redis**: used in **GIA as a queue** (fila).
- **Azure**: hosts the complete Group Software app in containers + managed PostgreSQL, and the models come from there (Azure OpenAI).

## Repo mining results (2026-10-01)

### Financeiro (`Documents/Pessoal/Financeiro`)
- **35 MCP tools** (`@mcp.tool` in 14 modules: budgets, categories, dividends, expenses, fixed_income, goals, incomes, investments, positions, recurring, shared_groups, transactions, whoami)
- **667 test functions** across 51 test files (pytest, asyncio_mode=auto, ruff py312)
- **1,343 commits** from 2026-08-07 to 2026-09-21+ (still active)
- UI pages (NiceGUI): admin, budget, categories, dashboard, investments, login, metas, profile, shared_groups, shell, transactions; API routes for budgets/categories/dividends/investments/shared_groups/transactions/users
- Quotes layer: brapi + coingecko + yfinance_fallback + scheduled job (APScheduler)
- Infra: docker/ (Caddyfile, Dockerfile, docker-compose, backup, init-test-db) on VPS
- Auth: pwdlib[argon2], itsdangerous sessions, MCP bearer middleware (mcp_token.py); deliberate no-OAuth-metadata MCP design (DNS-rebinding transport security, lifespan rebuild)
- Multi-user: shared groups (family use — user + família)
- Backfills: portfolio_backfill, position_entry_backfill; benchmarks, dividends, fixed income with deposit history

### Termômetro da Massa (`Documents/Pessoal/Termometro da Massa`)
- Academic ABSA pipeline (text mining coursework): fan perception per Atlético player from X/Instagram comments
- **7 curated matches** (configs/matches.yaml), real data collected 2026-08-29 → 2026-09-12 (X + Instagram parquets)
- Medallion layers: raw (immutable) → interim (canonical parquet, dedup) → raw-sanitized mirror → silver → gold; **cost ledger** (logs/cost/runs.jsonl, cache-first Apify re-runs at US$0.00)
- **Gold dataset** with annotation log + manifest; inter-annotator **kappa** module; **Streamlit annotation app** (sampling/store)
- **453 test functions** in 26 test files; uv entry points (collect/preprocess/extract/funnel/gold/silver/kappa/annotate-app)
- Academic presentation artifacts (pptx + roteiro) — in development phase
- Stack: Python 3.12, uv, apify-client, pandas 3, pyarrow, OpenAI, scikit-learn, Streamlit, pydantic, pytest

### Proposed skills additions (curated, defensible)
- IA Generativa: **Azure OpenAI**
- Frameworks: **SQLAlchemy**, **NiceGUI**
- Dados: **Power BI**, **pandas**, **Redis**, **Excel**
- Ferramentas: **Docker**
- Competências: **CI/CD**, **Testes automatizados (pytest)**
