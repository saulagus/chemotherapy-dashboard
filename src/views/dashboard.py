import tkinter as tk
from tkinter import ttk


class DashboardView(tk.Frame):
    """Patient dashboard — displays treatment summary for a single patient."""

    def __init__(self, parent, app, patient_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.patient_id = patient_id  # integer DB id of the selected patient
        self._build_ui()

    def _build_ui(self):
        # Header bar: title on the left, Back button on the right.
        header = tk.Frame(self, pady=10, padx=16)
        header.pack(fill='x')

        tk.Label(
            header,
            text="Patient Dashboard",
            font=('Arial', 20, 'bold'),
        ).pack(side='left')

        tk.Button(
            header,
            text="<- Back to Patient List",
            command=self._go_back,
        ).pack(side='right')

        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=16)

        # Patient info area — populated with real data on Day 7.
        self.patient_frame = tk.Frame(self, padx=16, pady=12)
        self.patient_frame.pack(fill='x')

        self.patient_label = tk.Label(
            self.patient_frame,
            text="No patient selected." if self.patient_id is None else f"Patient ID: {self.patient_id}",
            font=('Arial', 13),
            fg='gray',
        )
        self.patient_label.pack(anchor='w')

        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=16)

        # Main content area — cycle table and lab results added on Day 7.
        content = tk.Frame(self, padx=16, pady=8)
        content.pack(fill='both', expand=True)

        tk.Label(
            content,
            text="Treatment cycles and lab results will appear here.",
            font=('Arial', 12),
            fg='gray',
        ).place(relx=0.5, rely=0.5, anchor='center')

    def _go_back(self):
        from views.patient_list import PatientListView
        self.app.show_frame(PatientListView)
