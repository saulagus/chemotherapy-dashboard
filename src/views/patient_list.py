import tkinter as tk
from tkinter import ttk
from models import get_all_patients, get_cycles_by_patient
from utils import show_info


class PatientListView(tk.Frame):
    """Main screen — shows all patients and allows navigating to their dashboard."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self._build_ui()
        self._load_patients()

    def _build_ui(self):
        # Header bar: app title on the left.
        header = tk.Frame(self, pady=10, padx=16)
        header.pack(fill='x')

        tk.Label(
            header,
            text="AC-T Chemotherapy Dashboard",
            font=('Arial', 20, 'bold'),
        ).pack(side='left')

        # Add Patient button — opens the form dialog (implemented on Day 6).
        tk.Button(
            header,
            text="+ Add Patient",
            command=self._on_add_patient,
        ).pack(side='right', padx=(0, 8))

        # Section label above the list.
        content = tk.Frame(self, padx=16, pady=8)
        content.pack(fill='both', expand=True)

        tk.Label(content, text="Patients", font=('Arial', 14)).pack(anchor='w', pady=(0, 8))

        # Treeview + vertical scrollbar in a shared frame.
        tree_frame = tk.Frame(content)
        tree_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('id', 'name', 'current_cycle', 'status'),
            show='headings',          # hide the default empty first column
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        # Column headings.
        self.tree.heading('id',            text='Patient ID')
        self.tree.heading('name',          text='Name')
        self.tree.heading('current_cycle', text='Current Cycle')
        self.tree.heading('status',        text='Status')

        # Column widths and alignment.
        self.tree.column('id',            width=120, anchor='center')
        self.tree.column('name',          width=220)
        self.tree.column('current_cycle', width=160, anchor='center')
        self.tree.column('status',        width=130, anchor='center')

        self.tree.pack(fill='both', expand=True)

        # Double-click a row to open that patient's dashboard.
        self.tree.bind('<Double-1>', self._on_row_double_click)

        # Empty-state label overlaid on the tree when no patients exist.
        self.empty_label = tk.Label(
            tree_frame,
            text="No patients found.\nUse 'Add Patient' to create one.",
            font=('Arial', 12),
            fg='gray',
            justify='center',
        )

    def _load_patients(self):
        """Fetch all patients from the database and populate the Treeview."""
        # Remove any previously displayed rows before reloading.
        for row in self.tree.get_children():
            self.tree.delete(row)

        patients = get_all_patients(self.app.conn)

        if not patients:
            # Show the empty-state message centred over the tree.
            self.empty_label.place(relx=0.5, rely=0.5, anchor='center')
            return

        # Hide the empty-state label now that we have rows.
        self.empty_label.place_forget()

        for patient in patients:
            cycles = get_cycles_by_patient(self.app.conn, patient.id)
            if cycles:
                # get_cycles_by_patient returns cycles ordered by cycle_number.
                latest = cycles[-1]
                current_cycle = f"Cycle {latest.cycle_number} / {patient.total_cycles or '?'}"
                status = (latest.status or '-').capitalize()
            else:
                current_cycle = 'No cycles'
                status = '-'

            # iid is the row identifier — storing patient.id lets us retrieve it on click.
            self.tree.insert('', 'end', iid=str(patient.id), values=(
                patient.patient_id,
                patient.name,
                current_cycle,
                status,
            ))

    def _on_row_double_click(self, event):
        """Handle double-click on a Treeview row — navigate to that patient's dashboard."""
        selected = self.tree.selection()
        if selected:
            # iid was set to str(patient.id) on insert.
            patient_db_id = int(selected[0])
            self._open_patient(patient_id=patient_db_id)

    def _on_add_patient(self):
        """Open the Add Patient form. Form dialog implemented on Day 6."""
        show_info("Coming Soon", "Add Patient form will be available on Day 6.")

    def _open_patient(self, patient_id: int):
        """Navigate to the dashboard for the given patient."""
        from views.dashboard import DashboardView
        self.app.show_frame(DashboardView, patient_id=patient_id)
