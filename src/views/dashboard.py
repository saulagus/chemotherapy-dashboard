import tkinter as tk
from tkinter import ttk
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED
from models import Patient, get_patient_by_db_id, get_cycles_by_patient, get_labs_by_patient


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

        # ── Top nav bar ────────────────────────────────────────────────────────
        nav = tk.Frame(self, bg=BG, pady=10, padx=16)
        nav.pack(fill='x')

        self.title_label = tk.Label(nav, text="Patient Dashboard",
                                    font=('Arial', 13), bg=BG, fg=FG)
        self.title_label.pack(side='left')

        back_btn = tk.Label(nav, text="<- Back",
                            font=('Arial', 11), bg=BG, fg=FG,
                            cursor='hand2', padx=8, pady=4)
        back_btn.pack(side='right')
        back_btn.bind('<Button-1>', lambda e: self._go_back())

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # ── Patient header card ────────────────────────────────────────────────
        self.header_frame = tk.Frame(self, bg=BG_ALT, padx=20, pady=16)
        self.header_frame.pack(fill='x')

        # Patient name — large and prominent.
        self.name_label = tk.Label(self.header_frame, text="",
                                   font=('Arial', 20, 'bold'), bg=BG_ALT, fg=FG,
                                   anchor='w')
        self.name_label.pack(anchor='w')

        # Detail row: ID · Protocol · Start Date
        detail_row = tk.Frame(self.header_frame, bg=BG_ALT)
        detail_row.pack(anchor='w', pady=(6, 0))

        self.id_label = tk.Label(detail_row, text="",
                                 font=('Arial', 11), bg=BG_ALT, fg=FG_MUTED)
        self.id_label.pack(side='left')

        tk.Label(detail_row, text="  ·  ",
                 font=('Arial', 11), bg=BG_ALT, fg=FG_MUTED).pack(side='left')

        self.protocol_label = tk.Label(detail_row, text="",
                                       font=('Arial', 11), bg=BG_ALT, fg=FG_MUTED)
        self.protocol_label.pack(side='left')

        tk.Label(detail_row, text="  ·  ",
                 font=('Arial', 11), bg=BG_ALT, fg=FG_MUTED).pack(side='left')

        self.start_date_label = tk.Label(detail_row, text="",
                                         font=('Arial', 11), bg=BG_ALT, fg=FG_MUTED)
        self.start_date_label.pack(side='left')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # ── Main content area ──────────────────────────────────────────────────
        content = tk.Frame(self, bg=BG, padx=16, pady=16)
        content.pack(fill='both', expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # ── Timeline placeholder ───────────────────────────────────────────────
        timeline_frame = tk.Frame(content, bg=BG_ALT, padx=16, pady=16)
        timeline_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        tk.Label(timeline_frame, text="Treatment Timeline",
                 font=('Arial', 11, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(anchor='w')
        tk.Frame(timeline_frame, bg=SEPARATOR, height=1).pack(fill='x', pady=(6, 12))
        tk.Label(timeline_frame,
                 text="Treatment Timeline\n(Coming in Sprint 2)",
                 font=('Arial', 12), bg=BG_ALT, fg=FG_MUTED,
                 justify='center').place(relx=0.5, rely=0.5, anchor='center')

        # ── Labs placeholder ───────────────────────────────────────────────────
        labs_frame = tk.Frame(content, bg=BG_ALT, padx=16, pady=16)
        labs_frame.grid(row=0, column=1, sticky='nsew')

        tk.Label(labs_frame, text="Latest Labs",
                 font=('Arial', 11, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(anchor='w')
        tk.Frame(labs_frame, bg=SEPARATOR, height=1).pack(fill='x', pady=(6, 12))
        tk.Label(labs_frame,
                 text="Latest Labs\n(Coming in Sprint 3)",
                 font=('Arial', 12), bg=BG_ALT, fg=FG_MUTED,
                 justify='center').place(relx=0.5, rely=0.5, anchor='center')

    def set_patient(self, patient_id):
        """Load patient from DB, store in self.patient, then refresh display."""
        self.patient_id = patient_id
        self.patient = get_patient_by_db_id(self.app.conn, patient_id) if patient_id else None
        self.refresh()

    def refresh(self):
        """Update all header labels from self.patient."""
        if self.patient is None:
            self.title_label.config(text="Patient Dashboard")
            self.name_label.config(text="No patient selected.")
            self.id_label.config(text="")
            self.protocol_label.config(text="")
            self.start_date_label.config(text="")
        else:
            self.title_label.config(text="Patient Dashboard")
            self.name_label.config(text=self.patient.name)
            self.id_label.config(text=f"ID: {self.patient.patient_id}")
            self.protocol_label.config(text=self.patient.protocol or "—")
            self.start_date_label.config(
                text=f"Started {self.patient.start_date}" if self.patient.start_date else "—")

    def _go_back(self):
        from views.patient_list import PatientListView
        self.app.show_frame(PatientListView)
