"""Tests for reports/pdf_patient.py (Sprint 9 — US-035)."""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import make_config, simple_report_data
from reports.pdf_patient import _draw_plain_checklist, render


def test_patient_pdf_renders_pdf_bytes():
    pdf = render(simple_report_data(), make_config())

    assert pdf.startswith(b'%PDF')
    assert len(pdf) > 1000


def test_patient_pdf_is_byte_stable():
    data = simple_report_data()
    cfg = make_config()

    assert render(data, cfg) == render(data, cfg)


def test_patient_pdf_handles_no_labs():
    data = simple_report_data()
    data.latest_labs = None

    pdf = render(data, make_config())

    assert pdf.startswith(b'%PDF')


def test_patient_plain_checklist_all_clear_path():
    calls = []

    class FakeCanvas:
        def setFillColorRGB(self, *args):
            calls.append(('color', args))

        def drawString(self, x, y, text):
            calls.append(('text', text))

    data = simple_report_data()
    data.last_checklist_result = SimpleNamespace(
        rules=[SimpleNamespace(rule_id='labs_stale', status='pass', message='Fresh')]
    )

    next_y = _draw_plain_checklist(FakeCanvas(), data, 36, 500)

    assert next_y == 489
    assert any('Everything looks on track' in text for kind, text in calls if kind == 'text')
