"""Neuropathy grading rules (US-027).

Pure functions — no DB or Tk imports. All thresholds and action mappings
are read from the config dict; nothing is hardcoded here.
"""

from dataclasses import dataclass


@dataclass
class NeuropathyAction:
    grade: int
    dose_pct: int
    action_code: str
    advisory_text: str


_ACTION_LABELS = {
    'continue': 'Continue at current dose.',
    'hold_one_cycle_then_resume': 'Hold one cycle, then resume at {dose_pct}% dose.',
    'hold_until_recovered_then_resume_discontinue_on_recurrence': (
        'Hold until recovered (≤G1), resume at {dose_pct}% dose; '
        'discontinue permanently on recurrence.'
    ),
    'discontinue_permanently': 'Discontinue treatment permanently.',
}


def effective_grade(sensory: int, motor: int, config: dict) -> int:
    """Return the clinically relevant grade for action lookup.

    When use_higher_grade_for_action is True (default), returns max(sensory, motor).
    Both grades must be 0–4; raises ValueError otherwise.
    """
    for name, val in (('sensory', sensory), ('motor', motor)):
        if not isinstance(val, int) or not (0 <= val <= 4):
            raise ValueError(f"{name}_grade must be an integer 0–4, got {val!r}")

    neuro_cfg = config.get('neuropathy', config)  # accept both full toxicity dict and sub-dict
    use_higher = neuro_cfg.get('use_higher_grade_for_action', True)
    return max(sensory, motor) if use_higher else sensory


def recommended_action(grade: int, config: dict) -> NeuropathyAction:
    """Map a CTCAE grade (0–4) to a dose/action recommendation.

    config may be the full toxicity section dict or the neuropathy sub-dict.
    Raises ValueError for grades outside 0–4.
    """
    if not isinstance(grade, int) or not (0 <= grade <= 4):
        raise ValueError(f"grade must be an integer 0–4, got {grade!r}")

    neuro_cfg = config.get('neuropathy', config)
    grade_actions = neuro_cfg.get('grade_actions', {})

    entry = grade_actions.get(grade)
    if entry is None:
        raise ValueError(f"No grade_action entry for grade {grade} in config")

    # entry may be a Pydantic model (NeuropathyGradeAction) or a plain dict
    if hasattr(entry, 'dose_pct'):
        dose_pct = entry.dose_pct
        action_code = entry.action
    else:
        dose_pct = entry['dose_pct']
        action_code = entry['action']

    template = _ACTION_LABELS.get(action_code, action_code)
    advisory_text = template.format(dose_pct=dose_pct)

    return NeuropathyAction(
        grade=grade,
        dose_pct=dose_pct,
        action_code=action_code,
        advisory_text=advisory_text,
    )
