import sqlite3
from datetime import date, datetime

# Path to the SQLite database file. Tests pass ':memory:' to get_connection() instead.
DB_PATH = 'chemo_dashboard.db'

# Python 3.12+ requires explicit adapters to convert date/datetime objects
# to strings when saving, and back to date/datetime objects when reading.
# detect_types=PARSE_DECLTYPES in get_connection() activates the converters below.
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter('DATE', lambda b: date.fromisoformat(b.decode()))
sqlite3.register_converter('TIMESTAMP', lambda b: datetime.fromisoformat(b.decode()))


def get_connection(db_path=None):
    """Return a connection to the SQLite database.

    Pass ':memory:' for an isolated in-memory database (used in tests).
    """
    return sqlite3.connect(db_path or DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    # Returns a sqlite3.Connection — all queries and inserts go through this object.


def create_tables(conn=None):
    """Create all required tables if they do not already exist.

    Accepts an open connection so tests can pass an in-memory connection directly.
    If no connection is provided, one is opened and closed internally.
    Safe to call multiple times — IF NOT EXISTS prevents overwriting existing data.
    """
    close_after = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()  # cursor is the object used to run SQL commands.

    # One row per patient enrolled in AC-T treatment.
    # patient_id is the human-readable ID (e.g. 'PT-001'), not the numeric PK.
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

    # One row per treatment cycle per patient.
    # patient_id references patients.id (the INTEGER PK), not the text 'PT-001'.
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

    # One row per lab draw per patient.
    # ANC is the most critical value — it determines if the next cycle can proceed.
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

    conn.commit()  # Saves all changes to disk.
    if close_after:
        conn.close()
    # Returns nothing. Tables now exist and are ready to use.


if __name__ == "__main__":
    # Running this file directly initializes the database on disk.
    create_tables()
    print("Database and tables initialized successfully.")
