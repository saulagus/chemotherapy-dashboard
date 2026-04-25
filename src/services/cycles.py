"""Cycle mutation service.

Cycles are hard-deleted (unlike patients). The audit_log row written in the
same transaction preserves the full before-state, so history remains queryable
after a destructive delete.
"""

from typing import Optional

from clinical.cardiotoxicity import compute_bsa
from config import get as get_config
from models import Cycle, get_cycles_by_patient
from services.audit import write_audit


def _compute_dose_fields(cycle: Cycle) -> None:
    """Populate bsa_m2 and dose_mg_per_m2 on cycle in-place if inputs are present.

    Clears both derived fields when height_cm or weight_kg is absent so that a
    stale computed value is never persisted after an input is removed.
    dose_mg_per_m2 is only set when both bsa_m2 and dose_mg_total are present.
    """
    if cycle.height_cm and cycle.weight_kg:
        formula = get_config().cardiotoxicity.bsa_formula
        cycle.bsa_m2 = round(compute_bsa(cycle.height_cm, cycle.weight_kg, formula), 4)
        if cycle.dose_mg_total and cycle.bsa_m2:
            cycle.dose_mg_per_m2 = round(cycle.dose_mg_total / cycle.bsa_m2, 4)
        else:
            cycle.dose_mg_per_m2 = None
    else:
        cycle.bsa_m2 = None
        cycle.dose_mg_per_m2 = None


def _get_cycle_by_id(conn, cycle_id: int) -> Optional[Cycle]:
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, cycle_number, phase, planned_date, actual_date,
                  status, dose_percent, dose_reason, notes,
                  height_cm, weight_kg, bsa_m2, anthracycline_agent,
                  dose_mg_total, dose_mg_per_m2
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
        height_cm=row[10], weight_kg=row[11], bsa_m2=row[12],
        anthracycline_agent=row[13], dose_mg_total=row[14], dose_mg_per_m2=row[15],
    )


def create_cycle(conn, cycle: Cycle, actor: Optional[str] = None) -> Cycle:
    """Insert a cycle and write a matching 'create' audit row.

    If height_cm and weight_kg are present, bsa_m2 is computed automatically.
    If dose_mg_total is also present, dose_mg_per_m2 is computed as total / bsa.
    """
    _compute_dose_fields(cycle)
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO cycles
               (patient_id, cycle_number, phase, planned_date, actual_date,
                status, dose_percent, dose_reason, notes,
                height_cm, weight_kg, bsa_m2, anthracycline_agent,
                dose_mg_total, dose_mg_per_m2)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (cycle.patient_id, cycle.cycle_number, cycle.phase,
             cycle.planned_date, cycle.actual_date, cycle.status,
             cycle.dose_percent, cycle.dose_reason, cycle.notes,
             cycle.height_cm, cycle.weight_kg, cycle.bsa_m2,
             cycle.anthracycline_agent, cycle.dose_mg_total, cycle.dose_mg_per_m2),
        )
        cycle.id = cursor.lastrowid
        write_audit(conn, 'cycle', cycle.id, 'create', after=cycle, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return cycle


def update_cycle(conn, cycle: Cycle, actor: Optional[str] = None) -> Cycle:
    """Update a cycle and write a matching 'update' audit row.

    If height_cm and weight_kg are present, bsa_m2 is recomputed automatically.
    """
    if cycle.id is None:
        raise ValueError("update_cycle requires cycle.id")
    before = _get_cycle_by_id(conn, cycle.id)
    if before is None:
        raise LookupError(f"cycle id={cycle.id} not found")

    _compute_dose_fields(cycle)
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE cycles
               SET cycle_number=?, phase=?, planned_date=?, actual_date=?,
                   status=?, dose_percent=?, dose_reason=?, notes=?,
                   height_cm=?, weight_kg=?, bsa_m2=?,
                   anthracycline_agent=?, dose_mg_total=?, dose_mg_per_m2=?
               WHERE id=?''',
            (cycle.cycle_number, cycle.phase, cycle.planned_date,
             cycle.actual_date, cycle.status, cycle.dose_percent,
             cycle.dose_reason, cycle.notes,
             cycle.height_cm, cycle.weight_kg, cycle.bsa_m2,
             cycle.anthracycline_agent, cycle.dose_mg_total, cycle.dose_mg_per_m2,
             cycle.id),
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
