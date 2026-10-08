"""D-103 public-beta input envelopes, enforced at runtime with the canonical size measure.

Every size here is ``jobfit.llm.document_bytes.document_bytes``: the UTF-8 bytes a value adds to the
frozen guard's measured messages (the same measure the public-beta bounds calculator uses). Nothing
is ever truncated: an input above its envelope is refused before any reservation, and an extraction
above its envelope holds the job before the Sol matching call. Text that cannot be encoded as UTF-8
does not fit (the frozen guard would fail on it too).
"""
from __future__ import annotations

from jobfit.llm.document_bytes import document_bytes
from jobfit.llm.public_beta_bounds import BetaEnvelopes

INPUT_TOO_LARGE = 'input_too_large'
EXTRACTION_HOLD = 'beta_envelope_exceeded'


def _within(value, limit: int) -> bool:
    try:
        return document_bytes(value) <= limit
    except (UnicodeEncodeError, TypeError, ValueError):
        return False


def _short(value, env: BetaEnvelopes) -> bool:
    return isinstance(value, str) and len(value) <= env.short_field_max_chars


def cv_fits(env: BetaEnvelopes, cv_text: str, cv_id: str) -> bool:
    """The consented masked CV text (parse, search and matching payloads) and its id."""
    return isinstance(cv_text, str) and _within(cv_text, env.cv_document_max_bytes) and _short(cv_id, env)


def jd_fits(env: BetaEnvelopes, jd_text: str, job_id: str) -> bool:
    """One JD text for the frozen extract_jd: bytes, the frozen inventory size and the job id."""
    from jobfit.extraction.audited import qualification_inventory
    if not (isinstance(jd_text, str) and _within(jd_text, env.jd_document_max_bytes) and _short(job_id, env)):
        return False
    try:
        return len(qualification_inventory(jd_text)) <= env.max_inventory_items
    except Exception:
        return False


def extraction_fits(env: BetaEnvelopes, extraction) -> bool:
    """The extraction exactly as the frozen match_evidence sends it (model_dump(mode='json'))."""
    try:
        dumped = extraction.model_dump(mode='json')
        units = extraction.units
    except Exception:
        return False
    return (_within(dumped, env.extraction_document_max_bytes) and len(units) <= env.max_units
            and all(_short(u.unit_id, env) for u in units))
