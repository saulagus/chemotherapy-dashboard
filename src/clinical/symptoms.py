def applicable_symptoms(phase: str, config: dict) -> list[str]:
    """Return the symptom list for the given treatment phase.

    phase: 'AC' or 'T'. T phase appends set_t_phase_additional to the base set.
    """
    raise NotImplementedError


def is_advisory(grade: int, config: dict) -> bool:
    """Return True when grade meets or exceeds the advisory threshold in config."""
    raise NotImplementedError
