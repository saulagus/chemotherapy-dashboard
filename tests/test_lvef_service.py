"""Tests for services/lvef.py.

Covers: create, update, soft-delete, list, get_baseline, audit trail.
"""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import LvefAssessment, Patient
from services import audit as audit_module
from services.lvef import (
    create_lvef,
    delete_lvef,
    get_baseline_lvef,
    list_lvef,
    update_lvef,
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
        patient_id='PT-001', name='Cardiac Patient',
        start_date=date(2026, 1, 1), protocol='Standard AC-T', total_cycles=8,
    ))


def _assessment(patient_id, lvef=62.0, modality='echo',
                context='baseline', notes=None, on_date=None):
    return LvefAssessment(
        patient_id=patient_id,
        assessment_date=on_date or date(2026, 1, 10),
        lvef_percent=lvef,
        modality=modality,
        context=context,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# create_lvef
# ---------------------------------------------------------------------------

def test_create_lvef_returns_with_id(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    assert a.id is not None


def test_create_lvef_persisted(conn, patient):
    create_lvef(conn, _assessment(patient.id, lvef=65.0, context='baseline'))
    rows = list_lvef(conn, patient.id)
    assert len(rows) == 1
    assert rows[0].lvef_percent == 65.0
    assert rows[0].context == 'baseline'


def test_create_lvef_writes_audit(conn, patient):
    a = create_lvef(conn, _assessment(patient.id), actor='nurse_a')
    audit_rows = audit_module.get_audit_for_entity(conn, 'lvef_assessment', a.id)
    assert len(audit_rows) == 1
    assert audit_rows[0]['action'] == 'lvef_created'
    assert audit_rows[0]['actor'] == 'nurse_a'


def test_create_lvef_audit_captures_lvef_percent(conn, patient):
    a = create_lvef(conn, _assessment(patient.id, lvef=58.0))
    audit_rows = audit_module.get_audit_for_entity(conn, 'lvef_assessment', a.id)
    assert audit_rows[0]['after']['lvef_percent'] == 58.0


# ---------------------------------------------------------------------------
# update_lvef
# ---------------------------------------------------------------------------

def test_update_lvef_changes_percent(conn, patient):
    a = create_lvef(conn, _assessment(patient.id, lvef=65.0))
    a.lvef_percent = 55.0
    update_lvef(conn, a)
    rows = list_lvef(conn, patient.id)
    assert rows[0].lvef_percent == 55.0


def test_update_lvef_changes_notes(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    a.notes = 'Re-checked after symptoms'
    update_lvef(conn, a)
    rows = list_lvef(conn, patient.id)
    assert rows[0].notes == 'Re-checked after symptoms'


def test_update_lvef_writes_audit_with_before_and_after(conn, patient):
    a = create_lvef(conn, _assessment(patient.id, lvef=65.0))
    a.lvef_percent = 52.0
    update_lvef(conn, a, actor='nurse_b')
    audit_rows = audit_module.get_audit_for_entity(conn, 'lvef_assessment', a.id)
    upd = next(r for r in audit_rows if r['action'] == 'lvef_updated')
    assert upd['before']['lvef_percent'] == 65.0
    assert upd['after']['lvef_percent'] == 52.0
    assert upd['actor'] == 'nurse_b'


def test_update_lvef_missing_id_raises(conn, patient):
    a = _assessment(patient.id)  # no id assigned
    with pytest.raises(ValueError, match='id'):
        update_lvef(conn, a)


def test_update_lvef_unknown_id_raises(conn, patient):
    a = _assessment(patient.id)
    a.id = 9999
    with pytest.raises(LookupError):
        update_lvef(conn, a)


def test_update_lvef_soft_deleted_raises(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    delete_lvef(conn, a.id)
    a.lvef_percent = 50.0
    with pytest.raises(ValueError, match='soft-deleted'):
        update_lvef(conn, a)


# ---------------------------------------------------------------------------
# delete_lvef (soft-delete)
# ---------------------------------------------------------------------------

def test_delete_lvef_hides_from_list(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    delete_lvef(conn, a.id)
    assert list_lvef(conn, patient.id) == []


def test_delete_lvef_visible_with_include_deleted(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    delete_lvef(conn, a.id)
    rows = list_lvef(conn, patient.id, include_deleted=True)
    assert len(rows) == 1
    assert rows[0].deleted_at is not None


def test_delete_lvef_writes_audit(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    delete_lvef(conn, a.id, actor='admin')
    audit_rows = audit_module.get_audit_for_entity(conn, 'lvef_assessment', a.id)
    del_row = next(r for r in audit_rows if r['action'] == 'lvef_deleted')
    assert del_row['actor'] == 'admin'
    assert del_row['before']['lvef_percent'] == 62.0


def test_delete_lvef_second_call_is_noop(conn, patient):
    a = create_lvef(conn, _assessment(patient.id))
    delete_lvef(conn, a.id)
    delete_lvef(conn, a.id)  # should not raise
    audit_rows = audit_module.get_audit_for_entity(conn, 'lvef_assessment', a.id)
    assert sum(1 for r in audit_rows if r['action'] == 'lvef_deleted') == 1


def test_delete_lvef_unknown_id_raises(conn, patient):
    with pytest.raises(LookupError):
        delete_lvef(conn, 9999)


# ---------------------------------------------------------------------------
# list_lvef
# ---------------------------------------------------------------------------

def test_list_lvef_returns_newest_first(conn, patient):
    create_lvef(conn, _assessment(patient.id, lvef=65.0, on_date=date(2026, 1, 1)))
    create_lvef(conn, _assessment(patient.id, lvef=60.0, on_date=date(2026, 3, 1)))
    rows = list_lvef(conn, patient.id)
    assert rows[0].lvef_percent == 60.0
    assert rows[1].lvef_percent == 65.0


def test_list_lvef_empty_for_no_records(conn, patient):
    assert list_lvef(conn, patient.id) == []


def test_list_lvef_excludes_soft_deleted_by_default(conn, patient):
    a1 = create_lvef(conn, _assessment(patient.id, lvef=65.0))
    a2 = create_lvef(conn, _assessment(patient.id, lvef=60.0))
    delete_lvef(conn, a1.id)
    rows = list_lvef(conn, patient.id)
    assert len(rows) == 1
    assert rows[0].id == a2.id


# ---------------------------------------------------------------------------
# get_baseline_lvef
# ---------------------------------------------------------------------------

def test_get_baseline_returns_most_recent_baseline(conn, patient):
    create_lvef(conn, _assessment(patient.id, lvef=65.0, context='baseline',
                                  on_date=date(2026, 1, 1)))
    create_lvef(conn, _assessment(patient.id, lvef=63.0, context='baseline',
                                  on_date=date(2026, 2, 1)))
    baseline = get_baseline_lvef(conn, patient.id)
    assert baseline.lvef_percent == 63.0


def test_get_baseline_ignores_non_baseline_context(conn, patient):
    create_lvef(conn, _assessment(patient.id, lvef=60.0, context='ad_hoc'))
    assert get_baseline_lvef(conn, patient.id) is None


def test_get_baseline_ignores_deleted(conn, patient):
    a = create_lvef(conn, _assessment(patient.id, lvef=65.0, context='baseline'))
    delete_lvef(conn, a.id)
    assert get_baseline_lvef(conn, patient.id) is None


def test_get_baseline_returns_none_when_no_records(conn, patient):
    assert get_baseline_lvef(conn, patient.id) is None


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------

def test_lvef_lifecycle_audit_trail(conn, patient):
    a = create_lvef(conn, _assessment(patient.id, lvef=65.0))
    a.lvef_percent = 58.0
    update_lvef(conn, a)
    delete_lvef(conn, a.id)
    audit_rows = audit_module.get_audit_for_entity(conn, 'lvef_assessment', a.id)
    actions = [r['action'] for r in audit_rows]
    assert 'lvef_created' in actions
    assert 'lvef_updated' in actions
    assert 'lvef_deleted' in actions
