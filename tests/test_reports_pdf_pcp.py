"""Tests for reports/pdf_pcp.py (Sprint 9 — US-035)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import make_config, simple_report_data
from reports.pdf_pcp import _build_toxicity_paragraph, _guidance_for_rule, render


def test_pcp_pdf_renders_pdf_bytes():
    pdf = render(simple_report_data(), make_config())

    assert pdf.startswith(b'%PDF')
    assert len(pdf) > 1000


def test_pcp_pdf_is_byte_stable():
    data = simple_report_data()
    cfg = make_config()

    assert render(data, cfg) == render(data, cfg)


def test_pcp_referral_guidance_known_rule():
    assert 'Delay next cycle' in _guidance_for_rule('anc_below_threshold')


def test_pcp_toxicity_empty_state():
    data = simple_report_data()
    data.neuropathy_effective_grade = None
    data.reaction_latest = None
    data.symptom_entries = []

    assert _build_toxicity_paragraph(data) == ['No significant toxicity on record.']
