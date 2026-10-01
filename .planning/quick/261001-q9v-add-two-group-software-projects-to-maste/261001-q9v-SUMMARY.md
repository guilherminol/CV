---
phase: quick-261001-q9v
plan: 01
subsystem: content-profile
tags: [profile, bilingual, group-software, mcp, quick-task]
requires: [content/profile.md, backend/app/profile/models.py, backend/app/profile/loader.py]
provides: ["two new professional projects in master profile (GIA IEBT, mcp-com) grounded in 261001-q9v-evidence-extractions.md"]
affects: [resume generation, LinkedIn generation, profile preview]
tech-stack:
  added: []
  patterns: ["single-quoted folded YAML scalars (single-line, probe-safe)", "bilingual pt-BR/en pairs on every narrative string"]
key-files:
  created: []
  modified:
    - content/profile.md
decisions:
  - "Commit scope narrowed to content/profile.md only — orchestrator constraint forbids committing the task dir's docs artifacts (PLAN/CONTEXT/evidence/COVERAGE); orchestrator handles the docs commit"
  - "Parity gate corrected from the plan's 118/118 literal to 106/106 — the plan's arithmetic mixed both languages into a per-entry count and dropped the name pairs; real invariant pt==en==90+16 holds exactly"
  - "Mechanical plan-vs-file fidelity check (regex extraction of all 34 locked strings from PLAN.md bytes) used as the authoritative content gate after a typed-assertion circularity was detected; it caught one wrong self-'fix' (invented 'ferramentas (tools)' variant) which was reverted before commit — shipped text is plan-verbatim"
metrics:
  duration: 15 min
  completed: 2026-10-01
status: complete
actuals:
  tokens: 2200
  tasks: 3
  commits: 1
commits: 1
plan_head_before: 099ecbc0c0bd8dd20c7a163d917800b1452609b5
---

# Quick Task 261001-q9v Summary: Two Group Software projects added to master profile

Two locked-decision professional project entries inserted into `content/profile.md` — **Plataforma Conversacional Group Software (GIA IEBT)** (team-safe authorship) and **Servidor MCP do Ecossistema Condominial (mcp-com)** (direct authorship) — in the locked order GIA → GIA IEBT → mcp-com → Nexus Agente → Financeiro → Termômetro da Massa, with zero skills changes and zero production-traffic/monetary claims.

## What Was Done

- **Task 1 — GIA IEBT entry** inserted between the original GIA entry's last impact and Nexus Agente: bilingual name pair, `scope: profissional`, bilingual description (state-based dynamic MCP routing, 6 input channels, MemGPT-inspired long-term memory, canonical identity, per-conversation/client/model LLM cost auditing, active since 2026-07, 3 AWS/ECS/Terraform environments), 14 technologies in locked order, 3 team-safe impacts (`Integra o time…` / `Atua no desenvolvimento…`, metrics attributed to "o time"/"the team") carrying the locked numbers: 6 channels, 21 entities, 120 migrations, 408 commits in ~3 months; 2.870 tests / 290 files / 90% CI coverage gate / 28 versioned specs; server-side multi-tenancy, promptfoo red team, OpenTelemetry→Datadog + Langfuse, model comparison via OpenRouter (GPT-5-mini, GPT-4.1-mini, Claude 3 Haiku, Gemini, Gemma).
- **Task 2 — mcp-com entry** inserted between GIA IEBT and Nexus Agente: bilingual name pair, `scope: profissional`, bilingual description (self-service APIs as MCP tools, dual transport stdio + stateless HTTP, consumed by the company's conversational AI platform, active since 2026-07), 9 technologies in locked order, 3 direct-authorship impacts (`Desenvolveu` / `Implementou` / `Mantém`) carrying the locked numbers: 19 production MCP tools with strict Zod schemas consistent across both transports; two-layer auth (client API key + per-call end-user JWT) and RSA-SHA256 signing byte-compatible with the legacy Java protocol via reverse engineering; 250 Vitest tests on DDD/hexagonal architecture, self-hosted CI/CD with SonarQube.
- **Task 3 — full gate, then commit**: loader tests + fresh load, structural assertion, bilingual parity, additive-diff proof, range-scoped claims/framing negative greps, 24 presence probes — all green before the single commit `d80bbbc`.

## Verification (all executed live)

| Gate | Result |
|------|--------|
| `uv run pytest tests/test_loader.py tests/test_schema.py -q` | 36 passed |
| Fresh `load_profile()` after every task | zero ProfileError |
| Structural assertion (parsed object) | 6 projects in locked order; scopes profissional×3 + pessoal×3; impact counts [4,3,3,0,4,3]; skills untouched (8 groups / 57 items) |
| Mechanical fidelity check vs PLAN bytes | 34/34 locked strings exact-match (names, scopes, descriptions, technologies, 12 impact strings × 2 entries) |
| Bilingual parity | 106/106 pt-BR == en (baseline 90 + 8 key lines per entry per language; pt==en invariant exact) |
| Additive-only diff | 77 insertions, **0 deletions** — original GIA entry and skills byte-unchanged |
| NO-CLAIMS grep over both new entries | 0 hits (MRR, R\$, tráfego, receita, milhões de, revenue, traffic, usuários em produção, users in production) |
| TEAM-FRAMING grep over IEBT range | 0 hits (sozinho, sozinha, por conta própria, single-handed) |
| 24 presence probes | all hit |
| Commit scope | `d80bbbc` = content/profile.md ONLY (1 file changed, 77 insertions); unrelated dirty-tree work (backend candidatura feature) not swept in |

## Deviations from Plan

**1. [Constraint precedence — commit scope]** Plan Task 3's suggested `git add` included this task directory; the execution constraint forbids committing docs artifacts (PLAN.md, CONTEXT.md, evidence file, COVERAGE.md) and reserves them for the orchestrator's docs commit. Committed `content/profile.md` only.

**2. [Rule 1 — plan gate arithmetic] Parity literal corrected 118 → 106.**
- **Found during:** Task 3 gate run
- **Issue:** The plan's expectation "exactly 118/118 after both entries (+14 localized key lines each)" is arithmetically inconsistent with the insertion shape: each entry contributes 8 pt-BR and 8 en key lines (1 name + 1 description + 3 actions + 3 metrics). The plan's +14 mixed both languages into a per-entry count (description pair counted as 2) and dropped the name pairs entirely.
- **Fix:** Gate corrected to the true invariant: pt == en == 106 (90 + 16). Content untouched — no strings were altered to chase the wrong literal.
- **Files modified:** none (gate formula only)
- **Commit:** n/a

**3. [Verification hardening — typed-assertion circularity caught and corrected]** During Task 2 verification, a manually typed exact-string assertion reported the pt-BR description diverging; a "fix" added a `ferramentas (tools)` variant to the file. Direct greps against the PLAN file bytes proved the plan reads `como tools consumíveis` (0 occurrences of the ferramentas variant) — the assertion's expectation was the typo, not the file. The wrong edit was reverted before commit, and the authoritative check was replaced with a mechanical extractor that pulls all 34 locked strings from PLAN.md itself and compares against the YAML-parsed profile (regex-extraction, no hand-typing). The shipped commit contains plan-verbatim text.

## Integrity Notes

- Every number in both entries is verbatim from `261001-q9v-evidence-extractions.md` (408 commits, 21 entities, 120 migrations, 2.870/290/90%/28 for gia-iebt; 19 tools, 250 tests for mcp-com). Neither entry claims production traffic, user counts, or revenue (both repos' extractions explicitly flag no traffic evidence).
- Authorship framing follows the locked decisions: IEBT entry uses team-contribution verbs only, no subsystem attributed to the user; mcp-com uses direct verbs (user's own product work).

## Self-Check: PASSED

- content/profile.md modified and committed (d80bbbc) — FOUND
- Commit measured from ledger: 099ecbc..HEAD = 1 commit — FOUND
- All verification gates above re-runnable from the repo (backend pytest + load_profile + greps)
