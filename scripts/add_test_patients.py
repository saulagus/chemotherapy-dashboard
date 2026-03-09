"""Quick script to insert 2 test patients into the local database.

Run from the project root:
    python scripts/add_test_patients.py
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_connection, create_tables
from models import Patient, Cycle, add_patient, add_cycle


def main():
    conn = get_connection()
    create_tables(conn)

    # ── Patient 1 ─────────────────────────────────────────────────────────────
    p1 = add_patient(conn, Patient(
        patient_id='PT-001',
        name='Maria Torres',
        age=48,
        diagnosis_date=date(2025, 9, 10),
        start_date=date(2025, 10, 1),
        protocol='Dose-Dense',
        total_cycles=8,
    ))
    # 3 cycles completed, 1 pending
    add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=1, status='completed', actual_date=date(2025, 10, 1)))
    add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=2, status='completed', actual_date=date(2025, 10, 15)))
    add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=3, status='completed', actual_date=date(2025, 10, 29)))
    add_cycle(conn, Cycle(patient_id=p1.id, cycle_number=4, status='pending',   planned_date=date(2025, 11, 12)))
    print(f'Added: {p1.name} (id={p1.id}) — 3 completed, 1 pending')

    # ── Patient 2 ─────────────────────────────────────────────────────────────
    p2 = add_patient(conn, Patient(
        patient_id='PT-002',
        name='Linda Chen',
        age=55,
        diagnosis_date=date(2025, 11, 5),
        start_date=date(2025, 12, 1),
        protocol='Standard',
        total_cycles=8,
    ))
    # 1 cycle completed
    add_cycle(conn, Cycle(patient_id=p2.id, cycle_number=1, status='completed', actual_date=date(2025, 12, 1)))
    add_cycle(conn, Cycle(patient_id=p2.id, cycle_number=2, status='pending',   planned_date=date(2025, 12, 22)))
    print(f'Added: {p2.name} (id={p2.id}) — 1 completed, 1 pending')

    conn.close()
    print('\nDone. Run the app to see the patients in the list.')


if __name__ == '__main__':
    main()
