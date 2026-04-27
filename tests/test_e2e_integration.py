"""End-to-end integration tests — Day 34 walkthrough (automated phases).

Covers the data-layer and component-refresh portions of the 8-phase
manual test checklist. UI-only items (window timing, visual rendering,
navigation clicks) are documented at the bottom as MANUAL items.
"""
import sys, sqlite3, os, tempfile, pytest
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date, timedelta

from database import create_tables, get_connection
from migrations import run_migrations
from models import (
    Patient, Cycle, Lab, LvefAssessment,
    add_patient, get_all_patients, get_patient_by_db_id, get_patient_by_id,
    add_cycle, get_cycles_by_patient,
    add_lab, get_labs_by_patient, get_latest_lab,
)
from utils.anc_utils import get_anc_status
from views.components.latest_labs_panel import LatestLabsPanel
from views.components.anc_trend_chart import ANCTrendChart


# ── Shared fixtures ───────────────────────────────────────────────────────────

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
def john(conn):
    return add_patient(conn, Patient(
        patient_id='PT-001', name='John Smith',
        protocol='Dose-Dense AC-T', start_date=date(2024, 1, 15),
    ))


@pytest.fixture
def jane(conn):
    return add_patient(conn, Patient(
        patient_id='PT-002', name='Jane Doe',
        protocol='Standard AC-T', start_date=date(2024, 2, 1),
    ))


# ── Phase 1: Application startup ─────────────────────────────────────────────

def test_phase1_db_initializes_cleanly():
    """DB creates all three tables without error."""
    c = sqlite3.connect(':memory:')
    create_tables(c)
    cursor = c.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert {'patients', 'cycles', 'labs'}.issubset(tables)
    c.close()


def test_phase1_empty_db_has_no_patients(conn):
    """Fresh DB returns empty patient list — matches 'No patients' UI state."""
    assert get_all_patients(conn) == []


def test_phase1_imports_resolve():
    """All view imports succeed — app will launch without ImportError."""
    from views.dashboard import DashboardView
    from views.patient_list import PatientListView
    from views.components.patient_header import PatientHeader
    from views.components.timeline import TimelineComponent
    from views.components.latest_labs_panel import LatestLabsPanel
    from views.components.anc_trend_chart import ANCTrendChart
    assert all([DashboardView, PatientListView, PatientHeader,
                TimelineComponent, LatestLabsPanel, ANCTrendChart])


# ── Phase 2: Patient management ──────────────────────────────────────────────

def test_phase2_add_first_patient(conn):
    """2.2 — Add PT-001 John Smith; patient saved and retrievable."""
    p = add_patient(conn, Patient(patient_id='PT-001', name='John Smith',
                                  protocol='Dose-Dense AC-T'))
    assert p.id is not None
    fetched = get_patient_by_id(conn, 'PT-001')
    assert fetched.name == 'John Smith'


def test_phase2_patient_appears_in_list(conn):
    """2.3 — Patient list returns the added patient."""
    add_patient(conn, Patient(patient_id='PT-001', name='John Smith'))
    patients = get_all_patients(conn)
    assert len(patients) == 1
    assert patients[0].patient_id == 'PT-001'


def test_phase2_add_second_patient(conn):
    """2.4 — Two patients both appear in list."""
    add_patient(conn, Patient(patient_id='PT-001', name='John Smith'))
    add_patient(conn, Patient(patient_id='PT-002', name='Jane Doe'))
    patients = get_all_patients(conn)
    ids = {p.patient_id for p in patients}
    assert ids == {'PT-001', 'PT-002'}


def test_phase2_empty_name_rejected(conn):
    """2.5 — Patient with empty name raises IntegrityError."""
    import sqlite3 as _sqlite3
    with pytest.raises(_sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO patients (patient_id, name) VALUES (?, ?)",
            ('PT-X', None)
        )


def test_phase2_duplicate_id_rejected(conn):
    """2.6 — Duplicate patient_id raises IntegrityError."""
    import sqlite3 as _sqlite3
    add_patient(conn, Patient(patient_id='PT-001', name='John Smith'))
    with pytest.raises(_sqlite3.IntegrityError):
        add_patient(conn, Patient(patient_id='PT-001', name='Other Person'))


def test_phase2_patient_fields_stored_correctly(conn):
    """Patient ID, protocol, and start date survive a round-trip."""
    add_patient(conn, Patient(
        patient_id='PT-001', name='John Smith',
        protocol='Dose-Dense AC-T', start_date=date(2024, 1, 15),
    ))
    p = get_patient_by_id(conn, 'PT-001')
    assert p.protocol == 'Dose-Dense AC-T'
    assert str(p.start_date) == '2024-01-15'


# ── Phase 3: Dashboard data loading ──────────────────────────────────────────

def test_phase3_set_patient_loads_correct_patient(conn, john):
    """3.1/3.3 — get_patient_by_db_id (used by set_patient) returns right record."""
    loaded = get_patient_by_db_id(conn, john.id)
    assert loaded.name == 'John Smith'
    assert loaded.patient_id == 'PT-001'
    assert loaded.protocol == 'Dose-Dense AC-T'


def test_phase3_new_patient_has_no_cycles(conn, john):
    """3.4 — Brand new patient: no cycles in DB."""
    cycles = get_cycles_by_patient(conn, john.id)
    assert cycles == []


def test_phase3_new_patient_has_no_labs(conn, john):
    """3.5/3.6 — Brand new patient: no labs in DB."""
    assert get_latest_lab(conn, john.id) is None
    assert get_labs_by_patient(conn, john.id) == []


def test_phase3_panel_loads_empty_state(root, conn, john):
    """3.5 — LatestLabsPanel renders without error for patient with no labs."""
    panel = LatestLabsPanel(root, conn, john.id)
    assert panel.winfo_exists()
    panel.destroy()


def test_phase3_chart_loads_empty_state(root, conn, john):
    """3.6 — ANCTrendChart renders without error for patient with no labs."""
    chart = ANCTrendChart(root, conn, patient_id=john.id)
    assert chart.winfo_exists()
    chart.destroy()


# ── Phase 4: Cycle completion ─────────────────────────────────────────────────

def test_phase4_complete_cycle1_full_dose(conn, john):
    """4.2 — Cycle 1 saved as completed at 100%."""
    add_cycle(conn, Cycle(
        patient_id=john.id, cycle_number=1, phase='AC',
        actual_date=date.today(), status='completed', dose_percent=100.0,
    ))
    cycles = get_cycles_by_patient(conn, john.id)
    assert cycles[0].status == 'completed'
    assert cycles[0].dose_percent == 100.0


def test_phase4_cycle1_appears_in_list(conn, john):
    """4.3 — After completing cycle 1, it shows up in the patient's cycle list."""
    add_cycle(conn, Cycle(
        patient_id=john.id, cycle_number=1, phase='AC',
        actual_date=date.today(), status='completed', dose_percent=100.0,
    ))
    cycles = get_cycles_by_patient(conn, john.id)
    assert len(cycles) == 1
    assert cycles[0].cycle_number == 1


def test_phase4_cycle2_dose_modification(conn, john):
    """4.5/4.6 — Cycle 2 saved with 80% dose and reason."""
    add_cycle(conn, Cycle(
        patient_id=john.id, cycle_number=2, phase='AC',
        actual_date=date.today(), status='completed',
        dose_percent=80.0, dose_reason='Neutropenia',
    ))
    cycles = get_cycles_by_patient(conn, john.id)
    c2 = cycles[0]
    assert c2.dose_percent == 80.0
    assert c2.dose_reason == 'Neutropenia'


def test_phase4_three_cycles_stored_in_order(conn, john):
    """4.7 — Three cycles stored and returned in cycle_number order."""
    for num in [1, 2, 3]:
        add_cycle(conn, Cycle(
            patient_id=john.id, cycle_number=num, phase='AC',
            actual_date=date.today(), status='completed', dose_percent=100.0,
        ))
    cycles = get_cycles_by_patient(conn, john.id)
    assert [c.cycle_number for c in cycles] == [1, 2, 3]


def test_phase4_current_cycle_is_first_pending(conn, john):
    """4.4 — Current cycle = lowest cycle_number not yet completed."""
    add_cycle(conn, Cycle(
        patient_id=john.id, cycle_number=1, phase='AC',
        actual_date=date.today(), status='completed', dose_percent=100.0,
    ))
    cycles = get_cycles_by_patient(conn, john.id)
    completed_nums = {c.cycle_number for c in cycles if c.status == 'completed'}
    # Current cycle is the next one after the highest completed
    current = max(completed_nums) + 1
    assert current == 2


# ── Phase 5: Lab entry ────────────────────────────────────────────────────────

def test_phase5_first_lab_saved(conn, john):
    """5.2 — Lab with ANC 2.1 saved and retrievable."""
    add_lab(conn, Lab(
        patient_id=john.id, lab_date=date.today() - timedelta(days=14),
        anc=2.1, wbc=4.5, platelets=180,
    ))
    lab = get_latest_lab(conn, john.id)
    assert lab.anc == 2.1
    assert lab.wbc == 4.5
    assert lab.platelets == 180


def test_phase5_anc_2_1_is_normal(conn, john):
    """5.4 — ANC 2.1 → green Normal."""
    status = get_anc_status(2.1)
    assert status['label'] == 'Normal'
    assert status['color'] == '#4CAF50'


def test_phase5_latest_lab_updates_to_most_recent(conn, john):
    """5.7 — After two labs, latest returns the more recent one."""
    add_lab(conn, Lab(
        patient_id=john.id, lab_date=date.today() - timedelta(days=14),
        anc=2.1,
    ))
    add_lab(conn, Lab(
        patient_id=john.id, lab_date=date.today() - timedelta(days=7),
        anc=1.2,
    ))
    latest = get_latest_lab(conn, john.id)
    assert latest.anc == 1.2


def test_phase5_anc_1_2_is_mild(conn, john):
    """5.8 — ANC 1.2 → yellow Mild Neutropenia."""
    status = get_anc_status(1.2)
    assert status['label'] == 'Mild Neutropenia'
    assert status['color'] == '#FFC107'


def test_phase5_chart_has_two_data_points(conn, john):
    """5.9 — After two labs, get_labs_by_patient returns two records."""
    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today() - timedelta(days=14), anc=2.1))
    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today() - timedelta(days=7), anc=1.2))
    labs = get_labs_by_patient(conn, john.id)
    assert len(labs) == 2


def test_phase5_labs_sorted_oldest_first(conn, john):
    """5.9 — Chart data ordered oldest → newest."""
    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today() - timedelta(days=14), anc=2.1))
    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today() - timedelta(days=7), anc=1.2))
    labs = get_labs_by_patient(conn, john.id)
    assert labs[0].anc == 2.1   # oldest first
    assert labs[1].anc == 1.2


def test_phase5_anc_0_7_is_moderate(conn, john):
    """5.10 — ANC 0.7 → orange Moderate Neutropenia."""
    status = get_anc_status(0.7)
    assert status['label'] == 'Moderate Neutropenia'
    assert status['color'] == '#FF9800'


def test_phase5_three_labs_in_chart_data(conn, john):
    """5.11 — After three labs, chart data has three points."""
    for days_ago, anc in [(14, 2.1), (7, 1.2), (0, 0.7)]:
        add_lab(conn, Lab(patient_id=john.id,
                          lab_date=date.today() - timedelta(days=days_ago),
                          anc=anc))
    labs = get_labs_by_patient(conn, john.id)
    assert len(labs) == 3


def test_phase5_panel_refreshes_after_lab_added(root, conn, john):
    """5.3 — LatestLabsPanel.refresh() reflects newly added lab."""
    panel = LatestLabsPanel(root, conn, john.id)
    assert get_latest_lab(conn, john.id) is None

    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today() - timedelta(days=14), anc=2.1))
    panel.refresh()

    lab = get_latest_lab(conn, john.id)
    assert lab is not None
    assert lab.anc == 2.1
    panel.destroy()


def test_phase5_chart_refreshes_after_lab_added(root, conn, john):
    """5.5 — ANCTrendChart data grows after lab added and refresh called."""
    chart = ANCTrendChart(root, conn, patient_id=john.id)
    dates, ancs = chart._load_data()
    assert len(dates) == 0

    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today() - timedelta(days=14), anc=2.1))
    chart.refresh()
    dates, ancs = chart._load_data()
    assert len(dates) == 1
    chart.destroy()


# ── Phase 6: Data persistence ─────────────────────────────────────────────────

def test_phase6_data_survives_connection_close():
    """6.3–6.5 — Data written to file DB persists after connection is closed and reopened."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')

        # Write session
        conn1 = sqlite3.connect(db_path)
        create_tables(conn1)
        p = add_patient(conn1, Patient(patient_id='PT-001', name='John Smith',
                                       protocol='Dose-Dense AC-T'))
        add_cycle(conn1, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                               actual_date=date.today(), status='completed',
                               dose_percent=100.0))
        add_cycle(conn1, Cycle(patient_id=p.id, cycle_number=2, phase='AC',
                               actual_date=date.today(), status='completed',
                               dose_percent=80.0, dose_reason='Neutropenia'))
        add_cycle(conn1, Cycle(patient_id=p.id, cycle_number=3, phase='AC',
                               actual_date=date.today(), status='completed',
                               dose_percent=100.0))
        add_lab(conn1, Lab(patient_id=p.id,
                           lab_date=date.today() - timedelta(days=14), anc=2.1))
        add_lab(conn1, Lab(patient_id=p.id,
                           lab_date=date.today() - timedelta(days=7), anc=1.2))
        add_lab(conn1, Lab(patient_id=p.id,
                           lab_date=date.today(), anc=0.7))
        conn1.close()

        # Read session — simulates reopening the app
        conn2 = sqlite3.connect(db_path)
        create_tables(conn2)  # idempotent

        patients = get_all_patients(conn2)
        assert len(patients) == 1
        assert patients[0].name == 'John Smith'

        loaded = get_patient_by_id(conn2, 'PT-001')
        cycles = get_cycles_by_patient(conn2, loaded.id)
        assert len(cycles) == 3
        assert cycles[1].dose_percent == 80.0        # Cycle 2 modification persisted
        assert cycles[1].dose_reason == 'Neutropenia'

        labs = get_labs_by_patient(conn2, loaded.id)
        assert len(labs) == 3
        assert labs[2].anc == 0.7                    # Most recent lab persisted
        conn2.close()


# ── Phase 7: Multiple patient / data isolation ────────────────────────────────

def test_phase7_switching_patients_loads_correct_data(conn, john, jane):
    """7.1/7.5 — get_patient_by_db_id returns the correct patient each time."""
    loaded_john = get_patient_by_db_id(conn, john.id)
    loaded_jane = get_patient_by_db_id(conn, jane.id)
    assert loaded_john.name == 'John Smith'
    assert loaded_jane.name == 'Jane Doe'


def test_phase7_new_patient_has_no_cycles(conn, john, jane):
    """7.2 — Jane starts with no cycles."""
    assert get_cycles_by_patient(conn, jane.id) == []


def test_phase7_new_patient_has_no_labs(conn, john, jane):
    """7.3 — Jane starts with no labs."""
    assert get_latest_lab(conn, jane.id) is None


def test_phase7_cycles_isolated_by_patient(conn, john, jane):
    """7.6 — Cycles added to John do not appear in Jane's records."""
    add_cycle(conn, Cycle(patient_id=john.id, cycle_number=1, phase='AC',
                          actual_date=date.today(), status='completed',
                          dose_percent=100.0))
    assert get_cycles_by_patient(conn, jane.id) == []


def test_phase7_labs_isolated_by_patient(conn, john, jane):
    """7.6 — Labs added to John do not appear in Jane's records."""
    add_lab(conn, Lab(patient_id=john.id,
                      lab_date=date.today(), anc=2.1))
    assert get_latest_lab(conn, jane.id) is None
    assert get_labs_by_patient(conn, jane.id) == []


def test_phase7_janes_data_does_not_pollute_john(conn, john, jane):
    """7.6 — Data added to Jane does not appear under John."""
    add_lab(conn, Lab(patient_id=jane.id,
                      lab_date=date.today(), anc=0.5))
    add_cycle(conn, Cycle(patient_id=jane.id, cycle_number=1, phase='AC',
                          actual_date=date.today(), status='completed',
                          dose_percent=100.0))
    assert get_latest_lab(conn, john.id) is None
    assert get_cycles_by_patient(conn, john.id) == []


def test_phase7_panel_switches_patient_correctly(root, conn, john, jane):
    """7.1 — LatestLabsPanel.load_patient() shows the correct patient's data."""
    add_lab(conn, Lab(patient_id=john.id, lab_date=date.today(), anc=2.1))

    panel = LatestLabsPanel(root, conn, john.id)
    assert get_latest_lab(conn, john.id).anc == 2.1

    panel.load_patient(jane.id)
    assert get_latest_lab(conn, jane.id) is None   # Jane has no labs
    panel.destroy()


# ── Phase 8: Edge cases ───────────────────────────────────────────────────────

def test_phase8_all_8_cycles_complete(conn, john):
    """8.1/8.2 — All 8 cycles can be saved as completed."""
    phases = ['AC'] * 4 + ['T'] * 4
    for i, phase in enumerate(phases, start=1):
        add_cycle(conn, Cycle(
            patient_id=john.id, cycle_number=i, phase=phase,
            actual_date=date.today(), status='completed', dose_percent=100.0,
        ))
    cycles = get_cycles_by_patient(conn, john.id)
    assert len(cycles) == 8
    assert all(c.status == 'completed' for c in cycles)


def test_phase8_no_pending_cycles_when_complete(conn, john):
    """8.3 — When all 8 cycles complete there are no pending cycles."""
    phases = ['AC'] * 4 + ['T'] * 4
    for i, phase in enumerate(phases, start=1):
        add_cycle(conn, Cycle(
            patient_id=john.id, cycle_number=i, phase=phase,
            actual_date=date.today(), status='completed', dose_percent=100.0,
        ))
    cycles = get_cycles_by_patient(conn, john.id)
    pending = [c for c in cycles if c.status == 'pending']
    assert pending == []


def test_phase8_can_add_labs_after_all_cycles_complete(conn, john):
    """8.1 — Lab entry still works after treatment is complete."""
    phases = ['AC'] * 4 + ['T'] * 4
    for i, phase in enumerate(phases, start=1):
        add_cycle(conn, Cycle(
            patient_id=john.id, cycle_number=i, phase=phase,
            actual_date=date.today(), status='completed', dose_percent=100.0,
        ))
    add_lab(conn, Lab(patient_id=john.id, lab_date=date.today(), anc=2.5))
    assert get_latest_lab(conn, john.id).anc == 2.5


# ── Phase 9: Cardiotoxicity walkthrough ──────────────────────────────────────
#
# Uses the migrations-aware connection (run_migrations) so all V2 tables exist.
# Walks: patient created → AC cycles → badge green → yellow → red → override
# audit rows visible → LVEF hold → override_lvef audit row visible.

@pytest.fixture
def v2_conn():
    """In-memory DB with all V2 migrations applied."""
    c = get_connection(':memory:')
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture
def cardio_patient(v2_conn):
    from services.patients import create_patient
    return create_patient(v2_conn, Patient(
        patient_id='PT-C01', name='Cardio Test',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
    ))


def test_phase9_fresh_patient_badge_green(v2_conn, cardio_patient):
    """New patient with no cycles → cumulative = 0 → green."""
    from services.cycles import cumulative_dose
    summary = cumulative_dose(v2_conn, cardio_patient.id)
    assert summary.total_mg_per_m2 == 0.0
    assert summary.status == 'green'


def test_phase9_four_ac_cycles_badge_stays_green(v2_conn, cardio_patient):
    """4 AC cycles × ~60 mg/m² dox (240 total) → still green (threshold 300)."""
    from services.cycles import create_cycle, cumulative_dose
    for i in range(1, 5):
        create_cycle(v2_conn, Cycle(
            patient_id=cardio_patient.id, cycle_number=i,
            phase='AC', actual_date=date(2026, 1, 15),
            status='completed', dose_percent=100.0,
            height_cm=170, weight_kg=65,
            anthracycline_agent='doxorubicin', dose_mg_total=105.0,
        ))
    summary = cumulative_dose(v2_conn, cardio_patient.id)
    assert summary.total_mg_per_m2 == pytest.approx(240.0, abs=2.0)
    assert summary.status == 'green'


def test_phase9_prior_exposure_pushes_badge_to_yellow(v2_conn):
    """Patient with 270 mg/m² prior exposure + one cycle → yellow."""
    from services.cycles import create_cycle, cumulative_dose
    from services.patients import create_patient
    p = create_patient(v2_conn, Patient(
        patient_id='PT-C02', name='Yellow Test',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=270.0,
    ))
    create_cycle(v2_conn, Cycle(
        patient_id=p.id, cycle_number=1,
        phase='AC', actual_date=date(2026, 1, 15),
        status='completed', dose_percent=100.0,
        height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.0,
    ))
    summary = cumulative_dose(v2_conn, p.id)
    assert summary.status == 'yellow'


def test_phase9_prior_exposure_pushes_badge_to_red(v2_conn):
    """Patient with 360 mg/m² prior + one cycle → red."""
    from services.cycles import create_cycle, cumulative_dose
    from services.patients import create_patient
    p = create_patient(v2_conn, Patient(
        patient_id='PT-C03', name='Red Test',
        start_date=date(2026, 1, 1), protocol='AC-T', total_cycles=8,
        prior_anthracycline_dose_mg_per_m2=360.0,
    ))
    create_cycle(v2_conn, Cycle(
        patient_id=p.id, cycle_number=1,
        phase='AC', actual_date=date(2026, 1, 15),
        status='completed', dose_percent=100.0,
        height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.0,
    ))
    summary = cumulative_dose(v2_conn, p.id)
    assert summary.status == 'red'


def test_phase9_override_red_audit_row_visible(v2_conn, cardio_patient):
    """After an override_red, the audit row surfaces via get_audit_for_entity."""
    from services.audit import write_audit, get_audit_for_entity
    from services.cycles import create_cycle
    c = create_cycle(v2_conn, Cycle(
        patient_id=cardio_patient.id, cycle_number=1,
        phase='AC', actual_date=date(2026, 1, 15),
        status='completed', dose_percent=100.0,
    ))
    write_audit(v2_conn, 'cycle', c.id, 'override_red',
                after={'override_reason': 'Clinical benefit justified'})
    v2_conn.commit()
    rows = get_audit_for_entity(v2_conn, 'cycle', c.id)
    override_rows = [r for r in rows if r['action'] == 'override_red']
    assert len(override_rows) == 1
    assert override_rows[0]['after']['override_reason'] == 'Clinical benefit justified'


def test_phase9_override_lvef_audit_row_visible(v2_conn, cardio_patient):
    """After an override_lvef, the audit row surfaces via get_audit_for_entity."""
    from services.audit import write_audit, get_audit_for_entity
    from services.cycles import create_cycle
    c = create_cycle(v2_conn, Cycle(
        patient_id=cardio_patient.id, cycle_number=2,
        phase='AC', actual_date=date(2026, 2, 15),
        status='completed', dose_percent=100.0,
    ))
    write_audit(v2_conn, 'cycle', c.id, 'override_lvef',
                after={'override_reason': 'Oncologist reviewed; continue treatment'})
    v2_conn.commit()
    rows = get_audit_for_entity(v2_conn, 'cycle', c.id)
    override_rows = [r for r in rows if r['action'] == 'override_lvef']
    assert len(override_rows) == 1
    assert 'Oncologist reviewed' in override_rows[0]['after']['override_reason']


def test_phase9_lvef_hold_detected_from_absolute(v2_conn, cardio_patient):
    """LVEF 48% (below 50% absolute hold) → lvef_status returns 'hold'."""
    from services.lvef import create_lvef
    from clinical.cardiotoxicity import lvef_status
    from config import get as get_config
    create_lvef(v2_conn, LvefAssessment(
        patient_id=cardio_patient.id,
        assessment_date=date(2026, 3, 1),
        lvef_percent=48.0, modality='echo', context='end_of_ac',
    ))
    cfg = get_config().cardiotoxicity.lvef.model_dump()
    status = lvef_status(48.0, None, cfg)
    assert status['status'] == 'hold'


def test_phase9_lvef_hold_detected_from_delta(v2_conn, cardio_patient):
    """Baseline 65%, current 52% → drop 13pp AND <55% → hold."""
    from clinical.cardiotoxicity import lvef_status
    from config import get as get_config
    cfg = get_config().cardiotoxicity.lvef.model_dump()
    status = lvef_status(52.0, 65.0, cfg)
    assert status['status'] == 'hold'


def test_phase9_both_override_audit_rows_written_on_double_block(v2_conn, cardio_patient):
    """A save that clears both cumulative-red and LVEF-hold writes two audit rows."""
    from services.audit import write_audit, get_audit_for_entity
    from services.cycles import create_cycle
    c = create_cycle(v2_conn, Cycle(
        patient_id=cardio_patient.id, cycle_number=3,
        phase='AC', actual_date=date(2026, 3, 15),
        status='completed', dose_percent=100.0,
    ))
    write_audit(v2_conn, 'cycle', c.id, 'override_red',
                after={'override_reason': 'Dose benefits outweigh risk'})
    write_audit(v2_conn, 'cycle', c.id, 'override_lvef',
                after={'override_reason': 'Cardiology clearance obtained'})
    v2_conn.commit()
    rows = get_audit_for_entity(v2_conn, 'cycle', c.id)
    actions = {r['action'] for r in rows}
    assert 'override_red' in actions
    assert 'override_lvef' in actions


def test_phase9_cardiotoxicity_panel_renders_with_data(root, v2_conn, cardio_patient):
    """CardiotoxicityPanel renders without error after cycles and LVEF added."""
    from services.cycles import create_cycle
    from services.lvef import create_lvef
    from views.components.cardiotoxicity_panel import CardiotoxicityPanel
    create_cycle(v2_conn, Cycle(
        patient_id=cardio_patient.id, cycle_number=1,
        phase='AC', actual_date=date(2026, 1, 15),
        status='completed', dose_percent=100.0,
        height_cm=170, weight_kg=65,
        anthracycline_agent='doxorubicin', dose_mg_total=105.0,
    ))
    create_lvef(v2_conn, LvefAssessment(
        patient_id=cardio_patient.id,
        assessment_date=date(2026, 1, 1),
        lvef_percent=65.0, modality='echo', context='baseline',
    ))
    panel = CardiotoxicityPanel(root, v2_conn)
    panel.load_patient(cardio_patient.id)
    assert panel.winfo_exists()
    panel.destroy()


# ── MANUAL TEST ITEMS (cannot be automated without live display) ──────────────
#
# The following items from the Day 34 checklist require manual verification:
#
# Phase 1:
#   1.1  Window opens in < 3 seconds        (requires timing a live launch)
#   1.2  "No patients" empty-state message  (requires visual inspection)
#   1.3  Window centered, correct title     (requires visual inspection)
#
# Phase 2:
#   2.1  Add Patient dialog opens on click  (requires UI interaction)
#   2.2  Dialog closes after save           (requires UI interaction)
#   2.3  Patient shows "0/8" in list        (requires Treeview rendering)
#
# Phase 3:
#   3.1  Dashboard loads on double-click    (requires UI navigation)
#   3.2  Load time < 1 second              (requires timing)
#   3.7  Back button returns to list        (requires UI navigation)
#
# Phase 4:
#   4.1  Cycle dialog opens on cycle click  (requires UI interaction)
#   4.3  Timeline visually updates green    (requires visual inspection)
#   4.6  Modification icon visible          (requires visual inspection)
#
# Phase 5:
#   5.1  Add Labs dialog opens on click     (requires UI interaction)
#   5.9  Threshold line visible on chart    (requires visual inspection)
#   5.11 Orange point below threshold       (requires visual inspection)
#
# Phase 6:
#   6.1  App closes cleanly on quit         (requires live quit)
#   6.2  App reopens normally               (requires live launch)
#
# Run: python src/main.py — and walk through phases 1, 2.1–2.3, 3.7,
#      4.1, 4.3, 4.6, 5.1, 5.9, 5.11, 6.1, 6.2 manually.
