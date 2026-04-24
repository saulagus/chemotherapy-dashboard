"""Pure cardiotoxicity calculation functions.

No database access, no Tkinter imports. Takes primitives in, returns primitives out.
"""

from typing import Dict, Literal, Optional


BsaFormula = Literal["mosteller", "dubois"]
CumulativeStatus = Literal["green", "yellow", "red", "hard_stop"]
LvefStatus = Literal["ok", "review", "hold"]


def compute_bsa(height_cm: float, weight_kg: float, formula: BsaFormula = "mosteller") -> float:
    """Return body surface area in m²."""
    raise NotImplementedError


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
