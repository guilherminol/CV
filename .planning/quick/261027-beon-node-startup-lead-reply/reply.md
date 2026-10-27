# Resposta ao recrutador — BEON.tech (Node.js + startup/tech lead)

- **Data:** 2026-10-27
- **Contexto:** follow-up da BEON.tech (💙 = branding deles; provável mesma thread da Sol — ajustar o nome se for outra pessoa) perguntando: (1) experiência com Node.js — o quê, onde, quando; (2) experiência em early-stage startup ou papel de tech lead.
- **Fontes:** 100% grounded em `content/profile.md` — mcp-com (linhas 622-687), Group Software (26-122), H&P (123-187), The Brooklyn Brothers (188-234), Kenzie (235-274).

## Ângulo pedido

"Apesar de a IA recente ser mais Python, também construo com Node: MCP server em TypeScript/Node (mcp-com), frontends React/JS, ebackend." + liderança técnica de facto (squad autônomo, 0→1 do Group Verifica) + founder-operador do AgendaFacilitada como experiência early-stage.

## Fatos-chave usados

| Fato | Fonte |
|---|---|
| MCP server TS/Node, ativo desde 2026-07, 19 tools, MCP SDK + Fastify + Zod + OpenTelemetry, transporte duplo stdio/HTTP | mcp-com |
| Auth 2 camadas + RSA-SHA256 byte a byte vs. protocolo Java legado (eng. reversa) | mcp-com |
| 250 testes Vitest, hexagonal/DDD, CI/CD self-hosted (SonarQube, Docker, Terraform) | mcp-com |
| Brooklyn Brothers: Front-end Pleno, 2022-03→2023-01, React/Context API/ES6+ p/ Rexona, +23% SEO, ~30% perf, times Índia/UK | profile |
| Kenzie: Peer Coach 2021-08→2022-02, 100 alunos, React/Redux | profile |
| Group Software: squad autônomo, dono ponta a ponta, influencia arquitetura/stack (OpenRouter, LLMs), define padrões | profile |
| Group Verifica 0→1: R$4.750 MRR em 45 dias, 53 clientes/20 dias, 72% intenção de compra | profile |
| H&P: pioneirou IA generativa, coordenou grupos de estudo | profile |
| AgendaFacilitada.com: micro-SaaS próprio no ar, VPS própria, operação solo | profile |

## Resposta (EN — pronta para enviar)

---

Hi Sol,

Great to hear from you! Happy to share the details on both points.

**1) Node.js experience** — my most recent AI work is mostly Python (LangGraph agents, FastAPI backends), but Node.js/TypeScript is very much part of my day-to-day:

- **Production MCP server at Group Software** (AI Engineer since June 2025; the server live since July 2026). I built the MCP (Model Context Protocol) server that exposes our condominium-management platform's self-service APIs as AI-consumable tools — **19 tools in production**, consumed by the company's conversational AI platform. It's built with the official MCP SDK on **Node.js/TypeScript**, using Fastify, strict Zod input/output schemas, and dual transport (local stdio + stateless remote HTTP) served by the same core. Two things I'm particularly proud of: a two-layer auth scheme (MCP client API key + end-user JWT per call), and **RSA-SHA256 request signing that I reimplemented in TypeScript with byte-for-byte compatibility with the legacy Java protocol** — reverse-engineered from scratch, since there was no formal spec. Quality-wise it runs on 250 automated Vitest tests, a hexagonal/DDD architecture, and a self-hosted CI/CD pipeline (SonarQube, Docker, Terraform-managed deploys).
- **Front-end on the JavaScript/Node ecosystem earlier on:** at **The Brooklyn Brothers** (Mid-Level Front-End Developer, Mar 2022 – Jan 2023) I built high-performance React interfaces (Context API, JavaScript ES6+) for Rexona/Unilever alongside teams in India and the UK — 23% SEO improvement and ~30% performance gains. Before that, I was a Peer Coach at Kenzie Academy Brasil (2021–2022), mentoring 100 students in React, Redux, and JavaScript. Today I also build the TypeScript/React front ends of our AI products at Group Software, so I move comfortably across the whole stack.

**2) Early-stage startup / technical leadership** — I don't carry a formal "Tech Lead" title, but in practice:

- At Group Software I work in a **highly autonomous squad where I own products end to end** — frontend, backend, AI, and database. I influence architectural decisions and stack choices (OpenRouter and our LLM providers among them) and set engineering standards for the team. I also took a product from zero to launch: **Group Verifica**, an AI background-check product that reached **R$4,750 MRR in its first 45 days**, with 53 clients testing in the first 20 days and 72% declaring purchase intent.
- At **H&P** (Data Scientist | AI Engineer, Nov 2023 – Jun 2025) I pioneered the company's adoption of generative AI and ran the internal AI study groups — effectively leading the team's AI upskilling.
- On the startup side, I **run my own micro-SaaS**: AgendaFacilitada.com, an AI appointment setter for health and beauty clinics over WhatsApp, live in production on my own VPS. I designed, built, deployed, and operate the whole thing myself — the full early-stage experience: product decisions, infrastructure, monitoring, and support.

Happy to go deeper on any of these in a call.

Best regards,
Guilhermino Lucas
+55 (37) 99928-1391 · linkedin.com/in/guilherminolucas

---
