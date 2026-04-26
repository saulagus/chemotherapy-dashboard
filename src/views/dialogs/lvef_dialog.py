import logging
import tkinter as tk
from tkinter import messagebox
from datetime import date

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)
from models import LvefAssessment, get_patient_by_db_id
from services.lvef import create_lvef, update_lvef

log = logging.getLogger(__name__)

_MODALITIES = ['echo', 'muga']
_CONTEXTS   = ['baseline', 'end_of_ac', 'ad_hoc']


class LvefDialog(tk.Toplevel):
    """Modal dialog for recording a new LVEF assessment.

    Parameters
    ----------
    parent     : tk.Widget
    conn       : sqlite3.Connection
    patient_id : int  — DB integer id of the patient
    on_save    : callable | None  — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id, on_save=None):
        super().__init__(parent)
        self.conn       = conn
        self.patient_id = patient_id
        self.on_save    = on_save

        patient = get_patient_by_db_id(conn, patient_id)
        self._patient_name = patient.name if patient else ""

        self.title("Add LVEF Assessment")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()
        self.geometry('420x520')
        self.protocol('WM_DELETE_WINDOW', self._confirm_cancel)
        self.bind('<Return>', lambda e: self._on_save())
        self.bind('<Escape>', lambda e: self._confirm_cancel())
        self.date_entry.focus_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text="Add LVEF Assessment",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text=f"Patient: {self._patient_name}",
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

        save = tk.Label(btn_row, text="Save", font=('Arial', FONT_BODY, 'bold'),
                        bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save.pack(side='right', padx=(0, 12))
        save.bind('<Button-1>', lambda e: self._on_save())

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=0, minsize=160)
        body.columnconfigure(1, weight=1)

        row = 0

        # ── Assessment date ───────────────────────────────────────────────────
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

        # ── LVEF % ────────────────────────────────────────────────────────────
        self._grid_label(body, "LVEF % *", row)
        self.lvef_var = tk.StringVar()
        self.lvef_entry = tk.Entry(body, textvariable=self.lvef_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.lvef_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1
        tk.Label(body, text="Normal: ≥ 55%  ·  Range: 10–85",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # ── Modality ─────────────────────────────────────────────────────────
        self._grid_label(body, "Modality *", row)
        self.modality_var = tk.StringVar(value='echo')
        modality_frame = tk.Frame(body, bg=BG)
        modality_frame.grid(row=row, column=1, sticky='w', pady=(0, 12))
        for m in _MODALITIES:
            tk.Radiobutton(modality_frame, text=m.upper(), variable=self.modality_var,
                           value=m, font=('Arial', FONT_BODY),
                           bg=BG, fg=FG, selectcolor=BG_ALT,
                           activebackground=BG, activeforeground=FG).pack(side='left', padx=(0, 16))
        row += 1

        # ── Context ───────────────────────────────────────────────────────────
        self._grid_label(body, "Context (optional)", row)
        self.context_var = tk.StringVar(value='')
        context_frame = tk.Frame(body, bg=BG)
        context_frame.grid(row=row, column=1, sticky='w', pady=(0, 12))
        labels = {'baseline': 'Baseline', 'end_of_ac': 'End of AC', 'ad_hoc': 'Ad hoc', '': 'None'}
        for val in ['', 'baseline', 'end_of_ac', 'ad_hoc']:
            tk.Radiobutton(context_frame, text=labels[val], variable=self.context_var,
                           value=val, font=('Arial', FONT_HINT),
                           bg=BG, fg=FG, selectcolor=BG_ALT,
                           activebackground=BG, activeforeground=FG).pack(side='left', padx=(0, 10))
        row += 1

        # ── Notes ─────────────────────────────────────────────────────────────
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
                                    bg=BG, fg='#e05555', anchor='w', wraplength=260)
        self.error_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 0))

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

    # ── Close behavior ────────────────────────────────────────────────────────

    def _snapshot(self) -> dict:
        return {
            'date':     self.date_var.get(),
            'lvef':     self.lvef_var.get(),
            'modality': self.modality_var.get(),
            'context':  self.context_var.get(),
            'notes':    self.notes_var.get(),
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

        if not data['lvef']:
            errors.append("LVEF % is required.")
        else:
            try:
                val = float(data['lvef'])
                if val < 10 or val > 85:
                    errors.append("LVEF % must be between 10 and 85.")
            except ValueError:
                errors.append("LVEF % must be a number (e.g. 62).")

        return errors

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            first = errors[0].lower()
            if 'date' in first:
                self.date_entry.focus_set()
            elif 'lvef' in first:
                self.lvef_entry.focus_set()
            return

        self.error_label.config(text="")
        data = self.get_form_data()

        try:
            create_lvef(self.conn, LvefAssessment(
                patient_id      = self.patient_id,
                assessment_date = date.fromisoformat(data['date']),
                lvef_percent    = float(data['lvef']),
                modality        = data['modality'],
                context         = data['context'] or None,
                notes           = data['notes'] or None,
            ))
        except Exception as e:
            log.exception('Failed to save LVEF for patient_id=%d', self.patient_id)
            messagebox.showerror('Save Failed', f'Could not save LVEF data:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()


class EditLvefDialog(LvefDialog):
    """Modal dialog for editing an existing LVEF assessment.

    Reuses LvefDialog layout and validation. Pre-populates fields from
    the given LvefAssessment and routes save through update_lvef.
    """

    def __init__(self, parent, conn, assessment: LvefAssessment, on_save=None):
        self._editing = assessment
        super().__init__(parent, conn, assessment.patient_id, on_save=on_save)
        self.title("Edit LVEF Assessment")
        self._populate()

    def _populate(self):
        a = self._editing
        d = a.assessment_date
        self.date_var.set(d.isoformat() if hasattr(d, 'isoformat') else str(d))
        self.lvef_var.set(str(a.lvef_percent))
        self.modality_var.set(a.modality or 'echo')
        self.context_var.set(a.context or '')
        self.notes_var.set(a.notes or '')
        self._initial = self._snapshot()

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            return

        self.error_label.config(text="")
        data = self.get_form_data()

        try:
            updated = LvefAssessment(
                id              = self._editing.id,
                patient_id      = self._editing.patient_id,
                assessment_date = date.fromisoformat(data['date']),
                lvef_percent    = float(data['lvef']),
                modality        = data['modality'],
                context         = data['context'] or None,
                notes           = data['notes'] or None,
            )
            update_lvef(self.conn, updated)
        except Exception as e:
            log.exception('Failed to update LVEF id=%s', self._editing.id)
            messagebox.showerror('Save Failed', f'Could not save LVEF data:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
