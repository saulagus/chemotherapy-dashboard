"""Shared Sprint 9 report/export fixtures."""

import os
import sys
from datetime import date
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import config as config_module
from database import get_connection
from migrations import run_migrations
from models import Cycle, Lab, LvefAssessment, Patient
from reports.data import PatientReportData
from services.cycles import create_cycle
from services.gcsf import GcsfAdmin, create_gcsf
from services.infusion_reactions import InfusionReaction, create_reaction
from services.labs import create_lab
from services.lvef import create_lvef
from services.neuropathy import NeuropathyAssessment, create_neuropathy
from services.patients import create_patient
from services.symptoms import SymptomEntry, create_symptom


TODAY = date(2026, 1, 20)


def make_conn():
    conn = get_connection(':memory:')
    run_migrations(conn)
    return conn


def make_config(overrides=None):
    config_module.reset()
    return config_module.load(user_path='/nonexistent/path.yaml', overrides=overrides)


def seed_report_patient(conn):
    patient = create_patient(conn, Patient(
        patient_id='PT-RPT1',
        name='Report Patient',
        age=54,
        diagnosis_date=date(2025, 12, 1),
        start_date=date(2026, 1, 1),
        protocol='Dose-Dense AC-T',
        total_cycles=8,
        dose_density='dose_dense_q2w',
    ), actor='nurse_seed')

    cycle1 = create_cycle(conn, Cycle(
        patient_id=patient.id,
        cycle_number=1,
        phase='AC',
        actual_date=date(2026, 1, 1),
        status='completed',
        dose_percent=100.0,
        height_cm=170,
        weight_kg=65,
        anthracycline_agent='doxorubicin',
        dose_mg_total=105.12,
    ), actor='nurse_seed')

    cycle2 = create_cycle(conn, Cycle(
        patient_id=patient.id,
        cycle_number=2,
        phase='AC',
        actual_date=date(2026, 1, 15),
        status='completed',
        dose_percent=80.0,
        dose_reason='Neutropenia',
        height_cm=170,
        weight_kg=65,
        anthracycline_agent='doxorubicin',
        dose_mg_total=84.10,
    ), actor='nurse_seed')

    lab1 = create_lab(conn, Lab(
        patient_id=patient.id,
        lab_date=date(2026, 1, 8),
        anc=2.0,
        wbc=5.0,
        platelets=190.0,
        hemoglobin=12.3,
    ), actor='nurse_seed')
    lab2 = create_lab(conn, Lab(
        patient_id=patient.id,
        lab_date=date(2026, 1, 16),
        anc=1.1,
        wbc=4.0,
        platelets=130.0,
        hemoglobin=11.1,
    ), actor='nurse_seed')

    create_lvef(conn, LvefAssessment(
        patient_id=patient.id,
        assessment_date=date(2025, 12, 15),
        lvef_percent=65.0,
        modality='echo',
        context='baseline',
    ), actor='nurse_seed')
    create_lvef(conn, LvefAssessment(
        patient_id=patient.id,
        assessment_date=date(2026, 1, 17),
        lvef_percent=56.0,
        modality='echo',
        context='ad_hoc',
    ), actor='nurse_seed')

    create_neuropathy(conn, NeuropathyAssessment(
        patient_id=patient.patient_id,
        assessment_date='2026-01-16',
        sensory_grade=2,
        motor_grade=1,
        cycle_id=cycle2.id,
    ), actor='nurse_seed')
    create_reaction(conn, InfusionReaction(
        patient_id=patient.patient_id,
        cycle_id=cycle2.id,
        agent='paclitaxel',
        onset_min=20,
        severity_grade=2,
        symptoms_json='["flushing"]',
    ), actor='nurse_seed')
    create_gcsf(conn, GcsfAdmin(
        patient_id=patient.patient_id,
        cycle_id=cycle2.id,
        agent='pegfilgrastim',
        admin_date='2026-01-14',
        prophylaxis_type='secondary',
    ), actor='nurse_seed')
    create_symptom(conn, SymptomEntry(
        patient_id=patient.patient_id,
        cycle_id=cycle2.id,
        entry_date='2026-01-16',
        symptom='nausea',
        grade=3,
    ), actor='nurse_seed')

    return SimpleNamespace(
        patient=patient,
        cycle1=cycle1,
        cycle2=cycle2,
        lab1=lab1,
        lab2=lab2,
    )


def simple_report_data():
    latest_cycle = SimpleNamespace(
        cycle_number=2,
        actual_date=date(2026, 1, 15),
        anthracycline_agent='doxorubicin',
        dose_percent=80.0,
        bsa_m2=1.75,
        dose_mg_per_m2=48.0,
    )
    latest_labs = SimpleNamespace(
        lab_date=date(2026, 1, 16),
        anc=1.1,
        wbc=4.0,
        platelets=130.0,
        hemoglobin=11.1,
    )
    checklist = SimpleNamespace(
        worst_status='soft_block',
        rules=[
            SimpleNamespace(rule_id='anc_below_threshold', status='soft_block',
                            message='ANC below configured threshold'),
            SimpleNamespace(rule_id='labs_stale', status='pass',
                            message='Labs are fresh'),
        ],
    )
    return PatientReportData(
        patient_id='PT-RPT1',
        patient_name='Report Patient',
        patient_age=54,
        diagnosis_date=date(2025, 12, 1),
        protocol='Dose-Dense AC-T',
        phase='AC',
        cycle_number=2,
        next_cycle_date=date(2026, 1, 29),
        latest_cycle=latest_cycle,
        latest_labs=latest_labs,
        lab_history=[latest_labs],
        cumulative_total_mg_per_m2=108.0,
        cumulative_status='green',
        lvef_latest=SimpleNamespace(
            assessment_date=date(2026, 1, 17),
            lvef_percent=56.0,
            modality='echo',
        ),
        lvef_status='review',
        lvef_reason='LVEF drop requires review',
        neuropathy_effective_grade=2,
        reaction_latest=SimpleNamespace(severity_grade=2, agent='paclitaxel'),
        gcsf_latest=SimpleNamespace(agent='pegfilgrastim', admin_date=date(2026, 1, 14)),
        symptom_entries=[SimpleNamespace(symptom='nausea', grade=3)],
        last_checklist_result=checklist,
        recent_audit=[{'action': 'create'}, {'action': 'update'}, {'action': 'update'}],
        gcsf_dates=[date(2026, 1, 16)],
        generated_on=TODAY,
    )
