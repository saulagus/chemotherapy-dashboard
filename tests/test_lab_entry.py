"""Tests for US-013: Add Lab Values dialog validation and save flow."""
import sys, sqlite3, pytest
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date, timedelta
from database import create_tables
from models import add_patient, Patient, get_labs_by_patient
from views.dialogs.add_lab_dialog import AddLabDialog


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


@pytest.fixture
def dialog(root, conn, patient):
    d = AddLabDialog(root, conn, patient.id)
    yield d
    d.destroy()


# ── Date validation ───────────────────────────────────────────────────────────

def test_empty_date_returns_error(dialog):
    dialog.date_var.set('')
    dialog.anc_var.set('1.8')
    errors = dialog.validate()
    assert any('date is required' in e.lower() for e in errors)

def test_invalid_date_format_returns_error(dialog):
    dialog.date_var.set('15-03-2026')
    dialog.anc_var.set('1.8')
    errors = dialog.validate()
    assert any('invalid date' in e.lower() for e in errors)

def test_future_date_returns_error(dialog):
    future = str(date.today() + timedelta(days=1))
    dialog.date_var.set(future)
    dialog.anc_var.set('1.8')
    errors = dialog.validate()
    assert any('future' in e.lower() for e in errors)

def test_date_before_2000_returns_error(dialog):
    dialog.date_var.set('1999-12-31')
    dialog.anc_var.set('1.8')
    errors = dialog.validate()
    assert any('2000' in e for e in errors)

def test_today_date_is_valid(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    errors = dialog.validate()
    assert errors == []

def test_past_date_is_valid(dialog):
    dialog.date_var.set('2026-01-15')
    dialog.anc_var.set('1.8')
    errors = dialog.validate()
    assert errors == []


# ── ANC validation ────────────────────────────────────────────────────────────

def test_empty_anc_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('')
    errors = dialog.validate()
    assert any('anc is required' in e.lower() for e in errors)

def test_non_numeric_anc_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('abc')
    errors = dialog.validate()
    assert any('anc must be a number' in e.lower() for e in errors)

def test_negative_anc_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('-1.0')
    errors = dialog.validate()
    assert any('positive' in e.lower() for e in errors)

def test_zero_anc_is_valid(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('0.0')
    errors = dialog.validate()
    assert errors == []

def test_high_anc_is_valid(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('18.5')
    errors = dialog.validate()
    assert errors == []


# ── Optional fields validation ────────────────────────────────────────────────

def test_all_optional_empty_is_valid(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.wbc_var.set('')
    dialog.platelets_var.set('')
    dialog.hgb_var.set('')
    errors = dialog.validate()
    assert errors == []

def test_non_numeric_wbc_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.wbc_var.set('high')
    errors = dialog.validate()
    assert any('wbc' in e.lower() for e in errors)

def test_non_numeric_platelets_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.platelets_var.set('lots')
    errors = dialog.validate()
    assert any('platelet' in e.lower() for e in errors)

def test_non_numeric_hemoglobin_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.hgb_var.set('normal')
    errors = dialog.validate()
    assert any('hemoglobin' in e.lower() for e in errors)

def test_negative_optional_returns_error(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.wbc_var.set('-2.0')
    errors = dialog.validate()
    assert any('positive' in e.lower() for e in errors)

def test_all_fields_valid_no_errors(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.wbc_var.set('5.2')
    dialog.platelets_var.set('200')
    dialog.hgb_var.set('13.5')
    errors = dialog.validate()
    assert errors == []


# ── Range warnings ───────────────────────────────────────────────────────────

def test_high_anc_triggers_warning(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('25.0')
    warnings = dialog._get_warnings()
    assert any('ANC' in w for w in warnings)

def test_high_wbc_triggers_warning(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.wbc_var.set('60.0')
    warnings = dialog._get_warnings()
    assert any('WBC' in w for w in warnings)

def test_high_platelets_triggers_warning(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.platelets_var.set('1500')
    warnings = dialog._get_warnings()
    assert any('Platelets' in w for w in warnings)

def test_high_hemoglobin_triggers_warning(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.hgb_var.set('22.0')
    warnings = dialog._get_warnings()
    assert any('Hemoglobin' in w for w in warnings)

def test_normal_values_no_warnings(dialog):
    dialog.date_var.set(str(date.today()))
    dialog.anc_var.set('1.8')
    dialog.wbc_var.set('5.2')
    dialog.platelets_var.set('200')
    dialog.hgb_var.set('13.5')
    warnings = dialog._get_warnings()
    assert warnings == []

# ── Save flow ────────────────────────────────────────────────────────────────

def test_save_creates_lab_in_db(root, conn, patient):
    saved = []
    d = AddLabDialog(root, conn, patient.id, on_save=lambda: saved.append(True))
    d.date_var.set('2026-03-15')
    d.anc_var.set('1.8')
    d.wbc_var.set('5.2')
    d.platelets_var.set('200')
    d.hgb_var.set('13.5')
    d._on_save()

    labs = get_labs_by_patient(conn, patient.id)
    assert len(labs) == 1
    assert labs[0].anc == 1.8
    assert labs[0].wbc == 5.2
    assert labs[0].platelets == 200.0
    assert labs[0].hemoglobin == 13.5

def test_save_with_anc_only_stores_nones(root, conn, patient):
    d = AddLabDialog(root, conn, patient.id)
    d.date_var.set('2026-03-20')
    d.anc_var.set('0.4')
    d._on_save()

    labs = get_labs_by_patient(conn, patient.id)
    anc_only = next(l for l in labs if str(l.lab_date) == '2026-03-20')
    assert anc_only.anc == 0.4
    assert anc_only.wbc is None
    assert anc_only.platelets is None
    assert anc_only.hemoglobin is None

def test_on_save_callback_fired(root, conn, patient):
    fired = []
    d = AddLabDialog(root, conn, patient.id, on_save=lambda: fired.append(True))
    d.date_var.set('2026-03-25')
    d.anc_var.set('2.1')
    d._on_save()
    assert fired == [True]

def test_dialog_stays_open_on_invalid_data(root, conn, patient):
    d = AddLabDialog(root, conn, patient.id)
    d.date_var.set('')
    d.anc_var.set('')
    d._on_save()
    assert d.winfo_exists()
    d.destroy()


# ── AC: Multiple labs saved separately ───────────────────────────────────────

def test_multiple_labs_all_stored_separately(root, conn):
    c = sqlite3.connect(':memory:')
    create_tables(c)
    p = add_patient(c, Patient(patient_id='PT-MULTI', name='Multi'))

    dates_ancs = [('2026-01-10', '2.1'), ('2026-02-10', '1.2'), ('2026-03-10', '0.4')]
    for lab_date, anc in dates_ancs:
        d = AddLabDialog(root, c, p.id)
        d.date_var.set(lab_date)
        d.anc_var.set(anc)
        d._on_save()

    labs = get_labs_by_patient(c, p.id)
    assert len(labs) == 3
    saved_ancs = sorted(l.anc for l in labs)
    assert saved_ancs == [0.4, 1.2, 2.1]
    c.close()

def test_save_anc_50_triggers_warning(root, conn, patient):
    d = AddLabDialog(root, conn, patient.id)
    d.date_var.set(str(date.today()))
    d.anc_var.set('50.0')
    warnings = d._get_warnings()
    assert any('ANC' in w for w in warnings)
    d.destroy()

def test_error_label_shown_on_invalid_save(root, conn, patient):
    d = AddLabDialog(root, conn, patient.id)
    d.date_var.set('')
    d.anc_var.set('')
    d._on_save()
    assert d.error_label.cget('text') != ''
    d.destroy()
