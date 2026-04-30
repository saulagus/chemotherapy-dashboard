"""Pre-cycle safety checklist dialog (US-033).

Runs before the cycle-completion dialog. Shows the result of every
pre-cycle rule, allows the nurse to attest infection-free status,
and gates the save on checklist outcome.

Public API
----------
PrecycleChecklistDialog(parent, conn, patient_db_id, cycle_number, on_proceed, on_cancel)
"""

import tkinter as tk
from datetime import date

from clinical.precycle import RuleResult
from config import get as get_config
from services.audit import current_actor, write_audit
from services.checklist import evaluate, gather_inputs
from clinical.precycle import run_checklist
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED, FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL

_STATUS_ICON = {
    'pass':       '✓',
    'advisory':   'ℹ',
    'soft_block': '⚠',
    'hard_block': '⛔',
}

_STATUS_COLOR = {
    'pass':       '#4CAF50',
    'advisory':   '#2196F3',
    'soft_block': '#FF9800',
    'hard_block': '#F44336',
}


class PrecycleChecklistDialog(tk.Toplevel):

    def __init__(self, parent, conn, patient_db_id, cycle_number,
                 on_proceed=None, on_cancel=None):
        super().__init__(parent)
        self.conn = conn
        self.patient_db_id = patient_db_id
        self.cycle_number = cycle_number
        self.on_proceed = on_proceed
        self.on_cancel = on_cancel
        self._infection_var = tk.BooleanVar(value=False)

        self.title(f'Pre-Cycle Safety Checklist — Cycle {cycle_number}')
        self.configure(bg=BG)
        self.resizable(False, True)
        self.grab_set()
        self.transient(parent)
        self.minsize(540, 400)

        self._result = None
        self._build_ui()
        self._run_checklist()
        self._center()
        self.protocol('WM_DELETE_WINDOW', self._cancel)

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = self.winfo_rootx() + (self.master.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.master.winfo_height() - h) // 2
        self.geometry(f'+{max(0,x)}+{max(0,y)}')

    def _build_ui(self):
        phase = 'AC' if self.cycle_number <= 4 else 'T'

        header = tk.Frame(self, bg=BG_ALT, padx=20, pady=14)
        header.pack(fill='x')
        from models import get_patient_by_db_id
        patient = get_patient_by_db_id(self.conn, self.patient_db_id)
        name = patient.name if patient else '—'
        tk.Label(header, text=f'{name} — Cycle {self.cycle_number} ({phase})',
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(anchor='w')
        tk.Label(header, text=f'Planned: {date.today().isoformat()}',
                 font=('Arial', FONT_LABEL), bg=BG_ALT, fg=FG_MUTED).pack(anchor='w')

        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        # Buttons pinned bottom
        btn_sep = tk.Frame(self, bg=SEPARATOR, height=1)
        btn_sep.pack(side='bottom', fill='x')
        self._btn_row = tk.Frame(self, bg=BG, padx=24, pady=14)
        self._btn_row.pack(side='bottom', fill='x')

        cancel_btn = tk.Label(self._btn_row, text='Cancel',
                              font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED,
                              cursor='hand2', padx=10)
        cancel_btn.pack(side='right')
        cancel_btn.bind('<Button-1>', lambda e: self._cancel())

        self._proceed_btn = tk.Label(self._btn_row, text='Proceed',
                                     font=('Arial', FONT_BODY, 'bold'),
                                     bg='#388E3C', fg='#FFFFFF',
                                     cursor='hand2', padx=14, pady=6)
        self._proceed_btn.pack(side='right', padx=(0, 12))
        self._proceed_btn.bind('<Button-1>', lambda e: self._on_proceed())

        # Body
        body = tk.Frame(self, bg=BG, padx=24, pady=16)
        body.pack(fill='both', expand=True)

        # Infection attestation checkbox
        attest_frame = tk.Frame(body, bg=BG)
        attest_frame.pack(fill='x', pady=(0, 12))
        cb = tk.Checkbutton(attest_frame, variable=self._infection_var,
                            text='Patient is free of active infection (nurse attestation)',
                            font=('Arial', FONT_BODY), bg=BG, fg=FG,
                            selectcolor=BG_ALT, activebackground=BG,
                            activeforeground=FG,
                            command=self._run_checklist)
        cb.pack(anchor='w')

        tk.Frame(body, bg=SEPARATOR, height=1).pack(fill='x', pady=(0, 8))

        self._rules_frame = tk.Frame(body, bg=BG)
        self._rules_frame.pack(fill='both', expand=True)

        self._override_frame = tk.Frame(body, bg=BG)
        self._override_frame.pack(fill='x', pady=(8, 0))

    def _run_checklist(self):
        inputs = gather_inputs(
            self.conn, self.patient_db_id, self.cycle_number,
            date.today(), self._infection_var.get(),
        )
        cfg = get_config()
        config_dict = {
            'precycle': cfg.precycle.model_dump(),
            'labs': cfg.labs.model_dump(),
        }
        self._result = run_checklist(inputs, config_dict)
        self._render_rules()
        self._update_proceed_button()

    def _render_rules(self):
        for w in self._rules_frame.winfo_children():
            w.destroy()
        for w in self._override_frame.winfo_children():
            w.destroy()

        if self._result is None:
            return

        for rule in self._result.rules:
            self._render_rule_row(rule)

        if self._result.worst_status in ('soft_block',):
            self._render_override_input()
        elif self._result.worst_status == 'hard_block':
            tk.Label(self._override_frame,
                     text='One or more rules impose a hard block. Cannot proceed.',
                     font=('Arial', FONT_LABEL), bg=BG, fg='#F44336',
                     anchor='w').pack(anchor='w', pady=(4, 0))

    def _render_rule_row(self, rule: RuleResult):
        row = tk.Frame(self._rules_frame, bg=BG)
        row.pack(fill='x', pady=3)

        icon = _STATUS_ICON.get(rule.status, '?')
        color = _STATUS_COLOR.get(rule.status, FG)

        tk.Label(row, text=icon, font=('Arial', FONT_BODY),
                 bg=BG, fg=color, width=3).pack(side='left')
        tk.Label(row, text=rule.message, font=('Arial', FONT_BODY),
                 bg=BG, fg=FG, anchor='w', wraplength=420).pack(side='left', fill='x')

    def _render_override_input(self):
        tk.Label(self._override_frame,
                 text='Override reason (minimum 20 characters):',
                 font=('Arial', FONT_LABEL), bg=BG, fg=FG_MUTED,
                 anchor='w').pack(anchor='w')

        self._override_var = tk.StringVar()
        self._char_lbl = tk.Label(self._override_frame, text='0 / 20 min',
                                   font=('Arial', FONT_HINT), bg=BG, fg=FG_MUTED,
                                   anchor='e')
        self._char_lbl.pack(anchor='e')

        def _on_key(*_):
            n = len(self._override_var.get().strip())
            self._char_lbl.config(text=f'{n} / 20 min',
                                   fg='#4CAF50' if n >= 20 else FG_MUTED)

        self._override_var.trace_add('write', _on_key)

        entry = tk.Entry(self._override_frame, textvariable=self._override_var,
                         font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG,
                         insertbackground=FG, relief='flat',
                         highlightbackground=SEPARATOR, highlightthickness=1)
        entry.pack(fill='x', pady=(4, 0))

        self._override_err = tk.Label(self._override_frame, text='',
                                       font=('Arial', FONT_HINT), bg=BG, fg='#F44336',
                                       anchor='w')
        self._override_err.pack(anchor='w')

    def _update_proceed_button(self):
        if self._result is None:
            return
        if self._result.worst_status == 'hard_block':
            self._proceed_btn.config(bg='#555555', cursor='arrow')
        elif self._result.worst_status == 'soft_block':
            self._proceed_btn.config(bg='#FF9800', cursor='hand2')
        else:
            self._proceed_btn.config(bg='#388E3C', cursor='hand2')

    def _on_proceed(self):
        if self._result is None:
            return

        if self._result.worst_status == 'hard_block':
            return

        if self._result.worst_status == 'soft_block':
            reason = self._override_var.get().strip() if hasattr(self, '_override_var') else ''
            if len(reason) < 20:
                if hasattr(self, '_override_err'):
                    self._override_err.config(text='Override reason must be at least 20 characters.')
                return
            overridden = [r.rule_id for r in self._result.rules
                          if r.status in ('soft_block', 'hard_block')]
            try:
                write_audit(
                    self.conn, 'cycle', None, 'checklist_override',
                    after={'rules': overridden, 'reason': reason,
                           'patient_id': self.patient_db_id,
                           'cycle_number': self.cycle_number},
                    actor=current_actor(),
                )
                self.conn.commit()
            except Exception:
                pass

        if self.on_proceed:
            self.on_proceed()
        self.destroy()

    def _cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.destroy()
