"""Lab mutation service.

Like cycles, labs are hard-deleted. The audit_log row written in the same
transaction preserves the full before-state for history queries.
"""

from typing import Optional

from models import Lab
from services.audit import write_audit


def _get_lab_by_id(conn, lab_id: int) -> Optional[Lab]:
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, lab_date, anc, wbc, platelets, hemoglobin
           FROM labs WHERE id = ?''',
        (lab_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Lab(
        id=row[0], patient_id=row[1], lab_date=row[2], anc=row[3],
        wbc=row[4], platelets=row[5], hemoglobin=row[6],
    )


def create_lab(conn, lab: Lab, actor: Optional[str] = None) -> Lab:
    """Insert a lab and write a matching 'create' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO labs
               (patient_id, lab_date, anc, wbc, platelets, hemoglobin)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (lab.patient_id, lab.lab_date, lab.anc,
             lab.wbc, lab.platelets, lab.hemoglobin),
        )
        lab.id = cursor.lastrowid
        write_audit(conn, 'lab', lab.id, 'create', after=lab, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return lab


def update_lab(conn, lab: Lab, actor: Optional[str] = None) -> Lab:
    """Update a lab and write a matching 'update' audit row."""
    if lab.id is None:
        raise ValueError("update_lab requires lab.id")
    before = _get_lab_by_id(conn, lab.id)
    if before is None:
        raise LookupError(f"lab id={lab.id} not found")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE labs
               SET lab_date=?, anc=?, wbc=?, platelets=?, hemoglobin=?
               WHERE id=?''',
            (lab.lab_date, lab.anc, lab.wbc, lab.platelets, lab.hemoglobin, lab.id),
        )
        write_audit(conn, 'lab', lab.id, 'update',
                    before=before, after=lab, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return lab


def delete_lab(conn, lab_id: int, actor: Optional[str] = None) -> None:
    """Hard-delete a lab. Writes a 'delete' audit row preserving before-state."""
    before = _get_lab_by_id(conn, lab_id)
    if before is None:
        raise LookupError(f"lab id={lab_id} not found")

    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM labs WHERE id=?', (lab_id,))
        write_audit(conn, 'lab', lab_id, 'delete', before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
