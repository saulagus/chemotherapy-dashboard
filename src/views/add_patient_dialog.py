import tkinter as tk
from tkinter import ttk
from utils import BG, SEPARATOR, FG, FG_MUTED


class AddPatientDialog(tk.Toplevel):
    """Modal dialog for adding a new patient.

    Opens as a separate window on top of the main app.
    Blocks interaction with the main window until closed.
    """

    PROTOCOLS = ['Dose-Dense AC-T', 'Standard AC-T']

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.result = None      # Set to the new Patient after a successful save.
        self._build_ui()
        self._make_modal(parent)

    def _make_modal(self, parent):
        self.title("Add Patient")
        self.resizable(False, False)
        self.configure(bg=BG)

        # Center over the parent window.
        self.update_idletasks()
        pw = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w, h = 420, 420
        x = pw + (parent.winfo_width()  - w) // 2
        y = py + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Block the parent window until this dialog is closed.
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, padx=16, pady=10)
        header.pack(fill='x')
        tk.Label(header, text="Add Patient", font=('Arial', 13),
                 bg=BG, fg=FG).pack(side='left')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # ── Form fields ────────────────────────────────────────────────────────
        form = tk.Frame(self, bg=BG, padx=20, pady=16)
        form.pack(fill='both', expand=True)

        # Column weights: label column fixed, input column stretches.
        form.columnconfigure(1, weight=1)

        self._fields = {}
        rows = [
            ('patient_id',      'Patient ID *',         'entry',    None),
            ('name',            'Name / Initials *',    'entry',    None),
            ('start_date',      'AC-T Start Date *',    'entry',    'YYYY-MM-DD'),
            ('protocol',        'Protocol *',           'combo',    self.PROTOCOLS),
            ('age',             'Age at Diagnosis',     'entry',    None),
            ('diagnosis_date',  'Diagnosis Date',       'entry',    'YYYY-MM-DD'),
        ]

        for row_idx, (key, label, widget_type, extra) in enumerate(rows):
            # Label.
            tk.Label(form, text=label, font=('Arial', 11),
                     bg=BG, fg=FG, anchor='w').grid(
                row=row_idx, column=0, sticky='w', pady=6, padx=(0, 16))

            # Input widget.
            if widget_type == 'combo':
                var = tk.StringVar()
                widget = ttk.Combobox(form, textvariable=var,
                                      values=extra, state='readonly',
                                      font=('Arial', 11))
                widget.current(0)
                self._fields[key] = var
            else:
                var = tk.StringVar()
                widget = tk.Entry(form, textvariable=var,
                                  font=('Arial', 11),
                                  bg='#2e2e2e', fg=FG,
                                  insertbackground=FG,
                                  relief='flat', bd=4)
                if extra:   # placeholder hint
                    widget.insert(0, extra)
                    widget.config(fg=FG_MUTED)
                    widget.bind('<FocusIn>',  lambda e, w=widget, h=extra: self._clear_hint(w, h))
                    widget.bind('<FocusOut>', lambda e, w=widget, h=extra: self._restore_hint(w, h))
                self._fields[key] = var

            widget.grid(row=row_idx, column=1, sticky='ew', pady=6)

        # ── Inline error label ─────────────────────────────────────────────────
        self._error_label = tk.Label(form, text='', font=('Arial', 10),
                                     bg=BG, fg='#e05555',
                                     justify='left', wraplength=360, anchor='w')
        self._error_label.grid(row=len(rows), column=0, columnspan=2,
                               sticky='w', pady=(8, 0))

        # ── Buttons ────────────────────────────────────────────────────────────
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        btn_row = tk.Frame(self, bg=BG, padx=20, pady=12)
        btn_row.pack(fill='x')

        tk.Button(btn_row, text="Cancel",
                  command=self._on_cancel).pack(side='right', padx=(8, 0))
        tk.Button(btn_row, text="Save Patient",
                  command=self._on_save).pack(side='right')

    # ── Hint helpers ──────────────────────────────────────────────────────────

    def _clear_hint(self, widget, hint):
        if widget.get() == hint:
            widget.delete(0, 'end')
            widget.config(fg=FG)

    def _restore_hint(self, widget, hint):
        if not widget.get():
            widget.insert(0, hint)
            widget.config(fg=FG_MUTED)

    def _show_error(self, message):
        self._error_label.config(text=message)

    def _clear_error(self):
        self._error_label.config(text='')

    # ── Validation ────────────────────────────────────────────────────────────

    def _get(self, key, hint=None):
        """Return stripped field value, treating the placeholder hint as empty."""
        val = self._fields[key].get().strip()
        return '' if val == hint else val

    def validate_inputs(self):
        """Check all fields and return a list of error strings (empty = valid)."""
        from datetime import date
        errors = []

        patient_id = self._get('patient_id')
        name       = self._get('name')
        start_date = self._get('start_date', 'YYYY-MM-DD')
        protocol   = self._get('protocol')
        age        = self._get('age')
        diag_date  = self._get('diagnosis_date', 'YYYY-MM-DD')

        # Required fields.
        if not patient_id:
            errors.append("Patient ID is required.")
        elif not (3 <= len(patient_id) <= 20 and patient_id.replace('-', '').isalnum()):
            errors.append("Patient ID must be 3–20 alphanumeric characters.")

        if not name:
            errors.append("Name / Initials is required.")

        if not start_date:
            errors.append("AC-T Start Date is required.")
        else:
            try:
                sd = date.fromisoformat(start_date)
                if sd > date.today():
                    errors.append("AC-T Start Date cannot be in the future.")
            except ValueError:
                errors.append("AC-T Start Date must be YYYY-MM-DD.")

        if not protocol:
            errors.append("Protocol is required.")

        # Optional fields — validate only if provided.
        if age:
            if not age.isdigit() or not (0 < int(age) < 120):
                errors.append("Age must be a number between 1 and 119.")

        if diag_date:
            try:
                dd = date.fromisoformat(diag_date)
                if dd > date.today():
                    errors.append("Diagnosis Date cannot be in the future.")
            except ValueError:
                errors.append("Diagnosis Date must be YYYY-MM-DD.")

        return errors

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_save(self):
        from datetime import date
        from models import Patient, add_patient

        self._clear_error()
        errors = self.validate_inputs()
        if errors:
            self._show_error("\n".join(f"• {e}" for e in errors))
            return

        patient_id = self._get('patient_id')
        name       = self._get('name')
        start_date = self._get('start_date', 'YYYY-MM-DD')
        protocol   = self._get('protocol')
        age        = self._get('age')
        diag_date  = self._get('diagnosis_date', 'YYYY-MM-DD')

        try:
            new_patient = add_patient(self.app.conn, Patient(
                patient_id  = patient_id,
                name        = name,
                start_date  = date.fromisoformat(start_date),
                protocol    = protocol,
                age         = int(age) if age else None,
                diagnosis_date = date.fromisoformat(diag_date) if diag_date else None,
                total_cycles = 8,
            ))
        except Exception as e:
            if 'UNIQUE' in str(e):
                self._show_error(f"• Patient ID '{patient_id}' already exists.")
            else:
                self._show_error(f"• Save failed: {e}")
            return

        self.result = new_patient
        self.destroy()

    def _on_cancel(self):
        self.destroy()
