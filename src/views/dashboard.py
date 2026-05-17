import tkinter as tk
from utils import BG, BG_ALT, SEPARATOR, FONT_HEADER, FONT_BODY, FONT_HINT, FG, FG_MUTED
from models import get_patient_by_db_id
from services.cycles import cumulative_dose
from views.components.patient_header import PatientHeader
from views.components.timeline import TimelineComponent
from views.components.latest_labs_panel import LatestLabsPanel
from views.components.anc_trend_chart import ANCTrendChart
from views.components.cardiotoxicity_panel import CardiotoxicityPanel
from views.components.low_anc_banner import LowAncBanner
from views.components.dose_mod_history_panel import DoseModHistoryPanel


class DashboardView(tk.Frame):
    """Patient dashboard — displays treatment summary for a single patient."""

    def __init__(self, parent, app, patient_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.patient_id = None
        self.patient = None
        self._build_ui()
        self.set_patient(patient_id)

    def _build_ui(self):
        self.configure(bg=BG)

        # ── Low-ANC banner ────────────────────────────────────────────────────
        self.anc_banner = LowAncBanner(self, self.app.conn)
        self.anc_banner.pack(fill='x')

        # ── Patient header ────────────────────────────────────────────────────
        self.header = PatientHeader(self, self.app,
                                    on_add_labs=self._on_add_labs,
                                    on_show_history=self._on_show_history,
                                    on_export_pdf=self._on_export_pdf,
                                    on_export_csv=self._on_export_csv,
                                    on_print=self._on_print)
        self.header.pack(fill='x')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # ── Scrollable content ────────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        content = tk.Frame(canvas, bg=BG, padx=16, pady=16)
        content_window = canvas.create_window((0, 0), window=content, anchor='nw')

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(content_window, width=canvas.winfo_width())

        content.bind('<Configure>', _on_configure)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(content_window, width=e.width))

        content.columnconfigure(0, weight=1)

        # ── Timeline ──────────────────────────────────────────────────────────
        timeline_frame = tk.Frame(content, bg=BG_ALT, padx=16, pady=16)
        timeline_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 8))

        tk.Label(timeline_frame, text="Treatment Timeline",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(anchor='w')
        tk.Frame(timeline_frame, bg=SEPARATOR, height=1).pack(fill='x', pady=(6, 12))

        self.timeline = TimelineComponent(timeline_frame, self.app)
        self.timeline.on_cycle_save = self._on_cycle_saved
        self.timeline.pack(anchor='w', pady=(0, 8))

        # ── Labs + chart ──────────────────────────────────────────────────────
        bottom = tk.Frame(content, bg=BG)
        bottom.grid(row=1, column=0, sticky='nsew', pady=(0, 8))
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)

        self.labs_panel = LatestLabsPanel(bottom, self.app.conn,
                                          on_add_labs=self._on_add_labs)
        self.labs_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        self.chart = ANCTrendChart(bottom, self.app.conn)
        self.chart.grid(row=0, column=1, sticky='nsew')

        # ── Cardiotoxicity panel ──────────────────────────────────────────────
        self.cardiotoxicity_panel = CardiotoxicityPanel(
            content, self.app.conn, on_add_lvef=self._on_add_lvef
        )
        self.cardiotoxicity_panel.grid(row=2, column=0, sticky='nsew', pady=(0, 8))

        # ── Dose modification history panel ──────────────────────────────────
        self.dose_mod_panel = DoseModHistoryPanel(content, self.app.conn)
        self.dose_mod_panel.grid(row=3, column=0, sticky='nsew', pady=(0, 8))

    def set_patient(self, patient_id):
        self.patient_id = patient_id
        self.patient = get_patient_by_db_id(self.app.conn, patient_id) if patient_id else None
        if patient_id:
            self.anc_banner.load_patient(patient_id)
            self.timeline.load_patient(patient_id)
            self.labs_panel.load_patient(patient_id)
            self.chart.load_patient(patient_id)
            self.cardiotoxicity_panel.load_patient(patient_id)
            self.dose_mod_panel.load_patient(patient_id)
        self.refresh()

    def refresh(self):
        self.header.update_display(self.patient)
        self._refresh_header_badge()

    def _refresh_header_badge(self):
        if self.patient_id is None:
            self.header.update_cumulative_badge(None)
            return
        summary = cumulative_dose(self.app.conn, self.patient_id)
        self.header.update_cumulative_badge(summary)

    def _on_cycle_saved(self):
        self.cardiotoxicity_panel.refresh()
        self._refresh_header_badge()
        self.dose_mod_panel.refresh()

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

    def _on_export_pdf(self):
        if self.patient is None:
            return
        from views.dialogs.export_pdf_dialog import ExportPdfDialog
        from config import get as get_config
        ExportPdfDialog(self.winfo_toplevel(), self.app.conn,
                        self.patient_id, self.patient.patient_id, get_config())

    def _on_export_csv(self):
        if self.patient is None:
            return
        from views.dialogs.export_csv_dialog import ExportCsvDialog
        from config import get as get_config
        ExportCsvDialog(self.winfo_toplevel(), self.app.conn,
                        self.patient_id, self.patient.patient_id, get_config())

    def _on_print(self):
        if self.patient is None:
            return
        import os, subprocess, tempfile
        from datetime import date
        from config import get as get_config
        from services.exports import export_print_dashboard_pdf

        config = get_config()
        today = date.today()
        try:
            tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            tmp.close()
            result = export_print_dashboard_pdf(
                self.app.conn, self.patient_id, tmp.name, config, today
            )

            # OS print
            try:
                if os.name == 'nt':
                    os.startfile(result.path, 'print')
                else:
                    subprocess.run(['lpr', result.path], check=True)
            except Exception:
                import platform
                if platform.system() == 'Darwin':
                    subprocess.run(['open', result.path])
                else:
                    from tkinter import messagebox
                    messagebox.showinfo("Print",
                        f"PDF saved to: {result.path}\nOpen it to print.", parent=self)
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror("Print Failed", str(exc), parent=self)

    def _refresh_labs(self):
        self.labs_panel.refresh()
        self.chart.refresh()
        self.anc_banner.refresh()
