"""Patient mutation service.

Every create / update / soft-delete / restore goes through this module. Each
mutation pairs its SQL write with an audit_log row in the same transaction —
on any error both are rolled back together.
"""

from datetime import datetime
from typing import List, Optional

import models
from models import Patient, _row_to_patient, _PATIENT_COLUMNS
from services.audit import write_audit


def list_patients(
    conn,
    search: str = '',
    sort_by: str = 'name',
    sort_dir: str = 'asc',
    phase_filter: Optional[str] = None,
) -> List[Patient]:
    """Return patients matching search/filter/sort criteria. Soft-deleted excluded.

    search: substring match on patient_id or name (case-insensitive).
    sort_by: 'name' | 'patient_id' | 'age' | 'diagnosis_date'.
    sort_dir: 'asc' | 'desc'.
    phase_filter: None (all) | 'AC' | 'T' | 'Completed'.
    """
    allowed_sort = {'name', 'patient_id', 'age', 'diagnosis_date'}
    col = sort_by if sort_by in allowed_sort else 'name'
    direction = 'DESC' if sort_dir.lower() == 'desc' else 'ASC'

    clauses = ['deleted_at IS NULL']
    params: list = []

    if search:
        clauses.append('(LOWER(patient_id) LIKE ? OR LOWER(name) LIKE ?)')
        term = f'%{search.lower()}%'
        params.extend([term, term])

    if phase_filter == 'Completed':
        clauses.append(
            '''id IN (SELECT patient_id FROM cycles
                      WHERE status = 'completed'
                      GROUP BY patient_id HAVING COUNT(*) >= 8)'''
        )
    elif phase_filter in ('AC', 'T'):
        if phase_filter == 'AC':
            clauses.append(
                '''id NOT IN (SELECT patient_id FROM cycles
                              WHERE status = 'completed'
                              GROUP BY patient_id HAVING COUNT(*) >= 8)
                   AND (SELECT COALESCE(MAX(cycle_number), 0) FROM cycles
                        WHERE cycles.patient_id = patients.id
                              AND status = 'completed') < 5'''
            )
        else:
            clauses.append(
                '''id NOT IN (SELECT patient_id FROM cycles
                              WHERE status = 'completed'
                              GROUP BY patient_id HAVING COUNT(*) >= 8)
                   AND (SELECT COALESCE(MAX(cycle_number), 0) FROM cycles
                        WHERE cycles.patient_id = patients.id
                              AND status = 'completed') >= 4'''
            )

    where = ' AND '.join(clauses)
    sql = f'SELECT {_PATIENT_COLUMNS} FROM patients WHERE {where} ORDER BY {col} {direction}'

    cursor = conn.cursor()
    cursor.execute(sql, params)
    return [_row_to_patient(row) for row in cursor.fetchall()]


def create_patient(conn, patient: Patient, actor: Optional[str] = None) -> Patient:
    """Insert a patient and write a matching 'create' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO patients
               (patient_id, name, age, diagnosis_date, start_date, protocol,
                total_cycles, dose_density,
                prior_anthracycline_dose_mg_per_m2, prior_anthracycline_agent)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (patient.patient_id, patient.name, patient.age,
             patient.diagnosis_date, patient.start_date, patient.protocol,
             patient.total_cycles, patient.dose_density,
             patient.prior_anthracycline_dose_mg_per_m2,
             patient.prior_anthracycline_agent),
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
                   protocol=?, total_cycles=?, dose_density=?,
                   prior_anthracycline_dose_mg_per_m2=?, prior_anthracycline_agent=?
               WHERE id=?''',
            (patient.patient_id, patient.name, patient.age,
             patient.diagnosis_date, patient.start_date, patient.protocol,
             patient.total_cycles, patient.dose_density,
             patient.prior_anthracycline_dose_mg_per_m2,
             patient.prior_anthracycline_agent, patient.id),
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
