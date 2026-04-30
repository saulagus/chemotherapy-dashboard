"""Cycle status indicator widget (US-032).

Shows a green/yellow/red/gray dot with a tooltip for the patient list.

Public API
----------
CycleStatusIndicator — tk.Frame with a colored dot label
get_status_for_patient(conn, patient_db_id) — returns (status_code, tooltip_text)
"""

from datetime import date
from typing import Optional, Tuple

from clinical.scheduling import cycle_status
from config import get as get_config
from services.cycles import last_completed_cycle_date
from models import get_patient_by_db_id

_STATUS_COLORS = {
    'on_schedule': '#4CAF50',
    'due_soon':    '#FFC107',
    'overdue':     '#F44336',
    'no_cycles':   '#6b7494',
}

_STATUS_TEXT = {
    'on_schedule': 'On schedule',
    'due_soon':    'Due soon',
    'overdue':     'Overdue',
    'no_cycles':   'No cycles',
}

_STATUS_SORT_KEY = {
    'overdue':     0,
    'due_soon':    1,
    'on_schedule': 2,
    'no_cycles':   3,
}


def get_status_for_patient(
    conn,
    patient_db_id: int,
    today: Optional[date] = None,
) -> Tuple[str, str, str]:
    """Return (status_code, display_text, tooltip) for a patient's cycle status."""
    if today is None:
        today = date.today()

    last_date = last_completed_cycle_date(conn, patient_db_id)
    if last_date is None:
        return ('no_cycles', 'No cycles', 'No completed cycles on record')

    patient = get_patient_by_db_id(conn, patient_db_id)
    dose_density = patient.dose_density if patient else None

    cfg = get_config().scheduling.model_dump()
    status_code, delta = cycle_status(last_date, dose_density, today, cfg)

    from clinical.scheduling import expected_cycle_date
    expected = expected_cycle_date(last_date, dose_density, cfg)

    if status_code == 'overdue':
        tooltip = (f'Last cycle {last_date.isoformat()} · '
                   f'expected {expected.isoformat()} · '
                   f'{abs(delta)} days overdue')
    elif status_code == 'due_soon':
        tooltip = (f'Last cycle {last_date.isoformat()} · '
                   f'expected {expected.isoformat()} · '
                   f'due in {delta} days')
    else:
        tooltip = (f'Last cycle {last_date.isoformat()} · '
                   f'expected {expected.isoformat()} · '
                   f'{delta} days away')

    return (status_code, _STATUS_TEXT.get(status_code, ''), tooltip)


def status_sort_key(status_code: str) -> int:
    return _STATUS_SORT_KEY.get(status_code, 3)


def status_color(status_code: str) -> str:
    return _STATUS_COLORS.get(status_code, '#6b7494')
