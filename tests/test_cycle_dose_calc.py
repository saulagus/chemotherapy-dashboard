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
from services.cycles import create_cycle, cumulative_dose, update_cycle


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


# ===========================================================================
# cumulative_dose integration tests
# ===========================================================================

def _dox_cycle(patient_id, cycle_number, dose_mg_per_m2=60.0):
    """Helper: a completed doxorubicin cycle with explicit dose_mg_per_m2."""
    c = Cycle(
        patient_id=patient_id, cycle_number=cycle_number, phase='AC',
        actual_date=date(2026, 1, cycle_number), status='completed',
        anthracycline_agent='doxorubicin',
        # Set height/weight so the service computes bsa_m2 and dose_mg_per_m2.
        # BSA ≈ 1.752 m²  →  dose_mg_total = dose_mg_per_m2 × 1.752
        height_cm=170.0, weight_kg=65.0,
        dose_mg_total=round(dose_mg_per_m2 * 1.752, 2),
    )
    return c


# --- happy path ---

def test_cumulative_dose_four_dox_cycles_green(conn, patient):
    """Acceptance criterion: 4 × 60 mg/m² dox → 240 mg/m² → green."""
    for i in range(1, 5):
        create_cycle(conn, _dox_cycle(patient.id, i, 60.0))
    summary = cumulative_dose(conn, patient.id)
    assert summary.total_mg_per_m2 == pytest.approx(240.0, abs=1.0)
    assert summary.status == 'green'


def test_cumulative_dose_breakdown_contains_doxorubicin(conn, patient):
    create_cycle(conn, _dox_cycle(patient.id, 1, 60.0))
    summary = cumulative_dose(conn, patient.id)
    assert 'doxorubicin' in summary.agent_breakdown
    assert summary.agent_breakdown['doxorubicin'] == pytest.approx(60.0, abs=1.0)


def test_cumulative_dose_yellow_at_300(conn, patient):
    # 5 cycles × 60 mg/m² = 300 mg/m² → yellow
    for i in range(1, 6):
        create_cycle(conn, _dox_cycle(patient.id, i, 60.0))
    summary = cumulative_dose(conn, patient.id)
    assert summary.total_mg_per_m2 == pytest.approx(300.0, abs=2.0)
    assert summary.status == 'yellow'


def test_cumulative_dose_includes_prior_exposure(conn):
    """Prior anthracycline dose on the Patient record adds to the total."""
    p = create_patient(conn, Patient(
        patient_id='PT-PRIOR', name='Prior Patient',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=120.0,
        prior_anthracycline_agent='doxorubicin',
    ))
    create_cycle(conn, _dox_cycle(p.id, 1, 60.0))
    summary = cumulative_dose(conn, p.id)
    assert summary.total_mg_per_m2 == pytest.approx(180.0, abs=1.0)


def test_cumulative_dose_zero_for_no_dose_data(conn, patient):
    """Cycles without agent/dose data contribute 0."""
    create_cycle(conn, Cycle(
        patient_id=patient.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 1), status='completed',
    ))
    summary = cumulative_dose(conn, patient.id)
    assert summary.total_mg_per_m2 == 0.0
    assert summary.status == 'green'


def test_cumulative_dose_no_cycles_returns_zero(conn, patient):
    summary = cumulative_dose(conn, patient.id)
    assert summary.total_mg_per_m2 == 0.0
    assert summary.status == 'green'
    assert summary.agent_breakdown == {}
