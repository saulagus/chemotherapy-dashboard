"""Performance and remaining edge case tests — Day 35.

Performance targets from SPRINT_4_PLAN.md:
  - _load_data() with any dataset   < 100ms
  - chart refresh() with 20 labs    < 500ms
  - get_all_patients() 20 patients  < 100ms
  - get_latest_lab()                < 100ms
  - lab save + read round-trip      < 100ms

Edge cases not covered by earlier test files:
  - Patient name 50 characters
  - 20 patients in list
"""
import sys, sqlite3, time, pytest
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date, timedelta

from database import create_tables
from models import (
    Patient, Cycle, Lab,
    add_patient, get_all_patients, get_patient_by_id,
    add_cycle, get_cycles_by_patient,
    add_lab, get_labs_by_patient, get_latest_lab,
)
from views.components.anc_trend_chart import ANCTrendChart


# ── Fixtures ──────────────────────────────────────────────────────────────────

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
    return add_patient(conn, Patient(patient_id='PT-001', name='Test Patient'))


def _add_labs(conn, patient_id, n):
    """Add n sequential labs with ANC values alternating above/below threshold."""
    base = date.today() - timedelta(days=n)
    for i in range(n):
        anc = 2.0 if i % 2 == 0 else 0.8
        add_lab(conn, Lab(
            patient_id=patient_id,
            lab_date=base + timedelta(days=i),
            anc=anc,
        ))


# ── Edge cases: 50-char name ──────────────────────────────────────────────────

def test_edge_patient_name_50_chars_accepted(conn):
    """Patient name of exactly 50 characters is saved and retrieved correctly."""
    long_name = 'A' * 50
    p = add_patient(conn, Patient(patient_id='PT-LONG', name=long_name))
    fetched = get_patient_by_id(conn, 'PT-LONG')
    assert fetched.name == long_name
    assert len(fetched.name) == 50


def test_edge_patient_name_50_chars_in_list(conn):
    """50-char patient name appears correctly in get_all_patients()."""
    long_name = 'B' * 50
    add_patient(conn, Patient(patient_id='PT-LONG2', name=long_name))
    patients = get_all_patients(conn)
    names = [p.name for p in patients]
    assert long_name in names


# ── Edge cases: 20 patients ───────────────────────────────────────────────────

def test_edge_20_patients_all_stored(conn):
    """20 patients are all saved and returned by get_all_patients()."""
    for i in range(1, 21):
        add_patient(conn, Patient(
            patient_id=f'PT-{i:03d}',
            name=f'Patient {i:02d}',
            protocol='Dose-Dense AC-T',
        ))
    patients = get_all_patients(conn)
    assert len(patients) == 20


def test_edge_20_patients_ordered_by_name(conn):
    """get_all_patients() returns 20 patients in alphabetical order."""
    for i in range(1, 21):
        add_patient(conn, Patient(
            patient_id=f'PT-{i:03d}',
            name=f'Patient {i:02d}',
        ))
    patients = get_all_patients(conn)
    names = [p.name for p in patients]
    assert names == sorted(names)


# ── Performance: data layer ───────────────────────────────────────────────────

def test_perf_get_all_patients_20(conn):
    """get_all_patients() with 20 rows completes in < 100ms."""
    for i in range(1, 21):
        add_patient(conn, Patient(patient_id=f'PT-{i:03d}', name=f'Patient {i:02d}'))

    start = time.perf_counter()
    patients = get_all_patients(conn)
    elapsed = time.perf_counter() - start

    assert len(patients) == 20
    assert elapsed < 0.1, f"get_all_patients() took {elapsed:.3f}s — expected < 0.1s"


def test_perf_get_latest_lab(conn, patient):
    """get_latest_lab() completes in < 100ms."""
    _add_labs(conn, patient.id, 20)

    start = time.perf_counter()
    lab = get_latest_lab(conn, patient.id)
    elapsed = time.perf_counter() - start

    assert lab is not None
    assert elapsed < 0.1, f"get_latest_lab() took {elapsed:.3f}s — expected < 0.1s"


def test_perf_lab_save_and_read_roundtrip(conn, patient):
    """add_lab() + get_latest_lab() round-trip completes in < 100ms."""
    start = time.perf_counter()
    add_lab(conn, Lab(patient_id=patient.id, lab_date=date.today(), anc=1.8))
    lab = get_latest_lab(conn, patient.id)
    elapsed = time.perf_counter() - start

    assert lab.anc == 1.8
    assert elapsed < 0.1, f"Lab save+read took {elapsed:.3f}s — expected < 0.1s"


def test_perf_get_labs_by_patient_20(conn, patient):
    """get_labs_by_patient() with 20 rows completes in < 100ms."""
    _add_labs(conn, patient.id, 20)

    start = time.perf_counter()
    labs = get_labs_by_patient(conn, patient.id)
    elapsed = time.perf_counter() - start

    assert len(labs) == 20
    assert elapsed < 0.1, f"get_labs_by_patient(20) took {elapsed:.3f}s — expected < 0.1s"


def test_perf_get_cycles_by_patient(conn, patient):
    """get_cycles_by_patient() with 8 cycles completes in < 100ms."""
    phases = ['AC'] * 4 + ['T'] * 4
    for i, phase in enumerate(phases, start=1):
        add_cycle(conn, Cycle(
            patient_id=patient.id, cycle_number=i, phase=phase,
            actual_date=date.today(), status='completed', dose_percent=100.0,
        ))

    start = time.perf_counter()
    cycles = get_cycles_by_patient(conn, patient.id)
    elapsed = time.perf_counter() - start

    assert len(cycles) == 8
    assert elapsed < 0.1, f"get_cycles_by_patient() took {elapsed:.3f}s — expected < 0.1s"


# ── Performance: chart component ──────────────────────────────────────────────

def test_perf_chart_load_data_3_labs(root, conn, patient):
    """_load_data() with 3 labs completes in < 100ms."""
    _add_labs(conn, patient.id, 3)
    chart = ANCTrendChart(root, conn, patient_id=patient.id)

    start = time.perf_counter()
    dates, ancs = chart._load_data()
    elapsed = time.perf_counter() - start

    assert len(dates) == 3
    assert elapsed < 0.1, f"_load_data(3) took {elapsed:.3f}s — expected < 0.1s"
    chart.destroy()


def test_perf_chart_load_data_20_labs(root, conn, patient):
    """_load_data() with 20 labs completes in < 100ms."""
    _add_labs(conn, patient.id, 20)
    chart = ANCTrendChart(root, conn, patient_id=patient.id)

    start = time.perf_counter()
    dates, ancs = chart._load_data()
    elapsed = time.perf_counter() - start

    assert len(dates) == 20
    assert elapsed < 0.1, f"_load_data(20) took {elapsed:.3f}s — expected < 0.1s"
    chart.destroy()


def test_perf_chart_refresh_3_labs(root, conn, patient):
    """chart.refresh() with 3 labs completes in < 500ms."""
    _add_labs(conn, patient.id, 3)
    chart = ANCTrendChart(root, conn, patient_id=patient.id)

    start = time.perf_counter()
    chart.refresh()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"chart.refresh(3) took {elapsed:.3f}s — expected < 0.5s"
    chart.destroy()


def test_perf_chart_refresh_20_labs(root, conn, patient):
    """chart.refresh() with 20 labs completes in < 500ms."""
    _add_labs(conn, patient.id, 20)
    chart = ANCTrendChart(root, conn, patient_id=patient.id)

    start = time.perf_counter()
    chart.refresh()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"chart.refresh(20) took {elapsed:.3f}s — expected < 0.5s"
    chart.destroy()


def test_perf_labs_panel_refresh_after_add(conn, patient):
    """add_lab() + get_latest_lab() refresh cycle completes in < 500ms."""
    start = time.perf_counter()
    add_lab(conn, Lab(patient_id=patient.id, lab_date=date.today(), anc=1.5))
    _ = get_latest_lab(conn, patient.id)
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"Add lab + refresh took {elapsed:.3f}s — expected < 0.5s"
