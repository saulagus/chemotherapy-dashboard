"""Tests for cycle status indicator (US-032) — integration with DB fixtures."""

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, Cycle, add_patient, add_cycle
from views.components.cycle_status_indicator import (
    get_status_for_patient,
    status_color,
    status_sort_key,
)
import config as config_module


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    config_module.reset()
    yield connection
    connection.close()
    config_module.reset()


# ---------------------------------------------------------------------------
# No cycles → gray / no_cycles
# ---------------------------------------------------------------------------

class TestNoCycles:

    def test_no_cycles_status(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-200', name='No Cycles'))
        code, text, tip = get_status_for_patient(conn, p.id)
        assert code == 'no_cycles'
        assert 'No completed cycles' in tip


# ---------------------------------------------------------------------------
# On schedule — last cycle recent
# ---------------------------------------------------------------------------

class TestOnSchedule:

    def test_on_schedule_q3w(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-201', name='On Schedule',
                                       dose_density='standard_q3w'))
        today = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=today))
        code, text, tip = get_status_for_patient(conn, p.id, today=today + timedelta(days=5))
        assert code == 'on_schedule'
        assert 'away' in tip


# ---------------------------------------------------------------------------
# Due soon — within the lookahead window
# ---------------------------------------------------------------------------

class TestDueSoon:

    def test_due_soon_q3w(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-202', name='Due Soon',
                                       dose_density='standard_q3w'))
        last = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=last))
        code, text, tip = get_status_for_patient(conn, p.id, today=last + timedelta(days=17))
        assert code == 'due_soon'
        assert 'due in' in tip

    def test_due_soon_dose_dense(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-203', name='DD Due Soon',
                                       dose_density='dose_dense_q2w'))
        last = date(2026, 5, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=last))
        code, _, _ = get_status_for_patient(conn, p.id, today=last + timedelta(days=10))
        assert code == 'due_soon'


# ---------------------------------------------------------------------------
# Overdue — past the expected date
# ---------------------------------------------------------------------------

class TestOverdue:

    def test_overdue_q3w(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-204', name='Overdue',
                                       dose_density='standard_q3w'))
        last = date(2026, 4, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=last))
        code, text, tip = get_status_for_patient(conn, p.id, today=last + timedelta(days=25))
        assert code == 'overdue'
        assert 'overdue' in tip

    def test_overdue_dose_dense(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-205', name='DD Overdue',
                                       dose_density='dose_dense_q2w'))
        last = date(2026, 4, 1)
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=last))
        code, _, _ = get_status_for_patient(conn, p.id, today=last + timedelta(days=20))
        assert code == 'overdue'


# ---------------------------------------------------------------------------
# Sort key ordering
# ---------------------------------------------------------------------------

class TestSortKey:

    def test_overdue_sorts_first(self):
        assert status_sort_key('overdue') < status_sort_key('due_soon')

    def test_due_soon_before_on_schedule(self):
        assert status_sort_key('due_soon') < status_sort_key('on_schedule')

    def test_no_cycles_sorts_last(self):
        assert status_sort_key('no_cycles') > status_sort_key('on_schedule')


# ---------------------------------------------------------------------------
# Color mapping
# ---------------------------------------------------------------------------

class TestStatusColor:

    def test_on_schedule_green(self):
        assert status_color('on_schedule') == '#4CAF50'

    def test_due_soon_yellow(self):
        assert status_color('due_soon') == '#FFC107'

    def test_overdue_red(self):
        assert status_color('overdue') == '#F44336'

    def test_no_cycles_gray(self):
        assert status_color('no_cycles') == '#6b7494'

    def test_unknown_defaults_to_gray(self):
        assert status_color('unknown') == '#6b7494'


# ---------------------------------------------------------------------------
# Uses latest completed cycle only
# ---------------------------------------------------------------------------

class TestLatestCycle:

    def test_uses_latest_completed_not_pending(self, conn):
        p = add_patient(conn, Patient(patient_id='PT-206', name='Latest Test',
                                       dose_density='standard_q3w'))
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=1, phase='AC',
                              status='completed', actual_date=date(2026, 4, 1)))
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=2, phase='AC',
                              status='completed', actual_date=date(2026, 4, 22)))
        add_cycle(conn, Cycle(patient_id=p.id, cycle_number=3, phase='AC',
                              status='pending'))
        code, _, tip = get_status_for_patient(conn, p.id, today=date(2026, 4, 25))
        assert code == 'on_schedule'
        assert '2026-04-22' in tip
