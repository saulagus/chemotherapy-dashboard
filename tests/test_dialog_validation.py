"""Tests for CycleCompletionDialog.validate().

Each test sets field values directly on the dialog's StringVars
and calls validate() — no UI interaction needed.

Run with:
    pytest tests/test_dialog_validation.py -v
"""

import sys, os
import tkinter as tk
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from views.dialogs.cycle_completion_dialog import CycleCompletionDialog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn():
    conn = get_connection(':memory:')
    run_migrations(conn)
    return conn


def _make_dialog(root, conn, start_date=None):
    """Return a fresh dialog hidden off-screen."""
    return CycleCompletionDialog(
        root, conn, patient_id=1, cycle_number=3,
        start_date=start_date,
    )


def _set_dose(dlg, selection, custom_value='', reason='Neutropenia', other_text=''):
    """Set dose-related fields and trigger the show/hide logic."""
    dlg.dose_var.set(selection)
    dlg.custom_dose_var.set(custom_value)
    dlg._on_dose_change()
    dlg.reason_var.set(reason)
    dlg.other_reason_var.set(other_text)
    dlg._on_reason_change()


# ---------------------------------------------------------------------------
# Fixtures / setup
# ---------------------------------------------------------------------------

import pytest

@pytest.fixture(scope='module')
def root():
    r = tk.Tk()
    r.withdraw()   # Keep off-screen — no window appears during tests.
    yield r
    r.destroy()


@pytest.fixture(scope='module')
def conn():
    return _make_conn()


@pytest.fixture(autouse=True)
def cleanup(root):
    """Destroy any Toplevel dialogs created during a test."""
    yield
    for w in root.winfo_children():
        if isinstance(w, tk.Toplevel):
            w.destroy()


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------

def test_empty_date_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set('')
    errors = dlg.validate()
    assert any('date' in e.lower() for e in errors), errors


def test_invalid_date_format_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set('03/20/2026')   # MM/DD/YYYY — wrong format
    errors = dlg.validate()
    assert any('format' in e.lower() or 'invalid' in e.lower() for e in errors), errors


def test_future_date_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today() + timedelta(days=1)))
    errors = dlg.validate()
    assert any('future' in e.lower() for e in errors), errors


def test_date_before_start_returns_error(root, conn):
    start = date(2026, 1, 15)
    dlg = _make_dialog(root, conn, start_date=start)
    dlg.date_var.set('2026-01-10')   # 5 days before start
    errors = dlg.validate()
    assert any('start' in e.lower() for e in errors), errors


def test_today_date_is_valid(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    errors = dlg.validate()
    assert errors == [], errors


# ---------------------------------------------------------------------------
# Dose validation
# ---------------------------------------------------------------------------

def test_custom_dose_not_numeric_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='abc')
    errors = dlg.validate()
    assert any('number' in e.lower() or 'dose' in e.lower() for e in errors), errors


def test_custom_dose_zero_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='0')
    errors = dlg.validate()
    assert any('1 and 100' in e or 'dose' in e.lower() for e in errors), errors


def test_custom_dose_over_100_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='150')
    errors = dlg.validate()
    assert any('1 and 100' in e or 'dose' in e.lower() for e in errors), errors


def test_custom_dose_with_percent_symbol_is_valid(root, conn):
    """User types '80%' — the % should be stripped before parsing."""
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='80%', reason='Neutropenia')
    errors = dlg.validate()
    assert errors == [], errors


# ---------------------------------------------------------------------------
# Reason validation — the five checklist cases
# ---------------------------------------------------------------------------

def test_valid_full_dose_no_errors(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    errors = dlg.validate()
    assert errors == [], errors


def test_dose_80_no_reason_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    # 'Other' selected but text left blank → no reason provided.
    _set_dose(dlg, 'Custom', custom_value='80', reason='Other', other_text='')
    errors = dlg.validate()
    assert errors, 'Expected a reason error but got none'
    assert any('reason' in e.lower() or 'describe' in e.lower() for e in errors), errors


def test_dose_80_with_reason_no_errors(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='80', reason='Neutropenia')
    errors = dlg.validate()
    assert errors == [], errors


def test_dose_80_other_reason_with_text_no_errors(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='80', reason='Other',
              other_text='Severe fatigue')
    errors = dlg.validate()
    assert errors == [], errors


def test_custom_dose_100_does_not_require_reason(root, conn):
    """Custom=100 is functionally full dose — reason should not be required."""
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, 'Custom', custom_value='100', reason='')
    errors = dlg.validate()
    assert errors == [], errors


# ---------------------------------------------------------------------------
# Anthracycline Dosing field validation
# ---------------------------------------------------------------------------

def _set_dosing(dlg, height='', weight='', dose_mg=''):
    dlg.height_var.set(height)
    dlg.weight_var.set(weight)
    dlg.dose_mg_var.set(dose_mg)


def test_empty_dosing_fields_no_errors(root, conn):
    """All dosing fields optional — leaving them blank produces no errors."""
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg)
    assert dlg.validate() == []


def test_valid_height_weight_dose_no_errors(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, height='170', weight='65', dose_mg='105')
    assert dlg.validate() == []


def test_height_non_numeric_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, height='abc')
    errors = dlg.validate()
    assert any('height' in e.lower() for e in errors), errors


def test_height_below_range_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, height='30')
    errors = dlg.validate()
    assert any('height' in e.lower() for e in errors), errors


def test_height_above_range_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, height='350')
    errors = dlg.validate()
    assert any('height' in e.lower() for e in errors), errors


def test_weight_non_numeric_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, weight='heavy')
    errors = dlg.validate()
    assert any('weight' in e.lower() for e in errors), errors


def test_weight_zero_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, weight='0')
    errors = dlg.validate()
    assert any('weight' in e.lower() for e in errors), errors


def test_dose_mg_non_numeric_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, dose_mg='lots')
    errors = dlg.validate()
    assert any('dose' in e.lower() for e in errors), errors


def test_dose_mg_zero_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, dose_mg='0')
    errors = dlg.validate()
    assert any('dose' in e.lower() for e in errors), errors


def test_dose_mg_negative_returns_error(root, conn):
    dlg = _make_dialog(root, conn)
    dlg.date_var.set(str(date.today()))
    _set_dose(dlg, '100% (Full dose)')
    _set_dosing(dlg, dose_mg='-50')
    errors = dlg.validate()
    assert any('dose' in e.lower() for e in errors), errors


# ---------------------------------------------------------------------------
# Prior cycle prefill and weight-change warning
# ---------------------------------------------------------------------------

def test_prior_height_weight_prefilled(root):
    """Height and weight from the last cycle with measurements are prefilled."""
    from models import Patient, Cycle
    from services.patients import create_patient
    from services.cycles import create_cycle

    conn = _make_conn()
    p = create_patient(conn, Patient(
        patient_id='PT-001', name='Prefill Patient',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
    ))
    create_cycle(conn, Cycle(
        patient_id=p.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 15), status='completed',
        height_cm=170.0, weight_kg=68.0,
    ))
    dlg = CycleCompletionDialog(root, conn, patient_id=p.id, cycle_number=2)
    assert dlg.height_var.get() == '170'
    assert dlg.weight_var.get() == '68.0'
    dlg.destroy()
    conn.close()


def test_weight_change_warning_shown_when_over_threshold(root):
    """Warning label is populated when weight changes >10% from prior cycle."""
    from models import Patient, Cycle
    from services.patients import create_patient
    from services.cycles import create_cycle

    conn = _make_conn()
    p = create_patient(conn, Patient(
        patient_id='PT-002', name='Weight Patient',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
    ))
    create_cycle(conn, Cycle(
        patient_id=p.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 15), status='completed',
        height_cm=170.0, weight_kg=65.0,
    ))
    dlg = CycleCompletionDialog(root, conn, patient_id=p.id, cycle_number=2)
    # Set weight to 80 kg — 23% change from 65 kg → should show warning
    dlg.weight_var.set('80')
    dlg._check_weight_warning()
    assert '⚠' in dlg.weight_warning_label.cget('text')
    dlg.destroy()
    conn.close()


def test_weight_change_warning_hidden_when_under_threshold(root):
    """Warning label stays empty when weight is within threshold."""
    from models import Patient, Cycle
    from services.patients import create_patient
    from services.cycles import create_cycle

    conn = _make_conn()
    p = create_patient(conn, Patient(
        patient_id='PT-003', name='Stable Patient',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
    ))
    create_cycle(conn, Cycle(
        patient_id=p.id, cycle_number=1, phase='AC',
        actual_date=date(2026, 1, 15), status='completed',
        height_cm=170.0, weight_kg=65.0,
    ))
    dlg = CycleCompletionDialog(root, conn, patient_id=p.id, cycle_number=2)
    # Set weight to 66 kg — 1.5% change → no warning
    dlg.weight_var.set('66')
    dlg._check_weight_warning()
    assert dlg.weight_warning_label.cget('text') == ''
    dlg.destroy()
    conn.close()
