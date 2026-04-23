"""Schema migration runner.

Migrations are numbered Python files in this directory:
    NNNN_name.py  — must expose VERSION:int, up(conn), down(conn).

The runner tracks applied versions in the schema_migrations table.
Each migration runs in its own transaction; failure rolls back cleanly.
Before running against a real file-backed DB, the file is backed up.
"""

import importlib
import os
import re
import shutil
from datetime import datetime
from typing import List, Tuple

_MIGRATION_FILENAME = re.compile(r'^(\d{4})_[a-z0-9_]+\.py$')


def _ensure_migrations_table(conn) -> None:
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()


def get_applied_versions(conn) -> List[int]:
    """Return sorted list of applied migration versions. Empty if table missing."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    )
    if cursor.fetchone() is None:
        return []
    cursor.execute('SELECT version FROM schema_migrations ORDER BY version')
    return [row[0] for row in cursor.fetchall()]


def discover_migrations() -> List[Tuple[int, object]]:
    """Return [(version, module), ...] sorted by version, from this directory."""
    here = os.path.dirname(__file__)
    found = []
    for filename in os.listdir(here):
        match = _MIGRATION_FILENAME.match(filename)
        if match is None:
            continue
        version = int(match.group(1))
        module_name = filename[:-3]
        module = importlib.import_module(f'migrations.{module_name}')
        if not hasattr(module, 'VERSION') or not hasattr(module, 'up'):
            raise RuntimeError(f"migration {filename} missing VERSION or up()")
        if module.VERSION != version:
            raise RuntimeError(
                f"migration {filename} declares VERSION={module.VERSION} but filename says {version}"
            )
        found.append((version, module))
    found.sort(key=lambda pair: pair[0])
    return found


def backup_db(db_path: str) -> str:
    """Copy db_path to a timestamped sibling file. Returns backup path.

    No-op for ':memory:' or missing files; returns '' in those cases.
    """
    if not db_path or db_path == ':memory:' or not os.path.exists(db_path):
        return ''
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{db_path}.pre-migrate-{stamp}'
    shutil.copy2(db_path, backup_path)
    return backup_path


def run_migrations(conn, db_path: str = None) -> List[int]:
    """Apply all pending migrations in order. Returns list of newly-applied versions.

    If db_path is provided and points to an existing file, that file is
    backed up before the first migration runs.
    """
    _ensure_migrations_table(conn)
    applied = set(get_applied_versions(conn))
    pending = [(v, m) for v, m in discover_migrations() if v not in applied]
    if not pending:
        return []

    if db_path:
        backup_db(db_path)

    newly_applied = []
    for version, module in pending:
        try:
            module.up(conn)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO schema_migrations (version) VALUES (?)', (version,)
            )
            conn.commit()
            newly_applied.append(version)
        except Exception:
            conn.rollback()
            raise
    return newly_applied


def rollback_to(conn, target_version: int) -> List[int]:
    """Run down() for every applied migration with version > target_version.

    Used only by tests. Returns list of versions rolled back (newest first).
    """
    _ensure_migrations_table(conn)
    applied = get_applied_versions(conn)
    to_rollback = sorted([v for v in applied if v > target_version], reverse=True)
    modules_by_version = dict(discover_migrations())
    rolled_back = []
    for version in to_rollback:
        module = modules_by_version[version]
        if not hasattr(module, 'down'):
            raise RuntimeError(f"migration {version} has no down() — cannot roll back")
        try:
            module.down(conn)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM schema_migrations WHERE version=?', (version,))
            conn.commit()
            rolled_back.append(version)
        except Exception:
            conn.rollback()
            raise
    return rolled_back
