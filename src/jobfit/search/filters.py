"""Optional CP1-metadata filters with explicit unknown/conflict states (D-010)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Mapping


class FilterState(str, Enum):
    MATCHES='matches'
    UNKNOWN='unknown'
    CONFLICTS='conflicts'


@dataclass(frozen=True)
class JobFilters:
    role_family: str | None=None
    country_code: str | None=None
    city: str | None=None
    experience_bucket: str | None=None
    work_mode: str | None=None
    posted_within_days: int | None=None
    include_unknown: bool=True

    def __post_init__(self):
        if self.role_family is not None and self.role_family not in {'ai_ml_engineering','data_science','genai_llm','software_ai'}:
            raise ValueError('Only the four approved target role families are supported')
        if self.country_code is not None and (len(self.country_code)!=2 or not self.country_code.isalpha()):
            raise ValueError('Country must be a two-letter code')
        if self.city is not None and not self.city.strip():raise ValueError('Empty city filter')
        if self.experience_bucket is not None and self.experience_bucket not in {'entry','1-2y','3-4y','5y+'}:
            raise ValueError('Unapproved experience bucket')
        if self.work_mode is not None and self.work_mode not in {'onsite','hybrid','remote'}:
            raise ValueError('Unapproved work mode')
        if self.posted_within_days is not None and self.posted_within_days not in (7,30):
            raise ValueError('Posting window must be 7, 30 or all')

    @property
    def active(self):
        return tuple(k for k in ('role_family','country_code','city','experience_bucket','work_mode','posted_within_days')
                     if getattr(self,k) is not None)


@dataclass(frozen=True)
class FilteredJob:
    job_id: str
    status: FilterState
    per_filter: dict[str,FilterState]


@dataclass(frozen=True)
class FilterResult:
    matches: tuple[FilteredJob,...]
    unknown: tuple[FilteredJob,...]
    conflicts: tuple[FilteredJob,...]
    active_filters: tuple[str,...]
    include_unknown: bool

    @property
    def eligible_ids(self):
        return tuple(x.job_id for x in self.matches+(self.unknown if self.include_unknown else ()))

    @property
    def empty_message(self):
        if self.eligible_ids:return None
        return ('No jobs meet the active filters. Change them; the system did not widen the search.'
                if self.active_filters else 'No target-role jobs are available in this corpus.')


def _unknown(value):
    return value is None or str(value).strip().lower() in {'','unknown','not_stated','not stated'}


def _country(job):
    geo=job.get('analysis_geo')
    if geo=='indonesia':return 'ID'
    if geo in {'unknown','remote_unverified',None}:return None
    code=job.get('country_code') or job.get('country')
    return code.upper() if isinstance(code,str) and len(code)==2 and code.isalpha() else None


def _posted(job):
    raw=job.get('posted_at')
    if _unknown(raw):return None
    if isinstance(raw,datetime):return raw.date()
    if isinstance(raw,date):return raw
    if isinstance(raw,str):
        try:return date.fromisoformat(raw[:10])
        except ValueError:return None
    return None


def filter_status(job: Mapping, filters: JobFilters, *, analysis_date: date) -> FilteredJob:
    if type(analysis_date) is not date:raise ValueError('Explicit analysis date required')
    job_id=job.get('final_cluster_id') or job.get('job_id')
    if not isinstance(job_id,str) or not job_id:raise ValueError('Job identity required')
    checks={}
    def check(name,value,wanted):
        checks[name]=FilterState.UNKNOWN if _unknown(value) else FilterState.MATCHES if value==wanted else FilterState.CONFLICTS
    if filters.role_family is not None:check('role_family',job.get('role_family'),filters.role_family)
    if filters.country_code is not None:check('country_code',_country(job),filters.country_code.upper())
    if filters.city is not None:
        city=job.get('city_normalized')
        check('city',city.casefold() if isinstance(city,str) else city,filters.city.strip().casefold())
    if filters.experience_bucket is not None:check('experience_bucket',job.get('experience_bucket'),filters.experience_bucket)
    if filters.work_mode is not None:
        mode=job.get('work_mode')
        check('work_mode',None if mode=='remote_mentioned' else mode,filters.work_mode)
    if filters.posted_within_days is not None:
        posted=_posted(job)
        checks['posted_within_days']=(FilterState.UNKNOWN if posted is None or posted>analysis_date else
            FilterState.MATCHES if posted>=analysis_date-timedelta(days=filters.posted_within_days) else FilterState.CONFLICTS)
    state=(FilterState.CONFLICTS if FilterState.CONFLICTS in checks.values() else
           FilterState.UNKNOWN if FilterState.UNKNOWN in checks.values() else FilterState.MATCHES)
    return FilteredJob(job_id,state,checks)


def filter_jobs(jobs: list[Mapping], filters: JobFilters, *, analysis_date: date) -> FilterResult:
    seen=set();matched=[];unknown=[];conflicts=[]
    for job in jobs:
        if job.get('role_group')!='target':raise ValueError('Caller must supply only target-role jobs')
        item=filter_status(job,filters,analysis_date=analysis_date)
        if item.job_id in seen:raise ValueError('Duplicate job identity')
        seen.add(item.job_id)
        {FilterState.MATCHES:matched,FilterState.UNKNOWN:unknown,FilterState.CONFLICTS:conflicts}[item.status].append(item)
    return FilterResult(tuple(matched),tuple(unknown),tuple(conflicts),filters.active,filters.include_unknown)
