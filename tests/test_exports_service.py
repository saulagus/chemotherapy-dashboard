"""Tests for services/exports.py (Sprint 9 — US-035, US-037, US-038)."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import TODAY, make_config, make_conn, seed_report_patient
from services.audit import get_audit_for_entity
from services.exports import (
    export_patient_csv,
    export_patient_pdf,
    export_print_dashboard_pdf,
)


@pytest.fixture
def conn():
    connection = make_conn()
    yield connection
    connection.close()


@pytest.fixture
def cfg():
    return make_config()


def _latest_action(conn, patient_id, action):
    rows = get_audit_for_entity(conn, 'patient', patient_id)
    return next(row for row in rows if row['action'] == action)


def test_export_patient_pdf_writes_file_and_audit_row(conn, cfg, tmp_path):
    seeded = seed_report_patient(conn)
    path = tmp_path / 'summary.pdf'

    result = export_patient_pdf(
        conn, seeded.patient.id, 'oncologist', str(path), cfg, TODAY, actor='exporter'
    )

    assert path.read_bytes().startswith(b'%PDF')
    assert result.size_bytes == path.stat().st_size
    row = _latest_action(conn, seeded.patient.id, 'export_pdf')
    details = row['after']
    assert row['actor'] == 'exporter'
    assert details['audience'] == 'oncologist'
    assert details['filename'] == 'summary.pdf'
    assert details['size_bytes'] == result.size_bytes


def test_export_patient_pdf_rejects_unknown_audience(conn, cfg, tmp_path):
    seeded = seed_report_patient(conn)

    with pytest.raises(ValueError):
        export_patient_pdf(conn, seeded.patient.id, 'unknown', str(tmp_path / 'x.pdf'), cfg, TODAY)


def test_export_patient_csv_writes_file_and_audit_row(conn, cfg, tmp_path):
    seeded = seed_report_patient(conn)
    path = tmp_path / 'labs.csv'

    result = export_patient_csv(
        conn, seeded.patient.id, str(path), cfg, TODAY, actor='exporter'
    )

    assert path.read_text().splitlines()[0] == ','.join(cfg.reports.csv.labs.columns)
    assert result.size_bytes == path.stat().st_size
    row = _latest_action(conn, seeded.patient.id, 'export_csv')
    details = row['after']
    assert row['actor'] == 'exporter'
    assert details['filename'] == 'labs.csv'
    assert details['size_bytes'] == result.size_bytes


def test_export_print_dashboard_pdf_writes_file_and_audit_row(conn, cfg, tmp_path):
    seeded = seed_report_patient(conn)
    path = tmp_path / 'print.pdf'

    result = export_print_dashboard_pdf(
        conn, seeded.patient.id, str(path), cfg, TODAY, actor='printer'
    )

    assert path.read_bytes().startswith(b'%PDF')
    assert result.audience == 'print_dashboard'
    row = _latest_action(conn, seeded.patient.id, 'print_dashboard')
    details = row['after']
    assert row['actor'] == 'printer'
    assert details['filename'] == 'print.pdf'
    assert details['size_bytes'] == result.size_bytes
