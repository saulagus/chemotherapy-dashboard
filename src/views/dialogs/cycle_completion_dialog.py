import tkinter as tk
from tkinter import ttk
from datetime import date
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED
from models import Cycle, add_cycle, update_cycle

DOSE_REASONS = [
    'Neutropenia', 'Neuropathy', 'Thrombocytopenia',
    'Hepatotoxicity', 'Patient Tolerance',
    'Physician Discretion', 'Other',
]


class CycleCompletionDialog(tk.Toplevel):
    """Modal dialog for marking a cycle as completed.

    Opens when the user clicks a pending or current cycle box.
    Creates a new Cycle DB row if one doesn't exist yet, or updates
    an existing one.

    Parameters
    ----------
    parent       : tk.Widget        — parent widget (timeline component)
    conn         : sqlite3.Connection
    patient_id   : int              — DB integer id of the patient
    cycle_number : int              — cycle being completed (1-8)
    cycle        : Cycle | None     — existing Cycle object, or None if not in DB yet
    on_save      : callable | None  — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id, cycle_number, cycle=None, on_save=None):
        super().__init__(parent)
        self.conn         = conn
        self.patient_id   = patient_id
        self.cycle_number = cycle_number
        self.cycle        = cycle
        self.on_save      = on_save

        self.title(f"Complete Cycle {cycle_number}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        phase = 'AC' if self.cycle_number <= 4 else 'T'

        # Header — cycle number and phase (read-only display)
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text=f"Cycle {self.cycle_number} — {phase} Phase",
                 font=('Arial', 16, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text="Record completion details below.",
                 font=('Arial', 12), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both')

        # Completion date
        self._add_label(body, "Completion Date (YYYY-MM-DD)")
        self.date_var = tk.StringVar(value=str(date.today()))
        if self.cycle and self.cycle.actual_date:
            self.date_var.set(str(self.cycle.actual_date))
        tk.Entry(body, textvariable=self.date_var,
                 font=('Arial', 13), bg=BG_ALT, fg=FG,
                 insertbackground=FG, relief='flat',
                 highlightbackground=SEPARATOR, highlightthickness=1,
                 ).pack(fill='x', pady=(4, 14))

        # Dose percentage — combobox dropdown
        DOSE_OPTIONS = ['100% (Full dose)', '85%', '75%', '50%', 'Custom']
        self._add_label(body, "Dose Given")

        self.dose_var = tk.StringVar(value='100% (Full dose)')
        if self.cycle and self.cycle.dose_percent is not None:
            pct = int(self.cycle.dose_percent)
            if pct == 100:
                self.dose_var.set('100% (Full dose)')
            elif pct in (85, 75, 50):
                self.dose_var.set(f'{pct}%')
            else:
                self.dose_var.set('Custom')

        self.dose_combo = ttk.Combobox(body, textvariable=self.dose_var,
                                       values=DOSE_OPTIONS, state='readonly',
                                       font=('Arial', 13))
        self.dose_combo.pack(fill='x', pady=(4, 14))
        self.dose_combo.bind('<<ComboboxSelected>>', lambda e: self._on_dose_change())

        # Custom dose entry — shown only when Custom selected
        self.custom_dose_frame = tk.Frame(body, bg=BG)
        self._add_label(self.custom_dose_frame, "Custom Dose (%)")
        self.custom_dose_var = tk.StringVar(value='')
        if self.cycle and self.cycle.dose_percent and int(self.cycle.dose_percent) not in (100, 85, 75, 50):
            self.custom_dose_var.set(str(int(self.cycle.dose_percent)))
        tk.Entry(self.custom_dose_frame, textvariable=self.custom_dose_var,
                 font=('Arial', 13), bg=BG_ALT, fg=FG, insertbackground=FG,
                 relief='flat', highlightbackground=SEPARATOR, highlightthickness=1,
                 width=8).pack(anchor='w', pady=(4, 0))

        # Dose reason dropdown — shown only when dose < 100%
        self.reason_frame = tk.Frame(body, bg=BG)
        self._add_label(self.reason_frame, "Reason for Dose Modification")

        # Pre-fill: if saved reason isn't in the list it was a custom "Other" entry
        saved_reason = self.cycle.dose_reason if self.cycle and self.cycle.dose_reason else ''
        initial_reason = saved_reason if saved_reason in DOSE_REASONS else ('Other' if saved_reason else DOSE_REASONS[0])
        self.reason_var = tk.StringVar(value=initial_reason)

        self.reason_combo = ttk.Combobox(self.reason_frame, textvariable=self.reason_var,
                                         values=DOSE_REASONS, state='readonly',
                                         font=('Arial', 12))
        self.reason_combo.pack(fill='x', pady=(4, 6))
        self.reason_combo.bind('<<ComboboxSelected>>', lambda e: self._on_reason_change())

        # "Other" free text — shown only when Other selected
        self.other_reason_frame = tk.Frame(self.reason_frame, bg=BG)
        self._add_label(self.other_reason_frame, "Please specify")
        self.other_reason_var = tk.StringVar(value=saved_reason if saved_reason not in DOSE_REASONS else '')
        tk.Entry(self.other_reason_frame, textvariable=self.other_reason_var,
                 font=('Arial', 12), bg=BG_ALT, fg=FG, insertbackground=FG,
                 relief='flat', highlightbackground=SEPARATOR, highlightthickness=1,
                 ).pack(fill='x', pady=(4, 0))

        self._on_reason_change()

        # Notes — optional, max 500 characters
        notes_header = tk.Frame(body, bg=BG)
        notes_header.pack(fill='x')
        self._add_label(notes_header, "Notes (optional)")
        self.char_count_label = tk.Label(notes_header, text="0 / 500",
                                         font=('Arial', 10), bg=BG, fg=FG_MUTED)
        self.char_count_label.pack(side='right')

        self.notes_text = tk.Text(body, height=4, font=('Arial', 12),
                                  bg=BG_ALT, fg=FG, insertbackground=FG,
                                  relief='flat', wrap='word',
                                  highlightbackground=SEPARATOR, highlightthickness=1)
        self.notes_text.pack(fill='x', pady=(4, 0))
        if self.cycle and self.cycle.notes:
            self.notes_text.insert('1.0', self.cycle.notes)
        self.notes_text.bind('<KeyRelease>', self._on_notes_change)
        self._on_notes_change()

        # Trigger show/hide on initial state
        self._on_dose_change()

        # Inline error
        self.error_label = tk.Label(body, text='', font=('Arial', 11),
                                    bg=BG, fg='#e05555', anchor='w')
        self.error_label.pack(anchor='w', pady=(8, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons
        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(fill='x')

        cancel = tk.Label(btn_row, text="Cancel", font=('Arial', 13),
                          bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        cancel.pack(side='right')
        cancel.bind('<Button-1>', lambda e: self.destroy())

        save = tk.Label(btn_row, text="Mark Complete", font=('Arial', 13, 'bold'),
                        bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save.pack(side='right', padx=(0, 12))
        save.bind('<Button-1>', lambda e: self._on_save())

    def _add_label(self, parent, text):
        tk.Label(parent, text=text, font=('Arial', 12),
                 bg=BG, fg=FG_MUTED, anchor='w').pack(anchor='w')

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.winfo_screenwidth()  // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"+{x}+{y}")

    # ── Dose visibility ───────────────────────────────────────────────────────

    def _on_notes_change(self, event=None):
        """Update character counter and cap input at 500 characters."""
        content = self.notes_text.get('1.0', 'end-1c')
        if len(content) > 500:
            self.notes_text.delete('1.0', 'end')
            self.notes_text.insert('1.0', content[:500])
            content = content[:500]
        self.char_count_label.config(text=f"{len(content)} / 500")

    def _on_reason_change(self):
        """Show free text entry when 'Other' is selected as the reason."""
        if self.reason_var.get() == 'Other':
            self.other_reason_frame.pack(fill='x', pady=(4, 0))
        else:
            self.other_reason_frame.pack_forget()

    def _on_dose_change(self):
        """Show/hide custom dose entry and reason dropdown based on selection."""
        selected   = self.dose_var.get()
        is_custom  = selected == 'Custom'
        is_reduced = selected != '100% (Full dose)'

        if is_custom:
            self.custom_dose_frame.pack(fill='x', pady=(0, 8))
        else:
            self.custom_dose_frame.pack_forget()

        if is_reduced:
            self.reason_frame.pack(fill='x', pady=(0, 14))
        else:
            self.reason_frame.pack_forget()

    # ── Validation & Save ─────────────────────────────────────────────────────

    def _show_error(self, msg):
        self.error_label.config(text=msg)

    def _clear_error(self):
        self.error_label.config(text='')

    def _on_save(self):
        self._clear_error()

        # Validate date
        date_str = self.date_var.get().strip()
        try:
            actual_date = date.fromisoformat(date_str)
        except ValueError:
            self._show_error("Invalid date — use YYYY-MM-DD format.")
            return
        if actual_date > date.today():
            self._show_error("Completion date cannot be in the future.")
            return

        # Validate dose
        dose_selection = self.dose_var.get()
        if dose_selection == 'Custom':
            try:
                dose_percent = float(self.custom_dose_var.get().strip())
                if not (1 <= dose_percent <= 100):
                    raise ValueError
            except ValueError:
                self._show_error("Custom dose must be a number between 1 and 100.")
                return
        else:
            dose_percent = float(dose_selection.replace('% (Full dose)', '').replace('%', ''))

        if dose_percent < 100:
            if self.reason_var.get() == 'Other':
                other = self.other_reason_var.get().strip()
                if not other:
                    self._show_error("Please specify the reason for dose modification.")
                    return
                dose_reason = other
            else:
                dose_reason = self.reason_var.get()
        else:
            dose_reason = None
        notes       = self.notes_text.get('1.0', 'end').strip() or None
        phase       = 'AC' if self.cycle_number <= 4 else 'T'

        if self.cycle is None:
            add_cycle(self.conn, Cycle(
                patient_id=self.patient_id,
                cycle_number=self.cycle_number,
                phase=phase,
                actual_date=actual_date,
                status='completed',
                dose_percent=dose_percent,
                dose_reason=dose_reason,
                notes=notes,
            ))
        else:
            self.cycle.actual_date  = actual_date
            self.cycle.status       = 'completed'
            self.cycle.dose_percent = dose_percent
            self.cycle.dose_reason  = dose_reason
            self.cycle.notes        = notes
            update_cycle(self.conn, self.cycle)

        if self.on_save:
            self.on_save()
        self.destroy()
