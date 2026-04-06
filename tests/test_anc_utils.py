"""Tests for ANC threshold utility function."""
import sys
sys.path.insert(0, 'src')

from utils.anc_utils import get_anc_status


# ── Standard ranges ───────────────────────────────────────────────────────────

def test_normal_range():
    result = get_anc_status(2.0)
    assert result['status'] == 'normal'
    assert result['color']  == '#4CAF50'
    assert result['label']  == 'Normal'

def test_mild_neutropenia():
    result = get_anc_status(1.3)
    assert result['status'] == 'mild'
    assert result['color']  == '#FFC107'
    assert result['label']  == 'Mild Neutropenia'

def test_moderate_neutropenia():
    result = get_anc_status(0.8)
    assert result['status'] == 'moderate'
    assert result['color']  == '#FF9800'
    assert result['label']  == 'Moderate Neutropenia'

def test_severe_neutropenia():
    result = get_anc_status(0.3)
    assert result['status'] == 'severe'
    assert result['color']  == '#F44336'
    assert result['label']  == 'Severe Neutropenia'


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_edge_exactly_1_5():
    assert get_anc_status(1.5)['status'] == 'normal'

def test_edge_exactly_1_0():
    assert get_anc_status(1.0)['status'] == 'mild'

def test_edge_exactly_0_5():
    assert get_anc_status(0.5)['status'] == 'moderate'

def test_edge_just_below_0_5():
    assert get_anc_status(0.49)['status'] == 'severe'

def test_edge_zero():
    assert get_anc_status(0.0)['status'] == 'severe'
