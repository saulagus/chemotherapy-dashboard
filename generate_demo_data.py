"""
generate_demo_data.py — Creates three deterministic demo patients for stakeholder demos.

Usage:
    python3 generate_demo_data.py

Always clears existing data first, then creates exactly:
  DEMO-001  "A. Rivera"   — Mid-treatment (5/8), Cycle 3 dose reduction, rich ANC history
  DEMO-002  "M. Chen"     — Early treatment (1/8), ready for live cycle completion
  DEMO-003  "P. Wallace"  — Treatment complete (8/8)
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_connection, create_tables
from models import Patient, Cycle, Lab, add_patient, add_cycle, add_lab


TODAY = date.today()


def clear_all_data(conn):
    cur = conn.cursor()
    cur.execute('DELETE FROM labs')
    cur.execute('DELETE FROM cycles')
    cur.execute('DELETE FROM patients')
    conn.commit()
    print("Cleared all existing data.")


# ---------------------------------------------------------------------------
# Demo Patient 1 — mid-treatment with dose reduction, all four ANC colors
# ---------------------------------------------------------------------------

def create_demo_patient_1(conn):
    """A. Rivera — 5/8 cycles complete, Cycle 3 at 75% (Neutropenia), ANC spanning all colors."""
    start = TODAY - timedelta(days=98)  # ~14 weeks ago (Dose-Dense: 14-day cycles)

    patient = add_patient(conn, Patient(
        patient_id     = 'DEMO-001',
        name           = 'A. Rivera',
        age            = 52,
        diagnosis_date = start - timedelta(days=45),
        start_date     = start,
        protocol       = 'Dose-Dense AC-T',
        total_cycles   = 8,
    ))

    cycle_data = [
        # (cycle_num, phase, days_offset, status, dose_percent, dose_reason)
        (1, 'AC', 0,  'completed', 100.0, None),
        (2, 'AC', 14, 'completed', 100.0, None),
        (3, 'AC', 28, 'completed', 75.0,  'Neutropenia'),   # <-- dose reduction
        (4, 'AC', 42, 'completed', 100.0, None),
        (5, 'T',  56, 'completed', 100.0, None),
        (6, 'T',  70, 'pending',   100.0, None),
        (7, 'T',  84, 'pending',   100.0, None),
        (8, 'T',  98, 'pending',   100.0, None),
    ]

    cycles = []
    for cn, phase, offset, status, dose_pct, dose_reason in cycle_data:
        planned = start + timedelta(days=offset)
        actual  = (planned + timedelta(days=1)) if status == 'completed' else None
        c = add_cycle(conn, Cycle(
            patient_id   = patient.id,
            cycle_number = cn,
            phase        = phase,
            planned_date = planned,
            actual_date  = actual,
            status       = status,
            dose_percent = dose_pct,
            dose_reason  = dose_reason,
        ))
        cycles.append(c)

    # Lab values designed to span all four ANC colors across the history
    lab_entries = [
        # (days_before_today, anc, wbc, platelets, hemoglobin)
        (90, 2.8, 4.2, 245, 13.2),   # green  — Cycle 1 pre-treatment, Normal
        (76, 1.8, 3.1, 210, 12.8),   # green  — Cycle 2, still Normal
        (62, 1.2, 2.4, 185, 12.1),   # yellow — Cycle 3, Mild Neutropenia (triggered dose mod)
        (48, 2.1, 3.5, 200, 11.9),   # green  — Cycle 4, recovering
        (34, 0.7, 1.8, 160, 11.4),   # orange — Cycle 5, Moderate Neutropenia
    ]

    for days_ago, anc, wbc, plt, hgb in lab_entries:
        add_lab(conn, Lab(
            patient_id = patient.id,
            lab_date   = TODAY - timedelta(days=days_ago),
            anc        = anc,
            wbc        = wbc,
            platelets  = plt,
            hemoglobin = hgb,
        ))

    print(f"  DEMO-001 A. Rivera — 5/8 cycles, Cycle 3 @ 75% (Neutropenia), 5 lab draws")
    return patient


# ---------------------------------------------------------------------------
# Demo Patient 2 — early treatment, ready for live cycle completion
# ---------------------------------------------------------------------------

def create_demo_patient_2(conn):
    """M. Chen — 1/8 cycles complete, Cycle 2 is current. Use for live demo."""
    start = TODAY - timedelta(days=21)

    patient = add_patient(conn, Patient(
        patient_id     = 'DEMO-002',
        name           = 'M. Chen',
        age            = 45,
        diagnosis_date = start - timedelta(days=30),
        start_date     = start,
        protocol       = 'Standard AC-T',
        total_cycles   = 8,
    ))

    cycle_data = [
        (1, 'AC', 0,  'completed', 100.0, None),
        (2, 'AC', 21, 'pending',   100.0, None),
        (3, 'AC', 42, 'pending',   100.0, None),
        (4, 'AC', 63, 'pending',   100.0, None),
        (5, 'T',  84, 'pending',   100.0, None),
        (6, 'T',  105,'pending',   100.0, None),
        (7, 'T',  126,'pending',   100.0, None),
        (8, 'T',  147,'pending',   100.0, None),
    ]

    for cn, phase, offset, status, dose_pct, dose_reason in cycle_data:
        planned = start + timedelta(days=offset)
        actual  = (planned + timedelta(days=0)) if status == 'completed' else None
        add_cycle(conn, Cycle(
            patient_id   = patient.id,
            cycle_number = cn,
            phase        = phase,
            planned_date = planned,
            actual_date  = actual,
            status       = status,
            dose_percent = dose_pct,
            dose_reason  = dose_reason,
        ))

    # One baseline lab draw
    add_lab(conn, Lab(
        patient_id = patient.id,
        lab_date   = TODAY - timedelta(days=19),
        anc        = 2.4,
        wbc        = 3.9,
        platelets  = 230,
        hemoglobin = 13.5,
    ))

    print(f"  DEMO-002 M. Chen — 1/8 cycles, Cycle 2 current (ready for live completion)")
    return patient


# ---------------------------------------------------------------------------
# Demo Patient 3 — treatment complete
# ---------------------------------------------------------------------------

def create_demo_patient_3(conn):
    """P. Wallace — all 8 cycles complete, treatment finished."""
    start = TODAY - timedelta(days=196)  # 28 weeks ago

    patient = add_patient(conn, Patient(
        patient_id     = 'DEMO-003',
        name           = 'P. Wallace',
        age            = 61,
        diagnosis_date = start - timedelta(days=60),
        start_date     = start,
        protocol       = 'Dose-Dense AC-T',
        total_cycles   = 8,
    ))

    for cn in range(1, 9):
        phase   = 'AC' if cn <= 4 else 'T'
        planned = start + timedelta(days=(cn - 1) * 14)
        actual  = planned + timedelta(days=1)
        add_cycle(conn, Cycle(
            patient_id   = patient.id,
            cycle_number = cn,
            phase        = phase,
            planned_date = planned,
            actual_date  = actual,
            status       = 'completed',
            dose_percent = 100.0,
            dose_reason  = None,
        ))

    lab_values = [
        (189, 3.1, 4.6, 260, 13.8),
        (175, 2.4, 3.8, 235, 13.1),
        (161, 1.6, 2.9, 210, 12.6),
        (147, 0.9, 2.1, 185, 12.0),
        (133, 1.4, 2.6, 195, 11.7),
        (119, 0.4, 1.3, 155, 11.2),
        (105, 1.1, 2.2, 170, 11.5),
        ( 91, 2.0, 3.3, 200, 12.1),
    ]

    for days_ago, anc, wbc, plt, hgb in lab_values:
        add_lab(conn, Lab(
            patient_id = patient.id,
            lab_date   = TODAY - timedelta(days=days_ago),
            anc        = anc,
            wbc        = wbc,
            platelets  = plt,
            hemoglobin = hgb,
        ))

    print(f"  DEMO-003 P. Wallace — 8/8 cycles complete, 8 lab draws (all ANC colors visible)")
    return patient


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    conn = get_connection()
    create_tables(conn)

    print("\nClearing existing data...")
    clear_all_data(conn)

    print("\nCreating demo patients...\n")
    create_demo_patient_1(conn)
    create_demo_patient_2(conn)
    create_demo_patient_3(conn)

    print("\nDemo data ready.")
    print("\nPatient roles:")
    print("  DEMO-001  A. Rivera   — Use for lab overview, ANC trend, dose modification story")
    print("  DEMO-002  M. Chen     — Use for live cycle completion during demo")
    print("  DEMO-003  P. Wallace  — Use to show completed treatment state")
    conn.close()


if __name__ == '__main__':
    main()
