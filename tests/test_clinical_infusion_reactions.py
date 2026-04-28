"""Tests for src/clinical/infusion_reactions.py.

Covers rechallenge_advice() for grades 1–4 against a config fixture.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.infusion_reactions import rechallenge_advice, RechallengeAdvice


# ---------------------------------------------------------------------------
# Config fixture — mirrors the defaults YAML infusion_reactions section
# ---------------------------------------------------------------------------

REACTION_CFG = {
    'infusion_reactions': {
        'rechallenge_policy': {
            1: {'rechallenge': True,  'rate_pct': 50, 'premed_enhance': False,
                'switch_agent_to': None, 'hard_block': False},
            2: {'rechallenge': True,  'rate_pct': 50, 'premed_enhance': True,
                'switch_agent_to': None, 'hard_block': False},
            3: {'rechallenge': False, 'rate_pct': None, 'premed_enhance': False,
                'switch_agent_to': 'nab_paclitaxel_or_docetaxel', 'hard_block': False},
            4: {'rechallenge': False, 'rate_pct': None, 'premed_enhance': False,
                'switch_agent_to': 'nab_paclitaxel_or_docetaxel', 'hard_block': True},
        }
    }
}


class TestRechallengeAdvice:
    def test_grade_1_rechallenge_allowed(self):
        advice = rechallenge_advice(1, REACTION_CFG)
        assert advice.rechallenge is True
        assert advice.rate_pct == 50
        assert advice.premed_enhance is False
        assert advice.hard_block is False

    def test_grade_2_rechallenge_with_premed(self):
        advice = rechallenge_advice(2, REACTION_CFG)
        assert advice.rechallenge is True
        assert advice.rate_pct == 50
        assert advice.premed_enhance is True
        assert '50%' in advice.advisory_text
        assert 'premedication' in advice.advisory_text.lower()

    def test_grade_3_no_rechallenge(self):
        advice = rechallenge_advice(3, REACTION_CFG)
        assert advice.rechallenge is False
        assert advice.switch_agent_to == 'nab_paclitaxel_or_docetaxel'
        assert advice.hard_block is False
        assert 'do not rechallenge' in advice.advisory_text.lower()

    def test_grade_4_hard_block(self):
        advice = rechallenge_advice(4, REACTION_CFG)
        assert advice.rechallenge is False
        assert advice.hard_block is True
        assert 'hard block' in advice.advisory_text.lower()

    def test_returns_rechallenge_advice_dataclass(self):
        result = rechallenge_advice(1, REACTION_CFG)
        assert isinstance(result, RechallengeAdvice)

    def test_grade_field_matches_input(self):
        for g in range(1, 5):
            assert rechallenge_advice(g, REACTION_CFG).grade == g

    def test_grade_0_raises(self):
        with pytest.raises(ValueError):
            rechallenge_advice(0, REACTION_CFG)

    def test_grade_5_raises(self):
        with pytest.raises(ValueError):
            rechallenge_advice(5, REACTION_CFG)

    def test_non_int_raises(self):
        with pytest.raises(ValueError):
            rechallenge_advice(2.0, REACTION_CFG)  # type: ignore

    def test_grade_1_advisory_text_mentions_rate(self):
        advice = rechallenge_advice(1, REACTION_CFG)
        assert '50%' in advice.advisory_text

    def test_grade_3_advisory_mentions_switch_agent(self):
        advice = rechallenge_advice(3, REACTION_CFG)
        assert 'nab' in advice.advisory_text.lower() or 'docetaxel' in advice.advisory_text.lower()
