"""Tests for src/clinical/symptoms.py (US-030).

Covers applicable_symptoms() and is_advisory() against a config fixture.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.symptoms import applicable_symptoms, is_advisory


# ---------------------------------------------------------------------------
# Config fixture — mirrors defaults YAML symptoms section
# ---------------------------------------------------------------------------

SYM_CFG = {
    'symptoms': {
        'set_all_phases': ['nausea', 'fatigue', 'mucositis', 'constipation'],
        'set_t_phase_additional': ['arthralgia', 'peripheral_edema'],
        'advisory_grade': 3,
    }
}


class TestApplicableSymptoms:
    def test_ac_phase_returns_base_set(self):
        syms = applicable_symptoms('AC', SYM_CFG)
        assert syms == ['nausea', 'fatigue', 'mucositis', 'constipation']

    def test_t_phase_includes_additional(self):
        syms = applicable_symptoms('T', SYM_CFG)
        assert 'arthralgia' in syms
        assert 'peripheral_edema' in syms

    def test_t_phase_preserves_base_set(self):
        syms = applicable_symptoms('T', SYM_CFG)
        for s in ['nausea', 'fatigue', 'mucositis', 'constipation']:
            assert s in syms

    def test_t_phase_has_6_symptoms(self):
        syms = applicable_symptoms('T', SYM_CFG)
        assert len(syms) == 6

    def test_ac_phase_has_4_symptoms(self):
        syms = applicable_symptoms('AC', SYM_CFG)
        assert len(syms) == 4

    def test_case_insensitive_ac(self):
        syms_lower = applicable_symptoms('ac', SYM_CFG)
        syms_upper = applicable_symptoms('AC', SYM_CFG)
        assert syms_lower == syms_upper

    def test_case_insensitive_t(self):
        syms_lower = applicable_symptoms('t', SYM_CFG)
        syms_upper = applicable_symptoms('T', SYM_CFG)
        assert syms_lower == syms_upper

    def test_no_hardcoded_symptom_names_in_base_list(self):
        """Symptom names must come from config, not be hardcoded."""
        custom_cfg = {
            'symptoms': {
                'set_all_phases': ['custom_symptom_1'],
                'set_t_phase_additional': ['custom_symptom_2'],
                'advisory_grade': 3,
            }
        }
        syms = applicable_symptoms('T', custom_cfg)
        assert 'custom_symptom_1' in syms
        assert 'custom_symptom_2' in syms
        # Ensure no default names leaked in
        assert 'nausea' not in syms


class TestIsAdvisory:
    def test_grade_below_threshold_not_advisory(self):
        assert is_advisory(2, SYM_CFG) is False

    def test_grade_at_threshold_is_advisory(self):
        assert is_advisory(3, SYM_CFG) is True

    def test_grade_above_threshold_is_advisory(self):
        assert is_advisory(4, SYM_CFG) is True

    def test_grade_0_not_advisory(self):
        assert is_advisory(0, SYM_CFG) is False

    def test_custom_advisory_grade(self):
        cfg = {'symptoms': {'advisory_grade': 2}}
        assert is_advisory(2, cfg) is True
        assert is_advisory(1, cfg) is False
