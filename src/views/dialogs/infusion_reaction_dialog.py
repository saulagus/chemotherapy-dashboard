"""Infusion reaction dialog (US-028).

InfusionReactionDialog   — log a new reaction
EditInfusionReactionDialog — edit an existing one

After save the rechallenge advisory is shown inline in the dialog (Grade ≥ 3
advisory text surfaced here; Sprint 8 enforces the block at cycle completion).
"""

import json
import logging
import tkinter as tk
from tkinter import messagebox
from datetime import date

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)
from models import get_patient_by_db_id
from clinical.infusion_reactions import rechallenge_advice
from services.infusion_reactions import (
    InfusionReaction, create_reaction, update_reaction,
)
from models import get_cycles_by_patient
from config import get as get_config

log = logging.getLogger(__name__)

_GRADES = [1, 2, 3, 4]
_RECHALLENGE_OUTCOMES = ['', 'tolerated', 'recurred', 'switched_agent']
_OUTCOME_LABELS = {
    '':              'None / pending',
    'tolerated':     'Tolerated',
    'recurred':      'Recurred',
    'switched_agent':'Switched agent',
}


class InfusionReactionDialog(tk.Toplevel):
    """Modal dialog for logging a new infusion reaction.

    Parameters
    ----------
    parent      : tk.Widget
    conn        : sqlite3.Connection
    patient_id  : int  — DB integer id of the patient
    on_save     : callable | None — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id: int, on_save=None):
        super().__init__(parent)
        self.conn          = conn
        self.patient_db_id = patient_id
        self.on_save       = on_save

        patient = get_patient_by_db_id(conn, patient_id)
        self._patient_str_id = patient.patient_id if patient else ''
        self._patient_name   = patient.name if patient else ''

        # Load cycles for this patient (for the cycle dropdown)
        self._cycles = get_cycles_by_patient(conn, patient_id) if patient else []

        self.title("Log Infusion Reaction")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()
        self.geometry('520x660')
        self.protocol('WM_DELETE_WINDOW', self._confirm_cancel)
        self.bind('<Escape>', lambda e: self._confirm_cancel())

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text="Log Infusion Reaction",
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

        # Body
        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=0, minsize=160)
        body.columnconfigure(1, weight=1)
        self._body = body

        row = 0

        # Cycle (required)
        self._grid_label(body, "Cycle *", row)
        cycle_labels = [f"Cycle {c.cycle_number}" for c in self._cycles] if self._cycles else ['No cycles']
        self.cycle_var = tk.StringVar(value=cycle_labels[0] if cycle_labels else '')
        cycle_menu = tk.OptionMenu(body, self.cycle_var, *cycle_labels)
        cycle_menu.config(bg=BG_ALT, fg=FG, font=('Arial', FONT_BODY),
                          highlightthickness=0, activebackground=BG_ALT)
        cycle_menu['menu'].config(bg=BG_ALT, fg=FG)
        cycle_menu.grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Agent (required)
        self._grid_label(body, "Agent *", row)
        self.agent_var = tk.StringVar()
        self.agent_entry = tk.Entry(body, textvariable=self.agent_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.agent_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1
        tk.Label(body, text="e.g. paclitaxel, doxorubicin",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Onset (minutes)
        self._grid_label(body, "Onset (min) *", row)
        self.onset_var = tk.StringVar()
        self.onset_entry = tk.Entry(body, textvariable=self.onset_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.onset_entry.grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1
        tk.Label(body, text="Minutes from infusion start",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Severity grade
        self._grid_label(body, "Severity Grade *", row)
        self.grade_var = tk.IntVar(value=1)
        grade_frame = tk.Frame(body, bg=BG)
        grade_frame.grid(row=row, column=1, sticky='w', pady=(0, 4))
        for g in _GRADES:
            tk.Radiobutton(grade_frame, text=f"G{g}", variable=self.grade_var, value=g,
                           font=('Arial', FONT_BODY), bg=BG, fg=FG,
                           selectcolor=BG_ALT, activebackground=BG,
                           command=self._update_rechallenge_advisory).pack(side='left', padx=(0, 10))
        row += 1
        self.advisory_label = tk.Label(body, text="",
                 font=('Arial', FONT_HINT), bg=BG, fg='#FFA726', anchor='w', wraplength=280)
        self.advisory_label.grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Symptoms (multi-select checkboxes from config vocab)
        self._grid_label(body, "Symptoms", row)
        vocab = get_config().toxicity.infusion_reactions.symptom_vocab
        sym_frame = tk.Frame(body, bg=BG)
        sym_frame.grid(row=row, column=1, sticky='w', pady=(0, 12))
        self._symptom_vars = {}
        for i, sym in enumerate(vocab):
            var = tk.BooleanVar(value=False)
            self._symptom_vars[sym] = var
            col = i % 3
            r   = i // 3
            tk.Checkbutton(sym_frame, text=sym.replace('_', ' '), variable=var,
                           font=('Arial', FONT_HINT), bg=BG, fg=FG,
                           selectcolor=BG_ALT, activebackground=BG,
                           ).grid(row=r, column=col, sticky='w', padx=(0, 8))
        row += 1

        # Response (free text)
        self._grid_label(body, "Response (optional)", row)
        self.response_var = tk.StringVar()
        self.response_entry = tk.Entry(body, textvariable=self.response_var,
                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                insertbackground=FG, relief='flat',
                highlightbackground=SEPARATOR, highlightthickness=1)
        self.response_entry.grid(row=row, column=1, sticky='ew', pady=(0, 12))
        row += 1

        # Rechallenge outcome
        self._grid_label(body, "Rechallenge outcome", row)
        self.outcome_var = tk.StringVar(value='')
        outcome_display = [_OUTCOME_LABELS[k] for k in _RECHALLENGE_OUTCOMES]
        outcome_menu = tk.OptionMenu(body, self.outcome_var,
                                     *[_OUTCOME_LABELS[k] for k in _RECHALLENGE_OUTCOMES])
        outcome_menu.config(bg=BG_ALT, fg=FG, font=('Arial', FONT_BODY),
                            highlightthickness=0, activebackground=BG_ALT)
        outcome_menu['menu'].config(bg=BG_ALT, fg=FG)
        outcome_menu.grid(row=row, column=1, sticky='w', pady=(0, 12))
        row += 1

        # Error label
        self.error_label = tk.Label(body, text="", font=('Arial', FONT_HINT),
                                    bg=BG, fg='#e05555', anchor='w', wraplength=280)
        self.error_label.grid(row=row, column=0, columnspan=2, sticky='w', pady=(4, 0))

        self._update_rechallenge_advisory()
        self._initial = self._snapshot()
        self.agent_entry.focus_set()

    def _grid_label(self, parent, text, row):
        tk.Label(parent, text=text, font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG_MUTED, anchor='w',
                 ).grid(row=row, column=0, sticky='nw', padx=(0, 16), pady=(0, 4))

    def _center(self):
        self.update_idletasks()
        x = self.winfo_screenwidth()  // 2 - self.winfo_width()  // 2
        y = self.winfo_screenheight() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")

    # ── Advisory ──────────────────────────────────────────────────────────────

    def _update_rechallenge_advisory(self):
        grade = self.grade_var.get()
        try:
            cfg    = get_config().toxicity.model_dump()
            advice = rechallenge_advice(grade, cfg)
            color  = '#e05555' if advice.hard_block else '#FFA726'
            self.advisory_label.config(text=advice.advisory_text, fg=color)
        except Exception:
            self.advisory_label.config(text="")

    # ── Close ─────────────────────────────────────────────────────────────────

    def _snapshot(self) -> dict:
        return {
            'cycle':    self.cycle_var.get(),
            'agent':    self.agent_var.get(),
            'onset':    self.onset_var.get(),
            'grade':    self.grade_var.get(),
            'response': self.response_var.get(),
            'outcome':  self.outcome_var.get(),
            'symptoms': {k: v.get() for k, v in self._symptom_vars.items()},
        }

    def _has_changes(self) -> bool:
        s = self._snapshot()
        i = self._initial
        return (s['agent'] != i['agent'] or s['onset'] != i['onset'] or
                s['grade'] != i['grade'] or s['response'] != i['response'] or
                any(s['symptoms'][k] for k in s['symptoms']))

    def _confirm_cancel(self):
        if self._has_changes():
            if not messagebox.askokcancel(
                'Discard changes?', 'Discard unsaved reaction?', parent=self,
            ):
                return
        self.destroy()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_cycle_id(self) -> int | None:
        label = self.cycle_var.get()
        for c in self._cycles:
            if f"Cycle {c.cycle_number}" == label:
                return c.id
        return None

    def _selected_symptoms(self) -> list:
        return [sym for sym, var in self._symptom_vars.items() if var.get()]

    def _label_to_outcome_key(self, label: str) -> str:
        for k, l in _OUTCOME_LABELS.items():
            if l == label:
                return k
        return ''

    # ── Validation & Save ─────────────────────────────────────────────────────

    def get_form_data(self) -> dict:
        return self._snapshot()

    def validate(self) -> list:
        errors = []
        if not self.agent_var.get().strip():
            errors.append("Agent is required.")
        if not self.onset_var.get().strip():
            errors.append("Onset (minutes) is required.")
        else:
            try:
                val = int(self.onset_var.get())
                if val < 0:
                    errors.append("Onset must be a non-negative integer.")
            except ValueError:
                errors.append("Onset must be a whole number of minutes.")
        if not self._cycles:
            errors.append("No cycles on record — complete a cycle before logging a reaction.")
        return errors

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            return

        self.error_label.config(text="")
        cycle_id = self._selected_cycle_id()
        if cycle_id is None:
            self.error_label.config(text="Please select a valid cycle.")
            return

        symptoms = self._selected_symptoms()
        outcome_key = self._label_to_outcome_key(self.outcome_var.get())

        try:
            create_reaction(self.conn, InfusionReaction(
                patient_id          = self._patient_str_id,
                cycle_id            = cycle_id,
                agent               = self.agent_var.get().strip(),
                onset_min           = int(self.onset_var.get()),
                severity_grade      = self.grade_var.get(),
                symptoms_json       = json.dumps(symptoms),
                response            = self.response_var.get().strip() or None,
                rechallenge_outcome = outcome_key or None,
            ))
        except Exception as e:
            log.exception('Failed to save reaction for patient %s', self._patient_str_id)
            messagebox.showerror('Save Failed', f'Could not save reaction:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()


class EditInfusionReactionDialog(InfusionReactionDialog):
    """Edit an existing InfusionReaction. Pre-populates from the given record."""

    def __init__(self, parent, conn, reaction: InfusionReaction,
                 patient_db_id: int, on_save=None):
        self._editing = reaction
        super().__init__(parent, conn, patient_db_id, on_save=on_save)
        self.title("Edit Infusion Reaction")
        self._populate()

    def _populate(self):
        r = self._editing
        self.agent_var.set(r.agent)
        self.onset_var.set(str(r.onset_min))
        self.grade_var.set(r.severity_grade)
        self.response_var.set(r.response or '')
        label = _OUTCOME_LABELS.get(r.rechallenge_outcome or '', _OUTCOME_LABELS[''])
        self.outcome_var.set(label)
        for sym in r.symptoms:
            if sym in self._symptom_vars:
                self._symptom_vars[sym].set(True)
        self._update_rechallenge_advisory()
        self._initial = self._snapshot()

    def _on_save(self):
        errors = self.validate()
        if errors:
            self.error_label.config(text=errors[0])
            return

        self.error_label.config(text="")
        symptoms    = self._selected_symptoms()
        outcome_key = self._label_to_outcome_key(self.outcome_var.get())

        try:
            updated = InfusionReaction(
                id                  = self._editing.id,
                patient_id          = self._editing.patient_id,
                cycle_id            = self._editing.cycle_id,
                agent               = self.agent_var.get().strip(),
                onset_min           = int(self.onset_var.get()),
                severity_grade      = self.grade_var.get(),
                symptoms_json       = json.dumps(symptoms),
                response            = self.response_var.get().strip() or None,
                rechallenge_outcome = outcome_key or None,
            )
            update_reaction(self.conn, updated)
        except Exception as e:
            log.exception('Failed to update reaction id=%s', self._editing.id)
            messagebox.showerror('Save Failed', f'Could not update reaction:\n{e}', parent=self)
            return

        if self.on_save:
            self.on_save()
        self.destroy()
