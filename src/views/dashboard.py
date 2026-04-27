import tkinter as tk
from utils import BG, BG_ALT, SEPARATOR, FONT_HEADER, FG
from models import get_patient_by_db_id
from services.cycles import cumulative_dose
from views.components.patient_header import PatientHeader
from views.components.timeline import TimelineComponent
from views.components.latest_labs_panel import LatestLabsPanel
from views.components.anc_trend_chart import ANCTrendChart
from views.components.cardiotoxicity_panel import CardiotoxicityPanel


class DashboardView(tk.Frame):
    """Patient dashboard — displays treatment summary for a single patient."""

    def __init__(self, parent, app, patient_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.patient_id = None
        self.patient = None     # Full Patient object loaded from DB.
        self._build_ui()
        self.set_patient(patient_id)

    def _build_ui(self):
        self.configure(bg=BG)

        # ── Patient header ─────────────────────────────────────────────────────
        self.header = PatientHeader(self, self.app,
                                    on_add_labs=self._on_add_labs,
                                    on_show_history=self._on_show_history)
        self.header.pack(fill='x')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # ── Main content area ──────────────────────────────────────────────────
        content = tk.Frame(self, bg=BG, padx=16, pady=16)
        content.pack(fill='both', expand=True)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=0)  # timeline fixed height
        content.rowconfigure(1, weight=2)  # labs+chart expand
        content.rowconfigure(2, weight=1)  # cardiotoxicity panel

        # ── Timeline component ─────────────────────────────────────────────────
        timeline_frame = tk.Frame(content, bg=BG_ALT, padx=16, pady=16)
        timeline_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 8))

        tk.Label(timeline_frame, text="Treatment Timeline",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(anchor='w')
        tk.Frame(timeline_frame, bg=SEPARATOR, height=1).pack(fill='x', pady=(6, 12))

        self.timeline = TimelineComponent(timeline_frame, self.app)
        self.timeline.on_cycle_save = self._on_cycle_saved
        self.timeline.pack(anchor='w', pady=(0, 8))

        # ── Bottom section: labs + chart side by side ──────────────────────────
        bottom = tk.Frame(content, bg=BG)
        bottom.grid(row=1, column=0, sticky='nsew')
        bottom.rowconfigure(0, weight=1)
        bottom.columnconfigure(0, weight=1)   # labs ~35%
        bottom.columnconfigure(1, weight=2)   # chart ~65%

        self.labs_panel = LatestLabsPanel(bottom, self.app.conn,
                                          on_add_labs=self._on_add_labs)
        self.labs_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        self.chart = ANCTrendChart(bottom, self.app.conn)
        self.chart.grid(row=0, column=1, sticky='nsew')

        # ── Cardiotoxicity panel ───────────────────────────────────────────────
        self.cardiotoxicity_panel = CardiotoxicityPanel(
            content, self.app.conn, on_add_lvef=self._on_add_lvef
        )
        self.cardiotoxicity_panel.grid(row=2, column=0, sticky='nsew', pady=(8, 0))

    def set_patient(self, patient_id):
        """Load patient from DB, store in self.patient, then refresh display."""
        self.patient_id = patient_id
        self.patient = get_patient_by_db_id(self.app.conn, patient_id) if patient_id else None
        if patient_id:
            self.timeline.load_patient(patient_id)
            self.labs_panel.load_patient(patient_id)
            self.chart.load_patient(patient_id)
            self.cardiotoxicity_panel.load_patient(patient_id)
        self.refresh()

    def refresh(self):
        """Refresh all dashboard components from self.patient."""
        self.header.update_display(self.patient)
        self._refresh_header_badge()

    def _refresh_header_badge(self):
        """Recompute cumulative dose and update the header risk badge."""
        if self.patient_id is None:
            self.header.update_cumulative_badge(None)
            return
        summary = cumulative_dose(self.app.conn, self.patient_id)
        self.header.update_cumulative_badge(summary)

    def _on_cycle_saved(self):
        """Called by TimelineComponent after any cycle create/update/delete."""
        self.cardiotoxicity_panel.refresh()
        self._refresh_header_badge()

    def _on_add_labs(self):
        if self.patient_id is None:
            return
        from views.dialogs.add_lab_dialog import AddLabDialog
        AddLabDialog(self.winfo_toplevel(), self.app.conn, self.patient_id,
                     on_save=self._refresh_labs)

    def _on_add_lvef(self):
        if self.patient_id is None:
            return
        from views.dialogs.lvef_dialog import LvefDialog
        LvefDialog(self.winfo_toplevel(), self.app.conn, self.patient_id,
                   on_save=self._refresh_lvef)

    def _refresh_lvef(self):
        self.cardiotoxicity_panel.refresh()

    def _on_show_history(self):
        if self.patient is None:
            return
        from views.dialogs.audit_viewer_dialog import AuditViewerDialog
        AuditViewerDialog(self.winfo_toplevel(), self.app.conn, self.patient)

    def _refresh_labs(self):
        self.labs_panel.refresh()
        self.chart.refresh()

