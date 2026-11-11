"""Persistence tests for the tracker SQLite layer (plan 07-01, Wave-0).

Pins the project's FIRST database module (D-01): a fresh TRACKER_DB
auto-migrates to schema v1 with exactly three tables (estagios, candidaturas,
eventos) and the five seeded stage rows in ordem 1..5; aplicar_migracoes is
idempotent (user_version unchanged, row counts unchanged); the
PRAGMA application_id header is stamped; every conectar() connection
enforces foreign keys AND carries check_same_thread=False (CR-01 — one
connection per REQUEST, usable across the threadpool workers a single
request spans); config exposes TRACKER_DB + TRACKER_FOLLOWUP_SUGGEST_DAYS
(default 7, D-12) and the TRACKER_DB env override is honored with the parent
dir auto-created.

Isolation seam (RESEARCH Wave-0): tests monkeypatch the app.tracker.db module
constant TRACKER_DB at tmp_path — NEVER the real data/ directory.
100% offline (D-15 — no LLM anywhere in the tracker module).
"""

import importlib
import sqlite3
import threading

import pytest

import app.tracker.db as tracker_db
from app.tracker.db import MIGRATIONS, TRACKER_APPLICATION_ID, aplicar_migracoes, conectar

ESTAGIOS_ESPERADOS = [
    (1, "Pesquisando", 1),
    (2, "Enviado", 2),
    (3, "Entrevista", 3),
    (4, "Oferta", 4),
    (5, "Encerrado", 5),
]


@pytest.fixture()
def db_tmp(tmp_path, monkeypatch):
    """Point the tracker module's DB constant at tmp_path — never the real data/."""
    alvo = tmp_path / "tracker.db"
    monkeypatch.setattr(tracker_db, "TRACKER_DB", alvo)
    return alvo


def test_migracao_fresh_db_user_version_1(db_tmp):
    conn = conectar()
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        aplicar_migracoes(conn)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
    finally:
        conn.close()


def test_schema_v1_tem_exatamente_tres_tabelas(db_tmp):
    conn = conectar()
    try:
        aplicar_migracoes(conn)
        tabelas = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
                " AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        assert tabelas == {"estagios", "candidaturas", "eventos"}
    finally:
        conn.close()


def test_seed_cinco_estagios_em_ordem(db_tmp):
    conn = conectar()
    try:
        aplicar_migracoes(conn)
        rows = conn.execute(
            "SELECT id, nome, ordem FROM estagios ORDER BY ordem"
        ).fetchall()
        assert [tuple(row) for row in rows] == ESTAGIOS_ESPERADOS
    finally:
        conn.close()


def test_migracao_idempotente(db_tmp):
    conn = conectar()
    try:
        aplicar_migracoes(conn)
        contar_antes = conn.execute("SELECT COUNT(*) FROM estagios").fetchone()[0]
        aplicar_migracoes(conn)  # re-run — must be a no-op
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM estagios").fetchone()[0] == contar_antes
        assert conn.execute("SELECT COUNT(*) FROM candidaturas").fetchone()[0] == 0
    finally:
        conn.close()


def test_application_id_pinned(db_tmp):
    conn = conectar()
    try:
        aplicar_migracoes(conn)
        assert (
            conn.execute("PRAGMA application_id").fetchone()[0]
            == TRACKER_APPLICATION_ID
        )
    finally:
        conn.close()


def test_conectar_liga_foreign_keys(db_tmp):
    conn = conectar()
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()


def test_conectar_relaxa_mesma_thread_por_request(db_tmp, monkeypatch):
    """CR-01 pin: FastAPI runs the yield dependency's setup/teardown
    (contextmanager_in_threadpool) and the sync handler on DIFFERENT
    threadpool workers — anyio gives no same-thread guarantee — so conectar()
    must open with check_same_thread=False. Confinement is per REQUEST
    (never shared across requests), not per thread."""
    capturado: dict = {}
    original_connect = sqlite3.connect

    def espiar(*args, **kwargs):
        capturado.update(kwargs)
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(tracker_db.sqlite3, "connect", espiar)
    conn = conectar()
    try:
        assert capturado.get("check_same_thread") is False
    finally:
        conn.close()


def test_conexao_aceita_uso_de_outra_thread(db_tmp):
    """CR-01 behavioral pin: the exact failure mode reproduced against a real
    uvicorn server — using the connection from a thread OTHER than the one
    that opened it (teardown commit/close lands on another worker than the
    setup) — must NOT raise sqlite3.ProgrammingError."""
    conn = conectar()
    try:
        aplicar_migracoes(conn)
        erros: list[Exception] = []

        def usar_de_outra_thread() -> None:
            try:
                conn.execute("SELECT COUNT(*) FROM estagios").fetchone()
            except Exception as exc:  # noqa: BLE001 — the pin IS the absence of this
                erros.append(exc)

        thread = threading.Thread(target=usar_de_outra_thread)
        thread.start()
        thread.join()
        assert erros == []
    finally:
        conn.close()


def test_migrations_carry_seed_and_ddl():
    """The v1 script carries the three CREATE TABLEs and the five seed INSERTs."""
    script = MIGRATIONS[0]
    for tabela in ("estagios", "candidaturas", "eventos"):
        assert f"CREATE TABLE {tabela}" in script
    assert script.count("INSERT INTO estagios") == 1


def test_config_exposes_tracker_constants():
    import app.config as config_module

    assert config_module.TRACKER_DB.name == "tracker.db"
    assert config_module.TRACKER_FOLLOWUP_SUGGEST_DAYS == 7  # D-12 pin


def test_config_env_override_cria_diretorio_pai(tmp_path, monkeypatch):
    import app.config as config_module

    destino = tmp_path / "aninhado" / "tracker.db"
    monkeypatch.setenv("TRACKER_DB", str(destino))
    recarregado = importlib.reload(config_module)
    try:
        assert recarregado.TRACKER_DB == destino
        assert destino.parent.is_dir()  # parent auto-created at import
    finally:
        importlib.reload(config_module)  # restore the real default constant
