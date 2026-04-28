"""Tests for src/services/gcsf.py (US-029).

Covers: create, update, soft-delete, list, list_for_cycle, latest,
        gcsf_dates_for_patient, audit trail.
"""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient
from services import audit as audit_module
from services.audit import get_audit_for_entity
from services.gcsf import (
    GcsfAdmin,
    create_gcsf,
    delete_gcsf,
    gcsf_dates_for_patient,
    latest_gcsf,
    list_gcsf,
    list_gcsf_for_cycle,
    update_gcsf,
)
from services.patients import create_patient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    yield connection
    connection.close()


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


def _make_gcsf(**kwargs) -> GcsfAdmin:
    defaults = dict(
        patient_id='PT-001',
        agent='pegfilgrastim',
        admin_date='2026-04-10',
    )
    defaults.update(kwargs)
    return GcsfAdmin(**defaults)


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------

class TestCreateGcsf:
    def test_create_returns_gcsf_with_id(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf())
        assert g.id is not None
        assert g.id > 0

    def test_create_persists_agent(self, conn, patient):
        create_gcsf(conn, _make_gcsf(agent='filgrastim'))
        assert list_gcsf(conn, 'PT-001')[0].agent == 'filgrastim'

    def test_create_persists_dose(self, conn, patient):
        create_gcsf(conn, _make_gcsf(dose_mg=6.0))
        assert list_gcsf(conn, 'PT-001')[0].dose_mg == 6.0

    def test_create_writes_audit_row(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf(), actor='nurse1')
        rows = get_audit_for_entity(conn, 'gcsf_admin', g.id)
        assert rows[0]['action'] == 'gcsf_created'
        assert rows[0]['actor'] == 'nurse1'

    def test_create_audit_action_in_actions_set(self):
        assert 'gcsf_created' in audit_module.ACTIONS

    def test_create_with_cycle_id(self, conn, patient, cycle_id):
        g = create_gcsf(conn, _make_gcsf(cycle_id=cycle_id))
        assert list_gcsf(conn, 'PT-001')[0].cycle_id == cycle_id


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------

class TestUpdateGcsf:
    def test_update_changes_agent(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf(agent='pegfilgrastim'))
        g.agent = 'filgrastim'
        update_gcsf(conn, g)
        assert list_gcsf(conn, 'PT-001')[0].agent == 'filgrastim'

    def test_update_writes_audit_row(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf())
        g.dose_mg = 10.0
        update_gcsf(conn, g, actor='nurse2')
        rows = get_audit_for_entity(conn, 'gcsf_admin', g.id)
        assert any(r['action'] == 'gcsf_updated' for r in rows)

    def test_update_without_id_raises(self, conn, patient):
        g = _make_gcsf()
        with pytest.raises(ValueError):
            update_gcsf(conn, g)

    def test_update_missing_id_raises_lookup(self, conn, patient):
        g = _make_gcsf()
        g.id = 9999
        with pytest.raises(LookupError):
            update_gcsf(conn, g)

    def test_update_audit_action_in_actions_set(self):
        assert 'gcsf_updated' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# Soft-delete tests
# ---------------------------------------------------------------------------

class TestDeleteGcsf:
    def test_delete_removes_from_list(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf())
        delete_gcsf(conn, g.id)
        assert list_gcsf(conn, 'PT-001') == []

    def test_delete_keeps_row_include_deleted(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf())
        delete_gcsf(conn, g.id)
        assert len(list_gcsf(conn, 'PT-001', include_deleted=True)) == 1

    def test_delete_writes_audit_row(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf())
        delete_gcsf(conn, g.id, actor='nurse3')
        rows = get_audit_for_entity(conn, 'gcsf_admin', g.id)
        assert any(r['action'] == 'gcsf_deleted' for r in rows)

    def test_delete_idempotent(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf())
        delete_gcsf(conn, g.id)
        delete_gcsf(conn, g.id)  # no-op
        assert list_gcsf(conn, 'PT-001', include_deleted=True)[0].deleted_at is not None

    def test_delete_missing_id_raises(self, conn, patient):
        with pytest.raises(LookupError):
            delete_gcsf(conn, 9999)

    def test_delete_audit_action_in_actions_set(self):
        assert 'gcsf_deleted' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# List + latest tests
# ---------------------------------------------------------------------------

class TestListGcsf:
    def test_list_empty(self, conn, patient):
        assert list_gcsf(conn, 'PT-001') == []

    def test_list_for_cycle_empty(self, conn, patient, cycle_id):
        assert list_gcsf_for_cycle(conn, cycle_id) == []

    def test_list_for_cycle_filters_correctly(self, conn, patient, cycle_id):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cycles (patient_id, cycle_number, status) VALUES (?, ?, ?)",
            (patient.id, 2, 'completed'),
        )
        conn.commit()
        cycle2 = cursor.lastrowid

        create_gcsf(conn, _make_gcsf(cycle_id=cycle_id, agent='pegfilgrastim'))
        create_gcsf(conn, _make_gcsf(cycle_id=cycle2, agent='filgrastim'))

        rows = list_gcsf_for_cycle(conn, cycle_id)
        assert len(rows) == 1
        assert rows[0].agent == 'pegfilgrastim'

    def test_latest_returns_none_when_empty(self, conn, patient):
        assert latest_gcsf(conn, 'PT-001') is None

    def test_latest_returns_most_recent(self, conn, patient):
        create_gcsf(conn, _make_gcsf(admin_date='2026-01-01', agent='filgrastim'))
        create_gcsf(conn, _make_gcsf(admin_date='2026-04-10', agent='pegfilgrastim'))
        assert latest_gcsf(conn, 'PT-001').agent == 'pegfilgrastim'

    def test_latest_excludes_deleted(self, conn, patient):
        g = create_gcsf(conn, _make_gcsf(admin_date='2026-04-10', agent='pegfilgrastim'))
        delete_gcsf(conn, g.id)
        create_gcsf(conn, _make_gcsf(admin_date='2026-01-01', agent='filgrastim'))
        assert latest_gcsf(conn, 'PT-001').agent == 'filgrastim'


# ---------------------------------------------------------------------------
# gcsf_dates_for_patient tests (chart integration)
# ---------------------------------------------------------------------------

class TestGcsfDates:
    def test_empty_when_no_records(self, conn, patient):
        assert gcsf_dates_for_patient(conn, 'PT-001') == []

    def test_window_covers_admin_date_plus_7(self, conn, patient):
        create_gcsf(conn, _make_gcsf(admin_date='2026-04-10'))
        stimulated = gcsf_dates_for_patient(conn, 'PT-001', window_days=7)
        assert date(2026, 4, 10) in stimulated
        assert date(2026, 4, 17) in stimulated
        assert date(2026, 4, 18) not in stimulated

    def test_marker_count_with_two_records(self, conn, patient):
        create_gcsf(conn, _make_gcsf(admin_date='2026-04-10'))
        create_gcsf(conn, _make_gcsf(admin_date='2026-04-20'))
        stimulated = gcsf_dates_for_patient(conn, 'PT-001', window_days=7)
        # Each record covers 8 dates (admin_date + 7 days inclusive)
        assert len(stimulated) == 16

    def test_custom_window(self, conn, patient):
        create_gcsf(conn, _make_gcsf(admin_date='2026-04-10'))
        stimulated = gcsf_dates_for_patient(conn, 'PT-001', window_days=3)
        assert len(stimulated) == 4   # day 0, 1, 2, 3
        assert date(2026, 4, 13) in stimulated
        assert date(2026, 4, 14) not in stimulated
