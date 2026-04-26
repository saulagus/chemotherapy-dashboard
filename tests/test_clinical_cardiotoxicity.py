"""Tests for src/clinical/cardiotoxicity.py pure functions.

Day 12: compute_bsa
Day 14: to_doxorubicin_equivalent, cumulative_doxorubicin_equivalent
Day 16: lvef_status
Day 17: cumulative_status
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.cardiotoxicity import (
    compute_bsa,
    cumulative_doxorubicin_equivalent,
    cumulative_status,
    lvef_status,
    to_doxorubicin_equivalent,
)

# Default equivalence factors matching institution.defaults.yaml
FACTORS = {
    'doxorubicin': 1.0,
    'epirubicin': 0.5,
    'daunorubicin': 0.5,
    'idarubicin': 5.0,
    'mitoxantrone': 4.0,
}


@dataclass
class _Cycle:
    """Minimal stand-in for a Cycle object — pure function only reads these two attrs."""
    anthracycline_agent: Optional[str] = None
    dose_mg_per_m2: Optional[float] = None


# ---------------------------------------------------------------------------
# compute_bsa — Mosteller
# ---------------------------------------------------------------------------

def test_compute_bsa_mosteller_reference_value():
    # 170 cm, 65 kg → sqrt(170*65/3600) = 1.7520 m²
    result = compute_bsa(170, 65, 'mosteller')
    assert result == pytest.approx(1.7520, abs=0.001)


def test_compute_bsa_mosteller_is_default():
    assert compute_bsa(170, 65) == pytest.approx(compute_bsa(170, 65, 'mosteller'))


def test_compute_bsa_mosteller_larger_patient():
    # 180 cm, 90 kg → sqrt(180*90/3600) = sqrt(4.5) = 2.121
    result = compute_bsa(180, 90, 'mosteller')
    assert result == pytest.approx(2.121, abs=0.001)


def test_compute_bsa_mosteller_small_patient():
    # 155 cm, 50 kg → sqrt(155*50/3600) = sqrt(2.1528) = 1.467
    result = compute_bsa(155, 50, 'mosteller')
    assert result == pytest.approx(1.467, abs=0.001)


# ---------------------------------------------------------------------------
# compute_bsa — DuBois
# ---------------------------------------------------------------------------

def test_compute_bsa_dubois_reference_value():
    # 170 cm, 65 kg → 0.007184 * 170^0.725 * 65^0.425 ≈ 1.754
    result = compute_bsa(170, 65, 'dubois')
    assert result == pytest.approx(1.754, abs=0.005)


def test_compute_bsa_dubois_larger_patient():
    result = compute_bsa(180, 90, 'dubois')
    # Both formulas should agree within 5% for normal adult range
    mosteller = compute_bsa(180, 90, 'mosteller')
    assert abs(result - mosteller) / mosteller < 0.05


def test_compute_bsa_dubois_small_patient():
    result = compute_bsa(155, 50, 'dubois')
    mosteller = compute_bsa(155, 50, 'mosteller')
    assert abs(result - mosteller) / mosteller < 0.05


# ---------------------------------------------------------------------------
# compute_bsa — returns a float > 0
# ---------------------------------------------------------------------------

def test_compute_bsa_returns_positive():
    assert compute_bsa(170, 65) > 0


def test_compute_bsa_result_in_plausible_range():
    # Human BSA is almost always between 1.2 and 2.5 m²
    for h, w in [(150, 40), (160, 55), (170, 70), (180, 85), (190, 100)]:
        bsa = compute_bsa(h, w)
        assert 1.2 <= bsa <= 2.5, f"BSA {bsa:.3f} out of range for {h}cm/{w}kg"


# ---------------------------------------------------------------------------
# compute_bsa — edge cases: invalid input
# ---------------------------------------------------------------------------

def test_compute_bsa_zero_height_raises():
    with pytest.raises(ValueError, match="height_cm"):
        compute_bsa(0, 65)


def test_compute_bsa_negative_height_raises():
    with pytest.raises(ValueError, match="height_cm"):
        compute_bsa(-10, 65)


def test_compute_bsa_zero_weight_raises():
    with pytest.raises(ValueError, match="weight_kg"):
        compute_bsa(170, 0)


def test_compute_bsa_negative_weight_raises():
    with pytest.raises(ValueError, match="weight_kg"):
        compute_bsa(170, -5)


def test_compute_bsa_unknown_formula_raises():
    with pytest.raises(ValueError, match="Unknown BSA formula"):
        compute_bsa(170, 65, 'invalid_formula')


# ===========================================================================
# to_doxorubicin_equivalent
# ===========================================================================

# ---------------------------------------------------------------------------
# Happy path — all five configured agents
# ---------------------------------------------------------------------------

def test_to_dox_eq_doxorubicin_factor_is_one():
    assert to_doxorubicin_equivalent('doxorubicin', 60.0, FACTORS) == 60.0


def test_to_dox_eq_epirubicin_factor_is_half():
    assert to_doxorubicin_equivalent('epirubicin', 60.0, FACTORS) == 30.0


def test_to_dox_eq_daunorubicin_factor_is_half():
    assert to_doxorubicin_equivalent('daunorubicin', 60.0, FACTORS) == 30.0


def test_to_dox_eq_idarubicin_factor_is_five():
    assert to_doxorubicin_equivalent('idarubicin', 10.0, FACTORS) == 50.0


def test_to_dox_eq_mitoxantrone_factor_is_four():
    assert to_doxorubicin_equivalent('mitoxantrone', 12.0, FACTORS) == 48.0


# ---------------------------------------------------------------------------
# Case-insensitive lookup
# ---------------------------------------------------------------------------

def test_to_dox_eq_uppercase_agent_ok():
    assert to_doxorubicin_equivalent('Doxorubicin', 60.0, FACTORS) == 60.0


def test_to_dox_eq_mixed_case_agent_ok():
    assert to_doxorubicin_equivalent('EPIRUBICIN', 60.0, FACTORS) == 30.0


# ---------------------------------------------------------------------------
# Zero dose
# ---------------------------------------------------------------------------

def test_to_dox_eq_zero_dose_returns_zero():
    assert to_doxorubicin_equivalent('doxorubicin', 0.0, FACTORS) == 0.0


# ---------------------------------------------------------------------------
# Unknown agent raises
# ---------------------------------------------------------------------------

def test_to_dox_eq_unknown_agent_raises():
    with pytest.raises(ValueError, match="Unknown agent"):
        to_doxorubicin_equivalent('cyclophosphamide', 60.0, FACTORS)


def test_to_dox_eq_empty_string_raises():
    with pytest.raises(ValueError):
        to_doxorubicin_equivalent('', 60.0, FACTORS)


# ===========================================================================
# cumulative_doxorubicin_equivalent
# ===========================================================================

# ---------------------------------------------------------------------------
# Empty / trivial cases
# ---------------------------------------------------------------------------

def test_cumulative_empty_cycle_list_returns_zero():
    assert cumulative_doxorubicin_equivalent([], FACTORS) == 0.0


def test_cumulative_empty_list_with_prior_returns_prior():
    assert cumulative_doxorubicin_equivalent([], FACTORS, prior_exposure_mg_per_m2=50.0) == 50.0


def test_cumulative_prior_none_treated_as_zero():
    assert cumulative_doxorubicin_equivalent([], FACTORS, prior_exposure_mg_per_m2=None) == 0.0


# ---------------------------------------------------------------------------
# Single-agent cumulation
# ---------------------------------------------------------------------------

def test_cumulative_single_dox_cycle():
    cycles = [_Cycle('doxorubicin', 60.0)]
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == 60.0


def test_cumulative_four_dox_cycles():
    cycles = [_Cycle('doxorubicin', 60.0)] * 4
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == 240.0


def test_cumulative_four_epi_cycles():
    # 4 cycles × 100 mg/m² epirubicin × 0.5 factor = 200 mg/m² dox-eq
    cycles = [_Cycle('epirubicin', 100.0)] * 4
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == 200.0


# ---------------------------------------------------------------------------
# Mixed agents
# ---------------------------------------------------------------------------

def test_cumulative_mixed_agents():
    # dox 60 + epi 80 (×0.5=40) = 100
    cycles = [_Cycle('doxorubicin', 60.0), _Cycle('epirubicin', 80.0)]
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == pytest.approx(100.0)


def test_cumulative_all_five_agents():
    cycles = [
        _Cycle('doxorubicin', 60.0),    # 60.0
        _Cycle('epirubicin', 60.0),     # 30.0
        _Cycle('daunorubicin', 60.0),   # 30.0
        _Cycle('idarubicin', 10.0),     # 50.0
        _Cycle('mitoxantrone', 12.0),   # 48.0
    ]
    expected = 60.0 + 30.0 + 30.0 + 50.0 + 48.0
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Prior exposure
# ---------------------------------------------------------------------------

def test_cumulative_adds_prior_exposure():
    cycles = [_Cycle('doxorubicin', 60.0)] * 4   # 240 mg/m²
    total = cumulative_doxorubicin_equivalent(cycles, FACTORS, prior_exposure_mg_per_m2=100.0)
    assert total == pytest.approx(340.0)


def test_cumulative_prior_only_no_cycles():
    total = cumulative_doxorubicin_equivalent([], FACTORS, prior_exposure_mg_per_m2=200.0)
    assert total == 200.0


# ---------------------------------------------------------------------------
# Cycles with missing data are skipped
# ---------------------------------------------------------------------------

def test_cumulative_skips_cycles_with_no_agent():
    cycles = [_Cycle('doxorubicin', 60.0), _Cycle(None, 60.0)]
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == 60.0


def test_cumulative_skips_cycles_with_no_dose():
    cycles = [_Cycle('doxorubicin', 60.0), _Cycle('doxorubicin', None)]
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == 60.0


def test_cumulative_skips_cycles_with_zero_dose():
    cycles = [_Cycle('doxorubicin', 60.0), _Cycle('doxorubicin', 0.0)]
    # 0.0 is falsy — skipped
    assert cumulative_doxorubicin_equivalent(cycles, FACTORS) == 60.0


def test_cumulative_all_missing_data_returns_prior():
    cycles = [_Cycle(None, None), _Cycle('doxorubicin', None)]
    total = cumulative_doxorubicin_equivalent(cycles, FACTORS, prior_exposure_mg_per_m2=75.0)
    assert total == 75.0


# ---------------------------------------------------------------------------
# Integration: 4 AC cycles × 60 mg/m² → 240 mg/m² (green threshold)
# ---------------------------------------------------------------------------

def test_cumulative_four_cycles_60_each_equals_240():
    """Sprint 6 acceptance criterion: 4 × 60 dox → 240 mg/m²."""
    cycles = [_Cycle('doxorubicin', 60.0)] * 4
    total = cumulative_doxorubicin_equivalent(cycles, FACTORS)
    assert total == pytest.approx(240.0)
    # 240 < yellow threshold of 300 → green
    assert total < 300.0


# ===========================================================================
# lvef_status
# ===========================================================================

LVEF_CFG = {
    'absolute_hold_pct': 50.0,
    'delta_hold_pct': 10.0,
    'delta_hold_absolute_ceiling_pct': 55.0,
    'review_flag_delta_pct': 16.0,
}


# ---------------------------------------------------------------------------
# ok — no baseline
# ---------------------------------------------------------------------------

def test_lvef_status_ok_no_baseline():
    result = lvef_status(62.0, None, LVEF_CFG)
    assert result['status'] == 'ok'
    assert result['reason'] == ''


def test_lvef_status_ok_above_absolute_no_baseline():
    result = lvef_status(50.1, None, LVEF_CFG)
    assert result['status'] == 'ok'


# ---------------------------------------------------------------------------
# hold — absolute threshold
# ---------------------------------------------------------------------------

def test_lvef_status_hold_absolute_below_threshold():
    result = lvef_status(49.9, None, LVEF_CFG)
    assert result['status'] == 'hold'
    assert '49.9' in result['reason']
    assert '50.0' in result['reason']


def test_lvef_status_hold_absolute_exactly_at_threshold():
    # current == absolute_hold_pct is NOT < threshold → ok (boundary)
    result = lvef_status(50.0, None, LVEF_CFG)
    assert result['status'] == 'ok'


def test_lvef_status_hold_absolute_with_baseline_ignored():
    # Absolute hold fires even with a healthy baseline
    result = lvef_status(48.0, 65.0, LVEF_CFG)
    assert result['status'] == 'hold'


# ---------------------------------------------------------------------------
# hold — delta threshold
# ---------------------------------------------------------------------------

def test_lvef_status_hold_delta_drop_10_below_ceiling():
    # drop=13, current=52 < 55 ceiling → hold
    result = lvef_status(52.0, 65.0, LVEF_CFG)
    assert result['status'] == 'hold'
    assert '13.0' in result['reason']


def test_lvef_status_hold_delta_exactly_10_drop_below_ceiling():
    # drop=10 (== delta_hold_pct) AND current=54 < 55 → hold
    result = lvef_status(54.0, 64.0, LVEF_CFG)
    assert result['status'] == 'hold'


def test_lvef_status_no_hold_when_current_at_or_above_ceiling():
    # drop=10 but current=55 == ceiling (not < 55) → no delta hold
    result = lvef_status(55.0, 65.0, LVEF_CFG)
    # delta=10 < review_flag_delta_pct(16) → ok
    assert result['status'] == 'ok'


def test_lvef_status_no_hold_when_drop_below_delta_threshold():
    # drop=9 < 10 → no hold
    result = lvef_status(56.0, 65.0, LVEF_CFG)
    assert result['status'] == 'ok'


# ---------------------------------------------------------------------------
# review
# ---------------------------------------------------------------------------

def test_lvef_status_review_drop_exactly_16():
    # drop=16, current=56 >= 55 ceiling → no delta hold; drop>=16 → review
    result = lvef_status(56.0, 72.0, LVEF_CFG)
    assert result['status'] == 'review'
    assert '16.0' in result['reason']


def test_lvef_status_review_drop_above_16_but_above_ceiling():
    # drop=20, current=58 >= 55 → no delta hold; drop>=16 → review
    result = lvef_status(58.0, 78.0, LVEF_CFG)
    assert result['status'] == 'review'


def test_lvef_status_no_review_drop_below_16():
    # drop=15, current=57 >= 55 → no hold, no review
    result = lvef_status(57.0, 72.0, LVEF_CFG)
    assert result['status'] == 'ok'


# ---------------------------------------------------------------------------
# ok — with baseline, small drop
# ---------------------------------------------------------------------------

def test_lvef_status_ok_small_drop_with_baseline():
    result = lvef_status(62.0, 65.0, LVEF_CFG)
    assert result['status'] == 'ok'
    assert result['reason'] == ''


def test_lvef_status_ok_lvef_improved_from_baseline():
    # current higher than baseline → delta negative → no hold/review
    result = lvef_status(68.0, 62.0, LVEF_CFG)
    assert result['status'] == 'ok'


# ---------------------------------------------------------------------------
# priority: absolute hold beats delta/review when both could apply
# ---------------------------------------------------------------------------

def test_lvef_status_absolute_hold_takes_priority_over_review():
    # drop=20 ≥16 → would be review, but current=48 < 50 → absolute hold wins
    result = lvef_status(48.0, 68.0, LVEF_CFG)
    assert result['status'] == 'hold'
    assert 'absolute' in result['reason'].lower()


# ===========================================================================
# cumulative_status
# ===========================================================================

THRESHOLDS = {'yellow': 300.0, 'red': 400.0, 'hard_stop': 450.0}


def test_cumulative_status_zero_is_green():
    assert cumulative_status(0.0, THRESHOLDS) == 'green'


def test_cumulative_status_below_yellow_is_green():
    assert cumulative_status(299.9, THRESHOLDS) == 'green'


def test_cumulative_status_exactly_at_yellow_is_yellow():
    assert cumulative_status(300.0, THRESHOLDS) == 'yellow'


def test_cumulative_status_between_yellow_and_red_is_yellow():
    assert cumulative_status(350.0, THRESHOLDS) == 'yellow'


def test_cumulative_status_exactly_at_red_is_red():
    assert cumulative_status(400.0, THRESHOLDS) == 'red'


def test_cumulative_status_between_red_and_hard_stop_is_red():
    assert cumulative_status(420.0, THRESHOLDS) == 'red'


def test_cumulative_status_exactly_at_hard_stop_is_hard_stop():
    assert cumulative_status(450.0, THRESHOLDS) == 'hard_stop'


def test_cumulative_status_above_hard_stop_is_hard_stop():
    assert cumulative_status(500.0, THRESHOLDS) == 'hard_stop'
