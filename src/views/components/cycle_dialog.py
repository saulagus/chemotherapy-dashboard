import tkinter as tk
from datetime import date
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED, FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER
from tkinter import messagebox
from models import Cycle
from services.cycles import create_cycle, update_cycle, delete_cycle


class CycleCompletionDialog(tk.Toplevel):
    """Modal dialog for marking a cycle as completed.

    Opens when the user clicks a pending or current cycle box.
    Creates a new Cycle DB row if one doesn't exist yet, or updates
    an existing one.

    Parameters
    ----------
    parent      : tk.Widget  — parent widget (timeline component)
    conn        : sqlite3.Connection
    patient_id  : int        — DB integer id of the patient
    cycle_number: int        — cycle being completed (1-8)
    cycle       : Cycle | None — existing Cycle object, or None if not yet in DB
    on_save     : callable   — called with no args after a successful save
    """

    def __init__(self, parent, conn, patient_id, cycle_number, cycle=None, on_save=None):
        super().__init__(parent)
        self.conn         = conn
        self.patient_id   = patient_id
        self.cycle_number = cycle_number
        self.cycle        = cycle        # None if cycle has no DB row yet
        self.on_save      = on_save

        self.title(f"Complete Cycle {cycle_number}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()                  # Modal — blocks parent interaction

        self._build_ui()
        self._center()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        phase = 'AC' if self.cycle_number <= 4 else 'T'

        # Header
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text=f"Cycle {self.cycle_number} — {phase} Phase",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text="Record completion details below.",
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Form body
        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both')

        # Actual date
        self._add_label(body, "Completion Date (YYYY-MM-DD)")
        self.date_var = tk.StringVar(value=str(date.today()))
        if self.cycle and self.cycle.actual_date:
            self.date_var.set(str(self.cycle.actual_date))
        self.date_entry = tk.Entry(body, textvariable=self.date_var,
                                   font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                                   insertbackground=FG, relief='flat',
                                   highlightbackground=SEPARATOR, highlightthickness=1)
        self.date_entry.pack(fill='x', pady=(4, 14))

        # Dose percentage selector
        self._add_label(body, "Dose Given")
        dose_row = tk.Frame(body, bg=BG)
        dose_row.pack(fill='x', pady=(4, 14))

        self.dose_var = tk.StringVar(value='100')
        if self.cycle and self.cycle.dose_percent is not None:
            pct = int(self.cycle.dose_percent)
            self.dose_var.set(str(pct) if pct in (100, 85, 75, 50) else 'custom')

        for label, value in [('100%', '100'), ('85%', '85'), ('75%', '75'), ('50%', '50'), ('Custom', 'custom')]:
            rb = tk.Radiobutton(dose_row, text=label, variable=self.dose_var, value=value,
                                font=('Arial', FONT_LABEL), bg=BG, fg=FG,
                                selectcolor=BG_ALT, activebackground=BG, activeforeground=FG,
                                command=self._on_dose_change)
            rb.pack(side='left', padx=(0, 12))

        # Custom dose entry — shown only when 'Custom' selected
        self.custom_dose_frame = tk.Frame(body, bg=BG)
        self._add_label(self.custom_dose_frame, "Custom Dose (%)")
        self.custom_dose_var = tk.StringVar(value='')
        if self.cycle and self.cycle.dose_percent and int(self.cycle.dose_percent) not in (100, 85, 75, 50):
            self.custom_dose_var.set(str(int(self.cycle.dose_percent)))
        tk.Entry(self.custom_dose_frame, textvariable=self.custom_dose_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG, insertbackground=FG,
                 relief='flat', highlightbackground=SEPARATOR, highlightthickness=1,
                 width=8).pack(anchor='w', pady=(4, 0))

        # Dose reason — shown only when dose < 100%
        self.reason_frame = tk.Frame(body, bg=BG)
        self._add_label(self.reason_frame, "Reason for Dose Modification")
        REASONS = [
            'Neutropenia', 'Thrombocytopenia', 'Neuropathy',
            'Fatigue / Performance Status', 'Renal Impairment',
            'Hepatic Impairment', 'Patient Request', 'Other',
        ]
        self.reason_var = tk.StringVar(value=self.cycle.dose_reason if self.cycle and self.cycle.dose_reason else REASONS[0])
        from tkinter import ttk
        reason_menu = ttk.Combobox(self.reason_frame, textvariable=self.reason_var,
                                   values=REASONS, state='readonly', font=('Arial', FONT_LABEL))
        reason_menu.pack(fill='x', pady=(4, 0))

        # Notes
        self._add_label(body, "Notes (optional)")
        self.notes_text = tk.Text(body, height=4, font=('Arial', FONT_LABEL),
                                  bg=BG_ALT, fg=FG, insertbackground=FG,
                                  relief='flat', wrap='word',
                                  highlightbackground=SEPARATOR, highlightthickness=1)
        self.notes_text.pack(fill='x', pady=(4, 0))
        if self.cycle and self.cycle.notes:
            self.notes_text.insert('1.0', self.cycle.notes)

        # Show/hide dose-related frames based on initial value
        self._on_dose_change()

        # Inline error label
        self.error_label = tk.Label(body, text='', font=('Arial', FONT_HINT),
                                    bg=BG, fg='#e05555', anchor='w')
        self.error_label.pack(anchor='w', pady=(8, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons
        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(fill='x')

        cancel = tk.Label(btn_row, text="Cancel", font=('Arial', FONT_BODY),
                          bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        cancel.pack(side='right')
        cancel.bind('<Button-1>', lambda e: self.destroy())

        save = tk.Label(btn_row, text="Mark Complete", font=('Arial', FONT_BODY, 'bold'),
                        bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save.pack(side='right', padx=(0, 12))
        save.bind('<Button-1>', lambda e: self._on_save())

    def _on_dose_change(self):
        """Show/hide custom dose entry and reason dropdown based on selection."""
        is_custom  = self.dose_var.get() == 'custom'
        is_reduced = self.dose_var.get() != '100'

        if is_custom:
            self.custom_dose_frame.pack(after=self.custom_dose_frame.master.winfo_children()[0], fill='x', pady=(0, 8))
        else:
            self.custom_dose_frame.pack_forget()

        if is_reduced:
            self.reason_frame.pack(fill='x', pady=(0, 14))
        else:
            self.reason_frame.pack_forget()

    def _add_label(self, parent, text):
        tk.Label(parent, text=text, font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG_MUTED, anchor='w').pack(anchor='w')

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.winfo_screenwidth()  // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"+{x}+{y}")

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

        # Validate and read dose
        dose_selection = self.dose_var.get()
        if dose_selection == 'custom':
            try:
                dose_percent = float(self.custom_dose_var.get().strip())
                if not (1 <= dose_percent <= 100):
                    raise ValueError
            except ValueError:
                self._show_error("Custom dose must be a number between 1 and 100.")
                return
        else:
            dose_percent = float(dose_selection)

        dose_reason = self.reason_var.get() if dose_percent < 100 else None
        notes       = self.notes_text.get('1.0', 'end').strip() or None
        phase       = 'AC' if self.cycle_number <= 4 else 'T'

        if self.cycle is None:
            # No DB row yet — create one
            new_cycle = Cycle(
                patient_id=self.patient_id,
                cycle_number=self.cycle_number,
                phase=phase,
                actual_date=actual_date,
                status='completed',
                dose_percent=dose_percent,
                dose_reason=dose_reason,
                notes=notes,
            )
            create_cycle(self.conn, new_cycle)
        else:
            # Update existing row
            self.cycle.actual_date  = actual_date
            self.cycle.status       = 'completed'
            self.cycle.dose_percent = dose_percent
            self.cycle.dose_reason  = dose_reason
            self.cycle.notes        = notes
            update_cycle(self.conn, self.cycle)

        if self.on_save:
            self.on_save()
        self.destroy()


class CycleDetailDialog(tk.Toplevel):
    """Read-only view of a completed cycle, with an Edit button.

    Opens when the user clicks a completed cycle box.

    Parameters
    ----------
    parent      : tk.Widget
    conn        : sqlite3.Connection
    patient_id  : int
    cycle       : Cycle   — the completed cycle to display
    on_save     : callable — passed through to CycleCompletionDialog if user edits
    """

    def __init__(self, parent, conn, patient_id, cycle, on_save=None):
        super().__init__(parent)
        self.conn       = conn
        self.patient_id = patient_id
        self.cycle      = cycle
        self.on_save    = on_save

        self.title(f"Cycle {cycle.cycle_number} Details")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._center()

    def _build_ui(self):
        c = self.cycle
        phase = 'AC' if c.cycle_number <= 4 else 'T'

        # Header
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text=f"Cycle {c.cycle_number} — {phase} Phase",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text="Completed", font=('Arial', FONT_LABEL),
                 bg=BG_ALT, fg='#81c784').pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both')

        self._row(body, "Completion Date", str(c.actual_date) if c.actual_date else "—")
        self._row(body, "Dose",            f"{c.dose_percent}%" if c.dose_percent else "—")
        self._row(body, "Dose Reason",     c.dose_reason or "—")
        self._row(body, "Notes",           c.notes or "—")

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(fill='x')

        close = tk.Label(btn_row, text="Close", font=('Arial', FONT_BODY),
                         bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        close.pack(side='right')
        close.bind('<Button-1>', lambda e: self.destroy())

        edit = tk.Label(btn_row, text="Edit", font=('Arial', FONT_BODY, 'bold'),
                        bg='#1a3a5c', fg='#90caf9', cursor='hand2', padx=14, pady=6)
        edit.pack(side='right', padx=(0, 12))
        edit.bind('<Button-1>', lambda e: self._open_edit())

        delete = tk.Label(btn_row, text="Delete", font=('Arial', FONT_BODY),
                          bg=BG, fg='#e05555', cursor='hand2', padx=10)
        delete.pack(side='left')
        delete.bind('<Button-1>', lambda e: self._on_delete())

    def _row(self, parent, label, value):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=4)
        tk.Label(row, text=f"{label}:", font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG_MUTED, width=16, anchor='w').pack(side='left')
        tk.Label(row, text=value, font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG, anchor='w').pack(side='left')

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.winfo_screenwidth()  // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"+{x}+{y}")

    def _open_edit(self):
        self.destroy()
        from views.dialogs.cycle_completion_dialog import CycleCompletionDialog
        CycleCompletionDialog(
            self.master, self.conn, self.patient_id,
            self.cycle.cycle_number, self.cycle, self.on_save
        )

    def _on_delete(self):
        confirmed = messagebox.askyesno(
            "Delete Cycle",
            f"Delete cycle {self.cycle.cycle_number} record?\n"
            f"This cannot be undone. The event is kept in the audit trail.",
            parent=self,
        )
        if not confirmed:
            return
        delete_cycle(self.conn, self.cycle.id)
        if self.on_save:
            self.on_save()
        self.destroy()
