"""Pydantic models for the institutional configuration.

Only fields needed by the current sprint are declared. Later sprints extend
the schema as stories land.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class InstitutionSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = "Default Institution"


class PatientSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id_regex: str = r'^PT-\d{3,}$'


DoseDensityOption = Literal['standard_q3w', 'dose_dense_q2w']


class CyclesSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dose_density_options: List[DoseDensityOption] = Field(
        default_factory=lambda: ['standard_q3w', 'dose_dense_q2w']
    )


class BackupSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reminder_interval_days: int = Field(default=7, ge=1, le=365)


class CumulativeThresholdsSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    yellow: float = 300.0
    red: float = 400.0
    hard_stop: float = 450.0


class LvefSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    absolute_hold_pct: float = 50.0
    delta_hold_pct: float = 10.0
    delta_hold_absolute_ceiling_pct: float = 55.0
    review_flag_delta_pct: float = 16.0


BlockingMode = Literal['advisory', 'soft_block', 'hard_block']


class BlockingModesSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cumulative_yellow: BlockingMode = 'advisory'
    cumulative_red: BlockingMode = 'soft_block'
    cumulative_hard_stop: BlockingMode = 'hard_block'
    lvef_absolute: BlockingMode = 'soft_block'
    lvef_delta: BlockingMode = 'soft_block'


class CardiotoxicitySection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    bsa_formula: Literal['mosteller', 'dubois'] = 'mosteller'
    weight_change_warning_pct: float = 10.0
    cumulative_thresholds_mg_per_m2: CumulativeThresholdsSection = Field(
        default_factory=CumulativeThresholdsSection
    )
    equivalence_factors: Dict[str, float] = Field(
        default_factory=lambda: {
            'doxorubicin': 1.0,
            'epirubicin': 0.5,
            'daunorubicin': 0.5,
            'idarubicin': 5.0,
            'mitoxantrone': 4.0,
        }
    )
    lvef: LvefSection = Field(default_factory=LvefSection)
    blocking_modes: BlockingModesSection = Field(default_factory=BlockingModesSection)


# ---------------------------------------------------------------------------
# Toxicity section (Sprint 7 — US-027–030)
# ---------------------------------------------------------------------------

class NeuropathyGradeAction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dose_pct: int = Field(ge=0, le=100)
    action: str


class NeuropathySection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    grade_actions: Dict[int, NeuropathyGradeAction] = Field(
        default_factory=lambda: {
            0: NeuropathyGradeAction(dose_pct=100, action='continue'),
            1: NeuropathyGradeAction(dose_pct=100, action='continue'),
            2: NeuropathyGradeAction(dose_pct=80,  action='hold_one_cycle_then_resume'),
            3: NeuropathyGradeAction(dose_pct=75,  action='hold_until_recovered_then_resume_discontinue_on_recurrence'),
            4: NeuropathyGradeAction(dose_pct=0,   action='discontinue_permanently'),
        }
    )
    use_higher_grade_for_action: bool = True


class RechallengeRule(BaseModel):
    model_config = ConfigDict(extra='forbid')
    rechallenge: bool
    rate_pct: Optional[int] = None
    premed_enhance: bool = False
    switch_agent_to: Optional[str] = None
    hard_block: bool = False


class InfusionReactionsSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    symptom_vocab: List[str] = Field(
        default_factory=lambda: [
            'flushing', 'urticaria', 'hypotension', 'hypertension',
            'dyspnea', 'bronchospasm', 'back_pain', 'chest_pain', 'anaphylaxis',
        ]
    )
    rechallenge_policy: Dict[int, RechallengeRule] = Field(
        default_factory=lambda: {
            1: RechallengeRule(rechallenge=True,  rate_pct=50, premed_enhance=False),
            2: RechallengeRule(rechallenge=True,  rate_pct=50, premed_enhance=True),
            3: RechallengeRule(rechallenge=False, switch_agent_to='nab_paclitaxel_or_docetaxel'),
            4: RechallengeRule(rechallenge=False, switch_agent_to='nab_paclitaxel_or_docetaxel', hard_block=True),
        }
    )


class GcsfPolicySection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dose_dense_q2w: str = 'primary'
    standard_q3w: str = 'secondary'


class GcsfSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    agent_vocab: List[str] = Field(
        default_factory=lambda: ['pegfilgrastim', 'filgrastim', 'lipegfilgrastim']
    )
    policy: GcsfPolicySection = Field(default_factory=GcsfPolicySection)
    stimulated_window_days: int = Field(default=7, ge=1)


class SymptomsSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    set_all_phases: List[str] = Field(
        default_factory=lambda: ['nausea', 'fatigue', 'mucositis', 'constipation']
    )
    set_t_phase_additional: List[str] = Field(
        default_factory=lambda: ['arthralgia', 'peripheral_edema']
    )
    advisory_grade: int = Field(default=3, ge=0, le=4)


class ToxicityBlockingModesSection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    neuropathy_grade_2: BlockingMode = 'advisory'
    neuropathy_grade_3_before_t: BlockingMode = 'soft_block'
    neuropathy_grade_4: BlockingMode = 'hard_block'
    infusion_reaction_grade_4: BlockingMode = 'hard_block'
    symptoms_grade_3_or_higher: BlockingMode = 'advisory'


class ToxicitySection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    ctcae_version: str = '5.0'
    neuropathy: NeuropathySection = Field(default_factory=NeuropathySection)
    infusion_reactions: InfusionReactionsSection = Field(default_factory=InfusionReactionsSection)
    gcsf: GcsfSection = Field(default_factory=GcsfSection)
    symptoms: SymptomsSection = Field(default_factory=SymptomsSection)
    blocking_modes: ToxicityBlockingModesSection = Field(default_factory=ToxicityBlockingModesSection)


# ---------------------------------------------------------------------------

class InstitutionConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    institution: InstitutionSection = Field(default_factory=InstitutionSection)
    patient: PatientSection = Field(default_factory=PatientSection)
    cycles: CyclesSection = Field(default_factory=CyclesSection)
    backup: BackupSection = Field(default_factory=BackupSection)
    cardiotoxicity: CardiotoxicitySection = Field(default_factory=CardiotoxicitySection)
    toxicity: ToxicitySection = Field(default_factory=ToxicitySection)
