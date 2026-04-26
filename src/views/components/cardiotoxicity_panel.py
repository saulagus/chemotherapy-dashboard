import tkinter as tk
from datetime import date
from tkinter import messagebox

import config
from clinical.cardiotoxicity import lvef_status
from services.cycles import cumulative_dose
from services.lvef import delete_lvef, get_baseline_lvef, list_lvef
from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)

_STATUS_COLOR = {
    'ok':     '#4CAF50',
    'review': '#FFC107',
    'hold':   '#F44336',
}

_CUMULATIVE_COLOR = {
    'green':     '#4CAF50',
    'yellow':    '#FFC107',
    'red':       '#F44336',
    'hard_stop': '#F44336',
}

_CUMULATIVE_BADGE = {
    'yellow':    'ADVISORY',
    'red':       'HOLD',
    'hard_stop': 'HARD STOP',
}


class CardiotoxicityPanel(tk.Frame):
    """Cardiotoxicity summary panel shown in the patient dashboard.

    Shows cumulative anthracycline dose (badge + meter) and LVEF history.

    Public API
    ----------
    load_patient(patient_id) — switch patient context and refresh
    refresh()                — reload from DB and redraw
    """

    def __init__(self, parent, conn, on_add_lvef=None, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn          = conn
        self.patient_id    = None
        self.on_add_lvef   = on_add_lvef
        self._content      = None
        self._meter_canvas = None

        self._build_header()
        self.refresh()

    # ── Static header ──────────────────────────────────────────────────────────

    def _build_header(self):
        header_row = tk.Frame(self, bg=BG_ALT, padx=16)
        header_row.pack(fill='x', pady=(14, 0))

        tk.Label(header_row, text="Cardiac Assessment",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(side='left')

        if self.on_add_lvef is not None:
            add_btn = tk.Label(header_row, text="+ Add LVEF",
                               font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED,
                               cursor='hand2')
            add_btn.pack(side='right')
            add_btn.bind('<Button-1>', lambda e: self.on_add_lvef())
            add_btn.bind('<Enter>', lambda e: add_btn.config(fg=FG))
            add_btn.bind('<Leave>', lambda e: add_btn.config(fg=FG_MUTED))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x', padx=16, pady=(8, 0))

    # ── Dynamic content ────────────────────────────────────────────────────────

    def _clear_content(self):
        if self._content is not None:
            self._content.destroy()
        self._content = tk.Frame(self, bg=BG_ALT)
        self._content.pack(fill='x', padx=16, pady=12)

    def refresh(self):
        """Reload cumulative dose and LVEF records from DB and redraw."""
        self._clear_content()

        if self.patient_id is None:
            self._show_empty("No patient selected.")
            return

        cfg = config.get().cardiotoxicity
        summary = cumulative_dose(self.conn, self.patient_id)
        self._show_cumulative(summary, cfg.cumulative_thresholds_mg_per_m2)

        tk.Frame(self._content, bg=SEPARATOR, height=1).pack(fill='x', pady=(10, 8))

        assessments = list_lvef(self.conn, self.patient_id)
        baseline = get_baseline_lvef(self.conn, self.patient_id)
        lvef_cfg = cfg.lvef.model_dump()

        if not assessments:
            self._show_empty("No LVEF assessments recorded.")
        else:
            self._show_lvef(assessments, baseline, lvef_cfg)

    def _show_cumulative(self, summary, thresholds):
        label_row = tk.Frame(self._content, bg=BG_ALT)
        label_row.pack(anchor='w', fill='x')

        tk.Label(label_row, text="Cumulative Anthracycline Dose",
                 font=('Arial', FONT_LABEL, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(side='left')

        value_row = tk.Frame(self._content, bg=BG_ALT)
        value_row.pack(anchor='w', fill='x', pady=(2, 0))

        color = _CUMULATIVE_COLOR.get(summary.status, FG)
        tk.Label(value_row,
                 text=f"{summary.total_mg_per_m2:.1f} mg/m² dox-equiv",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG_ALT, fg=color,
                 anchor='w').pack(side='left')

        if summary.status in _CUMULATIVE_BADGE:
            tk.Label(value_row,
                     text=f"  [{_CUMULATIVE_BADGE[summary.status]}]",
                     font=('Arial', FONT_LABEL, 'bold'), bg=BG_ALT,
                     fg=color).pack(side='left')

        hint = (
            f"Thresholds: {thresholds.yellow:.0f} advisory"
            f" · {thresholds.red:.0f} hold"
            f" · {thresholds.hard_stop:.0f} hard stop mg/m²"
        )
        tk.Label(self._content, text=hint,
                 font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                 anchor='w').pack(anchor='w', pady=(2, 0))

        canvas = tk.Canvas(self._content, height=26, bg=BG_ALT,
                           highlightthickness=0, bd=0)
        canvas.pack(fill='x', pady=(6, 0))
        self._meter_canvas = canvas
        canvas.bind('<Configure>',
                    lambda e, s=summary, t=thresholds:
                    self._draw_meter(canvas, e.width,
                                     s.total_mg_per_m2, s.status, t))

    def _draw_meter(self, canvas, width, total, status, thresholds):
        canvas.delete('all')
        if width <= 1:
            return
        bar_h    = 10
        max_dose = thresholds.hard_stop * 1.1

        def px(dose):
            return max(0, min(int(dose / max_dose * width), width))

        # Zone tint backgrounds
        canvas.create_rectangle(0, 0, px(thresholds.yellow), bar_h,
                                 fill='#1a2e1a', outline='')
        canvas.create_rectangle(px(thresholds.yellow), 0, px(thresholds.red), bar_h,
                                 fill='#2e2810', outline='')
        canvas.create_rectangle(px(thresholds.red), 0, px(thresholds.hard_stop), bar_h,
                                 fill='#2e1010', outline='')

        # Filled bar in status color
        if total > 0:
            fill_px = px(min(total, max_dose))
            color   = _CUMULATIVE_COLOR.get(status, '#4CAF50')
            canvas.create_rectangle(0, 0, fill_px, bar_h, fill=color, outline='')

        # Tick marks + threshold labels
        for dose, label in [
            (thresholds.yellow,    f'{thresholds.yellow:.0f}'),
            (thresholds.red,       f'{thresholds.red:.0f}'),
            (thresholds.hard_stop, f'{thresholds.hard_stop:.0f}'),
        ]:
            x = px(dose)
            canvas.create_line(x, 0, x, bar_h + 3, fill=SEPARATOR, width=1)
            canvas.create_text(x, bar_h + 4, text=label,
                               font=('Arial', FONT_HINT), fill=FG_MUTED, anchor='n')

    def _show_empty(self, message: str):
        tk.Label(self._content, text=message,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                 justify='left', anchor='w').pack(anchor='w', pady=(4, 8))

        if self.on_add_lvef is not None:
            btn = tk.Label(self._content, text="+ Add LVEF",
                           font=('Arial', FONT_LABEL, 'bold'),
                           bg=BG_ALT, fg='#4CAF50', cursor='hand2')
            btn.pack(anchor='w')
            btn.bind('<Button-1>', lambda e: self.on_add_lvef())
            btn.bind('<Enter>', lambda e: btn.config(fg='#81C784'))
            btn.bind('<Leave>', lambda e: btn.config(fg='#4CAF50'))

    def _show_lvef(self, assessments, baseline, lvef_cfg):
        latest = assessments[0]

        # ── Summary row ───────────────────────────────────────────────────────
        summary_row = tk.Frame(self._content, bg=BG_ALT)
        summary_row.pack(anchor='w', fill='x', pady=(0, 8))

        # Compute status
        baseline_pct = baseline.lvef_percent if baseline else None
        status_info = lvef_status(latest.lvef_percent, baseline_pct, lvef_cfg)
        status_color = _STATUS_COLOR.get(status_info['status'], FG)

        # LVEF value + modality + date
        d = latest.assessment_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        date_str = d.strftime("%b %d, %Y")
        modality = latest.modality.upper() if latest.modality else ""

        tk.Label(summary_row,
                 text=f"LVEF: {latest.lvef_percent:.0f}%",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG_ALT, fg=status_color,
                 anchor='w').pack(side='left')
        tk.Label(summary_row,
                 text=f"  ({modality}, {date_str})",
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                 anchor='w').pack(side='left')

        # Status badge (if not ok)
        if status_info['status'] != 'ok':
            badge_text = status_info['status'].upper()
            tk.Label(summary_row, text=f"  [{badge_text}]",
                     font=('Arial', FONT_LABEL, 'bold'), bg=BG_ALT,
                     fg=status_color).pack(side='left')

        # ── Baseline + delta row ───────────────────────────────────────────────
        if baseline and baseline.id != latest.id:
            delta = latest.lvef_percent - baseline.lvef_percent
            delta_sign = '+' if delta >= 0 else ''
            delta_color = '#4CAF50' if delta >= 0 else status_color

            delta_row = tk.Frame(self._content, bg=BG_ALT)
            delta_row.pack(anchor='w', fill='x', pady=(0, 10))

            tk.Label(delta_row,
                     text=f"Baseline: {baseline.lvef_percent:.0f}%",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                     anchor='w').pack(side='left')
            tk.Label(delta_row,
                     text=f"   Δ {delta_sign}{delta:.0f}pp",
                     font=('Arial', FONT_HINT, 'bold'), bg=BG_ALT,
                     fg=delta_color, anchor='w').pack(side='left')

            if status_info['reason']:
                tk.Label(delta_row,
                         text=f"   · {status_info['reason']}",
                         font=('Arial', FONT_HINT), bg=BG_ALT, fg=status_color,
                         anchor='w').pack(side='left')

        # ── History rows ──────────────────────────────────────────────────────
        tk.Frame(self._content, bg=SEPARATOR, height=1).pack(fill='x', pady=(4, 8))

        for a in assessments:
            self._show_assessment_row(a, baseline, lvef_cfg)

    def _show_assessment_row(self, assessment, baseline, lvef_cfg):
        row = tk.Frame(self._content, bg=BG_ALT)
        row.pack(anchor='w', fill='x', pady=2)

        d = assessment.assessment_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        date_str = d.strftime("%b %d, %Y")

        baseline_pct = baseline.lvef_percent if baseline else None
        s = lvef_status(assessment.lvef_percent, baseline_pct, lvef_cfg)
        color = _STATUS_COLOR.get(s['status'], FG)

        context_str = f" · {assessment.context}" if assessment.context else ""
        modality_str = assessment.modality.upper() if assessment.modality else ""

        tk.Label(row,
                 text=f"{date_str}  {modality_str}{context_str}",
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED,
                 anchor='w', width=30).pack(side='left')
        tk.Label(row,
                 text=f"{assessment.lvef_percent:.0f}%",
                 font=('Arial', FONT_LABEL, 'bold'), bg=BG_ALT, fg=color,
                 anchor='w').pack(side='left')

        # Edit / Delete
        del_btn = tk.Label(row, text='Delete',
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#F44336',
                           cursor='hand2')
        del_btn.pack(side='right')
        del_btn.bind('<Button-1>', lambda e, a=assessment: self._on_delete(a))
        del_btn.bind('<Enter>', lambda e: del_btn.config(fg='#E57373'))
        del_btn.bind('<Leave>', lambda e: del_btn.config(fg='#F44336'))

        tk.Label(row, text='  ·  ', font=('Arial', FONT_HINT),
                 bg=BG_ALT, fg=FG_MUTED).pack(side='right')

        edit_btn = tk.Label(row, text='Edit',
                            font=('Arial', FONT_HINT), bg=BG_ALT, fg='#4CAF50',
                            cursor='hand2')
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e, a=assessment: self._on_edit(a))
        edit_btn.bind('<Enter>', lambda e: edit_btn.config(fg='#81C784'))
        edit_btn.bind('<Leave>', lambda e: edit_btn.config(fg='#4CAF50'))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_edit(self, assessment):
        from views.dialogs.lvef_dialog import EditLvefDialog
        EditLvefDialog(self, self.conn, assessment, on_save=self.refresh)

    def _on_delete(self, assessment):
        if not messagebox.askyesno(
            'Delete LVEF Assessment',
            f'Delete LVEF from {assessment.assessment_date}?\n\nAn audit record will be kept.',
            parent=self,
        ):
            return
        try:
            delete_lvef(self.conn, assessment.id)
        except Exception as e:
            messagebox.showerror('Delete Failed', f'Could not delete assessment:\n{e}',
                                 parent=self)
            return
        self.refresh()

    # ── Public API ────────────────────────────────────────────────────────────

    def load_patient(self, patient_id):
        self.patient_id = patient_id
        self.refresh()
