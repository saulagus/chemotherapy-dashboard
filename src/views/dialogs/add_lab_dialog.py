import logging
import tkinter as tk
from tkinter import messagebox
from datetime import date
from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)
from models import Lab, add_lab, get_patient_by_db_id

log = logging.getLogger(__name__)


class AddLabDialog(tk.Toplevel):
    """Modal dialog for recording a new lab draw for a patient.

    Parameters
    ----------
    parent     : tk.Widget           — parent widget
    conn       : sqlite3.Connection
    patient_id : int                 — DB integer id of the patient
    on_save    : callable | None     — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id, on_save=None):
        super().__init__(parent)
        self.conn       = conn
        self.patient_id = patient_id
        self.on_save    = on_save

        patient = get_patient_by_db_id(conn, patient_id)
        self._patient_name = patient.name if patient else ""

        self.title("Add Lab Values")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()
        self.protocol('WM_DELETE_WINDOW', self._confirm_cancel)
        self.bind('<Return>', lambda e: self._on_save())
        self.bind('<Escape>', lambda e: self._confirm_cancel())
        self.date_entry.focus_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text="Add Lab Values",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text=f"Patient: {self._patient_name}",
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons pinned to bottom before body so expand=True doesn't push them off
        tk.Frame(self, bg=SEPARATOR, height=1).pack(side='bottom', fill='x')
        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(side='bottom', fill='x')

        cancel = tk.Label(btn_row, text="Cancel", font=('Arial', FONT_BODY),
                          bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        cancel.pack(side='right')
        cancel.bind('<Button-1>', lambda e: self._confirm_cancel())

        save = tk.Label(btn_row, text="Save Labs", font=('Arial', FONT_BODY, 'bold'),
                        bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save.pack(side='right', padx=(0, 12))
        save.bind('<Button-1>', lambda e: self._on_save())

        # Form body
        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=0, minsize=160)
        body.columnconfigure(1, weight=1)

        row = 0

        # ── Lab date ─────────────────────────────────────────────────────────
        self._grid_label(body, "Lab Date *", row)
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

        # ── ANC (required) ───────────────────────────────────────────────────
        self._grid_label(body, "ANC *", row)
        self.anc_var = tk.StringVar()
        self.anc_entry = tk.Entry(body, textvariable=self.anc_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.anc_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1

        tk.Label(body, text="K/μL  ·  Normal: 1.5 – 8.0",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # ── WBC (optional) ───────────────────────────────────────────────────
        self._grid_label(body, "WBC (optional)", row)
        self.wbc_var = tk.StringVar()
        self.wbc_entry = tk.Entry(body, textvariable=self.wbc_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.wbc_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1

        tk.Label(body, text="K/μL  ·  Normal: 4.0 – 11.0",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # ── Platelets (optional) ─────────────────────────────────────────────
        self._grid_label(body, "Platelets (optional)", row)
        self.platelets_var = tk.StringVar()
        self.platelets_entry = tk.Entry(body, textvariable=self.platelets_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.platelets_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1

        tk.Label(body, text="K/μL  ·  Normal: 150 – 400",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # ── Hemoglobin (optional) ────────────────────────────────────────────
        self._grid_label(body, "Hemoglobin (optional)", row)
        self.hgb_var = tk.StringVar()
        self.hgb_entry = tk.Entry(body, textvariable=self.hgb_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.hgb_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1

        tk.Label(body, text="g/dL  ·  Normal: 12.0 – 16.0",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Error label (hidden until validation fails)
        self.error_label = tk.Label(body, text="", font=('Arial', FONT_HINT),
                                    bg=BG, fg='#e05555', anchor='w', wraplength=260)
        self.error_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 0))

        # Snapshot for unsaved-changes detection
        self._initial = {
            'date':      self.date_var.get(),
            'anc':       '',
            'wbc':       '',
            'platelets': '',
            'hgb':       '',
        }

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

    def _has_changes(self) -> bool:
        return (
            self.date_var.get().strip()      != self._initial['date']
            or self.anc_var.get().strip()    != self._initial['anc']
            or self.wbc_var.get().strip()    != self._initial['wbc']
            or self.platelets_var.get().strip() != self._initial['platelets']
            or self.hgb_var.get().strip()    != self._initial['hgb']
        )

    def _confirm_cancel(self):
        if self._has_changes():
            ok = messagebox.askokcancel(
                'Discard changes?',
                'You have unsaved changes. Close without saving?',
                parent=self,
            )
            if not ok:
                return
        self.destroy()

    # ── Validation & Save ─────────────────────────────────────────────────────

    def get_form_data(self) -> dict:
        """Return raw field values as a dict — no validation applied."""
        return {
            'lab_date':  self.date_var.get().strip(),
            'anc':       self.anc_var.get().strip(),
            'wbc':       self.wbc_var.get().strip(),
            'platelets': self.platelets_var.get().strip(),
            'hgb':       self.hgb_var.get().strip(),
        }

    @staticmethod
    def _parse_optional(value: str):
        """Return float if value is non-empty, None otherwise. Raises ValueError if unparseable."""
        if not value:
            return None
        return float(value)

    def validate(self) -> list[str]:
        """Validate all fields. Returns a list of error messages (empty = valid)."""
        errors = []
        data = self.get_form_data()

        # ── Date ──────────────────────────────────────────────────────────────
        if not data['lab_date']:
            errors.append("Lab date is required.")
        else:
            try:
                lab_date = date.fromisoformat(data['lab_date'])
                if lab_date > date.today():
                    errors.append("Lab date cannot be in the future.")
            except ValueError:
                errors.append("Invalid date — use YYYY-MM-DD format.")

        # ── ANC (required) ───────────────────────────────────────────────────
        if not data['anc']:
            errors.append("ANC is required.")
        else:
            try:
                anc_val = float(data['anc'])
                if anc_val < 0:
                    errors.append("ANC must be a positive number.")
            except ValueError:
                errors.append("ANC must be a number (e.g. 1.8).")

        # ── Optional numeric fields ───────────────────────────────────────────
        optional_fields = [
            ('wbc',       'WBC',       0, 50),
            ('platelets', 'Platelets', 0, 1000),
            ('hgb',       'Hemoglobin', 0, 20),
        ]
        for key, label, lo, hi in optional_fields:
            val = data[key]
            if val:
                try:
                    num = float(val)
                    if num < 0:
                        errors.append(f"{label} must be a positive number.")
                except ValueError:
                    errors.append(f"{label} must be a number.")

        return errors

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            # Focus the first offending field
            first = errors[0].lower()
            if 'date' in first:
                self.date_entry.focus_set()
            elif 'anc' in first:
                self.anc_entry.focus_set()
            elif 'wbc' in first:
                self.wbc_entry.focus_set()
            elif 'platelet' in first:
                self.platelets_entry.focus_set()
            elif 'hemoglobin' in first:
                self.hgb_entry.focus_set()
            return

        self.error_label.config(text="")
        data = self.get_form_data()

        try:
            add_lab(self.conn, Lab(
                patient_id = self.patient_id,
                lab_date   = date.fromisoformat(data['lab_date']),
                anc        = float(data['anc']),
                wbc        = self._parse_optional(data['wbc']),
                platelets  = self._parse_optional(data['platelets']),
                hemoglobin = self._parse_optional(data['hgb']),
            ))
        except Exception as e:
            log.exception('Failed to save lab for patient_id=%d', self.patient_id)
            messagebox.showerror('Save Failed', f'Could not save lab data:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
