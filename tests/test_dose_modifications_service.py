"""Tests for services/dose_modifications.py (US-036)."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Cycle, Patient
from services.patients import create_patient
from services.cycles import create_cycle, update_cycle
from services.dose_modifications import list_for_patient, list_for_cycle


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


@pytest.fixture
def patient(conn):
    return create_patient(conn, Patient(
        patient_id='PT-DM1', name='Dose Mod Patient',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
    ))


def _cycle(patient_id, cycle_number, dose_pct=100.0, actual_date=None, phase='AC', agent='doxorubicin'):
    from datetime import timedelta
    d = actual_date or (date(2026, 1, 1) + timedelta(days=(cycle_number - 1) * 14))
    return Cycle(
        patient_id=patient_id, cycle_number=cycle_number, phase=phase,
        actual_date=d, status='completed', dose_percent=dose_pct,
        dose_reason='ANC low' if dose_pct < 100 else None,
        anthracycline_agent=agent,
    )


# ── list_for_patient ──────────────────────────────────────────────────────────

def test_no_modifications_returns_empty(conn, patient):
    create_cycle(conn, _cycle(patient.id, 1, 100.0))
    create_cycle(conn, _cycle(patient.id, 2, 100.0))
    result = list_for_patient(conn, patient.id)
    assert result == []


def test_single_modification_returned(conn, patient):
    create_cycle(conn, _cycle(patient.id, 1, 100.0))
    create_cycle(conn, _cycle(patient.id, 2, 75.0))
    result = list_for_patient(conn, patient.id)
    assert len(result) == 1
    assert result[0].cycle_number == 2
    assert result[0].dose_pct == 75.0


def test_multiple_modifications_ordered_by_cycle(conn, patient):
    create_cycle(conn, _cycle(patient.id, 1, 100.0))
    create_cycle(conn, _cycle(patient.id, 2, 75.0))
    create_cycle(conn, _cycle(patient.id, 3, 100.0))
    create_cycle(conn, _cycle(patient.id, 5, 80.0))
    result = list_for_patient(conn, patient.id)
    assert len(result) == 2
    assert result[0].cycle_number == 2
    assert result[1].cycle_number == 5


def test_modification_has_reason(conn, patient):
    create_cycle(conn, _cycle(patient.id, 2, 75.0))
    result = list_for_patient(conn, patient.id)
    assert result[0].reason == 'ANC low'


def test_modification_has_date(conn, patient):
    create_cycle(conn, _cycle(patient.id, 2, 75.0, actual_date=date(2026, 2, 14)))
    result = list_for_patient(conn, patient.id)
    assert result[0].date == date(2026, 2, 14)


def test_modification_has_agent(conn, patient):
    create_cycle(conn, _cycle(patient.id, 2, 75.0, agent='epirubicin'))
    result = list_for_patient(conn, patient.id)
    assert result[0].agent == 'epirubicin'


def test_prior_pct_defaults_100_for_create(conn, patient):
    create_cycle(conn, _cycle(patient.id, 2, 75.0))
    result = list_for_patient(conn, patient.id)
    # On initial create there's no 'before' state in audit; prior_pct defaults to 100
    assert result[0].prior_pct == 100.0


def test_prior_pct_from_update(conn, patient):
    c = create_cycle(conn, _cycle(patient.id, 2, 100.0))
    c.dose_percent = 80.0
    c.dose_reason = 'Weight loss'
    update_cycle(conn, c)
    result = list_for_patient(conn, patient.id)
    assert len(result) == 1
    assert result[0].dose_pct == 80.0
    assert result[0].prior_pct == 100.0


def test_actor_populated_from_audit(conn, patient):
    create_cycle(conn, _cycle(patient.id, 2, 75.0), actor='nurse_x')
    result = list_for_patient(conn, patient.id)
    assert result[0].actor == 'nurse_x'


def test_empty_patient_returns_empty(conn, patient):
    result = list_for_patient(conn, patient.id)
    assert result == []


# ── list_for_cycle ────────────────────────────────────────────────────────────

def test_list_for_cycle_returns_modification(conn, patient):
    c = create_cycle(conn, _cycle(patient.id, 2, 80.0))
    result = list_for_cycle(conn, c.id)
    assert len(result) == 1
    assert result[0].cycle_number == 2


def test_list_for_cycle_empty_when_full_dose(conn, patient):
    c = create_cycle(conn, _cycle(patient.id, 1, 100.0))
    result = list_for_cycle(conn, c.id)
    assert result == []


def test_list_for_cycle_nonexistent_returns_empty(conn, patient):
    result = list_for_cycle(conn, 99999)
    assert result == []


# ── Three-cycle fixture (C2 reduction + C5 reduction) ────────────────────────

def test_fixture_three_cycle(conn, patient):
    for i in range(1, 9):
        pct = 75.0 if i == 2 else (80.0 if i == 5 else 100.0)
        create_cycle(conn, _cycle(patient.id, i, pct))

    result = list_for_patient(conn, patient.id)
    assert len(result) == 2
    cycles = [m.cycle_number for m in result]
    assert 2 in cycles
    assert 5 in cycles
