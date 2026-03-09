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
        # Header bar: matches the patient list header style.
        header = tk.Frame(self, bg='#1e1e1e', pady=10, padx=16)
        header.pack(fill='x')

        tk.Label(
            header,
            text="Patient Dashboard",
            font=('Arial', 13),
            bg='#1e1e1e',
            fg='#f0f0f0',
        ).pack(side='left')

        # Label styled as a button — avoids macOS system gray on tk.Button.
        back_btn = tk.Label(
            header,
            text="<- Back",
            font=('Arial', 11),
            bg='#1e1e1e',
            fg='#f0f0f0',
            cursor='hand2',
            padx=8,
            pady=4,
        )
        back_btn.pack(side='right')
        back_btn.bind('<Button-1>', lambda e: self._go_back())

        # Thin separator line below the header.
        tk.Frame(self, bg='#333333', height=1).pack(fill='x')

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
