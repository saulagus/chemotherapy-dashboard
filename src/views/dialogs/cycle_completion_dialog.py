import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED, FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER
from models import Cycle, add_cycle, update_cycle

log = logging.getLogger(__name__)

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
    start_date   : date | None      — treatment start date used to validate completion date
    """

    def __init__(self, parent, conn, patient_id, cycle_number,
                 cycle=None, on_save=None, start_date=None):
        super().__init__(parent)
        self.conn         = conn
        self.patient_id   = patient_id
        self.cycle_number = cycle_number
        self.cycle        = cycle
        self.on_save      = on_save
        self.start_date   = start_date

        self.title(f"Complete Cycle {cycle_number}")
        self.configure(bg=BG)
        self.resizable(False, True)
        self.grab_set()

        self._build_ui()
        self._center()
        self.minsize(480, 520)
        self.protocol('WM_DELETE_WINDOW', self._confirm_cancel)
        self.bind('<Return>', lambda e: self._on_save())
        self.bind('<Escape>', lambda e: self._confirm_cancel())
        self.date_entry.focus_set()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        phase = 'AC' if self.cycle_number <= 4 else 'T'

        # Header — cycle number and phase (read-only display)
        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        header.pack(fill='x')
        tk.Label(header, text=f"Cycle {self.cycle_number} — {phase} Phase",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text="Record completion details below.",
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w', pady=(4, 0))

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons pinned to bottom before body so expand=True doesn't push them off
        btn_sep = tk.Frame(self, bg=SEPARATOR, height=1)
        btn_sep.pack(side='bottom', fill='x')
        btn_row = tk.Frame(self, bg=BG, padx=24, pady=16)
        btn_row.pack(side='bottom', fill='x')

        cancel = tk.Label(btn_row, text="Cancel", font=('Arial', FONT_BODY),
                          bg=BG, fg=FG_MUTED, cursor='hand2', padx=10)
        cancel.pack(side='right')
        cancel.bind('<Button-1>', lambda e: self._confirm_cancel())

        save = tk.Label(btn_row, text="Mark Complete", font=('Arial', FONT_BODY, 'bold'),
                        bg='#388E3C', fg='#FFFFFF', cursor='hand2', padx=14, pady=6)
        save.pack(side='right', padx=(0, 12))
        save.bind('<Button-1>', lambda e: self._on_save())

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=0, minsize=180)  # Label column
        body.columnconfigure(1, weight=1)               # Input column

        row = 0  # Grid row counter

        # ── Completion date ──────────────────────────────────────────────────
        self._grid_label(body, "Completion Date", row)
        self.date_var = tk.StringVar(value=str(date.today()))
        if self.cycle and self.cycle.actual_date:
            self.date_var.set(str(self.cycle.actual_date))
        self.date_entry = tk.Entry(body, textvariable=self.date_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                 insertbackground=FG, relief='flat',
                 highlightbackground=SEPARATOR, highlightthickness=1)
        self.date_entry.grid(row=row, column=1, sticky='ew', pady=(0, 12))
        row += 1

        # Format hint
        tk.Label(body, text="YYYY-MM-DD", font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 ).grid(row=row, column=1, sticky='w', pady=(0, 6))
        row += 1

        # ── Dose percentage ──────────────────────────────────────────────────
        DOSE_OPTIONS = ['100% (Full dose)', '85%', '75%', '50%', 'Custom']
        self._grid_label(body, "Dose Given", row)

        self.dose_var = tk.StringVar(value='100% (Full dose)')
        if self.cycle and self.cycle.dose_percent is not None:
            pct = int(self.cycle.dose_percent)
            if pct == 100:   self.dose_var.set('100% (Full dose)')
            elif pct in (85, 75, 50): self.dose_var.set(f'{pct}%')
            else:            self.dose_var.set('Custom')

        self.dose_combo = ttk.Combobox(body, textvariable=self.dose_var,
                                       values=DOSE_OPTIONS, state='readonly',
                                       font=('Arial', FONT_BODY))
        self.dose_combo.grid(row=row, column=1, sticky='ew', pady=(0, 12))
        self.dose_combo.bind('<<ComboboxSelected>>', lambda e: self._on_dose_change())
        row += 1

        # ── Dose reduction warning (hidden until dose < 100%) ────────────────
        # Starts hidden; _on_dose_change shows it whenever a reduced dose is selected.
        self.dose_warning_label = tk.Label(
            body,
            text="⚠  Dose reduction will be recorded",
            font=('Arial', FONT_LABEL), bg=BG, fg='#FF9800', anchor='w',
        )
        self._warning_row = row
        row += 1

        # ── Custom dose entry (hidden until Custom selected) ─────────────────
        self.custom_dose_frame = tk.Frame(body, bg=BG)
        self.custom_dose_frame.columnconfigure(0, weight=1)
        self._grid_label(self.custom_dose_frame, "Custom Dose (%)", 0)
        self.custom_dose_var = tk.StringVar(value='')
        if self.cycle and self.cycle.dose_percent and int(self.cycle.dose_percent) not in (100, 85, 75, 50):
            self.custom_dose_var.set(str(int(self.cycle.dose_percent)))
        self.custom_dose_entry = tk.Entry(self.custom_dose_frame, textvariable=self.custom_dose_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG, insertbackground=FG,
                 relief='flat', highlightbackground=SEPARATOR, highlightthickness=1,
                 width=8)
        self.custom_dose_entry.grid(row=0, column=1, sticky='w', pady=(0, 12))
        self.custom_dose_frame.columnconfigure(1, weight=0)
        # Store row index so _on_dose_change can grid/unGrid this frame later.
        # The frame is NOT gridded here — it starts hidden and is shown only
        # when the user selects 'Custom' from the dose dropdown.
        self._custom_dose_row = row
        row += 1

        # ── Dose reason (hidden until dose < 100%) ───────────────────────────
        self.reason_frame = tk.Frame(body, bg=BG)
        self.reason_frame.columnconfigure(1, weight=1)
        saved_reason    = self.cycle.dose_reason if self.cycle and self.cycle.dose_reason else ''
        initial_reason  = saved_reason if saved_reason in DOSE_REASONS else ('Other' if saved_reason else DOSE_REASONS[0])
        self.reason_var = tk.StringVar(value=initial_reason)

        self.reason_label = tk.Label(self.reason_frame, text="Dose Reason",
                                     font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED, anchor='w')
        self.reason_label.grid(row=0, column=0, sticky='nw', padx=(0, 16), pady=(0, 12))
        self.reason_combo = ttk.Combobox(self.reason_frame, textvariable=self.reason_var,
                                         values=DOSE_REASONS, state='readonly', font=('Arial', FONT_BODY))
        self.reason_combo.grid(row=0, column=1, sticky='ew', pady=(0, 6))
        self.reason_combo.bind('<<ComboboxSelected>>', lambda e: self._on_reason_change())

        # "Other" free text sub-row
        self.other_reason_frame = tk.Frame(self.reason_frame, bg=BG)
        self.other_reason_frame.columnconfigure(1, weight=1)
        self._grid_label(self.other_reason_frame, "Please specify", 0)
        self.other_reason_var = tk.StringVar(value=saved_reason if saved_reason not in DOSE_REASONS else '')
        self.other_reason_entry = tk.Entry(self.other_reason_frame, textvariable=self.other_reason_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG, insertbackground=FG,
                 relief='flat', highlightbackground=SEPARATOR, highlightthickness=1)
        self.other_reason_entry.grid(row=0, column=1, sticky='ew', pady=(0, 8))
        # Same deferred-grid pattern as custom_dose_frame above — starts hidden,
        # shown by _on_dose_change whenever a reduced dose is selected.
        self._reason_row = row
        row += 1

        # ── Notes ────────────────────────────────────────────────────────────
        self._grid_label(body, "Notes (optional)", row)
        self.char_count_label = tk.Label(body, text="0 / 500",
                                         font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED, anchor='e')
        self.char_count_label.grid(row=row, column=1, sticky='e')
        row += 1

        self.notes_text = tk.Text(body, height=4, font=('Arial', FONT_BODY),
                                  bg=BG_ALT, fg=FG, insertbackground=FG,
                                  relief='flat', wrap='word',
                                  highlightbackground=SEPARATOR, highlightthickness=1)
        self.notes_text.grid(row=row, column=0, columnspan=2, sticky='ew', pady=(4, 0))
        if self.cycle and self.cycle.notes:
            self.notes_text.insert('1.0', self.cycle.notes)
        self.notes_text.bind('<KeyRelease>', self._on_notes_change)
        self._on_notes_change()
        row += 1

        # Trigger show/hide on initial values
        self._on_dose_change()
        self._on_reason_change()

        # Snapshot field values at open time so _has_changes() can tell whether
        # the user modified anything — used to decide if a cancel confirmation
        # dialog is needed.
        self._initial = {
            'date':  self.date_var.get(),
            'dose':  self.dose_var.get(),
            'notes': self.cycle.notes if self.cycle and self.cycle.notes else '',
        }



    def _grid_label(self, parent, text, row):
        """Grid-based label for column 0 of a form row."""
        tk.Label(parent, text=text, font=('Arial', FONT_LABEL),
                 bg=BG, fg=FG_MUTED, anchor='w',
                 ).grid(row=row, column=0, sticky='nw', padx=(0, 16), pady=(0, 12))

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
            self.other_reason_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 8))
        else:
            self.other_reason_frame.grid_remove()

    def _on_dose_change(self):
        """Show/hide custom dose entry and reason dropdown based on selection."""
        selected   = self.dose_var.get()
        is_custom  = selected == 'Custom'
        is_reduced = selected != '100% (Full dose)'

        if is_custom:
            self.custom_dose_frame.grid(row=self._custom_dose_row, column=0,
                                        columnspan=2, sticky='ew', pady=(0, 8))
        else:
            self.custom_dose_frame.grid_remove()

        if is_reduced:
            self.dose_warning_label.grid(
                row=self._warning_row, column=0, columnspan=2,
                sticky='w', pady=(0, 8),
            )
            # Tint the reason frame background to draw attention to the field.
            self.reason_frame.configure(bg='#1f1a0d')
            self.reason_label.config(text="Dose Reason *", fg='#e05555', bg='#1f1a0d')
            self.reason_frame.grid(row=self._reason_row, column=0,
                                   columnspan=2, sticky='ew', pady=(0, 12))
        else:
            self.dose_warning_label.grid_remove()
            self.reason_frame.configure(bg=BG)
            self.reason_label.config(text="Dose Reason", fg=FG_MUTED, bg=BG)
            self.reason_frame.grid_remove()

    # ── Close behavior ────────────────────────────────────────────────────────

    def _has_changes(self) -> bool:
        """Return True if the user has modified any field from its initial value."""
        date_changed = self.date_var.get().strip() != self._initial['date']
        dose_changed = self.dose_var.get() != self._initial['dose']
        notes_changed = self.notes_text.get('1.0', 'end-1c') != self._initial['notes']
        return date_changed or dose_changed or notes_changed

    def _confirm_cancel(self):
        """Close dialog, asking for confirmation only if the form has been modified."""
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
        """Return raw field values as a dictionary — no validation applied.

        Keys
        ----
        date_completed  : str         — raw text from the date entry (YYYY-MM-DD)
        dose_selection  : str         — dropdown value e.g. '85%', 'Custom', '100% (Full dose)'
        dose_percent_raw: str | None  — custom dose text when selection is 'Custom', else None
        dose_reason     : str | None  — selected/typed reason; None when full dose chosen
        notes           : str | None  — trimmed notes text, or None if empty
        """
        dose_selection = self.dose_var.get()

        # Collect the free-text dose only when 'Custom' is active.
        dose_percent_raw = (
            self.custom_dose_var.get().strip() if dose_selection == 'Custom' else None
        )

        # Collect reason only when a reduced dose is selected; resolve 'Other' to its text.
        if dose_selection == '100% (Full dose)':
            dose_reason = None
        elif self.reason_var.get() == 'Other':
            dose_reason = self.other_reason_var.get().strip() or None
        else:
            dose_reason = self.reason_var.get()

        return {
            'date_completed':   self.date_var.get().strip(),
            'dose_selection':   dose_selection,
            'dose_percent_raw': dose_percent_raw,
            'dose_reason':      dose_reason,
            'notes':            self.notes_text.get('1.0', 'end-1c').strip() or None,
        }

    def validate(self) -> list[str]:
        """Validate all form fields and return a list of error messages.

        Returns an empty list when the form is valid.
        Errors are returned in field order (date → dose → reason) so the
        first one can be shown as an inline error without overwhelming the user.
        """
        errors = []
        data   = self.get_form_data()

        # ── Date ──────────────────────────────────────────────────────────────
        date_str = data['date_completed']
        if not date_str:
            errors.append("Completion date is required.")
        else:
            try:
                actual_date = date.fromisoformat(date_str)
            except ValueError:
                errors.append("Invalid date — use YYYY-MM-DD format.")
                actual_date = None

            if actual_date is not None:
                if actual_date > date.today():
                    errors.append("Completion date cannot be in the future.")
                if self.start_date and actual_date < self.start_date:
                    errors.append(
                        f"Completion date cannot be before treatment start "
                        f"({self.start_date})."
                    )

        # ── Dose ──────────────────────────────────────────────────────────────
        if data['dose_selection'] == 'Custom':
            # Strip a trailing % the user may have typed (e.g. "85%") before parsing.
            raw = (data['dose_percent_raw'] or '').replace('%', '').strip()
            try:
                dose_val = float(raw)
                if not (1 <= dose_val <= 100):
                    raise ValueError
            except ValueError:
                errors.append("Custom dose must be a number between 1 and 100.")

        # ── Reason ────────────────────────────────────────────────────────────
        # Reason is only required when the actual dose is below 100%.
        # For preset selections the dropdown value implies the dose; for Custom
        # we parse the numeric value (defaulting to 100 if unparseable — the
        # dose error above already covers that case).
        if data['dose_selection'] == 'Custom':
            try:
                raw = (data['dose_percent_raw'] or '').replace('%', '').strip()
                is_reduced = float(raw) < 100
            except ValueError:
                is_reduced = False  # Dose error already reported; skip reason check.
        else:
            is_reduced = data['dose_selection'] != '100% (Full dose)'

        if is_reduced:
            if self.reason_var.get() == 'Other' and not data['dose_reason']:
                errors.append("Please describe the reason in the text field below.")
            elif not data['dose_reason']:
                errors.append("Please select a reason for the dose modification.")

        return errors

    def _focus_first_error(self, errors: list[str]) -> None:
        """Move keyboard focus to the field that produced the first error."""
        first = errors[0] if errors else ''
        if 'date' in first.lower():
            self.date_entry.focus_set()
            self.date_entry.select_range(0, 'end')
        elif 'dose' in first.lower():
            self.custom_dose_entry.focus_set()
            self.custom_dose_entry.select_range(0, 'end')
        elif 'reason' in first.lower() or 'describe' in first.lower():
            if self.reason_var.get() == 'Other':
                self.other_reason_entry.focus_set()
            else:
                self.reason_combo.focus_set()

    def _on_save(self):
        errors = self.validate()
        if errors:
            messagebox.showerror(
                'Please fix the following errors',
                '\n'.join(f'• {e}' for e in errors),
                parent=self,
            )
            self._focus_first_error(errors)
            return

        data = self.get_form_data()
        actual_date  = date.fromisoformat(data['date_completed'])
        dose_reason  = data['dose_reason']
        notes        = data['notes']
        phase        = 'AC' if self.cycle_number <= 4 else 'T'

        if data['dose_selection'] == 'Custom':
            dose_percent = float(data['dose_percent_raw'].replace('%', '').strip())
        else:
            dose_percent = float(
                data['dose_selection'].replace('% (Full dose)', '').replace('%', '')
            )

        try:
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
        except Exception as e:
            log.exception(
                'Failed to save cycle %d for patient_id=%d',
                self.cycle_number, self.patient_id,
            )
            messagebox.showerror(
                'Save Failed',
                f'Could not save cycle data:\n{e}',
                parent=self,
            )
            return

        if self.on_save:
            self.on_save()
        self.destroy()
