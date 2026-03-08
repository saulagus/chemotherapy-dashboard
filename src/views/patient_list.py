import tkinter as tk
from tkinter import ttk


class PatientListView(tk.Frame):
    """Main screen — shows all patients and allows navigating to their dashboard."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Header bar: title on the left.
        header = tk.Frame(self, pady=10, padx=16)
        header.pack(fill='x')

        tk.Label(
            header,
            text="AC-T Chemotherapy Dashboard",
            font=('Arial', 20, 'bold'),
        ).pack(side='left')

        # Main content area fills the rest of the window.
        content = tk.Frame(self, padx=16, pady=8)
        content.pack(fill='both', expand=True)

        tk.Label(
            content,
            text="Patients",
            font=('Arial', 14),
        ).pack(anchor='w', pady=(0, 8))

        # Placeholder for the Treeview — replaced on Day 5.
        self.list_frame = tk.Frame(content, relief='sunken', bd=1)
        self.list_frame.pack(fill='both', expand=True)

        self._show_empty_state()

    def _show_empty_state(self):
        """Display a message when no patients are loaded yet."""
        tk.Label(
            self.list_frame,
            text="No patients found.\nUse 'Add Patient' to create one.",
            font=('Arial', 12),
            fg='gray',
            justify='center',
        ).place(relx=0.5, rely=0.5, anchor='center')

        # Temporary nav test — replaced by Treeview double-click on Day 5.
        tk.Button(
            self.list_frame,
            text="Open Patient Dashboard (test)",
            command=lambda: self._open_patient(patient_id=1),
        ).place(relx=0.5, rely=0.7, anchor='center')

    def _open_patient(self, patient_id: int):
        """Navigate to the dashboard for the given patient. Called by Treeview on Day 5."""
        from views.dashboard import DashboardView
        self.app.show_frame(DashboardView, patient_id=patient_id)
