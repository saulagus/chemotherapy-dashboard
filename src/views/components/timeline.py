import tkinter as tk
from utils import BG, BG_ALT, SEPARATOR, FG, FG_MUTED
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
    'pending_bg':     '#E0E0E0',   # Light gray
    'pending_fg':     '#666666',   # Dark gray text
    'completed_bg':   '#4CAF50',   # Green
    'completed_fg':   '#FFFFFF',   # White text
    'current_border': '#2196F3',   # Blue border
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
        tk.Label(tip[0], text=text, font=('Arial', 9),
                 bg='#ffffe0', fg='#333333',
                 relief='solid', borderwidth=1,
                 padx=4, pady=2).pack()

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
        self.controller = controller
        self.patient_id = patient_id
        self.cycles: list[Cycle] = []          # Loaded from DB in _load_cycles()
        self._cycle_frames: list[tk.Frame] = [] # References to the 8 cycle boxes

        self.configure(bg=BG)
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
            self, text="", font=('Arial', 11), bg=BG, fg=FG_MUTED, anchor='w'
        )
        self.status_label.pack(anchor='w', pady=(0, 12))

        # Cycle boxes container — filled in _rebuild_timeline()
        self.cycles_frame = tk.Frame(self, bg=BG)
        self.cycles_frame.pack(anchor='w')

    def _rebuild_timeline(self) -> None:
        """Destroy and recreate all cycle boxes based on current cycle data."""
        # Clear existing cycle boxes.
        for widget in self.cycles_frame.winfo_children():
            widget.destroy()
        self._cycle_frames.clear()

        # Build a lookup from cycle_number → Cycle for quick access.
        cycle_map = {c.cycle_number: c for c in self.cycles}

        # AC phase group (cycles 1-4).
        ac_group = self._build_phase_group(self.cycles_frame, cycle_map, range(1, 5), 'AC')
        ac_group.pack(side='left', padx=(0, 24))

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
        group = tk.Frame(parent, bg=BG)

        # Row of cycle boxes.
        boxes_row = tk.Frame(group, bg=BG)
        boxes_row.pack()

        for cycle_number in cycle_range:
            cycle = cycle_map.get(cycle_number)
            box = self._create_cycle_box(boxes_row, cycle_number, cycle)
            box.pack(side='left', padx=4)
            self._cycle_frames.append(box)

        # Phase label below the boxes — coloured by phase.
        phase_color = COLORS['ac_phase'] if phase_name == 'AC' else COLORS['t_phase']
        tk.Label(
            group,
            text=f"{phase_name} Phase",
            font=('Arial', 10),
            bg=BG,
            fg=phase_color,
        ).pack(pady=(6, 0))

        return group

    def _get_cycle_state(self, cycle: Cycle | None, cycle_number: int) -> str:
        """Return the visual state for a cycle: 'pending', 'current', or 'completed'."""
        if cycle is None or cycle.status != 'completed':
            completed_count = sum(1 for c in self.cycles if c.status == 'completed')
            current_number  = completed_count + 1
            if cycle_number == current_number:
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
            bg, fg       = COLORS['completed_bg'], COLORS['completed_fg']
            status_text  = '✓'
            highlight    = COLORS['completed_bg']
        elif state == 'current':
            bg, fg       = COLORS['pending_bg'], COLORS['pending_fg']
            status_text  = 'Current'
            highlight    = COLORS['current_border']
        else:
            bg, fg       = COLORS['pending_bg'], COLORS['pending_fg']
            status_text  = 'Pending'
            highlight    = '#BDBDBD'   # Subtle light-gray border for pending

        box = tk.Frame(parent, width=80, height=80, bg=bg,
                       highlightbackground=highlight, highlightthickness=2)
        box.pack_propagate(False)

        # Phase indicator — small label at top.
        phase_text = 'AC' if cycle_number <= 4 else 'T'
        tk.Label(box, text=phase_text,
                 font=('Arial', 8), bg=bg, fg=fg).pack(pady=(4, 0))

        # Cycle number — prominent centre.
        tk.Label(box, text=str(cycle_number),
                 font=('Arial', 16, 'bold'), bg=bg, fg=fg).pack()

        # Status indicator at bottom — checkmark for completed, text for others.
        status_font = ('Arial', 12, 'bold') if state == 'completed' else ('Arial', 7)
        status_lbl = tk.Label(box, text=status_text,
                              font=status_font, bg=bg, fg=fg)
        status_lbl.pack(pady=(0, 4))

        # Tooltip: show completed date on hover for completed cycles.
        if state == 'completed' and cycle is not None and cycle.actual_date:
            _add_tooltip(status_lbl, f"Completed {cycle.actual_date}")

        # Bind click on box and all child labels so the whole box is clickable.
        for widget in (box, *box.winfo_children()):
            widget.bind('<Button-1>', lambda e, c=cycle, n=cycle_number: self._on_cycle_click(c, n))
            widget.configure(cursor='hand2')

        return box

    def _on_cycle_click(self, cycle: Cycle | None, cycle_number: int) -> None:
        """Handle a click on a cycle box. Full dialog opens on Day 13."""
        # Placeholder — completion dialog wired up in Day 13.
        pass

    def _update_status_label(self, cycle_map: dict) -> None:
        """Set the status text above the timeline based on cycle progress."""
        completed = [c for c in self.cycles if c.status == 'completed']

        if not self.cycles:
            self.status_label.config(text="No cycle data available.")
            return

        if len(completed) == len(self.cycles):
            self.status_label.config(text="Treatment Complete")
            return

        # Current cycle = first non-completed cycle.
        current_number = len(completed) + 1
        phase = 'AC Phase' if current_number <= 4 else 'T Phase'
        self.status_label.config(text=f"Current: Cycle {current_number} ({phase})")
