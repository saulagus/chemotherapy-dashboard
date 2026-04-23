import json
import os
import sys
from datetime import date
from dataclasses import dataclass
from typing import Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from services.audit import (
    write_audit,
    get_audit_for_entity,
    current_actor,
    ACTIONS,
)


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


# --- migration ---

def test_audit_log_table_created_by_migration(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'"
    )
    assert cursor.fetchone() is not None


def test_audit_index_exists(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='ix_audit_entity'"
    )
    assert cursor.fetchone() is not None


# --- write_audit: happy path ---

def test_write_create_records_after_only(conn):
    row_id = write_audit(conn, 'patient', 7, 'create',
                         after={'patient_id': 'PT-007', 'name': 'Bond'})
    conn.commit()
    assert row_id > 0
    rows = get_audit_for_entity(conn, 'patient', 7)
    assert len(rows) == 1
    assert rows[0]['action'] == 'create'
    assert rows[0]['before'] is None
    assert rows[0]['after']['name'] == 'Bond'


def test_write_update_records_before_and_after(conn):
    write_audit(conn, 'patient', 1, 'update',
                before={'name': 'Old'}, after={'name': 'New'})
    conn.commit()
    rows = get_audit_for_entity(conn, 'patient', 1)
    assert rows[0]['before']['name'] == 'Old'
    assert rows[0]['after']['name'] == 'New'


def test_write_delete_records_before_only(conn):
    write_audit(conn, 'cycle', 3, 'delete', before={'cycle_number': 2})
    conn.commit()
    rows = get_audit_for_entity(conn, 'cycle', 3)
    assert rows[0]['action'] == 'delete'
    assert rows[0]['after'] is None


def test_write_accepts_dataclass(conn):
    @dataclass
    class P:
        patient_id: str
        name: str
        diagnosis_date: Optional[date] = None

    write_audit(conn, 'patient', 2, 'create',
                after=P(patient_id='PT-002', name='X', diagnosis_date=date(2026, 1, 15)))
    conn.commit()
    row = get_audit_for_entity(conn, 'patient', 2)[0]
    assert row['after']['diagnosis_date'] == '2026-01-15'
    assert row['after']['patient_id'] == 'PT-002'


def test_date_objects_round_trip_as_iso_strings(conn):
    write_audit(conn, 'lab', 5, 'update',
                before={'lab_date': date(2026, 2, 1)},
                after={'lab_date': date(2026, 2, 8)})
    conn.commit()
    row = get_audit_for_entity(conn, 'lab', 5)[0]
    assert row['before']['lab_date'] == '2026-02-01'
    assert row['after']['lab_date'] == '2026-02-08'


# --- atomicity ---

def test_rollback_leaves_no_audit_row(conn):
    write_audit(conn, 'patient', 9, 'create', after={'name': 'X'})
    conn.rollback()
    assert get_audit_for_entity(conn, 'patient', 9) == []


def test_write_audit_does_not_auto_commit(conn):
    write_audit(conn, 'patient', 11, 'create', after={'name': 'X'})
    # Open a second connection to the same (memory) DB — tests in-memory
    # can't share, so instead verify on a file-backed DB in the next test.
    # Here we just verify rollback works.
    conn.rollback()
    assert get_audit_for_entity(conn, 'patient', 11) == []


def test_write_audit_persistence_requires_commit(tmp_path):
    db_path = str(tmp_path / 'audit.db')
    conn1 = get_connection(db_path)
    run_migrations(conn1, db_path)
    write_audit(conn1, 'patient', 12, 'create', after={'name': 'X'})
    # no commit yet
    conn1.close()
    # Fresh connection — the uncommitted write must not have survived.
    conn2 = get_connection(db_path)
    assert get_audit_for_entity(conn2, 'patient', 12) == []
    conn2.close()


# --- validation / edge cases ---

def test_unknown_action_rejected(conn):
    with pytest.raises(ValueError):
        write_audit(conn, 'patient', 1, 'frobnicate', after={})


def test_unsupported_record_type_rejected(conn):
    with pytest.raises(TypeError):
        write_audit(conn, 'patient', 1, 'create', after="just a string")


def test_actor_override_used(conn):
    write_audit(conn, 'patient', 4, 'create', after={'n': 1}, actor='test_user')
    conn.commit()
    assert get_audit_for_entity(conn, 'patient', 4)[0]['actor'] == 'test_user'


def test_default_actor_is_current_user(conn):
    write_audit(conn, 'patient', 5, 'create', after={'n': 1})
    conn.commit()
    assert get_audit_for_entity(conn, 'patient', 5)[0]['actor'] == current_actor()


def test_entity_id_can_be_null(conn):
    write_audit(conn, 'patient', None, 'delete', before={'n': 1})
    conn.commit()
    cursor = conn.cursor()
    cursor.execute("SELECT entity_id FROM audit_log WHERE action='delete'")
    assert cursor.fetchone()[0] is None


# --- ordering ---

def test_get_audit_returns_newest_first(conn):
    write_audit(conn, 'patient', 1, 'create', after={'v': 1})
    write_audit(conn, 'patient', 1, 'update', before={'v': 1}, after={'v': 2})
    write_audit(conn, 'patient', 1, 'update', before={'v': 2}, after={'v': 3})
    conn.commit()
    rows = get_audit_for_entity(conn, 'patient', 1)
    assert [r['after']['v'] for r in rows] == [3, 2, 1]


def test_get_audit_scopes_to_entity(conn):
    write_audit(conn, 'patient', 1, 'create', after={'n': 'A'})
    write_audit(conn, 'patient', 2, 'create', after={'n': 'B'})
    write_audit(conn, 'cycle', 1, 'create', after={'n': 'C'})
    conn.commit()
    assert len(get_audit_for_entity(conn, 'patient', 1)) == 1
    assert len(get_audit_for_entity(conn, 'patient', 2)) == 1
    assert len(get_audit_for_entity(conn, 'cycle', 1)) == 1


def test_get_audit_empty_for_unknown_entity(conn):
    assert get_audit_for_entity(conn, 'patient', 999) == []


# --- actions vocabulary ---

def test_all_documented_actions_accepted(conn):
    for i, action in enumerate(ACTIONS):
        write_audit(conn, 'patient', i, action, before={'x': 1}, after={'x': 2})
    conn.commit()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM audit_log')
    assert cursor.fetchone()[0] == len(ACTIONS)
