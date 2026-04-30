import tkinter as tk
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED, FONT_HINT, FONT_LABEL, FONT_BODY, FONT_HEADER, FONT_TITLE, FONT_CYCLE

# Timeline component lives inside a BG_ALT panel — use BG_ALT for all internal frames
# so there's no dark rectangle cutting into the card background.
_BG = BG_ALT
from models import get_cycles_by_patient, Cycle

# ---------------------------------------------------------------------------
# Cycle status constants — match values stored in the database
# ---------------------------------------------------------------------------

STATUS_PENDING   = 'pending'
STATUS_COMPLETED = 'completed'
STATUS_DELAYED   = 'delayed'
STATUS_SKIPPED   = 'skipped'

# ---------------------------------------------------------------------------
# Colour scheme for cycle states and phases
# ---------------------------------------------------------------------------

COLORS = {
    'pending_bg':        '#E0E0E0',   # Light gray
    'pending_bg_hover':  '#CACACA',   # Slightly darker on hover
    'pending_fg':        '#666666',   # Dark gray text
    'current_bg':        '#1a3a5c',   # Dark navy
    'current_bg_hover':  '#1f4570',   # Lighter navy on hover
    'current_fg':        '#90caf9',   # Soft blue text
    'current_border':    '#3b82f6',   # Bright blue border
    'completed_bg':      '#388E3C',   # Darker green — white text contrast 4.0:1 (WCAG AA)
    'completed_bg_hover':'#2E7D32',   # Deeper green on hover
    'completed_fg':      '#FFFFFF',   # White text
    'ac_phase':       '#3498DB',   # Blue accent
    't_phase':        '#9B59B6',   # Purple accent
    'modified':       '#FF9800',   # Orange warning
}


def _add_tooltip(widget: tk.Widget, text: str) -> None:
    """Attach a simple hover tooltip to a widget."""
    tip: list[tk.Toplevel | None] = [None]

    def show(event):
        tip[0] = tk.Toplevel(widget)
        tip[0].wm_overrideredirect(True)
        tip[0].wm_geometry(f"+{event.x_root + 12}+{event.y_root + 8}")
        tk.Label(tip[0], text=text, font=('Arial', FONT_BODY),
                 bg='#ffffe0', fg='#333333',
                 relief='solid', borderwidth=1,
                 padx=8, pady=4).pack()

    def hide(event):
        if tip[0]:
            tip[0].destroy()
            tip[0] = None

    widget.bind('<Enter>', show)
    widget.bind('<Leave>', hide)


class TimelineComponent(tk.Frame):
    """Visual 8-cycle treatment timeline for a single patient.

    Displays all cycles as clickable boxes grouped into AC phase (1-4)
    and T phase (5-8). Visual state changes based on cycle status:
    pending, current, completed, or completed with dose modification.

    Parameters
    ----------
    parent     : tk.Widget  — parent widget (dashboard content frame)
    controller : App        — main app reference for DB access
    patient_id : int | None — DB integer id of the patient to display
    """

    def __init__(self, parent, controller, patient_id=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller    = controller
        self.patient_id    = patient_id
        self.cycles: list[Cycle] = []          # Loaded from DB in _load_cycles()
        self._cycle_frames: list[tk.Frame] = [] # References to the 8 cycle boxes
        self.on_cycle_save = None              # Dashboard wires this after construction

        self.configure(bg=_BG)
        self._build_ui()

        if patient_id is not None:
            self.load_patient(patient_id)

    # ── Public API ─────────────────────────────────────────────────────────────

    def load_patient(self, patient_id: int) -> None:
        """Load cycle data for a new patient and rebuild the timeline."""
        self.patient_id = patient_id
        self._load_cycles()
        self.refresh()

    def refresh(self) -> None:
        """Reload cycle data from DB and redraw all cycle boxes."""
        if self.patient_id is not None:
            self._load_cycles()
        self._rebuild_timeline()

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load_cycles(self) -> None:
        """Fetch all cycles for the current patient from the database."""
        self.cycles = get_cycles_by_patient(self.controller.conn, self.patient_id)

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Create the static skeleton of the timeline (rebuilt on refresh)."""
        # Status text row — e.g. "Current: Cycle 3 (AC Phase)"
        self.status_label = tk.Label(
            self, text="", font=('Arial', FONT_TITLE, 'bold'), bg=_BG, fg=FG, anchor='w'
        )
        self.status_label.pack(anchor='w', pady=(0, 14))

        # Cycle boxes container — filled in _rebuild_timeline()
        self.cycles_frame = tk.Frame(self, bg=_BG)
        self.cycles_frame.pack(anchor='w')

    def _rebuild_timeline(self) -> None:
        """Destroy and recreate all cycle boxes based on current cycle data."""
        # Clear existing cycle boxes.
        for widget in self.cycles_frame.winfo_children():
            widget.destroy()
        self._cycle_frames.clear()

        # Determine current cycle once — used by _get_cycle_state and _update_status_label.
        self.current_cycle_number: int | None = self._compute_current_cycle_number()

        # Build a lookup from cycle_number → Cycle for quick access.
        cycle_map = {c.cycle_number: c for c in self.cycles}

        # AC phase group (cycles 1-4).
        ac_group = self._build_phase_group(self.cycles_frame, cycle_map, range(1, 5), 'AC')
        ac_group.pack(side='left', padx=(0, 20))

        # Vertical separator between phases.
        tk.Frame(self.cycles_frame, width=2, bg=SEPARATOR).pack(side='left', fill='y', padx=20)

        # T phase group (cycles 5-8).
        t_group = self._build_phase_group(self.cycles_frame, cycle_map, range(5, 9), 'T')
        t_group.pack(side='left')

        self._update_status_label(cycle_map)

    def _build_phase_group(
        self,
        parent: tk.Widget,
        cycle_map: dict,
        cycle_range: range,
        phase_name: str,
    ) -> tk.Frame:
        """Create a labelled group of cycle boxes for one phase (AC or T)."""
        group = tk.Frame(parent, bg=_BG)

        # Row of cycle boxes.
        boxes_row = tk.Frame(group, bg=_BG)
        boxes_row.pack()

        for cycle_number in cycle_range:
            cycle = cycle_map.get(cycle_number)
            box = self._create_cycle_box(boxes_row, cycle_number, cycle)
            box.pack(side='left', padx=4)
            self._cycle_frames.append(box)

        # Phase label + drug name below the boxes — coloured by phase.
        phase_color = COLORS['ac_phase'] if phase_name == 'AC' else COLORS['t_phase']
        drug_name   = 'Adriamycin + Cyclophosphamide' if phase_name == 'AC' else 'Taxol (Paclitaxel)'

        tk.Label(
            group,
            text=f"{phase_name} Phase",
            font=('Arial', FONT_HEADER, 'bold'),
            bg=_BG,
            fg=phase_color,
        ).pack(pady=(10, 0))

        tk.Label(
            group,
            text=drug_name,
            font=('Arial', FONT_BODY),
            bg=_BG,
            fg=FG,
        ).pack(pady=(3, 0))

        return group

    def _compute_current_cycle_number(self) -> int | None:
        """Return the current cycle number, or None if treatment is complete.

        Current cycle = first non-completed cycle (completed_count + 1).
        Returns None when all cycles are completed.
        """
        completed_count = sum(1 for c in self.cycles if c.status == 'completed')
        if self.cycles and completed_count == len(self.cycles):
            return None   # All cycles done — treatment complete
        return completed_count + 1

    def _get_cycle_state(self, cycle: Cycle | None, cycle_number: int) -> str:
        """Return the visual state for a cycle: 'pending', 'current', or 'completed'."""
        if cycle is None or cycle.status != 'completed':
            if cycle_number == self.current_cycle_number:
                return 'current'
            return 'pending'
        return 'completed'

    def _create_cycle_box(
        self,
        parent: tk.Widget,
        cycle_number: int,
        cycle: Cycle | None,
    ) -> tk.Frame:
        """Create a single styled cycle box (~80x80).

        Visual state (pending / current / completed) drives background and text colours.
        Dose modification indicator and click binding are added on Day 13+.
        """
        state = self._get_cycle_state(cycle, cycle_number)

        # Pick colours and labels based on state.
        # Pending: light gray, empty appearance, subtle border.
        # Current: same colours as pending — blue border is the visual distinction.
        # Completed: green background, white text, checkmark indicator.
        if state == 'completed':
            bg, fg            = COLORS['completed_bg'], COLORS['completed_fg']
            status_text       = '✓'
            highlight         = COLORS['completed_bg']
            border_thickness  = 2
        elif state == 'current':
            bg, fg            = COLORS['current_bg'], COLORS['current_fg']
            status_text       = 'Current'
            highlight         = COLORS['current_border']
            border_thickness  = 3   # Thicker border makes it stand out
        else:
            bg, fg            = COLORS['pending_bg'], COLORS['pending_fg']
            status_text       = 'Pending'
            highlight         = '#BDBDBD'   # Subtle light-gray border for pending
            border_thickness  = 2

        box = tk.Frame(parent, width=82, height=82, bg=bg,
                       highlightbackground=highlight, highlightthickness=border_thickness)
        box.pack_propagate(False)

        # Phase accent — 4px colored strip at top + phase label in box fg color.
        phase_text   = 'AC' if cycle_number <= 4 else 'T'
        phase_color  = COLORS['ac_phase'] if cycle_number <= 4 else COLORS['t_phase']
        tk.Frame(box, height=4, bg=phase_color).pack(fill='x')
        tk.Label(box, text=phase_text,
                 font=('Arial', FONT_LABEL, 'bold'), bg=bg, fg=fg).pack(pady=(2, 0))

        # Cycle number — prominent centre.
        tk.Label(box, text=str(cycle_number),
                 font=('Arial', FONT_CYCLE, 'bold'), bg=bg, fg=fg).pack()

        # Status indicator at bottom — checkmark for completed, text for others.
        status_font = ('Arial', FONT_TITLE, 'bold') if state == 'completed' else ('Arial', FONT_LABEL)
        status_lbl = tk.Label(box, text=status_text,
                              font=status_font, bg=bg, fg=fg)
        status_lbl.pack(pady=(0, 5))

        # Dose modification indicator — orange ⚠ badge in top-right corner.
        # Only shown on completed cycles where dose was reduced below 100%.
        is_modified = (
            state == 'completed'
            and cycle is not None
            and cycle.dose_percent is not None
            and cycle.dose_percent < 100
        )
        if is_modified:
            mod_badge = tk.Label(box, text='⚠', font=('Arial', FONT_LABEL, 'bold'),
                                 bg=bg, fg=COLORS['modified'])
            mod_badge.place(relx=1.0, rely=0.0, anchor='ne', x=-4, y=6)

        # Tooltip: completed date, plus dose info if modified.
        if state == 'completed' and cycle is not None and cycle.actual_date:
            tip_text = f"Completed {cycle.actual_date}"
            if is_modified:
                reason_part = f" — {cycle.dose_reason}" if cycle.dose_reason else ""
                tip_text += f"\nDose: {int(cycle.dose_percent)}%{reason_part}"
            _add_tooltip(status_lbl, tip_text)

        # Hover colours — slightly shifted shade of the base bg.
        hover_bg = COLORS.get(f'{state}_bg_hover', bg)

        def _on_enter(e):
            box.configure(bg=hover_bg)
            for child in box.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=hover_bg)

        def _on_leave(e):
            box.configure(bg=bg)
            for child in box.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=bg)

        # Bind click and hover on the box frame AND every child label so the
        # full 82x82 area is clickable — not just the gaps between labels.
        # Default args (c=cycle, n=cycle_number) capture current loop values;
        # without them every lambda would close over the final loop iteration.
        for widget in (box, *box.winfo_children()):
            widget.bind('<Button-1>', lambda e, c=cycle, n=cycle_number: self._on_cycle_click(c, n))
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)
            widget.configure(cursor='hand2')

        return box

    def _on_cycle_click(self, cycle: Cycle | None, cycle_number: int) -> None:
        """Handle a click on a cycle box.

        Pending/current → CycleCompletionDialog (mark complete).
        Completed       → CycleDetailDialog (view + edit).
        """
        from views.dialogs.cycle_completion_dialog import CycleCompletionDialog
        from views.components.cycle_dialog import CycleDetailDialog
        from models import get_patient_by_db_id

        def _on_save():
            self.refresh()
            if self.on_cycle_save:
                self.on_cycle_save()

        if cycle is not None and cycle.status == 'completed':
            CycleDetailDialog(
                self, self.controller.conn, self.patient_id,
                cycle, on_save=_on_save
            )
        else:
            patient    = get_patient_by_db_id(self.controller.conn, self.patient_id)
            start_date = patient.start_date if patient else None

            def _open_completion():
                CycleCompletionDialog(
                    self, self.controller.conn, self.patient_id,
                    cycle_number, cycle, on_save=_on_save, start_date=start_date
                )

            from views.dialogs.precycle_checklist_dialog import PrecycleChecklistDialog
            PrecycleChecklistDialog(
                self, self.controller.conn, self.patient_id,
                cycle_number, on_proceed=_open_completion,
            )

    def _update_status_label(self, cycle_map: dict) -> None:
        """Set the status text above the timeline based on cycle progress."""
        if self.current_cycle_number is None:
            self.status_label.config(text="Treatment Complete")
            return

        phase = 'AC Phase' if self.current_cycle_number <= 4 else 'T Phase'
        transition = '  —  Starting T Phase' if self.current_cycle_number == 5 else ''
        self.status_label.config(
            text=f"Current: Cycle {self.current_cycle_number} ({phase}){transition}"
        )
