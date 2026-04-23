"""Pydantic models for the institutional configuration.

Only fields needed by the current sprint are declared. Later sprints extend
the schema (cardiotoxicity thresholds, CTCAE version, etc.) as stories land.
"""

from typing import List, Literal

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


class InstitutionConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    institution: InstitutionSection = Field(default_factory=InstitutionSection)
    patient: PatientSection = Field(default_factory=PatientSection)
    cycles: CyclesSection = Field(default_factory=CyclesSection)
    backup: BackupSection = Field(default_factory=BackupSection)
