import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Cycle, Patient, get_cycles_by_patient
from services import audit as audit_module
from services.patients import create_patient
from services.cycles import create_cycle, update_cycle, delete_cycle


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


@pytest.fixture
def patient(conn):
    return create_patient(conn, Patient(
        patient_id='PT-001', name='Alpha',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
    ))


def _make_cycle(patient_id, cycle_number=1, **kwargs):
    defaults = dict(
        phase='AC', actual_date=date(2026, 1, 15),
        status='completed', dose_percent=100.0,
    )
    defaults.update(kwargs)
    return Cycle(patient_id=patient_id, cycle_number=cycle_number, **defaults)


# --- create_cycle ---

def test_create_cycle_returns_with_id(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id))
    assert c.id is not None


def test_create_cycle_writes_audit(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id), actor='nurse_a')
    rows = audit_module.get_audit_for_entity(conn, 'cycle', c.id)
    assert len(rows) == 1
    assert rows[0]['action'] == 'create'
    assert rows[0]['actor'] == 'nurse_a'
    assert rows[0]['after']['cycle_number'] == 1


def test_create_cycle_stored_in_db(conn, patient):
    create_cycle(conn, _make_cycle(patient.id, cycle_number=3))
    cycles = get_cycles_by_patient(conn, patient.id)
    assert len(cycles) == 1
    assert cycles[0].cycle_number == 3


# --- update_cycle ---

def test_update_cycle_changes_fields(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id, dose_percent=100.0))
    c.dose_percent = 75.0
    c.dose_reason = 'Neutropenia'
    update_cycle(conn, c)
    fetched = get_cycles_by_patient(conn, patient.id)[0]
    assert fetched.dose_percent == 75.0
    assert fetched.dose_reason == 'Neutropenia'


def test_update_cycle_writes_before_and_after(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id, dose_percent=100.0))
    c.dose_percent = 80.0
    update_cycle(conn, c, actor='nurse_b')
    rows = audit_module.get_audit_for_entity(conn, 'cycle', c.id)
    upd = next(r for r in rows if r['action'] == 'update')
    assert upd['before']['dose_percent'] == 100.0
    assert upd['after']['dose_percent'] == 80.0
    assert upd['actor'] == 'nurse_b'


def test_update_cycle_missing_id_raises(conn, patient):
    with pytest.raises(ValueError):
        update_cycle(conn, _make_cycle(patient.id))


def test_update_cycle_unknown_id_raises(conn, patient):
    c = _make_cycle(patient.id)
    c.id = 9999
    with pytest.raises(LookupError):
        update_cycle(conn, c)


# --- delete_cycle ---

def test_delete_cycle_removes_row(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id))
    delete_cycle(conn, c.id)
    assert get_cycles_by_patient(conn, patient.id) == []


def test_delete_cycle_preserves_before_in_audit(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id, notes='important note'))
    delete_cycle(conn, c.id, actor='admin')
    rows = audit_module.get_audit_for_entity(conn, 'cycle', c.id)
    del_row = next(r for r in rows if r['action'] == 'delete')
    assert del_row['before']['notes'] == 'important note'
    assert del_row['after'] is None
    assert del_row['actor'] == 'admin'


def test_delete_cycle_unknown_id_raises(conn, patient):
    with pytest.raises(LookupError):
        delete_cycle(conn, 9999)


# --- full lifecycle ---

def test_cycle_lifecycle_audit_trail(conn, patient):
    c = create_cycle(conn, _make_cycle(patient.id, dose_percent=100.0))
    c.dose_percent = 75.0
    update_cycle(conn, c)
    delete_cycle(conn, c.id)
    rows = audit_module.get_audit_for_entity(conn, 'cycle', c.id)
    assert [r['action'] for r in rows] == ['delete', 'update', 'create']
