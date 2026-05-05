"""Tests for views/components/dose_mod_history_panel.py (US-036)."""

import os
import sys
from datetime import date
import tkinter as tk

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Cycle, Patient
from services.patients import create_patient
from services.cycles import create_cycle


@pytest.fixture(scope='session')
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


@pytest.fixture
def patient(conn):
    return create_patient(conn, Patient(
        patient_id='PT-DMP1', name='Panel Patient',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
    ))


def _cycle(patient_id, cycle_number, dose_pct=100.0):
    from datetime import timedelta
    d = date(2026, 1, 1) + timedelta(days=(cycle_number - 1) * 14)
    return Cycle(
        patient_id=patient_id, cycle_number=cycle_number, phase='AC',
        actual_date=d, status='completed', dose_percent=dose_pct,
        dose_reason='Toxicity' if dose_pct < 100 else None,
    )


def test_panel_creates_without_error(tk_root, conn):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    assert panel is not None
    panel.destroy()


def test_panel_load_patient_no_crash(tk_root, conn, patient):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    panel.destroy()


def test_panel_collapsed_by_default(tk_root, conn, patient):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    assert panel._expanded is False
    panel.destroy()


def test_panel_toggle_expands(tk_root, conn, patient):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    panel._toggle()
    assert panel._expanded is True
    panel.destroy()


def test_panel_empty_state_shown(tk_root, conn, patient):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    panel._toggle()  # expand
    # Content frame children include empty-state label
    children = panel._content_frame.winfo_children()
    texts = [w.cget('text') for w in children if isinstance(w, tk.Label)]
    assert any('No dose modifications' in t for t in texts)
    panel.destroy()


def test_panel_shows_modifications(tk_root, conn, patient):
    create_cycle(conn, _cycle(patient.id, 1, 100.0))
    create_cycle(conn, _cycle(patient.id, 2, 75.0))

    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    panel._toggle()
    # Should render row data, not empty state
    children = panel._content_frame.winfo_children()
    texts = [w.cget('text') for w in children if isinstance(w, tk.Label)]
    assert not any('No dose modifications' in t for t in texts)
    panel.destroy()


def test_panel_sort_cycle(tk_root, conn, patient):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    panel._set_sort('cycle')
    assert panel._sort_by == 'cycle'
    panel.destroy()


def test_panel_sort_date(tk_root, conn, patient):
    from views.components.dose_mod_history_panel import DoseModHistoryPanel
    panel = DoseModHistoryPanel(tk_root, conn)
    panel.load_patient(patient.id)
    panel._set_sort('date')
    assert panel._sort_by == 'date'
    panel.destroy()
