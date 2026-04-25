"""Tests for BSA and dose_mg_per_m2 auto-computation in CycleService.

Covers: create_cycle and update_cycle computing bsa_m2 and dose_mg_per_m2
when height/weight/dose_mg_total are supplied, and leaving them None when not.
"""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Cycle, Patient, get_cycles_by_patient
from services.patients import create_patient
from services.cycles import create_cycle, update_cycle


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


@pytest.fixture
def patient(conn):
    return create_patient(conn, Patient(
        patient_id='PT-001', name='Dose Patient',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
    ))


def _base_cycle(patient_id, **kwargs):
    defaults = dict(
        cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 15), status='completed',
    )
    defaults.update(kwargs)
    return Cycle(patient_id=patient_id, **defaults)


# ---------------------------------------------------------------------------
# create_cycle — BSA auto-compute
# ---------------------------------------------------------------------------

def test_create_cycle_computes_bsa_when_height_weight_present(conn, patient):
    c = create_cycle(conn, _base_cycle(patient.id, height_cm=170, weight_kg=65))
    assert c.bsa_m2 is not None
    assert c.bsa_m2 == pytest.approx(1.752, abs=0.001)


def test_create_cycle_computes_dose_per_m2_when_total_present(conn, patient):
    c = create_cycle(conn, _base_cycle(
        patient.id, height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.0,
    ))
    # 105 mg / 1.752 m² ≈ 59.93 mg/m²
    assert c.dose_mg_per_m2 == pytest.approx(105.0 / c.bsa_m2, abs=0.01)


def test_create_cycle_bsa_none_when_no_height(conn, patient):
    c = create_cycle(conn, _base_cycle(patient.id, weight_kg=65))
    assert c.bsa_m2 is None
    assert c.dose_mg_per_m2 is None


def test_create_cycle_bsa_none_when_no_weight(conn, patient):
    c = create_cycle(conn, _base_cycle(patient.id, height_cm=170))
    assert c.bsa_m2 is None
    assert c.dose_mg_per_m2 is None


def test_create_cycle_dose_per_m2_none_when_no_dose_total(conn, patient):
    c = create_cycle(conn, _base_cycle(patient.id, height_cm=170, weight_kg=65))
    assert c.bsa_m2 is not None
    assert c.dose_mg_per_m2 is None


def test_create_cycle_bsa_persisted_to_db(conn, patient):
    create_cycle(conn, _base_cycle(patient.id, height_cm=170, weight_kg=65))
    fetched = get_cycles_by_patient(conn, patient.id)[0]
    assert fetched.bsa_m2 == pytest.approx(1.752, abs=0.001)


def test_create_cycle_all_dose_fields_persisted(conn, patient):
    create_cycle(conn, _base_cycle(
        patient.id, height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.0,
    ))
    fetched = get_cycles_by_patient(conn, patient.id)[0]
    assert fetched.height_cm == 170
    assert fetched.weight_kg == 65
    assert fetched.anthracycline_agent == 'doxorubicin'
    assert fetched.dose_mg_total == 105.0
    assert fetched.dose_mg_per_m2 == pytest.approx(105.0 / fetched.bsa_m2, abs=0.01)


# ---------------------------------------------------------------------------
# update_cycle — BSA auto-compute on edit
# ---------------------------------------------------------------------------

def test_update_cycle_recomputes_bsa(conn, patient):
    c = create_cycle(conn, _base_cycle(patient.id, height_cm=170, weight_kg=65))
    original_bsa = c.bsa_m2
    c.weight_kg = 75
    update_cycle(conn, c)
    fetched = get_cycles_by_patient(conn, patient.id)[0]
    assert fetched.bsa_m2 != pytest.approx(original_bsa, abs=0.001)
    assert fetched.bsa_m2 == pytest.approx(
        __import__('math').sqrt(170 * 75 / 3600), abs=0.001
    )


def test_update_cycle_clears_bsa_when_height_removed(conn, patient):
    c = create_cycle(conn, _base_cycle(patient.id, height_cm=170, weight_kg=65))
    c.height_cm = None
    update_cycle(conn, c)
    fetched = get_cycles_by_patient(conn, patient.id)[0]
    assert fetched.bsa_m2 is None
    assert fetched.dose_mg_per_m2 is None


def test_update_cycle_recomputes_dose_per_m2_on_weight_change(conn, patient):
    c = create_cycle(conn, _base_cycle(
        patient.id, height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.0,
    ))
    c.weight_kg = 75
    update_cycle(conn, c)
    fetched = get_cycles_by_patient(conn, patient.id)[0]
    expected_bsa = __import__('math').sqrt(170 * 75 / 3600)
    assert fetched.dose_mg_per_m2 == pytest.approx(105.0 / expected_bsa, abs=0.01)
