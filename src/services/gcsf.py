"""G-CSF administration service (US-029).

Every mutation writes an audit_log row in the same transaction.
Records are soft-deleted (deleted_at set) so history is preserved.

Audit actions used:
  gcsf_created  — new G-CSF administration logged
  gcsf_updated  — existing record edited
  gcsf_deleted  — record soft-deleted
"""

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import List, Optional

from services.audit import write_audit


@dataclass
class GcsfAdmin:
    patient_id: str           # string patient ID e.g. 'PT-001'
    agent: str                # from config vocab
    admin_date: str           # ISO 'YYYY-MM-DD'
    cycle_id: Optional[int] = None
    dose_mg: Optional[float] = None
    prophylaxis_type: Optional[str] = None  # 'primary' | 'secondary' | 'therapeutic'
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    deleted_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_COLUMNS = (
    'id, patient_id, cycle_id, agent, admin_date, '
    'dose_mg, prophylaxis_type, notes, created_at, deleted_at'
)


def _row_to_gcsf(row) -> GcsfAdmin:
    return GcsfAdmin(
        id=row[0],
        patient_id=row[1],
        cycle_id=row[2],
        agent=row[3],
        admin_date=row[4],
        dose_mg=row[5],
        prophylaxis_type=row[6],
        notes=row[7],
        created_at=row[8],
        deleted_at=row[9],
    )


def _get_by_id(conn, gcsf_id: int) -> Optional[GcsfAdmin]:
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM gcsf_admin WHERE id = ?',
        (gcsf_id,),
    )
    row = cursor.fetchone()
    return _row_to_gcsf(row) if row else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_gcsf(
    conn,
    gcsf: GcsfAdmin,
    actor: Optional[str] = None,
) -> GcsfAdmin:
    """Insert a G-CSF administration record and write 'gcsf_created' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO gcsf_admin
               (patient_id, cycle_id, agent, admin_date, dose_mg, prophylaxis_type, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (gcsf.patient_id, gcsf.cycle_id, gcsf.agent, gcsf.admin_date,
             gcsf.dose_mg, gcsf.prophylaxis_type, gcsf.notes),
        )
        gcsf.id = cursor.lastrowid
        write_audit(conn, 'gcsf_admin', gcsf.id, 'gcsf_created', after=gcsf, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return gcsf


def update_gcsf(
    conn,
    gcsf: GcsfAdmin,
    actor: Optional[str] = None,
) -> GcsfAdmin:
    """Update a G-CSF record and write 'gcsf_updated' audit row."""
    if gcsf.id is None:
        raise ValueError("update_gcsf requires gcsf.id")
    before = _get_by_id(conn, gcsf.id)
    if before is None:
        raise LookupError(f"gcsf_admin id={gcsf.id} not found")
    if before.deleted_at is not None:
        raise ValueError(f"gcsf_admin id={gcsf.id} is soft-deleted")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE gcsf_admin
               SET agent=?, admin_date=?, dose_mg=?, prophylaxis_type=?, cycle_id=?, notes=?
               WHERE id=?''',
            (gcsf.agent, gcsf.admin_date, gcsf.dose_mg, gcsf.prophylaxis_type,
             gcsf.cycle_id, gcsf.notes, gcsf.id),
        )
        write_audit(conn, 'gcsf_admin', gcsf.id, 'gcsf_updated',
                    before=before, after=gcsf, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return gcsf


def delete_gcsf(
    conn,
    gcsf_id: int,
    actor: Optional[str] = None,
) -> None:
    """Soft-delete a G-CSF record. Writes 'gcsf_deleted' audit row."""
    before = _get_by_id(conn, gcsf_id)
    if before is None:
        raise LookupError(f"gcsf_admin id={gcsf_id} not found")
    if before.deleted_at is not None:
        return  # already soft-deleted; no-op

    now = datetime.now().isoformat()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE gcsf_admin SET deleted_at=? WHERE id=?',
            (now, gcsf_id),
        )
        write_audit(conn, 'gcsf_admin', gcsf_id, 'gcsf_deleted', before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def list_gcsf(
    conn,
    patient_id: str,
    include_deleted: bool = False,
) -> List[GcsfAdmin]:
    """Return all G-CSF records for a patient, newest date first."""
    cursor = conn.cursor()
    where = (
        'WHERE patient_id = ?'
        if include_deleted
        else 'WHERE patient_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM gcsf_admin {where} '
        'ORDER BY admin_date DESC, id DESC',
        (patient_id,),
    )
    return [_row_to_gcsf(row) for row in cursor.fetchall()]


def list_gcsf_for_cycle(
    conn,
    cycle_id: int,
    include_deleted: bool = False,
) -> List[GcsfAdmin]:
    """Return all G-CSF records for a specific cycle, newest first."""
    cursor = conn.cursor()
    where = (
        'WHERE cycle_id = ?'
        if include_deleted
        else 'WHERE cycle_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM gcsf_admin {where} ORDER BY admin_date DESC, id DESC',
        (cycle_id,),
    )
    return [_row_to_gcsf(row) for row in cursor.fetchall()]


def latest_gcsf(
    conn,
    patient_id: str,
) -> Optional[GcsfAdmin]:
    """Return the most recent non-deleted G-CSF record for a patient, or None."""
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM gcsf_admin '
        'WHERE patient_id = ? AND deleted_at IS NULL '
        'ORDER BY admin_date DESC, id DESC LIMIT 1',
        (patient_id,),
    )
    row = cursor.fetchone()
    return _row_to_gcsf(row) if row else None


def gcsf_dates_for_patient(
    conn,
    patient_id: str,
    window_days: int = 7,
) -> List[date]:
    """Return all admin dates expanded to [admin_date, admin_date + window_days].

    Used by the ANC trend chart to mark G-CSF-stimulated readings.
    Returns a flat list of date objects covering the stimulated window.
    """
    records = list_gcsf(conn, patient_id)
    stimulated: List[date] = []
    for rec in records:
        d = rec.admin_date
        if hasattr(d, 'date'):
            d = d.date()
        elif isinstance(d, str):
            d = date.fromisoformat(d)
        for offset in range(window_days + 1):
            stimulated.append(d + timedelta(days=offset))
    return stimulated
