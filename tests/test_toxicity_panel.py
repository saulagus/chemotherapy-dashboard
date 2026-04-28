"""Tests for src/views/components/toxicity_panel.py (US-027–030).

Covers:
  - panel instantiation (no patient, no crash)
  - load_patient switches context and triggers refresh
  - all four sections render without error when data is present
  - _open_add_symptoms shows info dialog when no completed cycles exist
  - _SymptomHistoryWindow renders without error
"""

import os
import sys
import tkinter as tk
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient
from services.patients import create_patient
from services.neuropathy import NeuropathyAssessment, create_neuropathy
from services.infusion_reactions import InfusionReaction, create_reaction
from services.gcsf import GcsfAdmin, create_gcsf
from services.symptoms import SymptomEntry, create_many


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
    c = get_connection(':memory:')
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture
def patient(conn):
    return create_patient(conn, Patient(
        patient_id='PT-001', name='Test Patient',
        protocol='AC-T', start_date=None,
    ))


@pytest.fixture
def cycle_id(conn, patient):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cycles (patient_id, cycle_number, status) VALUES (?, ?, ?)",
        (patient.id, 1, 'completed'),
    )
    conn.commit()
    return cursor.lastrowid


@pytest.fixture
def panel(root, conn):
    from views.components.toxicity_panel import ToxicityPanel
    p = ToxicityPanel(root, conn)
    yield p
    p.destroy()


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------

class TestToxicityPanelInstantiation:
    def test_panel_creates_without_error(self, root, conn):
        from views.components.toxicity_panel import ToxicityPanel
        p = ToxicityPanel(root, conn)
        assert p.winfo_exists()
        p.destroy()

    def test_panel_has_no_patient_initially(self, panel):
        assert panel.patient_str_id is None

    def test_panel_has_no_db_id_initially(self, panel):
        assert panel.patient_db_id is None


# ---------------------------------------------------------------------------
# load_patient
# ---------------------------------------------------------------------------

class TestLoadPatient:
    def test_load_patient_sets_str_id(self, panel, conn, patient):
        panel.load_patient(patient.id)
        assert panel.patient_str_id == 'PT-001'

    def test_load_patient_sets_db_id(self, panel, conn, patient):
        panel.load_patient(patient.id)
        assert panel.patient_db_id == patient.id

    def test_load_patient_triggers_refresh(self, panel, conn, patient):
        with mock.patch.object(panel, 'refresh') as mock_refresh:
            panel.load_patient(patient.id)
        mock_refresh.assert_called_once()


# ---------------------------------------------------------------------------
# Render — no data
# ---------------------------------------------------------------------------

class TestRenderNoData:
    def test_refresh_no_patient_no_error(self, panel):
        panel.refresh()  # patient_str_id is None

    def test_refresh_with_patient_no_records(self, panel, conn, patient):
        panel.load_patient(patient.id)
        # Should render all four empty sections without raising


# ---------------------------------------------------------------------------
# Render — with neuropathy data
# ---------------------------------------------------------------------------

class TestRenderNeuropathy:
    def test_renders_with_neuropathy(self, panel, conn, patient):
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id='PT-001',
            assessment_date='2026-04-01',
            sensory_grade=1,
            motor_grade=0,
        ))
        panel.load_patient(patient.id)  # no exception

    def test_renders_g4_neuropathy(self, panel, conn, patient):
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id='PT-001',
            assessment_date='2026-04-01',
            sensory_grade=4,
            motor_grade=3,
        ))
        panel.load_patient(patient.id)  # no exception


# ---------------------------------------------------------------------------
# Render — with infusion reaction data
# ---------------------------------------------------------------------------

class TestRenderReactions:
    def test_renders_with_reaction(self, panel, conn, patient, cycle_id):
        create_reaction(conn, InfusionReaction(
            patient_id='PT-001',
            cycle_id=cycle_id,
            agent='Paclitaxel',
            onset_min=15,
            severity_grade=2,
            response='Slowed infusion',
        ))
        panel.load_patient(patient.id)  # no exception

    def test_renders_g4_reaction_hard_block(self, panel, conn, patient, cycle_id):
        create_reaction(conn, InfusionReaction(
            patient_id='PT-001',
            cycle_id=cycle_id,
            agent='Paclitaxel',
            onset_min=5,
            severity_grade=4,
            response='Stopped infusion',
        ))
        panel.load_patient(patient.id)  # no exception


# ---------------------------------------------------------------------------
# Render — with G-CSF data
# ---------------------------------------------------------------------------

class TestRenderGcsf:
    def test_renders_with_gcsf(self, panel, conn, patient):
        create_gcsf(conn, GcsfAdmin(
            patient_id='PT-001',
            admin_date='2026-04-02',
            agent='filgrastim',
            prophylaxis_type='primary',
        ))
        panel.load_patient(patient.id)  # no exception


# ---------------------------------------------------------------------------
# Render — with symptom data
# ---------------------------------------------------------------------------

class TestRenderSymptoms:
    def test_renders_with_symptoms(self, panel, conn, patient, cycle_id):
        entries = [
            SymptomEntry(patient_id='PT-001', cycle_id=cycle_id,
                         entry_date='2026-04-01', symptom='nausea', grade=2),
            SymptomEntry(patient_id='PT-001', cycle_id=cycle_id,
                         entry_date='2026-04-01', symptom='fatigue', grade=1),
        ]
        create_many(conn, entries)
        panel.load_patient(patient.id)  # no exception

    def test_renders_advisory_symptom(self, panel, conn, patient, cycle_id):
        entries = [
            SymptomEntry(patient_id='PT-001', cycle_id=cycle_id,
                         entry_date='2026-04-01', symptom='mucositis', grade=3),
        ]
        create_many(conn, entries)
        panel.load_patient(patient.id)  # no exception — advisory glyph rendered


# ---------------------------------------------------------------------------
# _open_add_symptoms — no completed cycles
# ---------------------------------------------------------------------------

class TestOpenAddSymptoms:
    def test_shows_info_when_no_completed_cycles(self, panel, conn, patient):
        panel.load_patient(patient.id)
        # The cycles table is empty → should call messagebox.showinfo
        with mock.patch('views.components.toxicity_panel.messagebox') as mb:
            panel._open_add_symptoms()
        mb.showinfo.assert_called_once()

    def test_no_action_when_no_patient(self, panel):
        # panel has no patient loaded
        panel._open_add_symptoms()  # should return early with no error


# ---------------------------------------------------------------------------
# History windows
# ---------------------------------------------------------------------------

class TestHistoryWindows:
    def test_neuropathy_history_window_opens(self, root, conn, patient):
        create_neuropathy(conn, NeuropathyAssessment(
            patient_id='PT-001',
            assessment_date='2026-04-01',
            sensory_grade=2,
            motor_grade=1,
        ))
        from views.components.toxicity_panel import _NeuropathyHistoryWindow
        win = _NeuropathyHistoryWindow(root, conn, patient.id, 'PT-001')
        assert win.winfo_exists()
        win.destroy()

    def test_reaction_history_window_opens(self, root, conn, patient, cycle_id):
        create_reaction(conn, InfusionReaction(
            patient_id='PT-001',
            cycle_id=cycle_id,
            agent='Paclitaxel',
            onset_min=10,
            severity_grade=1,
            response='Observed',
        ))
        from views.components.toxicity_panel import _ReactionHistoryWindow
        win = _ReactionHistoryWindow(root, conn, patient.id, 'PT-001')
        assert win.winfo_exists()
        win.destroy()

    def test_gcsf_history_window_opens(self, root, conn, patient):
        create_gcsf(conn, GcsfAdmin(
            patient_id='PT-001',
            admin_date='2026-04-02',
            agent='filgrastim',
            prophylaxis_type='primary',
        ))
        from views.components.toxicity_panel import _GcsfHistoryWindow
        win = _GcsfHistoryWindow(root, conn, patient.id, 'PT-001')
        assert win.winfo_exists()
        win.destroy()

    def test_symptom_history_window_opens(self, root, conn, patient, cycle_id):
        create_many(conn, [
            SymptomEntry(patient_id='PT-001', cycle_id=cycle_id,
                         entry_date='2026-04-01', symptom='nausea', grade=1),
        ])
        from views.components.toxicity_panel import _SymptomHistoryWindow
        win = _SymptomHistoryWindow(root, conn, patient.id, 'PT-001')
        assert win.winfo_exists()
        win.destroy()

    def test_symptom_history_empty_state(self, root, conn, patient):
        from views.components.toxicity_panel import _SymptomHistoryWindow
        win = _SymptomHistoryWindow(root, conn, patient.id, 'PT-001')
        assert win.winfo_exists()
        win.destroy()

    def test_neuropathy_history_empty_state(self, root, conn, patient):
        from views.components.toxicity_panel import _NeuropathyHistoryWindow
        win = _NeuropathyHistoryWindow(root, conn, patient.id, 'PT-001')
        assert win.winfo_exists()
        win.destroy()
