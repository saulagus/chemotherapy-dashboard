"""Tests for src/services/neuropathy.py.

Covers: create, update, soft-delete, list, latest, audit trail.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient
from services import audit as audit_module
from services.audit import get_audit_for_entity
from services.neuropathy import (
    NeuropathyAssessment,
    create_neuropathy,
    delete_neuropathy,
    latest_neuropathy,
    list_neuropathy,
    update_neuropathy,
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


def _make_assessment(**kwargs) -> NeuropathyAssessment:
    defaults = dict(
        patient_id='PT-001',
        assessment_date='2026-04-01',
        sensory_grade=1,
        motor_grade=0,
        ctcae_version='5.0',
    )
    defaults.update(kwargs)
    return NeuropathyAssessment(**defaults)


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------

class TestCreateNeuropathy:
    def test_create_returns_assessment_with_id(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment())
        assert a.id is not None
        assert a.id > 0

    def test_create_persists_grades(self, conn, patient):
        create_neuropathy(conn, _make_assessment(sensory_grade=2, motor_grade=1))
        rows = list_neuropathy(conn, 'PT-001')
        assert rows[0].sensory_grade == 2
        assert rows[0].motor_grade == 1

    def test_create_writes_audit_row(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment(), actor='nurse1')
        rows = get_audit_for_entity(conn, 'neuropathy_assessment', a.id)
        assert len(rows) == 1
        assert rows[0]['action'] == 'neuropathy_created'
        assert rows[0]['actor'] == 'nurse1'

    def test_create_audit_action_in_actions_set(self):
        assert 'neuropathy_created' in audit_module.ACTIONS

    def test_create_with_notes(self, conn, patient):
        create_neuropathy(conn, _make_assessment(notes='tingling fingers'))
        assert list_neuropathy(conn, 'PT-001')[0].notes == 'tingling fingers'

    def test_create_ctcae_version_stored(self, conn, patient):
        create_neuropathy(conn, _make_assessment(ctcae_version='4.03'))
        assert list_neuropathy(conn, 'PT-001')[0].ctcae_version == '4.03'


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------

class TestUpdateNeuropathy:
    def test_update_changes_grades(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment(sensory_grade=1))
        a.sensory_grade = 3
        update_neuropathy(conn, a)
        assert list_neuropathy(conn, 'PT-001')[0].sensory_grade == 3

    def test_update_writes_audit_row(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment())
        a.sensory_grade = 2
        update_neuropathy(conn, a, actor='nurse2')
        rows = get_audit_for_entity(conn, 'neuropathy_assessment', a.id)
        actions = [r['action'] for r in rows]
        assert 'neuropathy_updated' in actions

    def test_update_without_id_raises(self, conn, patient):
        a = _make_assessment()
        with pytest.raises(ValueError):
            update_neuropathy(conn, a)

    def test_update_missing_id_raises_lookup(self, conn, patient):
        a = _make_assessment()
        a.id = 9999
        with pytest.raises(LookupError):
            update_neuropathy(conn, a)

    def test_update_audit_action_in_actions_set(self):
        assert 'neuropathy_updated' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# Soft-delete tests
# ---------------------------------------------------------------------------

class TestDeleteNeuropathy:
    def test_delete_removes_from_list(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment())
        delete_neuropathy(conn, a.id)
        assert list_neuropathy(conn, 'PT-001') == []

    def test_delete_keeps_row_when_include_deleted(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment())
        delete_neuropathy(conn, a.id)
        assert len(list_neuropathy(conn, 'PT-001', include_deleted=True)) == 1

    def test_delete_writes_audit_row(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment())
        delete_neuropathy(conn, a.id, actor='nurse3')
        rows = get_audit_for_entity(conn, 'neuropathy_assessment', a.id)
        actions = [r['action'] for r in rows]
        assert 'neuropathy_deleted' in actions

    def test_delete_idempotent(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment())
        delete_neuropathy(conn, a.id)
        delete_neuropathy(conn, a.id)  # second call is no-op
        assert list_neuropathy(conn, 'PT-001', include_deleted=True)[0].deleted_at is not None

    def test_delete_missing_id_raises(self, conn, patient):
        with pytest.raises(LookupError):
            delete_neuropathy(conn, 9999)

    def test_delete_audit_action_in_actions_set(self):
        assert 'neuropathy_deleted' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# List + latest tests
# ---------------------------------------------------------------------------

class TestListNeuropathy:
    def test_list_empty_patient(self, conn, patient):
        assert list_neuropathy(conn, 'PT-001') == []

    def test_list_returns_newest_first(self, conn, patient):
        create_neuropathy(conn, _make_assessment(assessment_date='2026-01-01'))
        create_neuropathy(conn, _make_assessment(assessment_date='2026-03-01'))
        rows = list_neuropathy(conn, 'PT-001')
        assert str(rows[0].assessment_date) == '2026-03-01'

    def test_latest_returns_none_when_empty(self, conn, patient):
        assert latest_neuropathy(conn, 'PT-001') is None

    def test_latest_returns_most_recent(self, conn, patient):
        create_neuropathy(conn, _make_assessment(assessment_date='2026-01-01', sensory_grade=1))
        create_neuropathy(conn, _make_assessment(assessment_date='2026-04-01', sensory_grade=3))
        latest = latest_neuropathy(conn, 'PT-001')
        assert latest.sensory_grade == 3

    def test_latest_excludes_deleted(self, conn, patient):
        a = create_neuropathy(conn, _make_assessment(assessment_date='2026-04-01', sensory_grade=3))
        delete_neuropathy(conn, a.id)
        create_neuropathy(conn, _make_assessment(assessment_date='2026-01-01', sensory_grade=1))
        latest = latest_neuropathy(conn, 'PT-001')
        assert latest.sensory_grade == 1
