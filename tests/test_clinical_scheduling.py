"""Tests for src/clinical/scheduling.py pure functions."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clinical.scheduling import expected_cycle_date, cycle_status

CFG = {
    'cadence_days': {'standard_q3w': 21, 'dose_dense_q2w': 14},
    'due_within_days': 7,
    'overdue_after_days': 0,
}


# ---------------------------------------------------------------------------
# expected_cycle_date
# ---------------------------------------------------------------------------

class TestExpectedCycleDate:

    def test_standard_q3w(self):
        result = expected_cycle_date(date(2026, 4, 1), 'standard_q3w', CFG)
        assert result == date(2026, 4, 22)

    def test_dose_dense_q2w(self):
        result = expected_cycle_date(date(2026, 4, 1), 'dose_dense_q2w', CFG)
        assert result == date(2026, 4, 15)

    def test_none_dose_density_defaults_to_q3w(self):
        result = expected_cycle_date(date(2026, 4, 1), None, CFG)
        assert result == date(2026, 4, 22)

    def test_unknown_dose_density_defaults_to_q3w(self):
        result = expected_cycle_date(date(2026, 4, 1), 'unknown', CFG)
        assert result == date(2026, 4, 22)


# ---------------------------------------------------------------------------
# cycle_status
# ---------------------------------------------------------------------------

class TestCycleStatus:

    def test_on_schedule_far_away(self):
        status, delta = cycle_status(date(2026, 4, 1), 'standard_q3w', date(2026, 4, 5), CFG)
        assert status == 'on_schedule'
        assert delta == 17

    def test_due_soon_within_window(self):
        status, delta = cycle_status(date(2026, 4, 1), 'standard_q3w', date(2026, 4, 16), CFG)
        assert status == 'due_soon'
        assert delta == 6

    def test_due_soon_exactly_at_boundary(self):
        status, delta = cycle_status(date(2026, 4, 1), 'standard_q3w', date(2026, 4, 15), CFG)
        assert status == 'due_soon'
        assert delta == 7

    def test_due_soon_day_of(self):
        status, delta = cycle_status(date(2026, 4, 1), 'standard_q3w', date(2026, 4, 22), CFG)
        assert status == 'due_soon'
        assert delta == 0

    def test_overdue_day_after(self):
        status, delta = cycle_status(date(2026, 4, 1), 'standard_q3w', date(2026, 4, 23), CFG)
        assert status == 'overdue'
        assert delta == -1

    def test_overdue_several_days(self):
        status, delta = cycle_status(date(2026, 4, 1), 'standard_q3w', date(2026, 4, 30), CFG)
        assert status == 'overdue'
        assert delta == -8

    def test_dose_dense_overdue(self):
        status, delta = cycle_status(date(2026, 4, 1), 'dose_dense_q2w', date(2026, 4, 20), CFG)
        assert status == 'overdue'
        assert delta == -5

    def test_dose_dense_on_schedule(self):
        status, delta = cycle_status(date(2026, 4, 1), 'dose_dense_q2w', date(2026, 4, 5), CFG)
        assert status == 'on_schedule'
        assert delta == 10
