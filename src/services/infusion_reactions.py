"""Infusion reaction service (US-028).

Every mutation writes an audit_log row in the same transaction.
Reactions are soft-deleted (deleted_at set) so history is preserved.

Audit actions used:
  reaction_created  — new reaction logged
  reaction_updated  — existing reaction edited
  reaction_deleted  — reaction soft-deleted
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.audit import write_audit


@dataclass
class InfusionReaction:
    patient_id: str           # string patient ID e.g. 'PT-001'
    cycle_id: int
    agent: str
    onset_min: int
    severity_grade: int       # 1–4
    symptoms_json: str = '[]' # JSON array of symptom strings from config vocab
    response: Optional[str] = None
    rechallenge_outcome: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    deleted_at: Optional[str] = None

    @property
    def symptoms(self) -> List[str]:
        return json.loads(self.symptoms_json or '[]')

    @symptoms.setter
    def symptoms(self, value: List[str]):
        self.symptoms_json = json.dumps(value)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_COLUMNS = (
    'id, patient_id, cycle_id, agent, onset_min, severity_grade, '
    'symptoms_json, response, rechallenge_outcome, notes, created_at, deleted_at'
)


def _row_to_reaction(row) -> InfusionReaction:
    return InfusionReaction(
        id=row[0],
        patient_id=row[1],
        cycle_id=row[2],
        agent=row[3],
        onset_min=row[4],
        severity_grade=row[5],
        symptoms_json=row[6],
        response=row[7],
        rechallenge_outcome=row[8],
        notes=row[9],
        created_at=row[10],
        deleted_at=row[11],
    )


def _get_by_id(conn, reaction_id: int) -> Optional[InfusionReaction]:
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM infusion_reaction WHERE id = ?',
        (reaction_id,),
    )
    row = cursor.fetchone()
    return _row_to_reaction(row) if row else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_reaction(
    conn,
    reaction: InfusionReaction,
    actor: Optional[str] = None,
) -> InfusionReaction:
    """Insert an infusion reaction and write a 'reaction_created' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO infusion_reaction
               (patient_id, cycle_id, agent, onset_min, severity_grade,
                symptoms_json, response, rechallenge_outcome, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (reaction.patient_id, reaction.cycle_id, reaction.agent,
             reaction.onset_min, reaction.severity_grade, reaction.symptoms_json,
             reaction.response, reaction.rechallenge_outcome, reaction.notes),
        )
        reaction.id = cursor.lastrowid
        write_audit(conn, 'infusion_reaction', reaction.id,
                    'reaction_created', after=reaction, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return reaction


def update_reaction(
    conn,
    reaction: InfusionReaction,
    actor: Optional[str] = None,
) -> InfusionReaction:
    """Update an infusion reaction and write a 'reaction_updated' audit row."""
    if reaction.id is None:
        raise ValueError("update_reaction requires reaction.id")
    before = _get_by_id(conn, reaction.id)
    if before is None:
        raise LookupError(f"infusion_reaction id={reaction.id} not found")
    if before.deleted_at is not None:
        raise ValueError(f"infusion_reaction id={reaction.id} is soft-deleted")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE infusion_reaction
               SET agent=?, onset_min=?, severity_grade=?, symptoms_json=?,
                   response=?, rechallenge_outcome=?, notes=?
               WHERE id=?''',
            (reaction.agent, reaction.onset_min, reaction.severity_grade,
             reaction.symptoms_json, reaction.response,
             reaction.rechallenge_outcome, reaction.notes, reaction.id),
        )
        write_audit(conn, 'infusion_reaction', reaction.id,
                    'reaction_updated', before=before, after=reaction, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return reaction


def delete_reaction(
    conn,
    reaction_id: int,
    actor: Optional[str] = None,
) -> None:
    """Soft-delete an infusion reaction. Writes 'reaction_deleted' audit row."""
    before = _get_by_id(conn, reaction_id)
    if before is None:
        raise LookupError(f"infusion_reaction id={reaction_id} not found")
    if before.deleted_at is not None:
        return  # already soft-deleted; no-op

    now = datetime.now().isoformat()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE infusion_reaction SET deleted_at=? WHERE id=?',
            (now, reaction_id),
        )
        write_audit(conn, 'infusion_reaction', reaction_id,
                    'reaction_deleted', before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def list_reactions(
    conn,
    patient_id: str,
    include_deleted: bool = False,
) -> List[InfusionReaction]:
    """Return all infusion reactions for a patient, newest first."""
    cursor = conn.cursor()
    where = (
        'WHERE patient_id = ?'
        if include_deleted
        else 'WHERE patient_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM infusion_reaction {where} '
        'ORDER BY id DESC',
        (patient_id,),
    )
    return [_row_to_reaction(row) for row in cursor.fetchall()]


def list_reactions_for_cycle(
    conn,
    cycle_id: int,
    include_deleted: bool = False,
) -> List[InfusionReaction]:
    """Return all infusion reactions for a specific cycle, newest first."""
    cursor = conn.cursor()
    where = (
        'WHERE cycle_id = ?'
        if include_deleted
        else 'WHERE cycle_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM infusion_reaction {where} ORDER BY id DESC',
        (cycle_id,),
    )
    return [_row_to_reaction(row) for row in cursor.fetchall()]


def latest_reaction(
    conn,
    patient_id: str,
) -> Optional[InfusionReaction]:
    """Return the most recent non-deleted reaction for a patient, or None."""
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM infusion_reaction '
        'WHERE patient_id = ? AND deleted_at IS NULL '
        'ORDER BY id DESC LIMIT 1',
        (patient_id,),
    )
    row = cursor.fetchone()
    return _row_to_reaction(row) if row else None
