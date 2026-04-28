"""G-CSF administration dialog (US-029).

GcsfDialog     — log a new administration
EditGcsfDialog — edit an existing one
"""

import logging
import tkinter as tk
from tkinter import messagebox
from datetime import date

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)
from models import get_patient_by_db_id, get_cycles_by_patient
from services.gcsf import GcsfAdmin, create_gcsf, update_gcsf
from config import get as get_config

log = logging.getLogger(__name__)

_PROPHYLAXIS_TYPES = ['primary', 'secondary', 'therapeutic']
_PROPHYLAXIS_LABELS = {
    'primary':     'Primary (every cycle)',
    'secondary':   'Secondary (risk-based)',
    'therapeutic': 'Therapeutic (ANC rescue)',
}


class GcsfDialog(tk.Toplevel):
    """Modal dialog for logging a new G-CSF administration.

    Parameters
    ----------
    parent     : tk.Widget
    conn       : sqlite3.Connection
    patient_id : int  — DB integer id of the patient
    on_save    : callable | None — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id: int, on_save=None):
        super().__init__(parent)
        self.conn          = conn
        self.patient_db_id = patient_id
        self.on_save       = on_save

        patient = get_patient_by_db_id(conn, patient_id)
        self._patient_str_id = patient.patient_id if patient else ''
        self._patient_name   = patient.name if patient else ''
        self._cycles = get_cycles_by_patient(conn, patient_id) if patient else []

        self.title("Log G-CSF Administration")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()
        self.geometry('460x540')
        self.protocol('WM_DELETE_WINDOW', self._confirm_cancel)
        self.bind('<Escape>', lambda e: self._confirm_cancel())
        self.date_entry.focus_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text="Log G-CSF Administration",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text=f"Patient: {self._patient_name}",
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons pinned to bottom
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

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=0, minsize=160)
        body.columnconfigure(1, weight=1)

        row = 0

        # Admin date
        self._grid_label(body, "Admin Date *", row)
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

        # Agent (config vocab)
        self._grid_label(body, "Agent *", row)
        agent_vocab = get_config().toxicity.gcsf.agent_vocab
        self.agent_var = tk.StringVar(value=agent_vocab[0] if agent_vocab else '')
        agent_menu = tk.OptionMenu(body, self.agent_var, *agent_vocab)
        agent_menu.config(bg=BG_ALT, fg=FG, font=('Arial', FONT_BODY),
                          highlightthickness=0, activebackground=BG_ALT)
        agent_menu['menu'].config(bg=BG_ALT, fg=FG)
        agent_menu.grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Dose (mg) — optional
        self._grid_label(body, "Dose mg (optional)", row)
        self.dose_var = tk.StringVar()
        self.dose_entry = tk.Entry(body, textvariable=self.dose_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.dose_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1
        tk.Label(body, text="e.g. 6 for pegfilgrastim 6 mg",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Prophylaxis type
        self._grid_label(body, "Prophylaxis Type", row)
        self.prophy_var = tk.StringVar(value='primary')
        p_frame = tk.Frame(body, bg=BG)
        p_frame.grid(row=row, column=1, sticky='w', pady=(0, 12))
        for pt in _PROPHYLAXIS_TYPES:
            tk.Radiobutton(p_frame, text=_PROPHYLAXIS_LABELS[pt].split(' (')[0],
                           variable=self.prophy_var, value=pt,
                           font=('Arial', FONT_HINT), bg=BG, fg=FG,
                           selectcolor=BG_ALT, activebackground=BG).pack(side='left', padx=(0, 8))
        row += 1

        # Cycle (optional)
        self._grid_label(body, "Cycle (optional)", row)
        cycle_labels = ['None'] + [f"Cycle {c.cycle_number}" for c in self._cycles]
        self.cycle_var = tk.StringVar(value='None')
        cycle_menu = tk.OptionMenu(body, self.cycle_var, *cycle_labels)
        cycle_menu.config(bg=BG_ALT, fg=FG, font=('Arial', FONT_BODY),
                          highlightthickness=0, activebackground=BG_ALT)
        cycle_menu['menu'].config(bg=BG_ALT, fg=FG)
        cycle_menu.grid(row=row, column=1, sticky='w', pady=(0, 12))
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
                                    bg=BG, fg='#e05555', anchor='w', wraplength=260)
        self.error_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 0))

        self._initial = self._snapshot()

    def _grid_label(self, parent, text, row):
        tk.Label(parent, text=text, font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG_MUTED, anchor='w',
                 ).grid(row=row, column=0, sticky='nw', padx=(0, 16), pady=(0, 4))

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth()  // 2 - self.winfo_width()  // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_cycle_id(self) -> int | None:
        label = self.cycle_var.get()
        if label == 'None':
            return None
        for c in self._cycles:
            if f"Cycle {c.cycle_number}" == label:
                return c.id
        return None

    def _snapshot(self) -> dict:
        return {
            'date':   self.date_var.get(),
            'agent':  self.agent_var.get(),
            'dose':   self.dose_var.get(),
            'prophy': self.prophy_var.get(),
            'cycle':  self.cycle_var.get(),
            'notes':  self.notes_var.get(),
        }

    def _has_changes(self) -> bool:
        s, i = self._snapshot(), self._initial
        return s['agent'] != i['agent'] or s['dose'] != i['dose'] or s['date'] != i['date']

    def _confirm_cancel(self):
        if self._has_changes():
            if not messagebox.askokcancel(
                'Discard changes?', 'Discard unsaved G-CSF record?', parent=self,
            ):
                return
        self.destroy()

    # ── Validation & Save ─────────────────────────────────────────────────────

    def get_form_data(self) -> dict:
        return self._snapshot()

    def validate(self) -> list:
        errors = []
        d = self.date_var.get()
        if not d:
            errors.append("Admin date is required.")
        else:
            try:
                parsed = date.fromisoformat(d)
                if parsed > date.today():
                    errors.append("Admin date cannot be in the future.")
                elif parsed.year < 2000:
                    errors.append("Admin date year must be 2000 or later.")
            except ValueError:
                errors.append("Invalid date — use YYYY-MM-DD format.")

        dose_str = self.dose_var.get().strip()
        if dose_str:
            try:
                val = float(dose_str)
                if val <= 0:
                    errors.append("Dose must be positive.")
            except ValueError:
                errors.append("Dose must be a number (e.g. 6 or 1.5).")

        return errors

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            if 'date' in errors[0].lower():
                self.date_entry.focus_set()
            return

        self.error_label.config(text="")
        dose_str = self.dose_var.get().strip()

        try:
            create_gcsf(self.conn, GcsfAdmin(
                patient_id       = self._patient_str_id,
                agent            = self.agent_var.get(),
                admin_date       = self.date_var.get(),
                cycle_id         = self._selected_cycle_id(),
                dose_mg          = float(dose_str) if dose_str else None,
                prophylaxis_type = self.prophy_var.get(),
                notes            = self.notes_var.get().strip() or None,
            ))
        except Exception as e:
            log.exception('Failed to save G-CSF for patient %s', self._patient_str_id)
            messagebox.showerror('Save Failed', f'Could not save G-CSF record:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()


class EditGcsfDialog(GcsfDialog):
    """Edit an existing GcsfAdmin record. Pre-populates from the given record."""

    def __init__(self, parent, conn, gcsf: GcsfAdmin, patient_db_id: int, on_save=None):
        self._editing = gcsf
        super().__init__(parent, conn, patient_db_id, on_save=on_save)
        self.title("Edit G-CSF Administration")
        self._populate()

    def _populate(self):
        g = self._editing
        d = g.admin_date
        self.date_var.set(d.isoformat() if hasattr(d, 'isoformat') else str(d))
        self.agent_var.set(g.agent)
        self.dose_var.set(str(g.dose_mg) if g.dose_mg is not None else '')
        self.prophy_var.set(g.prophylaxis_type or 'primary')
        self.notes_var.set(g.notes or '')
        self._initial = self._snapshot()

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            return

        self.error_label.config(text="")
        dose_str = self.dose_var.get().strip()

        try:
            updated = GcsfAdmin(
                id               = self._editing.id,
                patient_id       = self._editing.patient_id,
                agent            = self.agent_var.get(),
                admin_date       = self.date_var.get(),
                cycle_id         = self._editing.cycle_id,
                dose_mg          = float(dose_str) if dose_str else None,
                prophylaxis_type = self.prophy_var.get(),
                notes            = self.notes_var.get().strip() or None,
            )
            update_gcsf(self.conn, updated)
        except Exception as e:
            log.exception('Failed to update G-CSF id=%s', self._editing.id)
            messagebox.showerror('Save Failed', f'Could not update G-CSF record:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
