"""Tests for CycleCompletionDialog.validate().

Each test sets field values directly on the dialog's StringVars
and calls validate() — no UI interaction needed.

Run with:
    pytest tests/test_dialog_validation.py -v
"""

import sys, os, sqlite3
import tkinter as tk
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from views.dialogs.cycle_completion_dialog import CycleCompletionDialog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn():
    conn = sqlite3.connect(':memory:')
    conn.executescript('''
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT, name TEXT, age INTEGER,
            diagnosis_date TEXT, start_date TEXT,
            protocol TEXT, total_cycles INTEGER
        );
        CREATE TABLE cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER, cycle_number INTEGER, phase TEXT,
            planned_date TEXT, actual_date TEXT,
            status TEXT, dose_percent REAL, dose_reason TEXT, notes TEXT
        );
    ''')
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
