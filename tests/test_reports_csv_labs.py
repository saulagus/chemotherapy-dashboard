"""Tests for reports/csv_labs.py (Sprint 9 — US-037)."""

import csv
import io
import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from helpers_reports import TODAY, make_config, make_conn, seed_report_patient
from reports.csv_labs import build_csv_filename, write_csv


@pytest.fixture
def conn():
    connection = make_conn()
    yield connection
    connection.close()


@pytest.fixture
def cfg():
    return make_config()


def _rows(csv_bytes):
    return list(csv.DictReader(io.StringIO(csv_bytes.decode('utf-8'))))


def test_write_csv_uses_configured_columns_and_round_trips(conn, cfg):
    seeded = seed_report_patient(conn)

    rows = _rows(write_csv(conn, seeded.patient.patient_id, cfg))

    assert list(rows[0].keys()) == cfg.reports.csv.labs.columns
    assert len(rows) == 2
    assert rows[0]['date'] == '2026-01-08'
    assert rows[1]['anc'] == '1.1'


def test_write_csv_applies_date_range(conn, cfg):
    seeded = seed_report_patient(conn)

    rows = _rows(write_csv(
        conn, seeded.patient.patient_id, cfg,
        from_date=date(2026, 1, 10),
        to_date=date(2026, 1, 20),
    ))

    assert [row['date'] for row in rows] == ['2026-01-16']


def test_write_csv_marks_gcsf_window(conn, cfg):
    seeded = seed_report_patient(conn)

    rows = _rows(write_csv(conn, seeded.patient.patient_id, cfg))

    assert rows[0]['gcsf_within_7d'] == 'false'
    assert rows[1]['gcsf_within_7d'] == 'true'


def test_write_csv_soft_deleted_labs_excluded_when_column_exists(conn, cfg):
    seeded = seed_report_patient(conn)
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE labs ADD COLUMN deleted_at TIMESTAMP')
    cursor.execute('UPDATE labs SET deleted_at=? WHERE id=?',
                   ('2026-01-18T00:00:00', seeded.lab1.id))
    conn.commit()

    rows = _rows(write_csv(conn, seeded.patient.patient_id, cfg))

    assert [row['date'] for row in rows] == ['2026-01-16']


def test_write_csv_can_include_soft_deleted_labs_when_column_exists(conn, cfg):
    seeded = seed_report_patient(conn)
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE labs ADD COLUMN deleted_at TIMESTAMP')
    cursor.execute('UPDATE labs SET deleted_at=? WHERE id=?',
                   ('2026-01-18T00:00:00', seeded.lab1.id))
    conn.commit()
    cfg.reports.csv.labs.include_soft_deleted = True

    rows = _rows(write_csv(conn, seeded.patient.patient_id, cfg))

    assert [row['date'] for row in rows] == ['2026-01-08', '2026-01-16']


def test_write_csv_unknown_patient_returns_header_only(conn, cfg):
    rows = write_csv(conn, 'PT-NOPE', cfg).decode('utf-8').splitlines()

    assert rows == [','.join(cfg.reports.csv.labs.columns)]


def test_build_csv_filename_uses_config_pattern(cfg):
    assert build_csv_filename('PT-RPT1', cfg, TODAY) == 'labs_PT-RPT1_2026_01_20.csv'
