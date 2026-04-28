"""Symptom quick-entry table (US-030).

Creates symptom_entry to store per-cycle, per-symptom grade records.
"""

VERSION = 10


def up(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS symptom_entry (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  TEXT    NOT NULL REFERENCES patients(patient_id),
            cycle_id    INTEGER REFERENCES cycles(id),
            entry_date  DATE    NOT NULL,
            symptom     TEXT    NOT NULL,
            grade       INTEGER NOT NULL CHECK (grade BETWEEN 0 AND 4),
            notes       TEXT,
            created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at  TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_symptom_patient_cycle
            ON symptom_entry(patient_id, cycle_id);
    ''')
    conn.commit()


def down(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        DROP INDEX IF EXISTS idx_symptom_patient_cycle;
        DROP TABLE IF EXISTS symptom_entry;
    ''')
    conn.commit()
