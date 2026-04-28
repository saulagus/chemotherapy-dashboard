"""Infusion reaction log table (US-028).

Creates infusion_reaction to store per-cycle hypersensitivity reaction events.
"""

VERSION = 8


def up(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS infusion_reaction (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id          TEXT    NOT NULL REFERENCES patients(patient_id),
            cycle_id            INTEGER NOT NULL REFERENCES cycles(id),
            agent               TEXT    NOT NULL,
            onset_min           INTEGER NOT NULL,
            severity_grade      INTEGER NOT NULL CHECK (severity_grade BETWEEN 1 AND 4),
            symptoms_json       TEXT    NOT NULL DEFAULT '[]',
            response            TEXT,
            rechallenge_outcome TEXT,
            notes               TEXT,
            created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at          TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_reaction_patient_cycle
            ON infusion_reaction(patient_id, cycle_id);
    ''')
    conn.commit()


def down(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        DROP INDEX IF EXISTS idx_reaction_patient_cycle;
        DROP TABLE IF EXISTS infusion_reaction;
    ''')
    conn.commit()
