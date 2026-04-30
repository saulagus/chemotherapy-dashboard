"""Sprint 8 end-to-end integration tests.

Cross-story scenarios verifying that all four US-031 through US-034 stories
work together: patient list filtering reflects real cycle status, pre-cycle
checklist blocks unsafe cycles, and the low-ANC banner triggers from labs
that also affect checklist evaluation.
"""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, Lab, Cycle, add_patient, add_lab, add_cycle, LvefAssessment
from services.patients import list_patients
from services.checklist import evaluate
from services.cycles import last_completed_cycle_date
from services.lvef import create_lvef
from services.neuropathy import NeuropathyAssessment, create_neuropathy
from services.symptoms import SymptomEntry, create_symptom
from views.components.cycle_status_indicator import (
    get_status_for_patient, status_sort_key, status_color,
)
from config import get as get_config
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
# Scenario 1: Full patient journey — new → on_schedule → due_soon → overdue
# with checklist passing at each step
# ---------------------------------------------------------------------------

class TestPatientJourney:

    def test_new_patient_no_cycles_status(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-001', name='Journey Test',
                                       dose_density='standard_q3w'))
        code, text, tip = get_status_for_patient(conn, p.id)
        assert code == 'no_cycles'

    def test_after_cycle1_on_schedule(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-002', name='Journey On',
                                       dose_density='standard_q3w'))
        today = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=today))
        code, _, _ = get_status_for_patient(conn, p.id, today=today + timedelta(days=5))
        assert code == 'on_schedule'

    def test_transitions_to_due_soon(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-003', name='Journey Due',
                                       dose_density='standard_q3w'))
        cycle_date = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=cycle_date))
        code, _, _ = get_status_for_patient(conn, p.id,
                                             today=cycle_date + timedelta(days=17))
        assert code == 'due_soon'

    def test_transitions_to_overdue(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-004', name='Journey Late',
                                       dose_density='standard_q3w'))
        cycle_date = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=cycle_date))
        code, _, _ = get_status_for_patient(conn, p.id,
                                             today=cycle_date + timedelta(days=25))
        assert code == 'overdue'

    def test_checklist_passes_for_healthy_patient(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-005', name='Journey OK',
                                       dose_density='standard_q3w'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 5, 1),
                          anc=2.0, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 2),
                          nurse_attests_no_infection=True)
        assert result.worst_status == 'pass'
        assert result.can_save_without_override is True


# ---------------------------------------------------------------------------
# Scenario 2: Low ANC triggers banner AND blocks checklist
# ---------------------------------------------------------------------------

class TestLowAncCrossStory:

    def test_low_anc_triggers_banner_threshold(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-010', name='Low ANC'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 5, 1), anc=0.4))
        from models import get_latest_lab
        lab = get_latest_lab(conn, p.id)
        cfg = get_config().alerts.low_anc_banner
        assert lab.anc < cfg.red_below_per_uL / 1000

    def test_low_anc_also_blocks_checklist(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-011', name='ANC Block'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 5, 1),
                          anc=0.8, platelets=200.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 2),
                          nurse_attests_no_infection=True)
        anc_rule = [r for r in result.rules if r.rule_id == 'anc_below_threshold'][0]
        assert anc_rule.status == 'soft_block'
        assert result.can_save_without_override is False

    def test_normal_anc_passes_both(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-012', name='ANC OK'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 5, 1),
                          anc=2.5, platelets=200.0))
        from models import get_latest_lab
        lab = get_latest_lab(conn, p.id)
        cfg = get_config().alerts.low_anc_banner
        assert lab.anc >= cfg.orange_below_per_uL / 1000
        result = evaluate(conn, p.id, 1, date(2026, 5, 2),
                          nurse_attests_no_infection=True)
        assert result.worst_status == 'pass'

    def test_borderline_anc_orange_banner_soft_block(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-013', name='ANC Border'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 5, 1),
                          anc=0.9, platelets=200.0))
        from models import get_latest_lab
        lab = get_latest_lab(conn, p.id)
        cfg = get_config().alerts.low_anc_banner
        assert lab.anc >= cfg.red_below_per_uL / 1000
        assert lab.anc < cfg.orange_below_per_uL / 1000
        result = evaluate(conn, p.id, 1, date(2026, 5, 2),
                          nurse_attests_no_infection=True)
        anc_rule = [r for r in result.rules if r.rule_id == 'anc_below_threshold'][0]
        assert anc_rule.status == 'soft_block'


# ---------------------------------------------------------------------------
# Scenario 3: Patient list search/filter reflects cycle completion state
# ---------------------------------------------------------------------------

class TestPatientListIntegration:

    def test_search_finds_by_name(self, conn):
        add_patient(conn, Patient(patient_id='E2E-020', name='Alice Smith'))
        add_patient(conn, Patient(patient_id='E2E-021', name='Bob Jones'))
        results = list_patients(conn, search='alice')
        assert len(results) == 1
        assert results[0].name == 'Alice Smith'

    def test_search_finds_by_id(self, conn):
        add_patient(conn, Patient(patient_id='E2E-020', name='Alice Smith'))
        add_patient(conn, Patient(patient_id='E2E-021', name='Bob Jones'))
        results = list_patients(conn, search='E2E-021')
        assert len(results) == 1
        assert results[0].name == 'Bob Jones'

    def test_phase_filter_ac(self, conn):
        p1 = add_patient(conn, Patient(patient_id='E2E-030', name='AC Patient'))
        p2 = add_patient(conn, Patient(patient_id='E2E-031', name='T Patient'))
        add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=date(2026, 5, 1)))
        for i in range(1, 5):
            add_cycle(conn, Cycle(patient_id=p2.id, cycle_number=i, phase='AC',
                                  status='completed', actual_date=date(2026, 4, i)))
        add_cycle(conn, Cycle(patient_id=p2.id, cycle_number=5, phase='T',
                              status='completed', actual_date=date(2026, 5, 1)))
        results = list_patients(conn, phase_filter='AC')
        ids = [r.patient_id for r in results]
        assert 'E2E-030' in ids
        assert 'E2E-031' not in ids

    def test_phase_filter_completed(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-032', name='Done Patient'))
        phases = ['AC'] * 4 + ['T'] * 4
        for i, phase in enumerate(phases, 1):
            add_cycle(conn, Cycle(patient_id=p.id, cycle_number=i, phase=phase,
                                  status='completed', actual_date=date(2026, 4, i)))
        results = list_patients(conn, phase_filter='Completed')
        assert len(results) == 1
        assert results[0].patient_id == 'E2E-032'

    def test_sort_by_name_asc(self, conn):
        add_patient(conn, Patient(patient_id='E2E-040', name='Zara'))
        add_patient(conn, Patient(patient_id='E2E-041', name='Alice'))
        results = list_patients(conn, sort_by='name', sort_dir='asc')
        assert results[0].name == 'Alice'
        assert results[1].name == 'Zara'

    def test_sort_by_name_desc(self, conn):
        add_patient(conn, Patient(patient_id='E2E-040', name='Zara'))
        add_patient(conn, Patient(patient_id='E2E-041', name='Alice'))
        results = list_patients(conn, sort_by='name', sort_dir='desc')
        assert results[0].name == 'Zara'


# ---------------------------------------------------------------------------
# Scenario 4: Checklist integrates with LVEF, neuropathy, and symptoms
# ---------------------------------------------------------------------------

class TestChecklistMultiRule:

    def test_multiple_blocks_worst_wins(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-050', name='Multi Block',
                                       dose_density='standard_q3w'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=0.8, platelets=50.0))
        result = evaluate(conn, p.id, 1, date(2026, 5, 1),
                          nurse_attests_no_infection=False)
        assert result.worst_status == 'soft_block'
        block_rules = [r for r in result.rules if r.status == 'soft_block']
        rule_ids = {r.rule_id for r in block_rules}
        assert 'anc_below_threshold' in rule_ids
        assert 'platelets_below_threshold' in rule_ids
        assert 'active_infection' in rule_ids

    def test_t_phase_neuropathy_plus_stale_labs(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-051', name='T Complex'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 20),
                          anc=2.0, platelets=200.0))
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id=p.patient_id, assessment_date='2026-04-28',
            sensory_grade=2, motor_grade=1))
        result = evaluate(conn, p.id, 5, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        stale = [r for r in result.rules if r.rule_id == 'labs_stale'][0]
        neuro = [r for r in result.rules if r.rule_id == 'neuropathy_t_above_max'][0]
        assert stale.status == 'advisory'
        assert neuro.status == 'soft_block'
        assert result.worst_status == 'soft_block'

    def test_ac_phase_cumulative_plus_lvef(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-052', name='AC Cardio',
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
        create_lvef(conn, LvefAssessment(
            patient_id=p.id, assessment_date=date(2026, 3, 1),
            lvef_percent=65, modality='echo', context='baseline'))
        create_lvef(conn, LvefAssessment(
            patient_id=p.id, assessment_date=date(2026, 4, 28),
            lvef_percent=48, modality='echo'))
        result = evaluate(conn, p.id, 4, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        cum = [r for r in result.rules if r.rule_id == 'cumulative_red'][0]
        lvef = [r for r in result.rules if r.rule_id == 'lvef_abnormal'][0]
        assert cum.status == 'soft_block'
        assert lvef.status == 'soft_block'


# ---------------------------------------------------------------------------
# Scenario 5: Status sort ordering matches clinical priority
# ---------------------------------------------------------------------------

class TestStatusSortOrdering:

    def test_overdue_patients_sort_first(self, conn):
        p1 = add_patient(conn, Patient(patient_id='E2E-060', name='Overdue Pat',
                                        dose_density='standard_q3w'))
        p2 = add_patient(conn, Patient(patient_id='E2E-061', name='On Sched Pat',
                                        dose_density='standard_q3w'))
        p3 = add_patient(conn, Patient(patient_id='E2E-062', name='New Pat'))

        add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=date(2026, 3, 1)))
        add_cycle(conn, Cycle(patient_id=p2.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=date(2026, 4, 25)))

        today = date(2026, 5, 1)
        statuses = []
        for p in [p1, p2, p3]:
            code, _, _ = get_status_for_patient(conn, p.id, today=today)
            statuses.append((code, p.patient_id))

        sorted_patients = sorted(statuses, key=lambda x: status_sort_key(x[0]))
        assert sorted_patients[0][1] == 'E2E-060'
        assert sorted_patients[-1][1] == 'E2E-062'


# ---------------------------------------------------------------------------
# Scenario 6: Dose-dense schedule changes checklist staleness window
# ---------------------------------------------------------------------------

class TestDoseDenseScheduling:

    def test_dose_dense_shorter_cadence(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-070', name='DD Patient',
                                       dose_density='dose_dense_q2w'))
        cycle_date = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=cycle_date))
        code, _, _ = get_status_for_patient(conn, p.id,
                                             today=cycle_date + timedelta(days=18))
        assert code == 'overdue'

    def test_standard_not_overdue_at_day_18(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-071', name='Std Patient',
                                       dose_density='standard_q3w'))
        cycle_date = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=cycle_date))
        code, _, _ = get_status_for_patient(conn, p.id,
                                             today=cycle_date + timedelta(days=18))
        assert code == 'due_soon'


# ---------------------------------------------------------------------------
# Scenario 7: Complete treatment lifecycle — AC → T transition
# ---------------------------------------------------------------------------

class TestACToTTransition:

    def test_phase_transition_checklist_rules_change(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-080', name='Transition',
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
        result_ac = evaluate(conn, p.id, 4, date(2026, 5, 1),
                             nurse_attests_no_infection=True)
        cum_ac = [r for r in result_ac.rules if r.rule_id == 'cumulative_red'][0]
        assert cum_ac.status == 'soft_block'

        result_t = evaluate(conn, p.id, 5, date(2026, 5, 1),
                            nurse_attests_no_infection=True)
        cum_t = [r for r in result_t.rules if r.rule_id == 'cumulative_red'][0]
        assert cum_t.status == 'pass'
        assert 'T phase' in cum_t.message

    def test_neuropathy_only_blocks_t_phase(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-081', name='Neuro Trans'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id=p.patient_id, assessment_date='2026-04-28',
            sensory_grade=3, motor_grade=2))
        result_ac = evaluate(conn, p.id, 3, date(2026, 5, 1),
                             nurse_attests_no_infection=True)
        neuro_ac = [r for r in result_ac.rules if r.rule_id == 'neuropathy_t_above_max'][0]
        assert neuro_ac.status == 'pass'

        result_t = evaluate(conn, p.id, 6, date(2026, 5, 1),
                            nurse_attests_no_infection=True)
        neuro_t = [r for r in result_t.rules if r.rule_id == 'neuropathy_t_above_max'][0]
        assert neuro_t.status == 'soft_block'


# ---------------------------------------------------------------------------
# Scenario 8: Symptoms from prior cycle raise advisory on next
# ---------------------------------------------------------------------------

class TestSymptomCarryover:

    def test_grade3_symptom_advisory_on_next_cycle(self, conn):
        p = add_patient(conn, Patient(patient_id='E2E-090', name='Symptom Carry'))
        add_lab(conn, Lab(patient_id=p.id, lab_date=date(2026, 4, 30),
                          anc=2.0, platelets=200.0))
        c = add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                                   status='completed', actual_date=date(2026, 4, 28)))
        create_symptom(conn, SymptomEntry(
            patient_id=p.patient_id, entry_date='2026-04-28',
            symptom='fatigue', grade=3, cycle_id=c.id))
        result = evaluate(conn, p.id, 2, date(2026, 5, 1),
                          nurse_attests_no_infection=True)
        sym = [r for r in result.rules if r.rule_id == 'symptoms_grade_3_or_higher'][0]
        assert sym.status == 'advisory'
        assert result.can_save_without_override is True


# ---------------------------------------------------------------------------
# Scenario 9: Soft-deleted patients excluded from list
# ---------------------------------------------------------------------------

class TestSoftDeleteExclusion:

    def test_deleted_patient_not_in_list(self, conn):
        add_patient(conn, Patient(patient_id='E2E-100', name='Active'))
        p2 = add_patient(conn, Patient(patient_id='E2E-101', name='Deleted'))
        conn.execute("UPDATE patients SET deleted_at = ? WHERE id = ?",
                     ('2026-04-30T00:00:00', p2.id))
        conn.commit()
        results = list_patients(conn)
        ids = [r.patient_id for r in results]
        assert 'E2E-100' in ids
        assert 'E2E-101' not in ids
