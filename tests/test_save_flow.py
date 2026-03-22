"""Tests for CycleCompletionDialog save flow.

Verifies that _on_save() correctly writes to the database,
fires the on_save callback, and destroys the dialog on success.

Run with:
    pytest tests/test_save_flow.py -v
"""

import sys, os
import tkinter as tk
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection, create_tables
from models import Patient, Cycle, add_patient, add_cycle, get_cycles_by_patient
from views.dialogs.cycle_completion_dialog import CycleCompletionDialog

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def conn():
    """Fresh in-memory DB with schema and one patient per test."""
    c = get_connection(':memory:')
    create_tables(c)
    add_patient(c, Patient(
        patient_id='PT-001', name='Test Patient', age=50,
        start_date=date(2026, 1, 1), total_cycles=8,
    ))
    yield c
    c.close()


@pytest.fixture(autouse=True)
def cleanup(root):
    yield
    for w in root.winfo_children():
        if isinstance(w, tk.Toplevel):
            w.destroy()


def _patient_db_id(conn) -> int:
    return conn.execute('SELECT id FROM patients LIMIT 1').fetchone()[0]


def _make_dialog(root, conn, cycle_number=2, cycle=None, on_save=None):
    return CycleCompletionDialog(
        root, conn,
        patient_id=_patient_db_id(conn),
        cycle_number=cycle_number,
        cycle=cycle,
        on_save=on_save,
        start_date=date(2026, 1, 1),
    )


def _set_dose(dlg, selection, custom_value='', reason='Neutropenia', other_text=''):
    dlg.dose_var.set(selection)
    dlg.custom_dose_var.set(custom_value)
    dlg._on_dose_change()
    dlg.reason_var.set(reason)
    dlg.other_reason_var.set(other_text)
    dlg._on_reason_change()


# ---------------------------------------------------------------------------
# New cycle — insert path
# ---------------------------------------------------------------------------

def test_save_new_cycle_inserts_row(root, conn):
    """Saving a new cycle creates exactly one DB row for that cycle number."""
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')

    dlg._on_save()

    cycles = get_cycles_by_patient(conn, _patient_db_id(conn))
    assert len([c for c in cycles if c.cycle_number == 2]) == 1


def test_save_new_cycle_status_is_completed(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.status == 'completed'


def test_save_new_cycle_stores_correct_date(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.actual_date == date(2026, 3, 15)


def test_save_new_cycle_full_dose_no_reason(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.dose_percent == 100.0
    assert cycle.dose_reason is None


def test_save_new_cycle_reduced_dose_stores_reason(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=3)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '75%', reason='Neutropenia')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.dose_percent == 75.0
    assert cycle.dose_reason == 'Neutropenia'


def test_save_new_cycle_custom_dose(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=3)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, 'Custom', custom_value='80', reason='Neutropenia')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.dose_percent == 80.0


def test_dose_modification_80pct_neutropenia(root, conn):
    """Checklist: 80% dose + Neutropenia reason — verify both fields in DB."""
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, 'Custom', custom_value='80', reason='Neutropenia')
    dlg._on_save()

    # Query database directly to confirm both fields saved correctly.
    row = conn.execute(
        'SELECT status, dose_percent, dose_reason FROM cycles WHERE cycle_number = 2'
    ).fetchone()

    assert row is not None,              'Cycle row was not inserted'
    assert row[0] == 'completed',        f'Expected status=completed, got {row[0]}'
    assert row[1] == 80.0,               f'Expected dose_percent=80.0, got {row[1]}'
    assert row[2] == 'Neutropenia',      f'Expected dose_reason=Neutropenia, got {row[2]}'


def test_save_new_cycle_stores_notes(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')
    dlg.notes_text.insert('1.0', 'Tolerated well.')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.notes == 'Tolerated well.'


# ---------------------------------------------------------------------------
# Existing cycle — update path
# ---------------------------------------------------------------------------

@pytest.fixture
def existing_cycle(conn):
    pid = _patient_db_id(conn)
    return add_cycle(conn, Cycle(
        patient_id=pid, cycle_number=4, phase='AC',
        status='pending', dose_percent=100.0,
    ))


def test_save_updates_existing_cycle_status(root, conn, existing_cycle):
    dlg = _make_dialog(root, conn, cycle_number=4, cycle=existing_cycle)
    dlg.date_var.set('2026-03-20')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.status == 'completed'


def test_save_updates_existing_cycle_dose(root, conn, existing_cycle):
    dlg = _make_dialog(root, conn, cycle_number=4, cycle=existing_cycle)
    dlg.date_var.set('2026-03-20')
    _set_dose(dlg, '85%', reason='Neuropathy')
    dlg._on_save()

    cycle = get_cycles_by_patient(conn, _patient_db_id(conn))[0]
    assert cycle.dose_percent == 85.0
    assert cycle.dose_reason == 'Neuropathy'


def test_save_does_not_duplicate_row(root, conn, existing_cycle):
    """Saving an existing cycle must update, not insert a second row."""
    dlg = _make_dialog(root, conn, cycle_number=4, cycle=existing_cycle)
    dlg.date_var.set('2026-03-20')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    cycles = get_cycles_by_patient(conn, _patient_db_id(conn))
    assert len(cycles) == 1


# ---------------------------------------------------------------------------
# Dialog lifecycle
# ---------------------------------------------------------------------------

def test_dialog_closes_after_successful_save(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    assert not dlg.winfo_exists(), 'Dialog should be destroyed after a successful save'


def test_on_save_callback_fired(root, conn):
    fired = []
    dlg = _make_dialog(root, conn, cycle_number=2, on_save=lambda: fired.append(True))
    dlg.date_var.set('2026-03-15')
    _set_dose(dlg, '100% (Full dose)')
    dlg._on_save()

    assert fired == [True], 'on_save callback should fire exactly once'


def test_dialog_stays_open_on_invalid_data(root, conn):
    dlg = _make_dialog(root, conn, cycle_number=2)
    dlg.date_var.set('')   # Invalid — will fail validation
    # Patch messagebox to avoid a real dialog popping up during tests
    import unittest.mock as mock
    with mock.patch('views.dialogs.cycle_completion_dialog.messagebox'):
        dlg._on_save()

    assert dlg.winfo_exists(), 'Dialog should remain open when validation fails'
