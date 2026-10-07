"""Exact-consent CV boundary for explicitly synthetic development processing.

Real-CV enablement, public routes and provider ZDR checks remain CP3 gates.
Helpers own no global cache and accept no alternate raw-text argument.
"""
from jobfit.cv.parser import parse_cv
from jobfit.cv.text_extract import TextResult
from jobfit.matching.evidence_matcher import match_evidence


def _synthetic_only(is_synthetic):
    if is_synthetic is not True:
        raise ValueError('Real-CV provider processing remains disabled')


def parse_session_cv(store, handle, lease, *, client, model, analysis_date, is_synthetic):
    _synthetic_only(is_synthetic)
    return store.dispatch(handle, lease, lambda text: parse_cv(TextResult(text=text),
        client=client, model=model, cv_id=handle.session_id, analysis_date=analysis_date, is_synthetic=True))


def embed_session_cv(store, handle, lease, *, client, model, is_synthetic):
    _synthetic_only(is_synthetic)
    return store.dispatch(handle, lease, lambda text: client.embed([text], model=model, task='session_cv_embedding'))


def match_session_cv(store, handle, lease, *, cv, extraction, client, model, duration_years=None):
    _synthetic_only(cv.profile.is_synthetic)
    def send(text):
        if cv.profile.raw_text != text:
            raise ValueError('Parsed CV differs from exact consented source')
        return match_evidence(cv, extraction, client=client, model=model, duration_years=duration_years, cache=None)
    return store.dispatch(handle, lease, send)
