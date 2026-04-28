"""Toxicity panel — combined Sprint 7 toxicity tracking surface (US-027–030).

Day 23: neuropathy section only (stub rows for reactions, G-CSF, symptoms).
Day 29: all four sections fully wired.

Public API
----------
load_patient(patient_db_id)  — switch patient context and refresh
refresh()                    — reload from DB and redraw
"""

import tkinter as tk
from tkinter import messagebox

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)
from clinical.neuropathy import effective_grade, recommended_action
from services.neuropathy import (
    NeuropathyAssessment,
    delete_neuropathy,
    latest_neuropathy,
    list_neuropathy,
)
from config import get as get_config

_NEUROPATHY_COLOR = {
    0: '#4CAF50',  # G0 — green
    1: '#4CAF50',  # G1 — green
    2: '#FFC107',  # G2 — yellow
    3: '#FF9800',  # G3 — orange
    4: '#F44336',  # G4 — red
}


class ToxicityPanel(tk.Frame):
    """Combined toxicity panel shown below CardiotoxicityPanel in the dashboard.

    Public API
    ----------
    load_patient(patient_db_id)  — switch to a patient by integer DB id
    refresh()                    — reload from DB and redraw
    """

    def __init__(self, parent, conn, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn            = conn
        self.patient_db_id   = None      # integer DB id
        self.patient_str_id  = None      # string 'PT-001'
        self._content        = None

        self._build_header()
        self.refresh()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        header_row = tk.Frame(self, bg=BG_ALT, padx=16)
        header_row.pack(fill='x', pady=(14, 0))
        tk.Label(header_row, text="Toxicity Tracking",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(side='left')

    # ── Public API ────────────────────────────────────────────────────────────

    def load_patient(self, patient_db_id: int):
        from models import get_patient_by_db_id
        self.patient_db_id  = patient_db_id
        patient = get_patient_by_db_id(self.conn, patient_db_id)
        self.patient_str_id = patient.patient_id if patient else None
        self.refresh()

    def refresh(self):
        if self._content:
            self._content.destroy()
        self._content = tk.Frame(self, bg=BG_ALT)
        self._content.pack(fill='both', expand=True, padx=16, pady=(8, 16))

        if not self.patient_str_id:
            tk.Label(self._content, text="No patient selected.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                     ).pack(anchor='w', pady=8)
            return

        self._render_neuropathy()
        self._render_stub("Infusion Reactions", "No reactions logged.")
        self._render_stub("G-CSF Administration", "No G-CSF doses logged.")
        self._render_stub("Symptoms", "No symptoms logged.")

    # ── Neuropathy section ────────────────────────────────────────────────────

    def _render_neuropathy(self):
        section = self._section_frame("Neuropathy (CTCAE v5)")
        latest  = latest_neuropathy(self.conn, self.patient_str_id)

        if latest is None:
            row = tk.Frame(section, bg=BG_ALT)
            row.pack(fill='x', pady=(4, 0))
            tk.Label(row, text="No assessments recorded.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(side='left')
            add = tk.Label(row, text="+ Add",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            add.pack(side='left', padx=(8, 0))
            add.bind('<Button-1>', lambda e: self._open_add_neuropathy())
        else:
            self._render_neuropathy_latest(section, latest)

        self._section_action_row(section, latest,
                                 on_add=self._open_add_neuropathy,
                                 on_history=self._open_neuropathy_history)

    def _render_neuropathy_latest(self, section, assessment: NeuropathyAssessment):
        cfg   = get_config().toxicity.model_dump()
        grade = effective_grade(assessment.sensory_grade, assessment.motor_grade, cfg)
        try:
            action = recommended_action(grade, cfg)
            advisory = action.advisory_text
        except Exception:
            advisory = ""

        color = _NEUROPATHY_COLOR.get(grade, FG)
        d     = assessment.assessment_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)

        summary_row = tk.Frame(section, bg=BG_ALT)
        summary_row.pack(fill='x', pady=(4, 0))

        tk.Label(summary_row,
                 text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'),
                 bg=BG_ALT, fg=color).pack(side='left')
        tk.Label(summary_row,
                 text=f"  Sensory G{assessment.sensory_grade} / Motor G{assessment.motor_grade}"
                      f"  ·  {date_str}",
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG).pack(side='left')

        if advisory:
            tk.Label(section, text=advisory,
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                     anchor='w', wraplength=400).pack(fill='x', pady=(2, 0))

    def _open_add_neuropathy(self):
        if not self.patient_db_id:
            return
        from views.dialogs.neuropathy_dialog import NeuropathyDialog
        NeuropathyDialog(self, self.conn, self.patient_db_id, on_save=self.refresh)

    def _open_neuropathy_history(self):
        if not self.patient_str_id:
            return
        _NeuropathyHistoryWindow(self, self.conn, self.patient_db_id,
                                 self.patient_str_id, on_change=self.refresh)

    # ── Stub sections (filled Days 24–28) ─────────────────────────────────────

    def _render_stub(self, title: str, empty_text: str):
        section = self._section_frame(title)
        tk.Label(section, text=empty_text,
                 font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _section_frame(self, title: str) -> tk.Frame:
        tk.Frame(self._content, bg=SEPARATOR, height=1).pack(fill='x', pady=(8, 0))
        header = tk.Frame(self._content, bg=BG_ALT)
        header.pack(fill='x', pady=(6, 0))
        tk.Label(header, text=title,
                 font=('Arial', FONT_LABEL, 'bold'), bg=BG_ALT, fg=FG).pack(side='left')
        body = tk.Frame(self._content, bg=BG_ALT)
        body.pack(fill='x')
        return body

    def _section_action_row(self, section, current_record, on_add, on_history):
        row = tk.Frame(section, bg=BG_ALT)
        row.pack(fill='x', pady=(6, 0))
        if current_record is not None:
            hist = tk.Label(row, text="View history",
                            font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            hist.pack(side='left')
            hist.bind('<Button-1>', lambda e: on_history())
            add = tk.Label(row, text="+ Add new",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2',
                           padx=12)
            add.pack(side='left')
            add.bind('<Button-1>', lambda e: on_add())


# ── Neuropathy history window ─────────────────────────────────────────────────

class _NeuropathyHistoryWindow(tk.Toplevel):
    """Lightweight history list for neuropathy assessments."""

    def __init__(self, parent, conn, patient_db_id: int, patient_str_id: str, on_change=None):
        super().__init__(parent)
        self.conn           = conn
        self.patient_db_id  = patient_db_id
        self.patient_str_id = patient_str_id
        self.on_change      = on_change

        self.title("Neuropathy History")
        self.configure(bg=BG)
        self.geometry('560x400')
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Neuropathy Assessments",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        scroll_frame = tk.Frame(self, bg=BG)
        scroll_frame.pack(fill='both', expand=True, padx=16, pady=12)

        rows = list_neuropathy(self.conn, self.patient_str_id)
        if not rows:
            tk.Label(scroll_frame, text="No assessments on record.",
                     font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED).pack(anchor='w')
            return

        cfg = get_config().toxicity.model_dump()
        for a in rows:
            self._render_row(scroll_frame, a, cfg)

    def _render_row(self, parent, a: NeuropathyAssessment, cfg: dict):
        grade = effective_grade(a.sensory_grade, a.motor_grade, cfg)
        color = _NEUROPATHY_COLOR.get(grade, FG)
        d     = a.assessment_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)

        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=3)

        tk.Label(row, text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG, fg=color).pack(side='left')
        tk.Label(row,
                 text=f"  S{a.sensory_grade}/M{a.motor_grade}  {date_str}",
                 font=('Arial', FONT_BODY), bg=BG, fg=FG).pack(side='left')

        del_btn = tk.Label(row, text="Delete",
                           font=('Arial', FONT_HINT), bg=BG, fg='#e05555', cursor='hand2',
                           padx=8)
        del_btn.pack(side='right')
        del_btn.bind('<Button-1>', lambda e, aid=a.id: self._on_delete(aid))

        edit_btn = tk.Label(row, text="Edit",
                            font=('Arial', FONT_HINT), bg=BG, fg='#90CAF9', cursor='hand2')
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e, rec=a: self._on_edit(rec))

    def _on_edit(self, assessment: NeuropathyAssessment):
        from views.dialogs.neuropathy_dialog import EditNeuropathyDialog
        EditNeuropathyDialog(self, self.conn, assessment,
                             self.patient_db_id, on_save=self._refresh)

    def _on_delete(self, assessment_id: int):
        if not messagebox.askyesno("Delete Assessment",
                                   "Delete this neuropathy assessment?", parent=self):
            return
        delete_neuropathy(self.conn, assessment_id)
        if self.on_change:
            self.on_change()
        self._refresh()

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()
