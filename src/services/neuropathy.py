"""Neuropathy assessment service (US-027).

Every mutation writes an audit_log row in the same transaction.
Assessments are soft-deleted (deleted_at set) so history is preserved.

Audit actions used:
  neuropathy_created  — new assessment inserted
  neuropathy_updated  — existing assessment edited
  neuropathy_deleted  — assessment soft-deleted
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.audit import write_audit


@dataclass
class NeuropathyAssessment:
    patient_id: str
    assessment_date: str          # ISO 'YYYY-MM-DD'
    sensory_grade: int
    motor_grade: int
    ctcae_version: str = '5.0'
    cycle_id: Optional[int] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    deleted_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_COLUMNS = (
    'id, patient_id, cycle_id, assessment_date, '
    'sensory_grade, motor_grade, ctcae_version, notes, created_at, deleted_at'
)


def _row_to_assessment(row) -> NeuropathyAssessment:
    return NeuropathyAssessment(
        id=row[0],
        patient_id=row[1],
        cycle_id=row[2],
        assessment_date=row[3],
        sensory_grade=row[4],
        motor_grade=row[5],
        ctcae_version=row[6],
        notes=row[7],
        created_at=row[8],
        deleted_at=row[9],
    )


def _get_by_id(conn, assessment_id: int) -> Optional[NeuropathyAssessment]:
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM neuropathy_assessment WHERE id = ?',
        (assessment_id,),
    )
    row = cursor.fetchone()
    return _row_to_assessment(row) if row else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_neuropathy(
    conn,
    assessment: NeuropathyAssessment,
    actor: Optional[str] = None,
) -> NeuropathyAssessment:
    """Insert a neuropathy assessment and write a 'neuropathy_created' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO neuropathy_assessment
               (patient_id, cycle_id, assessment_date,
                sensory_grade, motor_grade, ctcae_version, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (assessment.patient_id, assessment.cycle_id, assessment.assessment_date,
             assessment.sensory_grade, assessment.motor_grade,
             assessment.ctcae_version, assessment.notes),
        )
        assessment.id = cursor.lastrowid
        write_audit(conn, 'neuropathy_assessment', assessment.id,
                    'neuropathy_created', after=assessment, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return assessment


def update_neuropathy(
    conn,
    assessment: NeuropathyAssessment,
    actor: Optional[str] = None,
) -> NeuropathyAssessment:
    """Update a neuropathy assessment and write a 'neuropathy_updated' audit row."""
    if assessment.id is None:
        raise ValueError("update_neuropathy requires assessment.id")
    before = _get_by_id(conn, assessment.id)
    if before is None:
        raise LookupError(f"neuropathy_assessment id={assessment.id} not found")
    if before.deleted_at is not None:
        raise ValueError(f"neuropathy_assessment id={assessment.id} is soft-deleted")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE neuropathy_assessment
               SET assessment_date=?, sensory_grade=?, motor_grade=?,
                   ctcae_version=?, cycle_id=?, notes=?
               WHERE id=?''',
            (assessment.assessment_date, assessment.sensory_grade,
             assessment.motor_grade, assessment.ctcae_version,
             assessment.cycle_id, assessment.notes, assessment.id),
        )
        write_audit(conn, 'neuropathy_assessment', assessment.id,
                    'neuropathy_updated', before=before, after=assessment, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return assessment


def delete_neuropathy(
    conn,
    assessment_id: int,
    actor: Optional[str] = None,
) -> None:
    """Soft-delete a neuropathy assessment. Writes 'neuropathy_deleted' audit row."""
    before = _get_by_id(conn, assessment_id)
    if before is None:
        raise LookupError(f"neuropathy_assessment id={assessment_id} not found")
    if before.deleted_at is not None:
        return  # already soft-deleted; no-op

    now = datetime.now().isoformat()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE neuropathy_assessment SET deleted_at=? WHERE id=?',
            (now, assessment_id),
        )
        write_audit(conn, 'neuropathy_assessment', assessment_id,
                    'neuropathy_deleted', before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def list_neuropathy(
    conn,
    patient_id: str,
    include_deleted: bool = False,
) -> List[NeuropathyAssessment]:
    """Return all neuropathy assessments for a patient, newest first."""
    cursor = conn.cursor()
    where = (
        'WHERE patient_id = ?'
        if include_deleted
        else 'WHERE patient_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM neuropathy_assessment {where} '
        'ORDER BY assessment_date DESC, id DESC',
        (patient_id,),
    )
    return [_row_to_assessment(row) for row in cursor.fetchall()]


def latest_neuropathy(
    conn,
    patient_id: str,
) -> Optional[NeuropathyAssessment]:
    """Return the most recent non-deleted neuropathy assessment, or None."""
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM neuropathy_assessment '
        'WHERE patient_id = ? AND deleted_at IS NULL '
        'ORDER BY assessment_date DESC, id DESC LIMIT 1',
        (patient_id,),
    )
    row = cursor.fetchone()
    return _row_to_assessment(row) if row else None
