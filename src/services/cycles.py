"""Cycle mutation service.

Cycles are hard-deleted (unlike patients). The audit_log row written in the
same transaction preserves the full before-state, so history remains queryable
after a destructive delete.
"""

from typing import Optional

from models import Cycle, get_cycles_by_patient
from services.audit import write_audit


def _get_cycle_by_id(conn, cycle_id: int) -> Optional[Cycle]:
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, cycle_number, phase, planned_date, actual_date,
                  status, dose_percent, dose_reason, notes
           FROM cycles WHERE id = ?''',
        (cycle_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Cycle(
        id=row[0], patient_id=row[1], cycle_number=row[2], phase=row[3],
        planned_date=row[4], actual_date=row[5], status=row[6],
        dose_percent=row[7], dose_reason=row[8], notes=row[9],
    )


def create_cycle(conn, cycle: Cycle, actor: Optional[str] = None) -> Cycle:
    """Insert a cycle and write a matching 'create' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO cycles
               (patient_id, cycle_number, phase, planned_date, actual_date,
                status, dose_percent, dose_reason, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (cycle.patient_id, cycle.cycle_number, cycle.phase,
             cycle.planned_date, cycle.actual_date, cycle.status,
             cycle.dose_percent, cycle.dose_reason, cycle.notes),
        )
        cycle.id = cursor.lastrowid
        write_audit(conn, 'cycle', cycle.id, 'create', after=cycle, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return cycle


def update_cycle(conn, cycle: Cycle, actor: Optional[str] = None) -> Cycle:
    """Update a cycle and write a matching 'update' audit row."""
    if cycle.id is None:
        raise ValueError("update_cycle requires cycle.id")
    before = _get_cycle_by_id(conn, cycle.id)
    if before is None:
        raise LookupError(f"cycle id={cycle.id} not found")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE cycles
               SET cycle_number=?, phase=?, planned_date=?, actual_date=?,
                   status=?, dose_percent=?, dose_reason=?, notes=?
               WHERE id=?''',
            (cycle.cycle_number, cycle.phase, cycle.planned_date,
             cycle.actual_date, cycle.status, cycle.dose_percent,
             cycle.dose_reason, cycle.notes, cycle.id),
        )
        write_audit(conn, 'cycle', cycle.id, 'update',
                    before=before, after=cycle, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return cycle


def delete_cycle(conn, cycle_id: int, actor: Optional[str] = None) -> None:
    """Hard-delete a cycle. Writes a 'delete' audit row preserving before-state."""
    before = _get_cycle_by_id(conn, cycle_id)
    if before is None:
        raise LookupError(f"cycle id={cycle_id} not found")

    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM cycles WHERE id=?', (cycle_id,))
        write_audit(conn, 'cycle', cycle_id, 'delete', before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
