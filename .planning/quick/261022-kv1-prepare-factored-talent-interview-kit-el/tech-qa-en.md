# Technical Q&A + Delivery Cheat Sheet — Factored Talent Interview (English)

- **Use:** anticipated general technical questions with short speakable answers (recruiter screen — breadth, not deep whiteboarding), plus the English-pillar delivery tactics.
- **Rule:** every answer is grounded in `content/profile.md`; the `Grounding:` line under each answer names the supporting profile facts.
- **Pace:** deliver answers in 2–5 sentences at ~140 wpm; answers here are calibrated for 30–60 seconds each.

---

## Part A — Anticipated general technical questions

### Q1. Explain RAG — how do you improve retrieval quality?

> RAG grounds an LLM's answer in your own documents: instead of relying only on what the model memorized, you retrieve the relevant chunks and the model answers from them. To improve retrieval quality, I architected a two-layer ingestion pipeline — a summary layer plus the raw text — with overlapping chunking, semantic search, and re-ranking, so the model sees both the gist and the exact passage. In production this runs over pgvector with thousands of documents indexed, and it cut support response time by up to 80% because the team consults the documents before answering. I've also worked with Qdrant, Chroma, and Pinecone as vector stores.

*Grounding: profile — document-ingestion platform with two-layer pipeline (summary + raw text), overlapping chunking, semantic search + re-ranking; RAG over pgvector with thousands of documents; up to 80% support response-time reduction; Qdrant/Chroma/Pinecone in vector-store experience.*

### Q2. Agents versus chains — when do you use an agent?

> A chain follows a fixed path; an agent decides the next step dynamically based on state. I use agents when the path can't be predicted upfront — Group Verifica is my concrete example: I designed LangGraph agent flows that call tools querying real-time background-check APIs, branching on the risk level each client configures. On the conversational platform, part of the team's design decision was exactly this principle: routing by conversation state instead of a fixed intent tree, so the system interprets the user's request and routes dynamically.

*Grounding: profile — Group Verifica risk engine with LangGraph agent flows and tools querying real-time background-check APIs (direct work); conversational platform state-based dynamic routing vs fixed intent trees (team framing — "part of the team").*

### Q3. What is MCP?

> MCP — the Model Context Protocol — is Anthropic's open standard for exposing tools and data to AI agents in a uniform way, so any compatible client can discover and call them. I'm Anthropic MCP-certified, and I've built production MCP servers: a condominium-ecosystem server with 19 tools under strict Zod schemas and dual stdio/HTTP transport, and a finance server with 35 tools in production. I also co-architected GIA, our multi-MCP orchestration layer, which routes tools to each client based on entitlement and conversation context.

*Grounding: profile — MCP Professional Certification (Anthropic, 2026); 19-tool condominium MCP server with strict Zod schemas and dual transport; 35-tool finance MCP server; GIA co-architected multi-MCP routing by client entitlement + message context.*

### Q4. How do you evaluate LLM output quality?

> I treat evaluation as a system, not a vibe. On the conversational platform, we compare models systematically via OpenRouter — GPT-5-mini, GPT-4.1-mini, Claude 3 Haiku, Gemini, Gemma — and run automated red teaming with promptfoo covering client isolation, auth bypass, and instruction injection, with Langfuse and OpenTelemetry feeding Datadog for observability, and LLM cost audited per conversation, client, and model. The project holds its own engineering bar — 2,870 automated tests across 290 files with a 90% coverage gate in CI — and I develop under it. And on my PUC Minas ABSA project, I built a gold dataset with inter-annotator kappa to measure labeling agreement properly.

*Grounding: profile — systematic model comparison via OpenRouter (GPT-5-mini, GPT-4.1-mini, Claude 3 Haiku, Gemini, Gemma); promptfoo red teaming (client isolation, auth bypass, instruction injection); OpenTelemetry→Datadog + self-hosted Langfuse; per-conversation/client/model cost auditing; 2,870 tests across 290 files with 90% coverage gate; gold dataset with inter-annotator kappa (PUC Minas ABSA).*

### Q5. How do you secure a multi-tenant LLM application?

> First rule: tenancy is resolved server-side and never accepted raw from the channel. On the conversational platform I contribute to, multi-tenancy is enforced on the server with canonical identity across accounts and products, and access goes through JWT with a per-product flow. On the MCP servers I built, I implemented two-layer authentication — a client API key plus an end-user JWT on every call — and I reimplemented RSA-SHA256 request signing in TypeScript, byte-for-byte compatible with a legacy Java protocol that had no formal specification, via reverse engineering.

*Grounding: profile — multi-tenancy resolved server-side, never accepted from the channel (team framing); canonical identity across accounts; JWT auth with per-product flow; two-layer auth (MCP client API key + end-user JWT per call); RSA-SHA256 signing byte-compatible with legacy Java protocol via reverse engineering.*

### Q6. How are your database and SQL fundamentals?

> At H&P I redesigned the relational database structure with software-engineering best practices: 90 tables redesigned with a 70% performance increase and an estimated 60% saving in database-maintenance time, which also prepared the infrastructure for AI workflows. Day to day I work with PostgreSQL and SQLAlchemy. I also owned governance and integrity for the Fundão dam breach registration databases, where accuracy was absolute and 1,200 people were served, because strategic decisions depended on that data.

*Grounding: profile — 90 tables redesigned, 70% performance increase, ~60% maintenance-time saving (H&P); PostgreSQL + SQLAlchemy in stack; Fundão dam breach databases governance, absolute data accuracy, 1,200 people served.*

### Q7. How do you control LLM costs?

> You can't control what you don't measure — so first, cost auditing per conversation, per client, and per model. The proof it works is my lead-generation engine: it generated 239 leads in 78 days for about R$107 of total AI cost, against R$597 to R$1,434 for the same volume on market platforms — roughly 93% savings. And it runs autonomously and continuously, with no dedicated team.

*Grounding: profile — per-conversation/client/model LLM cost auditing; 239 leads in 78 days at ~R$107 total AI cost vs R$597–R$1,434 on market platforms (~93% savings); autonomous and continuous with no dedicated team.*

### Q8. Have you trained or fine-tuned models?

> Honestly: no — I have not done production model training or fine-tuning, and I don't claim it. My depth is applied generative AI: evaluation and model selection, RAG architecture, and agent systems running in production, plus the ML fundamentals I'm building in my Data Science and AI degree at PUC Minas, where I've used scikit-learn on coursework. When a problem genuinely needs fine-tuning I say so — my bias is to first extract everything from good context engineering and retrieval, which is exactly what produced the measured results I've shared.

*Grounding: profile contains NO fine-tuning/training claim — this answer is the honest boundary; scikit-learn appears in PUC Minas coursework (Termômetro da Massa technologies); degree in progress 2023–2027; "measured results" = the production impacts throughout the profile.*

### Q9. How do you align technical work with business needs?

> My pattern is to start from the business bottleneck, not from the technology. At Group Software I implemented the AI meeting-minutes feature that clients adopted organically — 68.1% adoption with no push, 1,446 specialist hours eliminated — because it attacked a real operational cost. The lead-generation engine opened a new revenue line with 239 leads, and Group Verifica reached R$4,750 MRR in its first 45 days. In each case the technical choice was justified by a business number.

*Grounding: profile — meeting-minutes feature, 68.1% organic adoption, 1,446 specialist hours eliminated; lead-gen engine, 239 leads; Group Verifica R$4,750 MRR in first 45 days.*

---

## Part B — English-pillar delivery cheat sheet (delivery tactics from the Factored deck)

### Listening: paraphrase the question back

Repeat the idea in your own words before answering — it proves active listening, confirms you understood, and buys three seconds of thinking time.

- *"If I understood correctly, you're asking about how we handled retrieval quality in production — is that right?"*
- *"So the question is whether I've fine-tuned models myself — let me answer that directly."*

### Vocabulary: "I" + powerful verbs

Use these verbs for your own actions: **led, implemented, resolved, managed, built, architected, pioneered.**

Honesty discipline (matches the profile): "I" is for **direct** work only — Verifica, the meeting-minutes feature, the lead-gen engine, the MCP servers, the H&P database redesign. For team work say "we" / "part of the team" (conversational platform — the team delivered 6 channels, 21 entities, 120 migrations) and "co-architected" (GIA). Never upgrade team work to "I" under interview pressure — it's probeable.

### Grammar: connector bank

Bridge sentences with connectors instead of "and then": **however** (contrast), **which meant that** (consequence), **as a result** (outcome), **in addition** (addition). Example: *"The external APIs could fail, **which meant that** an analysis could stall; **as a result**, I implemented fallback logic."*

### Fluency: calm pace

- ~**140 wpm** — slower than conversation on purpose; clarity beats speed.
- **Silence after numbers** — one full beat after "70%", "R$4,750", "93%". Let the interviewer write it down.
- It's fine to pause mid-answer to think; a calm pause reads as confidence, a rushed answer reads as nerves.

### Pronunciation hints (only where useful)

- **Guilhermino** → "ghee-yer-MEE-noo" (hard G, stress on MEE).
- **LangGraph** → "LANG-graf" (two clean syllables).
- **RAG** → "rag," like the fabric — one syllable, never spelled out.
- **Qdrant** → "KOO-drant" (stress on the first syllable).
- **R$4,750** → say "four thousand, seven hundred and fifty reais."

---

## Quick pre-call checklist

1. Camera at eye level; look at the camera on intro and numbers.
2. Water nearby; calm pace on purpose.
3. Numbers ready: 90% · 30 seconds · 53 · 72% · 196+ · R$4,750 · 45 days · 68.1% · 1,446 · 90 tables · 70% · 2,870 · R$107 · 93% — every one traces to the master profile.
4. If a question touches something outside the profile (fine-tuning, Kubernetes at scale, etc.), say so honestly and pivot to what you have proven.
