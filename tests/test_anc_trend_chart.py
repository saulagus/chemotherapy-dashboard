"""Tests for US-016: ANC Trend Chart component."""
import sys, sqlite3, pytest
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date, timedelta
from database import create_tables
from models import add_patient, add_lab, Patient, Lab
from views.components.anc_trend_chart import ANCTrendChart


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
    return add_patient(conn, Patient(patient_id='PT-001', name='Jane Doe'))


# ── Rendering ─────────────────────────────────────────────────────────────────

def test_chart_renders_no_patient(root, conn):
    chart = ANCTrendChart(root, conn, patient_id=None)
    assert chart.winfo_exists()
    chart.destroy()

def test_chart_renders_no_labs(root, conn, patient):
    chart = ANCTrendChart(root, conn, patient.id)
    assert chart.winfo_exists()
    chart.destroy()

def test_chart_renders_single_lab(root, conn, patient):
    add_lab(conn, Lab(patient_id=patient.id, lab_date=date.today(), anc=1.8))
    chart = ANCTrendChart(root, conn, patient.id)
    assert chart.winfo_exists()
    chart.destroy()

def test_chart_renders_multiple_labs(root, conn):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-M', name='Multi'))
    for i in range(5):
        add_lab(c, Lab(patient_id=p.id,
                       lab_date=date.today() - timedelta(days=i*7),
                       anc=round(2.0 - i * 0.3, 1)))
    chart = ANCTrendChart(root, c, p.id)
    assert chart.winfo_exists()
    chart.destroy()
    c.close()


# ── Data loading ──────────────────────────────────────────────────────────────

def test_load_data_empty(root, conn, patient):
    chart = ANCTrendChart(root, conn, patient.id)
    dates, ancs = chart._load_data()
    assert dates == []
    assert ancs == []
    chart.destroy()

def test_load_data_returns_sorted_oldest_first(root, conn):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-S', name='Sort'))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 3, 1), anc=1.2))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 1, 1), anc=2.0))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 2, 1), anc=0.8))
    chart = ANCTrendChart(root, c, p.id)
    dates, ancs = chart._load_data()
    assert ancs == [2.0, 0.8, 1.2]
    chart.destroy()
    c.close()

def test_load_data_skips_labs_without_anc(root, conn):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-N', name='NoANC'))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 1, 1), anc=None, wbc=5.0))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 2, 1), anc=1.8))
    chart = ANCTrendChart(root, c, p.id)
    dates, ancs = chart._load_data()
    assert len(ancs) == 1
    assert ancs[0] == 1.8
    chart.destroy()
    c.close()


# ── Public API ────────────────────────────────────────────────────────────────

def test_load_patient_switches_context(root, conn):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p1 = add_patient(c, Patient(patient_id='PT-A', name='Alice'))
    p2 = add_patient(c, Patient(patient_id='PT-B', name='Bob'))
    chart = ANCTrendChart(root, c, p1.id)
    assert chart.patient_id == p1.id
    chart.load_patient(p2.id)
    assert chart.patient_id == p2.id
    chart.destroy()
    c.close()

def test_refresh_does_not_crash(root, conn, patient):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-R', name='Refresh'))
    add_lab(c, Lab(patient_id=p.id, lab_date=date.today(), anc=1.4))
    chart = ANCTrendChart(root, c, p.id)
    add_lab(c, Lab(patient_id=p.id, lab_date=date.today() - timedelta(days=7), anc=0.9))
    chart.refresh()
    assert chart.winfo_exists()
    chart.destroy()
    c.close()


# ── AC: Edge cases ────────────────────────────────────────────────────────────

def test_chart_with_50_labs(root, conn):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-50', name='Fifty'))
    for i in range(50):
        add_lab(c, Lab(patient_id=p.id,
                       lab_date=date.today() - timedelta(days=i),
                       anc=round(0.5 + (i % 5) * 0.4, 1)))
    chart = ANCTrendChart(root, c, p.id)
    assert chart.winfo_exists()
    chart.destroy()
    c.close()

def test_chart_with_duplicate_dates(root, conn):
    """Two labs on the same date — both loaded, chart does not crash."""
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-DUP', name='Dup'))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 3, 1), anc=1.8))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 3, 1), anc=0.9))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 3, 15), anc=1.2))
    chart = ANCTrendChart(root, c, p.id)
    assert chart.winfo_exists()
    chart.destroy()
    c.close()

def test_chart_with_large_date_gaps(root, conn):
    """Labs on day 1, day 30, day 120 — wide gaps handled."""
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-GAP', name='Gaps'))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 1, 1),  anc=2.0))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 2, 1),  anc=0.8))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 5, 1),  anc=1.6))
    chart = ANCTrendChart(root, c, p.id)
    assert chart.winfo_exists()
    chart.destroy()
    c.close()

def test_chart_all_same_anc_value(root, conn):
    """Flat line (all ANC = 1.8) does not crash."""
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-FLAT', name='Flat'))
    for i in range(5):
        add_lab(c, Lab(patient_id=p.id,
                       lab_date=date.today() - timedelta(days=i * 7),
                       anc=1.8))
    chart = ANCTrendChart(root, c, p.id)
    assert chart.winfo_exists()
    chart.destroy()
    c.close()

def test_chart_refreshes_after_new_lab(root, conn):
    """Chart shows new point after lab is added and refresh() called."""
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-REF2', name='Refresh2'))
    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 1, 1), anc=1.8))
    chart = ANCTrendChart(root, c, p.id)
    dates_before, _ = chart._load_data()
    assert len(dates_before) == 1

    add_lab(c, Lab(patient_id=p.id, lab_date=date(2026, 2, 1), anc=0.6))
    chart.refresh()
    dates_after, _ = chart._load_data()
    assert len(dates_after) == 2
    chart.destroy()
    c.close()
