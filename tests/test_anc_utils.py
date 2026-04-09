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


# ── AC: Labels always present ─────────────────────────────────────────────────

def test_all_statuses_have_label():
    for anc in [2.0, 1.2, 0.7, 0.3]:
        result = get_anc_status(anc)
        assert 'label' in result
        assert len(result['label']) > 0

def test_boundary_1_49_is_mild():
    assert get_anc_status(1.49)['status'] == 'mild'

def test_boundary_just_above_1_5_is_normal():
    assert get_anc_status(1.51)['status'] == 'normal'

def test_boundary_exactly_0_5_is_moderate():
    assert get_anc_status(0.5)['status'] == 'moderate'

# ── AC: Color consistency — panel and chart use same constants ────────────────

def test_color_constants_importable():
    from utils.anc_utils import ANC_THRESHOLD_MILD, ANC_THRESHOLD_MODERATE, ANC_THRESHOLD_SEVERE
    assert ANC_THRESHOLD_MILD     == 1.5
    assert ANC_THRESHOLD_MODERATE == 1.0
    assert ANC_THRESHOLD_SEVERE   == 0.5

def test_panel_and_chart_use_same_anc_status_function():
    """Both components import get_anc_status from utils.anc_utils — single source of truth."""
    from views.components.latest_labs_panel import LatestLabsPanel
    from views.components.anc_trend_chart import ANCTrendChart
    import inspect, utils.anc_utils as mod
    panel_src = inspect.getsource(LatestLabsPanel)
    chart_src  = inspect.getsource(ANCTrendChart)
    assert 'get_anc_status' in panel_src
    assert 'get_anc_status' in chart_src


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_anc_0_0_is_severe():
    assert get_anc_status(0.0)['status'] == 'severe'

def test_anc_0_01_is_severe():
    assert get_anc_status(0.01)['status'] == 'severe'

def test_anc_very_high_is_normal():
    result = get_anc_status(50.0)
    assert result['status'] == 'normal'
    assert result['color'] == '#4CAF50'

def test_all_statuses_return_dict_with_required_keys():
    for anc in [0.0, 0.3, 0.5, 0.7, 1.0, 1.2, 1.5, 2.0, 10.0]:
        result = get_anc_status(anc)
        assert set(result.keys()) == {'status', 'color', 'label'}
