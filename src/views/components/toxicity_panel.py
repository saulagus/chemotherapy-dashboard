"""Toxicity panel — combined Sprint 7 toxicity tracking surface (US-027–030).

Day 23: neuropathy section only (stub rows for reactions, G-CSF, symptoms).
Day 29: all four sections fully wired.

Public API
----------
load_patient(patient_db_id)  — switch patient context and refresh
refresh()                    — reload from DB and redraw
"""

import tkinter as tk
from tkinter import messagebox

from utils import (BG, BG_ALT, SEPARATOR, FG, FG_MUTED,
                   FONT_BODY, FONT_HEADER, FONT_HINT, FONT_LABEL)
from clinical.neuropathy import effective_grade, recommended_action
from clinical.infusion_reactions import rechallenge_advice
from services.neuropathy import (
    NeuropathyAssessment,
    delete_neuropathy,
    latest_neuropathy,
    list_neuropathy,
)
from services.infusion_reactions import (
    InfusionReaction,
    delete_reaction,
    latest_reaction,
    list_reactions,
)
from services.gcsf import (
    GcsfAdmin,
    delete_gcsf,
    latest_gcsf,
    list_gcsf,
)
from services.symptoms import (
    SymptomEntry,
    delete_symptom,
    latest_cycle_symptoms,
    list_symptoms,
)
from config import get as get_config

_NEUROPATHY_COLOR = {
    0: '#4CAF50',  # G0 — green
    1: '#4CAF50',  # G1 — green
    2: '#FFC107',  # G2 — yellow
    3: '#FF9800',  # G3 — orange
    4: '#F44336',  # G4 — red
}


class ToxicityPanel(tk.Frame):
    """Combined toxicity panel shown below CardiotoxicityPanel in the dashboard.

    Public API
    ----------
    load_patient(patient_db_id)  — switch to a patient by integer DB id
    refresh()                    — reload from DB and redraw
    """

    def __init__(self, parent, conn, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn            = conn
        self.patient_db_id   = None      # integer DB id
        self.patient_str_id  = None      # string 'PT-001'
        self._content        = None

        self._build_header()
        self.refresh()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        header_row = tk.Frame(self, bg=BG_ALT, padx=16)
        header_row.pack(fill='x', pady=(14, 0))
        tk.Label(header_row, text="Toxicity Tracking",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG).pack(side='left')

    # ── Public API ────────────────────────────────────────────────────────────

    def load_patient(self, patient_db_id: int):
        from models import get_patient_by_db_id
        self.patient_db_id  = patient_db_id
        patient = get_patient_by_db_id(self.conn, patient_db_id)
        self.patient_str_id = patient.patient_id if patient else None
        self.refresh()

    def refresh(self):
        if self._content:
            self._content.destroy()
        self._content = tk.Frame(self, bg=BG_ALT)
        self._content.pack(fill='both', expand=True, padx=16, pady=(8, 16))

        if not self.patient_str_id:
            tk.Label(self._content, text="No patient selected.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                     ).pack(anchor='w', pady=8)
            return

        self._render_neuropathy()
        self._render_infusion_reactions()
        self._render_gcsf()
        self._render_symptoms()

    # ── Neuropathy section ────────────────────────────────────────────────────

    def _render_neuropathy(self):
        section = self._section_frame("Neuropathy (CTCAE v5)")
        latest  = latest_neuropathy(self.conn, self.patient_str_id)

        if latest is None:
            row = tk.Frame(section, bg=BG_ALT)
            row.pack(fill='x', pady=(4, 0))
            tk.Label(row, text="No assessments recorded.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(side='left')
            add = tk.Label(row, text="+ Add",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            add.pack(side='left', padx=(8, 0))
            add.bind('<Button-1>', lambda e: self._open_add_neuropathy())
        else:
            self._render_neuropathy_latest(section, latest)

        self._section_action_row(section, latest,
                                 on_add=self._open_add_neuropathy,
                                 on_history=self._open_neuropathy_history)

    def _render_neuropathy_latest(self, section, assessment: NeuropathyAssessment):
        cfg   = get_config().toxicity.model_dump()
        grade = effective_grade(assessment.sensory_grade, assessment.motor_grade, cfg)
        try:
            action = recommended_action(grade, cfg)
            advisory = action.advisory_text
        except Exception:
            advisory = ""

        color = _NEUROPATHY_COLOR.get(grade, FG)
        d     = assessment.assessment_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)

        summary_row = tk.Frame(section, bg=BG_ALT)
        summary_row.pack(fill='x', pady=(4, 0))

        tk.Label(summary_row,
                 text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'),
                 bg=BG_ALT, fg=color).pack(side='left')
        tk.Label(summary_row,
                 text=f"  Sensory G{assessment.sensory_grade} / Motor G{assessment.motor_grade}"
                      f"  ·  {date_str}",
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG).pack(side='left')

        if advisory:
            tk.Label(section, text=advisory,
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                     anchor='w', wraplength=400).pack(fill='x', pady=(2, 0))

    def _open_add_neuropathy(self):
        if not self.patient_db_id:
            return
        from views.dialogs.neuropathy_dialog import NeuropathyDialog
        NeuropathyDialog(self, self.conn, self.patient_db_id, on_save=self.refresh)

    def _open_neuropathy_history(self):
        if not self.patient_str_id:
            return
        _NeuropathyHistoryWindow(self, self.conn, self.patient_db_id,
                                 self.patient_str_id, on_change=self.refresh)

    # ── Infusion reactions section ────────────────────────────────────────────

    def _render_infusion_reactions(self):
        section = self._section_frame("Infusion Reactions")
        latest  = latest_reaction(self.conn, self.patient_str_id)

        if latest is None:
            row = tk.Frame(section, bg=BG_ALT)
            row.pack(fill='x', pady=(4, 0))
            tk.Label(row, text="No reactions logged.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(side='left')
            add = tk.Label(row, text="+ Add",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            add.pack(side='left', padx=(8, 0))
            add.bind('<Button-1>', lambda e: self._open_add_reaction())
        else:
            self._render_reaction_latest(section, latest)

        self._section_action_row(section, latest,
                                 on_add=self._open_add_reaction,
                                 on_history=self._open_reaction_history)

    def _render_reaction_latest(self, section, reaction: InfusionReaction):
        cfg    = get_config().toxicity.model_dump()
        grade  = reaction.severity_grade
        color  = {1: '#4CAF50', 2: '#FFC107', 3: '#FF9800', 4: '#F44336'}.get(grade, FG)

        summary_row = tk.Frame(section, bg=BG_ALT)
        summary_row.pack(fill='x', pady=(4, 0))

        tk.Label(summary_row,
                 text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG_ALT, fg=color).pack(side='left')
        tk.Label(summary_row,
                 text=f"  {reaction.agent}  ·  onset {reaction.onset_min} min",
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg=FG).pack(side='left')

        try:
            advice = rechallenge_advice(grade, cfg)
            adv_color = '#e05555' if advice.hard_block else '#FFA726'
            tk.Label(section, text=advice.advisory_text,
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=adv_color,
                     anchor='w', wraplength=400).pack(fill='x', pady=(2, 0))
        except Exception:
            pass

    def _open_add_reaction(self):
        if not self.patient_db_id:
            return
        from views.dialogs.infusion_reaction_dialog import InfusionReactionDialog
        InfusionReactionDialog(self, self.conn, self.patient_db_id, on_save=self.refresh)

    def _open_reaction_history(self):
        if not self.patient_str_id:
            return
        _ReactionHistoryWindow(self, self.conn, self.patient_db_id,
                               self.patient_str_id, on_change=self.refresh)

    # ── G-CSF section ─────────────────────────────────────────────────────────

    def _render_gcsf(self):
        section = self._section_frame("G-CSF Administration")
        latest  = latest_gcsf(self.conn, self.patient_str_id)

        if latest is None:
            row = tk.Frame(section, bg=BG_ALT)
            row.pack(fill='x', pady=(4, 0))
            tk.Label(row, text="No G-CSF doses logged.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(side='left')
            add = tk.Label(row, text="+ Add",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            add.pack(side='left', padx=(8, 0))
            add.bind('<Button-1>', lambda e: self._open_add_gcsf())
        else:
            self._render_gcsf_latest(section, latest)

        self._section_action_row(section, latest,
                                 on_add=self._open_add_gcsf,
                                 on_history=self._open_gcsf_history)

    def _render_gcsf_latest(self, section, gcsf: GcsfAdmin):
        d = gcsf.admin_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)
        parts = [f"{gcsf.agent}  ·  {date_str}"]
        if gcsf.dose_mg is not None:
            parts.append(f"{gcsf.dose_mg} mg")
        if gcsf.prophylaxis_type:
            parts.append(f"({gcsf.prophylaxis_type})")

        summary_row = tk.Frame(section, bg=BG_ALT)
        summary_row.pack(fill='x', pady=(4, 0))
        tk.Label(summary_row, text="▲ " + "  ".join(parts),
                 font=('Arial', FONT_BODY), bg=BG_ALT, fg='#80DEEA').pack(side='left')

    def _open_add_gcsf(self):
        if not self.patient_db_id:
            return
        from views.dialogs.gcsf_dialog import GcsfDialog
        GcsfDialog(self, self.conn, self.patient_db_id, on_save=self.refresh)

    def _open_gcsf_history(self):
        if not self.patient_str_id:
            return
        _GcsfHistoryWindow(self, self.conn, self.patient_db_id,
                           self.patient_str_id, on_change=self.refresh)

    # ── Symptoms section ──────────────────────────────────────────────────────

    def _render_symptoms(self):
        section = self._section_frame("Symptoms")
        entries = latest_cycle_symptoms(self.conn, self.patient_str_id)

        if not entries:
            row = tk.Frame(section, bg=BG_ALT)
            row.pack(fill='x', pady=(4, 0))
            tk.Label(row, text="No symptoms logged.",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED).pack(side='left')
            add = tk.Label(row, text="+ Add",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            add.pack(side='left', padx=(8, 0))
            add.bind('<Button-1>', lambda e: self._open_add_symptoms())
        else:
            self._render_symptoms_latest(section, entries)

        self._section_action_row(
            section,
            entries[0] if entries else None,
            on_add=self._open_add_symptoms,
            on_history=self._open_symptom_history,
        )

    def _render_symptoms_latest(self, section, entries: list):
        from clinical.symptoms import is_advisory
        cfg = get_config().toxicity.model_dump()

        d = entries[0].entry_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)
        tk.Label(section, text=date_str,
                 font=('Arial', FONT_HINT), bg=BG_ALT, fg=FG_MUTED,
                 anchor='w').pack(anchor='w', pady=(4, 2))

        sym_row = tk.Frame(section, bg=BG_ALT)
        sym_row.pack(fill='x')
        for entry in entries:
            grade = entry.grade
            name  = entry.symptom.replace('_', ' ').capitalize()
            color = _NEUROPATHY_COLOR.get(grade, FG)
            tk.Label(sym_row,
                     text=f"{name} G{grade}",
                     font=('Arial', FONT_HINT), bg=BG_ALT, fg=color,
                     ).pack(side='left', padx=(0, 12))

    def _open_add_symptoms(self):
        if not self.patient_db_id:
            return
        from models import get_cycles_by_patient
        cycles = [c for c in get_cycles_by_patient(self.conn, self.patient_db_id)
                  if c.status == 'completed']
        if not cycles:
            messagebox.showinfo(
                'No Completed Cycles',
                'Complete a treatment cycle first before recording symptoms.',
                parent=self,
            )
            return
        latest = max(cycles, key=lambda c: c.cycle_number)
        from views.dialogs.symptom_quick_entry_dialog import SymptomQuickEntryDialog
        SymptomQuickEntryDialog(self, self.conn, patient_id=self.patient_db_id,
                                cycle=latest, on_save=self.refresh)

    def _open_symptom_history(self):
        if not self.patient_str_id:
            return
        _SymptomHistoryWindow(self, self.conn, self.patient_db_id,
                              self.patient_str_id, on_change=self.refresh)

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _section_frame(self, title: str) -> tk.Frame:
        tk.Frame(self._content, bg=SEPARATOR, height=1).pack(fill='x', pady=(8, 0))
        header = tk.Frame(self._content, bg=BG_ALT)
        header.pack(fill='x', pady=(6, 0))
        tk.Label(header, text=title,
                 font=('Arial', FONT_LABEL, 'bold'), bg=BG_ALT, fg=FG).pack(side='left')
        body = tk.Frame(self._content, bg=BG_ALT)
        body.pack(fill='x')
        return body

    def _section_action_row(self, section, current_record, on_add, on_history):
        row = tk.Frame(section, bg=BG_ALT)
        row.pack(fill='x', pady=(6, 0))
        if current_record is not None:
            hist = tk.Label(row, text="View history",
                            font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2')
            hist.pack(side='left')
            hist.bind('<Button-1>', lambda e: on_history())
            add = tk.Label(row, text="+ Add new",
                           font=('Arial', FONT_HINT), bg=BG_ALT, fg='#90CAF9', cursor='hand2',
                           padx=12)
            add.pack(side='left')
            add.bind('<Button-1>', lambda e: on_add())


# ── Neuropathy history window ─────────────────────────────────────────────────

class _NeuropathyHistoryWindow(tk.Toplevel):
    """Lightweight history list for neuropathy assessments."""

    def __init__(self, parent, conn, patient_db_id: int, patient_str_id: str, on_change=None):
        super().__init__(parent)
        self.conn           = conn
        self.patient_db_id  = patient_db_id
        self.patient_str_id = patient_str_id
        self.on_change      = on_change

        self.title("Neuropathy History")
        self.configure(bg=BG)
        self.geometry('560x400')
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Neuropathy Assessments",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        scroll_frame = tk.Frame(self, bg=BG)
        scroll_frame.pack(fill='both', expand=True, padx=16, pady=12)

        rows = list_neuropathy(self.conn, self.patient_str_id)
        if not rows:
            tk.Label(scroll_frame, text="No assessments on record.",
                     font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED).pack(anchor='w')
            return

        cfg = get_config().toxicity.model_dump()
        for a in rows:
            self._render_row(scroll_frame, a, cfg)

    def _render_row(self, parent, a: NeuropathyAssessment, cfg: dict):
        grade = effective_grade(a.sensory_grade, a.motor_grade, cfg)
        color = _NEUROPATHY_COLOR.get(grade, FG)
        d     = a.assessment_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)

        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=3)

        tk.Label(row, text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG, fg=color).pack(side='left')
        tk.Label(row,
                 text=f"  S{a.sensory_grade}/M{a.motor_grade}  {date_str}",
                 font=('Arial', FONT_BODY), bg=BG, fg=FG).pack(side='left')

        del_btn = tk.Label(row, text="Delete",
                           font=('Arial', FONT_HINT), bg=BG, fg='#e05555', cursor='hand2',
                           padx=8)
        del_btn.pack(side='right')
        del_btn.bind('<Button-1>', lambda e, aid=a.id: self._on_delete(aid))

        edit_btn = tk.Label(row, text="Edit",
                            font=('Arial', FONT_HINT), bg=BG, fg='#90CAF9', cursor='hand2')
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e, rec=a: self._on_edit(rec))

    def _on_edit(self, assessment: NeuropathyAssessment):
        from views.dialogs.neuropathy_dialog import EditNeuropathyDialog
        EditNeuropathyDialog(self, self.conn, assessment,
                             self.patient_db_id, on_save=self._refresh)

    def _on_delete(self, assessment_id: int):
        if not messagebox.askyesno("Delete Assessment",
                                   "Delete this neuropathy assessment?", parent=self):
            return
        delete_neuropathy(self.conn, assessment_id)
        if self.on_change:
            self.on_change()
        self._refresh()

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Infusion reaction history window ─────────────────────────────────────────

class _ReactionHistoryWindow(tk.Toplevel):
    """Lightweight history list for infusion reactions."""

    def __init__(self, parent, conn, patient_db_id: int, patient_str_id: str, on_change=None):
        super().__init__(parent)
        self.conn           = conn
        self.patient_db_id  = patient_db_id
        self.patient_str_id = patient_str_id
        self.on_change      = on_change

        self.title("Infusion Reaction History")
        self.configure(bg=BG)
        self.geometry('600x420')
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Infusion Reactions",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill='both', expand=True, padx=16, pady=12)

        rows = list_reactions(self.conn, self.patient_str_id)
        if not rows:
            tk.Label(frame, text="No reactions on record.",
                     font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED).pack(anchor='w')
            return

        cfg = get_config().toxicity.model_dump()
        for r in rows:
            self._render_row(frame, r, cfg)

    def _render_row(self, parent, reaction: InfusionReaction, cfg: dict):
        grade = reaction.severity_grade
        color = {1: '#4CAF50', 2: '#FFC107', 3: '#FF9800', 4: '#F44336'}.get(grade, FG)

        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=3)

        tk.Label(row, text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG, fg=color).pack(side='left')
        tk.Label(row,
                 text=f"  {reaction.agent}  onset {reaction.onset_min} min",
                 font=('Arial', FONT_BODY), bg=BG, fg=FG).pack(side='left')

        del_btn = tk.Label(row, text="Delete",
                           font=('Arial', FONT_HINT), bg=BG, fg='#e05555', cursor='hand2',
                           padx=8)
        del_btn.pack(side='right')
        del_btn.bind('<Button-1>', lambda e, rid=reaction.id: self._on_delete(rid))

        edit_btn = tk.Label(row, text="Edit",
                            font=('Arial', FONT_HINT), bg=BG, fg='#90CAF9', cursor='hand2')
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e, rec=reaction: self._on_edit(rec))

    def _on_edit(self, reaction: InfusionReaction):
        from views.dialogs.infusion_reaction_dialog import EditInfusionReactionDialog
        EditInfusionReactionDialog(self, self.conn, reaction,
                                   self.patient_db_id, on_save=self._refresh)

    def _on_delete(self, reaction_id: int):
        if not messagebox.askyesno("Delete Reaction",
                                   "Delete this infusion reaction?", parent=self):
            return
        delete_reaction(self.conn, reaction_id)
        if self.on_change:
            self.on_change()
        self._refresh()

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── G-CSF history window ──────────────────────────────────────────────────────

class _GcsfHistoryWindow(tk.Toplevel):
    """Lightweight history list for G-CSF administrations."""

    def __init__(self, parent, conn, patient_db_id: int, patient_str_id: str, on_change=None):
        super().__init__(parent)
        self.conn           = conn
        self.patient_db_id  = patient_db_id
        self.patient_str_id = patient_str_id
        self.on_change      = on_change

        self.title("G-CSF Administration History")
        self.configure(bg=BG)
        self.geometry('580x380')
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="G-CSF Administrations",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill='both', expand=True, padx=16, pady=12)

        rows = list_gcsf(self.conn, self.patient_str_id)
        if not rows:
            tk.Label(frame, text="No G-CSF records on record.",
                     font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED).pack(anchor='w')
            return

        for g in rows:
            self._render_row(frame, g)

    def _render_row(self, parent, gcsf: GcsfAdmin):
        d = gcsf.admin_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)

        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=3)

        label = f"▲ {gcsf.agent}  {date_str}"
        if gcsf.dose_mg is not None:
            label += f"  {gcsf.dose_mg} mg"
        if gcsf.prophylaxis_type:
            label += f"  ({gcsf.prophylaxis_type})"
        tk.Label(row, text=label, font=('Arial', FONT_BODY), bg=BG, fg='#80DEEA').pack(side='left')

        del_btn = tk.Label(row, text="Delete",
                           font=('Arial', FONT_HINT), bg=BG, fg='#e05555', cursor='hand2',
                           padx=8)
        del_btn.pack(side='right')
        del_btn.bind('<Button-1>', lambda e, gid=gcsf.id: self._on_delete(gid))

        edit_btn = tk.Label(row, text="Edit",
                            font=('Arial', FONT_HINT), bg=BG, fg='#90CAF9', cursor='hand2')
        edit_btn.pack(side='right')
        edit_btn.bind('<Button-1>', lambda e, rec=gcsf: self._on_edit(rec))

    def _on_edit(self, gcsf: GcsfAdmin):
        from views.dialogs.gcsf_dialog import EditGcsfDialog
        EditGcsfDialog(self, self.conn, gcsf, self.patient_db_id, on_save=self._refresh)

    def _on_delete(self, gcsf_id: int):
        if not messagebox.askyesno("Delete G-CSF Record",
                                   "Delete this G-CSF administration?", parent=self):
            return
        delete_gcsf(self.conn, gcsf_id)
        if self.on_change:
            self.on_change()
        self._refresh()

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Symptom history window ────────────────────────────────────────────────────

class _SymptomHistoryWindow(tk.Toplevel):
    """Lightweight history list for symptom entries."""

    def __init__(self, parent, conn, patient_db_id: int, patient_str_id: str, on_change=None):
        super().__init__(parent)
        self.conn           = conn
        self.patient_db_id  = patient_db_id
        self.patient_str_id = patient_str_id
        self.on_change      = on_change

        self.title("Symptom History")
        self.configure(bg=BG)
        self.geometry('580x420')
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="Symptom Entries",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG, fg=FG,
                 padx=16, pady=12).pack(anchor='w')
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x')

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill='both', expand=True, padx=16, pady=12)

        rows = list_symptoms(self.conn, self.patient_str_id)
        if not rows:
            tk.Label(frame, text="No symptom entries on record.",
                     font=('Arial', FONT_BODY), bg=BG, fg=FG_MUTED).pack(anchor='w')
            return

        for entry in rows:
            self._render_row(frame, entry)

    def _render_row(self, parent, entry: SymptomEntry):
        grade = entry.grade
        color = _NEUROPATHY_COLOR.get(grade, FG)
        d = entry.entry_date
        date_str = d.isoformat() if hasattr(d, 'isoformat') else str(d)
        name = entry.symptom.replace('_', ' ').capitalize()

        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=3)

        tk.Label(row, text=f"● G{grade}",
                 font=('Arial', FONT_BODY, 'bold'), bg=BG, fg=color).pack(side='left')
        tk.Label(row,
                 text=f"  {name}  ·  {date_str}",
                 font=('Arial', FONT_BODY), bg=BG, fg=FG).pack(side='left')

        del_btn = tk.Label(row, text="Delete",
                           font=('Arial', FONT_HINT), bg=BG, fg='#e05555', cursor='hand2',
                           padx=8)
        del_btn.pack(side='right')
        del_btn.bind('<Button-1>', lambda e, eid=entry.id: self._on_delete(eid))

    def _on_delete(self, entry_id: int):
        if not messagebox.askyesno("Delete Symptom",
                                   "Delete this symptom entry?", parent=self):
            return
        delete_symptom(self.conn, entry_id)
        if self.on_change:
            self.on_change()
        self._refresh()

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()
