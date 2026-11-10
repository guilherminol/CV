# Phase 7: Application Tracker — Pipeline & Follow-up - Research

**Researched:** 2026-11-10
**Domain:** Local SQLite persistence (Python stdlib `sqlite3` + FastAPI), deterministic event-sourced counters, deadlines/follow-ups, React 19 kanban with `@dnd-kit`
**Confidence:** HIGH (codebase patterns verified in-repo; external choices verified against registries/docs; semantics proposals marked as discretion)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Implementation Decisions

**Persistência (a reversão deliberada da restrição file-based)**
- **D-01:** **SQLite local para os dados do tracker** — reversão PONTUAL, só para este módulo, da restrição "file-based (Markdown/YAML in git), not a database" do PROJECT.md; o perfil mestre continua em Markdown/YAML. — **Reversibility:** costly — desfazer toca a camada de armazenamento inteira (rotas CRUD, schema, path/bind-mount do .db); migrar de volta para arquivos reescreveria todos os call sites de leitura/escrita.
- **D-02:** **Homelab é a fonte da verdade** — o .db vive num bind mount próprio no container (como content/ e logs/ hoje); a instância local serve só para desenvolvimento, com banco descartável.
- **D-03:** **Export na UI** — botão que exporta tudo (JSON completo + CSV para planilha); zero infra nova; restore/import fica para fase futura.
- **D-04:** **Só arquivar, nunca apagar** — candidatura encerrada (rejeitada/desistiu) fica no banco com estágio final + data; o histórico alimenta as contagens; NENHUM caminho destrutivo nesta fase (exclusão é deferred).

**Estágios & campos**
- **D-05:** **Estágios customizáveis** (o usuário rejeitou o enum fixo recomendado) — tabela de estágios no banco + gestão pela UI; o vocabulário é pessoal e as contagens por estágio refletem isso. — **Reversibility:** costly — migrar para enum fixo depois exigiria migração de dados de todas as candidaturas existentes + remoção da UI de gestão.
- **D-06:** **Campos por candidatura — essencial + detalhes:** empresa, cargo, fonte (onde viu), link da vaga, estágio atual, datas (aplicação, eventos, prazo de retorno), notas livres, texto da JD opcional; MAIS faixa salarial, contato do recrutador e modalidade (remoto/híbrido/presencial).
- **D-07:** **Contagens derivadas dos eventos** — cada envio de currículo e cada entrevista é um evento datado na candidatura; contadores calculados mecanicamente dos eventos, nunca números digitados à mão (honestidade mecânica das fases anteriores).
- **D-08:** **Uma candidatura = uma vaga; eventos guardam só metadados** (data, tipo, idioma, observação) — o conteúdo do currículo enviado continua efêmero, fora do banco; reenvio na mesma vaga = evento novo na mesma candidatura.

**Prazos & follow-ups**
- **D-09:** **Prazos passivos na UI** — visão geral ordena por proximidade de prazo e destaca "vence em X dias" na família de cores aprovada (âmbar=aviso, vermelho=erro); sem notificações ativas nesta fase.
- **D-10:** **Follow-up agendado** — evento com data futura + nota; aparece como pendente até a data; ao registrar que executou, vira evento datado normal.
- **D-11:** **Vencido = destaque, sem mágica** — "venceu há X dias" em vermelho até o usuário registrar retorno ou adiar; nenhuma ação automática de estágio/arquivamento ao vencer.
- **D-12:** **Sugestão mecânica de follow-up** (o usuário escolheu ter, contra o recomendado) — badge determinístico "considerar follow-up" quando a candidatura fica N dias sem evento; limiar em constante de config (valor exato pinado no planejamento).

**Criação & visão geral**
- **D-13:** **Integração máxima** — três portas de entrada: formulário manual na página do tracker; botão "Registrar candidatura" na tela de resultado do Currículo (pré-preenche o texto da JD e o idioma da geração; empresa/cargo o usuário digita — extração mecânica de JD não é confiável); associação na tela de Respostas de candidatura.
- **D-14:** **Kanban por estágio com componente PRONTO** (o usuário foi explícito: "pega um componente pronto sem criar do 0") — lib de drag-and-drop escolhida no planejamento; candidata `@dnd-kit/core` (mantida, React 19); `react-beautiful-dnd` deprecada, evitar. **Exceção deliberada** à convenção no-new-frontend-deps — contida a UMA lib; sem runner de testes JS novo (tsc -b continua a trava). — **Reversibility:** reversible — trocar de lib depois é custo localizado na UI do kanban.
- **D-15:** **Sem LLM no tracker** — 100% determinístico (CRUD + eventos + contagens + prazos); independe de créditos OpenRouter (esgotados desde a Fase 6).
- **D-16:** **Novo item "Rastreador" na nav** — quinto item em NAV_ITEMS; o label "Candidatura" (módulo de respostas) permanece intocado — zero risco de quebrar strings/testes existentes.

### Claude's Discretion
- Mecanism técnicos: driver SQLite (stdlib `sqlite3` recomendado — zero dependência nova no backend), versionamento/migração de schema do banco, path do .db em `app/config.py` (env-overridável para o compose), contrato das rotas CRUD, DTOs Pydantic estritos.
- Escolha final da lib de kanban e o padrão de integração dela com React 19 + Tailwind.
- Métrica exata dos contadores globais (enviadas, entrevistas, ativas) e a semântica de cada tipo de evento.
- Detalhes de deploy do compose no homelab (bind mount do .db) e do export CSV (encoding, colunas).

### Deferred Ideas (OUT OF SCOPE)
- Restore/import do export JSON+CSV — só o export nasce nesta fase (D-03)
- Exclusão de candidaturas com confirmação — se o "só arquivar" (D-04) um dia doer
- Notificações ativas de prazo (Notification API / e-mail) — D-09 deixou passivo de propósito
- Resumo do pipeline gerado por LLM (ex.: semanal) — D-15 manteve o tracker sem LLM
- Sugestões de melhoria do vocabulário de estágios / relatórios avançados — kanban + contadores cobrem o essencial

Continua Out of Scope do projeto: extração de vaga por URL, auto-apply, multi-usuário.
</user_constraints>

<phase_requirements>
## Phase Requirements

ROADMAP.md has no mapped requirement IDs for Phase 7 (`requirements: TBD`). The planner must
derive them from 07-CONTEXT.md. PROPOSED IDs below (planner may renumber) map each to the
research support that enables it:

| Proposed ID | Description (from CONTEXT/STATE) | Research Support |
|----|-------------|------------------|
| TRK-01 (D-01/D-02) | SQLite persistence with schema versioning; .db path in `app/config.py` env-overridable for the homelab bind mount | Standard Stack (stdlib sqlite3); Pattern 1 (connection per request); Pattern 2 (user_version migrations); Pattern 3 (config path) |
| TRK-02 (D-05/D-16) | Customizable pipeline stages; kanban UI; "Rastreador" as fifth nav item | Pattern 4 (stages table + deletion policy); Pattern 5 (dnd-kit integration); Pattern 7 (nav/view switch — verbatim NAV_ITEMS quote) |
| TRK-03 (D-06/D-13) | Application CRUD with essential + detail fields; three entry points (manual form, "Registrar candidatura" prefill, Candidatura association) | Pattern 8 (envelope CRUD contract); Pattern 9 (prefill wiring through App state); Pitfall 6 |
| TRK-04 (D-07/D-08) | Event-sourced counters (enviados, entrevistas, ativas); metadata-only events | Pattern 6 (event semantics + derived counters); Don't Hand-Roll |
| TRK-05 (D-09–D-12) | Deadlines overview sorted by proximity with amber/red highlighting; scheduled follow-up pending until date; overdue highlight; deterministic follow-up suggestion badge (threshold constant) | Pattern 6 (date-only model); Pattern 6b (follow-up pending/overdue/execute semantics); Assumptions A2-A3 |
| TRK-06 (D-03/D-04) | Export all (JSON + CSV); archive-only, no destructive paths | Pattern 10 (export); Security Domain (CSV formula injection); Pitfall 5 |
</phase_requirements>

## Summary

Phase 7 is the project's first persistent module: a fully deterministic (D-15 — no LLM) job-application tracker backed by a local SQLite database, exposed through the existing FastAPI house patterns (envelope 200+{status,erros}, Pydantic `extra="forbid"`, sync `def` routes registered before the SPA mount) and rendered in the React 19 SPA as a fifth nav view with a drag-and-drop kanban. The backend needs **zero new dependencies** — stdlib `sqlite3` covers persistence, `csv`/`json` cover export. The frontend adds exactly **one deliberate exception** (D-14): the `@dnd-kit` family (`@dnd-kit/core` 6.3.1 + `@dnd-kit/sortable` 10.0.0 + `@dnd-kit/utilities` 3.2.2), all three verified OK on the legitimacy gate with ~42M weekly downloads each.

The two riskiest engineering points are (1) SQLite threading under sync `def` routes — the house pattern dispatches to the AnyIO threadpool, so a module-global connection would cross threads and crash; the fix is a connection-per-request `yield` dependency (official FastAPI docs pattern) — and (2) `@dnd-kit` + React 19 typings — the last legacy release (6.3.1, Dec 2024) ships `.d.ts` files with bare `JSX.Element`, which errors under React 19 types, but this project's `tsconfig.app.json` sets `skipLibCheck: true` [VERIFIED: frontend/tsconfig.app.json], suppressing exactly that class of error; `tsc -b` (the drift gate) is expected to pass. Both are resolved with small, testable patterns.

Everything else is well-trodden: `PRAGMA user_version` migrations (no Alembic — right-sized for a single-user app), date-only ISO strings with server-computed derived fields (`dias_para_prazo`, `atrasado`, `sugerir_followup`) so every deadline/badge rule is pinned by offline pytest vectors, and follow-up semantics where "pending" is *inferred from data* (a follow-up event dated in the future) so no flags can drift from reality.

**Primary recommendation:** Stdlib `sqlite3` behind a connection-per-request dependency + `PRAGMA user_version` migrations; `@dnd-kit/core`+`@dnd-kit/sortable` (one `DndContext`, one `SortableContext` per column, `sortableKeyboardCoordinates`, `closestCorners`); all deadline/badge/counters computed server-side from date-only ISO strings with an injectable "today"; route contract mirrors the candidatura 200-envelope verbatim.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Persistence, schema versioning, CRUD | Database/Storage (SQLite via API tier) | API/Backend | D-01/D-02 — the .db is the store; only the API tier touches it |
| Counter derivation, follow-up badges, deadline deltas | API/Backend | — | D-07 mechanical honesty + offline-testability: computed where pytest can pin them |
| Kanban drag & drop, optimistic ordering display | Browser/Client (React) | API/Backend (persist stage change) | D-14 — UI interaction; the server owns the *stage value*, the client owns the *gesture* |
| Deadline highlighting (amber/red), ordering by proximity | Browser/Client | API/Backend (provides sorted payload + day deltas) | D-09 — passive UI; server supplies the deterministic deltas, client picks the color family |
| Export JSON+CSV | API/Backend | Browser (download trigger, `downloadPdf`-style anchor pattern) | House rule — bytes generated server-side (04-01 precedent) |
| Entry-point prefill (JD text + language) | Browser/Client (App state) | — | D-13 — pure view-state hand-off, no backend involvement |
| Schema migrations | Database/Storage | — | `PRAGMA user_version` — runs at first request/startup, idempotent |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `sqlite3` (stdlib) | Python 3.12.10 bundled | Persistence, parameterized queries | D-01 + discretion: "zero dependência nova no backend" [VERIFIED: backend/pyproject.toml requires-python >=3.12; Python 3.12.10 probed] |
| `csv` / `json` (stdlib) | — | CSV + JSON export (D-03) | Zero infra nova per D-03 |
| `@dnd-kit/core` | 6.3.1 (npm latest, published 2024-12-05) | DndContext, sensors, collision detection | D-14 candidate; CONTEXT names it; verified current on npm [VERIFIED: npm view @dnd-kit/core] |
| `@dnd-kit/sortable` | 10.0.0 (published 2024-12-04) | SortableContext, useSortable, arrayMove, sortableKeyboardCoordinates | The sortable preset built for the kanban use case; peer `@dnd-kit/core ^6.3.0` [VERIFIED: npm view peerDependencies] |
| `@dnd-kit/utilities` | 3.2.2 | `CSS.Transform.toString(transform)` helper for the sortable style | Standard companion of the preset [VERIFIED: npm view] |

### Supporting (already in repo — no installs)
| Library | Version (in repo) | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI | >=0.141.1 | Router + TestClient | CRUD routes, house envelope |
| Pydantic | >=2.13.5 | Strict request DTOs (`extra="forbid"`) | Every tracker request body |
| @tanstack/react-query | ^5.103.2 | Queries/mutations + cache invalidation | All tracker fetches |
| React | ^19.2.8 | SPA | Fifth view + kanban rendering |
| TypeScript | ~5.9 | `tsc -b` drift gate | Mirrors of the backend DTOs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `sqlite3` | `aiosqlite` / SQLModel / Alembic | Extra deps contradict the discretion note; async driver would force `async def` routes, breaking the uniform house pattern; Alembic is oversized for a single-user personal DB |
| `@dnd-kit` | `react-beautiful-dnd` | Deprecated/atlassian-maintained-out — explicitly forbidden by D-14 |
| `@dnd-kit` | new dndkit.com rewrite | Maintainer's successor library with a new multi-framework API — unproven here, bigger migration surface; the stable legacy 6.3.1/10.0.0 pair satisfies this phase |
| Full kanban board lib (e.g. `@kanban/*` products) | — | D-14 says ONE lib, contained; the sortable preset + custom column chrome (Tailwind) is the minimal footprint |

**Installation:**
```bash
cd frontend && npm install @dnd-kit/core@^6.3.1 @dnd-kit/sortable@^10.0.0 @dnd-kit/utilities@^3.2.2
# backend: NOTHING to install — sqlite3/csv/json are stdlib (requires-python >=3.12)
```

**Version verification (done this session):** `npm view @dnd-kit/core version` → 6.3.1; `@dnd-kit/sortable` → 10.0.0; `@dnd-kit/utilities` → 3.2.2. Publish dates from `npm view ... time`: core 6.3.1 = 2024-12-05, sortable 10.0.0 = 2024-12-04. Peer ranges: core `react >=16.8.0`; sortable `@dnd-kit/core ^6.3.0`, `react >=16.8.0`. React 19.2.8 satisfies both. [VERIFIED: npm registry]

## Package Legitimacy Audit

> Run via `gsd_run query package-legitimacy check --ecosystem npm @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities` — all three returned verdict `OK`.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| @dnd-kit/core | npm | ~2 yrs (6.3.1, 2024-12-05) | ~42.4M/wk | github.com/clauderic/dnd-kit | OK | Approved |
| @dnd-kit/sortable | npm | ~2 yrs (10.0.0, 2024-12-04) | ~41.1M/wk | github.com/clauderic/dnd-kit | OK | Approved |
| @dnd-kit/utilities | npm | ~3 yrs (3.2.2, 2023-11-06) | ~42.3M/wk | github.com/clauderic/dnd-kit | OK | Approved |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none
**Postinstall check:** `npm view` signals show `postinstall: null` for all three — no install scripts. [VERIFIED: package-legitimacy seam signals]

Note: `sqlite3`, `csv`, `json`, `datetime` are Python **stdlib** — not registry packages, no audit needed.

## Architecture Patterns

### System Architecture Diagram

```
                       ENTRY POINTS (D-13 — three doors, one store)
  ┌────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
  │ Currículo result card  │  │ Tracker manual form      │  │ Candidatura (Respostas)  │
  │ ResumeResult.tsx       │  │ TrackerHome.tsx          │  │ CandidaturaHome.tsx      │
  │ "Registrar candidatura"│  │                          │  │ association picker       │
  │ → prefill {jd, idioma} │  │                          │  │ → metadata event only    │
  └───────────┬────────────┘  └────────────┬─────────────┘  └────────────┬─────────────┘
              │ App.tsx switches view      │                             │
              ▼                            ▼                             ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ Rastreador view (TrackerHome) — React Query v5 mutations/queries                │
  │  ├─ Contadores globais (enviados / entrevistas / ativas) — rendered from payload│
  │  ├─ Visão geral sorted by prazo + amber/red day deltas (D-09)                   │
  │  ├─ Kanban: 1 DndContext, 1 SortableContext/coluna (D-14) → drop = POST mover   │
  │  ├─ Formulário candidatura (essenciais + detalhes, D-06)                        │
  │  ├─ Gestão de estágios (D-05) ─ delete blocked while in use                     │
  │  └─ Exportar JSON + CSV (D-03) ─ anchor download                                 │
  └───────────────────────────────────┬─────────────────────────────────────────────┘
                                      │ fetch /api/tracker/* (typed client)
                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ FastAPI routes/tracker.py — sync def, envelope 200+{status,erros} (house rule)  │
  │  strict Pydantic DTOs (extra=forbid) → tracker/ service layer                   │
  │  derived fields computed HERE (dias_para_prazo, atrasado, sugerir_followup)     │
  │  "today" injected as a parameter (default date.today) → offline-testable        │
  └───────────────────────────────────┬─────────────────────────────────────────────┘
                                      │ connection-per-request (yield dependency)
                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ SQLite file  TRACKER_DB (default REPO_ROOT/data/tracker.db, env-overridable)    │
  │  estagios (id, nome, ordem)   candidaturas (…, estagio_id FK, arquivada…)       │
  │  eventos (candidatura_id FK, tipo, data_evento ISO date, idioma?, observacao?)  │
  │  PRAGMA user_version migrations at startup; journal_mode WAL (persistent)       │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
backend/
├── app/
│   ├── tracker/
│   │   ├── db.py            # connection factory, PRAGMAs, user_version migrations
│   │   ├── migrations.py    # ordered migration list (SQL strings) — or inline in db.py
│   │   ├── service.py       # CRUD + derived-field computation (pure, "today"-injected)
│   │   └── models.py        # Pydantic DTOs (extra=forbid) shared by routes
│   ├── routes/tracker.py    # sync def routes, 200-envelope, registered before SPA mount
│   ├── config.py            # + TRACKER_DB, TRACKER_FOLLOWUP_SUGGEST_DAYS (D-12)
│   └── main.py              # + include_router(tracker_router) BEFORE the SPA mount
└── tests/
    ├── test_tracker_db.py       # migrations, FK/seed, stage-deletion blocking
    ├── test_tracker_service.py  # counters, follow-up pending/overdue/suggestion vectors
    └── test_tracker_api.py      # envelope contracts + router-before-mount + 422s
frontend/src/
├── pages/TrackerHome.tsx        # fifth view; owns the screen assembly
├── components/tracker/
│   ├── KanbanBoard.tsx          # DndContext + per-column SortableContext
│   ├── CandidaturaCard.tsx      # kanban card (useSortable)
│   ├── CandidaturaForm.tsx      # manual entry + prefill from Currículo (D-13)
│   ├── EstagioManager.tsx       # add/rename/reorder/delete-blocked (D-05)
│   ├── EventosPanel.tsx         # dated events + follow-up pending/execute (D-10/D-11)
│   └── ContadoresGrid.tsx       # honest counters (D-07) — CompletenessGrid pattern
├── api/client.ts                # + tracker DTOs/functions (tsc -b drift gate)
├── constants/ui.ts              # + NAV_ITEMS fifth entry + RASTREADOR_* strings
└── App.tsx                      # + view union 'rastreador' + prefill state hand-off
```

### Pattern 1: Connection per request (the ONLY safe sqlite3 pattern here)
**What:** Open a fresh `sqlite3.Connection` inside a FastAPI dependency with `yield`; never store a connection at module level.
**When to use:** Every tracker route (all `sync def` — house pattern). Sync routes run in the AnyIO threadpool; a request may execute on any thread, and a sqlite3 connection may not cross threads.
**Example:**
```python
# Source: [CITED: fastapi.tiangolo.com/tutorial/sql-databases] + house sync-def pattern
# [VERIFIED: backend/app/routes/candidatura.py:53-56 — house sync def precedent]
import sqlite3
from fastapi import Depends

def get_tracker_db():
    conn = sqlite3.connect(TRACKER_DB)   # opened on THIS request's thread
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # default OFF — set per connection
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
```
Do NOT set `check_same_thread=False` — with per-request connections it is unnecessary; with a shared connection it is unsafe without serialized access [CITED: fastapi.tiangolo.com/tutorial/sql-databases; stackoverflow.com/questions/524797].

### Pattern 2: Schema versioning with `PRAGMA user_version`
**What:** The schema version lives in the database file header. On startup (or first connection), read `PRAGMA user_version`, apply each pending migration inside a transaction, then write the new version. Pair with `PRAGMA application_id` to prove the file belongs to this app.
**When to use:** First run creates schema v1; every future schema change appends one migration. No Alembic, no new deps.
**Example:**
```python
# Source: [CITED: levlaz.org/sqlite-db-migrations-with-pragma-user_version;
# eskerda.com/sqlite-schema-migrations-python; sqlite.org/forum/forumpost/0f9dd8806f]
MIGRATIONS: list[str] = [
    # v1: estagios + candidaturas + eventos (see Pattern 4)
    """CREATE TABLE estagios (...);""",
]
def aplicar_migracoes(conn: sqlite3.Connection) -> None:
    versao_atual = conn.execute("PRAGMA user_version").fetchone()[0]
    for i, sql in enumerate(MIGRATIONS, start=1):
        if i > versao_atual:
            with conn:                 # transaction per migration
                conn.executescript(sql)
            conn.execute(f"PRAGMA user_version = {i}")
```

### Pattern 3: .db path in `app/config.py` with env override
**What:** Follow the REPO_ROOT pattern; the env override is what the homelab compose bind mount targets (D-02).
**Example:**
```python
# REPO_ROOT pattern — verbatim precedent:
# [VERIFIED: backend/app/config.py:12-13]
# "# backend/app/config.py -> backend/app -> backend -> repo root"
# REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKER_DB = Path(os.environ.get("TRACKER_DB", str(REPO_ROOT / "data" / "tracker.db")))
TRACKER_DB.parent.mkdir(parents=True, exist_ok=True)   # first run creates data/
TRACKER_FOLLOWUP_SUGGEST_DAYS = int(os.environ.get("TRACKER_FOLLOWUP_SUGGEST_DAYS", "7"))
# ^ D-12: exact value pinned at planning (Open Question 1)
```
Also add `data/` to `.gitignore` (currently absent — verified; `.gitignore` covers `logs/` but no tracker data dir) [VERIFIED: .gitignore].

### Pattern 4: Data model — stages table + metadata-only events
**What:** D-05 (custom stages), D-06 (fields), D-07/D-08 (event-sourced counters, metadata only). Proposed v1 schema (planner finalizes):
```sql
CREATE TABLE estagios (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,             -- user's personal vocabulary (D-05)
    ordem INTEGER NOT NULL UNIQUE   -- kanban column order
);
CREATE TABLE candidaturas (
    id INTEGER PRIMARY KEY,
    empresa TEXT NOT NULL,
    cargo TEXT NOT NULL,
    fonte TEXT,                     -- onde viu (D-06)
    link_vaga TEXT,
    estagio_id INTEGER NOT NULL REFERENCES estagios(id),
    data_aplicacao TEXT,            -- ISO 'YYYY-MM-DD' — date-only, no timezones
    prazo_retorno TEXT,             -- nullable; drives D-09 sorting/highlights
    notas TEXT,
    jd_texto TEXT,                  -- optional (D-06); prefilled from Currículo (D-13)
    faixa_salarial TEXT,            -- detail fields (D-06 "MAIS")
    contato_recrutador TEXT,
    modalidade TEXT CHECK (modalidade IN ('remoto','hibrido','presencial') OR modalidade IS NULL),
    arquivada INTEGER NOT NULL DEFAULT 0,      -- D-04 archive flag (recommended over
    arquivada_em TEXT,                          --  a "final stage"; see Assumptions A2)
    criada_em TEXT NOT NULL
);
CREATE TABLE eventos (
    id INTEGER PRIMARY KEY,
    candidatura_id INTEGER NOT NULL REFERENCES candidaturas(id),
    tipo TEXT NOT NULL,             -- 'envio_curriculo' | 'entrevista' | 'retorno' | 'followup'
    data_evento TEXT NOT NULL,      -- ISO date; FUTURE date on a followup = pending (D-10)
    idioma TEXT,                    -- resume language on envio events (D-08 metadata)
    observacao TEXT                 -- free note (D-08)
);
```
Seed stages on v1 (data rows, editable via UI): e.g. `Pesquisando`, `Enviado`, `Entrevista`, `Oferta`, `Encerrado` — exact seed set is Open Question 2 (the user's vocabulary is personal, D-05).

### Pattern 4b: Follow-up semantics WITHOUT flags (data-inferred)
**What (D-10/D-11):** pending = a `followup` event with `data_evento > today`; overdue = a `followup` event with `data_evento < today` that was never executed; executing = re-dating the row to today (+ note), which turns it into "evento datado normal" exactly as D-10 requires. No `executada` column to drift.
- Counters and "last event" calculations must treat only **non-future** events as done.
- Alternative (also valid): explicit `executada INTEGER DEFAULT 0` column — more explicit, one more field to keep truthful. Planner pins one.
- "Adiar" (D-11) = update `data_evento` to a new future date.

### Pattern 5: Kanban with `@dnd-kit/sortable` (D-14)
**What:** One `DndContext` at the board level; one `SortableContext` per column; card components call `useSortable`; drag end posts the new stage; keyboard support via `KeyboardSensor` + `sortableKeyboardCoordinates`.
**When to use:** The kanban is the only DnD surface in the app.
**Example:**
```tsx
// Source: [CITED: dndkit.com/presets/sortable — official preset docs]
import { DndContext, closestCorners, KeyboardSensor, useSensor, useSensors,
         type DragEndEvent } from '@dnd-kit/core'
import { SortableContext, useSortable, arrayMove, verticalListSortingStrategy,
         sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'

const sensors = useSensors(
  useSensor(PointerSensor),   // activation constraint: distance 4-8px so clicks still work
  useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
)

// inside the card component:
const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id })
const style = { transform: CSS.Transform.toString(transform), transition }

// onDragEnd: if over.id is a card → same column reorder; if a column → stage change.
// Persist with a useMutation; invalidate the tracker query key on success.
```
Multi-container specifics [CITED: dndkit.com/presets/sortable]: use `onDragOver` for cross-column moves mid-drag OR keep it simple — at personal scale, resolve everything in `onDragEnd` (over.id ∈ column droppable → set stage; over.id ∈ card → stage of that card). Each column needs a droppable zone so an EMPTY column accepts drops; prefer `closestCorners` collision detection; never render the `useSortable` component inside `DragOverlay` (id collision). Columns/cards in this phase are small — `DragOverlay` is optional polish, not required.

### Pattern 6: Server-computed derived fields (D-07/D-09/D-11/D-12)
**What:** The overview/list payload carries precomputed, deterministic fields so the frontend never re-implements the rules:
```python
# service.py — "hoje" injectable for tests (house style: monkeypatch-free determinism)
def derivar_campo(cand: dict, eventos: list[dict], hoje: date,
                  limiar_followup: int) -> dict:
    prazo = date.fromisoformat(cand["prazo_retorno"]) if cand["prazo_retorno"] else None
    ultimos = [date.fromisoformat(e["data_evento"]) for e in eventos
               if date.fromisoformat(e["data_evento"]) <= hoje]          # future = pending
    ultimo_evento = max(ultimos) if ultimos else None
    return {
        "dias_para_prazo": (prazo - hoje).days if prazo else None,   # negativo = vencido
        "sugerir_followup": (ultimo_evento is None and cand["criada_em_dt"] …)
                            or (ultimo_evento and (hoje - ultimo_evento).days >= limiar_followup),
    }
# Contadores (D-07): enviados = COUNT(eventos WHERE tipo='envio_curriculo');
# entrevistas = COUNT(tipo='entrevista'); ativas = COUNT(candidaturas WHERE arquivada=0).
```
Exact counter metrics and event-type semantics are Claude's Discretion — the table above is the proposed pin (Open Question 3).

### Pattern 7: Fifth nav item + view switch (D-16)
The existing union and NAV_ITEMS (verbatim, for the planner):
```tsx
// [VERIFIED: frontend/src/constants/ui.ts:5-10]
// export const NAV_ITEMS = [
//   { id: 'curriculo', label: 'Currículo', enabled: true },
//   { id: 'perfil', label: 'Perfil', enabled: true },
//   { id: 'linkedin', label: 'LinkedIn', enabled: true },
//   { id: 'candidatura', label: 'Candidatura', enabled: true },
// ] as const
// [VERIFIED: frontend/src/App.tsx:69]
// const [view, setView] = useState<'curriculo' | 'perfil' | 'linkedin' | 'candidatura'>('curriculo')
```
Change: add `{ id: 'rastreador', label: 'Rastreador', enabled: true }`, extend the union and the render chain. Because `NAV_ITEMS` is `as const` and the button calls `setView(item.id)`, the union must include `'rastreador'` or `tsc -b` fails — the drift gate working as designed.

### Pattern 8: Route + envelope contract (house rule)
Mirror `routes/candidatura.py` exactly: strict Pydantic body, plain `def`, failures return HTTP 200 `{"status": "erro", "erros": [PT-BR lines]}` with raw detail to the logger only; validation failures stay FastAPI 422s.
```python
# [VERIFIED: backend/app/routes/candidatura.py:53-66 — the envelope verbatim:]
# @router.post("/api/candidatura/responder")
# def responder_candidatura(payload: CandidaturaRespostaRequest) -> dict:
#     try:
#         result = run_candidatura_resposta(...)
#     except (ProfileError, PromptError, LLMError) as exc:
#         logger.error("Falha na resposta de candidatura:\n%s", exc.raw)
#         return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
#     return {"status": "ok", **result}
```
Registration order (verbatim comment):
```python
# [VERIFIED: backend/app/main.py:19-24]
# # API routes FIRST — anything registered after the "/" mount is unreachable.
# ...
# app.include_router(candidatura_router)  # before the SPA mount (Pitfall 5)
```
Proposed route set (planner pins): `GET /api/tracker/resumo` (counters + candidaturas + estagios in one payload), `POST /api/tracker/candidaturas`, `PUT /api/tracker/candidaturas/{id}` (edit + archive), `POST /api/tracker/candidaturas/{id}/mover` (stage change), `POST /api/tracker/candidaturas/{id}/eventos` (add event / execute / postpone follow-up), `GET|POST|PUT|DELETE /api/tracker/estagios`, `GET /api/tracker/exportar.json`, `GET /api/tracker/exportar.csv`. NOT-FOUND on ids → 200 `status:"erro"` envelope (house style), never a bare 404.

### Pattern 9: "Registrar candidatura" prefill wiring (D-13)
**What:** The button lives on `ResumeResult` but the state hand-off crosses views. `App` owns `trackerPrefill` state; `CurriculoHome` passes a callback down to `ResumeResult` as a new optional prop. Clicking sets the prefill `{ jd_texto, language }` and switches view to `'rastreador'`; `TrackerHome`'s form initializes from it and clears it after first read (a `useEffect`-once or render-time consume).
```
App.tsx: const [trackerPrefill, setTrackerPrefill] = useState<{jd_texto: string; language: ResumeLanguage} | null>(null)
CurriculoHome → ResumeResult: onRegistrarCandidatura={() => { setTrackerPrefill({jd_texto, language}); setView('rastreador') }}
```
New props on ResumeResult must be optional — no existing call sites break.

### Pattern 10: Export (D-03) — reuse the download pattern
JSON: full dump of the three tables. CSV: one row per candidatura (planner pins columns); write via `csv.writer` into an `io.StringIO` with `newline=''` and return bytes encoded **`utf-8-sig`** so Windows Excel detects UTF-8 (PT-BR spreadsheet use is the point of the CSV). Frontend reuses the anchor + `URL.createObjectURL` pattern from `downloadPdf` in `api/client.ts` [VERIFIED: frontend/src/api/client.ts:569-577]. CSV delimiter: see Open Question 4 (PT-BR Excel may expect `;`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Drag & drop | Pointer-event kanban from scratch | `@dnd-kit/core` + `@dnd-kit/sortable` | D-14 is explicit ("pega um componente pronto"); keyboard a11y, collision detection, RTL/scale transforms are solved problems |
| Date day-deltas | JS `Date` timezone math in the client | ISO date strings + `date.fromisoformat` deltas server-side | Date-only strings have no TZ ambiguity; the deltas are then pytest-pinnable |
| Migrations | Hand-rolled "check if table exists" hacks | `PRAGMA user_version` sequence | Version lives in the file header, survives container rebuilds; no tooling dep |
| Excel-friendly CSV | Manual BOM byte prepending / custom escaping | `csv.writer` + `encoding='utf-8-sig'` | Quoting/escaping rules and BOM handling are exactly what the stdlib owns |
| Query/cache orchestration | Manual `useEffect` fetch chains | React Query v5 (in repo) | Invalidation after mover/eventos keeps kanban and overview consistent |

**Key insight:** This phase's entire logic is deterministic — the temptation to hand-roll is highest precisely where a stdlib or the pinned lib already solved it (dates, CSV, DnD).

## Common Pitfalls

### Pitfall 1: Sharing one sqlite3 connection across requests
**What goes wrong:** `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread` — intermittent, only under concurrent requests.
**Why it happens:** House routes are `sync def` → Starlette threadpool → different thread per request; the connection was opened on another thread.
**How to avoid:** Connection-per-request via `yield` dependency (Pattern 1). Never `check_same_thread=False` on a shared connection.
**Warning signs:** Tests pass with `TestClient` (same thread) but break under real uvicorn.

### Pitfall 2: `foreign_keys` pragma silently OFF
**What goes wrong:** Deleting a stage leaves orphan candidaturas; `REFERENCES` is decorative by default in SQLite.
**Why it happens:** SQLite disables FK enforcement unless `PRAGMA foreign_keys = ON` per connection.
**How to avoid:** Set it in the connection factory (Pattern 1); add a service test that stage deletion is blocked while referenced (D-05 policy — see Pattern 4 note: block with a PT-BR envelope erro line; never cascade-delete, honoring the no-destructive spirit of D-04).
**Warning signs:** A deletion test passes when it should error.

### Pitfall 3: `JSX.Element` typings panic with React 19
**What goes wrong:** With React 19 types, `@dnd-kit/core` 6.3.1's built `.d.ts` files contain bare `JSX.Element` which can raise `Cannot find namespace 'JSX'` [CITED: github.com/clauderic/dnd-kit/issues/1559].
**Why it happens:** React 19 moved the JSX namespace under `React.JSX`; the legacy package's build emitted the old global reference and was never re-cut (issue closed 2026-02-16 pointing to the dndkit.com rewrite).
**How to avoid:** Nothing to do — this repo's `tsconfig.app.json` sets `"skipLibCheck": true` [VERIFIED: frontend/tsconfig.app.json], which suppresses `.d.ts`-internal errors; `tsc -b` gates app code only. Verify with a build early in Wave 0.
**Warning signs:** Someone "fixes" it by downgrading @types/react — unnecessary here.

### Pitfall 4: Clicks swallowed by the drag sensor
**What goes wrong:** Opening a candidatura by clicking its kanban card stops working after adding dnd-kit.
**Why it happens:** PointerSensor activates immediately; a click is indistinguishable from a 1px drag.
**How to avoid:** Configure an activation constraint (`activationConstraint: { distance: 8 }`) on PointerSensor so click intents stay clicks; keep card actions (buttons) as explicit elements with `listeners` attached to a drag handle region, not to nested buttons [CITED: dndkit.com/presets/sortable — sensors composition].
**Warning signs:** UAT report "card opens by itself / never opens".

### Pitfall 5: Destructive creep (D-04 violation)
**What goes wrong:** A "remover candidatura" or cascading stage deletion ships "because it's easy".
**Why it happens:** CRUD scaffolding invites DELETE endpoints.
**How to avoid:** No DELETE on candidaturas — only archive (`arquivada=1` + date). Stage deletion allowed only when zero candidaturas reference it (envelope erro otherwise). No ConfirmStrip needed (no destructive path — 05-CONTEXT D-14 stays dormant).
**Warning signs:** Any `DELETE /api/tracker/candidaturas/*` in a plan.

### Pitfall 6: Stale kanban after a drag (React Query cache)
**What goes wrong:** The card visually snaps back or the overview counters desynchronize after a successful move.
**Why it happens:** The mutation succeeded but the query cache wasn't invalidated.
**How to avoid:** `onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tracker'] })` — one shared key for resumo/kanban/overview.
**Warning signs:** Manual refresh "fixes" the board.

### Pitfall 7: Timezone drift on "vence em X dias"
**What goes wrong:** Off-by-one-day deadlines when the container runs UTC and the user is at UTC-3.
**Why it happens:** `datetime.now()` vs `date.today()` mixing, or client-side parsing of ISO strings through `new Date()` (UTC interpretation).
**How to avoid:** Date-only ISO strings everywhere; all deltas computed server-side from `date.today()`/injected `hoje`; the client renders the delta numbers, never recomputes. Container TZ is then irrelevant for day arithmetic.
**Warning signs:** A `T00:00:00Z` timestamp anywhere in the schema.

### Pitfall 8: `.db` written inside the image layer / wrong place in Docker
**What goes wrong:** Data "disappears" on container recreate — the db was written to a non-mounted path (or root-owned bind mount rejects writes for the `cv` uid-1000 user).
**Why it happens:** The compose bind mount must target exactly the directory `TRACKER_DB` resolves to inside the container (`/srv/cv/data/` with the default config); the Dockerfile runs as `useradd --uid 1000 cv` [VERIFIED: Dockerfile — "RUN useradd --uid 1000 --create-home cv" / "USER cv"].
**How to avoid:** Document the homelab bind mount (`./data:/srv/cv/data`, host dir chowned to uid 1000); compose file lives in the homelab, not this repo [VERIFIED: no compose file in repo root].
**Warning signs:** Permission denied on first write in the container.

### Pitfall 9: React Query v5 isPending misuse
**What goes wrong:** TypeScript errors or spinner states that never resolve.
**Why it happens:** v5 renamed `isLoading` semantics — initial load is `isPending` (already a house convention).
**How to avoid:** Follow `App.tsx` PerfilHome pattern verbatim [VERIFIED: frontend/src/App.tsx:23-30 — `isPending` on the initial-load query].
**Warning signs:** `isLoading` on a fresh query returning true between fetches.

### Pitfall 10: Kanban `items` array out of sync with render order
**What goes wrong:** Erratic drop targets, cards jumping.
**Why it happens:** `SortableContext.items` must match rendered order exactly [CITED: dndkit.com/presets/sortable — "sorted in the same order in which the items are rendered"].
**How to avoid:** Derive `items` from the same array you `.map()` over; never sort one and render the other.
**Warning signs:** Working single-column sort but broken cross-column moves.

## Code Examples

### Envelope-typed client additions (frontend)
```typescript
// frontend/src/api/client.ts — mirrors routes/tracker.py; tsc -b is the drift gate
// (house comment precedent: [VERIFIED: frontend/src/api/client.ts:176-178])
export type TrackerModalidade = 'remoto' | 'hibrido' | 'presencial'

export interface EventoDTO {
  id: number
  candidatura_id: number
  tipo: 'envio_curriculo' | 'entrevista' | 'retorno' | 'followup'
  data_evento: string            // ISO 'YYYY-MM-DD'
  idioma: ResumeLanguage | null
  observacao: string | null
}

export interface EstagioDTO { id: number; nome: string; ordem: number }

export interface CandidaturaDTO {
  id: number
  empresa: string
  cargo: string
  fonte: string | null
  link_vaga: string | null
  estagio_id: number
  data_aplicacao: string | null
  prazo_retorno: string | null
  notas: string | null
  jd_texto: string | null
  faixa_salarial: string | null
  contato_recrutador: string | null
  modalidade: TrackerModalidade | null
  arquivada: boolean
  arquivada_em: string | null
  criada_em: string
  eventos: EventoDTO[]
  // derived (server-computed — the UI never recomputes):
  dias_para_prazo: number | null
  sugerir_followup: boolean
}

export type TrackerResumoResponse =
  | { status: 'ok'; contadores: { enviados: number; entrevistas: number; ativas: number }
      candidaturas: CandidaturaDTO[]; estagios: EstagioDTO[] }
  | { status: 'erro'; erros: string[] }
```

### Deadline chip classes (D-09 color family, PT-BR strings in constants/ui.ts)
```tsx
// âmbar = aviso / vermelho = erro — the approved family (D-09). sr-only suffix so
// status is never color-alone (house rule: [VERIFIED: frontend/src/constants/ui.ts:341]).
const prazoClasses =
  dias === null ? ''
  : dias < 0 ? 'rounded border border-red-300 bg-red-50 px-2 py-1 text-xs font-semibold text-red-700'
  : dias <= 3 ? 'rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700'
  : 'rounded border border-gray-200 bg-gray-50 px-2 py-1 text-xs text-gray-600'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `react-beautiful-dnd` | `@dnd-kit` (or the dndkit.com rewrite) | rbd deprecated since 2022; dnd-kit is the community standard | D-14 already forbids rbd; use the stable legacy dnd-kit pair [CITED: github.com/clauderic/dnd-kit/issues/1559] |
| Alembic/SQLAlchemy for every DB | `PRAGMA user_version` for single-file personal apps | long-standing small-app idiom | Zero backend deps for TRK-01 |
| File-based everything (this project's PROJECT.md) | Point reversal to SQLite for the tracker only | Phase 7 D-01 | Perfil mestre stays Markdown/YAML; planner registers the reversal in PROJECT.md Key Decisions |
| Global sqlite connection | Connection-per-request dependency | FastAPI docs standard | Pattern 1 |

**Deprecated/outdated:**
- `react-beautiful-dnd`: deprecated, no React 18+ StrictMode support — forbidden by D-14.
- Legacy `@dnd-kit` 6.3.1/10.0.0: feature-frozen since Dec 2024 (maintainer's effort moved to the dndkit.com rewrite) — acceptable: stable, massively downloaded, and the kanban needs only the sortable preset. Re-evaluate only if a future phase needs the rewrite's API.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `@dnd-kit` 6.3.1/10.0.0 + React 19.2.8 + TS 5.9 passes `tsc -b` because `skipLibCheck: true` suppresses the .d.ts JSX issue (peer range verified; issue #1559 verified; skipLibCheck verified — the *composition* is inference) | Standard Stack / Pitfall 3 | Wave 0 build failure → would need an npm `overrides` patch or a pinned earlier @types/react; cheap to detect (first build) |
| A2 | Archive as a **flag** (`arquivada` + `arquivada_em`) rather than D-04's literal "estágio final" wording | Pattern 4 | Stylistic; planner/user can pin either — flag survives user-deleted stages |
| A3 | Follow-up "pending" inferred from future `data_evento` (no explicit flag) | Pattern 4b | If planner prefers the explicit `executada` column, tests + DTO change but behavior is identical |
| A4 | Counter metric definitions (enviados = envio_curriculo events; entrevistas = entrevista events; ativas = not archived) | Pattern 6 | Discretion area — user confirmation of the metric semantics is worthwhile (D-07 honesty) |
| A5 | `journal_mode=WAL` persists in the file header; safe for this single-writer app | Pattern 1/2 | Trivially reversible; worst case default journal still works |
| A6 | PT-BR Excel prefers `;` delimiter for double-click CSV open | Pattern 10 | CSV opens with all columns in one column — cosmetic, one-constant fix |
| A7 | Date-only arithmetic needs no timezone handling for a UTC-3 user with dates stored as plain ISO strings computed from `date.today()` server-side | Pitfall 7 | Off-by-one edge cases at midnight boundaries; tests should pin a `hoje` boundary case |
| A8 | One `POST /mover` per drop (no optimistic update) is fine at personal scale | Pattern 5 | Slight flicker on slow homelab links; acceptable, reversible |
| A9 | Association on CandidaturaHome = recording a metadata-only event (never the answer text, per D-08 ephemerality) | TRK-03 | If the user intended stronger linking (e.g. storing answer), that would contradict D-08 — needs planner/user pin |

## Open Questions

1. **Follow-up suggestion threshold N (D-12) — exact value**
   - What we know: constant in `app/config.py`, env-overridable; "valor exato pinado no planejamento".
   - Recommendation: default `TRACKER_FOLLOWUP_SUGGEST_DAYS = 7`, planner confirms with user.
2. **Seed stage set (D-05)**
   - What we know: stages are user data; the v1 DB needs initial rows.
   - Recommendation: seed `Pesquisando / Enviado / Entrevista / Oferta / Encerrado` (PT-BR), editable via UI; planner confirms names.
3. **Counter semantics + event-type list (Discretion)**
   - What we know: D-07 requires mechanical derivation; STATE description names "currículos enviados e entrevistas feitas".
   - Recommendation: pin the four event types in Pattern 4 (`envio_curriculo`, `entrevista`, `retorno`, `followup`); confirm "ativas" excludes archived (A4).
4. **CSV delimiter for PT-BR Excel (Discretion: "encoding, colunas")**
   - Recommendation: `;` delimiter + `utf-8-sig` (A6); column list = candidatura fields + derived counters.
5. **Archive: flag vs final stage (A2)** — recommend flag; confirm with user if "estágio final" was meant literally.
6. **Candidatura association semantics (A9)** — recommend metadata-only event (`retorno`? dedicated `resposta` type?); planner pins the type name with the user.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | backend (sqlite3, csv, json stdlib) | ✓ | 3.12.10 | — |
| uv | backend sync/test runner | ✓ | 0.12.5 | — |
| Node | frontend build + npm install | ✓ | 22.16.0 | — |
| npm registry access | @dnd-kit install | ✓ (npm view succeeded this session) | — | — |
| Docker | NOT required for dev (homelab compose is external to this repo) | n/a | — | n/a |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none. (`data/` dir does not exist yet — created by config at first run; `.gitignore` needs a `data/` entry.)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=9.1.1 (offline by default); frontend gate = `tsc -b` via `npm run build` |
| Config file | `backend/pyproject.toml` — verbatim: `markers = ["llm: real OpenRouter API calls (spend) — run explicitly with -m llm"]`, `addopts = "-m 'not llm'"` [VERIFIED: backend/pyproject.toml] |
| Quick run command | `cd backend && uv run pytest tests/test_tracker_api.py tests/test_tracker_service.py tests/test_tracker_db.py -q` |
| Full suite command | `cd backend && uv run pytest -q` + `cd frontend && npm run build` (tsc -b + vite) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRK-01 | v1 migrations create 3 tables + seed stages; user_version advances; idempotent re-run | unit | `uv run pytest tests/test_tracker_db.py -q` | ❌ Wave 0 |
| TRK-01 | TRACKER_DB env override honored; parent dir auto-created | unit | `uv run pytest tests/test_tracker_db.py -q` | ❌ Wave 0 |
| TRK-02 | Stage deletion blocked while referenced (200 erro envelope); reorder persists | unit | `uv run pytest tests/test_tracker_api.py -q` | ❌ Wave 0 |
| TRK-02 | router registered BEFORE SPA mount (mirror the candidatura router-order test pattern) | unit | `uv run pytest tests/test_tracker_api.py -q` | ❌ Wave 0 |
| TRK-03 | Create/edit/archive envelope contracts; 422 on unknown key (extra=forbid), bad modalidade, oversized fields | unit | `uv run pytest tests/test_tracker_api.py -q` | ❌ Wave 0 |
| TRK-04 | Counters derived from events only (enviados/entrevistas/ativas); future events excluded | unit | `uv run pytest tests/test_tracker_service.py -q` | ❌ Wave 0 |
| TRK-05 | Follow-up: future = pending, past = overdue (vencido), execute re-dates to today; suggestion badge at exactly N days (boundary vectors with injected `hoje`) | unit | `uv run pytest tests/test_tracker_service.py -q` | ❌ Wave 0 |
| TRK-05 | Overview payload sorted by prazo proximity; `dias_para_prazo` correct at ±0 boundary | unit | `uv run pytest tests/test_tracker_service.py -q` | ❌ Wave 0 |
| TRK-06 | Export JSON = full tables; CSV bytes start with EF BB BF BOM; no destructive endpoint exists | unit | `uv run pytest tests/test_tracker_api.py -q` | ❌ Wave 0 |
| ALL | Frontend DTO mirror + kanban compile + nav union | build | `cd frontend && npm run build` | ✅ (existing gate) |
| UX | Drag feel, keyboard DnD, amber/red rendering | manual-only | /gsd-verify-work (house convention for UI UAT) | human_needed |

### Sampling Rate
- **Per task commit:** quick run command (tracker tests only, <30s — pure SQLite/tmp_path, no network)
- **Per wave merge:** full suite (`uv run pytest -q`) + `npm run build`
- **Phase gate:** full suite green + build green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_tracker_db.py` — migrations + env override + seed
- [ ] `backend/tests/test_tracker_service.py` — counters + follow-up/deadline vectors with injected `hoje`
- [ ] `backend/tests/test_tracker_api.py` — envelope contracts, router-order, 422s, export BOM
- [ ] Test isolation: tracker tests must point `TRACKER_DB` at `tmp_path` (monkeypatch env) — never the real `data/`
- [ ] Frontend install: `npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities` (the D-14 single exception)
- Framework install: none needed (pytest present; no JS test runner — house rule)

## Security Domain

> `security_enforcement: true`, ASVS Level 1 (config.json). Single-user localhost tool — no auth surface (PROJECT.md: "no hosting, no auth, no external database" [VERIFIED: .planning/PROJECT.md:53]).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | single-user localhost (out of scope per PROJECT.md) |
| V3 Session Management | no | no sessions exist |
| V4 Access Control | no | single user; bind 127.0.0.1 conventions |
| V5 Input Validation | **yes** | Pydantic `extra="forbid"` + Field bounds on every tracker body (house rule [VERIFIED: backend/app/routes/candidatura.py:43-50]); `modalidade` constrained to the D-06 set via Literal/Check |
| V6 Cryptography | no | no secrets, no crypto in this module |
| V14 Config | yes | `.db` path under gitignored `data/`; no secrets stored; env override is ops-owned |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection in CRUD/filters | Tampering | `sqlite3` parameter binding (`?` placeholders) ONLY — never f-string/format SQL; house test style should pin one parameterized-vs-injection vector |
| CSV formula injection (cell `=cmd()`) in the spreadsheet export | Tampering/Elevation | Sanitize cells whose first char is `= + - @` (prefix `'`) — the export's consumers open it in Excel |
| Stored XSS via empresa/notas/link rendered in kanban | Tampering | React JSX text escaping (house rule: content renders exclusively as JSX text children — ResumeResult posture [VERIFIED: frontend/src/components/ResumeResult.tsx:515-517]); `link_vaga` rendered as a plain anchor with `rel="noreferrer"` — never `dangerouslySetInnerHTML` |
| Data-at-rest exposure of job-search history | Information Disclosure | `.db` lives in gitignored `data/` locally and inside the homelab bind mount; export contains only what the user typed; D-08 keeps resume content out of the DB entirely |
| Denial of service via oversized payloads | DoS | Field `max_length` bounds mirror existing conventions (JD 20000 etc.); personal scale otherwise |

## Sources

### Primary (HIGH confidence)
- In-repo files read this session (all `[VERIFIED: path]` tags above): `backend/app/config.py`, `backend/app/main.py`, `backend/app/routes/candidatura.py`, `frontend/src/App.tsx`, `frontend/src/constants/ui.ts`, `frontend/src/api/client.ts`, `frontend/src/components/ResumeResult.tsx`, `frontend/src/pages/CandidaturaHome.tsx`, `frontend/tsconfig.json`/`tsconfig.app.json`, `backend/pyproject.toml`, `frontend/package.json`, `Dockerfile`, `.gitignore`, `backend/tests/conftest.py`, `backend/tests/test_candidatura_api.py`
- npm registry (`npm view`): @dnd-kit/core 6.3.1 / sortable 10.0.0 / utilities 3.2.2, peer deps, publish dates, postinstall=null
- package-legitimacy seam: all three verdicts OK

### Secondary (MEDIUM confidence)
- [dndkit.com/presets/sortable](https://dndkit.com/presets/sortable) — official sortable preset docs (DndContext/SortableContext/useSortable, strategies, keyboard sensor, multi-container kanban, gotchas)
- [FastAPI docs — SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases) — connection-per-request via yield dependency
- [github.com/clauderic/dnd-kit/issues/1559](https://github.com/clauderic/dnd-kit/issues/1559) — React 19 JSX typings issue, closed 2026-02-16, rewrite pointer
- [levlaz.org/sqlite-db-migrations-with-pragma-user_version](https://levlaz.org/sqlite-db-migrations-with-pragma-user_version), [eskerda.com/sqlite-schema-migrations-python](https://eskerda.com/sqlite-schema-migrations-python), [sqlite.org/forum/forumpost/0f9dd8806f](https://sqlite.org/forum/forumpost/0f9dd8806f) — user_version/application_id migration pattern
- [docs.python.org/3/library/csv.html](https://docs.python.org/3/library/csv.html) + [tobywf.com/2017/08/unicode-csv-excel](https://tobywf.com/2017/08/unicode-csv-excel) — utf-8-sig Excel compatibility

### Tertiary (LOW confidence)
- Community threads (Reddit/Medium/OneUptime) on FastAPI-SQLite threading — corroborate only; the official docs + in-repo house pattern carry the claim

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every package version verified against npm this session; backend is stdlib-only; all in-repo integration points read directly
- Architecture: HIGH for the house patterns (verbatim-quoted), MEDIUM for the proposed schema/semantics (discretion areas, flagged as Assumptions A2-A4/A9)
- Pitfalls: HIGH for threading/FK/React-19-typings/React-Query (verified mechanisms); MEDIUM for DnD sensor UX details (docs-sourced, not yet executed in this repo)

**Research date:** 2026-11-10
**Valid until:** 2026-12-10 (stable — pinned legacy dnd-kit line; stdlib-only backend; no fast-moving deps introduced)
