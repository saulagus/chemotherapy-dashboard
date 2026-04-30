"""Tests for src/clinical/precycle.py — one test class per rule + aggregator."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.precycle import (
    ChecklistInputs,
    ChecklistResult,
    RuleResult,
    active_infection,
    anc_below_threshold,
    cumulative_hard_stop,
    cumulative_red,
    labs_stale,
    lvef_abnormal,
    neuropathy_t_above_max,
    platelets_below_threshold,
    run_checklist,
    symptoms_grade_3_or_higher,
)

# Default config matching institution.defaults.yaml Sprint 8 additions
PRECYCLE_CFG = {
    'precycle': {
        'anc': {
            'ac': {'min_per_uL': 1500},
            't': {'min_per_uL': 1500},
            'dose_dense_from_cycle_2': {'min_per_uL': 1000},
        },
        'platelets': {'min_per_uL': 100000},
        'active_infection': {'require_nurse_attestation': True},
        'neuropathy_t_phase_max_grade': 1,
        'symptoms_advisory_grade': 3,
        'blocking_modes': {
            'anc_below_threshold': 'soft_block',
            'platelets_below_threshold': 'soft_block',
            'labs_stale': 'advisory',
            'active_infection': 'soft_block',
            'cumulative_red': 'soft_block',
            'cumulative_hard_stop': 'hard_block',
            'lvef_abnormal': 'soft_block',
            'neuropathy_t_above_max': 'soft_block',
            'symptoms_grade_3_or_higher': 'advisory',
        },
    },
    'labs': {'freshness_hours': 72},
}


def _make_inputs(**overrides) -> ChecklistInputs:
    defaults = dict(
        phase='AC', cycle_number=1, dose_density='standard_q3w',
        planned_admin_date=date(2026, 5, 1),
        latest_anc=2.0, latest_platelets=200.0,
        latest_lab_draw_date=date(2026, 4, 30),
        nurse_attests_no_infection=True,
        cumulative_status='green', cumulative_total_mg_per_m2=120.0,
        lvef_status='ok', lvef_reason='',
        latest_neuropathy_grade=None, latest_symptom_grades=None,
    )
    defaults.update(overrides)
    return ChecklistInputs(**defaults)


# ===========================================================================
# Rule 1: ANC
# ===========================================================================

class TestAncBelowThreshold:

    def test_pass_above_threshold(self):
        r = anc_below_threshold(_make_inputs(latest_anc=2.0), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_soft_block_below_threshold_ac(self):
        r = anc_below_threshold(_make_inputs(latest_anc=1.0), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_soft_block_below_threshold_t(self):
        r = anc_below_threshold(_make_inputs(phase='T', latest_anc=1.0), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_dose_dense_lower_threshold(self):
        r = anc_below_threshold(
            _make_inputs(dose_density='dose_dense_q2w', cycle_number=3, latest_anc=1.2),
            PRECYCLE_CFG,
        )
        assert r.status == 'pass'

    def test_dose_dense_below_lower_threshold(self):
        r = anc_below_threshold(
            _make_inputs(dose_density='dose_dense_q2w', cycle_number=3, latest_anc=0.8),
            PRECYCLE_CFG,
        )
        assert r.status == 'soft_block'

    def test_no_anc_returns_advisory(self):
        r = anc_below_threshold(_make_inputs(latest_anc=None), PRECYCLE_CFG)
        assert r.status == 'advisory'

    def test_boundary_exactly_at_threshold(self):
        r = anc_below_threshold(_make_inputs(latest_anc=1.5), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_boundary_just_below(self):
        r = anc_below_threshold(_make_inputs(latest_anc=1.499), PRECYCLE_CFG)
        assert r.status == 'soft_block'


# ===========================================================================
# Rule 2: Platelets
# ===========================================================================

class TestPlateletsBelowThreshold:

    def test_pass(self):
        r = platelets_below_threshold(_make_inputs(latest_platelets=150.0), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_soft_block(self):
        r = platelets_below_threshold(_make_inputs(latest_platelets=80.0), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_no_platelets_advisory(self):
        r = platelets_below_threshold(_make_inputs(latest_platelets=None), PRECYCLE_CFG)
        assert r.status == 'advisory'

    def test_boundary_exactly(self):
        r = platelets_below_threshold(_make_inputs(latest_platelets=100.0), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_boundary_below(self):
        r = platelets_below_threshold(_make_inputs(latest_platelets=99.999), PRECYCLE_CFG)
        assert r.status == 'soft_block'


# ===========================================================================
# Rule 3: Labs stale
# ===========================================================================

class TestLabsStale:

    def test_pass_fresh(self):
        r = labs_stale(
            _make_inputs(latest_lab_draw_date=date(2026, 4, 30),
                         planned_admin_date=date(2026, 5, 1)),
            PRECYCLE_CFG,
        )
        assert r.status == 'pass'

    def test_advisory_stale(self):
        r = labs_stale(
            _make_inputs(latest_lab_draw_date=date(2026, 4, 25),
                         planned_admin_date=date(2026, 5, 1)),
            PRECYCLE_CFG,
        )
        assert r.status == 'advisory'

    def test_no_labs(self):
        r = labs_stale(_make_inputs(latest_lab_draw_date=None), PRECYCLE_CFG)
        assert r.status == 'advisory'

    def test_boundary_exactly_72h(self):
        r = labs_stale(
            _make_inputs(latest_lab_draw_date=date(2026, 4, 28),
                         planned_admin_date=date(2026, 5, 1)),
            PRECYCLE_CFG,
        )
        assert r.status == 'pass'

    def test_boundary_over_72h(self):
        r = labs_stale(
            _make_inputs(latest_lab_draw_date=date(2026, 4, 27),
                         planned_admin_date=date(2026, 5, 1)),
            PRECYCLE_CFG,
        )
        assert r.status == 'advisory'


# ===========================================================================
# Rule 4: Active infection
# ===========================================================================

class TestActiveInfection:

    def test_pass_attested(self):
        r = active_infection(_make_inputs(nurse_attests_no_infection=True), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_soft_block_not_attested(self):
        r = active_infection(_make_inputs(nurse_attests_no_infection=False), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_pass_when_not_required(self):
        cfg = {**PRECYCLE_CFG, 'precycle': {
            **PRECYCLE_CFG['precycle'],
            'active_infection': {'require_nurse_attestation': False},
        }}
        r = active_infection(_make_inputs(nurse_attests_no_infection=False), cfg)
        assert r.status == 'pass'


# ===========================================================================
# Rule 5: Cumulative red
# ===========================================================================

class TestCumulativeRed:

    def test_pass_green(self):
        r = cumulative_red(_make_inputs(cumulative_status='green'), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_soft_block_red(self):
        r = cumulative_red(_make_inputs(cumulative_status='red'), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_t_phase_skipped(self):
        r = cumulative_red(_make_inputs(phase='T', cumulative_status='red'), PRECYCLE_CFG)
        assert r.status == 'pass'


# ===========================================================================
# Rule 6: Cumulative hard stop
# ===========================================================================

class TestCumulativeHardStop:

    def test_pass_green(self):
        r = cumulative_hard_stop(_make_inputs(cumulative_status='green'), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_hard_block(self):
        r = cumulative_hard_stop(_make_inputs(cumulative_status='hard_stop'), PRECYCLE_CFG)
        assert r.status == 'hard_block'

    def test_t_phase_skipped(self):
        r = cumulative_hard_stop(_make_inputs(phase='T', cumulative_status='hard_stop'), PRECYCLE_CFG)
        assert r.status == 'pass'


# ===========================================================================
# Rule 7: LVEF abnormal
# ===========================================================================

class TestLvefAbnormal:

    def test_pass_ok(self):
        r = lvef_abnormal(_make_inputs(lvef_status='ok'), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_soft_block_hold(self):
        r = lvef_abnormal(_make_inputs(lvef_status='hold', lvef_reason='Low EF'), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_t_phase_skipped(self):
        r = lvef_abnormal(_make_inputs(phase='T', lvef_status='hold'), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_no_assessments(self):
        r = lvef_abnormal(_make_inputs(lvef_status=None), PRECYCLE_CFG)
        assert r.status == 'pass'


# ===========================================================================
# Rule 8: Neuropathy
# ===========================================================================

class TestNeuropathyTAboveMax:

    def test_pass_ac_phase(self):
        r = neuropathy_t_above_max(
            _make_inputs(phase='AC', latest_neuropathy_grade=3), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_pass_within_threshold(self):
        r = neuropathy_t_above_max(
            _make_inputs(phase='T', latest_neuropathy_grade=1), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_soft_block_above_max(self):
        r = neuropathy_t_above_max(
            _make_inputs(phase='T', latest_neuropathy_grade=2), PRECYCLE_CFG)
        assert r.status == 'soft_block'

    def test_no_assessment_passes(self):
        r = neuropathy_t_above_max(
            _make_inputs(phase='T', latest_neuropathy_grade=None), PRECYCLE_CFG)
        assert r.status == 'pass'


# ===========================================================================
# Rule 9: Symptoms
# ===========================================================================

class TestSymptomsGrade3OrHigher:

    def test_pass_no_data(self):
        r = symptoms_grade_3_or_higher(
            _make_inputs(latest_symptom_grades=None), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_pass_all_low(self):
        r = symptoms_grade_3_or_higher(
            _make_inputs(latest_symptom_grades=[1, 2, 1]), PRECYCLE_CFG)
        assert r.status == 'pass'

    def test_advisory_grade_3(self):
        r = symptoms_grade_3_or_higher(
            _make_inputs(latest_symptom_grades=[1, 3, 2]), PRECYCLE_CFG)
        assert r.status == 'advisory'

    def test_advisory_grade_4(self):
        r = symptoms_grade_3_or_higher(
            _make_inputs(latest_symptom_grades=[4]), PRECYCLE_CFG)
        assert r.status == 'advisory'

    def test_empty_list_passes(self):
        r = symptoms_grade_3_or_higher(
            _make_inputs(latest_symptom_grades=[]), PRECYCLE_CFG)
        assert r.status == 'pass'


# ===========================================================================
# Aggregator
# ===========================================================================

class TestRunChecklist:

    def test_all_pass(self):
        inputs = _make_inputs()
        result = run_checklist(inputs, PRECYCLE_CFG)
        assert result.worst_status == 'pass'
        assert result.can_save_without_override is True
        assert len(result.rules) == 9

    def test_one_soft_block(self):
        inputs = _make_inputs(latest_anc=1.0)
        result = run_checklist(inputs, PRECYCLE_CFG)
        assert result.worst_status == 'soft_block'
        assert result.can_save_without_override is False

    def test_one_advisory(self):
        inputs = _make_inputs(latest_symptom_grades=[3])
        result = run_checklist(inputs, PRECYCLE_CFG)
        assert result.worst_status == 'advisory'
        assert result.can_save_without_override is True

    def test_hard_block_wins(self):
        inputs = _make_inputs(cumulative_status='hard_stop', latest_anc=1.0)
        result = run_checklist(inputs, PRECYCLE_CFG)
        assert result.worst_status == 'hard_block'
        assert result.can_save_without_override is False
