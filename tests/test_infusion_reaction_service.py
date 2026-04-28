"""Tests for src/services/infusion_reactions.py.

Covers: create, update, soft-delete, list, list_for_cycle, latest, audit trail.
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
from services.infusion_reactions import (
    InfusionReaction,
    create_reaction,
    delete_reaction,
    latest_reaction,
    list_reactions,
    list_reactions_for_cycle,
    update_reaction,
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
    """Insert a minimal cycle row and return its id."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cycles (patient_id, cycle_number, status) VALUES (?, ?, ?)",
        (patient.id, 1, 'completed'),
    )
    conn.commit()
    return cursor.lastrowid


def _make_reaction(cycle_id: int, **kwargs) -> InfusionReaction:
    defaults = dict(
        patient_id='PT-001',
        cycle_id=cycle_id,
        agent='paclitaxel',
        onset_min=14,
        severity_grade=2,
    )
    defaults.update(kwargs)
    return InfusionReaction(**defaults)


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------

class TestCreateReaction:
    def test_create_returns_reaction_with_id(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id))
        assert r.id is not None
        assert r.id > 0

    def test_create_persists_grade(self, conn, patient, cycle_id):
        create_reaction(conn, _make_reaction(cycle_id, severity_grade=3))
        assert list_reactions(conn, 'PT-001')[0].severity_grade == 3

    def test_create_persists_agent(self, conn, patient, cycle_id):
        create_reaction(conn, _make_reaction(cycle_id, agent='doxorubicin'))
        assert list_reactions(conn, 'PT-001')[0].agent == 'doxorubicin'

    def test_create_writes_audit_row(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id), actor='nurse1')
        rows = get_audit_for_entity(conn, 'infusion_reaction', r.id)
        assert len(rows) == 1
        assert rows[0]['action'] == 'reaction_created'
        assert rows[0]['actor'] == 'nurse1'

    def test_create_audit_action_in_actions_set(self):
        assert 'reaction_created' in audit_module.ACTIONS

    def test_create_with_symptoms_list(self, conn, patient, cycle_id):
        r = _make_reaction(cycle_id)
        r.symptoms = ['flushing', 'dyspnea']
        create_reaction(conn, r)
        saved = list_reactions(conn, 'PT-001')[0]
        assert 'flushing' in saved.symptoms
        assert 'dyspnea' in saved.symptoms


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------

class TestUpdateReaction:
    def test_update_changes_grade(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id, severity_grade=2))
        r.severity_grade = 3
        update_reaction(conn, r)
        assert list_reactions(conn, 'PT-001')[0].severity_grade == 3

    def test_update_writes_audit_row(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id))
        r.severity_grade = 4
        update_reaction(conn, r, actor='nurse2')
        rows = get_audit_for_entity(conn, 'infusion_reaction', r.id)
        assert any(row['action'] == 'reaction_updated' for row in rows)

    def test_update_without_id_raises(self, conn, patient, cycle_id):
        r = _make_reaction(cycle_id)
        with pytest.raises(ValueError):
            update_reaction(conn, r)

    def test_update_missing_id_raises_lookup(self, conn, patient, cycle_id):
        r = _make_reaction(cycle_id)
        r.id = 9999
        with pytest.raises(LookupError):
            update_reaction(conn, r)

    def test_update_audit_action_in_actions_set(self):
        assert 'reaction_updated' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# Soft-delete tests
# ---------------------------------------------------------------------------

class TestDeleteReaction:
    def test_delete_removes_from_list(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id))
        delete_reaction(conn, r.id)
        assert list_reactions(conn, 'PT-001') == []

    def test_delete_keeps_row_when_include_deleted(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id))
        delete_reaction(conn, r.id)
        assert len(list_reactions(conn, 'PT-001', include_deleted=True)) == 1

    def test_delete_writes_audit_row(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id))
        delete_reaction(conn, r.id, actor='nurse3')
        rows = get_audit_for_entity(conn, 'infusion_reaction', r.id)
        assert any(row['action'] == 'reaction_deleted' for row in rows)

    def test_delete_idempotent(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id))
        delete_reaction(conn, r.id)
        delete_reaction(conn, r.id)  # no-op
        assert list_reactions(conn, 'PT-001', include_deleted=True)[0].deleted_at is not None

    def test_delete_missing_id_raises(self, conn, patient, cycle_id):
        with pytest.raises(LookupError):
            delete_reaction(conn, 9999)

    def test_delete_audit_action_in_actions_set(self):
        assert 'reaction_deleted' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# List + latest tests
# ---------------------------------------------------------------------------

class TestListReactions:
    def test_list_empty(self, conn, patient, cycle_id):
        assert list_reactions(conn, 'PT-001') == []

    def test_list_for_cycle_empty(self, conn, patient, cycle_id):
        assert list_reactions_for_cycle(conn, cycle_id) == []

    def test_list_for_cycle_returns_only_matching_cycle(self, conn, patient, cycle_id):
        # second cycle
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cycles (patient_id, cycle_number, status) VALUES (?, ?, ?)",
            (patient.id, 2, 'completed'),
        )
        conn.commit()
        cycle2 = cursor.lastrowid

        create_reaction(conn, _make_reaction(cycle_id, agent='paclitaxel'))
        create_reaction(conn, _make_reaction(cycle2, agent='doxorubicin'))

        rows = list_reactions_for_cycle(conn, cycle_id)
        assert len(rows) == 1
        assert rows[0].agent == 'paclitaxel'

    def test_latest_returns_none_when_empty(self, conn, patient, cycle_id):
        assert latest_reaction(conn, 'PT-001') is None

    def test_latest_returns_most_recent(self, conn, patient, cycle_id):
        create_reaction(conn, _make_reaction(cycle_id, severity_grade=1))
        create_reaction(conn, _make_reaction(cycle_id, severity_grade=3))
        assert latest_reaction(conn, 'PT-001').severity_grade == 3

    def test_latest_excludes_deleted(self, conn, patient, cycle_id):
        r = create_reaction(conn, _make_reaction(cycle_id, severity_grade=3))
        delete_reaction(conn, r.id)
        create_reaction(conn, _make_reaction(cycle_id, severity_grade=1))
        assert latest_reaction(conn, 'PT-001').severity_grade == 1
