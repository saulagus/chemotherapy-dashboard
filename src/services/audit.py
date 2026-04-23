"""Audit logging primitive.

write_audit() INSERTs a row into audit_log but does NOT commit. Callers are
responsible for committing (or rolling back) the full transaction so the
mutation and its audit row land atomically together.

Actor in V2 = os.getlogin(), with getpass.getuser() fallback for contexts
with no controlling terminal (daemon runs, some CI environments). Real
authentication arrives in V3.
"""

import getpass
import json
import os
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any, List, Optional

ACTIONS = {'create', 'update', 'delete', 'soft_delete', 'restore'}


def current_actor() -> str:
    """Return the OS-level username of the current session."""
    try:
        return os.getlogin()
    except OSError:
        return getpass.getuser()


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"audit JSON: unsupported type {type(value).__name__}")


def _to_serializable(record: Any) -> Optional[dict]:
    if record is None:
        return None
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, dict):
        return dict(record)
    raise TypeError(
        f"audit record must be dataclass, dict, or None — got {type(record).__name__}"
    )


def write_audit(
    conn,
    entity: str,
    entity_id: Optional[int],
    action: str,
    before: Any = None,
    after: Any = None,
    actor: Optional[str] = None,
) -> int:
    """Insert an audit_log row. Does NOT commit.

    entity: 'patient' | 'cycle' | 'lab'
    action: one of ACTIONS
    before / after: dataclass, dict, or None. Dates are ISO-serialized.
    Returns the inserted audit row id.
    """
    if action not in ACTIONS:
        raise ValueError(f"unknown audit action: {action!r}")

    before_dict = _to_serializable(before)
    after_dict = _to_serializable(after)
    before_json = json.dumps(before_dict, default=_json_default) if before_dict is not None else None
    after_json = json.dumps(after_dict, default=_json_default) if after_dict is not None else None

    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO audit_log
           (actor, entity, entity_id, action, before_json, after_json)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (actor or current_actor(), entity, entity_id, action, before_json, after_json),
    )
    return cursor.lastrowid


def get_audit_for_entity(
    conn, entity: str, entity_id: int
) -> List[dict]:
    """Return audit rows for one entity, newest first.

    Each row is a dict with keys: id, ts, actor, entity, entity_id, action,
    before, after (before/after are parsed back into dicts or None).
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, ts, actor, entity, entity_id, action, before_json, after_json
           FROM audit_log
           WHERE entity = ? AND entity_id = ?
           ORDER BY ts DESC, id DESC''',
        (entity, entity_id),
    )
    return [
        {
            'id': row[0],
            'ts': row[1],
            'actor': row[2],
            'entity': row[3],
            'entity_id': row[4],
            'action': row[5],
            'before': json.loads(row[6]) if row[6] else None,
            'after': json.loads(row[7]) if row[7] else None,
        }
        for row in cursor.fetchall()
    ]
