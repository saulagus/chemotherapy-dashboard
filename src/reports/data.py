"""Patient report data assembler (Sprint 9 — US-035).

gather() calls every relevant service exactly once and assembles PatientReportData.
No DB calls inside templates — all data flows through this module.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class PatientReportData:
    # Header
    patient_id: str
    patient_name: str
    patient_age: Optional[int]
    diagnosis_date: Optional[date]
    protocol: Optional[str]
    phase: Optional[str]
    cycle_number: Optional[int]
    next_cycle_date: Optional[date]

    # Latest cycle
    latest_cycle: Optional[Any]          # Cycle dataclass or None
    latest_cycle_dose_mods: List[Any] = field(default_factory=list)  # list[DoseMod]

    # Cardiotoxicity
    cumulative_total_mg_per_m2: float = 0.0
    cumulative_status: str = "green"
    lvef_latest: Optional[Any] = None    # LvefAssessment or None
    lvef_status: Optional[str] = None
    lvef_reason: Optional[str] = None

    # Labs
    latest_labs: Optional[Any] = None    # Lab dataclass or None
    lab_history: List[Any] = field(default_factory=list)  # list[Lab], oldest -> newest

    # Toxicity summary
    neuropathy_latest: Optional[Any] = None
    neuropathy_effective_grade: Optional[int] = None
    reaction_latest: Optional[Any] = None
    gcsf_latest: Optional[Any] = None
    symptom_entries: List[Any] = field(default_factory=list)

    # Pre-cycle checklist
    last_checklist_result: Optional[Any] = None  # ChecklistResult or None

    # Audit / recent activity
    recent_audit: List[Dict] = field(default_factory=list)

    # All dose modifications
    dose_mod_history: List[Any] = field(default_factory=list)  # list[DoseMod]

    # G-CSF dates for chart
    gcsf_dates: List[date] = field(default_factory=list)

    # Report metadata
    generated_on: Optional[date] = None


def gather(conn, patient_id: int, config, today: date) -> PatientReportData:
    """Assemble all report data from services. Single entry point for all templates."""
    from models import get_patient_by_db_id, get_cycles_by_patient, get_latest_lab, get_labs_by_patient
    from services.cycles import cumulative_dose, last_completed_cycle_date
    from services.lvef import list_lvef, get_baseline_lvef
    from services.neuropathy import latest_neuropathy
    from services.infusion_reactions import latest_reaction
    from services.gcsf import latest_gcsf, gcsf_dates_for_patient
    from services.symptoms import latest_cycle_symptoms
    from services.audit import get_audit_for_patient
    from services.dose_modifications import list_for_patient, list_for_cycle
    from clinical.scheduling import cycle_status, expected_cycle_date
    from clinical.cardiotoxicity import lvef_status as compute_lvef_status
    from clinical.neuropathy import effective_grade as compute_neuropathy_grade

    patient = get_patient_by_db_id(conn, patient_id)
    if patient is None:
        raise LookupError(f"patient id={patient_id} not found")

    patient_str_id = patient.patient_id

    # Cumulative dose
    cum_summary = cumulative_dose(conn, patient_id)

    # LVEF — latest non-deleted assessment
    lvef_list = list_lvef(conn, patient_id)
    lvef_rec = lvef_list[0] if lvef_list else None
    baseline_lvef = get_baseline_lvef(conn, patient_id)
    lv_status, lv_reason = None, None
    if lvef_rec is not None:
        lvef_cfg = config.cardiotoxicity.lvef.model_dump()
        baseline_pct = baseline_lvef.lvef_percent if baseline_lvef else None
        result = compute_lvef_status(lvef_rec.lvef_percent, baseline_pct, lvef_cfg)
        lv_status = result['status']
        lv_reason = result.get('reason')

    # Latest labs
    labs = get_latest_lab(conn, patient_id)
    lab_history = get_labs_by_patient(conn, patient_id)

    # Neuropathy
    neuro = latest_neuropathy(conn, patient_str_id)
    neuro_grade = None
    if neuro is not None:
        try:
            neuro_grade = compute_neuropathy_grade(
                neuro.sensory_grade, neuro.motor_grade, config.toxicity.model_dump()
            )
        except Exception:
            neuro_grade = max(neuro.sensory_grade, neuro.motor_grade)

    # Infusion reaction
    reaction = latest_reaction(conn, patient_str_id)

    # G-CSF
    gcsf = latest_gcsf(conn, patient_str_id)
    gcsf_dates = gcsf_dates_for_patient(conn, patient_str_id,
                                        window_days=config.toxicity.gcsf.stimulated_window_days)

    # Symptoms
    symptoms = latest_cycle_symptoms(conn, patient_str_id)

    # Cycle data
    cycles = get_cycles_by_patient(conn, patient_id)
    completed = [c for c in cycles if c.status == 'completed']
    latest_cycle = max(completed, key=lambda c: c.cycle_number) if completed else None
    latest_cycle_mods = list_for_cycle(conn, latest_cycle.id) if latest_cycle and latest_cycle.id else []

    # Scheduling — derive phase, cycle number, next cycle date from latest completed cycle
    phase = latest_cycle.phase if latest_cycle else None
    cycle_num = latest_cycle.cycle_number if latest_cycle else None
    next_date = None
    if latest_cycle and latest_cycle.actual_date:
        last_date = latest_cycle.actual_date
        if isinstance(last_date, str):
            last_date = date.fromisoformat(last_date)
        try:
            next_date = expected_cycle_date(
                last_date, patient.dose_density, config.scheduling.model_dump()
            )
        except Exception:
            next_date = None

    # Pre-cycle checklist — last run
    last_checklist = _load_last_checklist(conn, patient_id, today, config, cum_summary,
                                          lv_status, lv_reason, neuro_grade, symptoms,
                                          phase, cycle_num, patient)

    # Audit
    recent_days = config.reports.oncologist.recent_activity_days
    all_audit = get_audit_for_patient(conn, patient_id)
    cutoff = today.replace(year=today.year - 1) if recent_days > 365 else \
        date.fromordinal(today.toordinal() - recent_days)
    recent_audit = [
        row for row in all_audit
        if _audit_ts_date(row['ts']) >= cutoff.isoformat()
    ]

    # All dose mods
    all_mods = list_for_patient(conn, patient_id)

    return PatientReportData(
        patient_id=patient_str_id,
        patient_name=patient.name,
        patient_age=patient.age,
        diagnosis_date=patient.diagnosis_date,
        protocol=patient.protocol,
        phase=phase,
        cycle_number=cycle_num,
        next_cycle_date=next_date,
        latest_cycle=latest_cycle,
        latest_cycle_dose_mods=latest_cycle_mods,
        cumulative_total_mg_per_m2=cum_summary.total_mg_per_m2,
        cumulative_status=cum_summary.status,
        lvef_latest=lvef_rec,
        lvef_status=lv_status,
        lvef_reason=lv_reason,
        latest_labs=labs,
        lab_history=lab_history,
        neuropathy_latest=neuro,
        neuropathy_effective_grade=neuro_grade,
        reaction_latest=reaction,
        gcsf_latest=gcsf,
        gcsf_dates=gcsf_dates,
        symptom_entries=symptoms,
        last_checklist_result=last_checklist,
        recent_audit=recent_audit,
        dose_mod_history=all_mods,
        generated_on=today,
    )


def _load_last_checklist(conn, patient_id, today, config, cum_summary,
                         lv_status, lv_reason, neuro_grade, symptoms,
                         phase, cycle_num, patient):
    """Run the pre-cycle checklist against latest data; returns ChecklistResult or None."""
    try:
        from clinical.precycle import ChecklistInputs, run_checklist
        from models import get_latest_lab

        labs = get_latest_lab(conn, patient_id)
        if phase is None or cycle_num is None:
            return None

        inputs = ChecklistInputs(
            phase=phase or 'AC',
            cycle_number=cycle_num or 1,
            dose_density=patient.dose_density,
            planned_admin_date=today,
            latest_anc=labs.anc if labs else None,
            latest_platelets=labs.platelets if labs else None,
            latest_lab_draw_date=labs.lab_date if labs else None,
            nurse_attests_no_infection=False,
            cumulative_status=cum_summary.status,
            cumulative_total_mg_per_m2=cum_summary.total_mg_per_m2,
            lvef_status=lv_status,
            lvef_reason=lv_reason,
            latest_neuropathy_grade=neuro_grade,
            latest_symptom_grades=[s.grade for s in symptoms] if symptoms else None,
        )
        return run_checklist(inputs, config.model_dump())
    except Exception:
        return None


def _audit_ts_date(ts) -> str:
    """Return an ISO date string from an audit timestamp value."""
    if hasattr(ts, 'date'):
        return ts.date().isoformat()
    return str(ts)[:10]
