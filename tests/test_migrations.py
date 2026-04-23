import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations, get_applied_versions, discover_migrations
from migrations.runner import backup_db, rollback_to


# --- discover_migrations ---

def test_discover_migrations_returns_sorted_by_version():
    found = discover_migrations()
    versions = [v for v, _ in found]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions)), "duplicate version numbers"


def test_discover_migrations_includes_0001():
    found = dict(discover_migrations())
    assert 1 in found
    assert hasattr(found[1], 'up')
    assert hasattr(found[1], 'down')


# --- run_migrations (happy path) ---

def test_run_migrations_on_empty_db_creates_tables():
    conn = get_connection(':memory:')
    applied = run_migrations(conn)
    assert 1 in applied
    cursor = conn.cursor()
    for table in ('patients', 'cycles', 'labs', 'schema_migrations'):
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        assert cursor.fetchone() is not None, f"{table} missing"
    conn.close()


def test_run_migrations_is_idempotent():
    conn = get_connection(':memory:')
    all_versions = [v for v, _ in discover_migrations()]
    first = run_migrations(conn)
    second = run_migrations(conn)
    assert first == all_versions
    assert second == []
    conn.close()


def test_get_applied_versions_reflects_applied():
    conn = get_connection(':memory:')
    assert get_applied_versions(conn) == []
    run_migrations(conn)
    all_versions = [v for v, _ in discover_migrations()]
    assert get_applied_versions(conn) == all_versions
    conn.close()


# --- rollback ---

def test_rollback_to_zero_drops_tables():
    conn = get_connection(':memory:')
    run_migrations(conn)
    rollback_to(conn, 0)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='patients'"
    )
    assert cursor.fetchone() is None
    assert get_applied_versions(conn) == []
    conn.close()


def test_round_trip_up_down_up():
    conn = get_connection(':memory:')
    all_versions = [v for v, _ in discover_migrations()]
    run_migrations(conn)
    rollback_to(conn, 0)
    applied = run_migrations(conn)
    assert applied == all_versions
    conn.close()


# --- backup_db ---

def test_backup_db_noop_for_memory():
    assert backup_db(':memory:') == ''


def test_backup_db_noop_for_missing_file(tmp_path):
    assert backup_db(str(tmp_path / 'does_not_exist.db')) == ''


def test_backup_db_copies_existing_file(tmp_path):
    src = tmp_path / 'test.db'
    src.write_bytes(b'sqlite-content')
    backup = backup_db(str(src))
    assert backup
    assert os.path.exists(backup)
    assert open(backup, 'rb').read() == b'sqlite-content'
    assert '.pre-migrate-' in backup


def test_run_migrations_backs_up_existing_db(tmp_path):
    db_path = str(tmp_path / 'existing.db')
    conn = get_connection(db_path)
    conn.close()
    # Re-open and run migrations — file now exists so a backup should be written.
    conn = get_connection(db_path)
    run_migrations(conn, db_path)
    conn.close()
    backups = [p for p in os.listdir(tmp_path) if '.pre-migrate-' in p]
    assert len(backups) == 1


# --- failure path ---

def test_failed_migration_rolls_back_and_is_not_recorded(monkeypatch):
    conn = get_connection(':memory:')

    class FakeModule:
        VERSION = 999

        @staticmethod
        def up(conn):
            conn.cursor().execute('CREATE TABLE junk (id INTEGER)')
            raise RuntimeError("boom")

        @staticmethod
        def down(conn):
            pass

    import migrations.runner as runner
    monkeypatch.setattr(runner, 'discover_migrations',
                        lambda: [(1, discover_migrations()[0][1]), (999, FakeModule)])

    with pytest.raises(RuntimeError):
        run_migrations(conn)

    # v1 applied before the failure, but 999 must not be recorded.
    assert 999 not in get_applied_versions(conn)
    conn.close()
