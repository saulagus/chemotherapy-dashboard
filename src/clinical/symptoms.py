"""Symptom classification rules (US-030).

Pure functions — no DB or Tk imports. Symptom set and advisory thresholds
are read from config; nothing is hardcoded here.
"""


def applicable_symptoms(phase: str, config: dict) -> list:
    """Return the symptom list for the given treatment phase.

    phase: 'AC' or 'T' (case-insensitive).
    T phase appends set_t_phase_additional to the all-phase base set.
    config may be the full toxicity section dict or the symptoms sub-dict.
    """
    sym_cfg = config.get('symptoms', config)
    base = list(sym_cfg.get('set_all_phases', []))

    if phase.upper() == 'T':
        base = base + list(sym_cfg.get('set_t_phase_additional', []))

    return base


def is_advisory(grade: int, config: dict) -> bool:
    """Return True when grade meets or exceeds the advisory threshold in config."""
    sym_cfg        = config.get('symptoms', config)
    advisory_grade = sym_cfg.get('advisory_grade', 3)
    return grade >= advisory_grade
