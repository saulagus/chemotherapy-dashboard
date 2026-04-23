"""Initial schema: patients, cycles, labs.

Mirrors the tables originally created by database.create_tables().
Safe to apply to an existing v1.0 database — CREATE TABLE IF NOT EXISTS
leaves existing tables untouched.
"""

VERSION = 1


def up(conn):
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
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
        CREATE TABLE IF NOT EXISTS cycles (
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
        CREATE TABLE IF NOT EXISTS labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            lab_date DATE NOT NULL,
            anc REAL,
            wbc REAL,
            platelets REAL,
            hemoglobin REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')


def down(conn):
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS labs')
    cursor.execute('DROP TABLE IF EXISTS cycles')
    cursor.execute('DROP TABLE IF EXISTS patients')
