import tkinter as tk
from datetime import date
from tkinter import messagebox

import config
from clinical.cardiotoxicity import lvef_status
from services.lvef import delete_lvef, get_baseline_lvef, list_lvef
from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)

_STATUS_COLOR = {
    'ok':     '#4CAF50',
    'review': '#FFC107',
    'hold':   '#F44336',
}


class CardiotoxicityPanel(tk.Frame):
    """Cardiotoxicity summary panel shown in the patient dashboard.

    Day 16: shows LVEF history (latest assessment + Δ from baseline).
    Day 17+: badge and cumulative dose meter will be added here.

    Public API
    ----------
    load_patient(patient_id) — switch patient context and refresh
    refresh()                — reload from DB and redraw
    """

    def __init__(self, parent, conn, on_add_lvef=None, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn         = conn
        self.patient_id   = None
        self.on_add_lvef  = on_add_lvef
        self._content     = None

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
        """Reload LVEF records from DB and redraw."""
        self._clear_content()

        if self.patient_id is None:
            self._show_empty("No patient selected.")
            return

        assessments = list_lvef(self.conn, self.patient_id)

        if not assessments:
            self._show_empty("No LVEF assessments recorded.")
            return

        baseline = get_baseline_lvef(self.conn, self.patient_id)
        lvef_cfg = config.get().cardiotoxicity.lvef.model_dump()

        self._show_lvef(assessments, baseline, lvef_cfg)

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
