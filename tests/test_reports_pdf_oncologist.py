"""Tests for reports/pdf_oncologist.py (Sprint 9 — US-035)."""

import base64
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import make_config, simple_report_data
from reports.pdf_oncologist import _get_all_labs_for_report, render


_ONE_PIXEL_PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII='
)


def test_oncologist_pdf_renders_pdf_bytes():
    pdf = render(simple_report_data(), make_config())

    assert pdf.startswith(b'%PDF')
    assert len(pdf) > 1000


def test_oncologist_pdf_is_byte_stable():
    data = simple_report_data()
    cfg = make_config()

    assert render(data, cfg) == render(data, cfg)


def test_oncologist_chart_receives_report_lab_history(monkeypatch):
    captured = {}

    def fake_chart(labs, gcsf_dates, size_in, config):
        captured['labs'] = labs
        captured['gcsf_dates'] = gcsf_dates
        return _ONE_PIXEL_PNG

    monkeypatch.setattr('reports.chart_png.render_anc_trend', fake_chart)

    data = simple_report_data()
    render(data, make_config())

    assert captured['labs'] == data.lab_history
    assert captured['gcsf_dates'] == data.gcsf_dates


def test_get_all_labs_for_report_handles_missing_history():
    assert _get_all_labs_for_report(object()) == []
