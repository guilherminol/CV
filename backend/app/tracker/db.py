"""Tracker persistence layer: connection factory + versioned migrations.

The project's FIRST SQLite module (D-01 — the deliberate point reversal of
the file-based constraint for the tracker ONLY; the master profile stays
Markdown/YAML in git — recorded in PROJECT.md Key Decisions).

Threading contract (RESEARCH Pattern 1, corrected by CR-01): tracker routes
are plain sync `def` (house rule — Starlette threadpool dispatch), so
connections are ALWAYS per-request — opened by the route's yield dependency,
never module-global, never shared ACROSS requests. One REQUEST may span
several threadpool workers: FastAPI runs the yield dependency's setup and
teardown via contextmanager_in_threadpool and the sync handler in another
worker — anyio gives no same-thread guarantee. conectar() therefore passes
check_same_thread=False, the FastAPI-documented relaxation for exactly this
yield-dependency pattern: the connection stays confined to its single
request's lifecycle, and SQLite's own locking plus that confinement keep
the sequential setup → handler → teardown use safe.

Schema history (RESEARCH Pattern 2): `PRAGMA user_version` lives in the file
header; each entry in MIGRATIONS is one transactional step, applied
idempotently by aplicar_migracoes(). Date-only ISO 'YYYY-MM-DD' strings
everywhere — no timezone-bearing timestamps (Pitfall 7).

Pins recorded in 07-01 (Phase planning):
- A2: archive is the candidaturas.arquivada FLAG (+ arquivada_em date), not a
  "estágio final" stage — a flag survives user-edited stage vocabularies (D-05).
- A3: a pending follow-up is data-INFERRED (a followup event with a future
  date) — NO executed-flag column exists to drift; the eventos DDL below is
  final.
"""

import sqlite3

from app.config import TRACKER_DB

# PRAGMA application_id — ASCII "TRK1" — marks this .db file as belonging to
# this app (RESEARCH Pattern 2), so tooling can identify the store.
TRACKER_APPLICATION_ID = 0x54524B31

# Ordered schema history. v1 = estagios + candidaturas + eventos
# (RESEARCH Pattern 4) + the five seed stage rows in ordem 1..5 (D-05 seed
# set pinned at planning; editable afterwards via the stage management UI).
MIGRATIONS: list[str] = [
    # v1
    """
    CREATE TABLE estagios (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        ordem INTEGER NOT NULL UNIQUE
    );

    CREATE TABLE candidaturas (
        id INTEGER PRIMARY KEY,
        empresa TEXT NOT NULL,
        cargo TEXT NOT NULL,
        fonte TEXT,
        link_vaga TEXT,
        estagio_id INTEGER NOT NULL REFERENCES estagios(id),
        data_aplicacao TEXT,
        prazo_retorno TEXT,
        notas TEXT,
        jd_texto TEXT,
        faixa_salarial TEXT,
        contato_recrutador TEXT,
        modalidade TEXT CHECK (
            modalidade IN ('remoto', 'hibrido', 'presencial') OR modalidade IS NULL
        ),
        arquivada INTEGER NOT NULL DEFAULT 0,
        arquivada_em TEXT,
        criada_em TEXT NOT NULL
    );

    CREATE TABLE eventos (
        id INTEGER PRIMARY KEY,
        candidatura_id INTEGER NOT NULL REFERENCES candidaturas(id),
        tipo TEXT NOT NULL,
        data_evento TEXT NOT NULL,
        idioma TEXT,
        observacao TEXT
    );

    INSERT INTO estagios (id, nome, ordem) VALUES
        (1, 'Pesquisando', 1),
        (2, 'Enviado', 2),
        (3, 'Entrevista', 3),
        (4, 'Oferta', 4),
        (5, 'Encerrado', 5);
    """,
]


def conectar() -> sqlite3.Connection:
    """Open a fresh per-request connection with the house PRAGMAs.

    Callers own the lifecycle (yield dependency: commit + close in finally).
    check_same_thread=False (CR-01): the single request this connection
    serves spans several threadpool workers (dependency setup, sync handler,
    teardown each land where anyio puts them), so confinement is per REQUEST,
    not per thread — the connection is never shared across requests.
    foreign_keys is OFF by default in SQLite — set per connection (Pitfall 2);
    busy_timeout tolerates the single-writer contention window; WAL keeps
    concurrent reads cheap (A5).
    """
    conn = sqlite3.connect(TRACKER_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def aplicar_migracoes(conn: sqlite3.Connection) -> None:
    """Apply pending migrations idempotently (RESEARCH Pattern 2).

    Reads PRAGMA user_version, applies each pending entry inside one
    transaction, then stamps the version. Re-running on a migrated file is a
    no-op (version unchanged, row counts unchanged). The application_id
    header write is idempotent by nature.
    """
    conn.execute(f"PRAGMA application_id = {TRACKER_APPLICATION_ID}")
    versao_atual = conn.execute("PRAGMA user_version").fetchone()[0]
    for indice, script in enumerate(MIGRATIONS, start=1):
        if indice > versao_atual:
            with conn:  # one transaction per migration
                conn.executescript(script)
            # The loop index is a compile-time int — never user data.
            conn.execute(f"PRAGMA user_version = {indice}")
