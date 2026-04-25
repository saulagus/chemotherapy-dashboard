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
    """Return the doxorubicin-equivalent dose for a single cycle."""
    raise NotImplementedError


def cumulative_doxorubicin_equivalent(
    cycles: list,
    factors: Dict[str, float],
    prior_exposure_mg_per_m2: float = 0.0,
) -> float:
    """Sum doxorubicin-equivalent dose across all non-deleted cycles plus prior exposure."""
    raise NotImplementedError


def cumulative_status(
    total_mg_per_m2: float,
    thresholds: Dict[str, float],
) -> CumulativeStatus:
    """Return green/yellow/red/hard_stop based on cumulative dose vs thresholds."""
    raise NotImplementedError


def lvef_status(
    current_pct: float,
    baseline_pct: Optional[float],
    config: Dict,
) -> Dict:
    """Return {"status": ok|review|hold, "reason": str} based on LVEF thresholds."""
    raise NotImplementedError
