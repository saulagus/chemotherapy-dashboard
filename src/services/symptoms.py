"""Symptom quick-entry service (US-030).

Every mutation writes an audit_log row in the same transaction.
Records are soft-deleted (deleted_at set) so history is preserved.

Audit actions used:
  symptom_created  — new symptom entry saved
  symptom_updated  — existing entry edited
  symptom_deleted  — entry soft-deleted
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from services.audit import write_audit


@dataclass
class SymptomEntry:
    patient_id: str      # string patient ID e.g. 'PT-001'
    entry_date: str      # ISO 'YYYY-MM-DD'
    symptom: str         # from config vocab
    grade: int           # 0–4
    cycle_id: Optional[int] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    deleted_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_COLUMNS = (
    'id, patient_id, cycle_id, entry_date, symptom, grade, notes, created_at, deleted_at'
)


def _row_to_entry(row) -> SymptomEntry:
    return SymptomEntry(
        id=row[0],
        patient_id=row[1],
        cycle_id=row[2],
        entry_date=row[3],
        symptom=row[4],
        grade=row[5],
        notes=row[6],
        created_at=row[7],
        deleted_at=row[8],
    )


def _get_by_id(conn, entry_id: int) -> Optional[SymptomEntry]:
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT {_COLUMNS} FROM symptom_entry WHERE id = ?',
        (entry_id,),
    )
    row = cursor.fetchone()
    return _row_to_entry(row) if row else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_symptom(
    conn,
    entry: SymptomEntry,
    actor: Optional[str] = None,
) -> SymptomEntry:
    """Insert a symptom entry and write 'symptom_created' audit row."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO symptom_entry
               (patient_id, cycle_id, entry_date, symptom, grade, notes)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (entry.patient_id, entry.cycle_id, entry.entry_date,
             entry.symptom, entry.grade, entry.notes),
        )
        entry.id = cursor.lastrowid
        write_audit(conn, 'symptom_entry', entry.id,
                    'symptom_created', after=entry, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return entry


def create_many(
    conn,
    entries: List[SymptomEntry],
    actor: Optional[str] = None,
) -> List[SymptomEntry]:
    """Insert a batch of symptom entries (one per symptom per cycle).

    All entries are written in a single transaction with individual audit rows.
    Returns the list with ids populated.
    """
    if not entries:
        return []
    cursor = conn.cursor()
    try:
        saved = []
        for entry in entries:
            cursor.execute(
                '''INSERT INTO symptom_entry
                   (patient_id, cycle_id, entry_date, symptom, grade, notes)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (entry.patient_id, entry.cycle_id, entry.entry_date,
                 entry.symptom, entry.grade, entry.notes),
            )
            entry.id = cursor.lastrowid
            write_audit(conn, 'symptom_entry', entry.id,
                        'symptom_created', after=entry, actor=actor)
            saved.append(entry)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return saved


def update_symptom(
    conn,
    entry: SymptomEntry,
    actor: Optional[str] = None,
) -> SymptomEntry:
    """Update a symptom entry and write 'symptom_updated' audit row."""
    if entry.id is None:
        raise ValueError("update_symptom requires entry.id")
    before = _get_by_id(conn, entry.id)
    if before is None:
        raise LookupError(f"symptom_entry id={entry.id} not found")
    if before.deleted_at is not None:
        raise ValueError(f"symptom_entry id={entry.id} is soft-deleted")

    cursor = conn.cursor()
    try:
        cursor.execute(
            '''UPDATE symptom_entry
               SET grade=?, notes=?, entry_date=?
               WHERE id=?''',
            (entry.grade, entry.notes, entry.entry_date, entry.id),
        )
        write_audit(conn, 'symptom_entry', entry.id,
                    'symptom_updated', before=before, after=entry, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return entry


def delete_symptom(
    conn,
    entry_id: int,
    actor: Optional[str] = None,
) -> None:
    """Soft-delete a symptom entry. Writes 'symptom_deleted' audit row."""
    before = _get_by_id(conn, entry_id)
    if before is None:
        raise LookupError(f"symptom_entry id={entry_id} not found")
    if before.deleted_at is not None:
        return  # already soft-deleted; no-op

    now = datetime.now().isoformat()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE symptom_entry SET deleted_at=? WHERE id=?',
            (now, entry_id),
        )
        write_audit(conn, 'symptom_entry', entry_id,
                    'symptom_deleted', before=before, actor=actor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def list_symptoms(
    conn,
    patient_id: str,
    include_deleted: bool = False,
) -> List[SymptomEntry]:
    """Return all symptom entries for a patient, newest first."""
    cursor = conn.cursor()
    where = (
        'WHERE patient_id = ?'
        if include_deleted
        else 'WHERE patient_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM symptom_entry {where} '
        'ORDER BY entry_date DESC, id DESC',
        (patient_id,),
    )
    return [_row_to_entry(row) for row in cursor.fetchall()]


def list_symptoms_for_cycle(
    conn,
    cycle_id: int,
    include_deleted: bool = False,
) -> List[SymptomEntry]:
    """Return all symptom entries for a specific cycle, ordered by symptom name."""
    cursor = conn.cursor()
    where = (
        'WHERE cycle_id = ?'
        if include_deleted
        else 'WHERE cycle_id = ? AND deleted_at IS NULL'
    )
    cursor.execute(
        f'SELECT {_COLUMNS} FROM symptom_entry {where} ORDER BY symptom',
        (cycle_id,),
    )
    return [_row_to_entry(row) for row in cursor.fetchall()]


def latest_cycle_symptoms(
    conn,
    patient_id: str,
) -> List[SymptomEntry]:
    """Return symptom entries for the most recent cycle that has any symptom records.

    Returns empty list when no entries exist.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT cycle_id FROM symptom_entry
           WHERE patient_id = ? AND deleted_at IS NULL
           ORDER BY entry_date DESC, id DESC LIMIT 1''',
        (patient_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return []
    return list_symptoms_for_cycle(conn, row[0])
