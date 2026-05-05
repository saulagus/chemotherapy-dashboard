"""Export service — PDF and CSV exports with audit logging (Sprint 9).

Each export call:
1. Gathers data via reports.data.gather()
2. Dispatches to the appropriate renderer
3. Writes bytes to the target path
4. Writes one audit_log row
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ExportResult:
    path: str
    size_bytes: int
    audience: str
    audit_id: int


def export_patient_pdf(
    conn,
    patient_id: int,
    audience: str,
    target_path: str,
    config,
    today: date,
    actor: Optional[str] = None,
) -> ExportResult:
    """Render a PDF for the given audience and write it to target_path.

    audience: 'oncologist' | 'pcp' | 'patient'
    Writes one audit_log row with action='export_pdf'.
    """
    from reports.data import gather
    from services.audit import write_audit, current_actor

    data = gather(conn, patient_id, config, today)

    if audience == 'oncologist':
        from reports.pdf_oncologist import render
    elif audience == 'pcp':
        from reports.pdf_pcp import render
    elif audience == 'patient':
        from reports.pdf_patient import render
    else:
        raise ValueError(f"Unknown audience: {audience!r}")

    pdf_bytes = render(data, config)

    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, 'wb') as f:
        f.write(pdf_bytes)

    size = len(pdf_bytes)
    filename = os.path.basename(target_path)

    details = json.dumps({
        'audience': audience,
        'patient_id': data.patient_id,
        'filename': filename,
        'size_bytes': size,
    })

    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO audit_log (actor, entity, entity_id, action, before_json, after_json)
           VALUES (?, ?, ?, ?, NULL, ?)''',
        (actor or current_actor(), 'patient', patient_id, 'export_pdf', details),
    )
    audit_id = cursor.lastrowid
    conn.commit()

    return ExportResult(path=target_path, size_bytes=size, audience=audience, audit_id=audit_id)


def export_patient_csv(
    conn,
    patient_id: int,
    target_path: str,
    config,
    today: date,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    actor: Optional[str] = None,
) -> ExportResult:
    """Write a CSV labs export to target_path.

    Writes one audit_log row with action='export_csv'.
    """
    from reports.csv_labs import write_csv
    from services.audit import current_actor
    from models import get_patient_by_db_id

    patient = get_patient_by_db_id(conn, patient_id)
    patient_str_id = patient.patient_id if patient else str(patient_id)

    csv_bytes = write_csv(conn, patient_str_id, config, from_date=from_date, to_date=to_date)

    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, 'wb') as f:
        f.write(csv_bytes)

    size = len(csv_bytes)
    filename = os.path.basename(target_path)

    details = json.dumps({
        'patient_id': patient_str_id,
        'filename': filename,
        'size_bytes': size,
        'from_date': from_date.isoformat() if from_date else None,
        'to_date': to_date.isoformat() if to_date else None,
    })

    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO audit_log (actor, entity, entity_id, action, before_json, after_json)
           VALUES (?, ?, ?, ?, NULL, ?)''',
        (actor or current_actor(), 'patient', patient_id, 'export_csv', details),
    )
    audit_id = cursor.lastrowid
    conn.commit()

    return ExportResult(path=target_path, size_bytes=size, audience='csv', audit_id=audit_id)
