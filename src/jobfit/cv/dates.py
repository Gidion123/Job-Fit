"""Recognize explicit dates only. Never default missing month/day to January/first."""
from datetime import date
import re
from jobfit.schemas.cv import PartialDate

MONTHS={}
for i,words in enumerate(['january jan januari','february feb februari','march mar maret','april apr','may mei','june jun juni','july jul juli','august aug agustus agu ags','september sep sept','october oct oktober okt','november nov','december dec desember des'],1):
    MONTHS.update({w:i for w in words.split()})

def parse_source_date(text: str | None) -> date | PartialDate | None:
    if not text: return None
    s=text.strip().lower()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',s): return date.fromisoformat(s)
    m=re.fullmatch(r'(\d{4})-(\d{2})',s)
    if m: return PartialDate(year=int(m[1]),month=int(m[2]))
    if re.fullmatch(r'\d{4}',s): return PartialDate(year=int(s))
    m=re.fullmatch(r'([a-z]+)\s+(\d{4})',s)
    if m and m[1] in MONTHS: return PartialDate(year=int(m[2]),month=MONTHS[m[1]])
    m=re.fullmatch(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})',s)
    if m and m[2] in MONTHS: return date(int(m[3]),MONTHS[m[2]],int(m[1]))
    return None
