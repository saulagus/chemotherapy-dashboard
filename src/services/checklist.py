"""Checklist input-gathering service (US-033).

Assembles ChecklistInputs from every service in one call, then delegates
to clinical/precycle.run_checklist for the pure rule evaluation.
"""

from datetime import date
from typing import Optional

from clinical.cardiotoxicity import lvef_status
from clinical.neuropathy import effective_grade
from clinical.precycle import ChecklistInputs, ChecklistResult, run_checklist
from config import get as get_config
from models import get_cycles_by_patient, get_latest_lab, get_patient_by_db_id
from services.cycles import cumulative_dose
from services.lvef import get_baseline_lvef, list_lvef
from services.neuropathy import latest_neuropathy
from services.symptoms import latest_cycle_symptoms


def gather_inputs(
    conn,
    patient_db_id: int,
    cycle_number: int,
    planned_admin_date: date,
    nurse_attests_no_infection: bool = False,
) -> ChecklistInputs:
    """Collect all data needed by the pre-cycle rules from existing services."""
    patient = get_patient_by_db_id(conn, patient_db_id)
    phase = 'AC' if cycle_number <= 4 else 'T'
    dose_density = patient.dose_density if patient else None

    lab = get_latest_lab(conn, patient_db_id)
    latest_anc = lab.anc if lab else None
    latest_platelets = lab.platelets if lab else None
    latest_lab_draw_date = None
    if lab and lab.lab_date:
        d = lab.lab_date
        if isinstance(d, str):
            latest_lab_draw_date = date.fromisoformat(d)
        else:
            latest_lab_draw_date = d

    cum = cumulative_dose(conn, patient_db_id)

    lvef_s = None
    lvef_r = None
    if phase == 'AC':
        assessments = list_lvef(conn, patient_db_id)
        if assessments:
            latest_lvef = assessments[0]
            baseline = get_baseline_lvef(conn, patient_db_id)
            baseline_pct = baseline.lvef_percent if baseline else None
            cfg_lvef = get_config().cardiotoxicity.lvef.model_dump()
            result = lvef_status(latest_lvef.lvef_percent, baseline_pct, cfg_lvef)
            lvef_s = result['status']
            lvef_r = result['reason']

    neuro_grade = None
    patient_str_id = patient.patient_id if patient else None
    if patient_str_id:
        neuro = latest_neuropathy(conn, patient_str_id)
        if neuro:
            tox_cfg = get_config().toxicity.model_dump()
            neuro_grade = effective_grade(neuro.sensory_grade, neuro.motor_grade, tox_cfg)

    sym_grades = None
    if patient_str_id:
        symptoms = latest_cycle_symptoms(conn, patient_str_id)
        if symptoms:
            sym_grades = [s.grade for s in symptoms]

    return ChecklistInputs(
        phase=phase,
        cycle_number=cycle_number,
        dose_density=dose_density,
        planned_admin_date=planned_admin_date,
        latest_anc=latest_anc,
        latest_platelets=latest_platelets,
        latest_lab_draw_date=latest_lab_draw_date,
        nurse_attests_no_infection=nurse_attests_no_infection,
        cumulative_status=cum.status,
        cumulative_total_mg_per_m2=cum.total_mg_per_m2,
        lvef_status=lvef_s,
        lvef_reason=lvef_r,
        latest_neuropathy_grade=neuro_grade,
        latest_symptom_grades=sym_grades,
    )


def evaluate(
    conn,
    patient_db_id: int,
    cycle_number: int,
    planned_admin_date: date,
    nurse_attests_no_infection: bool = False,
) -> ChecklistResult:
    """Gather inputs and run the full pre-cycle checklist."""
    inputs = gather_inputs(
        conn, patient_db_id, cycle_number, planned_admin_date,
        nurse_attests_no_infection,
    )
    cfg = get_config()
    config_dict = {
        'precycle': cfg.precycle.model_dump(),
        'labs': cfg.labs.model_dump(),
    }
    return run_checklist(inputs, config_dict)
