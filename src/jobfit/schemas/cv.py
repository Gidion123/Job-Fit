"""Parsed CV (System Design v1.3, sections 3 and 7). Default input is a synthetic CV (D-021)."""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ParseStatus(str, Enum):
    OK = "ok"
    FAILED = "failed"


class CVSection(str, Enum):
    SUMMARY = "Summary"
    EXPERIENCE = "Experience"
    PROJECTS = "Projects"
    EDUCATION = "Education"
    SKILLS = "Skills"
    CERTIFICATIONS = "Certifications"
    OTHER = "Other"


class PartialDate(BaseModel):
    """Original year or month precision. Never manufacture the missing day."""
    year: int = Field(ge=1, le=9999)
    month: int | None = Field(default=None, ge=1, le=12)


class ExperienceEntry(BaseModel):
    title: str
    organization: str | None = None
    start: date | None = None  # incomplete dates stay None, no false precision
    end: date | None = None
    is_present: bool = False  # "present/sekarang" is resolved with the analysis date
    description: str = ""
    start_partial: PartialDate | None = None
    end_partial: PartialDate | None = None
    start_text: str | None = None
    end_text: str | None = None

    @model_validator(mode="after")
    def _check_dates(self) -> "ExperienceEntry":
        if self.is_present and self.end is not None:
            raise ValueError("an entry cannot have both an end date and is_present")
        if self.start and self.end and self.end < self.start:
            raise ValueError("end date is before start date")
        if self.start and self.start_partial or self.end and self.end_partial:
            raise ValueError("use full or partial precision, never both")
        if self.is_present and self.end_partial:
            raise ValueError("present cannot have a partial end")
        start = self.start or self.start_partial
        end = self.end or self.end_partial
        if start and end and (end.year < start.year or
                (end.year == start.year and end.month and start.month and end.month < start.month)):
            raise ValueError("end precedes start at available precision")
        return self


class CVProfile(BaseModel):
    cv_id: str
    is_synthetic: bool = True
    language: str | None = None  # "id" or "en"
    parse_status: ParseStatus = ParseStatus.OK
    raw_text: str = ""
    sections: dict[CVSection, str] = Field(default_factory=dict)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills_list: list[str] = Field(default_factory=list)
    confirmed_location: str | None = None  # only what the user confirmed, never auto-applied
