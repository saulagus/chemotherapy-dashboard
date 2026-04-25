"""Tests for src/clinical/cardiotoxicity.py pure functions.

Day 12: compute_bsa
Day 14: to_doxorubicin_equivalent, cumulative_doxorubicin_equivalent,
        cumulative_status, lvef_status
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.cardiotoxicity import compute_bsa


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
