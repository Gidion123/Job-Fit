"""Source-grounded CV parser and review summary. No permanent CV cache."""
from datetime import date
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from jobfit.config import REPO_ROOT
from jobfit.cv.dates import parse_source_date
from jobfit.cv.text_extract import TextResult
from jobfit.llm.structured import StageFailure, validated_call
from jobfit.llm.output_policy import MODEL_OUTPUT_LIMIT, output_allowance, estimate_input_tokens
from jobfit.matching.quote_check import require_quotes
from jobfit.schemas.cv import CVProfile, CVSection, ExperienceEntry, ParseStatus, PartialDate

CV_SCHEMA_VERSION='cv-v1.1-precision'

class SectionText(BaseModel):
    model_config=ConfigDict(extra='forbid')
    section: CVSection
    text: str

class EvidenceFact(BaseModel):
    model_config=ConfigDict(extra='forbid')
    fact_id: str
    section: CVSection
    quote: str

class WorkSpan(BaseModel):
    model_config=ConfigDict(extra='forbid')
    title: str
    organization: str | None
    source_quote: str
    start_text: str | None
    end_text: str | None
    is_present: bool

class CVWire(BaseModel):
    model_config=ConfigDict(extra='forbid')
    language: str | None
    sections: list[SectionText]
    employment: list[WorkSpan]
    skills_list: list[str]
    evidence: list[EvidenceFact]
    location_quote: str | None

class ParsedCV(BaseModel):
    profile: CVProfile
    evidence: list[EvidenceFact]=Field(default_factory=list)
    source_work: list[WorkSpan]=Field(default_factory=list)
    location_suggestion: str | None=None
    analysis_date: date
    schema_version: str=CV_SCHEMA_VERSION
    warnings: list[str]=Field(default_factory=list)
    attempts: int=0
    review_required: bool=True

    def summary(self) -> dict:
        return {'parse_status':self.profile.parse_status.value,'analysis_date':self.analysis_date.isoformat(),
                'sections_found':[s.value for s in self.profile.sections],
                'evidence_count':len(self.evidence),'skills':self.profile.skills_list,
                'employment':[e.model_dump(mode='json') for e in self.profile.experience],
                'location_suggestion':self.location_suggestion,'location_confirmed':self.profile.confirmed_location,
                'review_required':True,'warnings':self.warnings}

def parse_cv(text: TextResult, *, cv_id: str, analysis_date: date, client, model: str,
             is_synthetic: bool, dynamic_output: bool=False) -> ParsedCV:
    if not isinstance(analysis_date,date): raise ValueError('explicit analysis_date required')
    # Synthetic status is supplied by the trusted caller, never inferred from uploaded metadata.
    if not is_synthetic: raise ValueError('Real-CV provider processing needs separate consent; not enabled in CP2.2')
    profile=CVProfile(cv_id=cv_id,is_synthetic=True,raw_text=text.text)
    result=ParsedCV(profile=profile,analysis_date=analysis_date,warnings=list(text.warnings))
    if text.status!='ok' or not text.text.strip():
        profile.parse_status=ParseStatus.FAILED
        return result
    def validate(out):
        if not out.sections or not out.evidence: raise ValueError('no_sections_or_evidence')
        if len({e.fact_id for e in out.evidence})!=len(out.evidence): raise ValueError('duplicate_fact_id')
        for s in out.sections: require_quotes([s.text],text.text)
        for e in out.evidence:
            require_quotes([e.quote],text.text)
            if not any(s.section==e.section and e.quote in s.text for s in out.sections): raise ValueError('evidence_section_mismatch')
        for skill in out.skills_list: require_quotes([skill],text.text)
        if out.location_quote: require_quotes([out.location_quote],text.text)
        for w in out.employment:
            require_quotes([w.source_quote],text.text)
            if not any(s.section==CVSection.EXPERIENCE and w.source_quote in s.text for s in out.sections): raise ValueError('employment_must_be_experience')
            require_quotes([w.title]+([w.organization] if w.organization else []),w.source_quote)
            for d in [w.start_text,w.end_text]:
                if d: require_quotes([d],w.source_quote); parse_source_date(d)
            if w.is_present and (not w.end_text or w.end_text.lower() not in ['present','sekarang','saat ini','current']): raise ValueError('present_not_in_source')
            _entry(w)
    try:
        prompt=(REPO_ROOT/'prompts/cv_parsing_v1.md').read_text()
        payload={'cv_text':text.text}
        max_tokens=(output_allowance('cv_parsing',estimate_input_tokens(prompt,payload,CVWire.model_json_schema()),
                                     max(1,len(text.text.splitlines())//6)) if dynamic_output else 16000)
        out,result.attempts=validated_call(client,model=model,prompt=prompt,payload=payload,
            output_model=CVWire,task='cv_parsing',validate=validate,max_tokens=max_tokens,
            model_output_limit=MODEL_OUTPUT_LIMIT if dynamic_output else None)
    except StageFailure as e:
        result.attempts=e.attempts; profile.parse_status=ParseStatus.FAILED
        result.warnings.append(str(e)); return result
    profile.language=out.language
    for s in out.sections: profile.sections[s.section]='\n'.join(filter(None,[profile.sections.get(s.section),s.text]))
    profile.skills_list=out.skills_list; profile.experience=[_entry(w) for w in out.employment]
    result.source_work=out.employment; result.evidence=out.evidence; result.location_suggestion=out.location_quote
    if any((e.start is None and (not e.start_partial or not e.start_partial.month)) or
           (not e.is_present and e.end is None and (not e.end_partial or not e.end_partial.month)) for e in profile.experience):
        result.warnings.append('Some employment dates lack month precision; duration remains unknown.')
    result.warnings.append('Check that employment, projects, education, dates and skills match the source before analysis.')
    return result

def _entry(w: WorkSpan) -> ExperienceEntry:
    start=parse_source_date(w.start_text);end=None if w.is_present else parse_source_date(w.end_text)
    return ExperienceEntry(title=w.title,organization=w.organization,start=start if isinstance(start,date) else None,
        end=end if isinstance(end,date) else None,start_partial=start if isinstance(start,PartialDate) else None,
        end_partial=end if isinstance(end,PartialDate) else None,start_text=w.start_text,end_text=w.end_text,
        is_present=w.is_present,description=w.source_quote)
