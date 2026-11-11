---
phase: "7"
slug: "application-tracker-pipeline-follow-up"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-11"
---

# Phase 7 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register authored at plan time (threat_model blocks in 07-01..07-05-PLAN.md); verified via L1 grep evidence at secure-phase (ASVS L1 short-circuit: threats_open 0 + plan-time register + L1 → no auditor dispatch needed).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser → FastAPI routes | Single-user local app (no auth surface per PROJECT.md); all tracker mutations cross `/api/tracker/*` | Job-search metadata (candidaturas, eventos, notas) — nunca o conteúdo do currículo (D-08) |
| Tracker DB (SQLite) → filesystem | Local store em `data/` (gitignored, bind-mount homelab) | Metadados de candidaturas; parâmetros sempre bound |
| CSV/JSON export → download | Bytes com BOM transportados no envelope 200; abertos pelo usuário em planilha | Campos digitados pelo próprio usuário — sanitização de fórmula obrigatória |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-07-01 | Tampering | tracker service/routes SQL (07-01) | high | mitigate | Parameterized `?` placeholders ONLY; grep L1: zero `execute` com interpolação `$`; roundtrip test + `test_no_candidatura_removal_route` | closed |
| T-07-02 | Tampering | CSV export cells (07-02) | medium | mitigate | `_sanitizar_celula` prefixa apóstrofo quando o 1º char é `= + - @` antes do csv.writer (service.py:512); vetor nomeado no teste; nota: WR-03 (bypass tab/CR OWASP) segue aberto em 07-REVIEW-DISPOSITION.md como melhoria | closed |
| T-07-03 | Tampering | tracker component rendering (empresa, notas, link_vaga) | medium | mitigate | JSX-text-children-only (grep: zero dangerouslySetInnerHTML/innerHTML em tracker); link_vaga como âncora com rel="noreferrer" (TrackerHome.tsx:497); nota: WR-04 (filtro de scheme javascript:) segue aberto como melhoria | closed |
| T-07-04 | Information Disclosure | data/tracker.db at rest (07-01) | low | accept | db sob `data/` gitignored (.gitignore:18) e bind mount homelab; D-08 mantém conteúdo do currículo fora do banco (DDL com 3 tabelas, sem coluna de conteúdo — test pinned) | closed |
| T-07-05 | Denial of Service | tracker request bodies (07-01) | low | mitigate | Pydantic Field max_length em todo campo string (20 ocorrências em models.py); CR-02 reforçado com `DataISO` AfterValidator (commit 2a1ddcc) | closed |
| T-07-06 | Tampering | expanded service/routes SQL (07-02) | high | mitigate | Parameterized placeholders carried from 07-01; reorder por id-list bound como parâmetros; pinned por acceptance criteria nos dois tasks | closed |
| T-07-07 | Denial of Service | new request bodies (07-02) | low | mitigate | extra=forbid + Field bounds nos novos campos (nome 80, observacao 2000, nova_data pattern) — validação antes de qualquer SQL | closed |
| T-07-08 | Information Disclosure | export payload (07-02) | low | accept | Export contém apenas o que o usuário digitou (D-08); servido ao usuário local único via localhost | closed |
| T-07-09 | Denial of Service | client-side length mirroring (07-03) | low | mitigate | maxLength espelhado no form (9 ocorrências) + constantes em ui.ts; bounds do servidor (07-02) permanecem autoritativos | closed |
| T-07-10 | Tampering | association event INSERT (07-04) | high | mitigate | Consome o registrarEvento já endurecido (SQL parametrizado, extra=forbid) — zero SQL novo (grep INSERT no frontend: 0) | closed |
| T-07-11 | Information Disclosure | prefill + association payloads (07-04) | low | accept | JD prefill vive só em React state efêmero; evento persistido é metadata-only por D-08 (coluna de conteúdo não existe) | closed |
| T-07-12 | Tampering | regression audit (07-05) | high | mitigate | FULL suite como gate — 522 passed / 0 failed na verificação final (todas as suítes de fases anteriores contra as adições do tracker) | closed |
| T-07-SC | Tampering | @dnd-kit supply chain | high | mitigate | Legitimacy audit all-OK (3 pacotes, ~42M downloads/sem, sem postinstall) na instalação 07-01; recheck 07-05: diff do package.json contém exatamente os 3 pacotes auditados | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-07-04 | Histórico pessoal de busca fica em SQLite local gitignored + bind mount privado do homelab; single-user localhost sem auth é o modelo do projeto (PROJECT.md) | user (D-01/D-02, discuss-phase) | 2026-11-10 |
| AR-02 | T-07-08 | Export carrega exatamente os dados que o usuário digitou; sem PII de terceiros além do que o próprio usuário registrou | user (D-03, discuss-phase) | 2026-11-10 |
| AR-03 | T-07-11 | Prefill de JD vive em estado efêmero de React (nunca persistido); evento de associação é metadata-only por D-08 | user (D-08/D-13, discuss-phase) | 2026-11-10 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-11 | 13 | 13 | 0 | orchestrator (secure-phase L1 short-circuit, ASVS L1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-11
