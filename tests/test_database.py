import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection, create_tables

@pytest.fixture
def conn():
    connection = get_connection(':memory:')
    create_tables(connection)
    yield connection
    connection.close()


# --- get_connection ---

def test_get_connection_returns_connection():
    connection = get_connection(':memory:')
    assert connection is not None
    connection.close()


def test_get_connection_is_usable():
    connection = get_connection(':memory:')
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    assert cursor.fetchone()[0] == 1
    connection.close()


# --- create_tables ---

def test_patients_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
    assert cursor.fetchone() is not None


def test_cycles_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cycles'")
    assert cursor.fetchone() is not None


def test_labs_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='labs'")
    assert cursor.fetchone() is not None


def test_create_tables_is_idempotent():
    connection = get_connection(':memory:')
    create_tables(connection)
    create_tables(connection)  # should not raise
    connection.close()


# --- patients table ---

def test_insert_patient(conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (patient_id, name, age, protocol, total_cycles) VALUES (?, ?, ?, ?, ?)",
        ('P001', 'John Doe', 45, 'CHOP', 6)
    )
    conn.commit()
    cursor.execute("SELECT name FROM patients WHERE patient_id = 'P001'")
    assert cursor.fetchone()[0] == 'John Doe'


def test_patient_id_is_unique(conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (patient_id, name) VALUES (?, ?)", ('P002', 'Jane Doe')
    )
    conn.commit()
    with pytest.raises(Exception):
        cursor.execute(
            "INSERT INTO patients (patient_id, name) VALUES (?, ?)", ('P002', 'Duplicate')
        )
        conn.commit()


def test_patient_name_is_required(conn):
    cursor = conn.cursor()
    with pytest.raises(Exception):
        cursor.execute("INSERT INTO patients (patient_id) VALUES (?)", ('P003',))
        conn.commit()


# --- cycles table ---

def test_insert_cycle(conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (patient_id, name) VALUES (?, ?)", ('P010', 'Test Patient')
    )
    patient_row_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO cycles (patient_id, cycle_number, status, dose_percent) VALUES (?, ?, ?, ?)",
        (patient_row_id, 1, 'completed', 100.0)
    )
    conn.commit()
    cursor.execute("SELECT status FROM cycles WHERE patient_id = ?", (patient_row_id,))
    assert cursor.fetchone()[0] == 'completed'


# --- labs table ---

def test_insert_lab(conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (patient_id, name) VALUES (?, ?)", ('P020', 'Lab Patient')
    )
    patient_row_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO labs (patient_id, lab_date, anc, wbc, platelets, hemoglobin) VALUES (?, ?, ?, ?, ?, ?)",
        (patient_row_id, '2026-03-07', 1.8, 4.5, 180.0, 12.5)
    )
    conn.commit()
    cursor.execute("SELECT anc FROM labs WHERE patient_id = ?", (patient_row_id,))
    assert cursor.fetchone()[0] == 1.8


def test_lab_requires_lab_date(conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (patient_id, name) VALUES (?, ?)", ('P021', 'No Date Patient')
    )
    patient_row_id = cursor.lastrowid
    with pytest.raises(Exception):
        cursor.execute(
            "INSERT INTO labs (patient_id) VALUES (?)", (patient_row_id,)
        )
        conn.commit()
