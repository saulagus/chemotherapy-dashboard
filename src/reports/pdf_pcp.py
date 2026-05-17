"""PCP referral summary PDF template (Sprint 9 — US-035, stretch).

render(data, config) -> bytes — pure function.
One page: header, latest cycle, cumulative dose summary, latest labs,
toxicity one-paragraph, referral guidance keyed to worst checklist rule.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reports.data import PatientReportData

from reports.pdf_oncologist import (
    _PAGE_SIZES, _FONT, _FONT_BOLD,
    _FG, _FG_MUTED, _BG_ALT, _SEP, _STATUS_COLORS, _CUM_STATUS_COLORS,
    _draw_footer, _fmt_date,
)

_ACRONYM_MAP = {
    'ANC': 'Absolute Neutrophil Count (ANC)',
    'LVEF': 'Left Ventricular Ejection Fraction (LVEF)',
    'AC': 'Adriamycin/Cyclophosphamide (AC)',
    'BSA': 'Body Surface Area (BSA)',
    'CTCAE': 'Common Terminology Criteria for Adverse Events (CTCAE)',
}


def render(data: 'PatientReportData', config) -> bytes:
    from reportlab.pdfgen.canvas import Canvas

    rpt_cfg = config.reports
    page_size = _PAGE_SIZES.get(rpt_cfg.page_size, _PAGE_SIZES['letter'])
    margin = rpt_cfg.margin_in * 72
    width, height = page_size

    buf = io.BytesIO()
    c = Canvas(buf, pagesize=page_size, invariant=1)
    y = height - margin

    # Header
    inst_name = rpt_cfg.branding.institution_name or "Chemotherapy Dashboard"
    c.setFont(_FONT_BOLD, 13)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, f"{inst_name} — PCP Summary")
    y -= 16

    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, y, f"Patient: {data.patient_name}  ·  ID: {data.patient_id}  ·  "
                             f"Protocol: {data.protocol or 'N/A'}  ·  Generated: {_fmt_date(data.generated_on)}")
    y -= 20

    c.setStrokeColorRGB(*_SEP)
    c.setLineWidth(0.4)
    c.line(margin, y, width - margin, y)
    y -= 12

    # Latest cycle
    c.setFont(_FONT_BOLD, 9)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, "LATEST CYCLE")
    y -= 12
    c.setFont(_FONT, 9)
    if data.latest_cycle:
        cyc = data.latest_cycle
        c.drawString(margin, y, f"C{cyc.cycle_number}  ·  {_fmt_date(cyc.actual_date)}  ·  "
                                 f"Dose {cyc.dose_percent or 100:.0f}%  ·  {cyc.anthracycline_agent or 'N/A'}")
    else:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No completed cycles.")
        c.setFillColorRGB(*_FG)
    y -= 16

    # Cumulative dose
    c.setFont(_FONT_BOLD, 9)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, "CUMULATIVE DOSE")
    y -= 12
    color = _CUM_STATUS_COLORS.get(data.cumulative_status, _FG)
    c.setFillColorRGB(*color)
    c.setFont(_FONT, 9)
    c.drawString(margin, y, f"{data.cumulative_total_mg_per_m2:.1f} mg/m²  [{data.cumulative_status.upper()}]")
    c.setFillColorRGB(*_FG)
    y -= 16

    # Latest labs
    c.setFont(_FONT_BOLD, 9)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, "LATEST LABS")
    y -= 12
    c.setFont(_FONT, 9)
    if data.latest_labs:
        labs = data.latest_labs
        parts = []
        if labs.anc is not None:
            parts.append(f"ANC {labs.anc:.2f}")
        if labs.platelets is not None:
            parts.append(f"Plt {labs.platelets:.0f}")
        if labs.hemoglobin is not None:
            parts.append(f"Hgb {labs.hemoglobin:.1f}")
        c.drawString(margin, y, f"{_fmt_date(labs.lab_date)}  ·  " + '  ·  '.join(parts))
    else:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No labs on record.")
        c.setFillColorRGB(*_FG)
    y -= 16

    # Toxicity summary
    c.setFont(_FONT_BOLD, 9)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, "TOXICITY SUMMARY")
    y -= 12
    c.setFont(_FONT, 9)
    tox_lines = _build_toxicity_paragraph(data)
    for line in tox_lines:
        c.drawString(margin, y, line)
        y -= 11

    y -= 6

    # Referral guidance
    if rpt_cfg.pcp.include_referral_guidance and data.last_checklist_result:
        c.setFont(_FONT_BOLD, 9)
        c.setFillColorRGB(*_FG)
        c.drawString(margin, y, "REFERRAL GUIDANCE")
        y -= 12
        c.setFont(_FONT, 8)
        y = _draw_referral_guidance(c, data, margin, y)

    _draw_footer(c, data, config, margin, width, height)
    c.save()
    buf.seek(0)
    return buf.read()


def _build_toxicity_paragraph(data) -> list:
    lines = []
    grade = data.neuropathy_effective_grade
    if grade is not None:
        lines.append(f"Neuropathy: effective grade {grade}")
    if data.reaction_latest:
        r = data.reaction_latest
        lines.append(f"Infusion reaction: G{r.severity_grade}  agent {r.agent}")
    if data.symptom_entries:
        advisory = [s for s in data.symptom_entries if s.grade >= 3]
        if advisory:
            names = ', '.join(s.symptom.replace('_', ' ') for s in advisory)
            lines.append(f"Symptoms ≥G3: {names}")
    if not lines:
        lines = ["No significant toxicity on record."]
    return lines


def _draw_referral_guidance(c, data, margin, y):
    result = data.last_checklist_result
    worst_rule = None
    severity_order = {'hard_block': 3, 'soft_block': 2, 'advisory': 1, 'pass': 0}
    for rule in result.rules:
        if worst_rule is None or severity_order.get(rule.status, 0) > severity_order.get(worst_rule.status, 0):
            worst_rule = rule

    c.setFillColorRGB(*_FG_MUTED)
    if worst_rule and worst_rule.status != 'pass':
        msg = worst_rule.message
        guidance = _guidance_for_rule(worst_rule.rule_id)
        c.drawString(margin, y, f"Flag: {worst_rule.rule_id.replace('_', ' ')}")
        y -= 10
        c.drawString(margin, y, f"Detail: {msg[:80]}")
        y -= 10
        if guidance:
            c.drawString(margin, y, f"Action: {guidance}")
            y -= 10
    else:
        c.drawString(margin, y, "No active safety flags. Continue per protocol.")
        y -= 10

    c.setFillColorRGB(*_FG)
    return y


def _guidance_for_rule(rule_id: str) -> str:
    guidance = {
        'anc_below_threshold': 'Delay next cycle until ANC recovers. Consider G-CSF.',
        'platelets_below_threshold': 'Delay next cycle. Monitor platelet trend.',
        'labs_stale': 'Obtain fresh CBC before administering treatment.',
        'active_infection': 'Treat infection before proceeding with chemotherapy.',
        'cumulative_red': 'Review cardiology consultation. LVEF monitoring recommended.',
        'cumulative_hard_stop': 'Cumulative dose limit reached. Consult oncologist.',
        'lvef_abnormal': 'Cardiac function compromised. Hold anthracycline pending cardiology review.',
        'neuropathy_t_above_max': 'Neuropathy exceeds treatment threshold. Dose modification or hold required.',
        'symptoms_grade_3_or_higher': 'Grade 3+ symptoms present. Supportive care and reassessment needed.',
    }
    return guidance.get(rule_id, '')
