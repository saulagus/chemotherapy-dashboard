"""Pydantic models for the institutional configuration.

Only fields needed by the current sprint are declared. Later sprints extend
the schema as stories land.
"""

from typing import Dict, List, Literal, Optional

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


class InstitutionConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    institution: InstitutionSection = Field(default_factory=InstitutionSection)
    patient: PatientSection = Field(default_factory=PatientSection)
    cycles: CyclesSection = Field(default_factory=CyclesSection)
    backup: BackupSection = Field(default_factory=BackupSection)
    cardiotoxicity: CardiotoxicitySection = Field(default_factory=CardiotoxicitySection)
