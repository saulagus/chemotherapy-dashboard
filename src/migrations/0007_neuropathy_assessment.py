"""Neuropathy assessment table (US-027).

Creates neuropathy_assessment to store per-patient CTCAE sensory/motor grades.
"""

VERSION = 7


def up(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS neuropathy_assessment (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      TEXT    NOT NULL REFERENCES patient(id),
            cycle_id        INTEGER REFERENCES cycle(id),
            assessment_date DATE    NOT NULL,
            sensory_grade   INTEGER NOT NULL CHECK (sensory_grade BETWEEN 0 AND 4),
            motor_grade     INTEGER NOT NULL CHECK (motor_grade   BETWEEN 0 AND 4),
            ctcae_version   TEXT    NOT NULL DEFAULT '5.0',
            notes           TEXT,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at      TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_neuropathy_patient_date
            ON neuropathy_assessment(patient_id, assessment_date);
    ''')
    conn.commit()


def down(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        DROP INDEX IF EXISTS idx_neuropathy_patient_date;
        DROP TABLE IF EXISTS neuropathy_assessment;
    ''')
    conn.commit()
