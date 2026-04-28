"""Tests for src/clinical/neuropathy.py.

Covers effective_grade() and recommended_action() against a config fixture.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.neuropathy import effective_grade, recommended_action, NeuropathyAction


# ---------------------------------------------------------------------------
# Config fixture — mirrors the defaults YAML neuropathy section
# ---------------------------------------------------------------------------

NEURO_CFG = {
    'neuropathy': {
        'grade_actions': {
            0: {'dose_pct': 100, 'action': 'continue'},
            1: {'dose_pct': 100, 'action': 'continue'},
            2: {'dose_pct': 80,  'action': 'hold_one_cycle_then_resume'},
            3: {'dose_pct': 75,  'action': 'hold_until_recovered_then_resume_discontinue_on_recurrence'},
            4: {'dose_pct': 0,   'action': 'discontinue_permanently'},
        },
        'use_higher_grade_for_action': True,
    }
}


# ---------------------------------------------------------------------------
# effective_grade tests
# ---------------------------------------------------------------------------

class TestEffectiveGrade:
    def test_higher_wins_sensory(self):
        assert effective_grade(3, 1, NEURO_CFG) == 3

    def test_higher_wins_motor(self):
        assert effective_grade(1, 4, NEURO_CFG) == 4

    def test_equal_grades(self):
        assert effective_grade(2, 2, NEURO_CFG) == 2

    def test_both_zero(self):
        assert effective_grade(0, 0, NEURO_CFG) == 0

    def test_use_higher_false_returns_sensory(self):
        cfg = {
            'neuropathy': {
                **NEURO_CFG['neuropathy'],
                'use_higher_grade_for_action': False,
            }
        }
        assert effective_grade(1, 4, cfg) == 1

    def test_invalid_sensory_raises(self):
        with pytest.raises(ValueError):
            effective_grade(5, 1, NEURO_CFG)

    def test_invalid_motor_raises(self):
        with pytest.raises(ValueError):
            effective_grade(1, -1, NEURO_CFG)

    def test_non_int_raises(self):
        with pytest.raises(ValueError):
            effective_grade(2.0, 1, NEURO_CFG)  # type: ignore


# ---------------------------------------------------------------------------
# recommended_action tests
# ---------------------------------------------------------------------------

class TestRecommendedAction:
    def test_grade_0_continue(self):
        action = recommended_action(0, NEURO_CFG)
        assert action.dose_pct == 100
        assert action.action_code == 'continue'
        assert isinstance(action.advisory_text, str)

    def test_grade_1_continue(self):
        action = recommended_action(1, NEURO_CFG)
        assert action.dose_pct == 100
        assert action.action_code == 'continue'

    def test_grade_2_hold_and_resume(self):
        action = recommended_action(2, NEURO_CFG)
        assert action.dose_pct == 80
        assert action.action_code == 'hold_one_cycle_then_resume'
        assert '80%' in action.advisory_text

    def test_grade_3_hold_with_discontinue_on_recurrence(self):
        action = recommended_action(3, NEURO_CFG)
        assert action.dose_pct == 75
        assert '75%' in action.advisory_text

    def test_grade_4_discontinue(self):
        action = recommended_action(4, NEURO_CFG)
        assert action.dose_pct == 0
        assert action.action_code == 'discontinue_permanently'

    def test_returns_neuropathy_action_dataclass(self):
        result = recommended_action(0, NEURO_CFG)
        assert isinstance(result, NeuropathyAction)

    def test_grade_minus_one_raises(self):
        with pytest.raises(ValueError):
            recommended_action(-1, NEURO_CFG)

    def test_grade_5_raises(self):
        with pytest.raises(ValueError):
            recommended_action(5, NEURO_CFG)

    def test_grade_field_matches_input(self):
        for g in range(5):
            action = recommended_action(g, NEURO_CFG)
            assert action.grade == g
