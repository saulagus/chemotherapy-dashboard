import sys
import os
import pytest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection, create_tables
from models import (
    Patient, Cycle, Lab,
    add_patient, get_all_patients, get_patient_by_id, update_patient, delete_patient,
    add_cycle, get_cycles_by_patient, update_cycle,
    add_lab, get_labs_by_patient, get_latest_lab,
)


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    create_tables(connection)
    yield connection
    connection.close()


@pytest.fixture
def sample_patient(conn):
    patient = Patient(patient_id='PT-001', name='Jane Doe', age=45,
                      diagnosis_date=date(2026, 1, 1), start_date=date(2026, 1, 15),
                      protocol='Dose-Dense AC-T', total_cycles=8)
    return add_patient(conn, patient)


# ---------------------------------------------------------------------------
# Patient CRUD
# ---------------------------------------------------------------------------

def test_add_patient_returns_with_id(conn):
    patient = Patient(patient_id='PT-001', name='Jane Doe')
    result = add_patient(conn, patient)
    assert result.id is not None


def test_add_patient_persists(conn):
    add_patient(conn, Patient(patient_id='PT-001', name='Jane Doe'))
    patients = get_all_patients(conn)
    assert len(patients) == 1
    assert patients[0].name == 'Jane Doe'


def test_get_all_patients_ordered_by_name(conn):
    add_patient(conn, Patient(patient_id='PT-002', name='Zara Smith'))
    add_patient(conn, Patient(patient_id='PT-001', name='Anna Jones'))
    patients = get_all_patients(conn)
    assert patients[0].name == 'Anna Jones'
    assert patients[1].name == 'Zara Smith'


def test_get_all_patients_empty(conn):
    assert get_all_patients(conn) == []


def test_get_patient_by_id_found(conn, sample_patient):
    result = get_patient_by_id(conn, 'PT-001')
    assert result is not None
    assert result.name == 'Jane Doe'
    assert result.age == 45
    assert result.protocol == 'Dose-Dense AC-T'


def test_get_patient_by_id_not_found(conn):
    assert get_patient_by_id(conn, 'PT-999') is None


def test_update_patient(conn, sample_patient):
    sample_patient.name = 'Jane Smith'
    sample_patient.age = 46
    update_patient(conn, sample_patient)
    result = get_patient_by_id(conn, 'PT-001')
    assert result.name == 'Jane Smith'
    assert result.age == 46


def test_delete_patient(conn, sample_patient):
    delete_patient(conn, 'PT-001')
    assert get_patient_by_id(conn, 'PT-001') is None


def test_delete_patient_not_in_list(conn, sample_patient):
    delete_patient(conn, 'PT-001')
    assert get_all_patients(conn) == []


# ---------------------------------------------------------------------------
# Cycle CRUD
# ---------------------------------------------------------------------------

def test_add_cycle_returns_with_id(conn, sample_patient):
    cycle = Cycle(patient_id=sample_patient.id, cycle_number=1,
                  phase='AC', status='completed', dose_percent=100.0)
    result = add_cycle(conn, cycle)
    assert result.id is not None


def test_get_cycles_by_patient_ordered(conn, sample_patient):
    add_cycle(conn, Cycle(patient_id=sample_patient.id, cycle_number=2, phase='AC'))
    add_cycle(conn, Cycle(patient_id=sample_patient.id, cycle_number=1, phase='AC'))
    cycles = get_cycles_by_patient(conn, sample_patient.id)
    assert cycles[0].cycle_number == 1
    assert cycles[1].cycle_number == 2


def test_get_cycles_empty(conn, sample_patient):
    assert get_cycles_by_patient(conn, sample_patient.id) == []


def test_update_cycle(conn, sample_patient):
    cycle = add_cycle(conn, Cycle(patient_id=sample_patient.id,
                                  cycle_number=1, phase='AC', status='pending'))
    cycle.status = 'completed'
    cycle.actual_date = date(2026, 2, 1)
    cycle.dose_percent = 80.0
    cycle.dose_reason = 'Neutropenia'
    update_cycle(conn, cycle)
    cycles = get_cycles_by_patient(conn, sample_patient.id)
    assert cycles[0].status == 'completed'
    assert cycles[0].dose_percent == 80.0
    assert cycles[0].dose_reason == 'Neutropenia'


def test_cycles_isolated_by_patient(conn):
    p1 = add_patient(conn, Patient(patient_id='PT-001', name='Patient One'))
    p2 = add_patient(conn, Patient(patient_id='PT-002', name='Patient Two'))
    add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=1, phase='AC'))
    assert get_cycles_by_patient(conn, p2.id) == []


# ---------------------------------------------------------------------------
# Lab CRUD
# ---------------------------------------------------------------------------

def test_add_lab_returns_with_id(conn, sample_patient):
    lab = Lab(patient_id=sample_patient.id, lab_date=date(2026, 2, 1),
              anc=1.8, wbc=4.5, platelets=180.0, hemoglobin=12.5)
    result = add_lab(conn, lab)
    assert result.id is not None


def test_get_labs_by_patient_ordered(conn, sample_patient):
    add_lab(conn, Lab(patient_id=sample_patient.id, lab_date=date(2026, 3, 1), anc=2.0))
    add_lab(conn, Lab(patient_id=sample_patient.id, lab_date=date(2026, 2, 1), anc=1.5))
    labs = get_labs_by_patient(conn, sample_patient.id)
    assert labs[0].lab_date == date(2026, 2, 1)
    assert labs[1].lab_date == date(2026, 3, 1)


def test_get_labs_empty(conn, sample_patient):
    assert get_labs_by_patient(conn, sample_patient.id) == []


def test_get_latest_lab(conn, sample_patient):
    add_lab(conn, Lab(patient_id=sample_patient.id, lab_date=date(2026, 2, 1), anc=1.5))
    add_lab(conn, Lab(patient_id=sample_patient.id, lab_date=date(2026, 3, 1), anc=2.0))
    latest = get_latest_lab(conn, sample_patient.id)
    assert latest.lab_date == date(2026, 3, 1)
    assert latest.anc == 2.0


def test_get_latest_lab_none(conn, sample_patient):
    assert get_latest_lab(conn, sample_patient.id) is None


def test_labs_isolated_by_patient(conn):
    p1 = add_patient(conn, Patient(patient_id='PT-001', name='Patient One'))
    p2 = add_patient(conn, Patient(patient_id='PT-002', name='Patient Two'))
    add_lab(conn, Lab(patient_id=p1.id, lab_date=date(2026, 2, 1), anc=1.8))
    assert get_labs_by_patient(conn, p2.id) == []
