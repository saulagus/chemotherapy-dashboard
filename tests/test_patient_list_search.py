"""Tests for patient list search/filter/sort query layer (US-031)."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, Cycle, add_patient, add_cycle
from services.patients import list_patients
import config as config_module


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    config_module.reset()
    yield connection
    connection.close()
    config_module.reset()


@pytest.fixture
def populated_db(conn):
    p1 = add_patient(conn, Patient(patient_id='PT-001', name='Alice Smith',
                                    age=45, dose_density='standard_q3w'))
    p2 = add_patient(conn, Patient(patient_id='PT-002', name='Bob Jones',
                                    age=60, dose_density='dose_dense_q2w'))
    p3 = add_patient(conn, Patient(patient_id='PT-003', name='Carol White',
                                    age=38, dose_density='standard_q3w'))
    # Alice: 2 completed cycles (AC phase)
    for i in range(1, 3):
        add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=i, phase='AC',
                              status='completed', actual_date=date(2026, 1, i)))
    # Bob: 5 completed cycles (T phase)
    for i in range(1, 6):
        phase = 'AC' if i <= 4 else 'T'
        add_cycle(conn, Cycle(patient_id=p2.id, cycle_number=i, phase=phase,
                              status='completed', actual_date=date(2026, 2, i)))
    # Carol: 8 completed cycles (completed)
    for i in range(1, 9):
        phase = 'AC' if i <= 4 else 'T'
        add_cycle(conn, Cycle(patient_id=p3.id, cycle_number=i, phase=phase,
                              status='completed', actual_date=date(2026, 3, i)))
    return p1, p2, p3


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class TestSearch:

    def test_no_search_returns_all(self, conn, populated_db):
        result = list_patients(conn)
        assert len(result) == 3

    def test_search_by_name(self, conn, populated_db):
        result = list_patients(conn, search='alice')
        assert len(result) == 1
        assert result[0].name == 'Alice Smith'

    def test_search_by_id(self, conn, populated_db):
        result = list_patients(conn, search='PT-002')
        assert len(result) == 1
        assert result[0].patient_id == 'PT-002'

    def test_search_case_insensitive(self, conn, populated_db):
        result = list_patients(conn, search='BOB')
        assert len(result) == 1

    def test_search_partial_match(self, conn, populated_db):
        result = list_patients(conn, search='o')
        names = {p.name for p in result}
        assert 'Bob Jones' in names
        assert 'Carol White' in names

    def test_search_no_match(self, conn, populated_db):
        result = list_patients(conn, search='zzz')
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------

class TestSort:

    def test_sort_by_name_asc(self, conn, populated_db):
        result = list_patients(conn, sort_by='name', sort_dir='asc')
        names = [p.name for p in result]
        assert names == sorted(names)

    def test_sort_by_name_desc(self, conn, populated_db):
        result = list_patients(conn, sort_by='name', sort_dir='desc')
        names = [p.name for p in result]
        assert names == sorted(names, reverse=True)

    def test_sort_by_age_asc(self, conn, populated_db):
        result = list_patients(conn, sort_by='age', sort_dir='asc')
        ages = [p.age for p in result]
        assert ages == sorted(ages)

    def test_sort_by_patient_id(self, conn, populated_db):
        result = list_patients(conn, sort_by='patient_id', sort_dir='asc')
        ids = [p.patient_id for p in result]
        assert ids == sorted(ids)

    def test_invalid_sort_defaults_to_name(self, conn, populated_db):
        result = list_patients(conn, sort_by='invalid_col')
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

class TestFilter:

    def test_filter_all(self, conn, populated_db):
        result = list_patients(conn, phase_filter=None)
        assert len(result) == 3

    def test_filter_ac(self, conn, populated_db):
        result = list_patients(conn, phase_filter='AC')
        assert len(result) == 1
        assert result[0].name == 'Alice Smith'

    def test_filter_t(self, conn, populated_db):
        result = list_patients(conn, phase_filter='T')
        assert len(result) == 1
        assert result[0].name == 'Bob Jones'

    def test_filter_completed(self, conn, populated_db):
        result = list_patients(conn, phase_filter='Completed')
        assert len(result) == 1
        assert result[0].name == 'Carol White'


# ---------------------------------------------------------------------------
# Combinations
# ---------------------------------------------------------------------------

class TestCombined:

    def test_search_plus_filter(self, conn, populated_db):
        result = list_patients(conn, search='alice', phase_filter='AC')
        assert len(result) == 1

    def test_search_plus_wrong_filter_empty(self, conn, populated_db):
        result = list_patients(conn, search='alice', phase_filter='T')
        assert len(result) == 0

    def test_soft_deleted_excluded(self, conn, populated_db):
        from services.patients import soft_delete_patient
        p1 = populated_db[0]
        soft_delete_patient(conn, p1.id)
        result = list_patients(conn)
        assert len(result) == 2
