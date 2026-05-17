"""Print-friendly dashboard snapshot PDF (Sprint 9 — US-038).

render(data, config) -> bytes — pure function.
Full-width single-page portrait snapshot reusing PatientReportData.
No chart embed (this is a snapshot, not a referral artifact).
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reports.data import PatientReportData

from reports.pdf_oncologist import (
    _PAGE_SIZES, _FONT, _FONT_BOLD,
    _FG, _FG_MUTED, _SEP, _STATUS_COLORS, _CUM_STATUS_COLORS,
    _draw_footer, _fmt_date,
)


def render(data: 'PatientReportData', config) -> bytes:
    from reportlab.pdfgen.canvas import Canvas

    rpt_cfg = config.reports
    pd_cfg = rpt_cfg.print_dashboard
    if pd_cfg.orientation == 'landscape':
        base = _PAGE_SIZES.get(rpt_cfg.page_size, _PAGE_SIZES['letter'])
        page_size = (base[1], base[0])
    else:
        page_size = _PAGE_SIZES.get(rpt_cfg.page_size, _PAGE_SIZES['letter'])

    margin = rpt_cfg.margin_in * 72
    width, height = page_size

    buf = io.BytesIO()
    c = Canvas(buf, pagesize=page_size, invariant=1)
    y = height - margin

    inst_name = rpt_cfg.branding.institution_name or "Chemotherapy Dashboard"
    c.setFont(_FONT_BOLD, 12)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, f"{inst_name} — Dashboard Snapshot")
    y -= 14

    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, y, f"{data.patient_name}  ·  {data.patient_id}  ·  {_fmt_date(data.generated_on)}")
    y -= 16

    c.setStrokeColorRGB(*_SEP)
    c.setLineWidth(0.4)
    c.line(margin, y, width - margin, y)
    y -= 12

    # Header info
    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, f"Protocol: {data.protocol or 'N/A'}  ·  Phase: {data.phase or 'N/A'}  ·  "
                             f"Cycle: {data.cycle_number or 'N/A'}  ·  Age: {data.patient_age or 'N/A'}")
    y -= 16

    # Latest cycle
    y = _section(c, "LATEST CYCLE", margin, y)
    if data.latest_cycle:
        cyc = data.latest_cycle
        c.setFont(_FONT, 9)
        c.setFillColorRGB(*_FG)
        c.drawString(margin, y, f"C{cyc.cycle_number}  {_fmt_date(cyc.actual_date)}  "
                                 f"dose {cyc.dose_percent or 100:.0f}%  {cyc.anthracycline_agent or ''}")
    else:
        c.setFont(_FONT, 9)
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No completed cycles.")
    y -= 14

    # Latest labs
    y = _section(c, "LATEST LABS", margin, y)
    c.setFont(_FONT, 9)
    if data.latest_labs:
        labs = data.latest_labs
        parts = []
        if labs.anc is not None: parts.append(f"ANC {labs.anc:.2f}")
        if labs.wbc is not None: parts.append(f"WBC {labs.wbc:.1f}")
        if labs.platelets is not None: parts.append(f"Plt {labs.platelets:.0f}")
        if labs.hemoglobin is not None: parts.append(f"Hgb {labs.hemoglobin:.1f}")
        c.setFillColorRGB(*_FG)
        c.drawString(margin, y, f"{_fmt_date(labs.lab_date)}  ·  " + '  ·  '.join(parts))
    else:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No labs on record.")
    y -= 14

    # Toxicity summary
    y = _section(c, "TOXICITY", margin, y)
    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG)
    tox_parts = []
    if data.neuropathy_effective_grade is not None:
        tox_parts.append(f"Neuro G{data.neuropathy_effective_grade}")
    if data.reaction_latest:
        tox_parts.append(f"Rxn G{data.reaction_latest.severity_grade}")
    if data.gcsf_latest:
        tox_parts.append(f"G-CSF {data.gcsf_latest.agent}")
    c.drawString(margin, y, '  ·  '.join(tox_parts) if tox_parts else "No toxicity data.")
    y -= 14

    # Checklist last outcome
    y = _section(c, "PRE-CYCLE CHECKLIST", margin, y)
    c.setFont(_FONT, 9)
    if data.last_checklist_result:
        worst = data.last_checklist_result.worst_status
        color = _STATUS_COLORS.get(worst, _FG)
        c.setFillColorRGB(*color)
        c.drawString(margin, y, f"Overall: {worst.replace('_', ' ').upper()}")
        c.setFillColorRGB(*_FG)
        y -= 11
        for rule in data.last_checklist_result.rules:
            if rule.status != 'pass':
                c.setFont(_FONT, 8)
                c.setFillColorRGB(*_STATUS_COLORS.get(rule.status, _FG_MUTED))
                c.drawString(margin + 6, y, f"{rule.rule_id.replace('_', ' ')}  —  {rule.message[:70]}")
                y -= 9
        c.setFillColorRGB(*_FG)
    else:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No checklist data.")
    y -= 14

    # Recent activity
    y = _section(c, "RECENT ACTIVITY", margin, y)
    days = config.reports.print_dashboard.recent_activity_days
    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, y, f"{len(data.recent_audit)} events in last {days} days")
    y -= 10

    from collections import Counter
    counts = Counter(row['action'] for row in data.recent_audit)
    summary = '  ·  '.join(f"{cnt} {act.replace('_', ' ')}" for act, cnt in counts.most_common(5))
    if summary:
        c.setFont(_FONT, 8)
        c.drawString(margin, y, summary)
        y -= 10

    _draw_footer(c, data, config, margin, width, height)
    c.save()
    buf.seek(0)
    return buf.read()


def _section(c, title, margin, y):
    c.setFont(_FONT_BOLD, 8)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, y, title)
    y -= 10
    return y
