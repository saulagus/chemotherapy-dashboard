import tkinter as tk
from tkinter import ttk, messagebox
from models import Patient, get_cycles_by_patient, get_patient_by_db_id
from services.cycles import cumulative_dose
from services.patients import soft_delete_patient, list_patients
from views.components.cycle_status_indicator import get_status_for_patient, status_sort_key, status_color
from utils import show_info, BG, BG_ALT, BG_ROW_ODD, SEPARATOR, FG, FG_MUTED, FONT_BODY, FONT_HINT, FONT_LABEL, FONT_TITLE

_RISK_TEXT = {
    'green':     'Green',
    'yellow':    '⚠ Yellow',
    'red':       '⛔ Red',
    'hard_stop': '⛔ STOP',
}
_RISK_FG = {
    'green':     '#4CAF50',
    'yellow':    '#FFC107',
    'red':       '#F44336',
    'hard_stop': '#F44336',
}

_STATUS_SORT_KEY = {
    'overdue': 0, 'due_soon': 1, 'on_schedule': 2, 'no_cycles': 3,
}


class PatientListView(tk.Frame):
    """Main screen — shows all patients and allows navigating to their dashboard."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self._patient_summaries = {}
        self._patient_statuses = {}
        self._status_tooltips = {}
        self._tooltip_win = None
        self._search_var = tk.StringVar()
        self._filter_var = tk.StringVar(value='All')
        self._sort_by = 'name'
        self._sort_dir = 'asc'
        self._search_after_id = None
        self._build_ui()
        self._load_patients()

    def _build_ui(self):
        self.configure(bg=BG)

        # Header bar
        header = tk.Frame(self, bg=BG, pady=14, padx=24)
        header.pack(fill='x')

        tk.Label(header, text="AC-T Chemotherapy Dashboard",
                 font=('Arial', FONT_TITLE), bg=BG, fg=FG).pack(side='left')

        add_btn = tk.Label(header, text="+ Add Patient",
                           font=('Arial', FONT_BODY), bg=BG, fg=FG,
                           cursor='hand2', padx=8, pady=4)
        add_btn.pack(side='right')
        add_btn.bind('<Button-1>', lambda e: self._on_add_patient())

        edit_btn = tk.Label(header, text="Edit Patient",
                            font=('Arial', FONT_BODY), bg=BG, fg=FG,
                            cursor='hand2', padx=8, pady=4)
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e: self._on_edit_patient())

        remove_btn = tk.Label(header, text="- Remove Patient",
                              font=('Arial', FONT_BODY), bg=BG, fg='#e05555',
                              cursor='hand2', padx=8, pady=4)
        remove_btn.pack(side='right')
        remove_btn.bind('<Button-1>', lambda e: self._on_remove_patient())

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Search + filter bar
        toolbar = tk.Frame(self, bg=BG, padx=16, pady=8)
        toolbar.pack(fill='x')

        tk.Label(toolbar, text="Search:",
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED).pack(side='left')
        search_entry = tk.Entry(toolbar, textvariable=self._search_var,
                                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                                insertbackground=FG, relief='flat',
                                highlightbackground=SEPARATOR, highlightthickness=1,
                                width=24)
        search_entry.pack(side='left', padx=(6, 16))
        self._search_var.trace_add('write', self._on_search_changed)

        tk.Label(toolbar, text="Phase:",
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED).pack(side='left')
        filter_menu = tk.OptionMenu(toolbar, self._filter_var,
                                    'All', 'AC', 'T', 'Completed',
                                    command=lambda _: self._load_patients())
        filter_menu.config(font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                           activebackground=SEPARATOR, highlightthickness=0,
                           relief='flat')
        filter_menu['menu'].config(bg=BG_ALT, fg=FG, font=('Arial', FONT_BODY))
        filter_menu.pack(side='left', padx=(6, 0))

        # Content area
        content = tk.Frame(self, bg=BG, padx=16, pady=0)
        content.pack(fill='both', expand=True)

        tree_frame = tk.Frame(content, bg=BG)
        tree_frame.pack(fill='both', expand=True, pady=(8, 0))

        self._scrollbar = ttk.Scrollbar(tree_frame, orient='vertical')
        self._scrollbar.grid(row=0, column=1, sticky='ns')

        self.tree = ttk.Treeview(
            tree_frame,
            columns=('id', 'name', 'status', 'current_cycle', 'protocol', 'age', 'diagnosis_date', 'risk'),
            show='headings',
            height=20,
            yscrollcommand=self._on_yscroll,
        )
        self._scrollbar.config(command=self.tree.yview)

        # Column headings with sort
        cols = [
            ('id',             'Patient ID',     130, 'center', False),
            ('name',           'Name',           180, 'w',      True),
            ('status',         'Status',          90, 'center', False),
            ('current_cycle',  'Current Cycle',  120, 'center', False),
            ('protocol',       'Protocol',       180, 'center', False),
            ('age',            'Age',             70, 'center', False),
            ('diagnosis_date', 'Diagnosis Date', 120, 'center', False),
            ('risk',           'Dose Risk',       90, 'center', False),
        ]
        for col_id, text, width, anchor, stretch in cols:
            self.tree.heading(col_id, text=text,
                              command=lambda c=col_id: self._on_sort(c))
            self.tree.column(col_id, width=width, anchor=anchor, stretch=stretch)

        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self._scrollbar.grid_remove()
        tree_frame.bind('<Configure>', lambda e: self.after(0, self._sync_scrollbar))

        # Tags
        self.tree.tag_configure('even', background=BG_ALT)
        self.tree.tag_configure('odd',  background=BG_ROW_ODD)
        self.tree.tag_configure('hover', background='#2a3152')
        self.tree.tag_configure('dose_green',     foreground='#4CAF50')
        self.tree.tag_configure('dose_yellow',    foreground='#FFC107')
        self.tree.tag_configure('dose_red',       foreground='#F44336')
        self.tree.tag_configure('dose_hard_stop', foreground='#F44336')

        self.tree.bind('<Double-1>', self._on_row_double_click)
        self.tree.bind('<Motion>', self._on_row_hover)
        self.tree.bind('<Leave>', self._on_row_leave)
        self._hovered_row  = None
        self._row_stripes  = {}
        self._row_dose_tags = {}

        # Empty-state + no-match state
        self.empty_label = tk.Label(
            tree_frame,
            text="No patients found.\nUse 'Add Patient' to create one.",
            font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED, justify='center',
        )
        self._no_match_frame = tk.Frame(tree_frame, bg=BG_ALT)
        tk.Label(self._no_match_frame, text="No patients match",
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED).pack()
        clear_link = tk.Label(self._no_match_frame, text="Clear filters",
                              font=('Arial', FONT_LABEL), bg=BG_ALT, fg='#90CAF9',
                              cursor='hand2')
        clear_link.pack(pady=(4, 0))
        clear_link.bind('<Button-1>', lambda e: self._clear_filters())

    def _on_search_changed(self, *_):
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(150, self._load_patients)

    def _on_sort(self, col_id):
        sort_map = {
            'id': 'patient_id', 'name': 'name', 'age': 'age',
            'diagnosis_date': 'diagnosis_date',
        }
        if col_id in sort_map:
            db_col = sort_map[col_id]
            if self._sort_by == db_col:
                self._sort_dir = 'desc' if self._sort_dir == 'asc' else 'asc'
            else:
                self._sort_by = db_col
                self._sort_dir = 'asc'
            self._load_patients()
        elif col_id == 'status':
            self._sort_by_status()
        elif col_id == 'risk':
            self._sort_by_risk()

    def _sort_by_status(self):
        rows = list(self.tree.get_children())
        if not rows:
            return
        items = []
        for r in rows:
            sc = self._patient_statuses.get(r, 'no_cycles')
            items.append((status_sort_key(sc), r))
        items.sort(key=lambda x: x[0])
        for i, (_, iid) in enumerate(items):
            self.tree.move(iid, '', i)
        self._restripe()

    def _sort_by_risk(self):
        risk_order = {'green': 0, 'yellow': 1, 'red': 2, 'hard_stop': 3}
        rows = list(self.tree.get_children())
        if not rows:
            return
        items = []
        for r in rows:
            s = self._patient_summaries.get(r)
            items.append((risk_order.get(s.status if s else 'green', 0), r))
        items.sort(key=lambda x: x[0])
        for i, (_, iid) in enumerate(items):
            self.tree.move(iid, '', i)
        self._restripe()

    def _restripe(self):
        for i, iid in enumerate(self.tree.get_children()):
            stripe = 'even' if i % 2 == 0 else 'odd'
            self._row_stripes[iid] = stripe
            dose_tag = self._row_dose_tags.get(iid, 'dose_green')
            self.tree.item(iid, tags=(iid, dose_tag, stripe))

    def _clear_filters(self):
        self._search_var.set('')
        self._filter_var.set('All')
        self._load_patients()

    def _on_yscroll(self, first: str, last: str) -> None:
        self._scrollbar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid()

    def _sync_scrollbar(self) -> None:
        first, last = self.tree.yview()
        self._on_yscroll(str(first), str(last))

    def _on_row_hover(self, event):
        row = self.tree.identify_row(event.y)
        if row != self._hovered_row:
            if self._hovered_row and self.tree.exists(self._hovered_row):
                self._restore_row_tags(self._hovered_row)
            if row:
                dose_tag = self._row_dose_tags.get(row, 'dose_green')
                self.tree.item(row, tags=(row, dose_tag, 'hover'))
            self._hovered_row = row or None

        col = self.tree.identify_column(event.x)
        if row and col == '#8':
            self._show_risk_tooltip(event, row)
        elif row and col == '#3':
            self._show_status_tooltip(event, row)
        else:
            self._hide_tooltip()

    def _on_row_leave(self, event):
        if self._hovered_row and self.tree.exists(self._hovered_row):
            self._restore_row_tags(self._hovered_row)
        self._hovered_row = None
        self._hide_tooltip()

    def _restore_row_tags(self, row):
        stripe   = self._row_stripes.get(row, 'even')
        dose_tag = self._row_dose_tags.get(row, 'dose_green')
        self.tree.item(row, tags=(row, dose_tag, stripe))

    def _show_risk_tooltip(self, event, row):
        self._hide_tooltip()
        summary = self._patient_summaries.get(row)
        if summary is None:
            return
        total = summary.total_mg_per_m2
        from config import get as get_config
        thresholds = get_config().cardiotoxicity.cumulative_thresholds_mg_per_m2
        if summary.status == 'green':
            headroom = thresholds.yellow - total
            detail = f"{headroom:.1f} mg/m² to advisory threshold"
        elif summary.status == 'yellow':
            headroom = thresholds.red - total
            detail = f"{headroom:.1f} mg/m² to hold threshold"
        elif summary.status == 'red':
            headroom = thresholds.hard_stop - total
            detail = f"{headroom:.1f} mg/m² to hard stop"
        else:
            detail = "Exceeds hard-stop limit"
        tip_text = f"{total:.1f} mg/m² dox-equiv · {detail}"
        self._show_tooltip(event, tip_text)

    def _show_status_tooltip(self, event, row):
        self._hide_tooltip()
        tip = self._status_tooltips.get(row)
        if tip:
            self._show_tooltip(event, tip)

    def _show_tooltip(self, event, text):
        win = tk.Toplevel(self)
        win.wm_overrideredirect(True)
        win.wm_geometry(f"+{event.x_root + 14}+{event.y_root + 6}")
        tk.Label(win, text=text, font=('Arial', FONT_HINT),
                 bg='#ffffe0', fg='#333333',
                 relief='solid', borderwidth=1,
                 padx=8, pady=4).pack()
        self._tooltip_win = win

    def _hide_tooltip(self):
        if self._tooltip_win is not None:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None

    def _load_patients(self):
        self.tree.delete(*self.tree.get_children())
        self._row_stripes.clear()
        self._row_dose_tags.clear()
        self._patient_summaries.clear()
        self._patient_statuses.clear()
        self._status_tooltips.clear()

        search = self._search_var.get().strip()
        phase = self._filter_var.get()
        phase_filter = phase if phase != 'All' else None

        patients = list_patients(
            self.app.conn, search=search,
            sort_by=self._sort_by, sort_dir=self._sort_dir,
            phase_filter=phase_filter,
        )

        self.empty_label.place_forget()
        self._no_match_frame.place_forget()

        if not patients and (search or phase_filter):
            self._no_match_frame.place(relx=0.5, rely=0.5, anchor='center')
            self.after(0, self._sync_scrollbar)
            return
        elif not patients:
            self.empty_label.place(relx=0.5, rely=0.5, anchor='center')
            self.after(0, self._sync_scrollbar)
            return

        for index, patient in enumerate(patients):
            cycles = get_cycles_by_patient(self.app.conn, patient.id)
            if cycles:
                completed = sum(1 for c in cycles if c.status == 'completed')
                current_cycle = f"{completed}/{patient.total_cycles or '?'}"
            else:
                current_cycle = f"0/{patient.total_cycles or 8}"

            summary = cumulative_dose(self.app.conn, patient.id)
            self._patient_summaries[str(patient.id)] = summary
            risk_text = _RISK_TEXT.get(summary.status, '')
            dose_tag = f'dose_{summary.status}'

            status_code, status_text, tooltip = get_status_for_patient(
                self.app.conn, patient.id)
            self._patient_statuses[str(patient.id)] = status_code
            self._status_tooltips[str(patient.id)] = tooltip

            stripe = 'even' if index % 2 == 0 else 'odd'
            self._row_stripes[str(patient.id)] = stripe
            self._row_dose_tags[str(patient.id)] = dose_tag

            self.tree.insert('', 'end', iid=str(patient.id),
                             tags=(str(patient.id), dose_tag, stripe),
                             values=(
                                 patient.patient_id,
                                 patient.name,
                                 f'● {status_text}',
                                 current_cycle,
                                 patient.protocol or '-',
                                 patient.age if patient.age is not None else '-',
                                 str(patient.diagnosis_date) if patient.diagnosis_date else '-',
                                 risk_text,
                             ))

        self.after(0, self._sync_scrollbar)

    def _on_row_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        self._open_patient(patient_id=patient_db_id)

    def _on_remove_patient(self):
        selected = self.tree.selection()
        if not selected:
            return
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        patient_id_str = self.tree.item(selected[0])['values'][0]
        name = self.tree.item(selected[0])['values'][1]
        confirmed = messagebox.askyesno(
            "Remove Patient",
            f"Remove {name} ({patient_id_str})?\n"
            f"The record is hidden from the list but kept in the audit trail.",
        )
        if confirmed:
            soft_delete_patient(self.app.conn, patient_db_id)
            self.refresh()

    def _on_add_patient(self):
        from views.add_patient_dialog import AddPatientDialog
        dialog = AddPatientDialog(self.winfo_toplevel(), self.app)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh()

    def _on_edit_patient(self):
        selected = self.tree.selection()
        if not selected:
            return
        patient_db_id = int(self.tree.item(selected[0])['tags'][0])
        patient = get_patient_by_db_id(self.app.conn, patient_db_id)
        if patient is None:
            return
        from views.dialogs.edit_patient_dialog import EditPatientDialog
        dialog = EditPatientDialog(self.winfo_toplevel(), self.app, patient)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh()

    def refresh(self):
        self._load_patients()

    def _open_patient(self, patient_id: int):
        from views.dashboard import DashboardView
        self.app.show_frame(DashboardView, patient_id=patient_id)
