"""LVEF assessment service (US-025).

Every mutation writes an audit_log row in the same transaction.
Assessments are soft-deleted (deleted_at set) rather than hard-deleted so
the history is preserved for cardiotoxicity review.

Audit actions used:
  lvef_created  — new assessment inserted
  lvef_updated  — existing assessment edited
  lvef_deleted  — assessment soft-deleted
"""

from datetime import datetime
from typing import List, Optional

from models import LvefAssessment
from services.audit import write_audit


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_COLUMNS = (
    'id, patient_id, assessment_date, lvef_percent, modality, '
    'context, notes, created_at, deleted_at'
)


def _row_to_assessment(row) -> LvefAssessment:
    return LvefAssessment(
        id=row[0],
        patient_id=row[1],
        assessment_date=row[2],
        lvef_percent=row[3],
        modality=row[4],
        context=row[5],
        notes=row[6],
        created_at=row[7],
        deleted_at=row[8],
    )


def _get_by_id(conn, assessment_id: int) -> Optional[LvefAssessment]:
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM lvef_assessment WHERE id = ?',
        (assessment_id,),
    )
    row = cursor.fetchone()
    return _row_to_assessment(row) if row else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_lvef(
    conn,
    assessment: LvefAssessment,
    actor: Optional[str] = None,
) -> LvefAssessment:
    """Insert an LVEF assessment and write a 'lvef_created' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO lvef_assessment
               (patient_id, assessment_date, lvef_percent, modality,
                context, notes)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (assessment.patient_id, assessment.assessment_date,
             assessment.lvef_percent, assessment.modality,
             assessment.context, assessment.notes),
        )
        assessment.id = cursor.lastrowid
        write_audit(conn, 'lvef_assessment', assessment.id, 'lvef_created',
                    after=assessment, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return assessment


def update_lvef(
    conn,
    assessment: LvefAssessment,
    actor: Optional[str] = None,
) -> LvefAssessment:
    """Update an LVEF assessment and write a 'lvef_updated' audit row."""
    if assessment.id is None:
        raise ValueError("update_lvef requires assessment.id")
    before = _get_by_id(conn, assessment.id)
    if before is None:
        raise LookupError(f"lvef_assessment id={assessment.id} not found")
    if before.deleted_at is not None:
        raise ValueError(f"lvef_assessment id={assessment.id} is soft-deleted; restore first")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE lvef_assessment
               SET assessment_date=?, lvef_percent=?, modality=?,
                   context=?, notes=?
               WHERE id=?''',
            (assessment.assessment_date, assessment.lvef_percent,
             assessment.modality, assessment.context, assessment.notes,
             assessment.id),
        )
        write_audit(conn, 'lvef_assessment', assessment.id, 'lvef_updated',
                    before=before, after=assessment, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return assessment


def delete_lvef(
    conn,
    assessment_id: int,
    actor: Optional[str] = None,
) -> None:
    """Soft-delete an LVEF assessment by setting deleted_at. Writes 'lvef_deleted' audit row."""
    before = _get_by_id(conn, assessment_id)
    if before is None:
        raise LookupError(f"lvef_assessment id={assessment_id} not found")
    if before.deleted_at is not None:
        return  # already soft-deleted; no-op

    now = datetime.now()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE lvef_assessment SET deleted_at=? WHERE id=?',
            (now, assessment_id),
        )
        write_audit(conn, 'lvef_assessment', assessment_id, 'lvef_deleted',
                    before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def list_lvef(
    conn,
    patient_id: int,
    include_deleted: bool = False,
) -> List[LvefAssessment]:
    """Return all LVEF assessments for a patient, newest first.

    Excludes soft-deleted rows by default.
    """
    cursor = conn.cursor()
    where = (
        'WHERE patient_id = ?'
        if include_deleted
        else 'WHERE patient_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM lvef_assessment {where} '
        'ORDER BY assessment_date DESC, id DESC',
        (patient_id,),
    )
    return [_row_to_assessment(row) for row in cursor.fetchall()]


def get_baseline_lvef(
    conn,
    patient_id: int,
) -> Optional[LvefAssessment]:
    """Return the most recent non-deleted baseline assessment, or None."""
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM lvef_assessment '
        "WHERE patient_id = ? AND context = 'baseline' AND deleted_at IS NULL "
        'ORDER BY assessment_date DESC, id DESC LIMIT 1',
        (patient_id,),
    )
    row = cursor.fetchone()
    return _row_to_assessment(row) if row else None
