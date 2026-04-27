import tkinter as tk
from datetime import date
from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_DETAIL, FONT_HINT, FONT_LABEL, FONT_NAME)

_BADGE_TEXT = {
    'green':     '● Green',
    'yellow':    '⚠ Yellow',
    'red':       '⛔ Red',
    'hard_stop': '⛔ STOP',
}
_BADGE_COLOR = {
    'green':     '#4CAF50',
    'yellow':    '#FFC107',
    'red':       '#F44336',
    'hard_stop': '#F44336',
}


class PatientHeader(tk.Frame):
    """Patient identity header shown at the top of the dashboard.

    Displays the back button, add-labs button, patient name, and
    detail row (ID, protocol, start date).

    Public API
    ----------
    update_display(patient) — refresh all labels from a Patient object or None
    """

    def __init__(self, parent, controller, on_add_labs=None,
                 on_show_history=None, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.controller       = controller
        self.on_add_labs      = on_add_labs
        self.on_show_history  = on_show_history
        self._build_ui()

    def _build_ui(self):
        # ── Action row: back (left) + add labs (right) ────────────────────────
        action_row = tk.Frame(self, bg=BG_ALT, padx=20, pady=10)
        action_row.pack(fill='x')

        back_btn = tk.Label(action_row, text="\u2190 Back to List",
                            font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                            cursor='hand2')
        back_btn.pack(side='left')
        back_btn.bind('<Button-1>', lambda e: self._go_back())
        back_btn.bind('<Enter>', lambda e: back_btn.config(fg=FG))
        back_btn.bind('<Leave>', lambda e: back_btn.config(fg=FG_MUTED))

        if self.on_add_labs is not None:
            add_btn = tk.Label(action_row, text="+ Add Labs",
                               font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                               cursor='hand2')
            add_btn.pack(side='right')
            add_btn.bind('<Button-1>', lambda e: self.on_add_labs())
            add_btn.bind('<Enter>', lambda e: add_btn.config(fg=FG))
            add_btn.bind('<Leave>', lambda e: add_btn.config(fg=FG_MUTED))

        if self.on_show_history is not None:
            hist_btn = tk.Label(action_row, text="History",
                                font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG_MUTED,
                                cursor='hand2', padx=12)
            hist_btn.pack(side='right')
            hist_btn.bind('<Button-1>', lambda e: self.on_show_history())
            hist_btn.bind('<Enter>', lambda e: hist_btn.config(fg=FG))
            hist_btn.bind('<Leave>', lambda e: hist_btn.config(fg=FG_MUTED))

        # ── Name + detail block ───────────────────────────────────────────────
        info_frame = tk.Frame(self, bg=BG_ALT, padx=20)
        info_frame.pack(fill='x', anchor='w', pady=(0, 16))

        name_row = tk.Frame(info_frame, bg=BG_ALT)
        name_row.pack(anchor='w', fill='x')

        self._name_label = tk.Label(name_row, text="",
                                    font=('Arial', FONT_NAME, 'bold'),
                                    bg=BG_ALT, fg=FG, anchor='w')
        self._name_label.pack(side='left')

        self._badge_label = tk.Label(name_row, text="",
                                     font=('Arial', FONT_LABEL, 'bold'),
                                     bg=BG_ALT, fg=FG_MUTED, anchor='w',
                                     padx=12)
        self._badge_label.pack(side='left', pady=(6, 0))

        self._detail_label = tk.Label(info_frame, text="",
                                      font=('Arial', FONT_DETAIL),
                                      bg=BG_ALT, fg=FG_MUTED, anchor='w')
        self._detail_label.pack(anchor='w', pady=(4, 0))

    def update_display(self, patient):
        """Refresh header labels from a Patient object. Pass None to clear."""
        if patient is None:
            self._name_label.config(text="")
            self._detail_label.config(text="")
            return

        self._name_label.config(text=patient.name)

        pid      = f"ID: {patient.patient_id}"
        protocol = patient.protocol or "\u2014"
        started  = self._format_date(patient.start_date)

        self._detail_label.config(
            text=f"{pid}  \u2502  {protocol}  \u2502  Started: {started}"
        )

    def update_cumulative_badge(self, summary):
        """Show or hide the cumulative dose risk badge next to the patient name.

        Pass a CumulativeSummary (from services.cycles.cumulative_dose) or None
        to clear the badge.
        """
        if summary is None:
            self._badge_label.config(text='', fg=FG_MUTED)
            return
        text  = _BADGE_TEXT.get(summary.status, '')
        color = _BADGE_COLOR.get(summary.status, FG_MUTED)
        self._badge_label.config(text=text, fg=color)

    def _format_date(self, d):
        if d is None:
            return "\u2014"
        if isinstance(d, str):
            d = date.fromisoformat(d)
        return d.strftime("%b %d, %Y")

    def _go_back(self):
        from views.patient_list import PatientListView
        self.controller.show_frame(PatientListView)
