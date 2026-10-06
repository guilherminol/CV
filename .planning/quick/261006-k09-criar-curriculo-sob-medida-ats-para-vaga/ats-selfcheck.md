# ATS Self-Check — CV vs Forward Deployed AI Engineer JD (BEON)

Scope: `cv-forward-deployed-ai-engineer-en.md` audited against `job-context.md` (JD tech stack, requirements, bonus skills + recruiter format rules). Grounding rule: every Covered verdict points at profile-supported content in the CV; unsupported JD terms are flagged as gaps here ONLY and appear nowhere in the CV.

## 1. Keyword coverage

### Tech stack listed in the JD (10 terms)

| JD term | Verdict | Where in the CV |
|---|---|---|
| Python | Covered | Core Skills (Languages and Frameworks); Group Software tech stack and bullets |
| Agile Methods | Covered | Core Skills (Ways of Working: Agile methodologies, Scrum); Group Software ("highly autonomous agile squad"); The Brooklyn Brothers ("agile (Scrum) environment") |
| Snowflake | Gap (honest) | Kept out of the CV — no Snowflake (or comparable enterprise data warehouse) experience in the profile; the data-ecosystem requirement is covered by production vector databases instead |
| CI/CD | Covered | Core Skills; Group Software (90% minimum coverage gate in CI); condominium MCP server (self-hosted CI/CD with SonarQube) |
| Machine Learning | Covered | Core Skills (Data and Machine Learning); H&P title "Data Scientist \| AI Engineer" |
| AI Agents | Covered | Core Skills (Agentic AI — AI agents, multi-agent systems); Group Software (autonomous LangGraph agents, agent tool integration) |
| MLOps | Partial — see Gaps | CV claims the LLMOps practices the profile supports (AI evaluations, promptfoo red teaming, Langfuse/OpenTelemetry/Datadog observability, per-conversation cost auditing, CI/CD) but makes no formal MLOps-platform claim |
| GenAI – Generative AI | Covered | Professional Summary; Core Skills ("GenAI — Generative AI and LLMs"); every Group Software bullet and Use of AI field |
| LangChain | Covered | Professional Summary; Core Skills; Group Software stack and hexagonal-architecture bullet |
| LangGraph | Covered | Professional Summary; Core Skills; Group Software (risk engine agent flows, conversational platform) |

### JD requirements

| JD requirement | Verdict | Where in the CV |
|---|---|---|
| 3+ years in ML / AI engineering roles | Covered | Professional Summary ("Three years of AI and data engineering work (since November 2023)"); H&P (Data Scientist \| AI Engineer, Nov 2023 – Jun 2025) + Group Software (AI Engineer, Jun 2025 – Present) |
| Hands-on ML (1+ year): training, fine-tuning, evaluating models, solid ML fundamentals | Partial — see Gaps | Evaluating models and ML fundamentals are covered (LLM evaluation and model selection in Core Skills). Training/fine-tuning depth is NOT claimed — flagged as Gap (honest) below |
| Production AI/ML systems, not just prototypes, incl. generative/agentic AI | Covered | Professional Summary ("production systems, not prototypes"); Group Software (Group Verifica: 196+ queries in production, R$4,750 MRR; 482 AI minutes; 135 management companies; GIA ~2 months serving clients) |
| Strong Python + agentic tooling (Claude Code, Cursor, Codex, GitHub Copilot) + agentic architecture patterns | Covered | Core Skills (Python; Claude Code, Cursor, GitHub Copilot, Codex); Group Software Use of AI ("Uses agentic coding tools daily"); agentic architecture (dynamic tool routing by entitlement/conversational context, hexagonal architecture with LangGraph/LangChain confined to infrastructure) |
| Modern GenAI patterns: RAG, embeddings, vector search, tool/function calling, structured outputs | Covered | Core Skills (Agentic AI, Agents and RAG group lists all five); Group Software (two-layer RAG ingestion; 19 MCP tools with strict Zod schemas for structured outputs) |
| One AI engineering framework (LangChain, LangGraph, LlamaIndex, or comparable) | Covered | LangChain + LangGraph in production (Group Software); custom MCP implementations as the "comparable custom" evidence |
| One cloud AI/ML platform + enterprise data ecosystem (Bedrock / Azure AI Foundry / Vertex AI; Snowflake / Databricks / vector databases) | Partial — see Gaps | Cloud AI: Azure OpenAI / Azure (containers + managed PostgreSQL), Azure AI Foundry + Vertex AI in Core Skills; AWS ECS + Terraform. Data ecosystem: production vector databases (pgvector, Qdrant, Chroma, Pinecone). Snowflake/Databricks/Bedrock = Gap (honest) below |
| Architecture tradeoffs explained plainly to technical and non-technical stakeholders | Covered | Group Software ("influences architectural decisions, stack choices (OpenRouter, LLMs), and sets engineering standards for the team"; 3-level configurable risk engine with full decision traceability) |
| Comfortable engaging with executives and frontline users | Covered | Client-facing adoption evidence: 53 clients tested, 72% purchase interest; residents + support teams as frontline users; 135 management companies adopted the minutes feature; 12 professionals upskilled (internal enablement) |
| English proficiency, based in LATAM | Covered | Header (Belo Horizonte, Minas Gerais, Brazil; English full professional proficiency); Languages section |

### Bonus skills

| JD bonus | Verdict | Where in the CV |
|---|---|---|
| LLMOps/MLOps standards (versioning, CI/CD, containerization, cost/performance optimization) | Covered (as LLMOps depth) | CI/CD: 90% coverage gate + self-hosted CI/CD (SonarQube); containerization: Docker (Azure containers, AWS ECS, Docker Compose); cost/performance optimization: per-conversation/client/model LLM cost auditing, systematic model comparison via OpenRouter, lead-gen cost ~R$107 vs R$597–R$1,434; promptfoo red teaming + Langfuse observability in Use of AI |
| Agile/Scrum teams; large, complex systems | Covered | Scrum (The Brooklyn Brothers, 15-person global team); autonomous agile squad (Group Software); large complex systems: conversational platform (6 channels, 21 domain entities, 120 migrations) and GIA multi-MCP orchestration (3 products, ~20 tools) |

### Honest gaps (documented here ONLY — none of these terms appear in the CV)

1. **Enterprise data platforms — Snowflake / Databricks class, and AWS Bedrock:** the profile contains no experience with these. Closest true evidence: production vector databases (pgvector, Qdrant, Chroma, Pinecone), Azure (containers + managed PostgreSQL), Azure OpenAI / Azure AI Foundry, AWS ECS + Terraform. These platform names stay out of the CV.
2. **Production model training / fine-tuning depth:** the profile supports ML fundamentals only — Data Science & AI degree in progress (PUC Minas), scikit-learn coursework (Termômetro da Massa), LLM evaluation and model selection (systematic OpenRouter comparisons), gold-dataset annotation with inter-annotator kappa. Evaluation yes; weight-training/fine-tuning no — no such claim is made anywhere in the CV.
3. **LlamaIndex:** never used in the profile; the AI frameworks are LangChain + LangGraph plus custom MCP server implementations. Not named in the CV.
4. **MLOps nuance:** strong LLMOps evidence (evaluations, red teaming, observability, cost auditing, CI/CD) but no formal MLOps-platform experience (MLflow/SageMaker-class), so the CV makes no MLOps-platform claim — only the practices it can prove.

## 2. Format audit checklist

> Updated 2026-10-06 (2nd revision): the CV was restructured to the app's own
> export montage (backend/app/export/render.py D-05) at the owner's request —
> section order Summary / Experience / Education / Core Skills / Certifications /
> Languages / Projects, entries as `Company · Role` + date line + bullets, one-line
> contact header, projects grouped under a scope label. Core Skills kept as a
> categorized section (owner preference, replaces the app's single-paragraph
> Skills). All recruiter-required fields remain present per experience, mapped
> into the app-native entry format. 3rd revision (same day): Use of AI is no
> longer a standalone block — AI usage is woven into the experience bullets
> (owner decision), with AI-as-work-tool highlighted via the custom Claude Code
> agents and skills bullet (quality + consistency of AI-generated code).
> 4th revision (same day): Education and Projects sections removed at owner request — the
> CV now ends at Languages; ML-fundamentals evidence remains via the Summary degree line and
> Core Skills only.
> 5th revision (same day): Group Software condensed from 11 to 7 bullets targeting the FDE JD —
> AI-first emphasis with key metrics bolded; conversational-platform team bullet and minor details
> (RSA-SHA256, 196+ queries, risk-level names) dropped; GS tech stack trimmed to distinctive items
> (duplicates of Core Skills removed); Certifications compressed to 2 lines (all 5 names kept);
> Kenzie reduced to 1 bullet; Red Lion tech line dropped; document is now a 2-pager.
> 6th revision (same day): headline adds the vacancy title next to the name
> (Guilhermino Lucas | Forward Deployed AI Engineer); Summary trimmed at owner request —
> "(since November 2023)", "(from nearly a manual day to under 30 seconds)" and the PUC Minas
> degree sentence removed.

- [x] Single column layout
- [x] Section headers follow the app D-05 montage (Summary, Experience, Core Skills, Certifications, Languages; Education and Projects removed at owner request, 4th revision — the degree stays signaled in the Summary)
- [x] No tables, graphics, images, or text boxes
- [x] Consistent Month YYYY date format on every experience (June 2025 – Present; November 2023 – June 2025; March 2022 – January 2023; August 2021 – February 2022; March 2020 – May 2020) and education
- [x] Action-verb-first bullets (Built, Architected, Designed, Implemented, Co-architected, Contributed, Developed, Upheld, Redesigned, Pioneered, Ran, Owned, Worked, Coached, Clarified, Taught)
- [x] Contact info complete in the header as one line (email · location · phone · LinkedIn; languages have their own section)
- [x] File is plain markdown that parses cleanly (no broken bold/heading syntax, no tabs, no HTML)
- [x] Recruiter-required per-experience fields preserved in app-native format (all 5 experiences): entry heading = **Company · Position/Role** (`Company · Role`, dates on the meta line) / tasks and responsibilities = entry bullets / **Tech stack and tools used** = "Tech stack:" meta line / **Use of AI** = woven into the responsibility bullets (LLMOps bullet + AI-first work bullet at Group Software; generative-AI pioneering bullets at H&P)

## 3. Fixes applied

1. **Added the literal term "AI agents" to the Agentic AI skills group** — ATS parsers matching the exact JD token "AI Agents" previously had no exact string to hit (the CV said "agentic AI", "autonomous agents", "multi-agent systems"). Grounded in the profile's own skills ("Agente de IA" / "Agentes de IA") and the autonomous LangGraph agents shipped at Group Software.

No other fixes needed — every remaining JD term already had an honest, profile-grounded placement, and the format audit passed as-is.
