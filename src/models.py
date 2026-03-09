from dataclasses import dataclass
from typing import Optional, List
from datetime import date


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
# A dataclass automatically generates a constructor and comparison methods
# from the fields declared below. Fields with defaults are optional on creation.

@dataclass
class Patient:
    patient_id: str           # Human-readable ID, e.g. 'PT-001'. Must be unique.
    name: str                 # Patient name or initials.
    age: Optional[int] = None
    diagnosis_date: Optional[date] = None
    start_date: Optional[date] = None     # Date AC-T treatment started.
    protocol: Optional[str] = None        # e.g. 'Dose-Dense AC-T' or 'Standard AC-T'
    total_cycles: Optional[int] = 8       # AC-T is always 8 cycles (4 AC + 4 T).
    id: Optional[int] = None             # Auto-assigned by the database after insert.

    @classmethod
    def get_all(cls, conn) -> List['Patient']:
        """Return all patients ordered by name."""
        return get_all_patients(conn)


@dataclass
class Cycle:
    patient_id: int           # References patients.id (INTEGER PK), not the text 'PT-001'.
    cycle_number: int         # 1 through 8.
    phase: Optional[str] = None            # 'AC' (cycles 1-4) or 'T' (cycles 5-8).
    planned_date: Optional[date] = None    # When the cycle was scheduled.
    actual_date: Optional[date] = None     # When it was actually administered.
    status: Optional[str] = 'pending'      # 'pending', 'completed', or 'delayed'.
    dose_percent: Optional[float] = 100.0  # 100.0 = full dose. Lower if reduced.
    dose_reason: Optional[str] = None      # Reason for dose reduction, if any.
    notes: Optional[str] = None
    id: Optional[int] = None             # Auto-assigned by the database after insert.


@dataclass
class Lab:
    patient_id: int           # References patients.id (INTEGER PK), not the text 'PT-001'.
    lab_date: date            # Required — every lab entry must have a date.
    # Key blood count values monitored during AC-T. ANC below 1.5 typically delays the next cycle.
    anc: Optional[float] = None           # Absolute Neutrophil Count (10^9/L)
    wbc: Optional[float] = None           # White Blood Cell count (10^9/L)
    platelets: Optional[float] = None     # Platelet count (10^9/L)
    hemoglobin: Optional[float] = None    # Hemoglobin level (g/dL)
    id: Optional[int] = None             # Auto-assigned by the database after insert.


# ---------------------------------------------------------------------------
# Patient CRUD
# ---------------------------------------------------------------------------
# CRUD = Create, Read, Update, Delete — the four basic database operations.
# All functions accept 'conn', an open database connection.

def add_patient(conn, patient: Patient) -> Patient:
    """Insert a new patient and return it with its DB id set."""
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO patients
           (patient_id, name, age, diagnosis_date, start_date, protocol, total_cycles)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        # '?' placeholders prevent SQL injection — malicious input altering the query.
        (patient.patient_id, patient.name, patient.age,
         patient.diagnosis_date, patient.start_date,
         patient.protocol, patient.total_cycles)
    )
    conn.commit()
    patient.id = cursor.lastrowid  # Auto-generated integer ID assigned by the database.
    # Returns the same Patient object with id now set, ready to link cycles or labs.
    return patient


def get_all_patients(conn) -> List[Patient]:
    """Return all patients ordered by name."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, patient_id, name, age, diagnosis_date, start_date, protocol, total_cycles '
        'FROM patients ORDER BY name'
    )
    # fetchall() returns a list of tuples; we convert each into a Patient object.
    # Returns an empty list [] if no patients exist yet.
    return [
        Patient(id=row[0], patient_id=row[1], name=row[2], age=row[3],
                diagnosis_date=row[4], start_date=row[5],
                protocol=row[6], total_cycles=row[7])
        for row in cursor.fetchall()
    ]


def get_patient_by_id(conn, patient_id: str) -> Optional[Patient]:
    """Return a patient by their text patient_id (e.g. 'PT-001'), or None if not found."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, patient_id, name, age, diagnosis_date, start_date, protocol, total_cycles '
        'FROM patients WHERE patient_id = ?',
        (patient_id,)  # Trailing comma required — Python needs a tuple, not a plain value.
    )
    row = cursor.fetchone()  # Returns one matching row, or None if not found.
    if row is None:
        return None  # No patient with that ID exists.
    # Returns a Patient object with all fields populated.
    return Patient(id=row[0], patient_id=row[1], name=row[2], age=row[3],
                   diagnosis_date=row[4], start_date=row[5],
                   protocol=row[6], total_cycles=row[7])


def update_patient(conn, patient: Patient) -> None:
    """Update all fields of an existing patient (matched by DB id)."""
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE patients
           SET patient_id=?, name=?, age=?, diagnosis_date=?, start_date=?,
               protocol=?, total_cycles=?
           WHERE id=?''',
        # id is passed last to match the WHERE clause at the end of the query.
        (patient.patient_id, patient.name, patient.age,
         patient.diagnosis_date, patient.start_date,
         patient.protocol, patient.total_cycles, patient.id)
    )
    conn.commit()
    # Returns nothing. The database row has been updated in place.


def delete_patient(conn, patient_id: str) -> None:
    """Delete a patient by their text patient_id (e.g. 'PT-001')."""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patients WHERE patient_id = ?', (patient_id,))
    conn.commit()
    # Returns nothing. The patient row is permanently removed from the database.


# ---------------------------------------------------------------------------
# Cycle CRUD
# ---------------------------------------------------------------------------

def add_cycle(conn, cycle: Cycle) -> Cycle:
    """Insert a new cycle and return it with its DB id set."""
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO cycles
           (patient_id, cycle_number, phase, planned_date, actual_date,
            status, dose_percent, dose_reason, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (cycle.patient_id, cycle.cycle_number, cycle.phase,
         cycle.planned_date, cycle.actual_date, cycle.status,
         cycle.dose_percent, cycle.dose_reason, cycle.notes)
    )
    conn.commit()
    cycle.id = cursor.lastrowid
    # Returns the same Cycle object with id now set.
    return cycle


def get_cycles_by_patient(conn, patient_db_id: int) -> List[Cycle]:
    """Return all cycles for a patient ordered by cycle number.

    patient_db_id is the INTEGER primary key from patients.id,
    not the text 'PT-001' patient_id field.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, cycle_number, phase, planned_date, actual_date,
                  status, dose_percent, dose_reason, notes
           FROM cycles WHERE patient_id = ? ORDER BY cycle_number''',
        (patient_db_id,)
    )
    # Returns a list of Cycle objects in order (1 through 8).
    # Returns an empty list [] if no cycles have been recorded yet.
    return [
        Cycle(id=row[0], patient_id=row[1], cycle_number=row[2], phase=row[3],
              planned_date=row[4], actual_date=row[5], status=row[6],
              dose_percent=row[7], dose_reason=row[8], notes=row[9])
        for row in cursor.fetchall()
    ]


def update_cycle(conn, cycle: Cycle) -> None:
    """Update all fields of an existing cycle (matched by DB id)."""
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE cycles
           SET cycle_number=?, phase=?, planned_date=?, actual_date=?,
               status=?, dose_percent=?, dose_reason=?, notes=?
           WHERE id=?''',
        (cycle.cycle_number, cycle.phase, cycle.planned_date,
         cycle.actual_date, cycle.status, cycle.dose_percent,
         cycle.dose_reason, cycle.notes, cycle.id)
    )
    conn.commit()
    # Returns nothing. The cycle row has been updated in place.


# ---------------------------------------------------------------------------
# Lab CRUD
# ---------------------------------------------------------------------------

def add_lab(conn, lab: Lab) -> Lab:
    """Insert a new lab record and return it with its DB id set."""
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO labs
           (patient_id, lab_date, anc, wbc, platelets, hemoglobin)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (lab.patient_id, lab.lab_date, lab.anc,
         lab.wbc, lab.platelets, lab.hemoglobin)
    )
    conn.commit()
    lab.id = cursor.lastrowid
    # Returns the same Lab object with id now set.
    return lab


def get_labs_by_patient(conn, patient_db_id: int) -> List[Lab]:
    """Return all labs for a patient ordered by date (oldest first).

    patient_db_id is the INTEGER primary key from patients.id.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, lab_date, anc, wbc, platelets, hemoglobin
           FROM labs WHERE patient_id = ? ORDER BY lab_date''',
        (patient_db_id,)
    )
    # Returns a list of Lab objects oldest to newest.
    # Returns an empty list [] if no labs have been recorded for this patient.
    return [
        Lab(id=row[0], patient_id=row[1], lab_date=row[2], anc=row[3],
            wbc=row[4], platelets=row[5], hemoglobin=row[6])
        for row in cursor.fetchall()
    ]


def get_latest_lab(conn, patient_db_id: int) -> Optional[Lab]:
    """Return the most recent lab record for a patient, or None if none exist.

    patient_db_id is the INTEGER primary key from patients.id.
    ORDER BY lab_date DESC + LIMIT 1 selects only the newest row.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, lab_date, anc, wbc, platelets, hemoglobin
           FROM labs WHERE patient_id = ? ORDER BY lab_date DESC LIMIT 1''',
        (patient_db_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None  # No lab records exist for this patient.
    # Returns a single Lab object representing the most recent blood draw.
    return Lab(id=row[0], patient_id=row[1], lab_date=row[2], anc=row[3],
               wbc=row[4], platelets=row[5], hemoglobin=row[6])
