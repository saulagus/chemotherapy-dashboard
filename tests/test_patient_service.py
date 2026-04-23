import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, get_all_patients, get_patient_by_db_id, get_patient_by_id
from services import audit as audit_module
from services.patients import (
    create_patient,
    update_patient,
    soft_delete_patient,
    restore_patient,
)


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


def _make(patient_id='PT-001', name='Alpha', **kwargs):
    return Patient(
        patient_id=patient_id, name=name,
        start_date=date(2026, 1, 1), protocol='Standard AC-T',
        total_cycles=8, **kwargs,
    )


# --- migration: columns added ---

def test_migration_adds_deleted_at_and_dose_density(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(patients)")
    cols = {row[1] for row in cursor.fetchall()}
    assert 'deleted_at' in cols
    assert 'dose_density' in cols


# --- create_patient ---

def test_create_patient_returns_with_id(conn):
    p = create_patient(conn, _make())
    assert p.id is not None


def test_create_patient_writes_audit_row(conn):
    p = create_patient(conn, _make(), actor='tester')
    rows = audit_module.get_audit_for_entity(conn, 'patient', p.id)
    assert len(rows) == 1
    assert rows[0]['action'] == 'create'
    assert rows[0]['actor'] == 'tester'
    assert rows[0]['before'] is None
    assert rows[0]['after']['patient_id'] == 'PT-001'


def test_create_patient_stores_dose_density(conn):
    p = create_patient(conn, _make(dose_density='dose_dense_q2w'))
    fetched = get_patient_by_db_id(conn, p.id)
    assert fetched.dose_density == 'dose_dense_q2w'


def test_create_patient_duplicate_id_rolls_back_audit(conn):
    create_patient(conn, _make(patient_id='PT-DUP'))
    with pytest.raises(Exception):
        create_patient(conn, _make(patient_id='PT-DUP', name='Other'))
    # Only one audit row exists (the successful one), not two.
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action='create'")
    assert cursor.fetchone()[0] == 1


# --- update_patient ---

def test_update_patient_changes_fields(conn):
    p = create_patient(conn, _make())
    p.name = 'Alpha Updated'
    p.dose_density = 'standard_q3w'
    update_patient(conn, p)
    fetched = get_patient_by_db_id(conn, p.id)
    assert fetched.name == 'Alpha Updated'
    assert fetched.dose_density == 'standard_q3w'


def test_update_patient_writes_audit_with_before_and_after(conn):
    p = create_patient(conn, _make(name='Orig'))
    p.name = 'Changed'
    update_patient(conn, p, actor='nurse_a')
    rows = audit_module.get_audit_for_entity(conn, 'patient', p.id)
    update_row = next(r for r in rows if r['action'] == 'update')
    assert update_row['before']['name'] == 'Orig'
    assert update_row['after']['name'] == 'Changed'
    assert update_row['actor'] == 'nurse_a'


def test_update_patient_missing_id_raises(conn):
    with pytest.raises(ValueError):
        update_patient(conn, _make())


def test_update_patient_unknown_id_raises(conn):
    p = _make()
    p.id = 999
    with pytest.raises(LookupError):
        update_patient(conn, p)


# --- soft_delete_patient ---

def test_soft_delete_sets_deleted_at(conn):
    p = create_patient(conn, _make())
    soft_delete_patient(conn, p.id)
    hidden = get_patient_by_db_id(conn, p.id)
    assert hidden is None
    visible = get_patient_by_db_id(conn, p.id, include_deleted=True)
    assert visible is not None
    assert visible.deleted_at is not None


def test_soft_deleted_patient_excluded_from_get_all(conn):
    p1 = create_patient(conn, _make(patient_id='PT-001'))
    p2 = create_patient(conn, _make(patient_id='PT-002', name='Bravo'))
    soft_delete_patient(conn, p1.id)
    patients = get_all_patients(conn)
    ids = [p.id for p in patients]
    assert p1.id not in ids
    assert p2.id in ids


def test_get_all_patients_include_deleted_returns_all(conn):
    p1 = create_patient(conn, _make(patient_id='PT-001'))
    p2 = create_patient(conn, _make(patient_id='PT-002', name='Bravo'))
    soft_delete_patient(conn, p1.id)
    patients = get_all_patients(conn, include_deleted=True)
    assert len(patients) == 2


def test_soft_deleted_patient_excluded_from_get_by_id(conn):
    p = create_patient(conn, _make(patient_id='PT-ZZZ'))
    soft_delete_patient(conn, p.id)
    assert get_patient_by_id(conn, 'PT-ZZZ') is None
    assert get_patient_by_id(conn, 'PT-ZZZ', include_deleted=True) is not None


def test_soft_delete_writes_audit(conn):
    p = create_patient(conn, _make())
    soft_delete_patient(conn, p.id, actor='admin')
    rows = audit_module.get_audit_for_entity(conn, 'patient', p.id)
    del_row = next(r for r in rows if r['action'] == 'soft_delete')
    assert del_row['actor'] == 'admin'
    assert del_row['before']['patient_id'] == 'PT-001'


def test_soft_delete_twice_is_noop(conn):
    p = create_patient(conn, _make())
    soft_delete_patient(conn, p.id)
    soft_delete_patient(conn, p.id)  # no-op
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action='soft_delete'")
    assert cursor.fetchone()[0] == 1


def test_soft_delete_unknown_raises(conn):
    with pytest.raises(LookupError):
        soft_delete_patient(conn, 9999)


# --- restore_patient ---

def test_restore_patient_clears_deleted_at(conn):
    p = create_patient(conn, _make())
    soft_delete_patient(conn, p.id)
    restore_patient(conn, p.id)
    visible = get_patient_by_db_id(conn, p.id)
    assert visible is not None
    assert visible.deleted_at is None


def test_restore_writes_audit(conn):
    p = create_patient(conn, _make())
    soft_delete_patient(conn, p.id)
    restore_patient(conn, p.id, actor='admin')
    rows = audit_module.get_audit_for_entity(conn, 'patient', p.id)
    assert any(r['action'] == 'restore' for r in rows)


def test_restore_non_deleted_is_noop(conn):
    p = create_patient(conn, _make())
    restore_patient(conn, p.id)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE action='restore'")
    assert cursor.fetchone()[0] == 0


# --- full audit trail across lifecycle ---

def test_full_lifecycle_audit_trail(conn):
    p = create_patient(conn, _make(name='Initial'))
    p.name = 'Revised'
    update_patient(conn, p)
    soft_delete_patient(conn, p.id)
    restore_patient(conn, p.id)

    rows = audit_module.get_audit_for_entity(conn, 'patient', p.id)
    actions = [r['action'] for r in rows]
    # Newest first.
    assert actions == ['restore', 'soft_delete', 'update', 'create']
