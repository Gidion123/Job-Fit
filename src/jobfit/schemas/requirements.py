"""Requirement units extracted from a job description (System Design v1.3, section 6).

A unit is atomic when it can be judged on its own without losing meaning.
The score only counts units with importance == required.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Importance(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    UNKNOWN = "unknown"  # not forced into required; kept out of the denominator


class UnitKind(str, Enum):
    SIMPLE = "simple"
    ALTERNATIVE_GROUP = "alternative_group"  # "Python or Java", "S1 or equivalent experience"
    QUALIFIED = "qualified"  # "3 years of Python": skill and duration stay together


class RequirementField(str, Enum):
    SKILL = "skill"
    TOOL = "tool"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    LANGUAGE = "language"
    CERTIFICATION = "certification"
    DOMAIN = "domain"
    SOFT_SKILL = "soft_skill"
    OTHER = "other"


class JDQuality(str, Enum):
    OK = "ok"
    LOOKS_INCOMPLETE = "looks_incomplete"


class RequirementBranch(BaseModel):
    """One option inside an alternative group."""

    branch_id: str
    text: str
    field: RequirementField = RequirementField.OTHER
    min_years: float | None = Field(default=None, ge=0)


class RequirementUnit(BaseModel):
    unit_id: str
    text: str = Field(min_length=1)
    kind: UnitKind = UnitKind.SIMPLE
    importance: Importance
    field: RequirementField = RequirementField.OTHER
    normalized_name: str | None = None  # used to merge repeated requirements
    min_years: float | None = Field(default=None, ge=0)
    branches: list[RequirementBranch] = Field(default_factory=list)
    source_quotes: list[str] = Field(default_factory=list)  # word for word from the JD
    needs_review: bool = False
    ai_suggested: bool = False

    @model_validator(mode="after")
    def _check_kind(self) -> "RequirementUnit":
        if self.kind == UnitKind.ALTERNATIVE_GROUP and len(self.branches) < 2:
            raise ValueError("an alternative group needs at least two branches")
        if self.kind != UnitKind.ALTERNATIVE_GROUP and self.branches:
            raise ValueError("only an alternative group can have branches")
        if self.kind == UnitKind.QUALIFIED and self.min_years is None:
            raise ValueError("a qualified unit needs min_years")
        return self


class JDExtraction(BaseModel):
    job_id: str
    units: list[RequirementUnit] = Field(default_factory=list)
    jd_quality: JDQuality = JDQuality.OK
    extractor_version: str = "manual"

    @model_validator(mode="after")
    def _unique_ids(self) -> "JDExtraction":
        ids = [u.unit_id for u in self.units]
        if len(ids) != len(set(ids)):
            raise ValueError("unit_id values must be unique within a job")
        return self
