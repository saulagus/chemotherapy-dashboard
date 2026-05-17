"""Oncologist PDF template (Sprint 9 — US-035).

render(data, config) -> bytes — pure function, no DB/Tk imports.
Uses ReportLab built-in Helvetica only (no system fonts) for byte-stable output.
"""

from __future__ import annotations

import io
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reports.data import PatientReportData


_PAGE_SIZES = {
    'letter': (612, 792),
    'a4': (595, 842),
}

_FONT = 'Helvetica'
_FONT_BOLD = 'Helvetica-Bold'

# Status icon map for checklist rules
_RULE_ICONS = {
    'pass':       '✓',
    'advisory':   'ℹ',
    'soft_block': '⚠',
    'hard_block': '⛔',
}

_STATUS_COLORS = {
    'pass':       (0.30, 0.69, 0.31),   # green
    'advisory':   (1.00, 0.76, 0.03),   # yellow
    'soft_block': (1.00, 0.60, 0.00),   # orange
    'hard_block': (0.88, 0.33, 0.33),   # red
}

_CUM_STATUS_COLORS = {
    'green':     (0.30, 0.69, 0.31),
    'yellow':    (1.00, 0.76, 0.03),
    'red':       (0.88, 0.33, 0.33),
    'hard_stop': (0.88, 0.20, 0.20),
}

_FG       = (0.91, 0.92, 0.94)   # #e8eaf0
_FG_MUTED = (0.42, 0.46, 0.58)   # #6b7494
_BG       = (0.07, 0.08, 0.11)   # #12151c
_BG_ALT   = (0.10, 0.12, 0.16)   # #1a1e2a
_SEP      = (0.16, 0.19, 0.26)   # #2a2f42


def render(data: 'PatientReportData', config) -> bytes:
    """Render the oncologist PDF and return raw bytes."""
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader

    rpt_cfg = config.reports
    page_size = _PAGE_SIZES.get(rpt_cfg.page_size, _PAGE_SIZES['letter'])
    margin = rpt_cfg.margin_in * 72   # points
    width, height = page_size

    buf = io.BytesIO()
    c = Canvas(buf, pagesize=page_size, invariant=1)

    y = height - margin
    col_w = width - 2 * margin

    # ── Section 1: Header ────────────────────────────────────────────────────
    y = _draw_header(c, data, config, margin, width, height, y)
    y -= 6

    # ── Section 2: Latest cycle summary ──────────────────────────────────────
    y = _draw_section_title(c, "Latest Cycle", margin, y)
    y = _draw_latest_cycle(c, data, margin, col_w, y)
    y -= 6

    # ── Section 3: Cumulative anthracycline dose ──────────────────────────────
    y = _draw_section_title(c, "Cumulative Anthracycline Dose", margin, y)
    y = _draw_cumulative_dose(c, data, margin, col_w, y)
    y -= 6

    # ── Section 4: LVEF ───────────────────────────────────────────────────────
    y = _draw_section_title(c, "LVEF", margin, y)
    y = _draw_lvef(c, data, margin, col_w, y)
    y -= 6

    # ── Section 5: Latest labs ────────────────────────────────────────────────
    y = _draw_section_title(c, "Latest Labs", margin, y)
    y = _draw_labs(c, data, margin, col_w, y)
    y -= 6

    # ── Section 6: ANC trend chart ────────────────────────────────────────────
    if rpt_cfg.oncologist.include_anc_chart:
        y = _draw_anc_chart(c, data, config, margin, col_w, y)
        y -= 6

    # ── Section 7: Toxicity summary ───────────────────────────────────────────
    y = _draw_section_title(c, "Toxicity Summary", margin, y)
    y = _draw_toxicity(c, data, margin, col_w, y)
    y -= 6

    # ── Section 8: Pre-cycle checklist ────────────────────────────────────────
    y = _draw_section_title(c, "Pre-Cycle Checklist (Last Run)", margin, y)
    y = _draw_checklist(c, data, margin, col_w, y, page_size, margin)
    y -= 6

    # ── Section 9: Recent activity ────────────────────────────────────────────
    y = _draw_section_title(c, "Recent Activity", margin, y)
    y = _draw_recent_activity(c, data, config, margin, col_w, y)

    # ── Section 10: Footer ────────────────────────────────────────────────────
    _draw_footer(c, data, config, margin, width, height)

    c.save()
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _draw_header(c, data, config, margin, width, height, y):
    from reportlab.lib.colors import Color

    inst_name = config.reports.branding.institution_name or "Chemotherapy Dashboard"

    # Institution name
    c.setFont(_FONT_BOLD, 14)
    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, inst_name)
    y -= 18

    # Separator line
    c.setStrokeColorRGB(*_SEP)
    c.setLineWidth(0.5)
    c.line(margin, y, width - margin, y)
    y -= 12

    # Patient info two-column
    c.setFont(_FONT_BOLD, 10)
    c.setFillColorRGB(*_FG)
    dob_str = _fmt_date(data.diagnosis_date)
    c.drawString(margin, y, f"Patient: {data.patient_name}  ({data.patient_id})")
    c.drawString(margin + 280, y, f"Diagnosis: {dob_str}")
    y -= 14

    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG_MUTED)
    proto = data.protocol or 'N/A'
    phase = data.phase or 'N/A'
    cycle = data.cycle_number or 'N/A'
    age = f"Age {data.patient_age}" if data.patient_age else ''
    c.drawString(margin, y, f"Protocol: {proto}  ·  Phase: {phase}  ·  Cycle: {cycle}  ·  {age}")
    y -= 10

    next_str = _fmt_date(data.next_cycle_date)
    c.drawString(margin, y, f"Next cycle: {next_str}")
    y -= 16

    return y


def _draw_section_title(c, title, margin, y):
    c.setFont(_FONT_BOLD, 9)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, y, title.upper())
    y -= 4
    c.setStrokeColorRGB(*_SEP)
    c.setLineWidth(0.3)
    # separator drawn below title
    return y - 8


def _draw_latest_cycle(c, data, margin, col_w, y):
    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG)
    if data.latest_cycle is None:
        c.drawString(margin, y, "No completed cycles on record.")
        return y - 12

    cycle = data.latest_cycle
    date_str = _fmt_date(cycle.actual_date)
    agent = cycle.anthracycline_agent or 'N/A'
    dose_pct = cycle.dose_percent if cycle.dose_percent is not None else 100.0
    bsa = f"{cycle.bsa_m2:.2f} m²" if cycle.bsa_m2 else 'N/A'
    dpm2 = f"{cycle.dose_mg_per_m2:.1f} mg/m²" if cycle.dose_mg_per_m2 else 'N/A'

    c.drawString(margin, y,
        f"C{cycle.cycle_number} · {date_str} · {agent} · BSA {bsa} · {dpm2} · Dose {dose_pct:.0f}%")
    y -= 12

    if data.latest_cycle_dose_mods:
        mod = data.latest_cycle_dose_mods[0]
        c.setFont(_FONT, 8)
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin + 8, y, f"Dose reduction: {mod.prior_pct:.0f}% → {mod.dose_pct:.0f}%"
                                    f"  Reason: {mod.reason or 'N/A'}")
        y -= 10
        c.setFont(_FONT, 9)
        c.setFillColorRGB(*_FG)
    return y


def _draw_cumulative_dose(c, data, margin, col_w, y):
    total = data.cumulative_total_mg_per_m2
    status = data.cumulative_status
    color = _CUM_STATUS_COLORS.get(status, _FG)

    c.setFont(_FONT, 9)
    c.setFillColorRGB(*color)
    c.drawString(margin, y, f"{total:.1f} mg/m²  [{status.replace('_', ' ').upper()}]")
    y -= 12
    c.setFillColorRGB(*_FG)
    return y


def _draw_lvef(c, data, margin, col_w, y):
    c.setFont(_FONT, 9)
    if data.lvef_latest is None:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No LVEF assessments on record.")
        c.setFillColorRGB(*_FG)
        return y - 12

    lvef = data.lvef_latest
    status = data.lvef_status or 'ok'
    status_colors = {'ok': (0.30, 0.69, 0.31), 'review': (1.00, 0.76, 0.03), 'hold': (0.88, 0.33, 0.33)}
    color = status_colors.get(status, _FG)

    date_str = _fmt_date(lvef.assessment_date)
    c.setFillColorRGB(*color)
    c.drawString(margin, y, f"{lvef.lvef_percent:.0f}%  [{status.upper()}]  ·  {date_str}  ({lvef.modality})")
    y -= 12

    if data.lvef_reason:
        c.setFont(_FONT, 8)
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin + 8, y, data.lvef_reason)
        y -= 10
        c.setFont(_FONT, 9)

    c.setFillColorRGB(*_FG)
    return y


def _draw_labs(c, data, margin, col_w, y):
    c.setFont(_FONT, 9)
    if data.latest_labs is None:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No labs on record.")
        c.setFillColorRGB(*_FG)
        return y - 12

    labs = data.latest_labs
    date_str = _fmt_date(labs.lab_date)
    parts = []
    if labs.anc is not None:
        parts.append(f"ANC {labs.anc:.2f}")
    if labs.wbc is not None:
        parts.append(f"WBC {labs.wbc:.1f}")
    if labs.platelets is not None:
        parts.append(f"Plt {labs.platelets:.0f}")
    if labs.hemoglobin is not None:
        parts.append(f"Hgb {labs.hemoglobin:.1f}")

    # Age of labs in hours
    age_str = ''
    if data.generated_on and labs.lab_date:
        lab_d = labs.lab_date
        if isinstance(lab_d, str):
            from datetime import date as _date
            lab_d = _date.fromisoformat(lab_d)
        delta_h = (data.generated_on - lab_d).days * 24
        stale = ' ⚠ STALE' if delta_h > 72 else ''
        age_str = f"  (drawn {delta_h}h ago{stale})"

    c.setFillColorRGB(*_FG)
    c.drawString(margin, y, f"{date_str}  ·  " + '  ·  '.join(parts) + age_str)
    y -= 12
    return y


def _draw_anc_chart(c, data, config, margin, col_w, y):
    from reportlab.lib.utils import ImageReader
    import io as _io

    try:
        from reports.chart_png import render_anc_trend
        from models import get_labs_by_patient
    except ImportError:
        return y

    rpt_cfg = config.reports.oncologist
    size_in = rpt_cfg.chart_size_in
    chart_w = size_in[0] * 72
    chart_h = size_in[1] * 72

    if y - chart_h - 10 < 50:
        c.showPage()
        y = c._pagesize[1] - margin if hasattr(c, '_pagesize') else 700
        _draw_footer(c, data, config, margin, c._pagesize[0] if hasattr(c, '_pagesize') else 612, c._pagesize[1] if hasattr(c, '_pagesize') else 792)

    png_bytes = render_anc_trend(
        labs=_get_all_labs_for_report(data),
        gcsf_dates=data.gcsf_dates,
        size_in=size_in,
        config=config,
    )
    img = ImageReader(_io.BytesIO(png_bytes))
    c.drawImage(img, margin, y - chart_h, width=chart_w, height=chart_h)
    return y - chart_h - 10


def _get_all_labs_for_report(data):
    """Return list of lab objects from data if available, else empty list."""
    return list(getattr(data, 'lab_history', []) or [])


def _draw_toxicity(c, data, margin, col_w, y):
    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG)

    lines = []

    # Neuropathy
    grade = data.neuropathy_effective_grade
    if grade is not None:
        lines.append(f"Neuropathy: effective G{grade}")
    else:
        lines.append("Neuropathy: no assessment")

    # Infusion reaction
    if data.reaction_latest:
        r = data.reaction_latest
        lines.append(f"Reaction: last G{r.severity_grade}  {r.agent}")
    else:
        lines.append("Reaction: none recorded")

    # G-CSF
    if data.gcsf_latest:
        g = data.gcsf_latest
        d = _fmt_date(g.admin_date)
        lines.append(f"G-CSF: {g.agent}  ·  {d}")
    else:
        lines.append("G-CSF: none recorded")

    # Symptoms
    if data.symptom_entries:
        advisory = [s for s in data.symptom_entries if s.grade >= 3]
        if advisory:
            names = ', '.join(s.symptom.replace('_', ' ') for s in advisory)
            lines.append(f"Symptoms ≥G3: {names}")
        else:
            lines.append("Symptoms: all below G3")
    else:
        lines.append("Symptoms: none recorded")

    for line in lines:
        c.drawString(margin, y, line)
        y -= 11

    return y


def _draw_checklist(c, data, margin, col_w, y, page_size, pg_margin):
    c.setFont(_FONT, 9)
    if data.last_checklist_result is None:
        c.setFillColorRGB(*_FG_MUTED)
        c.drawString(margin, y, "No checklist data available.")
        c.setFillColorRGB(*_FG)
        return y - 12

    result = data.last_checklist_result

    # Worst status banner
    worst = result.worst_status
    banner_color = _STATUS_COLORS.get(worst, _FG)
    c.setFillColorRGB(*banner_color)
    c.setFont(_FONT_BOLD, 9)
    c.drawString(margin, y, f"Overall: {worst.replace('_', ' ').upper()}")
    y -= 12

    c.setFont(_FONT, 8)
    for rule in result.rules:
        if y < pg_margin + 20:
            c.showPage()
            y = page_size[1] - pg_margin
        icon = _RULE_ICONS.get(rule.status, '?')
        color = _STATUS_COLORS.get(rule.status, _FG)
        c.setFillColorRGB(*color)
        c.drawString(margin + 4, y, f"{icon}  {rule.rule_id.replace('_', ' ')}")
        c.setFillColorRGB(*_FG_MUTED)
        # Truncate long messages
        msg = rule.message[:80] + '…' if len(rule.message) > 80 else rule.message
        c.drawString(margin + 160, y, msg)
        y -= 10

    c.setFillColorRGB(*_FG)
    return y


def _draw_recent_activity(c, data, config, margin, col_w, y):
    c.setFont(_FONT, 9)
    c.setFillColorRGB(*_FG_MUTED)
    days = config.reports.oncologist.recent_activity_days
    c.drawString(margin, y, f"Last {days} days  ·  {len(data.recent_audit)} events")
    y -= 10

    # Summarize by action type
    from collections import Counter
    counts = Counter(row['action'] for row in data.recent_audit)
    summary_parts = [f"{cnt} {action.replace('_', ' ')}" for action, cnt in counts.most_common(6)]
    if summary_parts:
        c.setFont(_FONT, 8)
        c.setFillColorRGB(*_FG)
        c.drawString(margin, y, '  ·  '.join(summary_parts))
        y -= 10

    return y


def _draw_footer(c, data, config, margin, width, height):
    footer_text = config.reports.branding.footer_text
    generated = _fmt_date(data.generated_on)
    c.setFont(_FONT, 7)
    c.setFillColorRGB(*_FG_MUTED)
    c.drawString(margin, margin - 10, f"{footer_text}  ·  Generated {generated}")
    c.drawRightString(width - margin, margin - 10, "Page 1")


def _fmt_date(d) -> str:
    if d is None:
        return 'N/A'
    if isinstance(d, str):
        return d
    if hasattr(d, 'isoformat'):
        return d.isoformat()
    return str(d)
