import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED, FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER
from clinical.cardiotoxicity import compute_bsa
from config import get as get_config
from models import Cycle, get_cycles_by_patient
from services.cycles import create_cycle, update_cycle

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

        self._prior_height, self._prior_weight = self._fetch_prior_height_weight()
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

        # ── Anthracycline Dosing ──────────────────────────────────────────────
        tk.Frame(body, bg=SEPARATOR, height=1).grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=(4, 12))
        row += 1

        tk.Label(body, text="Anthracycline Dosing",
                 font=('Arial', FONT_LABEL, 'bold'), bg=BG, fg=FG_MUTED, anchor='w',
                 ).grid(row=row, column=0, columnspan=2, sticky='w', pady=(0, 10))
        row += 1

        # Height
        self._grid_label(body, "Height (cm)", row)
        prior_h_str = str(int(self._prior_height)) if self._prior_height else ''
        init_height = str(self.cycle.height_cm) if self.cycle and self.cycle.height_cm else prior_h_str
        self.height_var = tk.StringVar(value=init_height)
        tk.Entry(body, textvariable=self.height_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                 insertbackground=FG, relief='flat',
                 highlightbackground=SEPARATOR, highlightthickness=1,
                 ).grid(row=row, column=1, sticky='ew', pady=(0, 12))
        row += 1

        # Weight
        self._grid_label(body, "Weight (kg)", row)
        prior_w_str = str(self._prior_weight) if self._prior_weight else ''
        init_weight = str(self.cycle.weight_kg) if self.cycle and self.cycle.weight_kg else prior_w_str
        self.weight_var = tk.StringVar(value=init_weight)
        tk.Entry(body, textvariable=self.weight_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                 insertbackground=FG, relief='flat',
                 highlightbackground=SEPARATOR, highlightthickness=1,
                 ).grid(row=row, column=1, sticky='ew', pady=(0, 4))
        row += 1

        # Weight-change warning (shown when weight differs >threshold% from prior)
        self.weight_warning_label = tk.Label(
            body, text='', font=('Arial', FONT_HINT), bg=BG, fg='#FF9800', anchor='w',
        )
        self._weight_warning_row = row
        row += 1

        # Anthracycline agent
        self._grid_label(body, "Agent", row)
        agents = list(get_config().cardiotoxicity.equivalence_factors.keys())
        init_agent = self.cycle.anthracycline_agent if self.cycle and self.cycle.anthracycline_agent else ''
        self.agent_var = tk.StringVar(value=init_agent)
        ttk.Combobox(body, textvariable=self.agent_var, values=agents,
                     state='readonly', font=('Arial', FONT_BODY),
                     ).grid(row=row, column=1, sticky='ew', pady=(0, 12))
        row += 1

        # Dose mg total
        self._grid_label(body, "Dose (mg total)", row)
        init_dose_mg = str(self.cycle.dose_mg_total) if self.cycle and self.cycle.dose_mg_total else ''
        self.dose_mg_var = tk.StringVar(value=init_dose_mg)
        tk.Entry(body, textvariable=self.dose_mg_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                 insertbackground=FG, relief='flat',
                 highlightbackground=SEPARATOR, highlightthickness=1,
                 ).grid(row=row, column=1, sticky='ew', pady=(0, 12))
        row += 1

        # Live BSA / dose display
        self.bsa_display_label = tk.Label(
            body, text='', font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED, anchor='w',
        )
        self.bsa_display_label.grid(
            row=row, column=0, columnspan=2, sticky='w', pady=(0, 14))
        row += 1

        # Wire live-update traces
        self.height_var.trace_add('write', lambda *_: self._on_bsa_change())
        self.weight_var.trace_add('write', lambda *_: self._on_bsa_change())
        self.dose_mg_var.trace_add('write', lambda *_: self._on_bsa_change())
        self._on_bsa_change()

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
            'date':     self.date_var.get(),
            'dose':     self.dose_var.get(),
            'notes':    self.cycle.notes if self.cycle and self.cycle.notes else '',
            'height':   self.height_var.get(),
            'weight':   self.weight_var.get(),
            'agent':    self.agent_var.get(),
            'dose_mg':  self.dose_mg_var.get(),
        }



    def _fetch_prior_height_weight(self):
        """Return (height_cm, weight_kg) from the most recent prior cycle that has both.

        Searches cycles with cycle_number < self.cycle_number. Returns (None, None)
        if no prior cycle with measurements exists, or if the query fails gracefully.
        """
        try:
            all_cycles = get_cycles_by_patient(self.conn, self.patient_id)
        except Exception:
            return None, None
        prior = [
            c for c in all_cycles
            if c.cycle_number < self.cycle_number
            and c.height_cm is not None and c.weight_kg is not None
        ]
        if not prior:
            return None, None
        latest = max(prior, key=lambda c: c.cycle_number)
        return latest.height_cm, latest.weight_kg

    def _on_bsa_change(self, *_):
        """Recompute BSA and dose/m² from current field values and update display label."""
        try:
            h = float(self.height_var.get())
            w = float(self.weight_var.get())
            if h <= 0 or w <= 0:
                raise ValueError
            bsa = compute_bsa(h, w)
            text = f"BSA: {bsa:.2f} m²"
            dose_raw = self.dose_mg_var.get().strip()
            if dose_raw:
                dose_total = float(dose_raw)
                if dose_total > 0:
                    text += f"  ·  Dose: {dose_total / bsa:.1f} mg/m²"
            self.bsa_display_label.config(text=text, fg=FG)
        except (ValueError, ZeroDivisionError):
            self.bsa_display_label.config(text='', fg=FG_MUTED)
        self._check_weight_warning()

    def _check_weight_warning(self):
        """Show a warning label when the entered weight changed >threshold% from prior cycle."""
        if self._prior_weight is None:
            self.weight_warning_label.grid_remove()
            return
        try:
            w = float(self.weight_var.get())
            change_pct = abs(w - self._prior_weight) / self._prior_weight * 100
            threshold = get_config().cardiotoxicity.weight_change_warning_pct
            if change_pct > threshold:
                self.weight_warning_label.config(
                    text=f"⚠  Weight changed {change_pct:.1f}% from last cycle "
                         f"({self._prior_weight} kg)"
                )
                self.weight_warning_label.grid(
                    row=self._weight_warning_row, column=1,
                    sticky='w', pady=(0, 8),
                )
            else:
                self.weight_warning_label.grid_remove()
        except (ValueError, TypeError):
            self.weight_warning_label.grid_remove()

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
        date_changed   = self.date_var.get().strip() != self._initial['date']
        dose_changed   = self.dose_var.get() != self._initial['dose']
        notes_changed  = self.notes_text.get('1.0', 'end-1c') != self._initial['notes']
        height_changed = self.height_var.get().strip() != self._initial['height']
        weight_changed = self.weight_var.get().strip() != self._initial['weight']
        agent_changed  = self.agent_var.get() != self._initial['agent']
        dose_mg_changed = self.dose_mg_var.get().strip() != self._initial['dose_mg']
        return (date_changed or dose_changed or notes_changed
                or height_changed or weight_changed or agent_changed or dose_mg_changed)

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
            'date_completed':     self.date_var.get().strip(),
            'dose_selection':     dose_selection,
            'dose_percent_raw':   dose_percent_raw,
            'dose_reason':        dose_reason,
            'notes':              self.notes_text.get('1.0', 'end-1c').strip() or None,
            'height_cm':          self.height_var.get().strip(),
            'weight_kg':          self.weight_var.get().strip(),
            'anthracycline_agent': self.agent_var.get() or None,
            'dose_mg_total':      self.dose_mg_var.get().strip(),
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

        # ── Anthracycline Dosing fields (all optional; validated only when filled) ──
        height_raw = data['height_cm']
        if height_raw:
            try:
                h = float(height_raw)
                if not (50 <= h <= 300):
                    errors.append("Height must be between 50 and 300 cm.")
            except ValueError:
                errors.append("Height must be a number (cm).")

        weight_raw = data['weight_kg']
        if weight_raw:
            try:
                w = float(weight_raw)
                if not (1 <= w <= 400):
                    errors.append("Weight must be between 1 and 400 kg.")
            except ValueError:
                errors.append("Weight must be a number (kg).")

        dose_mg_raw = data['dose_mg_total']
        if dose_mg_raw:
            try:
                d = float(dose_mg_raw)
                if d <= 0:
                    errors.append("Dose (mg total) must be greater than 0.")
            except ValueError:
                errors.append("Dose (mg total) must be a number.")

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

        def _parse_float(s):
            s = (s or '').strip()
            return float(s) if s else None

        height_cm           = _parse_float(data['height_cm'])
        weight_kg           = _parse_float(data['weight_kg'])
        anthracycline_agent = data['anthracycline_agent']
        dose_mg_total       = _parse_float(data['dose_mg_total'])

        # ── Prospective cumulative dose check ──────────────────────────────────
        cumulative_override_action = None
        cumulative_override_reason = None
        if height_cm and weight_kg and anthracycline_agent and dose_mg_total:
            result = self._check_cumulative_block(
                height_cm, weight_kg, anthracycline_agent, dose_mg_total
            )
            if result is None:
                return   # User cancelled the override dialog
            cumulative_override_action, cumulative_override_reason = result

        # ── LVEF block (AC phase only) ──────────────────────────────────────────
        lvef_override_action = None
        lvef_override_reason = None
        if self.cycle_number <= 4:   # AC phase
            lvef_result = self._check_lvef_block()
            if lvef_result is None:
                return   # User cancelled
            lvef_override_action, lvef_override_reason = lvef_result

        try:
            if self.cycle is None:
                saved_cycle = create_cycle(self.conn, Cycle(
                    patient_id=self.patient_id,
                    cycle_number=self.cycle_number,
                    phase=phase,
                    actual_date=actual_date,
                    status='completed',
                    dose_percent=dose_percent,
                    dose_reason=dose_reason,
                    notes=notes,
                    height_cm=height_cm,
                    weight_kg=weight_kg,
                    anthracycline_agent=anthracycline_agent,
                    dose_mg_total=dose_mg_total,
                ))
            else:
                self.cycle.actual_date          = actual_date
                self.cycle.status               = 'completed'
                self.cycle.dose_percent         = dose_percent
                self.cycle.dose_reason          = dose_reason
                self.cycle.notes                = notes
                self.cycle.height_cm            = height_cm
                self.cycle.weight_kg            = weight_kg
                self.cycle.anthracycline_agent  = anthracycline_agent
                self.cycle.dose_mg_total        = dose_mg_total
                update_cycle(self.conn, self.cycle)
                saved_cycle = self.cycle
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

        # Write override audit rows for any blocks the user proceeded past.
        overrides = []
        if cumulative_override_action and cumulative_override_reason:
            overrides.append((cumulative_override_action, cumulative_override_reason))
        if lvef_override_action and lvef_override_reason:
            overrides.append((lvef_override_action, lvef_override_reason))

        if overrides:
            try:
                from services.audit import write_audit, current_actor
                for action, reason in overrides:
                    write_audit(
                        self.conn, 'cycle', saved_cycle.id, action,
                        after={'override_reason': reason},
                        actor=current_actor(),
                    )
                self.conn.commit()
            except Exception:
                log.exception('Failed to write override audit rows')

        self._prompt_symptom_entry(saved_cycle)

    # ── Symptom quick-entry prompt ─────────────────────────────────────────────

    def _prompt_symptom_entry(self, saved_cycle):
        """After a successful cycle save, offer symptom capture (skippable)."""
        from views.dialogs.symptom_quick_entry_dialog import SymptomQuickEntryDialog

        def _finish():
            if self.on_save:
                self.on_save()
            self.destroy()

        answer = messagebox.askyesno(
            'Symptom Check',
            f'Record symptoms for Cycle {saved_cycle.cycle_number}?\n\n'
            'Yes to enter grades now — No to skip.',
            parent=self,
        )
        if answer:
            self.withdraw()
            SymptomQuickEntryDialog(
                self.master,
                self.conn,
                patient_id=self.patient_id,
                cycle=saved_cycle,
                on_save=_finish,
                on_skip=_finish,
            )
        else:
            _finish()

    # ── Cumulative dose blocking ───────────────────────────────────────────────

    def _check_cumulative_block(self, height_cm, weight_kg, agent, dose_mg_total):
        """Compute prospective cumulative dose and apply configured blocking mode.

        Returns
        -------
        (action, reason) : tuple(str | None, str | None)
            action is 'override_red' | 'override_hard_stop' | None (no override).
            reason is the text the user entered, or None.
        None
            User cancelled — caller must abort the save.
        """
        from clinical.cardiotoxicity import (
            compute_bsa, cumulative_status, to_doxorubicin_equivalent,
        )
        from services.cycles import cumulative_dose
        from config import get as get_config

        cfg       = get_config().cardiotoxicity
        factors   = dict(cfg.equivalence_factors)
        thresholds = {
            'yellow':    cfg.cumulative_thresholds_mg_per_m2.yellow,
            'red':       cfg.cumulative_thresholds_mg_per_m2.red,
            'hard_stop': cfg.cumulative_thresholds_mg_per_m2.hard_stop,
        }

        try:
            bsa              = compute_bsa(height_cm, weight_kg)
            new_per_m2       = dose_mg_total / bsa
            new_dox_eq       = to_doxorubicin_equivalent(agent, new_per_m2, factors)
        except (ValueError, ZeroDivisionError):
            return (None, None)   # Can't compute — skip blocking check

        current_summary = cumulative_dose(self.conn, self.patient_id)

        # Subtract existing contribution of this cycle (edit path).
        old_dox_eq = 0.0
        if self.cycle and self.cycle.anthracycline_agent and self.cycle.dose_mg_per_m2:
            try:
                old_dox_eq = to_doxorubicin_equivalent(
                    self.cycle.anthracycline_agent,
                    self.cycle.dose_mg_per_m2,
                    factors,
                )
            except ValueError:
                pass

        prospective = current_summary.total_mg_per_m2 - old_dox_eq + new_dox_eq
        status      = cumulative_status(prospective, thresholds)
        modes       = cfg.blocking_modes

        if status == 'hard_stop' and modes.cumulative_hard_stop != 'advisory':
            return self._hard_stop_dialog(prospective, thresholds['hard_stop'])
        if status in ('red', 'hard_stop') and modes.cumulative_red == 'soft_block':
            return self._soft_block_dialog(prospective, thresholds['red'], status)
        if status in ('yellow', 'red', 'hard_stop') and modes.cumulative_yellow == 'advisory':
            # Advisory: no blocking, just informational (shown via badge already)
            pass

        return (None, None)   # No blocking required

    def _check_lvef_block(self):
        """Check the latest LVEF for this patient and apply configured blocking mode.

        Only called for AC phase cycles (cycle_number <= 4). Returns the same
        contract as _check_cumulative_block: (action, reason) | None (cancel).
        """
        from clinical.cardiotoxicity import lvef_status
        from services.lvef import get_baseline_lvef, list_lvef
        from config import get as get_config

        assessments = list_lvef(self.conn, self.patient_id)
        if not assessments:
            return (None, None)   # No LVEF on record — nothing to check

        latest       = assessments[0]
        baseline     = get_baseline_lvef(self.conn, self.patient_id)
        baseline_pct = baseline.lvef_percent if baseline else None

        cfg         = get_config().cardiotoxicity
        lvef_cfg    = cfg.lvef.model_dump()
        status_info = lvef_status(latest.lvef_percent, baseline_pct, lvef_cfg)

        if status_info['status'] != 'hold':
            return (None, None)   # ok or review — no blocking in V2

        modes    = cfg.blocking_modes
        is_hard  = (modes.lvef_absolute == 'hard_block'
                    or modes.lvef_delta == 'hard_block')
        is_soft  = (modes.lvef_absolute == 'soft_block'
                    or modes.lvef_delta == 'soft_block')

        if is_hard:
            return self._lvef_block_dialog(status_info['reason'], hard=True)
        if is_soft:
            return self._lvef_block_dialog(status_info['reason'], hard=False)
        return (None, None)   # Both modes advisory

    def _lvef_block_dialog(self, lvef_reason: str, *, hard: bool):
        """Confirmation dialog for an LVEF hold state.

        hard=False → soft block: requires any non-empty reason.
        hard=True  → hard block: requires ≥20-char attending reason.
        Returns ('override_lvef', reason) or None on cancel.
        """
        min_chars = 20 if hard else 1
        accent    = '#B71C1C' if hard else '#F44336'
        btn_bg    = '#7B1FA2' if hard else '#B71C1C'
        btn_text  = 'Attending Override — Proceed' if hard else 'Proceed'
        title     = 'LVEF — Hard Limit' if hard else 'LVEF Hold Warning'

        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)

        result = [None]

        tk.Frame(dialog, bg=accent, height=6 if hard else 4).pack(fill='x')

        body = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        body.pack(fill='both')

        if hard:
            tk.Label(body, text='⛔  LVEF HARD STOP',
                     font=('Arial', FONT_HEADER, 'bold'),
                     bg=BG, fg='#F44336', anchor='w').pack(anchor='w', pady=(0, 8))

        tk.Label(body, text=lvef_reason,
                 font=('Arial', FONT_LABEL), bg=BG, fg='#F44336',
                 justify='left', anchor='w').pack(anchor='w', pady=(0, 14))

        prompt = ('Attending override reason (minimum 20 characters):'
                  if hard else 'Reason for proceeding (required):')
        tk.Label(body, text=prompt,
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED,
                 anchor='w').pack(anchor='w')

        reason_var = tk.StringVar()

        if hard:
            char_lbl = tk.Label(body, text='0 / 20 min',
                                font=('Arial', FONT_HINT), bg=BG,
                                fg=FG_MUTED, anchor='e')
            char_lbl.pack(anchor='e')

            def _on_key(*_):
                n = len(reason_var.get().strip())
                char_lbl.config(text=f'{n} / 20 min',
                                fg='#4CAF50' if n >= 20 else FG_MUTED)
            reason_var.trace_add('write', _on_key)

        reason_entry = tk.Entry(body, textvariable=reason_var,
                                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                                insertbackground=FG, relief='flat',
                                highlightbackground=SEPARATOR, highlightthickness=1)
        reason_entry.pack(fill='x', pady=(4, 14))

        err_lbl = tk.Label(body, text='', font=('Arial', FONT_HINT),
                           bg=BG, fg='#F44336', anchor='w')
        err_lbl.pack(anchor='w')

        tk.Frame(dialog, bg=SEPARATOR, height=1).pack(fill='x')
        btn_row = tk.Frame(dialog, bg=BG, padx=24, pady=14)
        btn_row.pack(fill='x')

        def _cancel():
            result[0] = None
            dialog.destroy()

        def _proceed():
            reason = reason_var.get().strip()
            if len(reason) < min_chars:
                msg = (f'Override reason must be at least {min_chars} characters.'
                       if hard else 'A reason is required to proceed.')
                err_lbl.config(text=msg)
                return
            result[0] = ('override_lvef', reason)
            dialog.destroy()

        cancel_btn = tk.Label(btn_row, text='Cancel',
                              font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED,
                              cursor='hand2', padx=10)
        cancel_btn.pack(side='right')
        cancel_btn.bind('<Button-1>', lambda e: _cancel())

        proceed_btn = tk.Label(btn_row, text=btn_text,
                               font=('Arial', FONT_BODY, 'bold'),
                               bg=btn_bg, fg='#FFFFFF',
                               cursor='hand2', padx=14, pady=6)
        proceed_btn.pack(side='right', padx=(0, 12))
        proceed_btn.bind('<Button-1>', lambda e: _proceed())

        dialog.update_idletasks()
        w, h = dialog.winfo_width(), dialog.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width()  - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        dialog.geometry(f'+{x}+{y}')
        reason_entry.focus_set()
        dialog.wait_window()
        return result[0]

    def _soft_block_dialog(self, prospective_total, threshold, status):
        """Confirmation dialog for red/soft-block state. Returns (action, reason) or None."""
        dialog = tk.Toplevel(self)
        dialog.title('Cumulative Dose Warning')
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)

        result = [None]   # mutable container for return value

        tk.Frame(dialog, bg='#F44336', height=4).pack(fill='x')

        body = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        body.pack(fill='both')

        tk.Label(body,
                 text=f"This cycle would bring the cumulative dose to "
                      f"{prospective_total:.1f} mg/m²,\n"
                      f"above the {threshold:.0f} mg/m² hold threshold.",
                 font=('Arial', FONT_LABEL), bg=BG, fg='#F44336',
                 justify='left', anchor='w').pack(anchor='w', pady=(0, 14))

        tk.Label(body, text="Reason for proceeding (required):",
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED,
                 anchor='w').pack(anchor='w')
        reason_var = tk.StringVar()
        reason_entry = tk.Entry(body, textvariable=reason_var,
                                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                                insertbackground=FG, relief='flat',
                                highlightbackground=SEPARATOR, highlightthickness=1)
        reason_entry.pack(fill='x', pady=(4, 14))

        err_lbl = tk.Label(body, text='', font=('Arial', FONT_HINT),
                           bg=BG, fg='#F44336', anchor='w')
        err_lbl.pack(anchor='w')

        tk.Frame(dialog, bg=SEPARATOR, height=1).pack(fill='x')
        btn_row = tk.Frame(dialog, bg=BG, padx=24, pady=14)
        btn_row.pack(fill='x')

        def _cancel():
            result[0] = None
            dialog.destroy()

        def _proceed():
            reason = reason_var.get().strip()
            if not reason:
                err_lbl.config(text='A reason is required to proceed.')
                return
            result[0] = ('override_red', reason)
            dialog.destroy()

        cancel_btn = tk.Label(btn_row, text='Cancel',
                              font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED,
                              cursor='hand2', padx=10)
        cancel_btn.pack(side='right')
        cancel_btn.bind('<Button-1>', lambda e: _cancel())

        proceed_btn = tk.Label(btn_row, text='Proceed',
                               font=('Arial', FONT_BODY, 'bold'),
                               bg='#B71C1C', fg='#FFFFFF',
                               cursor='hand2', padx=14, pady=6)
        proceed_btn.pack(side='right', padx=(0, 12))
        proceed_btn.bind('<Button-1>', lambda e: _proceed())

        dialog.update_idletasks()
        w, h = dialog.winfo_width(), dialog.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width()  - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        dialog.geometry(f'+{x}+{y}')
        reason_entry.focus_set()
        dialog.wait_window()
        return result[0]

    def _hard_stop_dialog(self, prospective_total, hard_stop_limit):
        """Hard-stop override dialog requiring attending physician reason (≥20 chars)."""
        dialog = tk.Toplevel(self)
        dialog.title('Cumulative Dose — Hard Limit')
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self)

        result = [None]

        tk.Frame(dialog, bg='#B71C1C', height=6).pack(fill='x')

        body = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        body.pack(fill='both')

        tk.Label(body,
                 text=f"⛔  HARD STOP",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg='#F44336',
                 anchor='w').pack(anchor='w', pady=(0, 8))
        tk.Label(body,
                 text=f"This cycle would bring the cumulative dose to "
                      f"{prospective_total:.1f} mg/m²,\n"
                      f"which exceeds the {hard_stop_limit:.0f} mg/m² hard-stop limit.\n\n"
                      f"An attending physician override is required to proceed.",
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG,
                 justify='left', anchor='w').pack(anchor='w', pady=(0, 14))

        tk.Label(body, text="Attending override reason (minimum 20 characters):",
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED,
                 anchor='w').pack(anchor='w')
        reason_var = tk.StringVar()
        char_lbl = tk.Label(body, text='0 / 20 min',
                            font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED, anchor='e')
        char_lbl.pack(anchor='e')
        reason_entry = tk.Entry(body, textvariable=reason_var,
                                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                                insertbackground=FG, relief='flat',
                                highlightbackground=SEPARATOR, highlightthickness=1)
        reason_entry.pack(fill='x', pady=(2, 14))

        def _on_reason_key(*_):
            n = len(reason_var.get().strip())
            char_lbl.config(text=f'{n} / 20 min',
                            fg='#4CAF50' if n >= 20 else FG_MUTED)
        reason_var.trace_add('write', _on_reason_key)

        err_lbl = tk.Label(body, text='', font=('Arial', FONT_HINT),
                           bg=BG, fg='#F44336', anchor='w')
        err_lbl.pack(anchor='w')

        tk.Frame(dialog, bg=SEPARATOR, height=1).pack(fill='x')
        btn_row = tk.Frame(dialog, bg=BG, padx=24, pady=14)
        btn_row.pack(fill='x')

        def _cancel():
            result[0] = None
            dialog.destroy()

        def _override():
            reason = reason_var.get().strip()
            if len(reason) < 20:
                err_lbl.config(text='Override reason must be at least 20 characters.')
                return
            result[0] = ('override_hard_stop', reason)
            dialog.destroy()

        cancel_btn = tk.Label(btn_row, text='Cancel',
                              font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED,
                              cursor='hand2', padx=10)
        cancel_btn.pack(side='right')
        cancel_btn.bind('<Button-1>', lambda e: _cancel())

        override_btn = tk.Label(btn_row, text='Attending Override — Proceed',
                                font=('Arial', FONT_BODY, 'bold'),
                                bg='#7B1FA2', fg='#FFFFFF',
                                cursor='hand2', padx=14, pady=6)
        override_btn.pack(side='right', padx=(0, 12))
        override_btn.bind('<Button-1>', lambda e: _override())

        dialog.update_idletasks()
        w, h = dialog.winfo_width(), dialog.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width()  - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        dialog.geometry(f'+{x}+{y}')
        reason_entry.focus_set()
        dialog.wait_window()
        return result[0]
