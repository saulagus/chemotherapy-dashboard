import tkinter as tk
from tkinter import ttk
from utils import BG, SEPARATOR, FG, FG_MUTED


class DashboardView(tk.Frame):
    """Patient dashboard — displays treatment summary for a single patient."""

    def __init__(self, parent, app, patient_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.patient_id = None
        self._build_ui()
        self.set_patient(patient_id)

    def _build_ui(self):
        self.configure(bg=BG)

        # Header bar.
        header = tk.Frame(self, bg=BG, pady=10, padx=16)
        header.pack(fill='x')

        self.title_label = tk.Label(header, text="Patient Dashboard",
                                    font=('Arial', 13), bg=BG, fg=FG)
        self.title_label.pack(side='left')

        back_btn = tk.Label(header, text="<- Back",
                            font=('Arial', 11), bg=BG, fg=FG,
                            cursor='hand2', padx=8, pady=4)
        back_btn.pack(side='right')
        back_btn.bind('<Button-1>', lambda e: self._go_back())

        # Thin separator line below the header.
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Patient info area — populated with real data on Day 7.
        self.patient_frame = tk.Frame(self, bg=BG, padx=16, pady=12)
        self.patient_frame.pack(fill='x')

        self.patient_label = tk.Label(
            self.patient_frame,
            text="",
            font=('Arial', 13), bg=BG, fg=FG_MUTED,
        )
        self.patient_label.pack(anchor='w')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x', padx=16)

        # Main content area — cycle table and lab results added on Day 7.
        content = tk.Frame(self, bg=BG, padx=16, pady=8)
        content.pack(fill='both', expand=True)

        tk.Label(content,
                 text="Treatment cycles and lab results will appear here.",
                 font=('Arial', 12), bg=BG, fg=FG_MUTED,
                 ).place(relx=0.5, rely=0.5, anchor='center')

    def set_patient(self, patient_id):
        """Store the patient id and update all labels that reference it."""
        self.patient_id = patient_id
        if patient_id is None:
            self.title_label.config(text="Patient Dashboard")
            self.patient_label.config(text="No patient selected.")
        else:
            self.title_label.config(text=f"Patient Dashboard — ID: {patient_id}")
            self.patient_label.config(text=f"Patient ID: {patient_id}")

    def _go_back(self):
        from views.patient_list import PatientListView
        self.app.show_frame(PatientListView)
