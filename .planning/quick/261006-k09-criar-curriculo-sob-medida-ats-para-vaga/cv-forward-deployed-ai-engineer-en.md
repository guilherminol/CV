# Guilhermino Lucas

Belo Horizonte, Minas Gerais, Brazil

Phone: +55 (37) 99928-1391

Email: guilherminolucasc@gmail.com

LinkedIn: linkedin.com/in/guilherminolucas

Languages: English (full professional proficiency), Portuguese (native)

## Professional Summary

Forward Deployed AI Engineer profile: full-stack engineer who ships production generative-AI and agentic systems end to end — from Python/FastAPI backends and LangGraph/LangChain agent flows to TypeScript/React frontends. Three years of AI and data engineering work (since November 2023) building advanced RAG platforms and MCP (Model Context Protocol) tool ecosystems adopted by real clients — production systems, not prototypes: a criminal-background and lawsuit analysis solution that cut analysis time by up to 90% (from nearly a manual day to under 30 seconds), AI-generated assembly minutes adopted by 135 management companies, and a support knowledge base that cut response time by up to 80%. Currently studying Data Science and Artificial Intelligence at PUC Minas.

## Core Skills

- **GenAI — Generative AI and LLMs:** OpenAI, OpenRouter, Azure OpenAI, Claude API, GPT, Gemini, Anthropic, prompt engineering, LLM deployment, speech-to-text, text-to-speech, voice AI
- **Agentic AI, Agents and RAG:** LangChain, LangGraph, advanced RAG, multi-agent systems, agent tool integration, tool/function calling, MCP — Model Context Protocol, semantic search, context engineering, embeddings, vector search, vector databases (pgvector, Qdrant, Chroma, Pinecone)
- **AI Tooling and Ops:** Claude Code, Cursor, GitHub Copilot, Codex, AI evaluations, LLMOps practices (automated red teaming, LLM observability, per-conversation LLM cost auditing), AI observability, CI/CD, Docker, Terraform, Azure, Azure AI Foundry, Vertex AI, pytest
- **Languages and Frameworks:** Python, TypeScript, JavaScript, FastAPI, React, SQLAlchemy, Node.js, Vitest
- **Data and Machine Learning:** PostgreSQL, MongoDB, Redis, data engineering, API development, pandas, Power BI, Machine Learning fundamentals (LLM evaluation and model selection)
- **Ways of Working:** Agile methodologies, Scrum, automated testing, multi-tenancy, hexagonal architecture

## Professional Experience

**Company:** Group Software

**Position/Role:** AI Engineer, June 2025 – Present (Belo Horizonte, Brazil)

**Tasks and responsibilities:**

- Built the Group Verifica solution end to end (frontend, backend, AI, and database) for the condominium and HR markets, shipped with generative AI — under 30 seconds per criminal-background and lawsuit analysis (vs. nearly 1 manual day, ~90% reduction); 53 clients tested within 20 days; 72% demonstrated purchase interest; 196+ queries in production; R$4,750 MRR in the first 45 days
- Architected a document-ingestion platform with a two-layer pipeline (summary + raw text), overlapping chunking, semantic search, and re-ranking — residents consult condo documents uploaded to the RAG via WhatsApp and via site/app, and support teams adopted the platform as their central knowledge base, delivering up to 80% reduction in support response time
- Designed Group Verifica's configurable risk engine with LangGraph agent flows and tools querying real-time background-check APIs — engine configurable in 3 risk levels (Brando/Normal/Rigoroso) with fallback logic and full traceability of every decision, integrating legacy systems and production databases
- Implemented AI-based transcription and automatic generation of assembly minutes and call notices — 482 meeting minutes generated in 49 days of production; 68.1% organic adoption among eligible assemblies (peak 77.3%); 1,446 specialist hours eliminated (482 × 3h per manual minute); 135 management companies adopted the feature
- Built a smart lead-generation engine that spots cross-selling opportunities (insurance, financial, energy) from meeting transcripts — 239 leads generated in 78 days (3.1 leads/day, autonomous and continuous, no dedicated team); total AI cost of ~R$107 for the 239 leads vs. R$597–R$1,434 on market platforms (~93% savings)
- Co-architected and developed GIA, the central AI platform that orchestrates multiple MCP (Model Context Protocol) servers — 3 Group Software products integrated simultaneously via 3 centralized MCP servers with ~20 AI tools exposed; dynamic tool routing by client entitlement and conversational context; JWT auth with a per-product flow; document chat in production via RAG over pgvector (thousands of documents indexed, adopted by internal support as the central knowledge base); recently evolved to a multi-tenant layer with per-tenant isolation and plug-and-play onboarding
- Contributed to Group Software's multichannel conversational platform — the team delivered 6 input channels (3 WhatsApp paths, Telegram, an internal chat API, and human handoff), 21 domain entities, and 120 database migrations in ~3 months of active development (408 commits), with long-term memory between conversations, canonical identity across accounts, and a delivery pipeline to 3 AWS ECS environments provisioned via Terraform
- Developed the production MCP tool set for the condominium-management ecosystem, consumed by the company's conversational AI platform — 19 MCP tools in production with strict Zod schemas for structured outputs, consistent across both transports (local stdio and stateless remote HTTP); two-layer authentication (MCP client API key + end-user JWT per call); RSA-SHA256 request signing reimplemented in TypeScript with byte-for-byte compatibility with the legacy Java protocol
- Upheld the team's engineering quality bar — 2,870 automated tests across 290 files with a minimum 90% coverage gate in CI, hexagonal architecture with LangGraph/LangChain confined to the infrastructure layer, and 28 versioned formal specifications

**Tech stack and tools used:** Python, FastAPI, TypeScript, React, Node.js, Fastify, LangChain, LangGraph, MCP (Model Context Protocol), OpenRouter, OpenAI GPT-4o, Azure OpenAI, Claude API, pgvector, Qdrant, Redis, PostgreSQL, Azure (containers + managed PostgreSQL), AWS ECS, Terraform, Docker, OpenTelemetry, Datadog, Langfuse, promptfoo, pytest, Vitest, Zod

**Use of AI:**

- Builds production LLM applications daily: advanced RAG platforms (two-layer ingestion, overlapping chunking, semantic search, re-ranking) with up to 80% support response-time reduction; autonomous LangGraph agents powering a configurable 3-level risk engine with full decision traceability; AI transcription and generation of assembly minutes (482 minutes in 49 days; 1,446 specialist hours eliminated; 135 management companies); lead generation from meeting transcripts (239 leads at a total AI cost of ~R$107 vs. R$597–R$1,434 on market platforms)
- Runs multi-model orchestration via OpenRouter with systematic model comparison (GPT-5-mini, GPT-4.1-mini, Claude 3 Haiku, Gemini, Gemma) and per-conversation/client/model LLM cost auditing
- Treats LLM safety and operations as first-class: automated red teaming with promptfoo (client isolation, auth bypass, instruction injection) and OpenTelemetry → Datadog plus self-hosted Langfuse observability
- Operates MCP servers that expose product APIs as AI-consumable tools (19 production tools with strict Zod structured-output schemas), plus the GIA multi-MCP orchestration layer routing ~20 tools by entitlement and conversational context
- Uses agentic coding tools daily (Claude Code, Cursor, GitHub Copilot, Codex) across design, implementation, testing, and review

**Company:** H&P

**Position/Role:** Data Scientist | AI Engineer, November 2023 – June 2025 (Belo Horizonte, Brazil)

**Tasks and responsibilities:**

- Redesigned the relational database structure with software-engineering best practices — 90 tables redesigned with a 70% performance increase and an estimated ~60% saving in database-maintenance time, preparing the infrastructure to support AI workflows
- Pioneered the deployment of generative-AI solutions across the company, from identified strategic use cases — up to 80% reduction in report-writing time for the responsible team
- Ran internal AI study groups on RAG, chunks, embeddings, and LLM selection — 12 professionals upskilled during the program
- Owned governance and integrity of the Fundão dam breach (Mariana/MG) registration databases — absolute data accuracy for strategic decisions and high-impact reports, serving 1,200 people

**Tech stack and tools used:** Relational database architecture and governance; generative-AI (LLM) solutions; RAG, chunking, embeddings, and LLM selection (internal AI study program)

**Use of AI:** Pioneered company-wide generative-AI adoption at H&P: shipped LLM solutions that automated report writing (up to 80% time reduction for the responsible team) and built internal AI capability by running study groups on RAG, chunking, embeddings, and LLM selection (12 professionals upskilled).

**Company:** The Brooklyn Brothers

**Position/Role:** Mid-Level Front-End Developer, March 2022 – January 2023

**Tasks and responsibilities:**

- Developed and improved high-performance web interfaces for Rexona, one of the top clients in the global portfolio — 23% SEO improvement plus better user experience, operational efficiency, and accessibility; ~30% performance improvement
- Worked hand-in-hand with development teams in India and the United Kingdom in a global team of 15 people, in a multilingual, agile (Scrum) environment

**Tech stack and tools used:** React, Context API, JavaScript (ES6+), HTML5, CSS3, responsive web components

**Use of AI:** AI tooling was not part of this role, which predates my AI engineering work (2022); my AI track record is documented in the two roles above.

**Company:** Kenzie Academy Brasil

**Position/Role:** Peer Coach (Teaching Assistant), August 2021 – February 2022

**Tasks and responsibilities:**

- Coached 100 students on React, CSS, and HTML (Virtual DOM, styled-components) and versioning with Git/GitHub, who raised the quality of their projects
- Clarified Context API, Redux, API consumption, and unit-testing questions, enabling more effective problem-solving among students

**Tech stack and tools used:** React, CSS, HTML, Git/GitHub, Context API, Redux

**Use of AI:** AI tooling was not part of this role; my AI track record is documented in the two roles above.

**Company:** Red Lion Inglês Britânico

**Position/Role:** English Instructor, March 2020 – May 2020 (Divinópolis, Brazil)

**Tasks and responsibilities:**

- Taught English to students of all age groups, creating didactic materials and interactive activities and tracking progress with tests and constructive feedback

**Tech stack and tools used:** None (classroom teaching role)

**Use of AI:** Not applicable to this teaching role; my AI track record is documented in the two roles above.

## Selected Projects

- **Nexus Agent** — WhatsApp AI agent for appointment scheduling in the health and beauty sectors (AI Appointment Setter), live at AgendaFacilitada.com on a self-hosted VPS; integrates LLMs (LangChain/LangGraph) with calendar APIs and natural-language processing for fluid WhatsApp conversations (Evolution API). Tech: Python, LangChain, LangGraph, WhatsApp Business API, Google Calendar API, Evolution API
- **Financeiro** — Personal finance and investment platform in daily use by my family, in production on a self-hosted VPS (Docker Compose + Caddy + PostgreSQL with automated backups; 1.3k+ commits since 2026-08); exposes 35 MCP tools in production (bearer-authenticated) so AI clients operate the finances in natural language; 667 automated tests (pytest/asyncio) covering finance rules, authentication, and MCP tools. Tech: Python, FastAPI, NiceGUI, SQLAlchemy, PostgreSQL, MCP (Model Context Protocol), Docker Compose, Caddy, pytest
- **Termômetro da Massa** — PUC Minas academic project (text-mining coursework): an ABSA (aspect-based sentiment analysis) pipeline measuring Atlético Mineiro fans' perception of each player from public X (Twitter) and Instagram comments; raw → silver → gold data layers with dedup; LLM-based aspect extraction (OpenAI); gold dataset with inter-annotator kappa (Streamlit annotation app); 453 automated tests. This project is my machine-learning fundamentals and evaluation evidence. Tech: Python, Apify, OpenAI, pandas, scikit-learn, PyArrow (Parquet), Streamlit, pytest

## Education

- **PUC Minas** — Bachelor's degree in Data Science and Artificial Intelligence, August 2023 – July 2027 (in progress)
- **Kenzie Academy Brazil** — Web Development, May 2021 – May 2022

## Certifications

- Model Context Protocol (MCP) Professional Certification — Anthropic (certificate of completion), 2026
- Model Context Protocol: Advanced Topics — Anthropic (certificate of completion)
- Introduction to Model Context Protocol — Anthropic (certificate of completion)
- Introduction to Subagents — Anthropic (certificate of completion)
- Introduction to Agent Skills — Anthropic (certificate of completion)

## Languages

- Portuguese — native
- English — full professional
