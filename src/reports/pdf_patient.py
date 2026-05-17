"""Patient-facing plain-language PDF (Sprint 9 — US-035, stretch).

Sections: header (no jargon), next cycle date, latest labs with plain labels,
plain-language explainer keyed to worst checklist rule.
Acronyms expanded on first use. 6th-grade reading level target.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reports.data import PatientReportData

from reports.pdf_oncologist import (
    _PAGE_SIZES, _FONT, _FONT_BOLD,
    _FG, _FG_MUTED, _SEP, _STATUS_COLORS,
    _draw_footer, _fmt_date,
)

_ACRONYM_MAP = {
    'ANC': 'Absolute Neutrophil Count (ANC)',
    'WBC': 'White Blood Cell Count (WBC)',
    'Hgb': 'Hemoglobin (Hgb)',
    'Plt': 'Platelets (Plt)',
    'LVEF': 'Left Ventricular Ejection Fraction (LVEF)',
    'G-CSF': 'Growth Factor Support (G-CSF)',
    'AC': 'Adriamycin/Cyclophosphamide (AC)',
    'BSA': 'Body Surface Area (BSA)',
}

_ANC_PLAIN = {
    'normal': 'Your blood counts look good.',
    'low': 'Your white blood cell count is low.',
    'very_low': 'Your white blood cell count is very low — your care team has been notified.',
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

    inst_name = rpt_cfg.branding.institution_name or "Chemotherapy Dashboard"
    c.setFont(_FONT_BOLD, 14)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, "Your Treatment Summary")
    y -= 14

    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, y, f"{inst_name}  ·  {_fmt_date(data.generated_on)}")
    y -= 20

    c.setStrokeColorRGB(*_SEP)
    c.setLineWidth(0.4)
    c.line(margin, y, width - margin, y)
    y -= 14

    # Patient name
    c.setFont(_FONT_BOLD, 11)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, f"Name: {data.patient_name}")
    y -= 16

    # Next cycle
    c.setFont(_FONT_BOLD, 10)
    c.drawString(margin, y, "Your Next Treatment Appointment")
    y -= 12
    c.setFont(_FONT, 10)
    if data.next_cycle_date:
        c.drawString(margin, y, f"Planned date: {_fmt_date(data.next_cycle_date)}")
    else:
        c.drawString(margin, y, "Your next treatment date has not been scheduled yet.")
    y -= 18

    # Blood counts in plain language
    c.setFont(_FONT_BOLD, 10)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, "Your Blood Count Results")
    y -= 12
    c.setFont(_FONT, 9)
    if data.latest_labs:
        labs = data.latest_labs
        date_str = _fmt_date(labs.lab_date)
        c.drawString(margin, y, f"Date of blood draw: {date_str}")
        y -= 11

        if labs.anc is not None:
            anc_per_ul = labs.anc * 1000
            if anc_per_ul >= 1500:
                anc_label = 'Normal'
                anc_color = (0.30, 0.69, 0.31)
            elif anc_per_ul >= 500:
                anc_label = 'Low — your care team is monitoring this'
                anc_color = (1.00, 0.76, 0.03)
            else:
                anc_label = 'Very Low — contact your care team'
                anc_color = (0.88, 0.33, 0.33)

            c.setFillColorRGB(*anc_color)
            c.drawString(margin, y, f"Infection-fighting cells: {anc_label}")
            c.setFillColorRGB(*_FG)
            y -= 11

        if labs.hemoglobin is not None:
            hgb_label = 'Normal' if labs.hemoglobin >= 12 else 'Low — you may feel more tired than usual'
            c.drawString(margin, y, f"Hemoglobin (energy cells): {hgb_label} ({labs.hemoglobin:.1f} g/dL)")
            y -= 11

        if labs.platelets is not None:
            plt_label = 'Normal' if labs.platelets >= 100 else 'Low — be careful with cuts and bruises'
            c.drawString(margin, y, f"Platelets (clotting cells): {plt_label} ({labs.platelets:.0f})")
            y -= 11
    else:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No recent blood test results on file.")
        c.setFillColorRGB(*_FG)
        y -= 11

    y -= 8

    # Checklist summary in plain language
    if data.last_checklist_result:
        c.setFont(_FONT_BOLD, 10)
        c.setFillColorRGB(*_FG)
        c.drawString(margin, y, "Notes From Your Care Team")
        y -= 12
        c.setFont(_FONT, 9)
        y = _draw_plain_checklist(c, data, margin, y)

    _draw_footer(c, data, config, margin, width, height)
    c.save()
    buf.seek(0)
    return buf.read()


def _draw_plain_checklist(c, data, margin, y):
    result = data.last_checklist_result
    blocking_rules = [r for r in result.rules if r.status in ('soft_block', 'hard_block')]
    advisory_rules = [r for r in result.rules if r.status == 'advisory']

    _plain_messages = {
        'anc_below_threshold': 'Your white blood cell count is too low for treatment right now. Your team will reschedule.',
        'platelets_below_threshold': 'Your platelet count is low. Your team is watching this closely.',
        'labs_stale': 'Your blood test results may be out of date. Your team may need a new sample.',
        'active_infection': 'You may have an infection. Treatment will be paused until you recover.',
        'cumulative_red': 'Your heart medicine dose is getting high. Your team is monitoring your heart closely.',
        'cumulative_hard_stop': 'You have reached the maximum safe dose of heart medicine.',
        'lvef_abnormal': 'Your heart function test showed a change. A heart specialist will review.',
        'neuropathy_t_above_max': 'The nerve symptoms you reported are significant. Your team will adjust your treatment.',
        'symptoms_grade_3_or_higher': 'You have reported significant side effects. Please talk to your care team.',
    }

    if not blocking_rules and not advisory_rules:
        c.setFillColorRGB(0.30, 0.69, 0.31)
        c.drawString(margin, y, "Everything looks on track for your next appointment.")
        c.setFillColorRGB(*_FG)
        y -= 11
        return y

    for rule in blocking_rules:
        msg = _plain_messages.get(rule.rule_id, rule.message)
        c.setFillColorRGB(0.88, 0.33, 0.33)
        c.drawString(margin, y, f"• {msg}")
        c.setFillColorRGB(*_FG)
        y -= 11

    for rule in advisory_rules:
        msg = _plain_messages.get(rule.rule_id, rule.message)
        c.setFillColorRGB(1.00, 0.76, 0.03)
        c.drawString(margin, y, f"• {msg}")
        c.setFillColorRGB(*_FG)
        y -= 11

    return y
