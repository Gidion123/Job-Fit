"""Real-CV public-beta operations: reserved parse and reserved search (CP3, D-097, D-103).

Each provider call runs inside its D-103 reservation through ``LiveRuntime.run`` with the
operation's reserved client (the public-beta ZDR client in production), and only through the
consent adapter (``jobfit.privacy.real_cv``), so only the exact consented masked text is sent.
Every refusal that can be decided before a reservation (no consent, input above the D-103 CV
envelope, no parsed CV, production retrieval or tokenizer unavailable) is decided before it.

Session state (all session-only, cleared by an edit, delete or expiry): the ParsedCV, which carries
the analysis date captured once when its parse started, and the retrieval-stage results.
"""
from __future__ import annotations

from datetime import datetime

from jobfit.live.beta_envelope import cv_fits
from jobfit.privacy.real_cv import embed_consented_cv, jakarta_date, new_cv_id, parse_consented_cv
from jobfit.session.store import SessionDenied

PARSED_KEY = 'parsed_cv'
SEARCH_KEY = 'search_results'


class RealCVRefused(Exception):
    """A refusal before any reservation; ``code`` is safe to show."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _consented_text(store, handle, lease) -> str:
    text, digest = store.preview(handle)
    if not text or digest != lease.text_digest:
        raise SessionDenied('Preview changed or consent unavailable')
    return text


def reserved_parse(runtime, store, handle, lease, *, operation_key: str, model: str, envelopes,
                   now: datetime | None = None, quota=None, on_first_intent=None):
    """Parse the consented CV in a D-103 ``parse`` reservation; store and return the ParsedCV."""
    store.consented_lease(handle)                        # consent must still cover the current preview
    cv_id, analysis_date = new_cv_id(), jakarta_date(now)       # captured once for this CV generation
    if not cv_fits(envelopes, _consented_text(store, handle, lease), cv_id):
        raise RealCVRefused('input_too_large')

    def work(client):
        return parse_consented_cv(store, handle, lease, client=client, model=model, analysis_date=analysis_date,
                                  cv_id=cv_id)
    parsed, _ = runtime.run('parse', operation_key, work, quota=quota, on_first_intent=on_first_intent)
    store.put(handle, lease, PARSED_KEY, parsed)        # refused (and discarded) if the preview changed
    return parsed


def consented_parsed_cv(store, handle, lease):
    """The successful ParsedCV of the current consented preview; RealCVRefused('parse_required') otherwise."""
    try:
        parsed = store.read(handle, lease, PARSED_KEY)
    except KeyError:
        raise RealCVRefused('parse_required') from None
    if getattr(parsed.profile.parse_status, 'value', parsed.profile.parse_status) != 'ok':
        raise RealCVRefused('parse_required')
    return parsed


def reserved_search(runtime, store, handle, lease, *, operation_key: str, spec, connect, filters, depth: int,
                    envelopes, tokenizer_loader=None, quota=None, on_first_intent=None) -> list[dict]:
    """Query embedding in a D-103 ``search`` reservation, then production retrieval (no provider call).

    Production readiness (seed, index, tokenizer) is checked before the reservation, so an
    unavailable production corpus never costs an embedding.
    """
    from jobfit.search import keyword, production
    parsed = consented_parsed_cv(store, handle, lease)
    if not cv_fits(envelopes, parsed.profile.raw_text, parsed.profile.cv_id):
        raise RealCVRefused('input_too_large')
    tokenizer = (tokenizer_loader or production.load_query_tokenizer)(spec)
    with connect() as conn:
        production.check_index(conn, spec, {r['job_id'] for r in production.eligible_jobs(conn)})

    def work(client):
        return embed_consented_cv(store, handle, lease, parsed, client=client, spec=spec, tokenizer=tokenizer)
    (query, _doc), _ = runtime.run('search', operation_key, work, quota=quota, on_first_intent=on_first_intent)
    with connect() as conn:
        results = production.production_search(conn, keyword.cv_skills(parsed.profile.raw_text), query, spec,
                                                filters, analysis_date=parsed.analysis_date, depth=depth)
    store.put(handle, lease, SEARCH_KEY, results)
    return results
