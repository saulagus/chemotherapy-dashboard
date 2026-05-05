"""CSV lab export dialog — date range + save-as (Sprint 9 — US-037)."""

import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)


class ExportCsvDialog(tk.Toplevel):
    """Date-range picker + save-as dialog for CSV lab export."""

    def __init__(self, parent, conn, patient_id: int, patient_str_id: str, config):
        super().__init__(parent)
        self.conn           = conn
        self.patient_id     = patient_id
        self.patient_str_id = patient_str_id
        self.config         = config

        self.title("Export Labs CSV")
        self.configure(bg=BG)
        self.geometry('360x240')
        self.resizable(False, False)
        self.grab_set()

        self._from_var = tk.StringVar(value='')
        self._to_var   = tk.StringVar(value='')
        self._build()

    def _build(self):
        tk.Label(self, text="Export Lab Results (CSV)",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        body = tk.Frame(self, bg=BG, padx=16, pady=12)
        body.pack(fill='both', expand=True)

        tk.Label(body, text="Date range (YYYY-MM-DD, leave blank = all):",
                 font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED).pack(anchor='w')

        row_from = tk.Frame(body, bg=BG)
        row_from.pack(fill='x', pady=(4, 0))
        tk.Label(row_from, text="From:", font=('Arial', FONT_LABEL), bg=BG, fg=FG,
                 width=5, anchor='w').pack(side='left')
        tk.Entry(row_from, textvariable=self._from_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                 insertbackground=FG, width=14).pack(side='left', padx=(4, 0))

        row_to = tk.Frame(body, bg=BG)
        row_to.pack(fill='x', pady=(4, 0))
        tk.Label(row_to, text="To:", font=('Arial', FONT_LABEL), bg=BG, fg=FG,
                 width=5, anchor='w').pack(side='left')
        tk.Entry(row_to, textvariable=self._to_var,
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                 insertbackground=FG, width=14).pack(side='left', padx=(4, 0))

        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill='x', pady=(14, 0), side='bottom')

        cancel_btn = tk.Label(btn_frame, text="Cancel",
                              font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED, cursor='hand2')
        cancel_btn.pack(side='right', padx=(8, 0))
        cancel_btn.bind('<Button-1>', lambda e: self.destroy())

        export_btn = tk.Label(btn_frame, text="Export CSV",
                              font=('Arial', FONT_BODY, 'bold'), bg='#2d5a8e', fg=FG,
                              padx=12, pady=6, cursor='hand2')
        export_btn.pack(side='right')
        export_btn.bind('<Button-1>', lambda e: self._on_export())

    def _on_export(self):
        from_date = self._parse_date(self._from_var.get())
        to_date   = self._parse_date(self._to_var.get())

        today = date.today()
        from reports.csv_labs import build_csv_filename
        default_name = build_csv_filename(self.patient_str_id, self.config, today)

        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')],
            initialfile=default_name,
            title="Save CSV as…",
        )
        if not path:
            return

        try:
            from services.exports import export_patient_csv
            result = export_patient_csv(
                self.conn, self.patient_id, path, self.config, today,
                from_date=from_date, to_date=to_date,
            )
            messagebox.showinfo(
                "Export Complete",
                f"CSV saved ({result.size_bytes} bytes)\n{os.path.basename(path)}",
                parent=self,
            )
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc), parent=self)

    def _parse_date(self, val: str):
        val = val.strip()
        if not val:
            return None
        try:
            return date.fromisoformat(val)
        except ValueError:
            messagebox.showerror("Invalid Date", f"Date format must be YYYY-MM-DD: {val!r}", parent=self)
            return None
