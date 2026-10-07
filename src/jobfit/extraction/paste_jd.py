"""Session-only paste preview. Uses existing CP1 cleaning, never changes the corpus."""
from dataclasses import dataclass
import re
from jobfit.extraction.cache import content_hash
from jobfit.extraction.jd_extractor import ExtractionResult, extract_jd
from jobfit.jobs.cleaning import clean_description

@dataclass
class PastePreview:
    job_id: str
    cleaned_text: str
    applied_rules: list[str]
    warnings: list[str]
    result: ExtractionResult

def preview_pasted_jd(text: str, *, client, model: str, cache=None, extraction_spec=None) -> PastePreview:
    cleaned,rules=clean_description(text)
    job_id='PASTE-'+content_hash(cleaned)[:20]
    warnings=[]
    if len(cleaned)<200: warnings.append('Short text: check completeness; length alone does not reject the JD.')
    if not re.search(r'requirement|qualification|kualifikasi|persyaratan|looking for|what you bring',cleaned,re.I):
        warnings.append('No clear requirement heading found. Check the extraction preview.')
    result=extract_jd(cleaned,job_id=job_id,client=client,model=model,cache=cache,scope='session_jd',spec=extraction_spec)
    if result.extraction and not result.extraction.units:
        warnings.append('No assessable requirements found. Paste the full requirements if available.')
    return PastePreview(job_id,cleaned,rules,warnings,result)
