"""Patient edit + soft-delete + dose-density fields.

Adds two columns to the patients table:
  - deleted_at  TIMESTAMP NULL   (non-null = soft-deleted; filtered from all
                                  patient queries by default)
  - dose_density TEXT NULL       (one of config.cycles.dose_density_options;
                                  NULL on v1.0 rows — backfilled on first edit)
"""

VERSION = 3


def up(conn):
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE patients ADD COLUMN deleted_at TIMESTAMP')
    cursor.execute('ALTER TABLE patients ADD COLUMN dose_density TEXT')


def down(conn):
    # SQLite pre-3.35 lacks DROP COLUMN; rebuild the table without the new cols.
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        INSERT INTO patients__new
            (id, patient_id, name, age, diagnosis_date, start_date,
             protocol, total_cycles, created_at)
        SELECT id, patient_id, name, age, diagnosis_date, start_date,
               protocol, total_cycles, created_at
        FROM patients
    ''')
    cursor.execute('DROP TABLE patients')
    cursor.execute('ALTER TABLE patients__new RENAME TO patients')
