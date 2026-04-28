"""G-CSF administration log table (US-029).

Creates gcsf_admin to store growth factor administrations per patient/cycle.
"""

VERSION = 9


def up(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS gcsf_admin (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id       TEXT    NOT NULL REFERENCES patients(patient_id),
            cycle_id         INTEGER REFERENCES cycles(id),
            agent            TEXT    NOT NULL,
            admin_date       DATE    NOT NULL,
            dose_mg          REAL,
            prophylaxis_type TEXT,
            notes            TEXT,
            created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at       TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_gcsf_patient_date
            ON gcsf_admin(patient_id, admin_date);
    ''')
    conn.commit()


def down(conn):
    cursor = conn.cursor()
    cursor.executescript('''
        DROP INDEX IF EXISTS idx_gcsf_patient_date;
        DROP TABLE IF EXISTS gcsf_admin;
    ''')
    conn.commit()
