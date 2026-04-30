"""Tests for pre-cycle checklist dialog integration (US-033).

Tests the checklist service end-to-end with DB fixtures covering
all four paths: pass / advisory / soft-block / hard-block.
"""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, Lab, Cycle, add_patient, add_lab, add_cycle, LvefAssessment
from services.checklist import evaluate, gather_inputs
from services.lvef import create_lvef
from services.neuropathy import NeuropathyAssessment, create_neuropathy
from services.symptoms import SymptomEntry, create_symptom
from services.audit import ACTIONS
import config as config_module


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    config_module.reset()
    yield connection
    connection.close()
    config_module.reset()


# ---------------------------------------------------------------------------
# Path 1: All green — checklist passes
# ---------------------------------------------------------------------------

class TestAllPass:

    def test_healthy_ac_patient(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-300', name='Healthy AC',
                                       dose_density='standard_q3w'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        assert result.worst_status == 'pass'
        assert result.can_save_without_override is True
        assert all(r.status == 'pass' for r in result.rules)

    def test_healthy_t_patient(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-301', name='Healthy T',
                                       dose_density='standard_q3w'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 5, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        assert result.worst_status == 'pass'


# ---------------------------------------------------------------------------
# Path 2: Advisory — stale labs or high symptoms
# ---------------------------------------------------------------------------

class TestAdvisory:

    def test_stale_labs_advisory(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-302', name='Stale Labs'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 20),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        stale = [r for r in result.rules if r.rule_id == 'labs_stale'][0]
        assert stale.status == 'advisory'
        assert result.can_save_without_override is True

    def test_high_symptoms_advisory(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-303', name='High Symptoms'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        c = add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                                   status='completed', actual_date=date(2026, 4, 28)))
        create_symptom(conn, SymptomEntry(
            patient_id=p.patient_id, entry_date='2026-04-28',
            symptom='nausea', grade=3, cycle_id=c.id))
        result = evaluate(conn, p.id, 2, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        sym = [r for r in result.rules if r.rule_id == 'symptoms_grade_3_or_higher'][0]
        assert sym.status == 'advisory'


# ---------------------------------------------------------------------------
# Path 3: Soft block — low ANC / no infection attestation
# ---------------------------------------------------------------------------

class TestSoftBlock:

    def test_low_anc_soft_block(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-304', name='Low ANC'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=1.0, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        anc_rule = [r for r in result.rules if r.rule_id == 'anc_below_threshold'][0]
        assert anc_rule.status == 'soft_block'
        assert result.worst_status == 'soft_block'
        assert result.can_save_without_override is False

    def test_no_infection_attestation(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-305', name='No Attest'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=False)
        inf = [r for r in result.rules if r.rule_id == 'active_infection'][0]
        assert inf.status == 'soft_block'

    def test_t_phase_neuropathy_soft_block(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-306', name='Neuro Block'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id=p.patient_id, assessment_date='2026-04-28',
            sensory_grade=2, motor_grade=1))
        result = evaluate(conn, p.id, 5, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        neuro = [r for r in result.rules if r.rule_id == 'neuropathy_t_above_max'][0]
        assert neuro.status == 'soft_block'

    def test_cumulative_red_soft_block(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-307', name='Cum Red',
                                       dose_density='standard_q3w'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        for i in range(1, 5):
            add_cycle(conn, Cycle(
                patient_id=p.id, cycle_number=i, phase='AC',
                status='completed', actual_date=date(2026, 3, i),
                height_cm=170, weight_kg=70, bsa_m2=1.8,
                anthracycline_agent='doxorubicin',
                dose_mg_total=180, dose_mg_per_m2=100,
            ))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        cum = [r for r in result.rules if r.rule_id == 'cumulative_red'][0]
        assert cum.status == 'soft_block'


# ---------------------------------------------------------------------------
# Path 4: Hard block — cumulative hard stop
# ---------------------------------------------------------------------------

class TestHardBlock:

    def test_cumulative_hard_stop(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-308', name='Cum Stop',
                                       dose_density='standard_q3w'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        for i in range(1, 5):
            add_cycle(conn, Cycle(
                patient_id=p.id, cycle_number=i, phase='AC',
                status='completed', actual_date=date(2026, 3, i),
                height_cm=170, weight_kg=70, bsa_m2=1.8,
                anthracycline_agent='doxorubicin',
                dose_mg_total=220, dose_mg_per_m2=122,
            ))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        hard = [r for r in result.rules if r.rule_id == 'cumulative_hard_stop'][0]
        assert hard.status == 'hard_block'
        assert result.worst_status == 'hard_block'
        assert result.can_save_without_override is False


# ---------------------------------------------------------------------------
# Phase gating
# ---------------------------------------------------------------------------

class TestPhaseGating:

    def test_ac_skips_neuropathy(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-309', name='AC Neuro Skip'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id=p.patient_id, assessment_date='2026-04-28',
            sensory_grade=3, motor_grade=2))
        result = evaluate(conn, p.id, 2, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        neuro = [r for r in result.rules if r.rule_id == 'neuropathy_t_above_max'][0]
        assert neuro.status == 'pass'
        assert 'AC phase' in neuro.message

    def test_t_skips_cumulative(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-310', name='T Cum Skip'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 6, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        cum_red = [r for r in result.rules if r.rule_id == 'cumulative_red'][0]
        cum_hs = [r for r in result.rules if r.rule_id == 'cumulative_hard_stop'][0]
        lvef = [r for r in result.rules if r.rule_id == 'lvef_abnormal'][0]
        assert all(r.status == 'pass' for r in [cum_red, cum_hs, lvef])


# ---------------------------------------------------------------------------
# LVEF integration
# ---------------------------------------------------------------------------

class TestLvefIntegration:

    def test_lvef_hold_soft_blocks(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-311', name='LVEF Hold'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        create_lvef(conn, LvefAssessment(
            patient_id=p.id, assessment_date=date(2026, 4, 1),
            lvef_percent=65, modality='echo', context='baseline'))
        create_lvef(conn, LvefAssessment(
            patient_id=p.id, assessment_date=date(2026, 4, 28),
            lvef_percent=48, modality='echo'))
        result = evaluate(conn, p.id, 2, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        lvef_rule = [r for r in result.rules if r.rule_id == 'lvef_abnormal'][0]
        assert lvef_rule.status == 'soft_block'


# ---------------------------------------------------------------------------
# Audit action registered
# ---------------------------------------------------------------------------

class TestAuditAction:

    def test_checklist_override_in_actions(self):
        assert 'checklist_override' in ACTIONS
