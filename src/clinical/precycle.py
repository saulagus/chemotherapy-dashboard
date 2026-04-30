"""Pre-cycle safety checklist rules (US-033).

Pure functions — no DB or Tk imports. Every threshold and blocking mode
is read from config. Each rule returns a RuleResult; the aggregator
collects them into a ChecklistResult.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

RuleStatus = Literal['pass', 'advisory', 'soft_block', 'hard_block']


@dataclass
class RuleResult:
    rule_id: str
    status: RuleStatus
    message: str
    value: Any = None
    threshold: Any = None


@dataclass
class ChecklistResult:
    rules: List[RuleResult] = field(default_factory=list)
    worst_status: RuleStatus = 'pass'
    can_save_without_override: bool = True


@dataclass
class ChecklistInputs:
    phase: str                                   # 'AC' or 'T'
    cycle_number: int
    dose_density: Optional[str]
    planned_admin_date: date
    latest_anc: Optional[float]                  # K/uL
    latest_platelets: Optional[float]            # K/uL
    latest_lab_draw_date: Optional[date]
    nurse_attests_no_infection: bool
    cumulative_status: Optional[str]             # green|yellow|red|hard_stop
    cumulative_total_mg_per_m2: Optional[float]
    lvef_status: Optional[str]                   # ok|review|hold
    lvef_reason: Optional[str]
    latest_neuropathy_grade: Optional[int]
    latest_symptom_grades: Optional[List[int]]


_STATUS_SEVERITY = {'pass': 0, 'advisory': 1, 'soft_block': 2, 'hard_block': 3}


def _resolve_mode(config_modes: Dict, rule_id: str) -> RuleStatus:
    mode = config_modes.get(rule_id, 'advisory')
    if hasattr(mode, 'value'):
        mode = mode.value
    return mode


def _clamp_status(computed: RuleStatus, configured_mode: RuleStatus) -> RuleStatus:
    if _STATUS_SEVERITY.get(computed, 0) > _STATUS_SEVERITY.get(configured_mode, 0):
        return configured_mode
    return computed


# ---------------------------------------------------------------------------
# Rule 1: ANC below threshold
# ---------------------------------------------------------------------------

def anc_below_threshold(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    precycle = config if 'anc' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'anc_below_threshold')

    if inputs.latest_anc is None:
        return RuleResult(
            rule_id='anc_below_threshold', status='advisory',
            message='No ANC value on record — cannot verify neutrophil count.',
        )

    anc_cfg = precycle['anc']
    anc_value_per_uL = inputs.latest_anc * 1000

    if (inputs.dose_density == 'dose_dense_q2w' and inputs.cycle_number >= 2):
        entry = anc_cfg.get('dose_dense_from_cycle_2', {})
    elif inputs.phase.upper() == 'AC':
        entry = anc_cfg.get('ac', {})
    else:
        entry = anc_cfg.get('t', {})

    threshold = entry.get('min_per_uL', 1500)
    if hasattr(threshold, '__int__'):
        threshold = int(threshold)

    if anc_value_per_uL < threshold:
        raw_status: RuleStatus = 'soft_block'
        status = _clamp_status(raw_status, configured_mode)
        return RuleResult(
            rule_id='anc_below_threshold', status=status,
            message=f'ANC {anc_value_per_uL:.0f} /uL is below {threshold} /uL threshold.',
            value=anc_value_per_uL, threshold=threshold,
        )

    return RuleResult(
        rule_id='anc_below_threshold', status='pass',
        message=f'ANC {anc_value_per_uL:.0f} /uL meets threshold ({threshold} /uL).',
        value=anc_value_per_uL, threshold=threshold,
    )


# ---------------------------------------------------------------------------
# Rule 2: Platelets below threshold
# ---------------------------------------------------------------------------

def platelets_below_threshold(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    precycle = config if 'platelets' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'platelets_below_threshold')

    if inputs.latest_platelets is None:
        return RuleResult(
            rule_id='platelets_below_threshold', status='advisory',
            message='No platelet value on record — cannot verify platelet count.',
        )

    plt_value_per_uL = inputs.latest_platelets * 1000
    threshold = precycle.get('platelets', {}).get('min_per_uL', 100000)
    if hasattr(threshold, '__int__'):
        threshold = int(threshold)

    if plt_value_per_uL < threshold:
        status = _clamp_status('soft_block', configured_mode)
        return RuleResult(
            rule_id='platelets_below_threshold', status=status,
            message=f'Platelets {plt_value_per_uL:.0f} /uL is below {threshold} /uL threshold.',
            value=plt_value_per_uL, threshold=threshold,
        )

    return RuleResult(
        rule_id='platelets_below_threshold', status='pass',
        message=f'Platelets {plt_value_per_uL:.0f} /uL meets threshold ({threshold} /uL).',
        value=plt_value_per_uL, threshold=threshold,
    )


# ---------------------------------------------------------------------------
# Rule 3: Labs stale
# ---------------------------------------------------------------------------

def labs_stale(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    labs_cfg = config if 'freshness_hours' in config else config.get('labs', config)
    precycle = config.get('precycle', config)
    modes = precycle.get('blocking_modes', {}) if precycle != config else config.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'labs_stale')

    if inputs.latest_lab_draw_date is None:
        return RuleResult(
            rule_id='labs_stale', status='advisory',
            message='No labs on record — draw date unknown.',
        )

    freshness_hours = labs_cfg.get('freshness_hours', 72)
    if hasattr(freshness_hours, '__int__'):
        freshness_hours = int(freshness_hours)

    draw = inputs.latest_lab_draw_date
    admin = inputs.planned_admin_date
    if isinstance(draw, datetime):
        draw = draw.date() if hasattr(draw, 'date') else draw
    if isinstance(draw, str):
        draw = date.fromisoformat(draw)
    if isinstance(admin, str):
        admin = date.fromisoformat(admin)

    hours_diff = (admin - draw).days * 24
    if hours_diff > freshness_hours:
        status = _clamp_status('advisory', configured_mode)
        return RuleResult(
            rule_id='labs_stale', status=status,
            message=f'Labs drawn {hours_diff}h before planned admin — exceeds {freshness_hours}h window.',
            value=hours_diff, threshold=freshness_hours,
        )

    return RuleResult(
        rule_id='labs_stale', status='pass',
        message=f'Labs drawn {hours_diff}h before planned admin — within {freshness_hours}h window.',
        value=hours_diff, threshold=freshness_hours,
    )


# ---------------------------------------------------------------------------
# Rule 4: Active infection attestation
# ---------------------------------------------------------------------------

def active_infection(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    precycle = config if 'active_infection' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'active_infection')

    inf_cfg = precycle.get('active_infection', {})
    require = inf_cfg.get('require_nurse_attestation', True)

    if not require:
        return RuleResult(
            rule_id='active_infection', status='pass',
            message='Active-infection attestation not required by config.',
        )

    if not inputs.nurse_attests_no_infection:
        status = _clamp_status('soft_block', configured_mode)
        return RuleResult(
            rule_id='active_infection', status=status,
            message='Nurse has not attested that the patient is infection-free.',
        )

    return RuleResult(
        rule_id='active_infection', status='pass',
        message='Nurse attests patient is infection-free.',
    )


# ---------------------------------------------------------------------------
# Rule 5: Cumulative dose — red zone
# ---------------------------------------------------------------------------

def cumulative_red(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    if inputs.phase.upper() != 'AC':
        return RuleResult(
            rule_id='cumulative_red', status='pass',
            message='Cumulative dose check — T phase, skipped.',
        )

    precycle = config if 'blocking_modes' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'cumulative_red')

    if inputs.cumulative_status in ('red',):
        status = _clamp_status('soft_block', configured_mode)
        total = inputs.cumulative_total_mg_per_m2 or 0
        return RuleResult(
            rule_id='cumulative_red', status=status,
            message=f'Cumulative doxorubicin-equivalent dose {total:.1f} mg/m² in red zone.',
            value=total,
        )

    return RuleResult(
        rule_id='cumulative_red', status='pass',
        message='Cumulative dose not in red zone.',
        value=inputs.cumulative_total_mg_per_m2,
    )


# ---------------------------------------------------------------------------
# Rule 6: Cumulative dose — hard stop
# ---------------------------------------------------------------------------

def cumulative_hard_stop(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    if inputs.phase.upper() != 'AC':
        return RuleResult(
            rule_id='cumulative_hard_stop', status='pass',
            message='Cumulative dose hard-stop — T phase, skipped.',
        )

    precycle = config if 'blocking_modes' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'cumulative_hard_stop')

    if inputs.cumulative_status == 'hard_stop':
        status = _clamp_status('hard_block', configured_mode)
        total = inputs.cumulative_total_mg_per_m2 or 0
        return RuleResult(
            rule_id='cumulative_hard_stop', status=status,
            message=f'Cumulative doxorubicin-equivalent dose {total:.1f} mg/m² exceeds hard-stop limit.',
            value=total,
        )

    return RuleResult(
        rule_id='cumulative_hard_stop', status='pass',
        message='Cumulative dose below hard-stop limit.',
        value=inputs.cumulative_total_mg_per_m2,
    )


# ---------------------------------------------------------------------------
# Rule 7: LVEF abnormal
# ---------------------------------------------------------------------------

def lvef_abnormal(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    if inputs.phase.upper() != 'AC':
        return RuleResult(
            rule_id='lvef_abnormal', status='pass',
            message='LVEF check — T phase, skipped.',
        )

    precycle = config if 'blocking_modes' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'lvef_abnormal')

    if inputs.lvef_status is None:
        return RuleResult(
            rule_id='lvef_abnormal', status='pass',
            message='No LVEF assessments on record.',
        )

    if inputs.lvef_status == 'hold':
        status = _clamp_status('soft_block', configured_mode)
        return RuleResult(
            rule_id='lvef_abnormal', status=status,
            message=inputs.lvef_reason or 'LVEF in hold state.',
        )

    return RuleResult(
        rule_id='lvef_abnormal', status='pass',
        message='LVEF within acceptable range.',
    )


# ---------------------------------------------------------------------------
# Rule 8: Neuropathy (T phase only)
# ---------------------------------------------------------------------------

def neuropathy_t_above_max(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    if inputs.phase.upper() != 'T':
        return RuleResult(
            rule_id='neuropathy_t_above_max', status='pass',
            message='Neuropathy check — AC phase, skipped.',
        )

    precycle = config if 'neuropathy_t_phase_max_grade' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'neuropathy_t_above_max')

    if inputs.latest_neuropathy_grade is None:
        return RuleResult(
            rule_id='neuropathy_t_above_max', status='pass',
            message='No neuropathy assessment on record — assumed safe.',
        )

    max_grade = precycle.get('neuropathy_t_phase_max_grade', 1)
    if hasattr(max_grade, '__int__'):
        max_grade = int(max_grade)

    if inputs.latest_neuropathy_grade > max_grade:
        status = _clamp_status('soft_block', configured_mode)
        return RuleResult(
            rule_id='neuropathy_t_above_max', status=status,
            message=f'Neuropathy grade {inputs.latest_neuropathy_grade} exceeds max allowed G{max_grade} for T phase.',
            value=inputs.latest_neuropathy_grade, threshold=max_grade,
        )

    return RuleResult(
        rule_id='neuropathy_t_above_max', status='pass',
        message=f'Neuropathy grade {inputs.latest_neuropathy_grade} within allowed G{max_grade}.',
        value=inputs.latest_neuropathy_grade, threshold=max_grade,
    )


# ---------------------------------------------------------------------------
# Rule 9: Symptoms grade 3+
# ---------------------------------------------------------------------------

def symptoms_grade_3_or_higher(inputs: ChecklistInputs, config: Dict) -> RuleResult:
    precycle = config if 'symptoms_advisory_grade' in config else config.get('precycle', config)
    modes = precycle.get('blocking_modes', {})
    configured_mode = _resolve_mode(modes, 'symptoms_grade_3_or_higher')

    if not inputs.latest_symptom_grades:
        return RuleResult(
            rule_id='symptoms_grade_3_or_higher', status='pass',
            message='No symptom data on record.',
        )

    advisory_grade = precycle.get('symptoms_advisory_grade', 3)
    if hasattr(advisory_grade, '__int__'):
        advisory_grade = int(advisory_grade)

    high = [g for g in inputs.latest_symptom_grades if g >= advisory_grade]
    if high:
        status = _clamp_status('advisory', configured_mode)
        return RuleResult(
            rule_id='symptoms_grade_3_or_higher', status=status,
            message=f'{len(high)} symptom(s) at grade {advisory_grade} or higher.',
            value=max(high), threshold=advisory_grade,
        )

    return RuleResult(
        rule_id='symptoms_grade_3_or_higher', status='pass',
        message=f'All symptoms below grade {advisory_grade}.',
        threshold=advisory_grade,
    )


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

_ALL_RULES = [
    anc_below_threshold,
    platelets_below_threshold,
    labs_stale,
    active_infection,
    cumulative_red,
    cumulative_hard_stop,
    lvef_abnormal,
    neuropathy_t_above_max,
    symptoms_grade_3_or_higher,
]


def run_checklist(inputs: ChecklistInputs, config: Dict) -> ChecklistResult:
    """Run all pre-cycle rules and aggregate results."""
    results: List[RuleResult] = []
    for rule_fn in _ALL_RULES:
        results.append(rule_fn(inputs, config))

    worst = 'pass'
    for r in results:
        if _STATUS_SEVERITY.get(r.status, 0) > _STATUS_SEVERITY.get(worst, 0):
            worst = r.status

    can_save = worst in ('pass', 'advisory')

    return ChecklistResult(rules=results, worst_status=worst, can_save_without_override=can_save)
