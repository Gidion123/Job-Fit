"""Request models of the API (CP3.1). Responses are plain JSON built in api/presenter.py."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MAX_PASTE_CHARS = 20_000
MIN_PASTE_CHARS = 200


class RunRequest(BaseModel):
    demo_cv_id: str
    seniority_rule: bool = True
    mode: Literal['saved', 'live'] = 'saved'
    # D-010 optional filters; empty means no filter. Unknown values are kept unless include_unknown is false.
    role_family: str | None = None
    country_code: str | None = None
    city: str | None = None
    work_mode: str | None = None
    posted_within_days: int | None = None
    include_unknown: bool = True


class ConsentRequest(BaseModel):
    digest: str
    affirmative: bool


class PreviewEdit(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class PasteRequest(BaseModel):
    jd_text: str = Field(min_length=MIN_PASTE_CHARS, max_length=MAX_PASTE_CHARS)


class AnalyzeRequest(BaseModel):
    paste_id: str
    demo_cv_id: str


class TailorRequest(BaseModel):
    run_id: str
    job_id: str | None = None     # with a job: CV coach v1 questions for that job (D-036)


class CoachAnswer(BaseModel):
    run_id: str
    job_id: str
    gap_index: int = Field(ge=0, le=2)
    done: bool
    answers: dict[str, str | None] = Field(default_factory=dict)


class MarketQuery(BaseModel):
    role_family: str | None = None
    top: int = Field(default=15, ge=1, le=50)


class FeedbackRequest(BaseModel):
    run_id: str
    job_id: str | None = None
    rating: Literal['useful', 'not_useful']
    # Categories only, no free text: feedback must never carry CV content or identifiers (D-051).
    reason: Literal['relevant', 'not_relevant_role', 'too_senior', 'wrong_evidence', 'missing_requirement', 'other'] = 'other'
