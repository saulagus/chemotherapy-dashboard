"""Symptom quick-entry dialog (US-030).

SymptomQuickEntryDialog — enter a grade 0–4 for each applicable symptom
                           for the given cycle. Designed to be launched
                           after a cycle save (skippable).
"""

import logging
import tkinter as tk
from tkinter import messagebox
from datetime import date

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)
from models import get_patient_by_db_id, Cycle
from clinical.symptoms import applicable_symptoms, is_advisory
from services.symptoms import SymptomEntry, create_many
from config import get as get_config

log = logging.getLogger(__name__)

_ADVISORY_GLYPH = ' ⚠'   # appended to grade label when advisory


def _cycle_phase(cycle: Cycle) -> str:
    """Return 'AC' or 'T' based on cycle number."""
    return 'AC' if cycle.cycle_number <= 4 else 'T'


class SymptomQuickEntryDialog(tk.Toplevel):
    """Modal dialog to grade all applicable symptoms for a cycle.

    One row per symptom. Grade 0–4 via Radiobutton. Notes field per row
    is omitted for speed — whole-dialog notes field instead.

    Parameters
    ----------
    parent      : tk.Widget
    conn        : sqlite3.Connection
    patient_id  : int  — DB integer id of the patient
    cycle       : Cycle — the cycle whose symptoms are being recorded
    on_save     : callable | None — called with no args after a successful save
    on_skip     : callable | None — called with no args if user skips
    """

    def __init__(self, parent, conn, patient_id: int, cycle: Cycle,
                 on_save=None, on_skip=None):
        super().__init__(parent)
        self.conn          = conn
        self.patient_db_id = patient_id
        self.cycle         = cycle
        self.on_save       = on_save
        self.on_skip       = on_skip

        patient = get_patient_by_db_id(conn, patient_id)
        self._patient_str_id = patient.patient_id if patient else ''
        self._patient_name   = patient.name if patient else ''

        self._phase    = _cycle_phase(cycle)
        cfg            = get_config().toxicity.model_dump()
        self._symptoms = applicable_symptoms(self._phase, cfg)
        self._cfg      = cfg

        self.title(f"Symptom Check — Cycle {cycle.cycle_number}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()
        self.protocol('WM_DELETE_WINDOW', self._on_skip)
        self.bind('<Escape>', lambda e: self._on_skip())

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=14)
        header.pack(fill='x')
        tk.Label(header,
                 text=f"Cycle {self.cycle.cycle_number} Symptom Check ({self._phase} Phase)",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text=f"Patient: {self._patient_name}  ·  Grade 0 = none, Grade 4 = severe",
                 font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons pinned to bottom
        tk.Frame(self, bg=SEPARATOR, height=1).pack(side='bottom', fill='x')
        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(side='bottom', fill='x')

        skip_btn = tk.Label(btn_row, text="Skip", font=('Arial', FONT_BODY),
                            bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        skip_btn.pack(side='right')
        skip_btn.bind('<Button-1>', lambda e: self._on_skip())

        save_btn = tk.Label(btn_row, text="Save Symptoms",
                            font=('Arial', FONT_BODY, 'bold'),
                            bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save_btn.pack(side='right', padx=(0, 12))
        save_btn.bind('<Button-1>', lambda e: self._on_save())

        # Body
        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill='both', expand=True)

        # Column headers
        header_row = tk.Frame(body, bg=BG)
        header_row.pack(fill='x', pady=(0, 8))
        tk.Label(header_row, text="Symptom", width=20, anchor='w',
                 font=('Arial', FONT_LABEL, 'bold'), bg=BG, fg=FG_MUTED).pack(side='left')
        for g in range(5):
            tk.Label(header_row, text=f"G{g}", width=5, anchor='center',
                     font=('Arial', FONT_LABEL, 'bold'), bg=BG, fg=FG_MUTED).pack(side='left')

        tk.Frame(body, bg=SEPARATOR, height=1).pack(fill='x', pady=(0, 8))

        # One row per symptom
        self._grade_vars: dict[str, tk.IntVar] = {}
        for sym in self._symptoms:
            self._build_symptom_row(body, sym)

        # Error label
        self.error_label = tk.Label(body, text="", font=('Arial', FONT_HINT),
                                    bg=BG, fg='#e05555', anchor='w')
        self.error_label.pack(fill='x', pady=(12, 0))

        # Adjust height to fit symptom count
        height = 240 + len(self._symptoms) * 36
        self.geometry(f'520x{height}')

    def _build_symptom_row(self, parent, symptom: str):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=2)

        var = tk.IntVar(value=0)
        self._grade_vars[symptom] = var

        label_text = symptom.replace('_', ' ').capitalize()
        tk.Label(row, text=label_text, width=20, anchor='w',
                 font=('Arial', FONT_BODY), bg=BG, fg=FG).pack(side='left')

        for g in range(5):
            tk.Radiobutton(row, text='', variable=var, value=g,
                           width=4,
                           font=('Arial', FONT_BODY), bg=BG, fg=FG,
                           selectcolor=BG_ALT, activebackground=BG,
                           command=lambda s=symptom: self._update_advisory(s),
                           ).pack(side='left')

        # Advisory glyph (shown when grade ≥ advisory_grade)
        adv = tk.Label(row, text='', font=('Arial', FONT_HINT), bg=BG, fg='#FFA726')
        adv.pack(side='left', padx=(4, 0))
        var.trace_add('write', lambda *a, sym=symptom, lbl=adv: self._refresh_advisory(sym, lbl))

    def _update_advisory(self, symptom: str):
        pass  # trace handles it

    def _refresh_advisory(self, symptom: str, label: tk.Label):
        grade = self._grade_vars[symptom].get()
        label.config(text=_ADVISORY_GLYPH if is_advisory(grade, self._cfg) else '')

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth()  // 2 - self.winfo_width()  // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    # ── Save / Skip ───────────────────────────────────────────────────────────

    def _on_skip(self):
        if self.on_skip:
            self.on_skip()
        self.destroy()

    def _on_save(self):
        self.error_label.config(text="")
        today = str(date.today())

        entries = [
            SymptomEntry(
                patient_id = self._patient_str_id,
                cycle_id   = self.cycle.id,
                entry_date = today,
                symptom    = sym,
                grade      = var.get(),
            )
            for sym, var in self._grade_vars.items()
        ]

        try:
            create_many(self.conn, entries)
        except Exception as e:
            log.exception('Failed to save symptoms for patient %s', self._patient_str_id)
            messagebox.showerror('Save Failed', f'Could not save symptoms:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
