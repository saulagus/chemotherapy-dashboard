import tkinter as tk
from tkinter import ttk
from models import Patient, get_cycles_by_patient
from utils import show_info, BG, BG_ALT, BG_ROW_ODD, SEPARATOR, FG, FG_MUTED


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
        header = tk.Frame(self, bg=BG, pady=10, padx=16)
        header.pack(fill='x')

        tk.Label(header, text="AC-T Chemotherapy Dashboard",
                 font=('Arial', 13), bg=BG, fg=FG).pack(side='left')

        add_btn = tk.Label(header, text="+ Add Patient",
                           font=('Arial', 11), bg=BG, fg=FG,
                           cursor='hand2', padx=8, pady=4)
        add_btn.pack(side='right')
        add_btn.bind('<Button-1>', lambda e: self._on_add_patient())

        # Thin separator line below the header.
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Content area.
        content = tk.Frame(self, bg=BG, padx=16, pady=8)
        content.pack(fill='both', expand=True)

        tk.Label(content, text="Patients", font=('Arial', 11),
                 bg=BG, fg=FG_MUTED).pack(anchor='w', pady=(0, 8))

        # Treeview + vertical scrollbar in a shared frame.
        tree_frame = tk.Frame(content, bg=BG)
        tree_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('id', 'name', 'current_cycle', 'protocol'),
            show='headings',
            height=20,            # visible rows before scrolling kicks in
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        # Column headings.
        self.tree.heading('id',            text='Patient ID')
        self.tree.heading('name',          text='Name')
        self.tree.heading('current_cycle', text='Current Cycle')
        self.tree.heading('protocol',      text='Protocol')

        # Column widths and alignment.
        self.tree.column('id',            width=130, anchor='center', stretch=False)
        self.tree.column('name',          width=200, anchor='w')
        self.tree.column('current_cycle', width=140, anchor='center', stretch=False)
        self.tree.column('protocol',      width=200, anchor='center', stretch=False)

        self.tree.pack(fill='both', expand=True)

        # Alternating row stripe colours.
        self.tree.tag_configure('even', background=BG_ALT)
        self.tree.tag_configure('odd',  background=BG_ROW_ODD)

        # Double-click a row to open that patient's dashboard.
        self.tree.bind('<Double-1>', self._on_row_double_click)

        # Empty-state label overlaid on the tree when no patients exist.
        self.empty_label = tk.Label(
            tree_frame,
            text="No patients found.\nUse 'Add Patient' to create one.",
            font=('Arial', 12), bg=BG_ALT, fg=FG_MUTED, justify='center',
        )

    def _load_patients(self):
        """Fetch all patients from the database and populate the Treeview."""
        # Clear all existing rows in one call before reloading.
        self.tree.delete(*self.tree.get_children())

        patients = Patient.get_all(self.app.conn)

        if not patients:
            # Show the empty-state message centred over the tree.
            self.empty_label.place(relx=0.5, rely=0.5, anchor='center')
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
                current_cycle = '-'

            # 'even'/'odd' drives the alternating stripe; patient.id enables tag-based id lookup.
            stripe = 'even' if index % 2 == 0 else 'odd'
            self.tree.insert('', 'end', iid=str(patient.id),
                             tags=(str(patient.id), stripe),
                             values=(
                                 patient.patient_id,
                                 patient.name,
                                 current_cycle,
                                 patient.protocol or '-',
                             ))

    def _on_row_double_click(self, event):
        """Handle double-click on a Treeview row — navigate to that patient's dashboard."""
        selected = self.tree.selection()
        if not selected:
            return
        # Extract the patient DB id from the row's tags (set during insert).
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        self._open_patient(patient_id=patient_db_id)

    def _on_add_patient(self):
        """Open the Add Patient form. Form dialog implemented on Day 6."""
        show_info("Coming Soon", "Add Patient form will be available on Day 6.")

    def refresh(self):
        """Reload the patient list from the database. Called after adding or editing a patient."""
        self._load_patients()

    def _open_patient(self, patient_id: int):
        """Navigate to the dashboard for the given patient."""
        from views.dashboard import DashboardView
        self.app.show_frame(DashboardView, patient_id=patient_id)
