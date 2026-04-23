import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Cycle, Lab, Patient
from services.audit import get_audit_for_patient
from services.cycles import create_cycle, delete_cycle
from services.labs import create_lab, update_lab, delete_lab
from services.patients import create_patient, update_patient


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


def test_audit_for_patient_empty_for_new_patient_only_create(conn, patient):
    rows = get_audit_for_patient(conn, patient.id)
    # Just the patient-create row.
    assert len(rows) == 1
    assert rows[0]['entity'] == 'patient'
    assert rows[0]['action'] == 'create'


def test_audit_for_patient_includes_cycles_and_labs(conn, patient):
    cycle = create_cycle(conn, Cycle(
        patient_id=patient.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 15), status='completed', dose_percent=100.0,
    ))
    lab = create_lab(conn, Lab(
        patient_id=patient.id, lab_date=date(2026, 1, 10),
        anc=2.0, wbc=5.0, platelets=200.0, hemoglobin=12.0,
    ))
    lab.anc = 1.1
    update_lab(conn, lab)

    rows = get_audit_for_patient(conn, patient.id)
    entities = [(r['entity'], r['action']) for r in rows]
    assert ('patient', 'create') in entities
    assert ('cycle', 'create') in entities
    assert ('lab', 'create') in entities
    assert ('lab', 'update') in entities


def test_audit_for_patient_still_includes_deleted_children(conn, patient):
    """Hard-deleted cycles/labs should remain in the patient history."""
    cycle = create_cycle(conn, Cycle(
        patient_id=patient.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 15), status='completed', dose_percent=100.0,
    ))
    lab = create_lab(conn, Lab(
        patient_id=patient.id, lab_date=date(2026, 1, 10), anc=2.0,
    ))
    delete_cycle(conn, cycle.id)
    delete_lab(conn, lab.id)

    rows = get_audit_for_patient(conn, patient.id)
    actions = [(r['entity'], r['action']) for r in rows]
    assert ('cycle', 'delete') in actions
    assert ('lab', 'delete') in actions


def test_audit_for_patient_ordered_newest_first(conn, patient):
    patient.name = 'Alpha Updated'
    update_patient(conn, patient)
    rows = get_audit_for_patient(conn, patient.id)
    # Update is newer than create; it should come first.
    assert rows[0]['action'] == 'update'
    assert rows[-1]['action'] == 'create'


def test_audit_for_patient_excludes_other_patients(conn, patient):
    other = create_patient(conn, Patient(
        patient_id='PT-002', name='Bravo',
        start_date=date(2026, 2, 1), protocol='Standard AC-T', total_cycles=8,
    ))
    create_cycle(conn, Cycle(
        patient_id=other.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 2, 15), status='completed', dose_percent=100.0,
    ))
    rows = get_audit_for_patient(conn, patient.id)
    # None of the returned rows should reference the other patient.
    for r in rows:
        snap = r['after'] or r['before'] or {}
        if r['entity'] in ('cycle', 'lab'):
            assert snap.get('patient_id') == patient.id
        else:
            assert r['entity_id'] == patient.id
