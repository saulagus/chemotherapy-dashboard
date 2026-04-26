"""Pure cardiotoxicity calculation functions.

No database access, no Tkinter imports. Takes primitives in, returns primitives out.
"""

import math
from typing import Dict, Literal, Optional


BsaFormula = Literal["mosteller", "dubois"]
CumulativeStatus = Literal["green", "yellow", "red", "hard_stop"]
LvefStatus = Literal["ok", "review", "hold"]


def compute_bsa(height_cm: float, weight_kg: float, formula: BsaFormula = "mosteller") -> float:
    """Return body surface area in m².

    Mosteller:  BSA = sqrt(height_cm * weight_kg / 3600)
    DuBois:     BSA = 0.007184 * height_cm^0.725 * weight_kg^0.425

    Raises ValueError for non-positive height or weight.
    """
    if height_cm <= 0:
        raise ValueError(f"height_cm must be > 0, got {height_cm}")
    if weight_kg <= 0:
        raise ValueError(f"weight_kg must be > 0, got {weight_kg}")
    if formula == "mosteller":
        return math.sqrt(height_cm * weight_kg / 3600.0)
    if formula == "dubois":
        return 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425)
    raise ValueError(f"Unknown BSA formula: {formula!r}")


def to_doxorubicin_equivalent(
    agent: str,
    dose_mg_per_m2: float,
    factors: Dict[str, float],
) -> float:
    """Return the doxorubicin-equivalent dose for a single cycle.

    Agent lookup is case-insensitive. Raises ValueError for unknown agents.
    """
    key = agent.lower()
    if key not in factors:
        raise ValueError(
            f"Unknown agent {agent!r}. Known agents: {sorted(factors.keys())}"
        )
    return dose_mg_per_m2 * factors[key]


def cumulative_doxorubicin_equivalent(
    cycles: list,
    factors: Dict[str, float],
    prior_exposure_mg_per_m2: float = 0.0,
) -> float:
    """Sum doxorubicin-equivalent dose across all cycles plus prior exposure.

    Cycles without anthracycline_agent or dose_mg_per_m2 are silently skipped
    (e.g. Taxane-only cycles, or cycles where dose data was not recorded).
    Hard-deleted cycles are excluded automatically because they never appear
    in the list returned by get_cycles_by_patient.
    prior_exposure_mg_per_m2 defaults to 0 and treats None as 0.
    """
    total = float(prior_exposure_mg_per_m2 or 0.0)
    for cycle in cycles:
        if cycle.anthracycline_agent and cycle.dose_mg_per_m2:
            total += to_doxorubicin_equivalent(
                cycle.anthracycline_agent, cycle.dose_mg_per_m2, factors
            )
    return total


def cumulative_status(
    total_mg_per_m2: float,
    thresholds: Dict[str, float],
) -> CumulativeStatus:
    """Return green/yellow/red/hard_stop based on cumulative dose vs thresholds.

    Thresholds dict must contain keys: yellow, red, hard_stop (all in mg/m²).
    Evaluation is highest-severity first so a value at exactly the hard_stop
    boundary is returned as 'hard_stop', not 'red'.
    """
    if total_mg_per_m2 >= thresholds['hard_stop']:
        return 'hard_stop'
    if total_mg_per_m2 >= thresholds['red']:
        return 'red'
    if total_mg_per_m2 >= thresholds['yellow']:
        return 'yellow'
    return 'green'


def lvef_status(
    current_pct: float,
    baseline_pct: Optional[float],
    config: Dict,
) -> Dict:
    """Return {"status": ok|review|hold, "reason": str} based on LVEF thresholds.

    Evaluation order (highest severity first):
      1. Absolute hold: current < absolute_hold_pct
      2. Delta hold:    drop >= delta_hold_pct AND current < delta_hold_absolute_ceiling_pct
      3. Review flag:   drop >= review_flag_delta_pct
      4. Ok
    All thresholds read from config dict (keys match LvefSection field names).
    """
    absolute_hold = config['absolute_hold_pct']
    delta_hold = config['delta_hold_pct']
    ceiling = config['delta_hold_absolute_ceiling_pct']
    review_flag = config['review_flag_delta_pct']

    if current_pct < absolute_hold:
        return {
            'status': 'hold',
            'reason': (
                f"LVEF {current_pct}% is below absolute hold threshold "
                f"({absolute_hold}%)"
            ),
        }

    if baseline_pct is not None:
        drop = baseline_pct - current_pct
        if drop >= delta_hold and current_pct < ceiling:
            return {
                'status': 'hold',
                'reason': (
                    f"LVEF dropped {drop:.1f}pp from baseline "
                    f"({baseline_pct}%) and is below {ceiling}%"
                ),
            }
        if drop >= review_flag:
            return {
                'status': 'review',
                'reason': (
                    f"LVEF dropped {drop:.1f}pp from baseline "
                    f"({baseline_pct}%)"
                ),
            }

    return {'status': 'ok', 'reason': ''}
