import tkinter as tk
from datetime import date
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

from utils import BG, BG_ALT, FG, FG_MUTED, SEPARATOR, FONT_HEADER, FONT_LABEL
from models import get_labs_by_patient
from utils.anc_utils import get_anc_status, ANC_THRESHOLD_MILD

# Chart colour constants
_FIG_BG  = '#1a1e2a'   # BG_ALT — figure outer background
_AX_BG   = '#12151c'   # BG     — axes plot area
_LINE_COLOR  = '#6b7494'  # FG_MUTED — neutral trend line
_GRID_COLOR  = '#2a2f42'  # SEPARATOR — grid lines
_TEXT_COLOR  = '#e8eaf0'  # FG — axis labels and ticks
_THRESH_COLOR = '#e05555' # red dashed threshold line


class ANCTrendChart(tk.Frame):
    """Embedded matplotlib line chart showing ANC values over time.

    Public API
    ----------
    load_patient(patient_id) — switch patient context and refresh
    refresh()                — reload data from DB and redraw
    """

    def __init__(self, parent, conn, patient_id=None, **kwargs):
        super().__init__(parent, bg=BG_ALT, **kwargs)
        self.conn       = conn
        self.patient_id = patient_id

        self._build_header()
        self._build_canvas()
        self.refresh()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        tk.Label(self, text="ANC Trend",
                 font=('Arial', FONT_HEADER, 'bold'), bg=BG_ALT, fg=FG,
                 anchor='w').pack(anchor='w', padx=16, pady=(14, 0))
        tk.Frame(self, bg=SEPARATOR, height=1).pack(fill='x', padx=16, pady=(8, 0))

    # ── Canvas setup (runs once) ──────────────────────────────────────────────

    def _build_canvas(self):
        self.fig = Figure(figsize=(6, 3.5), facecolor=_FIG_BG)
        self.ax  = self.fig.add_subplot(111)
        self.ax.set_facecolor(_AX_BG)
        self.fig.subplots_adjust(left=0.12, right=0.97, top=0.92, bottom=0.18)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=8, pady=(4, 8))

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_data(self):
        """Return (dates, ancs) lists sorted oldest→newest, skipping labs with no ANC."""
        if self.patient_id is None:
            return [], []
        labs = get_labs_by_patient(self.conn, self.patient_id)
        pairs = []
        for lab in labs:
            if lab.anc is None:
                continue
            lab_date = lab.lab_date
            if isinstance(lab_date, str):
                lab_date = date.fromisoformat(lab_date)
            pairs.append((lab_date, lab.anc))
        pairs.sort(key=lambda p: p[0])
        if not pairs:
            return [], []
        dates, ancs = zip(*pairs)
        return list(dates), list(ancs)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def refresh(self):
        """Reload data from DB and redraw the chart."""
        self.ax.clear()
        dates, ancs = self._load_data()
        self._style_axes()

        if not dates:
            self._draw_empty("No lab data to display.")
        elif len(dates) == 1:
            self._draw_single(dates[0], ancs[0])
        else:
            self._draw_chart(dates, ancs)

        self.canvas.draw()

    def _style_axes(self):
        """Apply consistent dark theme styling to axes."""
        ax = self.ax
        ax.set_facecolor(_AX_BG)
        ax.tick_params(colors=_TEXT_COLOR, labelsize=8)
        ax.xaxis.label.set_color(_TEXT_COLOR)
        ax.yaxis.label.set_color(_TEXT_COLOR)
        for spine in ax.spines.values():
            spine.set_edgecolor(_GRID_COLOR)
        ax.set_xlabel('Date', fontsize=9, color=_TEXT_COLOR)
        ax.set_ylabel('ANC (K/μL)', fontsize=9, color=_TEXT_COLOR)
        ax.grid(True, linestyle='--', color=_GRID_COLOR, alpha=0.6, zorder=0)
        ax.set_ylim(bottom=0)

    def _draw_empty(self, message: str):
        self.ax.text(0.5, 0.5, message,
                     transform=self.ax.transAxes,
                     ha='center', va='center',
                     color=_TEXT_COLOR, fontsize=10, alpha=0.6)

    def _draw_single(self, lab_date, anc):
        status = get_anc_status(anc)
        self.ax.plot(lab_date, anc, 'o',
                     color=status['color'], markersize=10, zorder=3)
        self._draw_threshold_line()
        self.ax.text(0.5, 0.05, "Add more labs to see trend",
                     transform=self.ax.transAxes,
                     ha='center', va='bottom',
                     color=_TEXT_COLOR, fontsize=8, alpha=0.6)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

    def _draw_chart(self, dates, ancs):
        # Neutral trend line
        self.ax.plot(dates, ancs, color=_LINE_COLOR, linewidth=2, zorder=2)

        # Color-coded markers
        for d, anc in zip(dates, ancs):
            status = get_anc_status(anc)
            self.ax.plot(d, anc, 'o',
                         color=status['color'], markersize=8, zorder=3)

        self._draw_threshold_line()

        # X-axis date formatting
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        self.fig.autofmt_xdate(rotation=30, ha='right')

        # Y-axis padding
        max_anc = max(ancs)
        self.ax.set_ylim(0, max(max_anc * 1.2, ANC_THRESHOLD_MILD * 2))

    def _draw_threshold_line(self):
        self.ax.axhline(y=ANC_THRESHOLD_MILD, color=_THRESH_COLOR,
                        linestyle='--', linewidth=1.5, alpha=0.8,
                        label=f'Threshold ({ANC_THRESHOLD_MILD})', zorder=1)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_patient(self, patient_id):
        """Switch to a different patient and refresh."""
        self.patient_id = patient_id
        self.refresh()
