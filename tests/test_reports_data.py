"""Tests for reports/data.py (Sprint 9 — US-035)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import TODAY, make_config, make_conn, seed_report_patient
from reports.data import gather


@pytest.fixture
def conn():
    connection = make_conn()
    yield connection
    connection.close()


@pytest.fixture
def cfg():
    return make_config()


def test_gather_populates_all_report_sections(conn, cfg):
    seeded = seed_report_patient(conn)

    data = gather(conn, seeded.patient.id, cfg, TODAY)

    assert data.patient_id == 'PT-RPT1'
    assert data.latest_cycle.cycle_number == 2
    assert data.latest_cycle_dose_mods[0].dose_pct == 80.0
    assert data.cumulative_total_mg_per_m2 > 0
    assert data.lvef_latest.lvef_percent == 56.0
    assert data.latest_labs.anc == 1.1
    assert len(data.lab_history) == 2
    assert data.neuropathy_effective_grade == 2
    assert data.reaction_latest.severity_grade == 2
    assert data.gcsf_latest.agent == 'pegfilgrastim'
    assert data.symptom_entries[0].symptom == 'nausea'
    assert data.last_checklist_result is not None
    assert data.recent_audit
    assert data.dose_mod_history[0].cycle_id == seeded.cycle2.id


def test_gather_unknown_patient_raises_lookup_error(conn, cfg):
    with pytest.raises(LookupError):
        gather(conn, 99999, cfg, TODAY)


def test_gather_empty_patient_uses_empty_defaults(conn, cfg):
    from models import Patient
    from services.patients import create_patient

    patient = create_patient(conn, Patient(
        patient_id='PT-EMPTY',
        name='Empty Patient',
        start_date=TODAY,
        protocol='Standard AC-T',
        total_cycles=8,
    ))

    data = gather(conn, patient.id, cfg, TODAY)

    assert data.latest_cycle is None
    assert data.latest_labs is None
    assert data.lab_history == []
    assert data.cumulative_total_mg_per_m2 == 0.0
    assert data.last_checklist_result is None
