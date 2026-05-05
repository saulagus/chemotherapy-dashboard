"""Dose modification history panel (Sprint 9 — US-036).

Collapsible section mounted below the toxicity panel.
Columns: Cycle · Date · Agent · % · Reason · Actor
Sortable by cycle number (default) or date.
"""

import tkinter as tk

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)


class DoseModHistoryPanel(tk.Frame):
    """Collapsible dose modification history panel.

    Public API
    ----------
    load_patient(patient_db_id)  — switch patient context and refresh
    refresh()                    — reload from DB and redraw
    """

    def __init__(self, parent, conn, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn           = conn
        self.patient_db_id  = None
        self._expanded      = False
        self._sort_by       = 'cycle'
        self._content       = None

        self._build_header()
        self._content_frame = tk.Frame(self, bg=BG_ALT)
        self._content_frame.pack(fill='x', padx=16)
        self.refresh()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self, bg=BG_ALT, padx=16)
        header.pack(fill='x', pady=(14, 0))

        self._toggle_label = tk.Label(
            header,
            text="▶  Dose Modifications",
            font=('Arial', FONT_HEADER, 'bold'),
            bg=BG_ALT, fg=FG, cursor='hand2',
        )
        self._toggle_label.pack(side='left')
        self._toggle_label.bind('<Button-1>', lambda e: self._toggle())

    # ── Public API ────────────────────────────────────────────────────────────

    def load_patient(self, patient_db_id: int):
        self.patient_db_id = patient_db_id
        self.refresh()

    def refresh(self):
        for w in self._content_frame.winfo_children():
            w.destroy()

        if not self._expanded or self.patient_db_id is None:
            return

        self._render_content()

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle(self):
        self._expanded = not self._expanded
        arrow = '▼' if self._expanded else '▶'
        self._toggle_label.config(text=f"{arrow}  Dose Modifications")
        self.refresh()

    # ── Content ───────────────────────────────────────────────────────────────

    def _render_content(self):
        from services.dose_modifications import list_for_patient

        mods = list_for_patient(self.conn, self.patient_db_id)

        if not mods:
            tk.Label(
                self._content_frame,
                text="No dose modifications recorded for this patient.",
                font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
            ).pack(anchor='w', pady=(4, 8))
            return

        # Sort
        if self._sort_by == 'date':
            mods = sorted(mods, key=lambda m: (m.date or ''), reverse=True)
        else:
            mods = sorted(mods, key=lambda m: m.cycle_number)

        # Column headers + sort buttons
        hdr = tk.Frame(self._content_frame, bg=BG_ALT)
        hdr.pack(fill='x', pady=(4, 2))

        cols = [('Cycle', 60, 'cycle'), ('Date', 90, 'date'),
                ('Agent', 90, None), ('%', 50, None),
                ('Reason', 180, None), ('Actor', 80, None)]

        for col_name, col_w, sort_key in cols:
            lbl_kw = dict(
                text=col_name,
                font=('Arial', FONT_LABEL, 'bold'),
                bg=BG_ALT, fg=FG_MUTED, width=col_w // 7,
                anchor='w',
            )
            if sort_key:
                lbl = tk.Label(hdr, cursor='hand2', **lbl_kw)
                lbl.bind('<Button-1>', lambda e, k=sort_key: self._set_sort(k))
            else:
                lbl = tk.Label(hdr, **lbl_kw)
            lbl.pack(side='left', padx=(0, 4))

        tk.Frame(self._content_frame, bg=SEPARATOR, height=1).pack(fill='x', pady=(2, 4))

        for mod in mods:
            row = tk.Frame(self._content_frame, bg=BG_ALT)
            row.pack(fill='x', pady=1)

            d = mod.date
            date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d) if d else '—'
            agent = mod.agent or '—'
            reason = (mod.reason or '—')[:30]
            actor = mod.actor or '—'

            values = [
                (f"C{mod.cycle_number}", 60),
                (date_str, 90),
                (agent, 90),
                (f"{mod.dose_pct:.0f}%", 50),
                (reason, 180),
                (actor, 80),
            ]
            for text, w in values:
                tk.Label(row, text=text,
                         font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                         width=w // 7, anchor='w').pack(side='left', padx=(0, 4))

        tk.Frame(self._content_frame, bg=SEPARATOR, height=1).pack(fill='x', pady=(4, 8))

    def _set_sort(self, key: str):
        self._sort_by = key
        self.refresh()
