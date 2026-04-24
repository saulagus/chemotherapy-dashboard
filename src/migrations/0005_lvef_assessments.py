"""LVEF assessment table (US-025).

Creates lvef_assessment to store cardiac function measurements:
  - patient_id      FK to patients.id
  - assessment_date DATE NOT NULL
  - lvef_percent    REAL NOT NULL
  - modality        TEXT NOT NULL   'echo' | 'muga'
  - context         TEXT NULL       'baseline' | 'end_of_ac' | 'ad_hoc'
  - notes           TEXT NULL
  - created_at      TIMESTAMP
  - deleted_at      TIMESTAMP NULL  soft-delete support
"""

VERSION = 5


def up(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lvef_assessment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            assessment_date DATE NOT NULL,
            lvef_percent REAL NOT NULL,
            modality TEXT NOT NULL,
            context TEXT,
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_lvef_patient_date '
        'ON lvef_assessment(patient_id, assessment_date)'
    )


def down(conn):
    cursor = conn.cursor()
    cursor.execute('DROP INDEX IF EXISTS idx_lvef_patient_date')
    cursor.execute('DROP TABLE IF EXISTS lvef_assessment')
