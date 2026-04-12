import tkinter as tk
from tkinter import ttk, messagebox
from models import Patient, get_cycles_by_patient, delete_patient
from utils import show_info, BG, BG_ALT, BG_ROW_ODD, SEPARATOR, FG, FG_MUTED, FONT_BODY, FONT_TITLE


class PatientListView(tk.Frame):
    """Main screen — shows all patients and allows navigating to their dashboard."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
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
            columns=('id', 'name', 'current_cycle', 'protocol', 'age', 'diagnosis_date'),
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

        # Column widths and alignment.
        self.tree.column('id',             width=130, anchor='center', stretch=False)
        self.tree.column('name',           width=200, anchor='w')
        self.tree.column('current_cycle',  width=140, anchor='center', stretch=False)
        self.tree.column('protocol',       width=200, anchor='center', stretch=False)
        self.tree.column('age',            width=80,  anchor='center', stretch=False)
        self.tree.column('diagnosis_date', width=140, anchor='center', stretch=False)

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

        # Double-click to open dashboard; Motion/Leave for hover effect.
        self.tree.bind('<Double-1>', self._on_row_double_click)
        self.tree.bind('<Motion>', self._on_row_hover)
        self.tree.bind('<Leave>', self._on_row_leave)
        self._hovered_row = None
        self._row_stripes = {}  # row_id -> 'even' | 'odd'

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
        """Highlight the row under the cursor."""
        row = self.tree.identify_row(event.y)
        if row == self._hovered_row:
            return
        # Restore previous row to its original stripe (no competing tags).
        if self._hovered_row and self.tree.exists(self._hovered_row):
            stripe = self._row_stripes.get(self._hovered_row, 'even')
            self.tree.item(self._hovered_row, tags=(self._hovered_row, stripe))
        # Replace stripe with hover so it's the only background tag.
        if row:
            self.tree.item(row, tags=(row, 'hover'))
        self._hovered_row = row or None

    def _on_row_leave(self, event):
        """Remove hover highlight when the mouse leaves the treeview."""
        if self._hovered_row and self.tree.exists(self._hovered_row):
            stripe = self._row_stripes.get(self._hovered_row, 'even')
            self.tree.item(self._hovered_row, tags=(self._hovered_row, stripe))
        self._hovered_row = None

    def _load_patients(self):
        """Fetch all patients from the database and populate the Treeview."""
        # Clear all existing rows in one call before reloading.
        self.tree.delete(*self.tree.get_children())
        self._row_stripes.clear()

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
                # Count completed cycles — e.g. "2/8" means 2 of 8 cycles done.
                completed = sum(1 for c in cycles if c.status == 'completed')
                current_cycle = f"{completed}/{patient.total_cycles or '?'}"
            else:
                current_cycle = f"0/{patient.total_cycles or 8}"

            # 'even'/'odd' drives the alternating stripe; patient.id enables tag-based id lookup.
            stripe = 'even' if index % 2 == 0 else 'odd'
            self._row_stripes[str(patient.id)] = stripe
            self.tree.insert('', 'end', iid=str(patient.id),
                             tags=(str(patient.id), stripe),
                             values=(
                                 patient.patient_id,
                                 patient.name,
                                 current_cycle,
                                 patient.protocol or '-',
                                 patient.age if patient.age is not None else '-',
                                 str(patient.diagnosis_date) if patient.diagnosis_date else '-',
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
        """Delete the selected patient after confirmation."""
        selected = self.tree.selection()
        if not selected:
            return
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        patient_id_str = self.tree.item(selected[0])['values'][0]
        name = self.tree.item(selected[0])['values'][1]
        confirmed = messagebox.askyesno(
            "Remove Patient",
            f"Remove {name} ({patient_id_str})?\nThis cannot be undone.",
        )
        if confirmed:
            delete_patient(self.app.conn, patient_id_str)
            self.refresh()

    def _on_add_patient(self):
        """Open the Add Patient dialog and refresh the list if a patient was saved."""
        from views.add_patient_dialog import AddPatientDialog
        dialog = AddPatientDialog(self.winfo_toplevel(), self.app)
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
