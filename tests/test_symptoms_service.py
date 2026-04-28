"""Tests for src/services/symptoms.py (US-030).

Covers: create, create_many, update, soft-delete, list, list_for_cycle,
        latest_cycle_symptoms, audit trail.
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
from services.patients import create_patient
from services.symptoms import (
    SymptomEntry,
    create_many,
    create_symptom,
    delete_symptom,
    latest_cycle_symptoms,
    list_symptoms,
    list_symptoms_for_cycle,
    update_symptom,
)


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


def _make_entry(cycle_id: int, symptom='nausea', grade=2, **kwargs) -> SymptomEntry:
    defaults = dict(
        patient_id='PT-001',
        cycle_id=cycle_id,
        entry_date='2026-04-01',
        symptom=symptom,
        grade=grade,
    )
    defaults.update(kwargs)
    return SymptomEntry(**defaults)


# ---------------------------------------------------------------------------
# Create tests
# ---------------------------------------------------------------------------

class TestCreateSymptom:
    def test_create_returns_entry_with_id(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id))
        assert e.id is not None

    def test_create_persists_grade(self, conn, patient, cycle_id):
        create_symptom(conn, _make_entry(cycle_id, grade=3))
        assert list_symptoms(conn, 'PT-001')[0].grade == 3

    def test_create_persists_symptom_name(self, conn, patient, cycle_id):
        create_symptom(conn, _make_entry(cycle_id, symptom='fatigue'))
        assert list_symptoms(conn, 'PT-001')[0].symptom == 'fatigue'

    def test_create_writes_audit_row(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id), actor='nurse1')
        rows = get_audit_for_entity(conn, 'symptom_entry', e.id)
        assert rows[0]['action'] == 'symptom_created'
        assert rows[0]['actor'] == 'nurse1'

    def test_create_audit_action_in_actions_set(self):
        assert 'symptom_created' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# create_many tests
# ---------------------------------------------------------------------------

class TestCreateMany:
    def test_create_many_saves_all(self, conn, patient, cycle_id):
        entries = [
            _make_entry(cycle_id, symptom='nausea',  grade=2),
            _make_entry(cycle_id, symptom='fatigue', grade=1),
        ]
        saved = create_many(conn, entries)
        assert len(saved) == 2
        assert all(e.id is not None for e in saved)

    def test_create_many_empty_list_is_no_op(self, conn, patient, cycle_id):
        result = create_many(conn, [])
        assert result == []

    def test_create_many_writes_audit_rows(self, conn, patient, cycle_id):
        entries = [
            _make_entry(cycle_id, symptom='nausea'),
            _make_entry(cycle_id, symptom='fatigue'),
        ]
        saved = create_many(conn, entries)
        for e in saved:
            rows = get_audit_for_entity(conn, 'symptom_entry', e.id)
            assert rows[0]['action'] == 'symptom_created'

    def test_create_many_all_in_same_cycle(self, conn, patient, cycle_id):
        entries = [_make_entry(cycle_id, symptom=s) for s in ['nausea', 'fatigue', 'mucositis']]
        create_many(conn, entries)
        assert len(list_symptoms_for_cycle(conn, cycle_id)) == 3


# ---------------------------------------------------------------------------
# Update tests
# ---------------------------------------------------------------------------

class TestUpdateSymptom:
    def test_update_changes_grade(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id, grade=1))
        e.grade = 4
        update_symptom(conn, e)
        assert list_symptoms(conn, 'PT-001')[0].grade == 4

    def test_update_writes_audit_row(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id))
        e.grade = 3
        update_symptom(conn, e, actor='nurse2')
        rows = get_audit_for_entity(conn, 'symptom_entry', e.id)
        assert any(r['action'] == 'symptom_updated' for r in rows)

    def test_update_without_id_raises(self, conn, patient, cycle_id):
        e = _make_entry(cycle_id)
        with pytest.raises(ValueError):
            update_symptom(conn, e)

    def test_update_missing_id_raises_lookup(self, conn, patient, cycle_id):
        e = _make_entry(cycle_id)
        e.id = 9999
        with pytest.raises(LookupError):
            update_symptom(conn, e)

    def test_update_audit_action_in_actions_set(self):
        assert 'symptom_updated' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# Soft-delete tests
# ---------------------------------------------------------------------------

class TestDeleteSymptom:
    def test_delete_removes_from_list(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id))
        delete_symptom(conn, e.id)
        assert list_symptoms(conn, 'PT-001') == []

    def test_delete_keeps_with_include_deleted(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id))
        delete_symptom(conn, e.id)
        assert len(list_symptoms(conn, 'PT-001', include_deleted=True)) == 1

    def test_delete_writes_audit_row(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id))
        delete_symptom(conn, e.id, actor='nurse3')
        rows = get_audit_for_entity(conn, 'symptom_entry', e.id)
        assert any(r['action'] == 'symptom_deleted' for r in rows)

    def test_delete_idempotent(self, conn, patient, cycle_id):
        e = create_symptom(conn, _make_entry(cycle_id))
        delete_symptom(conn, e.id)
        delete_symptom(conn, e.id)  # no-op
        assert list_symptoms(conn, 'PT-001', include_deleted=True)[0].deleted_at is not None

    def test_delete_missing_id_raises(self, conn, patient, cycle_id):
        with pytest.raises(LookupError):
            delete_symptom(conn, 9999)

    def test_delete_audit_action_in_actions_set(self):
        assert 'symptom_deleted' in audit_module.ACTIONS


# ---------------------------------------------------------------------------
# List + latest tests
# ---------------------------------------------------------------------------

class TestListSymptoms:
    def test_list_empty(self, conn, patient, cycle_id):
        assert list_symptoms(conn, 'PT-001') == []

    def test_list_for_cycle_empty(self, conn, patient, cycle_id):
        assert list_symptoms_for_cycle(conn, cycle_id) == []

    def test_list_for_cycle_returns_only_matching_cycle(self, conn, patient, cycle_id):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cycles (patient_id, cycle_number, status) VALUES (?, ?, ?)",
            (patient.id, 2, 'completed'),
        )
        conn.commit()
        cycle2 = cursor.lastrowid

        create_symptom(conn, _make_entry(cycle_id, symptom='nausea'))
        create_symptom(conn, _make_entry(cycle2, symptom='fatigue'))

        rows = list_symptoms_for_cycle(conn, cycle_id)
        assert len(rows) == 1
        assert rows[0].symptom == 'nausea'

    def test_latest_cycle_symptoms_empty(self, conn, patient, cycle_id):
        assert latest_cycle_symptoms(conn, 'PT-001') == []

    def test_latest_cycle_symptoms_returns_most_recent_cycle(self, conn, patient, cycle_id):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cycles (patient_id, cycle_number, status) VALUES (?, ?, ?)",
            (patient.id, 2, 'completed'),
        )
        conn.commit()
        cycle2 = cursor.lastrowid

        create_symptom(conn, _make_entry(cycle_id, symptom='nausea', entry_date='2026-01-01'))
        create_symptom(conn, _make_entry(cycle2, symptom='fatigue', entry_date='2026-04-01'))

        latest = latest_cycle_symptoms(conn, 'PT-001')
        assert len(latest) == 1
        assert latest[0].symptom == 'fatigue'

    def test_phase_ac_has_4_symptoms_via_create_many(self, conn, patient, cycle_id):
        from config import get as get_config
        from clinical.symptoms import applicable_symptoms
        cfg  = get_config().toxicity.model_dump()
        syms = applicable_symptoms('AC', cfg)
        entries = [_make_entry(cycle_id, symptom=s) for s in syms]
        saved = create_many(conn, entries)
        assert len(saved) == 4

    def test_phase_t_has_6_symptoms_via_create_many(self, conn, patient, cycle_id):
        from config import get as get_config
        from clinical.symptoms import applicable_symptoms
        cfg  = get_config().toxicity.model_dump()
        syms = applicable_symptoms('T', cfg)
        entries = [_make_entry(cycle_id, symptom=s) for s in syms]
        saved = create_many(conn, entries)
        assert len(saved) == 6
