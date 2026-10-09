"""CP3 consent compatibility adapter around the frozen CP2 parser (D-097 adapter 2).

The frozen ``parse_cv`` uses ``is_synthetic`` only as its real-CV guard (and as the output label):
the flag is not part of the prompt or the provider payload. This adapter has no raw-text interface.
It is entered only through ``SessionStore.dispatch(handle, lease, op)``, so the only CV content any
provider can receive is the exact current consented masked text; a changed preview, missing
consent, expiry or deletion refuses before the call and discards a late result. The returned
profile is relabelled ``is_synthetic=False``.

The real-CV analysis date is captured once (``jakarta_date``) when a parse starts and is carried by
the ParsedCV; every later stage of that CV generation reuses ``parsed.analysis_date``.
The ``cv_id`` is a random opaque id: the session identifier never reaches a provider.
"""
from __future__ import annotations

import re
import secrets
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from jobfit.cv.parser import ParsedCV, parse_cv
from jobfit.cv.text_extract import TextResult

JAKARTA = ZoneInfo('Asia/Jakarta')
CV_ID_RE = re.compile(r'upload-[0-9a-f]{12}')
QUERY_EMBEDDING_TASK = 'cv_query_embedding'


def new_cv_id() -> str:
    return 'upload-' + secrets.token_hex(6)


def jakarta_date(now: datetime | None = None) -> date:
    """The Asia/Jakarta calendar date of ``now`` (an aware datetime; default: the current time)."""
    moment = now if now is not None else datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise ValueError('an aware datetime is required')
    return moment.astimezone(JAKARTA).date()


def _check_cv_id(cv_id: str, session_id: str) -> None:
    if not isinstance(cv_id, str) or not CV_ID_RE.fullmatch(cv_id) or cv_id == session_id:
        raise ValueError('an opaque upload cv_id is required')


def parse_consented_cv(store, handle, lease, *, client, model: str, analysis_date: date, cv_id: str) -> ParsedCV:
    """Frozen parse of the exact consented text; the result is a real (not synthetic) profile."""
    _check_cv_id(cv_id, handle.session_id)
    if not isinstance(analysis_date, date):
        raise ValueError('explicit analysis_date required')

    def op(text: str) -> ParsedCV:
        # is_synthetic=True only passes the frozen guard; consent is enforced by dispatch above.
        parsed = parse_cv(TextResult(text=text), cv_id=cv_id, analysis_date=analysis_date, client=client,
                          model=model, is_synthetic=True)
        return parsed.model_copy(update={'profile': parsed.profile.model_copy(update={'is_synthetic': False})})
    return store.dispatch(handle, lease, op)


def embed_consented_cv(store, handle, lease, parsed: ParsedCV, *, client, spec, tokenizer):
    """Query embedding of the exact consented text (frozen preparation), as (QueryEmbedding, PreparedText).

    ``client`` must be the operation's reserved client, so the call runs inside the D-103 ``search``
    reservation. The parsed CV must come from the same consented text.
    """
    from jobfit.search.dense import QueryEmbedding
    from jobfit.search.embeddings import prepare, validate_vector

    def op(text: str):
        if parsed.profile.raw_text != text or parsed.profile.is_synthetic is not False:
            raise ValueError('parsed CV differs from the exact consented source')
        doc = prepare(parsed.profile.cv_id, text, spec, tokenizer)
        vectors = client.embed([doc.text], model=spec.model, task=QUERY_EMBEDDING_TASK, dimensions=spec.dimensions)
        if len(vectors) != 1:
            raise ValueError('incomplete embedding response')
        validate_vector(vectors[0], spec.dimensions)
        return QueryEmbedding(spec.profile_id, list(vectors[0])), doc
    return store.dispatch(handle, lease, op)
