"""ANC trend chart → BytesIO PNG (Sprint 9 — US-035).

render_anc_trend() produces a deterministic PNG via matplotlib.
DPI is fixed at 150 for byte-stable golden tests.
G-CSF stimulated dates are marked with a glyph matching the dashboard chart.
"""

from __future__ import annotations

import io
from datetime import date
from typing import List, Optional


_DPI = 150


def render_anc_trend(
    labs: list,
    gcsf_dates: List[date],
    size_in: List[float],
    config,
) -> bytes:
    """Render an ANC trend chart.

    labs      — list of Lab dataclass objects (sorted oldest→newest by caller)
    gcsf_dates — list of date objects representing G-CSF stimulated days
    size_in   — [width_inches, height_inches]
    config    — InstitutionConfig (used for ANC thresholds via utils)
    Returns PNG bytes from a fixed-DPI matplotlib figure.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import datetime

    width, height = float(size_in[0]), float(size_in[1])
    fig, ax = plt.subplots(figsize=(width, height), dpi=_DPI)
    fig.patch.set_facecolor('#1a1e2a')
    ax.set_facecolor('#1a1e2a')

    anc_labs = [lb for lb in labs if lb.anc is not None]
    if not anc_labs:
        ax.text(0.5, 0.5, 'No ANC data', transform=ax.transAxes,
                ha='center', va='center', color='#6b7494', fontsize=8)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=_DPI, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    dates = []
    anc_values = []
    for lb in anc_labs:
        d = lb.lab_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        dates.append(d)
        anc_values.append(lb.anc)

    gcsf_set = set(gcsf_dates)
    stimulated_x = [d for d in dates if d in gcsf_set]
    stimulated_y = [anc_values[dates.index(d)] for d in stimulated_x]

    ax.plot(dates, anc_values, color='#90CAF9', linewidth=1.5, marker='o',
            markersize=4, zorder=3)

    if stimulated_x:
        ax.scatter(stimulated_x, stimulated_y, color='#80DEEA', s=60,
                   marker='^', zorder=4, label='G-CSF')

    # ANC threshold reference lines
    ax.axhline(y=1.5, color='#FFC107', linewidth=0.8, linestyle='--', alpha=0.7)
    ax.axhline(y=0.5, color='#F44336', linewidth=0.8, linestyle='--', alpha=0.7)

    ax.set_xlabel('', color='#6b7494', fontsize=7)
    ax.set_ylabel('ANC (10⁹/L)', color='#e8eaf0', fontsize=7)
    ax.tick_params(colors='#6b7494', labelsize=6)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate(rotation=30, ha='right')

    for spine in ax.spines.values():
        spine.set_edgecolor('#2a2f42')

    ax.grid(True, color='#2a2f42', linewidth=0.5, alpha=0.7)
    fig.tight_layout(pad=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=_DPI, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()
