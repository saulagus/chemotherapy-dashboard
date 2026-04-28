"""Neuropathy assessment dialog (US-027).

NeuropathyDialog   — add a new assessment
EditNeuropathyDialog — edit an existing one
"""

import logging
import tkinter as tk
from tkinter import messagebox
from datetime import date

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)
from models import get_patient_by_db_id
from clinical.neuropathy import effective_grade, recommended_action
from services.neuropathy import NeuropathyAssessment, create_neuropathy, update_neuropathy
from config import get as get_config

log = logging.getLogger(__name__)

# CTCAE v5 descriptors shown next to each grade option
_SENSORY_HINTS = {
    0: "G0 — No symptoms",
    1: "G1 — Asymptomatic; loss of deep tendon reflexes or paresthesia",
    2: "G2 — Moderate symptoms; limiting instrumental ADL",
    3: "G3 — Severe symptoms; limiting self-care ADL",
    4: "G4 — Life-threatening; urgent intervention indicated",
}
_MOTOR_HINTS = {
    0: "G0 — No symptoms",
    1: "G1 — Asymptomatic; clinical or diagnostic observations only",
    2: "G2 — Moderate; limiting instrumental ADL",
    3: "G3 — Severe; limiting self-care ADL; assistive device indicated",
    4: "G4 — Life-threatening; urgent intervention indicated",
}
_GRADES = [0, 1, 2, 3, 4]


class NeuropathyDialog(tk.Toplevel):
    """Modal dialog for recording a new neuropathy assessment.

    Parameters
    ----------
    parent     : tk.Widget
    conn       : sqlite3.Connection
    patient_id : int  — DB integer id of the patient
    on_save    : callable | None  — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id: int, on_save=None):
        super().__init__(parent)
        self.conn       = conn
        self.patient_db_id = patient_id
        self.on_save    = on_save

        patient = get_patient_by_db_id(conn, patient_id)
        self._patient_str_id = patient.patient_id if patient else ''
        self._patient_name   = patient.name if patient else ''

        self.title("Add Neuropathy Assessment")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()
        self.geometry('480x580')
        self.protocol('WM_DELETE_WINDOW', self._confirm_cancel)
        self.bind('<Escape>', lambda e: self._confirm_cancel())
        self.date_entry.focus_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text="Add Neuropathy Assessment",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text=f"Patient: {self._patient_name}  ·  CTCAE v5.0",
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons pinned to bottom before body
        tk.Frame(self, bg=SEPARATOR, height=1).pack(side='bottom', fill='x')
        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(side='bottom', fill='x')

        cancel = tk.Label(btn_row, text="Cancel", font=('Arial', FONT_BODY),
                          bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        cancel.pack(side='right')
        cancel.bind('<Button-1>', lambda e: self._confirm_cancel())

        save_btn = tk.Label(btn_row, text="Save", font=('Arial', FONT_BODY, 'bold'),
                            bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save_btn.pack(side='right', padx=(0, 12))
        save_btn.bind('<Button-1>', lambda e: self._on_save())

        # Body
        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=0, minsize=160)
        body.columnconfigure(1, weight=1)

        row = 0

        # Assessment date
        self._grid_label(body, "Assessment Date *", row)
        self.date_var = tk.StringVar(value=str(date.today()))
        self.date_entry = tk.Entry(body, textvariable=self.date_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.date_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1
        tk.Label(body, text="YYYY-MM-DD",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Sensory grade
        self._grid_label(body, "Sensory Grade *", row)
        self.sensory_var = tk.IntVar(value=0)
        s_frame = tk.Frame(body, bg=BG)
        s_frame.grid(row=row, column=1, sticky='w', pady=(0, 4))
        for g in _GRADES:
            tk.Radiobutton(s_frame, text=str(g), variable=self.sensory_var, value=g,
                           font=('Arial', FONT_BODY), bg=BG, fg=FG,
                           selectcolor=BG_ALT, activebackground=BG,
                           command=self._update_advisory).pack(side='left', padx=(0, 10))
        row += 1
        self.sensory_hint = tk.Label(body, text=_SENSORY_HINTS[0],
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED, anchor='w', wraplength=280)
        self.sensory_hint.grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Motor grade
        self._grid_label(body, "Motor Grade *", row)
        self.motor_var = tk.IntVar(value=0)
        m_frame = tk.Frame(body, bg=BG)
        m_frame.grid(row=row, column=1, sticky='w', pady=(0, 4))
        for g in _GRADES:
            tk.Radiobutton(m_frame, text=str(g), variable=self.motor_var, value=g,
                           font=('Arial', FONT_BODY), bg=BG, fg=FG,
                           selectcolor=BG_ALT, activebackground=BG,
                           command=self._update_advisory).pack(side='left', padx=(0, 10))
        row += 1
        self.motor_hint = tk.Label(body, text=_MOTOR_HINTS[0],
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED, anchor='w', wraplength=280)
        self.motor_hint.grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Advisory recommendation (live)
        tk.Frame(body, bg=SEPARATOR, height=1).grid(row=row, column=0, columnspan=2, sticky='ew', pady=(0, 8))
        row += 1
        self.advisory_label = tk.Label(body, text="",
                 font=('Arial', FONT_HINT), bg=BG, fg='#90CAF9', anchor='w', wraplength=280)
        self.advisory_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(0, 12))
        row += 1

        # Notes
        self._grid_label(body, "Notes (optional)", row)
        self.notes_var = tk.StringVar()
        self.notes_entry = tk.Entry(body, textvariable=self.notes_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.notes_entry.grid(row=row, column=1, sticky='ew', pady=(0, 12))
        row += 1

        # Error label
        self.error_label = tk.Label(body, text="", font=('Arial', FONT_HINT),
                                    bg=BG, fg='#e05555', anchor='w', wraplength=280)
        self.error_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 0))

        self._update_advisory()
        self._initial = self._snapshot()

    def _grid_label(self, parent, text, row):
        tk.Label(parent, text=text, font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG_MUTED, anchor='w',
                 ).grid(row=row, column=0, sticky='nw', padx=(0, 16), pady=(0, 4))

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.winfo_screenwidth()  // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"+{x}+{y}")

    # ── Advisory update ───────────────────────────────────────────────────────

    def _update_advisory(self):
        s = self.sensory_var.get()
        m = self.motor_var.get()
        self.sensory_hint.config(text=_SENSORY_HINTS.get(s, ''))
        self.motor_hint.config(text=_MOTOR_HINTS.get(m, ''))
        try:
            cfg = get_config().toxicity.model_dump()
            grade = effective_grade(s, m, cfg)
            action = recommended_action(grade, cfg)
            self.advisory_label.config(
                text=f"Effective grade: G{grade} — {action.advisory_text}"
            )
        except Exception:
            self.advisory_label.config(text="")

    # ── Close behavior ────────────────────────────────────────────────────────

    def _snapshot(self) -> dict:
        return {
            'date':    self.date_var.get(),
            'sensory': self.sensory_var.get(),
            'motor':   self.motor_var.get(),
            'notes':   self.notes_var.get(),
        }

    def _has_changes(self) -> bool:
        return self._snapshot() != self._initial

    def _confirm_cancel(self):
        if self._has_changes():
            if not messagebox.askokcancel(
                'Discard changes?',
                'You have unsaved changes. Close without saving?',
                parent=self,
            ):
                return
        self.destroy()

    # ── Validation & Save ─────────────────────────────────────────────────────

    def get_form_data(self) -> dict:
        return self._snapshot()

    def validate(self) -> list:
        errors = []
        data = self.get_form_data()

        if not data['date']:
            errors.append("Assessment date is required.")
        else:
            try:
                d = date.fromisoformat(data['date'])
                if d > date.today():
                    errors.append("Assessment date cannot be in the future.")
                elif d.year < 2000:
                    errors.append("Assessment date year must be 2000 or later.")
            except ValueError:
                errors.append("Invalid date — use YYYY-MM-DD format.")

        return errors

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            if 'date' in errors[0].lower():
                self.date_entry.focus_set()
            return

        self.error_label.config(text="")
        data = self.get_form_data()

        try:
            create_neuropathy(self.conn, NeuropathyAssessment(
                patient_id      = self._patient_str_id,
                assessment_date = data['date'],
                sensory_grade   = data['sensory'],
                motor_grade     = data['motor'],
                notes           = data['notes'] or None,
            ))
        except Exception as e:
            log.exception('Failed to save neuropathy for patient %s', self._patient_str_id)
            messagebox.showerror('Save Failed', f'Could not save assessment:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()


class EditNeuropathyDialog(NeuropathyDialog):
    """Edit an existing NeuropathyAssessment. Pre-populates from the given record."""

    def __init__(self, parent, conn, assessment: NeuropathyAssessment,
                 patient_db_id: int, on_save=None):
        self._editing = assessment
        super().__init__(parent, conn, patient_db_id, on_save=on_save)
        self.title("Edit Neuropathy Assessment")
        self._populate()

    def _populate(self):
        a = self._editing
        d = a.assessment_date
        self.date_var.set(d.isoformat() if hasattr(d, 'isoformat') else str(d))
        self.sensory_var.set(a.sensory_grade)
        self.motor_var.set(a.motor_grade)
        self.notes_var.set(a.notes or '')
        self._update_advisory()
        self._initial = self._snapshot()

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            return

        self.error_label.config(text="")
        data = self.get_form_data()

        try:
            updated = NeuropathyAssessment(
                id              = self._editing.id,
                patient_id      = self._editing.patient_id,
                assessment_date = data['date'],
                sensory_grade   = data['sensory'],
                motor_grade     = data['motor'],
                cycle_id        = self._editing.cycle_id,
                ctcae_version   = self._editing.ctcae_version,
                notes           = data['notes'] or None,
            )
            update_neuropathy(self.conn, updated)
        except Exception as e:
            log.exception('Failed to update neuropathy id=%s', self._editing.id)
            messagebox.showerror('Save Failed', f'Could not update assessment:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
