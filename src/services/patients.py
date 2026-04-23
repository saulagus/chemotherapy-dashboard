"""Patient mutation service.

Every create / update / soft-delete / restore goes through this module. Each
mutation pairs its SQL write with an audit_log row in the same transaction —
on any error both are rolled back together.
"""

from datetime import datetime
from typing import Optional

import models
from models import Patient
from services.audit import write_audit


def create_patient(conn, patient: Patient, actor: Optional[str] = None) -> Patient:
    """Insert a patient and write a matching 'create' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO patients
               (patient_id, name, age, diagnosis_date, start_date, protocol,
                total_cycles, dose_density)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (patient.patient_id, patient.name, patient.age,
             patient.diagnosis_date, patient.start_date, patient.protocol,
             patient.total_cycles, patient.dose_density),
        )
        patient.id = cursor.lastrowid
        write_audit(conn, 'patient', patient.id, 'create',
                    after=patient, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return patient


def update_patient(conn, patient: Patient, actor: Optional[str] = None) -> Patient:
    """Update a patient and write a matching 'update' audit row."""
    if patient.id is None:
        raise ValueError("update_patient requires patient.id")
    before = models.get_patient_by_db_id(conn, patient.id, include_deleted=True)
    if before is None:
        raise LookupError(f"patient id={patient.id} not found")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE patients
               SET patient_id=?, name=?, age=?, diagnosis_date=?, start_date=?,
                   protocol=?, total_cycles=?, dose_density=?
               WHERE id=?''',
            (patient.patient_id, patient.name, patient.age,
             patient.diagnosis_date, patient.start_date, patient.protocol,
             patient.total_cycles, patient.dose_density, patient.id),
        )
        write_audit(conn, 'patient', patient.id, 'update',
                    before=before, after=patient, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return patient


def soft_delete_patient(
    conn, db_id: int, actor: Optional[str] = None
) -> None:
    """Mark a patient deleted (sets deleted_at). Writes a 'soft_delete' audit row."""
    before = models.get_patient_by_db_id(conn, db_id, include_deleted=True)
    if before is None:
        raise LookupError(f"patient id={db_id} not found")
    if before.deleted_at is not None:
        return  # already soft-deleted; no-op

    now = datetime.now()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE patients SET deleted_at=? WHERE id=?', (now, db_id)
        )
        write_audit(conn, 'patient', db_id, 'soft_delete',
                    before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def restore_patient(
    conn, db_id: int, actor: Optional[str] = None
) -> None:
    """Clear a patient's deleted_at. Writes a 'restore' audit row."""
    before = models.get_patient_by_db_id(conn, db_id, include_deleted=True)
    if before is None:
        raise LookupError(f"patient id={db_id} not found")
    if before.deleted_at is None:
        return  # not deleted; no-op

    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE patients SET deleted_at=NULL WHERE id=?', (db_id,))
        after = models.get_patient_by_db_id(conn, db_id)
        write_audit(conn, 'patient', db_id, 'restore',
                    before=before, after=after, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
