"""ANC threshold utilities — shared by the latest labs panel and trend chart."""

# Threshold constants (K/μL)
ANC_THRESHOLD_SEVERE   = 0.5
ANC_THRESHOLD_MODERATE = 1.0
ANC_THRESHOLD_MILD     = 1.5


def get_anc_status(anc_value: float) -> dict:
    """Return color, label, and status key for a given ANC value.

    Parameters
    ----------
    anc_value : float — ANC in K/μL

    Returns
    -------
    dict with keys:
        status : str  — 'normal' | 'mild' | 'moderate' | 'severe'
        color  : str  — hex color code
        label  : str  — human-readable status label
    """
    if anc_value >= ANC_THRESHOLD_MILD:
        return {'status': 'normal',   'color': '#4CAF50', 'label': 'Normal'}
    elif anc_value >= ANC_THRESHOLD_MODERATE:
        return {'status': 'mild',     'color': '#FFC107', 'label': 'Mild Neutropenia'}
    elif anc_value >= ANC_THRESHOLD_SEVERE:
        return {'status': 'moderate', 'color': '#FF9800', 'label': 'Moderate Neutropenia'}
    else:
        return {'status': 'severe',   'color': '#F44336', 'label': 'Severe Neutropenia'}
