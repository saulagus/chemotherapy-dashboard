import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Lab, Patient, get_labs_by_patient, get_latest_lab
from services import audit as audit_module
from services.patients import create_patient
from services.labs import create_lab, update_lab, delete_lab


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


def _make_lab(patient_id, **kwargs):
    defaults = dict(
        lab_date=date(2026, 1, 10),
        anc=2.0, wbc=5.0, platelets=200.0, hemoglobin=12.0,
    )
    defaults.update(kwargs)
    return Lab(patient_id=patient_id, **defaults)


# --- create_lab ---

def test_create_lab_returns_with_id(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id))
    assert lab.id is not None


def test_create_lab_writes_audit(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id, anc=1.8), actor='nurse_a')
    rows = audit_module.get_audit_for_entity(conn, 'lab', lab.id)
    assert len(rows) == 1
    assert rows[0]['action'] == 'create'
    assert rows[0]['actor'] == 'nurse_a'
    assert rows[0]['after']['anc'] == 1.8


def test_create_lab_stored_in_db(conn, patient):
    create_lab(conn, _make_lab(patient.id, anc=2.5))
    latest = get_latest_lab(conn, patient.id)
    assert latest is not None
    assert latest.anc == 2.5


# --- update_lab ---

def test_update_lab_changes_fields(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id, anc=2.0))
    lab.anc = 0.8
    lab.platelets = 90.0
    update_lab(conn, lab)
    fetched = get_labs_by_patient(conn, patient.id)[0]
    assert fetched.anc == 0.8
    assert fetched.platelets == 90.0


def test_update_lab_writes_before_and_after(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id, anc=2.0))
    lab.anc = 1.2
    update_lab(conn, lab, actor='nurse_b')
    rows = audit_module.get_audit_for_entity(conn, 'lab', lab.id)
    upd = next(r for r in rows if r['action'] == 'update')
    assert upd['before']['anc'] == 2.0
    assert upd['after']['anc'] == 1.2
    assert upd['actor'] == 'nurse_b'


def test_update_lab_missing_id_raises(conn, patient):
    with pytest.raises(ValueError):
        update_lab(conn, _make_lab(patient.id))


def test_update_lab_unknown_id_raises(conn, patient):
    lab = _make_lab(patient.id)
    lab.id = 9999
    with pytest.raises(LookupError):
        update_lab(conn, lab)


# --- delete_lab ---

def test_delete_lab_removes_row(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id))
    delete_lab(conn, lab.id)
    assert get_labs_by_patient(conn, patient.id) == []


def test_delete_lab_preserves_before_in_audit(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id, anc=1.1))
    delete_lab(conn, lab.id, actor='admin')
    rows = audit_module.get_audit_for_entity(conn, 'lab', lab.id)
    del_row = next(r for r in rows if r['action'] == 'delete')
    assert del_row['before']['anc'] == 1.1
    assert del_row['after'] is None
    assert del_row['actor'] == 'admin'


def test_delete_lab_unknown_id_raises(conn, patient):
    with pytest.raises(LookupError):
        delete_lab(conn, 9999)


# --- full lifecycle ---

def test_lab_lifecycle_audit_trail(conn, patient):
    lab = create_lab(conn, _make_lab(patient.id, anc=2.0))
    lab.anc = 0.9
    update_lab(conn, lab)
    delete_lab(conn, lab.id)
    rows = audit_module.get_audit_for_entity(conn, 'lab', lab.id)
    assert [r['action'] for r in rows] == ['delete', 'update', 'create']
