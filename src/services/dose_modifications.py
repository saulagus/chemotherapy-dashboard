"""Dose modification query service (Sprint 9 — US-036 + US-035).

A dose modification is any cycle where dose_percent < 100.
The 'why' comes from the audit_log row that recorded the cycle save —
specifically the dose_reason field from the cycle record itself.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional


@dataclass
class DoseMod:
    cycle_number: int
    date: Optional[date]
    agent: Optional[str]
    dose_pct: float
    prior_pct: float
    reason: Optional[str]
    actor: Optional[str]
    cycle_id: int


def list_for_patient(conn, patient_id: int) -> List[DoseMod]:
    """Return all dose modifications for a patient, ordered by cycle_number.

    A modification is any cycle with dose_percent < 100.
    Soft-deleted cycles are excluded.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, cycle_number, actual_date, anthracycline_agent,
                  dose_percent, dose_reason
           FROM cycles
           WHERE patient_id = ?
             AND dose_percent IS NOT NULL
             AND dose_percent < 100
           ORDER BY cycle_number''',
        (patient_id,),
    )
    rows = cursor.fetchall()
    return [_row_to_dose_mod(row, conn) for row in rows]


def list_for_cycle(conn, cycle_id: int) -> List[DoseMod]:
    """Return dose modifications for a specific cycle (usually 0 or 1 result)."""
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, cycle_number, actual_date, anthracycline_agent,
                  dose_percent, dose_reason
           FROM cycles
           WHERE id = ?
             AND dose_percent IS NOT NULL
             AND dose_percent < 100''',
        (cycle_id,),
    )
    rows = cursor.fetchall()
    return [_row_to_dose_mod(row, conn) for row in rows]


def _row_to_dose_mod(row, conn) -> DoseMod:
    cycle_id, cycle_number, raw_date, agent, dose_pct, reason = row
    d = raw_date
    if isinstance(d, str) and d:
        try:
            d = date.fromisoformat(d)
        except ValueError:
            d = None

    actor = _lookup_actor(conn, cycle_id)
    prior_pct = _lookup_prior_pct(conn, cycle_id, cycle_number)

    return DoseMod(
        cycle_id=cycle_id,
        cycle_number=cycle_number,
        date=d,
        agent=agent,
        dose_pct=float(dose_pct),
        prior_pct=prior_pct,
        reason=reason,
        actor=actor,
    )


def _lookup_actor(conn, cycle_id: int) -> Optional[str]:
    """Return the actor from the most recent audit row for this cycle."""
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT actor FROM audit_log
           WHERE entity = 'cycle' AND entity_id = ?
           ORDER BY ts DESC, id DESC LIMIT 1''',
        (cycle_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _lookup_prior_pct(conn, cycle_id: int, cycle_number: int) -> float:
    """Return the dose_percent from the audit 'before' state, or 100.0 if none."""
    import json
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT before_json FROM audit_log
           WHERE entity = 'cycle' AND entity_id = ? AND action = 'update'
           ORDER BY ts ASC, id ASC LIMIT 1''',
        (cycle_id,),
    )
    row = cursor.fetchone()
    if row and row[0]:
        try:
            before = json.loads(row[0])
            val = before.get('dose_percent')
            if val is not None:
                return float(val)
        except Exception:
            pass
    return 100.0
