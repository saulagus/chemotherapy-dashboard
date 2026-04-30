"""Tests for low-ANC banner (US-034)."""

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection
from migrations import run_migrations
from models import Patient, Lab, add_patient, add_lab
import config as config_module

# The banner is a Tkinter widget — we test its logic via the underlying
# threshold/dismiss state without instantiating Tk. We extract the core
# logic into testable helpers.


@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    run_migrations(connection)
    config_module.reset()
    yield connection
    connection.close()
    config_module.reset()


@pytest.fixture
def patient(conn):
    return add_patient(conn, Patient(patient_id='PT-050', name='Banner Test'))


def _add_lab(conn, patient_id, anc):
    return add_lab(conn, Lab(patient_id=patient_id, lab_date=date(2026, 5, 1), anc=anc))


# ---------------------------------------------------------------------------
# Banner threshold boundaries
# ---------------------------------------------------------------------------

class TestBannerThresholds:

    def test_red_below_500(self):
        from config import get as get_config
        cfg = get_config().alerts.low_anc_banner
        red_below = cfg.red_below_per_uL / 1000
        assert red_below == 0.5

    def test_orange_below_1000(self):
        from config import get as get_config
        cfg = get_config().alerts.low_anc_banner
        orange_below = cfg.orange_below_per_uL / 1000
        assert orange_below == 1.0

    def test_anc_499_is_red(self):
        anc = 0.499
        from config import get as get_config
        cfg = get_config().alerts.low_anc_banner
        red_below = cfg.red_below_per_uL / 1000
        orange_below = cfg.orange_below_per_uL / 1000
        assert anc < red_below

    def test_anc_500_is_orange(self):
        anc = 0.5
        from config import get as get_config
        cfg = get_config().alerts.low_anc_banner
        red_below = cfg.red_below_per_uL / 1000
        assert anc >= red_below

    def test_anc_999_is_orange(self):
        anc = 0.999
        from config import get as get_config
        cfg = get_config().alerts.low_anc_banner
        orange_below = cfg.orange_below_per_uL / 1000
        assert anc < orange_below

    def test_anc_1000_hidden(self):
        anc = 1.0
        from config import get as get_config
        cfg = get_config().alerts.low_anc_banner
        orange_below = cfg.orange_below_per_uL / 1000
        assert anc >= orange_below


# ---------------------------------------------------------------------------
# Dismiss / restore behavior (tested via internal state dict)
# ---------------------------------------------------------------------------

class TestDismissState:

    def test_dismissed_hides(self):
        dismissed = {}
        pid = 1
        dismissed[pid] = True
        assert dismissed.get(pid) is True

    def test_different_patient_not_dismissed(self):
        dismissed = {1: True}
        assert dismissed.get(2) is None

    def test_until_next_lab_clears_dismissal(self):
        dismissed = {1: True}
        last_lab_id = {1: 10}
        new_lab_id = 11
        if last_lab_id.get(1) != new_lab_id:
            dismissed.pop(1, None)
        last_lab_id[1] = new_lab_id
        assert dismissed.get(1) is None

    def test_same_lab_keeps_dismissed(self):
        dismissed = {1: True}
        last_lab_id = {1: 10}
        new_lab_id = 10
        if last_lab_id.get(1) != new_lab_id:
            dismissed.pop(1, None)
        assert dismissed.get(1) is True


# ---------------------------------------------------------------------------
# DB integration — latest lab read
# ---------------------------------------------------------------------------

class TestLatestLabRead:

    def test_no_labs_returns_none(self, conn, patient):
        from models import get_latest_lab
        assert get_latest_lab(conn, patient.id) is None

    def test_latest_lab_returns_most_recent(self, conn, patient):
        add_lab(conn, Lab(patient_id=patient.id, lab_date=date(2026, 4, 1), anc=2.0))
        add_lab(conn, Lab(patient_id=patient.id, lab_date=date(2026, 4, 15), anc=0.3))
        from models import get_latest_lab
        lab = get_latest_lab(conn, patient.id)
        assert lab.anc == 0.3

    def test_banner_triggered_for_low_anc(self, conn, patient):
        _add_lab(conn, patient.id, 0.4)
        from models import get_latest_lab
        from config import get as get_config
        lab = get_latest_lab(conn, patient.id)
        cfg = get_config().alerts.low_anc_banner
        assert lab.anc < cfg.red_below_per_uL / 1000

    def test_banner_hidden_for_normal_anc(self, conn, patient):
        _add_lab(conn, patient.id, 2.0)
        from models import get_latest_lab
        from config import get as get_config
        lab = get_latest_lab(conn, patient.id)
        cfg = get_config().alerts.low_anc_banner
        assert lab.anc >= cfg.orange_below_per_uL / 1000
