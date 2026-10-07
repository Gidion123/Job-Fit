"""Optional experimental wire coverage; public requirement/scoring schema unchanged."""
from dataclasses import dataclass
from pathlib import Path
import re
from pydantic import BaseModel,ConfigDict
from jobfit.schemas.requirements import JDExtraction

@dataclass(frozen=True)
class ExtractionSpec:
    prompt_file: Path
    prompt_version: str
    coverage_contract: str='qualification-inventory-v1'

class SourceCoverage(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_id: str
    unit_ids: list[str]

class AuditedExtraction(JDExtraction):
    qualification_coverage: list[SourceCoverage]


def qualification_inventory(text, *, include_preferred_heading=True):
    """Explicit heading/list inventory, with exact quotes; no gold label input.

    Stops at the next standalone heading. Wrapped nonblank bullet content stays
    in its original paragraph. Unsupported prose is left for semantic review.
    """
    headings=('qualifications?(?:\\s+and\\s+requirements)?|requirements?|kualifikasi|'
              'persyaratan|the successful applicant|about you')
    if include_preferred_heading:
        headings+='|preferred\\s+competencies\\s+and\\s+qualifications'
    start=re.compile(r'(?i)^(?:required\s+)?(?:'+headings+r')\s*:?$')
    bullet=re.compile(r'^\s*(?:[•*\-]|\d+[.)])\s+(.+)')
    records=[];active=False;current=None
    for raw in text.splitlines():
        line=raw.strip()
        if start.fullmatch(line.strip('#* ').strip()):active=True;current=None;continue
        if not active or not line:continue
        match=bullet.match(raw)
        if match:
            records.append({'source_id':f'Q{len(records)+1:02d}','source_quote':match.group(1)})
            current=records[-1]
        elif not records and line.lower()=='the company is looking for candidates with the following skills and qualifications:':
            continue
        elif raw[:1].isspace() and current:
            current['source_quote']+='\n'+raw
        else:active=False;current=None
    return records


def qualification_inventory_v1(text):
    """Frozen Stage-2 plan inventory, before the v1.1 heading addition.

    Only the historical planning code calls this. Current JD extraction keeps
    the stronger source check; no saved Stage-2 plan or prompt is rewritten.
    """
    return qualification_inventory(text, include_preferred_heading=False)


def validate_inventory(out,inventory):
    expected={x['source_id']:x['source_quote'] for x in inventory}
    checks=out.qualification_coverage
    if len(checks)!=len(expected) or {c.source_id for c in checks}!=set(expected):
        raise ValueError('qualification_inventory_incomplete')
    units={u.unit_id:u for u in out.units}
    for check in checks:
        if not check.unit_ids or len(set(check.unit_ids))!=len(check.unit_ids):
            raise ValueError('qualification_inventory_incomplete')
        for uid in check.unit_ids:
            if uid not in units:raise ValueError('qualification_inventory_incomplete')
            if not any(q in expected[check.source_id] or expected[check.source_id] in q for q in units[uid].source_quotes):
                raise ValueError('qualification_inventory_unsupported_mapping')
    # Coverage receipts only attest representation, not semantic correctness.
