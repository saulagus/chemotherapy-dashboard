import tkinter as tk


class DashboardView(tk.Frame):
    """Stub — will be fully implemented on Day 7."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        tk.Label(self, text="Dashboard View", font=('Arial', 18)).pack(pady=40)
        tk.Button(self, text="Back to Patient List",
                  command=self._go_back).pack()

    def _go_back(self):
        from views.patient_list import PatientListView
        self.app.show_frame(PatientListView)
