import sqlite3
from datetime import datetime

DB_PATH = 'chemo_dashboard.db'

def get_connection(db_path=None):
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(db_path or DB_PATH)

def create_tables(conn=None):
    """Creates the necessary tables if they don't already exist."""
    close_after = conn is None
    if conn is None:
        conn = get_connection()
    cursor = conn.cursor()

    # Patients table
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

    # Cycles table
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

    # Labs table
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

    conn.commit()
    if close_after:
        conn.close()

if __name__ == "__main__":
    create_tables()
    print("Database and tables initialized successfully.")
