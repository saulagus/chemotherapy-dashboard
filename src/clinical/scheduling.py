"""Cycle scheduling rules (US-032).

Pure functions — no DB or Tk imports. Cadence and lookahead windows
are read from config; nothing is hardcoded here.
"""

from datetime import date, timedelta
from typing import Any, Dict, Literal, Optional, Tuple

CycleStatusCode = Literal['on_schedule', 'due_soon', 'overdue', 'no_cycles']


def expected_cycle_date(
    last_cycle_date: date,
    dose_density: Optional[str],
    config: Dict[str, Any],
) -> date:
    """Return the expected date for the next cycle based on cadence.

    config is the scheduling section dict with cadence_days sub-dict.
    Falls back to standard_q3w (21 d) when dose_density is unknown.
    """
    sched = config if 'cadence_days' in config else config.get('scheduling', config)
    cadence = sched['cadence_days']

    if dose_density == 'dose_dense_q2w':
        days = cadence.get('dose_dense_q2w', 14)
    else:
        days = cadence.get('standard_q3w', 21)

    if hasattr(days, '__int__'):
        days = int(days)

    return last_cycle_date + timedelta(days=days)


def cycle_status(
    last_cycle_date: date,
    dose_density: Optional[str],
    today: date,
    config: Dict[str, Any],
) -> Tuple[CycleStatusCode, int]:
    """Return (status_code, day_delta) for the next cycle.

    day_delta is positive when the expected date is in the future
    (days until due) and negative when it is in the past (days overdue).

    config is the scheduling section dict.
    """
    sched = config if 'cadence_days' in config else config.get('scheduling', config)
    expected = expected_cycle_date(last_cycle_date, dose_density, sched)
    delta_days = (expected - today).days

    due_within = sched.get('due_within_days', 7)
    if hasattr(due_within, '__int__'):
        due_within = int(due_within)

    if delta_days < 0:
        return ('overdue', delta_days)
    if delta_days <= due_within:
        return ('due_soon', delta_days)
    return ('on_schedule', delta_days)
