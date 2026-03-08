import tkinter as tk


class PatientListView(tk.Frame):
    """Stub — will be fully implemented on Day 5."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        tk.Label(self, text="Patient List View", font=('Arial', 18)).pack(pady=40)
        tk.Button(self, text="Go to Dashboard (test)",
                  command=self._go_to_dashboard).pack()

    def _go_to_dashboard(self):
        from views.dashboard import DashboardView
        self.app.show_frame(DashboardView)
