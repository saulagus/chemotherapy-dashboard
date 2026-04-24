"""Patient prior-anthracycline exposure fields (US-024).

Adds two columns to the patients table:
  - prior_anthracycline_dose_mg_per_m2  REAL DEFAULT 0
    Cumulative doxorubicin-equivalent dose received before this treatment course.
  - prior_anthracycline_agent           TEXT NULL
    Primary agent received previously (e.g. 'doxorubicin').
"""

VERSION = 6


def up(conn):
    cursor = conn.cursor()
    cursor.execute(
        'ALTER TABLE patients ADD COLUMN '
        'prior_anthracycline_dose_mg_per_m2 REAL DEFAULT 0'
    )
    cursor.execute(
        'ALTER TABLE patients ADD COLUMN prior_anthracycline_agent TEXT'
    )


def down(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE patients__new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            diagnosis_date DATE,
            start_date DATE,
            protocol TEXT,
            total_cycles INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP,
            dose_density TEXT
        )
    ''')
    cursor.execute('''
        INSERT INTO patients__new
            (id, patient_id, name, age, diagnosis_date, start_date,
             protocol, total_cycles, created_at, deleted_at, dose_density)
        SELECT id, patient_id, name, age, diagnosis_date, start_date,
               protocol, total_cycles, created_at, deleted_at, dose_density
        FROM patients
    ''')
    cursor.execute('DROP TABLE patients')
    cursor.execute('ALTER TABLE patients__new RENAME TO patients')
