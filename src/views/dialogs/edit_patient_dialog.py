import tkinter as tk
from datetime import date
from tkinter import ttk

import config
from models import Patient
from services.patients import update_patient
from utils import BG, SEPARATOR, FG, FG_MUTED, FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER

# Agents available for prior anthracycline exposure entry
_PRIOR_AGENTS = ['', 'doxorubicin', 'epirubicin', 'daunorubicin', 'idarubicin', 'mitoxantrone']


class EditPatientDialog(tk.Toplevel):
    """Modal dialog for editing an existing patient.

    Mirrors AddPatientDialog layout. Adds a dose-density field and routes the
    save through services.patients.update_patient so an audit row is written.
    """

    PROTOCOLS = ['Dose-Dense AC-T', 'Standard AC-T']
    DOSE_DENSITY_LABELS = {
        'standard_q3w': 'Standard (q3w)',
        'dose_dense_q2w': 'Dose-Dense (q2w)',
    }

    def __init__(self, parent, app, patient: Patient):
        super().__init__(parent)
        self.app = app
        self.patient = patient
        self.result = None
        self._dose_density_options = config.get().cycles.dose_density_options
        self._build_ui()
        self._populate_from_patient()
        self._make_modal(parent)

    def _make_modal(self, parent):
        self.title("Edit Patient")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.update_idletasks()
        pw = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w, h = 420, 580
        x = pw + (parent.winfo_width() - w) // 2
        y = py + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _build_ui(self):
        header = tk.Frame(self, bg=BG, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text="Edit Patient", font=('Arial', FONT_HEADER, 'bold'),
                 bg=BG, fg=FG).pack(side='left')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        form = tk.Frame(self, bg=BG, padx=20, pady=16)
        form.pack(fill='both', expand=True)
        form.columnconfigure(1, weight=1)

        self._fields = {}
        dose_density_values = [self.DOSE_DENSITY_LABELS.get(o, o)
                               for o in self._dose_density_options]
        rows = [
            ('patient_id',      'Patient ID *',         'entry',    None),
            ('name',            'Name / Initials *',    'entry',    None),
            ('start_date',      'AC-T Start Date *',    'entry',    'YYYY-MM-DD'),
            ('protocol',        'Protocol *',           'combo',    self.PROTOCOLS),
            ('dose_density',    'Dose Density',         'combo',    dose_density_values),
            ('age',             'Age at Diagnosis',     'entry',    None),
            ('diagnosis_date',  'Diagnosis Date',       'entry',    'YYYY-MM-DD'),
        ]
        prior_rows = [
            ('prior_anthracycline_dose', 'Prior Anthracycline\nDose (mg/m²)', 'entry', None),
            ('prior_anthracycline_agent', 'Prior Agent',        'combo', _PRIOR_AGENTS),
        ]

        for row_idx, (key, label, widget_type, extra) in enumerate(rows):
            tk.Label(form, text=label, font=('Arial', FONT_BODY),
                     bg=BG, fg=FG, anchor='w').grid(
                row=row_idx, column=0, sticky='w', pady=6, padx=(0, 16))

            if widget_type == 'combo':
                var = tk.StringVar()
                widget = ttk.Combobox(form, textvariable=var,
                                      values=extra, state='readonly',
                                      font=('Arial', FONT_BODY))
                self._fields[key] = var
            else:
                var = tk.StringVar()
                widget = tk.Entry(form, textvariable=var,
                                  font=('Arial', FONT_BODY),
                                  bg='#2e2e2e', fg=FG,
                                  insertbackground=FG,
                                  relief='flat', bd=4)
                self._fields[key] = var
                if extra:
                    widget.bind('<FocusIn>',  lambda e, w=widget, h=extra: self._clear_hint(w, h))
                    widget.bind('<FocusOut>', lambda e, w=widget, h=extra: self._restore_hint(w, h))

            widget.grid(row=row_idx, column=1, sticky='ew', pady=6)

        # ── Prior Anthracycline History ──────────────────────────────────────
        sep_row = len(rows)
        tk.Frame(form, bg=SEPARATOR, height=1).grid(
            row=sep_row, column=0, columnspan=2, sticky='ew', pady=(8, 6))
        tk.Label(form, text="Prior Anthracycline History (optional)",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED, anchor='w',
                 ).grid(row=sep_row + 1, column=0, columnspan=2, sticky='w', pady=(0, 4))

        for pr_idx, (key, label, widget_type, extra) in enumerate(prior_rows):
            row_idx = sep_row + 2 + pr_idx
            tk.Label(form, text=label, font=('Arial', FONT_BODY),
                     bg=BG, fg=FG, anchor='w').grid(
                row=row_idx, column=0, sticky='w', pady=6, padx=(0, 16))
            if widget_type == 'combo':
                var = tk.StringVar()
                widget = ttk.Combobox(form, textvariable=var,
                                      values=extra, state='readonly',
                                      font=('Arial', FONT_BODY))
            else:
                var = tk.StringVar()
                widget = tk.Entry(form, textvariable=var,
                                  font=('Arial', FONT_BODY),
                                  bg='#2e2e2e', fg=FG,
                                  insertbackground=FG,
                                  relief='flat', bd=4)
            self._fields[key] = var
            widget.grid(row=row_idx, column=1, sticky='ew', pady=6)

        total_rows = sep_row + 2 + len(prior_rows)
        self._error_label = tk.Label(form, text='', font=('Arial', FONT_HINT),
                                     bg=BG, fg='#e05555',
                                     justify='left', wraplength=360, anchor='w')
        self._error_label.grid(row=total_rows, column=0, columnspan=2,
                               sticky='w', pady=(8, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')
        btn_row = tk.Frame(self, bg=BG, padx=20, pady=12)
        btn_row.pack(fill='x')
        tk.Button(btn_row, text="Cancel",
                  command=self._on_cancel).pack(side='right', padx=(8, 0))
        tk.Button(btn_row, text="Save Changes",
                  command=self._on_save).pack(side='right')

    def _populate_from_patient(self):
        p = self.patient
        self._fields['patient_id'].set(p.patient_id or '')
        self._fields['name'].set(p.name or '')
        self._fields['start_date'].set(p.start_date.isoformat() if p.start_date else '')
        self._fields['protocol'].set(p.protocol or self.PROTOCOLS[0])
        self._fields['dose_density'].set(
            self.DOSE_DENSITY_LABELS.get(p.dose_density, '')
        )
        self._fields['age'].set(str(p.age) if p.age is not None else '')
        self._fields['diagnosis_date'].set(
            p.diagnosis_date.isoformat() if p.diagnosis_date else ''
        )
        prior_dose = p.prior_anthracycline_dose_mg_per_m2
        self._fields['prior_anthracycline_dose'].set(
            str(prior_dose) if prior_dose else ''
        )
        self._fields['prior_anthracycline_agent'].set(
            p.prior_anthracycline_agent or ''
        )

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

    def _get(self, key, hint=None):
        val = self._fields[key].get().strip()
        return '' if val == hint else val

    def _resolve_dose_density(self) -> str:
        label = self._fields['dose_density'].get().strip()
        if not label:
            return None
        for option, pretty in self.DOSE_DENSITY_LABELS.items():
            if pretty == label:
                return option
        return None

    def validate_inputs(self):
        errors = []
        patient_id = self._get('patient_id')
        name = self._get('name')
        start_date = self._get('start_date', 'YYYY-MM-DD')
        protocol = self._get('protocol')
        age = self._get('age')
        diag_date = self._get('diagnosis_date', 'YYYY-MM-DD')

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

        if age and (not age.isdigit() or not (0 < int(age) < 120)):
            errors.append("Age must be a number between 1 and 119.")

        prior_dose_raw = self._get('prior_anthracycline_dose')
        if prior_dose_raw:
            try:
                pd = float(prior_dose_raw)
                if pd < 0:
                    errors.append("Prior anthracycline dose cannot be negative.")
            except ValueError:
                errors.append("Prior anthracycline dose must be a number (mg/m²).")

        if diag_date:
            try:
                dd = date.fromisoformat(diag_date)
                if dd > date.today():
                    errors.append("Diagnosis Date cannot be in the future.")
            except ValueError:
                errors.append("Diagnosis Date must be YYYY-MM-DD.")

        return errors

    def _on_save(self):
        self._clear_error()
        errors = self.validate_inputs()
        if errors:
            self._show_error("\n".join(f"• {e}" for e in errors))
            return

        patient_id = self._get('patient_id')
        name = self._get('name')
        start_date = self._get('start_date', 'YYYY-MM-DD')
        protocol = self._get('protocol')
        age = self._get('age')
        diag_date = self._get('diagnosis_date', 'YYYY-MM-DD')

        prior_dose_raw = self._get('prior_anthracycline_dose')
        prior_agent    = self._get('prior_anthracycline_agent') or None

        updated = Patient(
            id=self.patient.id,
            patient_id=patient_id,
            name=name,
            start_date=date.fromisoformat(start_date),
            protocol=protocol,
            age=int(age) if age else None,
            diagnosis_date=date.fromisoformat(diag_date) if diag_date else None,
            total_cycles=self.patient.total_cycles or 8,
            dose_density=self._resolve_dose_density(),
            prior_anthracycline_dose_mg_per_m2=float(prior_dose_raw) if prior_dose_raw else 0.0,
            prior_anthracycline_agent=prior_agent,
        )

        try:
            update_patient(self.app.conn, updated)
        except Exception as e:
            if 'UNIQUE' in str(e):
                self._show_error(f"• Patient ID '{patient_id}' already exists.")
            else:
                self._show_error(f"• Save failed: {e}")
            return

        self.result = updated
        self.destroy()

    def _on_cancel(self):
        self.destroy()
