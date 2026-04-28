from dataclasses import dataclass


@dataclass
class NeuropathyAction:
    grade: int
    dose_pct: int
    action_code: str
    advisory_text: str


def effective_grade(sensory: int, motor: int, config: dict) -> int:
    """Return the clinically relevant grade for action lookup.

    When use_higher_grade_for_action is true (default), returns max(sensory, motor).
    """
    raise NotImplementedError


def recommended_action(grade: int, config: dict) -> NeuropathyAction:
    """Map a CTCAE grade to a dose/action recommendation using config.

    Raises ValueError for grades outside 0–4.
    """
    raise NotImplementedError
