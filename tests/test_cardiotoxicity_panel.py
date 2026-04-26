"""Tests for CardiotoxicityPanel — cumulative dose display and LVEF section."""
import sys
import pytest
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date

from database import get_connection
from migrations import run_migrations
from models import Cycle, LvefAssessment, Patient
from services.cycles import create_cycle, cumulative_dose
from services.lvef import create_lvef
from services.patients import create_patient
from views.components.cardiotoxicity_panel import CardiotoxicityPanel


@pytest.fixture(scope='module')
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def conn():
    c = get_connection(':memory:')
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture
def patient(conn):
    return create_patient(conn, Patient(
        patient_id='PT-001', name='Test Patient',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
    ))


def _dox_cycle(patient_id, cycle_number):
    """Helper: doxorubicin cycle producing ~60 mg/m² dose (170 cm, 65 kg)."""
    return Cycle(
        patient_id=patient_id, cycle_number=cycle_number,
        phase='AC', actual_date=date(2026, 1, cycle_number),
        status='completed', dose_percent=100.0,
        height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.12,
    )


# ── Load / basic rendering ────────────────────────────────────────────────────

def test_panel_loads_without_error(root, conn):
    panel = CardiotoxicityPanel(root, conn)
    assert panel.winfo_exists()
    panel.destroy()


def test_panel_no_patient_shows_content(root, conn):
    panel = CardiotoxicityPanel(root, conn)
    assert panel._content is not None
    panel.destroy()


def test_panel_with_patient_no_data(root, conn, patient):
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    assert panel._content is not None
    panel.destroy()


def test_panel_refresh_does_not_crash(root, conn, patient):
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    panel.refresh()
    assert panel._content is not None
    panel.destroy()


# ── Meter canvas ──────────────────────────────────────────────────────────────

def test_meter_canvas_exists_after_load(root, conn, patient):
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    assert panel._meter_canvas is not None
    panel.destroy()


def test_meter_canvas_none_before_load(root, conn):
    panel = CardiotoxicityPanel(root, conn)
    # No patient: _meter_canvas stays None (empty state branch skips cumulative)
    assert panel._meter_canvas is None
    panel.destroy()


# ── Cumulative dose display at each status ────────────────────────────────────

def test_panel_green_dose_renders(root, conn, patient):
    for i in range(1, 5):
        create_cycle(conn, _dox_cycle(patient.id, i))
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    summary = cumulative_dose(conn, patient.id)
    assert summary.status == 'green'
    assert panel._meter_canvas is not None
    panel.destroy()


def test_panel_yellow_dose_renders(root, conn):
    c = get_connection(':memory:')
    run_migrations(c)
    p = create_patient(c, Patient(
        patient_id='PT-Y', name='Yellow',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=300.0,
    ))
    panel = CardiotoxicityPanel(root, c)
    panel.load_patient(p.id)
    summary = cumulative_dose(c, p.id)
    assert summary.status == 'yellow'
    assert panel._meter_canvas is not None
    panel.destroy()
    c.close()


def test_panel_red_dose_renders(root, conn):
    c = get_connection(':memory:')
    run_migrations(c)
    p = create_patient(c, Patient(
        patient_id='PT-R', name='Red',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=400.0,
    ))
    panel = CardiotoxicityPanel(root, c)
    panel.load_patient(p.id)
    summary = cumulative_dose(c, p.id)
    assert summary.status == 'red'
    assert panel._meter_canvas is not None
    panel.destroy()
    c.close()


def test_panel_hard_stop_dose_renders(root, conn):
    c = get_connection(':memory:')
    run_migrations(c)
    p = create_patient(c, Patient(
        patient_id='PT-HS', name='HardStop',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=450.0,
    ))
    panel = CardiotoxicityPanel(root, c)
    panel.load_patient(p.id)
    summary = cumulative_dose(c, p.id)
    assert summary.status == 'hard_stop'
    assert panel._meter_canvas is not None
    panel.destroy()
    c.close()


# ── LVEF section still renders alongside cumulative ───────────────────────────

def test_panel_with_lvef_and_dose_renders(root, conn, patient):
    create_lvef(conn, LvefAssessment(
        patient_id=patient.id,
        assessment_date=date(2026, 1, 10),
        lvef_percent=62.0,
        modality='echo',
        context='baseline',
    ))
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    assert panel._meter_canvas is not None
    panel.destroy()


# ── _draw_meter pure logic ────────────────────────────────────────────────────

def test_draw_meter_zero_width_does_not_crash(root, conn, patient):
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    canvas = panel._meter_canvas
    # Calling with width=0 or 1 should be a silent no-op
    panel._draw_meter(canvas, 0, 100.0, 'green',
                      type('T', (), {'yellow': 300.0, 'red': 400.0, 'hard_stop': 450.0})())
    panel._draw_meter(canvas, 1, 100.0, 'green',
                      type('T', (), {'yellow': 300.0, 'red': 400.0, 'hard_stop': 450.0})())
    panel.destroy()


def test_draw_meter_full_width_all_statuses(root, conn, patient):
    panel = CardiotoxicityPanel(root, conn)
    panel.load_patient(patient.id)
    canvas = panel._meter_canvas
    thresholds = type('T', (), {'yellow': 300.0, 'red': 400.0, 'hard_stop': 450.0})()
    for status, total in [('green', 200.0), ('yellow', 320.0),
                           ('red', 420.0), ('hard_stop', 460.0)]:
        panel._draw_meter(canvas, 400, total, status, thresholds)
    panel.destroy()
