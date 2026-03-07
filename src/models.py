from dataclasses import dataclass
from typing import Optional, List
from datetime import date


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Patient:
    patient_id: str
    name: str
    age: Optional[int] = None
    diagnosis_date: Optional[date] = None
    start_date: Optional[date] = None
    protocol: Optional[str] = None
    total_cycles: Optional[int] = 8
    id: Optional[int] = None  # DB row ID, set after insert


@dataclass
class Cycle:
    patient_id: int                        # references patients.id (INTEGER PK)
    cycle_number: int
    phase: Optional[str] = None            # 'AC' or 'T'
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[str] = 'pending'      # 'pending', 'completed', 'delayed'
    dose_percent: Optional[float] = 100.0
    dose_reason: Optional[str] = None
    notes: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Lab:
    patient_id: int                        # references patients.id (INTEGER PK)
    lab_date: date
    anc: Optional[float] = None
    wbc: Optional[float] = None
    platelets: Optional[float] = None
    hemoglobin: Optional[float] = None
    id: Optional[int] = None


# ---------------------------------------------------------------------------
# Patient CRUD
# ---------------------------------------------------------------------------

def add_patient(conn, patient: Patient) -> Patient:
    """Insert a new patient and return it with its DB id set."""
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO patients
           (patient_id, name, age, diagnosis_date, start_date, protocol, total_cycles)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (patient.patient_id, patient.name, patient.age,
         patient.diagnosis_date, patient.start_date,
         patient.protocol, patient.total_cycles)
    )
    conn.commit()
    patient.id = cursor.lastrowid
    return patient


def get_all_patients(conn) -> List[Patient]:
    """Return all patients ordered by name."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, patient_id, name, age, diagnosis_date, start_date, protocol, total_cycles '
        'FROM patients ORDER BY name'
    )
    return [
        Patient(id=row[0], patient_id=row[1], name=row[2], age=row[3],
                diagnosis_date=row[4], start_date=row[5],
                protocol=row[6], total_cycles=row[7])
        for row in cursor.fetchall()
    ]


def get_patient_by_id(conn, patient_id: str) -> Optional[Patient]:
    """Return a patient by their text patient_id, or None if not found."""
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, patient_id, name, age, diagnosis_date, start_date, protocol, total_cycles '
        'FROM patients WHERE patient_id = ?',
        (patient_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
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
        (patient.patient_id, patient.name, patient.age,
         patient.diagnosis_date, patient.start_date,
         patient.protocol, patient.total_cycles, patient.id)
    )
    conn.commit()


def delete_patient(conn, patient_id: str) -> None:
    """Delete a patient by their text patient_id."""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patients WHERE patient_id = ?', (patient_id,))
    conn.commit()


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
    return cycle


def get_cycles_by_patient(conn, patient_db_id: int) -> List[Cycle]:
    """Return all cycles for a patient ordered by cycle number."""
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, cycle_number, phase, planned_date, actual_date,
                  status, dose_percent, dose_reason, notes
           FROM cycles WHERE patient_id = ? ORDER BY cycle_number''',
        (patient_db_id,)
    )
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
    return lab


def get_labs_by_patient(conn, patient_db_id: int) -> List[Lab]:
    """Return all labs for a patient ordered by date."""
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, lab_date, anc, wbc, platelets, hemoglobin
           FROM labs WHERE patient_id = ? ORDER BY lab_date''',
        (patient_db_id,)
    )
    return [
        Lab(id=row[0], patient_id=row[1], lab_date=row[2], anc=row[3],
            wbc=row[4], platelets=row[5], hemoglobin=row[6])
        for row in cursor.fetchall()
    ]


def get_latest_lab(conn, patient_db_id: int) -> Optional[Lab]:
    """Return the most recent lab record for a patient, or None."""
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, patient_id, lab_date, anc, wbc, platelets, hemoglobin
           FROM labs WHERE patient_id = ? ORDER BY lab_date DESC LIMIT 1''',
        (patient_db_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Lab(id=row[0], patient_id=row[1], lab_date=row[2], anc=row[3],
               wbc=row[4], platelets=row[5], hemoglobin=row[6])
