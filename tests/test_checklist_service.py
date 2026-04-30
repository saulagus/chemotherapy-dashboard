"""Tests for src/services/checklist.py — integration with DB fixtures."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, Lab, add_patient, add_lab
from services.checklist import evaluate, gather_inputs
import config as config_module


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    config_module.reset()
    yield connection
    connection.close()
    config_module.reset()


@pytest.fixture
def patient_with_labs(conn):
    p = add_patient(conn, Patient(patient_id='PT-100', name='Test Patient',
                                   dose_density='standard_q3w'))
    add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                      anc=2.0, platelets=200.0))
    return p


class TestGatherInputs:

    def test_basic_inputs_populated(self, conn, patient_with_labs):
        inputs = gather_inputs(conn, patient_with_labs.id, 1, date(2026, 5, 1), True)
        assert inputs.phase == 'AC'
        assert inputs.latest_anc == 2.0
        assert inputs.latest_platelets == 200.0
        assert inputs.nurse_attests_no_infection is True

    def test_t_phase_for_cycle_5(self, conn, patient_with_labs):
        inputs = gather_inputs(conn, patient_with_labs.id, 5, date(2026, 5, 1))
        assert inputs.phase == 'T'

    def test_no_labs(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-101', name='No Labs'))
        inputs = gather_inputs(conn, p.id, 1, date(2026, 5, 1))
        assert inputs.latest_anc is None
        assert inputs.latest_platelets is None
        assert inputs.latest_lab_draw_date is None


class TestEvaluate:

    def test_all_pass_with_good_labs(self, conn, patient_with_labs):
        result = evaluate(conn, patient_with_labs.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        assert result.worst_status == 'pass'
        assert result.can_save_without_override is True
        assert len(result.rules) == 9

    def test_soft_block_without_infection_attestation(self, conn, patient_with_labs):
        result = evaluate(conn, patient_with_labs.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=False)
        assert result.worst_status == 'soft_block'

    def test_advisory_with_stale_labs(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-102', name='Stale'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 20),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        stale_rule = [r for r in result.rules if r.rule_id == 'labs_stale'][0]
        assert stale_rule.status == 'advisory'
