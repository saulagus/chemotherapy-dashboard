"""PDF export dialog — audience picker + save-as (Sprint 9 — US-035)."""

import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)


class ExportPdfDialog(tk.Toplevel):
    """Audience radio + save-as dialog for PDF export.

    Audiences that have enabled=false in config are shown but disabled.
    """

    def __init__(self, parent, conn, patient_id: int, patient_str_id: str, config):
        super().__init__(parent)
        self.conn          = conn
        self.patient_id    = patient_id
        self.patient_str_id = patient_str_id
        self.config        = config

        self.title("Export PDF")
        self.configure(bg=BG)
        self.geometry('400x280')
        self.resizable(False, False)
        self.grab_set()

        self._audience_var = tk.StringVar(value='oncologist')
        self._build()

    def _build(self):
        tk.Label(self, text="Export Patient Summary PDF",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        body = tk.Frame(self, bg=BG, padx=16, pady=12)
        body.pack(fill='both', expand=True)

        tk.Label(body, text="Select audience:",
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED).pack(anchor='w')

        audiences_cfg = self.config.reports.audiences
        audiences = [
            ('oncologist', 'Oncologist',  audiences_cfg.oncologist.enabled),
            ('pcp',        'PCP / Referring Physician', audiences_cfg.pcp.enabled),
            ('patient',    'Patient (plain language)',  audiences_cfg.patient.enabled),
        ]

        for value, label, enabled in audiences:
            rb = tk.Radiobutton(
                body, text=label,
                variable=self._audience_var, value=value,
                font=('Arial', FONT_BODY), bg=BG, fg=FG if enabled else FG_MUTED,
                selectcolor=BG_ALT, activebackground=BG, activeforeground=FG,
                state='normal' if enabled else 'disabled',
            )
            rb.pack(anchor='w', pady=2)

        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill='x', pady=(12, 0), side='bottom')

        cancel_btn = tk.Label(btn_frame, text="Cancel",
                              font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED, cursor='hand2')
        cancel_btn.pack(side='right', padx=(8, 0))
        cancel_btn.bind('<Button-1>', lambda e: self.destroy())

        export_btn = tk.Label(btn_frame, text="Export PDF",
                              font=('Arial', FONT_BODY, 'bold'), bg='#2d5a8e', fg=FG,
                              padx=12, pady=6, cursor='hand2')
        export_btn.pack(side='right')
        export_btn.bind('<Button-1>', lambda e: self._on_export())

    def _on_export(self):
        audience = self._audience_var.get()
        today = date.today()
        default_name = f"summary_{self.patient_str_id}_{audience}_{today.isoformat()}.pdf"

        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension='.pdf',
            filetypes=[('PDF files', '*.pdf')],
            initialfile=default_name,
            title="Save PDF as…",
        )
        if not path:
            return

        try:
            from services.exports import export_patient_pdf
            result = export_patient_pdf(
                self.conn, self.patient_id, audience, path, self.config, today
            )
            messagebox.showinfo(
                "Export Complete",
                f"PDF saved ({result.size_bytes // 1024} KB)\n{os.path.basename(path)}",
                parent=self,
            )
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc), parent=self)
