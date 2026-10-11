"""One-job analysis of the CP3 controlled public beta (D-103 ``job_analysis`` phase).

Not a frozen file: it only composes the frozen steps, unchanged, for exactly one JD. Extraction is
the saved corpus extraction or the frozen ``extract_jd`` (dynamic output, no disk cache); matching,
the Luna fallback, the hold policy and the score are the frozen ``analyze_job``. The one addition is
the D-103 extraction envelope: an extraction above it is never truncated; the job is held before
the Sol matching call (0 Sol and 0 Luna calls) and any extraction cost is settled from evidence by
the runtime as usual.

``job_analysis_refusal`` is the admission check that runs before any reservation, ticket or
allowance use.
"""
from __future__ import annotations

from jobfit.eval.product_order import held_score
from jobfit.live.beta_envelope import EXTRACTION_HOLD, INPUT_TOO_LARGE, cv_fits, extraction_fits, jd_fits
from jobfit.recommend.service import JobResult, analyze_job

HOLD_REASON = ('Held: the job requirements are larger than the public-beta analysis envelope '
               f'({EXTRACTION_HOLD}); nothing was truncated and no matching call was made.')


def job_analysis_refusal(envelopes, cv, job_id: str, *, cached=None, jd_text: str | None = None) -> str | None:
    """None when the inputs fit the D-103 envelopes, else ``input_too_large``. Exactly one JD source:
    ``cached`` (a saved (extraction, reason) pair) or ``jd_text``."""
    if (cached is None) == (jd_text is None):
        raise ValueError('exactly one of cached or jd_text is required')
    if not cv_fits(envelopes, cv.profile.raw_text, cv.profile.cv_id):
        return INPUT_TOO_LARGE
    if jd_text is not None:
        return None if jd_fits(envelopes, jd_text, job_id) else INPUT_TOO_LARGE
    extraction, _ = cached
    if extraction is not None and not extraction_fits(envelopes, extraction):
        return INPUT_TOO_LARGE
    return None


def analyze_one_job(cv, job_id: str, *, envelopes, client, config, cached=None, jd_text: str | None = None,
                    spec=None, extraction_model: str | None = None, scope: str = 'session_jd',
                    constraints=None, telemetry=None) -> JobResult:
    """One JD through the frozen steps; ``client`` is the operation's ReservedClient."""
    from jobfit.observability.metrics import observed
    if (cached is None) == (jd_text is None):
        raise ValueError('exactly one of cached or jd_text is required')
    if cached is not None:
        extraction, reason = cached
    else:
        from jobfit.extraction.jd_extractor import extract_jd
        ext = observed(telemetry, 'extraction', extract_jd, jd_text, job_id=job_id, client=client, model=extraction_model, cache=None, scope=scope,
                         spec=spec, dynamic_output=True)
        extraction, reason = (ext.extraction, None) if ext.status == 'done' else (None, ext.error_code or ext.status)
        if extraction is not None and extraction.jd_quality.value != 'ok':
            extraction, reason = None, 'jd_quality_' + extraction.jd_quality.value
    if extraction is not None and not extraction_fits(envelopes, extraction):
        return JobResult(job_id, 1, held_score(HOLD_REASON), hold_reason=HOLD_REASON, extraction=extraction)
    def measured_match(*args, **kwargs):
        from jobfit.matching.evidence_matcher import match_evidence
        return observed(telemetry, 'matching', match_evidence, *args, **kwargs)

    return analyze_job(cv, job_id, 1, extraction, reason, client=client, fallback_client=None, config=config,
                       constraints=constraints, matcher=measured_match if telemetry is not None else None)
