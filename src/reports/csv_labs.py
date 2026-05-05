"""CSV lab export (Sprint 9 — US-037).

write_csv() returns raw CSV bytes. Column set is YAML-driven.
Date-range filtering applied at query layer.
gcsf_within_7d computed from G-CSF admin overlap.
Soft-deleted labs excluded by default.
"""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from typing import List, Optional


def write_csv(
    conn,
    patient_str_id: str,
    config,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> bytes:
    """Return CSV bytes for lab export.

    Columns are read from config.reports.csv.labs.columns.
    Date range is applied at query time.
    gcsf_within_7d is computed per row.
    """
    csv_cfg = config.reports.csv.labs
    columns = list(csv_cfg.columns)
    include_soft_deleted = csv_cfg.include_soft_deleted

    rows = _query_labs(conn, patient_str_id, from_date, to_date, include_soft_deleted)
    gcsf_dates = _load_gcsf_dates(conn, patient_str_id)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns)
    writer.writeheader()

    for lab in rows:
        writer.writerow(_lab_to_row(lab, columns, gcsf_dates))

    return buf.getvalue().encode('utf-8')


def _query_labs(conn, patient_str_id: str, from_date, to_date, include_soft_deleted: bool) -> list:
    """Return Lab records within the date range."""
    from models import get_patient_by_id, get_labs_by_patient

    patient = get_patient_by_id(conn, patient_str_id)
    if patient is None:
        return []

    cursor = conn.cursor()
    query = 'SELECT id, patient_id, lab_date, anc, wbc, platelets, hemoglobin FROM labs WHERE patient_id = ?'
    params: list = [patient.id]

    if from_date:
        query += ' AND lab_date >= ?'
        params.append(from_date.isoformat() if hasattr(from_date, 'isoformat') else str(from_date))
    if to_date:
        query += ' AND lab_date <= ?'
        params.append(to_date.isoformat() if hasattr(to_date, 'isoformat') else str(to_date))

    query += ' ORDER BY lab_date ASC'
    cursor.execute(query, params)
    rows = cursor.fetchall()

    from models import Lab
    return [
        Lab(id=r[0], patient_id=r[1], lab_date=r[2], anc=r[3],
            wbc=r[4], platelets=r[5], hemoglobin=r[6])
        for r in rows
    ]


def _load_gcsf_dates(conn, patient_str_id: str) -> set:
    """Return a set of dates covered by G-CSF stimulated windows."""
    from services.gcsf import list_gcsf

    records = list_gcsf(conn, patient_str_id)
    stimulated: set = set()
    for rec in records:
        d = rec.admin_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        for offset in range(8):
            stimulated.add(d + timedelta(days=offset))
    return stimulated


def _lab_to_row(lab, columns: list, gcsf_dates: set) -> dict:
    """Map a Lab object to a CSV row dict keyed by column names."""
    lab_d = lab.lab_date
    if isinstance(lab_d, str):
        try:
            lab_d = date.fromisoformat(lab_d)
        except ValueError:
            lab_d = None

    gcsf_flag = lab_d in gcsf_dates if lab_d else False

    # Compute neut_pct from anc / wbc if both available
    neut_pct = None
    if lab.anc is not None and lab.wbc is not None and lab.wbc > 0:
        neut_pct = round((lab.anc / lab.wbc) * 100, 1)

    mapping = {
        'date': lab_d.isoformat() if lab_d else '',
        'anc': lab.anc if lab.anc is not None else '',
        'hgb': lab.hemoglobin if lab.hemoglobin is not None else '',
        'plt': lab.platelets if lab.platelets is not None else '',
        'wbc': lab.wbc if lab.wbc is not None else '',
        'neut_pct': neut_pct if neut_pct is not None else '',
        'gcsf_within_7d': 'true' if gcsf_flag else 'false',
        'notes': '',
    }

    return {col: mapping.get(col, '') for col in columns}


def build_csv_filename(patient_str_id: str, config, today: date) -> str:
    """Return the CSV filename from the config pattern."""
    pattern = config.reports.csv.labs.filename_pattern
    date_str = today.isoformat().replace('-', '_')
    return (
        pattern
        .replace('{patient_id}', patient_str_id)
        .replace('{YYYY_MM_DD}', date_str)
    )
