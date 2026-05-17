"""Tests for reports/pdf_print_dashboard.py (Sprint 9 — US-038)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import make_config, simple_report_data
from reports.pdf_print_dashboard import render


def test_print_dashboard_pdf_renders_pdf_bytes():
    pdf = render(simple_report_data(), make_config())

    assert pdf.startswith(b'%PDF')
    assert len(pdf) > 1000


def test_print_dashboard_pdf_is_byte_stable():
    data = simple_report_data()
    cfg = make_config()

    assert render(data, cfg) == render(data, cfg)


def test_print_dashboard_pdf_supports_landscape_orientation():
    cfg = make_config({'reports': {'print_dashboard': {'orientation': 'landscape'}}})

    pdf = render(simple_report_data(), cfg)

    assert pdf.startswith(b'%PDF')
