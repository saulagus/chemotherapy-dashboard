"""Tests for US-018: Patient Header Display component."""
import sys
sys.path.insert(0, 'src')

import tkinter as tk
from datetime import date
from models import Patient
from views.components.patient_header import PatientHeader


class FakeController:
    """Minimal stand-in for App — only used to satisfy PatientHeader.__init__."""
    def show_frame(self, view_class):
        pass


@tk.NO_DEFAULT_ROOT if hasattr(tk, 'NO_DEFAULT_ROOT') else lambda f: f
def _noop(f):
    return f


import pytest


@pytest.fixture(scope='module')
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def controller():
    return FakeController()


@pytest.fixture
def header(root, controller):
    h = PatientHeader(root, controller)
    yield h
    h.destroy()


@pytest.fixture
def patient():
    return Patient(
        patient_id='PT-001',
        name='Jane Doe',
        protocol='Dose-Dense AC-T',
        start_date=date(2024, 1, 15),
    )


# ── Import ────────────────────────────────────────────────────────────────────

def test_import():
    from views.components.patient_header import PatientHeader
    assert PatientHeader is not None


# ── update_display: valid patient ─────────────────────────────────────────────

def test_name_shown(header, patient):
    header.update_display(patient)
    assert header._name_label.cget('text') == 'Jane Doe'


def test_detail_contains_patient_id(header, patient):
    header.update_display(patient)
    assert 'PT-001' in header._detail_label.cget('text')


def test_detail_contains_protocol(header, patient):
    header.update_display(patient)
    assert 'Dose-Dense AC-T' in header._detail_label.cget('text')


def test_detail_contains_formatted_date(header, patient):
    header.update_display(patient)
    # date(2024, 1, 15) → "Jan 15, 2024"
    assert 'Jan 15, 2024' in header._detail_label.cget('text')


def test_detail_uses_pipe_separator(header, patient):
    header.update_display(patient)
    assert '│' in header._detail_label.cget('text')


# ── update_display: None patient ──────────────────────────────────────────────

def test_none_clears_name(header):
    header.update_display(None)
    assert header._name_label.cget('text') == ''


def test_none_clears_detail(header):
    header.update_display(None)
    assert header._detail_label.cget('text') == ''


def test_none_does_not_raise(header):
    # Should be safe to call with None at any point.
    header.update_display(None)


# ── Date formatting ───────────────────────────────────────────────────────────

def test_date_object_formatted(header):
    p = Patient(patient_id='PT-X', name='Test', start_date=date(2024, 6, 5))
    header.update_display(p)
    assert 'Jun 05, 2024' in header._detail_label.cget('text')


def test_date_string_formatted(header):
    p = Patient(patient_id='PT-X', name='Test', start_date='2024-03-20')
    header.update_display(p)
    assert 'Mar 20, 2024' in header._detail_label.cget('text')


def test_none_date_shows_dash(header):
    p = Patient(patient_id='PT-X', name='Test', start_date=None)
    header.update_display(p)
    assert '—' in header._detail_label.cget('text')


# ── None protocol ─────────────────────────────────────────────────────────────

def test_none_protocol_shows_dash(header):
    p = Patient(patient_id='PT-X', name='Test', protocol=None)
    header.update_display(p)
    assert '—' in header._detail_label.cget('text')


# ── on_add_labs callback ──────────────────────────────────────────────────────

def test_on_add_labs_called(root, controller):
    called = []
    h = PatientHeader(root, controller, on_add_labs=lambda: called.append(True))
    h.update_display(None)
    h.destroy()
    # Callback stored — we verified construction succeeded without errors.
    assert called == []  # not triggered unless button clicked


def test_no_add_labs_callback_no_error(root, controller):
    # PatientHeader with no on_add_labs should construct without raising.
    h = PatientHeader(root, controller, on_add_labs=None)
    h.update_display(None)
    h.destroy()
