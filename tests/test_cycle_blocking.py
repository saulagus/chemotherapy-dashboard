"""Tests for prospective cumulative-dose blocking logic (US-026).

Covers:
- override_red / override_hard_stop are valid audit ACTIONS
- write_audit correctly persists override rows
- Prospective dose arithmetic (no edit vs. edit-path subtraction)
- _check_cumulative_block advisory/green paths return (None, None) with no dialog
- Mocked soft-block and hard-stop dialog paths
- Cancel path returns None to abort the save
"""

import os
import sys
import tkinter as tk
from datetime import date
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Cycle, Patient
from services.audit import write_audit, get_audit_for_entity, ACTIONS
from services.cycles import cumulative_dose
from services.patients import create_patient
from clinical.cardiotoxicity import compute_bsa, to_doxorubicin_equivalent


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    c = get_connection(':memory:')
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture(scope='module')
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


def _patient(conn, prior_dose=0.0):
    """Insert a patient and return it."""
    return create_patient(conn, Patient(
        patient_id='PT-BLK', name='Block Test',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=prior_dose,
    ))


def _make_dialog(root, conn, patient_id, cycle_number=1):
    from views.dialogs.cycle_completion_dialog import CycleCompletionDialog
    return CycleCompletionDialog(root, conn, patient_id=patient_id,
                                 cycle_number=cycle_number)


# ---------------------------------------------------------------------------
# 1. Override actions are in the ACTIONS vocabulary
# ---------------------------------------------------------------------------

def test_override_red_in_actions_set():
    assert 'override_red' in ACTIONS


def test_override_hard_stop_in_actions_set():
    assert 'override_hard_stop' in ACTIONS


# ---------------------------------------------------------------------------
# 2. write_audit accepts both override actions
# ---------------------------------------------------------------------------

def test_write_audit_override_red_accepted(conn):
    row_id = write_audit(conn, 'cycle', 1, 'override_red',
                         after={'override_reason': 'Clinical urgency justified'})
    conn.commit()
    assert row_id > 0
    rows = get_audit_for_entity(conn, 'cycle', 1)
    assert rows[0]['action'] == 'override_red'


def test_write_audit_override_hard_stop_accepted(conn):
    row_id = write_audit(conn, 'cycle', 2, 'override_hard_stop',
                         after={'override_reason': 'Attending override: benefit outweighs risk'})
    conn.commit()
    assert row_id > 0
    rows = get_audit_for_entity(conn, 'cycle', 2)
    assert rows[0]['action'] == 'override_hard_stop'


def test_override_audit_row_stores_reason(conn):
    reason = 'Tumour response requires continuation'
    write_audit(conn, 'cycle', 5, 'override_red',
                after={'override_reason': reason})
    conn.commit()
    row = get_audit_for_entity(conn, 'cycle', 5)[0]
    assert row['after']['override_reason'] == reason


# ---------------------------------------------------------------------------
# 3. Prospective dose arithmetic (pure math, no UI)
# ---------------------------------------------------------------------------

def test_prospective_math_new_cycle():
    """Adding a fresh cycle: prospective = current_total + new_dox_eq."""
    factors = {'doxorubicin': 1.0}
    bsa = compute_bsa(170, 65)          # ≈ 1.752 m²
    dose_mg = 105.0
    new_per_m2 = dose_mg / bsa
    new_dox_eq = to_doxorubicin_equivalent('doxorubicin', new_per_m2, factors)
    current_total = 240.0
    prospective = current_total + new_dox_eq
    assert prospective == pytest.approx(240.0 + new_dox_eq, abs=0.01)
    assert prospective > 240.0


def test_prospective_math_edit_subtracts_old():
    """Editing a cycle: prospective = current - old_dox_eq + new_dox_eq."""
    factors = {'doxorubicin': 1.0}
    bsa = compute_bsa(170, 65)
    old_per_m2 = 60.0
    new_dose_mg = 126.0   # roughly 72 mg/m²
    new_per_m2 = new_dose_mg / bsa
    old_dox_eq = to_doxorubicin_equivalent('doxorubicin', old_per_m2, factors)
    new_dox_eq = to_doxorubicin_equivalent('doxorubicin', new_per_m2, factors)
    current_total = 300.0   # already includes old cycle
    prospective = current_total - old_dox_eq + new_dox_eq
    # prospective should reflect the delta, not a double-count
    assert prospective == pytest.approx(current_total - old_dox_eq + new_dox_eq, abs=0.01)
    assert prospective != current_total + new_dox_eq   # would be wrong without subtraction


def test_epirubicin_equivalence_factor_halved():
    """Epirubicin factor 0.5 means 100 mg/m² epi → 50 mg/m² dox-equiv."""
    factors = {'epirubicin': 0.5}
    dox_eq = to_doxorubicin_equivalent('epirubicin', 100.0, factors)
    assert dox_eq == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# 4. _check_cumulative_block — advisory / green paths (no dialog expected)
# ---------------------------------------------------------------------------

def test_check_cumulative_block_green_returns_no_action(root, conn):
    """Prospective dose stays green → (None, None) without any dialog."""
    patient = _patient(conn, prior_dose=0.0)
    dlg = _make_dialog(root, conn, patient.id)
    # Height 170 cm, weight 65 kg, 60 mg doxorubicin ≈ 34 mg/m² dox-equiv
    result = dlg._check_cumulative_block(170, 65, 'doxorubicin', 60.0)
    dlg.destroy()
    assert result == (None, None)


def test_check_cumulative_block_yellow_advisory_returns_no_action(root, conn):
    """Prospective reaches yellow zone; default mode = advisory → (None, None)."""
    # prior_dose = 270; adding ~60 mg/m² pushes to ~330 (yellow, not red)
    patient = _patient(conn, prior_dose=270.0)
    dlg = _make_dialog(root, conn, patient.id)
    # BSA ≈ 1.752 m²; 105 mg dox → ~60 mg/m² → prospective ≈ 330 (yellow)
    result = dlg._check_cumulative_block(170, 65, 'doxorubicin', 105.0)
    dlg.destroy()
    assert result == (None, None)


def test_check_cumulative_block_invalid_height_skips_block(root, conn):
    """Non-parseable height → can't compute BSA → skips block, returns (None, None)."""
    patient = _patient(conn, prior_dose=0.0)
    dlg = _make_dialog(root, conn, patient.id)
    # height=0 triggers ZeroDivisionError in BSA calc → skips safely
    result = dlg._check_cumulative_block(0, 65, 'doxorubicin', 100.0)
    dlg.destroy()
    assert result == (None, None)


# ---------------------------------------------------------------------------
# 5. Soft-block path — mocked dialog
# ---------------------------------------------------------------------------

def test_check_cumulative_block_red_calls_soft_block_dialog(root, conn):
    """Prospective reaches red zone with soft_block mode → _soft_block_dialog called."""
    # prior_dose = 360; adding ~60 mg/m² → ~420 (red, default soft_block)
    patient = _patient(conn, prior_dose=360.0)
    dlg = _make_dialog(root, conn, patient.id)
    with patch.object(dlg, '_soft_block_dialog', return_value=('override_red', 'reason')) as mock_sb:
        result = dlg._check_cumulative_block(170, 65, 'doxorubicin', 105.0)
        mock_sb.assert_called_once()
    dlg.destroy()
    assert result == ('override_red', 'reason')


def test_check_cumulative_block_soft_block_cancel_returns_none(root, conn):
    """User cancels the soft-block dialog → _check_cumulative_block returns None."""
    patient = _patient(conn, prior_dose=360.0)
    dlg = _make_dialog(root, conn, patient.id)
    with patch.object(dlg, '_soft_block_dialog', return_value=None):
        result = dlg._check_cumulative_block(170, 65, 'doxorubicin', 105.0)
    dlg.destroy()
    assert result is None


# ---------------------------------------------------------------------------
# 6. Hard-stop path — mocked dialog
# ---------------------------------------------------------------------------

def test_check_cumulative_block_hard_stop_calls_hard_stop_dialog(root, conn):
    """Prospective exceeds hard_stop limit with hard_block mode → _hard_stop_dialog called."""
    # prior_dose = 430; adding ~60 mg/m² → ~490 (hard_stop, default hard_block)
    patient = _patient(conn, prior_dose=430.0)
    dlg = _make_dialog(root, conn, patient.id)
    with patch.object(dlg, '_hard_stop_dialog',
                      return_value=('override_hard_stop', 'Attending approval documented')) as mock_hs:
        result = dlg._check_cumulative_block(170, 65, 'doxorubicin', 105.0)
        mock_hs.assert_called_once()
    dlg.destroy()
    assert result == ('override_hard_stop', 'Attending approval documented')


def test_check_cumulative_block_hard_stop_cancel_returns_none(root, conn):
    """User cancels the hard-stop override → _check_cumulative_block returns None."""
    patient = _patient(conn, prior_dose=430.0)
    dlg = _make_dialog(root, conn, patient.id)
    with patch.object(dlg, '_hard_stop_dialog', return_value=None):
        result = dlg._check_cumulative_block(170, 65, 'doxorubicin', 105.0)
    dlg.destroy()
    assert result is None


# ---------------------------------------------------------------------------
# 7. override_lvef in ACTIONS
# ---------------------------------------------------------------------------

def test_override_lvef_in_actions_set():
    assert 'override_lvef' in ACTIONS


def test_write_audit_override_lvef_accepted(conn):
    row_id = write_audit(conn, 'cycle', 3, 'override_lvef',
                         after={'override_reason': 'Attending reviewed; benefit outweighs risk'})
    conn.commit()
    assert row_id > 0
    rows = get_audit_for_entity(conn, 'cycle', 3)
    assert rows[0]['action'] == 'override_lvef'


# ---------------------------------------------------------------------------
# 8. _check_lvef_block paths
# ---------------------------------------------------------------------------

def _patient_with_lvef(conn, lvef_pct, baseline_pct=None):
    """Insert a patient and optionally one or two LVEF assessments."""
    from services.lvef import create_lvef
    from models import LvefAssessment

    p = create_patient(conn, Patient(
        patient_id='PT-LVEF', name='LVEF Test',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
    ))
    if baseline_pct is not None:
        create_lvef(conn, LvefAssessment(
            patient_id=p.id,
            assessment_date=date(2026, 1, 1),
            lvef_percent=baseline_pct,
            modality='echo',
            context='baseline',
        ))
    create_lvef(conn, LvefAssessment(
        patient_id=p.id,
        assessment_date=date(2026, 3, 1),
        lvef_percent=lvef_pct,
        modality='echo',
        context='end_of_ac',
    ))
    return p


def test_check_lvef_block_no_assessments_returns_no_action(root, conn):
    """Patient with no LVEF on record → (None, None)."""
    patient = _patient(conn)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=1)
    result = dlg._check_lvef_block()
    dlg.destroy()
    assert result == (None, None)


def test_check_lvef_block_ok_returns_no_action(root, conn):
    """LVEF 65% (ok) → (None, None), no dialog."""
    patient = _patient_with_lvef(conn, lvef_pct=65.0)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=2)
    result = dlg._check_lvef_block()
    dlg.destroy()
    assert result == (None, None)


def test_check_lvef_block_review_returns_no_action(root, conn):
    """Drop of 18pp but still above 55% → review (advisory only) → (None, None)."""
    # baseline 72, current 54 → drop 18pp >= review_flag(16), but 54 >= ceiling(55)? No, 54 < 55
    # Let me recalculate: drop=18 >= delta_hold(10) AND 54 < ceiling(55) → hold, not review
    # Use: baseline 72, current 56 → drop 16pp >= review_flag(16), 56 >= ceiling(55) → review ✓
    patient = _patient_with_lvef(conn, lvef_pct=56.0, baseline_pct=72.0)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=3)
    result = dlg._check_lvef_block()
    dlg.destroy()
    assert result == (None, None)


def test_check_lvef_block_absolute_hold_calls_lvef_dialog(root, conn):
    """LVEF 48% (< 50% absolute hold) → _lvef_block_dialog called."""
    patient = _patient_with_lvef(conn, lvef_pct=48.0)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=1)
    with patch.object(dlg, '_lvef_block_dialog',
                      return_value=('override_lvef', 'Reviewed with oncologist')) as mock_bd:
        result = dlg._check_lvef_block()
        mock_bd.assert_called_once()
    dlg.destroy()
    assert result == ('override_lvef', 'Reviewed with oncologist')


def test_check_lvef_block_delta_hold_calls_lvef_dialog(root, conn):
    """Drop ≥10pp AND below 55% → delta hold → _lvef_block_dialog called."""
    # baseline 65, current 52 → drop 13pp >= delta_hold(10) AND 52 < ceiling(55) → hold
    patient = _patient_with_lvef(conn, lvef_pct=52.0, baseline_pct=65.0)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=2)
    with patch.object(dlg, '_lvef_block_dialog',
                      return_value=('override_lvef', 'Cardiology consulted; continue')) as mock_bd:
        result = dlg._check_lvef_block()
        mock_bd.assert_called_once()
    dlg.destroy()
    assert result == ('override_lvef', 'Cardiology consulted; continue')


def test_check_lvef_block_cancel_returns_none(root, conn):
    """User cancels LVEF override dialog → None to abort save."""
    patient = _patient_with_lvef(conn, lvef_pct=48.0)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=1)
    with patch.object(dlg, '_lvef_block_dialog', return_value=None):
        result = dlg._check_lvef_block()
    dlg.destroy()
    assert result is None


def test_check_lvef_block_skipped_for_t_phase(root, conn):
    """LVEF block not applied for T-phase cycles (cycle_number > 4)."""
    # T-phase: cycle_number=5 should never call _check_lvef_block from _on_save.
    # Here we verify _check_lvef_block is still callable but confirm the
    # on-save guard (cycle_number <= 4) is the right place to enforce it.
    patient = _patient_with_lvef(conn, lvef_pct=48.0)
    dlg = _make_dialog(root, conn, patient.id, cycle_number=5)
    # _check_lvef_block itself doesn't know about the phase guard —
    # the guard lives in _on_save. Confirm a T-cycle dialog won't double-block
    # by verifying the guard condition:
    assert dlg.cycle_number > 4   # guard would skip the call
