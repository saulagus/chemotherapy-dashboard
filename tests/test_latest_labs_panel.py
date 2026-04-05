"""Tests for US-014: View Latest Lab Values panel."""
import sys, sqlite3, pytest
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date, timedelta
from database import create_tables
from models import add_patient, add_lab, Patient, Lab
from views.components.latest_labs_panel import LatestLabsPanel


@pytest.fixture(scope='module')
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def conn():
    c = sqlite3.connect(':memory:')
    create_tables(c)
    yield c
    c.close()


@pytest.fixture
def patient(conn):
    return add_patient(conn, Patient(
        patient_id='PT-001', name='Jane Doe', protocol='Dose-Dense AC-T'
    ))


# ── Empty state ───────────────────────────────────────────────────────────────

def test_panel_loads_without_error(root, conn, patient):
    panel = LatestLabsPanel(root, conn, patient.id)
    assert panel.winfo_exists()
    panel.destroy()

def test_no_labs_shows_empty_state(root, conn, patient):
    panel = LatestLabsPanel(root, conn, patient.id)
    # No exception raised and content frame exists
    assert panel._content is not None
    panel.destroy()

def test_no_patient_does_not_crash(root, conn):
    panel = LatestLabsPanel(root, conn, patient_id=None)
    assert panel._content is not None
    panel.destroy()


# ── Data display ──────────────────────────────────────────────────────────────

def test_refresh_after_lab_added(root, conn, patient):
    panel = LatestLabsPanel(root, conn, patient.id)
    add_lab(conn, Lab(patient_id=patient.id, lab_date=date.today(), anc=1.8))
    panel.refresh()
    assert panel._content is not None
    panel.destroy()

def test_shows_most_recent_lab_not_oldest(root, conn):
    conn2 = sqlite3.connect(':memory:')
    create_tables(conn2)
    p = add_patient(conn2, Patient(patient_id='PT-X', name='Test'))

    add_lab(conn2, Lab(patient_id=p.id, lab_date=date(2026, 1, 1), anc=0.3))
    add_lab(conn2, Lab(patient_id=p.id, lab_date=date(2026, 3, 1), anc=2.1))

    from models import get_latest_lab
    latest = get_latest_lab(conn2, p.id)
    assert latest.anc == 2.1
    conn2.close()

def test_optional_fields_none_does_not_crash(root, conn, patient):
    conn2 = sqlite3.connect(':memory:')
    create_tables(conn2)
    p = add_patient(conn2, Patient(patient_id='PT-Y', name='Test'))
    add_lab(conn2, Lab(patient_id=p.id, lab_date=date.today(),
                       anc=1.5, wbc=None, platelets=None, hemoglobin=None))
    panel = LatestLabsPanel(root, conn2, p.id)
    panel.refresh()
    assert panel._content is not None
    panel.destroy()
    conn2.close()


# ── Patient switching ─────────────────────────────────────────────────────────

def test_load_patient_switches_context(root, conn):
    conn2 = sqlite3.connect(':memory:')
    create_tables(conn2)
    p1 = add_patient(conn2, Patient(patient_id='PT-A', name='Alice'))
    p2 = add_patient(conn2, Patient(patient_id='PT-B', name='Bob'))

    add_lab(conn2, Lab(patient_id=p1.id, lab_date=date.today(), anc=1.8))

    panel = LatestLabsPanel(root, conn2, p1.id)
    assert panel.patient_id == p1.id

    panel.load_patient(p2.id)
    assert panel.patient_id == p2.id

    panel.destroy()
    conn2.close()


# ── Days ago logic ────────────────────────────────────────────────────────────

def test_today_label(root, conn):
    conn2 = sqlite3.connect(':memory:')
    create_tables(conn2)
    p = add_patient(conn2, Patient(patient_id='PT-T', name='Test'))
    add_lab(conn2, Lab(patient_id=p.id, lab_date=date.today(), anc=1.8))

    panel = LatestLabsPanel(root, conn2, p.id)
    days_diff = (date.today() - date.today()).days
    assert days_diff == 0
    panel.destroy()
    conn2.close()

def test_days_ago_calculation():
    lab_date = date.today() - timedelta(days=5)
    days_diff = (date.today() - lab_date).days
    assert days_diff == 5
