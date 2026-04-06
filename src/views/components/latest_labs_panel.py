import tkinter as tk
from datetime import date
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED, FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER
from models import get_latest_lab
from utils.anc_utils import get_anc_status, ANC_THRESHOLD_MILD, ANC_THRESHOLD_MODERATE, ANC_THRESHOLD_SEVERE


class LatestLabsPanel(tk.Frame):
    """Displays the most recent lab draw for a patient.

    Shows date, ANC, WBC, Platelets, and Hemoglobin (if recorded).
    Shows an empty state when no labs exist.

    Public API
    ----------
    load_patient(patient_id) — switch patient context and refresh
    refresh()                — reload latest lab from DB and redraw
    """

    def __init__(self, parent, conn, patient_id=None, on_add_labs=None, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn         = conn
        self.patient_id   = patient_id
        self.on_add_labs  = on_add_labs
        self._content     = None  # holds the current inner frame

        self._build_header()
        self.refresh()
        self._build_legend()

    # ── Header (static) ───────────────────────────────────────────────────────

    def _build_header(self):
        tk.Label(self, text="Latest Labs",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(anchor='w', padx=16, pady=(14, 0))
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x', padx=16, pady=(8, 0))

    # ── Content (rebuilt on each refresh) ────────────────────────────────────

    def _clear_content(self):
        if self._content is not None:
            self._content.destroy()
        self._content = tk.Frame(self, bg=BG_ALT)
        self._content.pack(fill='x', padx=16, pady=12)

    def refresh(self):
        """Reload latest lab from DB and redraw the panel."""
        self._clear_content()

        if self.patient_id is None:
            self._show_empty("No patient selected.")
            return

        lab = get_latest_lab(self.conn, self.patient_id)

        if lab is None:
            self._show_empty("No labs recorded yet.\nAdd labs using the button above.")
            return

        self._show_lab(lab)

    def _show_empty(self, message: str):
        tk.Label(self._content, text=message,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                 justify='left', anchor='w').pack(anchor='w', pady=(4, 8))

        if self.on_add_labs is not None:
            btn = tk.Label(self._content, text="+ Add Labs",
                           font=('Arial', FONT_LABEL, 'bold'),
                           bg=BG_ALT, fg='#4CAF50', cursor='hand2')
            btn.pack(anchor='w')
            btn.bind('<Button-1>', lambda e: self.on_add_labs())
            btn.bind('<Enter>', lambda e: btn.config(fg='#81C784'))
            btn.bind('<Leave>', lambda e: btn.config(fg='#4CAF50'))

    def _show_lab(self, lab):
        # ── Date row ──────────────────────────────────────────────────────────
        date_row = tk.Frame(self._content, bg=BG_ALT)
        date_row.pack(anchor='w', fill='x', pady=(0, 10))

        lab_date = lab.lab_date
        if isinstance(lab_date, str):
            lab_date = date.fromisoformat(lab_date)

        days_diff = (date.today() - lab_date).days
        if days_diff == 0:
            age_str = "Today"
        elif days_diff == 1:
            age_str = "Yesterday"
        else:
            age_str = f"{days_diff} days ago"

        formatted = lab_date.strftime("%b %d, %Y")

        tk.Label(date_row, text=formatted,
                 font=('Arial', FONT_BODY, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(side='left')
        tk.Label(date_row, text=f"  ·  {age_str}",
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                 anchor='w').pack(side='left')

        # ── Value rows ────────────────────────────────────────────────────────
        rows = [
            ("ANC",        lab.anc,        "K/μL",  True),
            ("WBC",        lab.wbc,        "K/μL",  False),
            ("Platelets",  lab.platelets,  "K/μL",  False),
            ("Hemoglobin", lab.hemoglobin, "g/dL",  False),
        ]

        grid = tk.Frame(self._content, bg=BG_ALT)
        grid.pack(anchor='w', fill='x')

        for i, (label, value, unit, required) in enumerate(rows):
            # Skip optional fields that were not recorded
            if value is None and not required:
                continue

            tk.Label(grid, text=label,
                     font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED,
                     anchor='w', width=12).grid(row=i, column=0, sticky='w', pady=3)

            if label == 'ANC' and value is not None:
                anc = get_anc_status(value)
                # Colored dot
                tk.Label(grid, text='●',
                         font=('Arial', FONT_LABEL), bg=BG_ALT, fg=anc['color'],
                         ).grid(row=i, column=1, sticky='w', pady=3)
                # Value in threshold color
                tk.Label(grid, text=f"{value:.1f}",
                         font=('Arial', FONT_BODY, 'bold'), bg=BG_ALT, fg=anc['color'],
                         anchor='w').grid(row=i, column=2, sticky='w', pady=3)
                # Unit (muted)
                tk.Label(grid, text=unit,
                         font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                         anchor='w').grid(row=i, column=3, sticky='w', padx=(6, 0), pady=3)
                # Status label
                tk.Label(grid, text=anc['label'],
                         font=('Arial', FONT_HINT), bg=BG_ALT, fg=anc['color'],
                         anchor='w').grid(row=i, column=4, sticky='w', padx=(10, 0), pady=3)
            else:
                value_str = f"{value:.1f}" if value is not None else "—"
                tk.Label(grid, text=value_str,
                         font=('Arial', FONT_BODY, 'bold'), bg=BG_ALT, fg=FG,
                         anchor='w').grid(row=i, column=1, columnspan=2, sticky='w', pady=3)
                tk.Label(grid, text=unit,
                         font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                         anchor='w').grid(row=i, column=3, sticky='w', padx=(6, 0), pady=3)

    def _build_legend(self):
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x', padx=16, pady=(4, 0))
        legend_row = tk.Frame(self, bg=BG_ALT)
        legend_row.pack(anchor='w', padx=16, pady=(6, 12))

        entries = [
            ('#4CAF50', '≥ 1.5  Normal'),
            ('#FFC107', '1.0–1.5  Mild'),
            ('#FF9800', '0.5–1.0  Moderate'),
            ('#F44336', '< 0.5  Severe'),
        ]
        for color, text in entries:
            tk.Label(legend_row, text='●', font=('Arial', FONT_HINT),
                     bg=BG_ALT, fg=color).pack(side='left')
            tk.Label(legend_row, text=f'{text}    ', font=('Arial', FONT_HINT),
                     bg=BG_ALT, fg=FG_MUTED).pack(side='left')

    # ── Public API ────────────────────────────────────────────────────────────

    def load_patient(self, patient_id):
        """Switch to a different patient and refresh."""
        self.patient_id = patient_id
        self.refresh()
