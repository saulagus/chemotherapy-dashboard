"""
generate_test_data.py — Synthetic data generator for AC-T Chemotherapy Dashboard.

Usage:
    python generate_test_data.py              # Generate 5 test patients
    python generate_test_data.py --patients 3 # Generate N test patients
    python generate_test_data.py --clear      # Clear all data
    python generate_test_data.py --clear --patients 5  # Clear then generate
"""

import sys
import os
import random
import argparse
from datetime import date, timedelta

# Add src/ to path so we can import models and database directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_connection, create_tables
from models import Patient, Cycle, Lab, add_patient, add_cycle, add_lab

# ---------------------------------------------------------------------------
# Patient profiles — fixed set for reproducible test scenarios
# ---------------------------------------------------------------------------

PROTOCOLS = ['Dose-Dense AC-T', 'Standard AC-T']

# Initials only — no real names stored in test data.
NAMES = ['M.R.', 'L.C.', 'A.T.', 'K.B.', 'S.M.',
         'J.P.', 'R.W.', 'T.N.', 'B.H.', 'D.F.']


def generate_patients(conn, count: int = 5) -> list[Patient]:
    """Insert `count` synthetic patients and return them with DB ids set."""
    today = date.today()
    patients = []

    for i in range(count):
        # Start date: random day within the past 6 months.
        days_ago = random.randint(14, 180)
        start_date = today - timedelta(days=days_ago)

        # Diagnosis typically 1-6 months before treatment started.
        diagnosis_date = start_date - timedelta(days=random.randint(30, 180))

        patient = add_patient(conn, Patient(
            patient_id     = f"TEST-{i + 1:03d}",
            name           = NAMES[i % len(NAMES)],
            age            = random.randint(40, 70),
            diagnosis_date = diagnosis_date,
            start_date     = start_date,
            protocol       = random.choice(PROTOCOLS),
            total_cycles   = 8,
        ))
        patients.append(patient)
        print(f"  Created patient: {patient.patient_id} — {patient.name} ({patient.protocol})")

    return patients


# ---------------------------------------------------------------------------
# Cycle progression
# ---------------------------------------------------------------------------

# Completed cycle counts by patient slot (0-indexed).
# Wraps around if more than 5 patients are generated.
CYCLE_PROFILES = [
    {'completed': lambda: random.randint(0, 2), 'dose_mods': False},  # early
    {'completed': lambda: random.randint(3, 5), 'dose_mods': False},  # mid
    {'completed': lambda: random.randint(6, 7), 'dose_mods': False},  # late
    {'completed': lambda: 8,                    'dose_mods': False},  # complete
    {'completed': lambda: random.randint(2, 4), 'dose_mods': True},   # dose mods
]

DOSE_MOD_PERCENTS = [75.0, 80.0, 85.0]
DOSE_MOD_REASONS  = ['Low ANC', 'Fatigue', 'Neuropathy']


def generate_cycles(conn, patient: Patient, profile_index: int) -> list[Cycle]:
    """Insert all 8 cycles for a patient; mark the first N as completed."""
    profile   = CYCLE_PROFILES[profile_index % len(CYCLE_PROFILES)]
    completed = profile['completed']()
    dose_mods = profile['dose_mods']

    # Interval between cycles depends on protocol.
    interval = 14 if 'Dose-Dense' in (patient.protocol or '') else 21

    cycles = []
    for cycle_number in range(1, 9):
        phase        = 'AC' if cycle_number <= 4 else 'T'
        planned_date = patient.start_date + timedelta(days=(cycle_number - 1) * interval)

        if cycle_number <= completed:
            status      = 'completed'
            actual_date = planned_date + timedelta(days=random.randint(0, 3))

            # Apply dose modification to some cycles when flagged.
            if dose_mods and random.random() < 0.6:
                dose_percent = random.choice(DOSE_MOD_PERCENTS)
                dose_reason  = random.choice(DOSE_MOD_REASONS)
            else:
                dose_percent = 100.0
                dose_reason  = None
        else:
            status       = 'pending'
            actual_date  = None
            dose_percent = 100.0
            dose_reason  = None

        cycle = add_cycle(conn, Cycle(
            patient_id   = patient.id,
            cycle_number = cycle_number,
            phase        = phase,
            planned_date = planned_date,
            actual_date  = actual_date,
            status       = status,
            dose_percent = dose_percent,
            dose_reason  = dose_reason,
        ))
        cycles.append(cycle)

    completed_count = sum(1 for c in cycles if c.status == 'completed')
    print(f"    Cycles: {completed_count}/8 completed"
          + (" (with dose mods)" if dose_mods else ""))
    return cycles


# ---------------------------------------------------------------------------
# Lab value generation
# ---------------------------------------------------------------------------

def generate_labs(conn, patient: Patient, cycles: list[Cycle]) -> None:
    """Insert one pre-treatment lab draw for each completed cycle.

    ANC trends downward over the course of treatment to simulate
    cumulative myelosuppression. WBC tracks ANC loosely; platelets
    and hemoglobin decline more gently.
    """
    completed = [c for c in cycles if c.status == 'completed']
    total     = len(completed)
    if total == 0:
        print("    Labs: none (no completed cycles)")
        return

    # Starting values — healthy baseline before treatment.
    anc_start = round(random.uniform(2.5, 4.0), 2)
    wbc_start = round(anc_start + random.uniform(0.5, 1.5), 2)
    plt_start = round(random.uniform(180, 280), 1)
    hgb_start = round(random.uniform(11.5, 14.0), 2)

    for i, cycle in enumerate(completed):
        # Downward trend factor: 0.0 at cycle 1, up to 0.6 at last cycle.
        trend = (i / max(total - 1, 1)) * 0.6

        anc = round(max(0.5, anc_start * (1 - trend) + random.uniform(-0.3, 0.3)), 2)
        wbc = round(max(0.8, wbc_start * (1 - trend * 0.8) + random.uniform(-0.4, 0.4)), 2)
        plt = round(max(50,  plt_start * (1 - trend * 0.4) + random.uniform(-20, 20)), 1)
        hgb = round(max(8.0, hgb_start * (1 - trend * 0.3) + random.uniform(-0.5, 0.5)), 2)

        # Lab drawn 2 days before the cycle's actual date.
        lab_date = (cycle.actual_date or cycle.planned_date) - timedelta(days=2)

        add_lab(conn, Lab(
            patient_id = patient.id,
            lab_date   = lab_date,
            anc        = anc,
            wbc        = wbc,
            platelets  = plt,
            hemoglobin = hgb,
        ))

    print(f"    Labs: {total} draws — ANC {anc_start} → {anc}")


# ---------------------------------------------------------------------------
# Clear all data
# ---------------------------------------------------------------------------

def clear_all_data(conn) -> None:
    """Delete all labs, cycles, and patients from the database."""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM labs')
    cursor.execute('DELETE FROM cycles')
    cursor.execute('DELETE FROM patients')
    conn.commit()
    print("All data cleared.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data for the AC-T Chemotherapy Dashboard."
    )
    parser.add_argument('--patients', type=int, default=5,
                        help="Number of patients to generate (default: 5)")
    parser.add_argument('--clear', action='store_true',
                        help="Clear all existing data before generating")
    args = parser.parse_args()

    conn = get_connection()
    create_tables(conn)

    if args.clear:
        clear_all_data(conn)

    print(f"\nGenerating {args.patients} patient(s)...\n")
    patients = generate_patients(conn, args.patients)

    for i, patient in enumerate(patients):
        print(f"\n  {patient.patient_id} — cycles & labs:")
        cycles = generate_cycles(conn, patient, profile_index=i)
        generate_labs(conn, patient, cycles)

    print(f"\nDone. {args.patients} patient(s) added to the database.")


if __name__ == '__main__':
    main()
