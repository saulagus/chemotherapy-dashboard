"""Low-ANC alert banner (US-034).

Renders a dismissible red/orange banner at the top of the dashboard when
the patient's latest ANC is below configured thresholds.

Public API
----------
load_patient(patient_db_id)  — switch patient context and refresh
refresh()                    — reload latest ANC and redraw
"""

import tkinter as tk
from datetime import date

from config import get as get_config
from models import get_latest_lab
from utils import BG, FG, FONT_BODY, FONT_HINT, FONT_LABEL


class LowAncBanner(tk.Frame):

    def __init__(self, parent, conn, **kwargs):
        super().__init__(parent, **kwargs)
        self.conn = conn
        self.patient_db_id = None
        self._dismissed: dict = {}
        self._last_lab_id: dict = {}
        self._banner_frame = None
        self.configure(bg=BG)

    def load_patient(self, patient_db_id: int):
        self.patient_db_id = patient_db_id
        self.refresh()

    def refresh(self):
        if self._banner_frame:
            self._banner_frame.destroy()
            self._banner_frame = None

        if self.patient_db_id is None:
            return

        lab = get_latest_lab(self.conn, self.patient_db_id)
        if lab is None or lab.anc is None:
            return

        cfg = get_config().alerts.low_anc_banner
        red_below = cfg.red_below_per_uL / 1000
        orange_below = cfg.orange_below_per_uL / 1000
        dismiss_scope = cfg.dismiss_scope

        anc = lab.anc
        pid = self.patient_db_id

        if anc >= orange_below:
            return

        if dismiss_scope == 'until_next_lab':
            prev_lab_id = self._last_lab_id.get(pid)
            if prev_lab_id is not None and prev_lab_id != lab.id:
                self._dismissed.pop(pid, None)
            self._last_lab_id[pid] = lab.id

        if self._dismissed.get(pid):
            return

        if anc < red_below:
            bg_color = '#B71C1C'
            text = f'ANC critically low: {anc:.2f} K/uL (< {red_below:.1f} K/uL)'
        else:
            bg_color = '#E65100'
            text = f'ANC low: {anc:.2f} K/uL (< {orange_below:.1f} K/uL)'

        self._banner_frame = tk.Frame(self, bg=bg_color)
        self._banner_frame.pack(fill='x')

        tk.Label(self._banner_frame, text=text,
                 font=('Arial', FONT_BODY, 'bold'), bg=bg_color, fg=FG,
                 padx=16, pady=8).pack(side='left')

        dismiss = tk.Label(self._banner_frame, text='Dismiss',
                           font=('Arial', FONT_HINT), bg=bg_color, fg='#FFFFFF',
                           cursor='hand2', padx=16)
        dismiss.pack(side='right', pady=4)
        dismiss.bind('<Button-1>', lambda e: self._on_dismiss())

    def _on_dismiss(self):
        if self.patient_db_id is not None:
            self._dismissed[self.patient_db_id] = True
        if self._banner_frame:
            self._banner_frame.destroy()
            self._banner_frame = None
