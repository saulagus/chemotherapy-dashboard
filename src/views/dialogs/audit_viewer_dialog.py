"""Patient audit history viewer.

Shows every audit_log row touching a patient (the patient row itself plus
all of its cycles and labs) newest-first, with a per-field before/after
diff for update actions and a full snapshot for create/delete.
"""

import tkinter as tk
from datetime import datetime

from services.audit import get_audit_for_patient
from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER)


ENTITY_LABELS = {
    'patient': 'Patient',
    'cycle':   'Cycle',
    'lab':     'Lab',
}

ACTION_COLORS = {
    'create':      '#4CAF50',
    'update':      '#FFC107',
    'delete':      '#F44336',
    'soft_delete': '#FF9800',
    'restore':     '#4CAF50',
}


class AuditViewerDialog(tk.Toplevel):
    """Modal dialog listing the full audit trail for one patient."""

    def __init__(self, parent, conn, patient):
        super().__init__(parent)
        self.conn = conn
        self.patient = patient
        self._build_ui()
        self._make_modal(parent)
        self._load_rows()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _make_modal(self, parent):
        self.title(f"History — {self.patient.name}")
        self.configure(bg=BG)
        self.update_idletasks()
        w, h = 640, 560
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG, padx=16, pady=12)
        header.pack(fill='x')
        tk.Label(header, text='Audit History',
                 font=('Arial', FONT_HEADER, 'bold'),
                 bg=BG, fg=FG, anchor='w').pack(anchor='w')
        tk.Label(header,
                 text='All changes to this patient, cycles, and labs.',
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                 anchor='w').pack(anchor='w', pady=(2, 0))
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Scrollable body
        body = tk.Frame(self, bg=BG)
        body.pack(fill='both', expand=True)

        self._canvas = tk.Canvas(body, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(body, orient='vertical',
                              command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)

        self._rows_frame = tk.Frame(self._canvas, bg=BG)
        self._rows_window = self._canvas.create_window(
            (0, 0), window=self._rows_frame, anchor='nw')
        self._rows_frame.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))
        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(
                self._rows_window, width=e.width))

        # Footer
        footer = tk.Frame(self, bg=BG, padx=16, pady=10)
        footer.pack(fill='x')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(
            fill='x', before=footer)
        close = tk.Label(footer, text='Close',
                         font=('Arial', FONT_LABEL, 'bold'),
                         bg=BG, fg=FG_MUTED, cursor='hand2')
        close.pack(side='right')
        close.bind('<Button-1>', lambda e: self.destroy())
        close.bind('<Enter>', lambda e: close.config(fg=FG))
        close.bind('<Leave>', lambda e: close.config(fg=FG_MUTED))

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_rows(self):
        rows = get_audit_for_patient(self.conn, self.patient.id)
        if not rows:
            tk.Label(self._rows_frame,
                     text='No audit history recorded for this patient yet.',
                     font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED,
                     anchor='w').pack(anchor='w', padx=16, pady=16)
            return
        for row in rows:
            self._render_row(row)

    def _render_row(self, row):
        card = tk.Frame(self._rows_frame, bg=BG_ALT, padx=12, pady=10)
        card.pack(fill='x', padx=12, pady=(8, 0))

        # Top line: action badge + entity + timestamp + actor
        top = tk.Frame(card, bg=BG_ALT)
        top.pack(fill='x')

        action = row['action']
        color = ACTION_COLORS.get(action, FG_MUTED)
        tk.Label(top, text=action.upper().replace('_', ' '),
                 font=('Arial', FONT_HINT, 'bold'),
                 bg=BG_ALT, fg=color).pack(side='left')
        entity_label = ENTITY_LABELS.get(row['entity'], row['entity'])
        tk.Label(top, text=f"  {entity_label} #{row['entity_id']}",
                 font=('Arial', FONT_LABEL, 'bold'),
                 bg=BG_ALT, fg=FG).pack(side='left')

        tk.Label(top, text=row['actor'] or '—',
                 font=('Arial', FONT_HINT), bg=BG_ALT,
                 fg=FG_MUTED).pack(side='right')
        tk.Label(top, text=self._format_ts(row['ts']) + '   ',
                 font=('Arial', FONT_HINT), bg=BG_ALT,
                 fg=FG_MUTED).pack(side='right')

        # Body: diff or snapshot
        body = tk.Frame(card, bg=BG_ALT)
        body.pack(fill='x', pady=(6, 0))

        if action == 'update':
            self._render_diff(body, row['before'] or {}, row['after'] or {})
        else:
            snap = row['after'] if row['after'] is not None else row['before']
            self._render_snapshot(body, snap or {})

    def _render_diff(self, parent, before: dict, after: dict):
        keys = sorted(set(before) | set(after))
        changed = [k for k in keys if before.get(k) != after.get(k)]
        if not changed:
            tk.Label(parent, text='(no field changes recorded)',
                     font=('Arial', FONT_HINT), bg=BG_ALT,
                     fg=FG_MUTED, anchor='w').pack(anchor='w')
            return
        for k in changed:
            if k == 'id':
                continue
            row = tk.Frame(parent, bg=BG_ALT)
            row.pack(fill='x', pady=1)
            tk.Label(row, text=f'{k}:', width=16,
                     font=('Arial', FONT_HINT, 'bold'),
                     bg=BG_ALT, fg=FG_MUTED,
                     anchor='w').pack(side='left')
            tk.Label(row, text=self._fmt_val(before.get(k)),
                     font=('Arial', FONT_HINT), bg=BG_ALT,
                     fg='#F44336', anchor='w').pack(side='left')
            tk.Label(row, text='  →  ',
                     font=('Arial', FONT_HINT), bg=BG_ALT,
                     fg=FG_MUTED).pack(side='left')
            tk.Label(row, text=self._fmt_val(after.get(k)),
                     font=('Arial', FONT_HINT), bg=BG_ALT,
                     fg='#4CAF50', anchor='w').pack(side='left')

    def _render_snapshot(self, parent, snap: dict):
        # Compact key: value listing; skip ids and Nones for readability.
        items = [(k, v) for k, v in snap.items()
                 if k != 'id' and v is not None]
        if not items:
            tk.Label(parent, text='(empty)',
                     font=('Arial', FONT_HINT), bg=BG_ALT,
                     fg=FG_MUTED, anchor='w').pack(anchor='w')
            return
        for k, v in items:
            row = tk.Frame(parent, bg=BG_ALT)
            row.pack(fill='x', pady=1)
            tk.Label(row, text=f'{k}:', width=16,
                     font=('Arial', FONT_HINT, 'bold'),
                     bg=BG_ALT, fg=FG_MUTED,
                     anchor='w').pack(side='left')
            tk.Label(row, text=self._fmt_val(v),
                     font=('Arial', FONT_HINT), bg=BG_ALT,
                     fg=FG, anchor='w').pack(side='left')

    # ── Formatting helpers ────────────────────────────────────────────────────

    @staticmethod
    def _fmt_val(v):
        if v is None:
            return '—'
        if isinstance(v, float):
            return f'{v:g}'
        return str(v)

    @staticmethod
    def _format_ts(ts):
        if ts is None:
            return ''
        # SQLite CURRENT_TIMESTAMP comes back as 'YYYY-MM-DD HH:MM:SS'.
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
            try:
                return datetime.strptime(str(ts), fmt).strftime('%b %d, %Y  %H:%M')
            except ValueError:
                continue
        return str(ts)
