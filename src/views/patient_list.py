import tkinter as tk
from tkinter import ttk, messagebox
from models import Patient, get_cycles_by_patient, get_patient_by_db_id
from services.cycles import cumulative_dose
from services.patients import soft_delete_patient
from utils import show_info, BG, BG_ALT, BG_ROW_ODD, SEPARATOR, FG, FG_MUTED, FONT_BODY, FONT_HINT, FONT_TITLE

_RISK_TEXT = {
    'green':     'Green',
    'yellow':    '⚠ Yellow',
    'red':       '⛔ Red',
    'hard_stop': '⛔ STOP',
}
_RISK_FG = {
    'green':     '#4CAF50',
    'yellow':    '#FFC107',
    'red':       '#F44336',
    'hard_stop': '#F44336',
}


class PatientListView(tk.Frame):
    """Main screen — shows all patients and allows navigating to their dashboard."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self._patient_summaries = {}   # patient.id → CumulativeSummary
        self._tooltip_win       = None # active tooltip Toplevel or None
        self._build_ui()
        self._load_patients()

    def _build_ui(self):
        self.configure(bg=BG)

        # Header bar.
        header = tk.Frame(self, bg=BG, pady=14, padx=24)
        header.pack(fill='x')

        tk.Label(header, text="AC-T Chemotherapy Dashboard",
                 font=('Arial', FONT_TITLE), bg=BG, fg=FG).pack(side='left')

        add_btn = tk.Label(header, text="+ Add Patient",
                           font=('Arial', FONT_BODY), bg=BG, fg=FG,
                           cursor='hand2', padx=8, pady=4)
        add_btn.pack(side='right')
        add_btn.bind('<Button-1>', lambda e: self._on_add_patient())

        edit_btn = tk.Label(header, text="Edit Patient",
                            font=('Arial', FONT_BODY), bg=BG, fg=FG,
                            cursor='hand2', padx=8, pady=4)
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e: self._on_edit_patient())

        remove_btn = tk.Label(header, text="- Remove Patient",
                              font=('Arial', FONT_BODY), bg=BG, fg='#e05555',
                              cursor='hand2', padx=8, pady=4)
        remove_btn.pack(side='right')
        remove_btn.bind('<Button-1>', lambda e: self._on_remove_patient())

        # Thin separator line below the header.
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Content area.
        content = tk.Frame(self, bg=BG, padx=16, pady=8)
        content.pack(fill='both', expand=True)

        # Treeview + vertical scrollbar in a shared frame.
        tree_frame = tk.Frame(content, bg=BG)
        tree_frame.pack(fill='both', expand=True, pady=(8, 0))

        self._scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        self._scrollbar.grid(row=0, column=1, sticky='ns')

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('id', 'name', 'current_cycle', 'protocol', 'age', 'diagnosis_date', 'risk'),
            show='headings',
            height=20,
            yscrollcommand=self._on_yscroll,
        )
        self._scrollbar.config(command=self.tree.yview)

        # Column headings.
        self.tree.heading('id',             text='Patient ID')
        self.tree.heading('name',           text='Name')
        self.tree.heading('current_cycle',  text='Current Cycle')
        self.tree.heading('protocol',       text='Protocol')
        self.tree.heading('age',            text='Age')
        self.tree.heading('diagnosis_date', text='Diagnosis Date')
        self.tree.heading('risk',           text='Dose Risk')

        # Column widths and alignment.
        self.tree.column('id',             width=130, anchor='center', stretch=False)
        self.tree.column('name',           width=200, anchor='w')
        self.tree.column('current_cycle',  width=140, anchor='center', stretch=False)
        self.tree.column('protocol',       width=200, anchor='center', stretch=False)
        self.tree.column('age',            width=80,  anchor='center', stretch=False)
        self.tree.column('diagnosis_date', width=140, anchor='center', stretch=False)
        self.tree.column('risk',           width=90,  anchor='center', stretch=False)

        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Hide scrollbar initially — shown only when content overflows.
        self._scrollbar.grid_remove()
        tree_frame.bind('<Configure>', lambda e: self.after(0, self._sync_scrollbar))

        # Alternating row stripe colours.
        self.tree.tag_configure('even', background=BG_ALT)
        self.tree.tag_configure('odd',  background=BG_ROW_ODD)
        self.tree.tag_configure('hover', background='#2a3152')

        # Dose-risk foreground tags — applied alongside stripe tags.
        self.tree.tag_configure('dose_green',     foreground='#4CAF50')
        self.tree.tag_configure('dose_yellow',    foreground='#FFC107')
        self.tree.tag_configure('dose_red',       foreground='#F44336')
        self.tree.tag_configure('dose_hard_stop', foreground='#F44336')

        # Double-click to open dashboard; Motion/Leave for hover effect + tooltip.
        self.tree.bind('<Double-1>', self._on_row_double_click)
        self.tree.bind('<Motion>', self._on_row_hover)
        self.tree.bind('<Leave>', self._on_row_leave)
        self._hovered_row  = None
        self._row_stripes  = {}   # row_id -> 'even' | 'odd'
        self._row_dose_tags = {}  # row_id -> 'dose_green' | 'dose_yellow' | ...

        # Empty-state label overlaid on the tree when no patients exist.
        self.empty_label = tk.Label(
            tree_frame,
            text="No patients found.\nUse 'Add Patient' to create one.",
            font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED, justify='center',
        )

    def _on_yscroll(self, first: str, last: str) -> None:
        """Update scrollbar position and show/hide based on content overflow."""
        self._scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid()

    def _sync_scrollbar(self) -> None:
        """Force scrollbar visibility check after layout has settled."""
        first, last = self.tree.yview()
        self._on_yscroll(str(first), str(last))

    def _on_row_hover(self, event):
        """Highlight the row under the cursor and show dose tooltip over Risk column."""
        row = self.tree.identify_row(event.y)
        if row != self._hovered_row:
            # Restore previous row — dose_tag + stripe (no hover).
            if self._hovered_row and self.tree.exists(self._hovered_row):
                self._restore_row_tags(self._hovered_row)
            # Apply hover background; dose_tag foreground carries through.
            if row:
                dose_tag = self._row_dose_tags.get(row, 'dose_green')
                self.tree.item(row, tags=(row, dose_tag, 'hover'))
            self._hovered_row = row or None

        # Tooltip — show when hovering over the Risk column.
        col = self.tree.identify_column(event.x)
        if row and col == '#7':   # '#7' is the 7th column (risk)
            self._show_risk_tooltip(event, row)
        else:
            self._hide_tooltip()

    def _on_row_leave(self, event):
        """Remove hover highlight and tooltip when the mouse leaves the treeview."""
        if self._hovered_row and self.tree.exists(self._hovered_row):
            self._restore_row_tags(self._hovered_row)
        self._hovered_row = None
        self._hide_tooltip()

    def _restore_row_tags(self, row):
        """Re-apply dose_tag + stripe tags after hover is removed."""
        stripe   = self._row_stripes.get(row, 'even')
        dose_tag = self._row_dose_tags.get(row, 'dose_green')
        self.tree.item(row, tags=(row, dose_tag, stripe))

    def _show_risk_tooltip(self, event, row):
        """Display a tooltip with detailed cumulative dose info for the hovered row."""
        self._hide_tooltip()
        summary = self._patient_summaries.get(row)
        if summary is None:
            return
        total = summary.total_mg_per_m2
        from config import get as get_config
        thresholds = get_config().cardiotoxicity.cumulative_thresholds_mg_per_m2
        if summary.status == 'green':
            headroom = thresholds.yellow - total
            detail   = f"{headroom:.1f} mg/m² to advisory threshold"
        elif summary.status == 'yellow':
            headroom = thresholds.red - total
            detail   = f"{headroom:.1f} mg/m² to hold threshold"
        elif summary.status == 'red':
            headroom = thresholds.hard_stop - total
            detail   = f"{headroom:.1f} mg/m² to hard stop"
        else:
            detail = "Exceeds hard-stop limit"

        tip_text = f"{total:.1f} mg/m² dox-equiv · {detail}"
        win = tk.Toplevel(self)
        win.wm_overrideredirect(True)
        win.wm_geometry(f"+{event.x_root + 14}+{event.y_root + 6}")
        tk.Label(win, text=tip_text, font=('Arial', FONT_HINT),
                 bg='#ffffe0', fg='#333333',
                 relief='solid', borderwidth=1,
                 padx=8, pady=4).pack()
        self._tooltip_win = win

    def _hide_tooltip(self):
        """Destroy the active tooltip window if one exists."""
        if self._tooltip_win is not None:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None

    def _load_patients(self):
        """Fetch all patients from the database and populate the Treeview."""
        # Clear all existing rows in one call before reloading.
        self.tree.delete(*self.tree.get_children())
        self._row_stripes.clear()
        self._row_dose_tags.clear()
        self._patient_summaries.clear()

        patients = Patient.get_all(self.app.conn)

        if not patients:
            self.empty_label.place(relx=0.5, rely=0.5, anchor='center')
            self.after(0, self._sync_scrollbar)
            return

        # Hide the empty-state label now that we have rows.
        self.empty_label.place_forget()

        for index, patient in enumerate(patients):
            cycles = get_cycles_by_patient(self.app.conn, patient.id)
            if cycles:
                completed = sum(1 for c in cycles if c.status == 'completed')
                current_cycle = f"{completed}/{patient.total_cycles or '?'}"
            else:
                current_cycle = f"0/{patient.total_cycles or 8}"

            # Cumulative dose risk for this patient.
            summary  = cumulative_dose(self.app.conn, patient.id)
            self._patient_summaries[str(patient.id)] = summary
            risk_text = _RISK_TEXT.get(summary.status, '')
            dose_tag  = f'dose_{summary.status}'

            stripe = 'even' if index % 2 == 0 else 'odd'
            self._row_stripes[str(patient.id)]   = stripe
            self._row_dose_tags[str(patient.id)] = dose_tag

            # dose_tag listed first — its foreground takes priority over stripe's.
            self.tree.insert('', 'end', iid=str(patient.id),
                             tags=(str(patient.id), dose_tag, stripe),
                             values=(
                                 patient.patient_id,
                                 patient.name,
                                 current_cycle,
                                 patient.protocol or '-',
                                 patient.age if patient.age is not None else '-',
                                 str(patient.diagnosis_date) if patient.diagnosis_date else '-',
                                 risk_text,
                             ))

        self.after(0, self._sync_scrollbar)

    def _on_row_double_click(self, event):
        """Handle double-click on a Treeview row — navigate to that patient's dashboard."""
        selected = self.tree.selection()
        if not selected:
            return
        # Extract the patient DB id from the row's tags (set during insert).
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        self._open_patient(patient_id=patient_db_id)

    def _on_remove_patient(self):
        """Soft-delete the selected patient after confirmation."""
        selected = self.tree.selection()
        if not selected:
            return
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        patient_id_str = self.tree.item(selected[0])['values'][0]
        name = self.tree.item(selected[0])['values'][1]
        confirmed = messagebox.askyesno(
            "Remove Patient",
            f"Remove {name} ({patient_id_str})?\n"
            f"The record is hidden from the list but kept in the audit trail.",
        )
        if confirmed:
            soft_delete_patient(self.app.conn, patient_db_id)
            self.refresh()

    def _on_add_patient(self):
        """Open the Add Patient dialog and refresh the list if a patient was saved."""
        from views.add_patient_dialog import AddPatientDialog
        dialog = AddPatientDialog(self.winfo_toplevel(), self.app)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh()

    def _on_edit_patient(self):
        """Open the Edit Patient dialog for the selected patient."""
        selected = self.tree.selection()
        if not selected:
            return
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        patient = get_patient_by_db_id(self.app.conn, patient_db_id)
        if patient is None:
            return
        from views.dialogs.edit_patient_dialog import EditPatientDialog
        dialog = EditPatientDialog(self.winfo_toplevel(), self.app, patient)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh()

    def refresh(self):
        """Reload the patient list from the database. Called after adding or editing a patient."""
        self._load_patients()

    def _open_patient(self, patient_id: int):
        """Navigate to the dashboard for the given patient."""
        from views.dashboard import DashboardView
        self.app.show_frame(DashboardView, patient_id=patient_id)
