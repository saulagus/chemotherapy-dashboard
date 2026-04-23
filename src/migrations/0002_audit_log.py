"""Audit log table.

Every write to patients, cycles, or labs is paired with a row here in the
same transaction. before_json / after_json capture the record state as JSON
(dates serialized as ISO strings); either may be NULL for create / delete.
"""

VERSION = 2


def up(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            actor TEXT NOT NULL,
            entity TEXT NOT NULL,
            entity_id INTEGER,
            action TEXT NOT NULL,
            before_json TEXT,
            after_json TEXT
        )
    ''')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS ix_audit_entity ON audit_log (entity, entity_id)'
    )


def down(conn):
    cursor = conn.cursor()
    cursor.execute('DROP INDEX IF EXISTS ix_audit_entity')
    cursor.execute('DROP TABLE IF EXISTS audit_log')
