"""Cycle BSA and delivered-dose fields (US-023).

Adds six columns to the cycles table:
  - height_cm           REAL NULL   patient height at time of cycle
  - weight_kg           REAL NULL   patient weight at time of cycle
  - bsa_m2              REAL NULL   computed from height/weight at save
  - anthracycline_agent TEXT NULL   'doxorubicin' | 'epirubicin' | ...
  - dose_mg_total       REAL NULL   total mg dispensed
  - dose_mg_per_m2      REAL NULL   computed: total / bsa
"""

VERSION = 4


def up(conn):
    cursor = conn.cursor()
    cursor.execute('ALTER TABLE cycles ADD COLUMN height_cm REAL')
    cursor.execute('ALTER TABLE cycles ADD COLUMN weight_kg REAL')
    cursor.execute('ALTER TABLE cycles ADD COLUMN bsa_m2 REAL')
    cursor.execute('ALTER TABLE cycles ADD COLUMN anthracycline_agent TEXT')
    cursor.execute('ALTER TABLE cycles ADD COLUMN dose_mg_total REAL')
    cursor.execute('ALTER TABLE cycles ADD COLUMN dose_mg_per_m2 REAL')


def down(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE cycles__new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            cycle_number INTEGER NOT NULL,
            phase TEXT,
            planned_date DATE,
            actual_date DATE,
            status TEXT,
            dose_percent REAL,
            dose_reason TEXT,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    cursor.execute('''
        INSERT INTO cycles__new
            (id, patient_id, cycle_number, phase, planned_date, actual_date,
             status, dose_percent, dose_reason, notes)
        SELECT id, patient_id, cycle_number, phase, planned_date, actual_date,
               status, dose_percent, dose_reason, notes
        FROM cycles
    ''')
    cursor.execute('DROP TABLE cycles')
    cursor.execute('ALTER TABLE cycles__new RENAME TO cycles')
