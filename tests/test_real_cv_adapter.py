"""CP3 consent compatibility adapter (D-097 adapter 2) and the server-side consent lease. Offline.

The seven D-097 tests, plus the provider-payload semantics of the frozen parser under the
compatibility flag, the opaque cv_id, the captured analysis date and the consented query embedding.
"""
import inspect
import json
import subprocess
import sys
from datetime import date, datetime, timezone

import pytest

from jobfit.config import REPO_ROOT
from jobfit.cv.parser import ParsedCV
from jobfit.llm.runtime import build_runtime_client
from jobfit.privacy import real_cv
from jobfit.privacy.masking import mask_local
from jobfit.session.store import SessionDenied, SessionStore
from tests.test_live_unit import CONFIG, FakeSDK, response, settings

CV_TEXT = ('Experience\nData Analyst, PT Contoh, 2025 - sekarang\nPython and SQL reporting for sales.\n'
           'Skills\nPython, SQL')
WIRE = {'language': 'en',
        'sections': [{'section': 'Experience', 'text': 'Data Analyst, PT Contoh, 2025 - sekarang\n'
                                                       'Python and SQL reporting for sales.'},
                     {'section': 'Skills', 'text': 'Python, SQL'}],
        'employment': [], 'skills_list': ['Python', 'SQL'],
        'evidence': [{'fact_id': 'f1', 'section': 'Experience', 'quote': 'Python and SQL reporting for sales.'}],
        'location_quote': None}
DAY = date(2026, 10, 9)


def consented(store, text=CV_TEXT):
    h = store.create()
    preview = mask_local(text)
    store.set_preview(h, preview)
    store.consent(h, exact_digest=preview.digest, affirmative=True)
    return h, preview, store.consented_lease(h)


def client(tmp_path, sdk):
    return build_runtime_client(settings(tmp_path), CONFIG, run_id='rcv', sdk_client=sdk)


def parse(store, h, lease, c):
    return real_cv.parse_consented_cv(store, h, lease, client=c, model='deepseek-flash', analysis_date=DAY,
                                      cv_id=real_cv.new_cv_id())


# --- the server-side lease --------------------------------------------------------------------------------

def test_the_lease_exists_only_for_consent_on_the_current_preview():
    store = SessionStore()
    h = store.create()
    with pytest.raises(SessionDenied):
        store.consented_lease(h)                                  # no preview
    preview = mask_local(CV_TEXT)
    store.set_preview(h, preview)
    with pytest.raises(SessionDenied):
        store.consented_lease(h)                                  # no consent
    store.consent(h, exact_digest=preview.digest, affirmative=True)
    lease = store.consented_lease(h)
    assert (lease.session_id, lease.text_digest) == (h.session_id, preview.digest)
    store.set_preview(h, mask_local(CV_TEXT + '\nTableau'))       # an edit clears consent
    with pytest.raises(SessionDenied):
        store.consented_lease(h)


# --- the seven D-097 adapter tests ------------------------------------------------------------------------

def test_1_no_lease_means_no_provider_call(tmp_path):
    store, sdk = SessionStore(), FakeSDK()
    h = store.create()
    store.set_preview(h, mask_local(CV_TEXT))
    from jobfit.session.store import Lease
    forged = Lease(h.session_id, 1, mask_local(CV_TEXT).digest)   # never consented
    with pytest.raises(SessionDenied):
        parse(store, h, forged, client(tmp_path, sdk))
    assert sdk.calls == []


def test_2_a_changed_preview_means_no_provider_call(tmp_path):
    store, sdk = SessionStore(), FakeSDK()
    h, _, lease = consented(store)
    store.set_preview(h, mask_local(CV_TEXT + '\nDocker'))
    with pytest.raises(SessionDenied):
        parse(store, h, lease, client(tmp_path, sdk))
    assert sdk.calls == []


def test_3_there_is_no_raw_text_entry_point():
    for fn in (real_cv.parse_consented_cv, real_cv.embed_consented_cv):
        params = set(inspect.signature(fn).parameters)
        assert not params & {'text', 'raw_text', 'cv_text', 'document'}, fn.__name__
    assert set(inspect.signature(real_cv.parse_consented_cv).parameters) == {
        'store', 'handle', 'lease', 'client', 'model', 'analysis_date', 'cv_id'}


def test_4_the_provider_payload_is_exactly_the_consented_text_with_no_marker_or_session_id(tmp_path):
    store = SessionStore()
    sdk = FakeSDK(lambda kw: response(kw['model'], json.dumps(WIRE)))
    h, preview, lease = consented(store)
    parsed = parse(store, h, lease, client(tmp_path, sdk))
    assert parsed.profile.parse_status.value == 'ok'
    (kw,) = sdk.calls
    system, user = kw['messages']
    # the frozen prompt, unchanged, and the payload {'cv_text': <exact consented text>} only
    assert system['content'] == (REPO_ROOT / 'prompts/cv_parsing_v1.md').read_text()
    assert json.loads(user['content']) == {'untrusted_document_data': {'cv_text': preview.text}}
    sent = json.dumps(kw, default=str)
    assert h.session_id not in sent and h.credential not in sent
    assert 'synthetic' not in sent.lower()                  # the compatibility flag adds no marker


def test_5_the_returned_profile_is_real_not_synthetic(tmp_path):
    store = SessionStore()
    sdk = FakeSDK(lambda kw: response(kw['model'], json.dumps(WIRE)))
    h, preview, lease = consented(store)
    parsed = parse(store, h, lease, client(tmp_path, sdk))
    assert isinstance(parsed, ParsedCV) and parsed.profile.is_synthetic is False
    assert parsed.profile.raw_text == preview.text and parsed.analysis_date == DAY
    assert real_cv.CV_ID_RE.fullmatch(parsed.profile.cv_id) and parsed.profile.cv_id != h.session_id


@pytest.mark.parametrize('how', ['delete', 'expire', 'edit'])
def test_6_a_late_result_after_delete_expiry_or_edit_is_not_returned_or_stored(tmp_path, how):
    clock = [1000.0]
    store = SessionStore(clock=lambda: clock[0])
    h, _, lease = consented(store)

    def respond(kw):
        if how == 'delete':
            store.delete(h)
        elif how == 'expire':
            clock[0] += 10_000
        else:
            store.set_preview(h, mask_local(CV_TEXT + '\nKubernetes'))
        return response(kw['model'], json.dumps(WIRE))
    sdk = FakeSDK(respond)
    with pytest.raises(SessionDenied):
        parse(store, h, lease, client(tmp_path, sdk))
    assert len(sdk.calls) == 1                         # in flight, not recallable, but never stored
    with pytest.raises(SessionDenied):
        store.put(h, lease, 'parsed_cv', 'x')


def test_7_frozen_files_are_unchanged():
    out = subprocess.run([sys.executable, 'scripts/prepare_cp23_freeze.py', '--verify',
                          'evals/freeze/cp23_freeze_draft_v2'], cwd=REPO_ROOT, capture_output=True, text=True)
    assert out.returncode == 0 and '"ok": true' in out.stdout


# --- opaque cv_id, analysis date and the consented query embedding ----------------------------------------

def test_the_session_id_can_never_be_the_cv_id(tmp_path):
    store, sdk = SessionStore(), FakeSDK()
    h, _, lease = consented(store)
    for bad in (h.session_id, 'CV1', 'upload-XYZ', ''):
        with pytest.raises(ValueError):
            real_cv.parse_consented_cv(store, h, lease, client=client(tmp_path, sdk), model='deepseek-flash',
                                       analysis_date=DAY, cv_id=bad)
    assert sdk.calls == []


def test_the_analysis_date_is_the_jakarta_calendar_day_of_an_injected_clock():
    assert real_cv.jakarta_date(datetime(2026, 10, 8, 16, 59, tzinfo=timezone.utc)) == date(2026, 10, 8)
    assert real_cv.jakarta_date(datetime(2026, 10, 8, 17, 0, tzinfo=timezone.utc)) == date(2026, 10, 9)
    with pytest.raises(ValueError):
        real_cv.jakarta_date(datetime(2026, 10, 8, 17, 0))


class EmbedClient:
    def __init__(self, dims):
        self.dims, self.calls = dims, []

    def embed(self, texts, model, task, dimensions):
        self.calls.append((list(texts), model, task, dimensions))
        return [[0.5] * dimensions for _ in texts]


class Spec:
    model, dimensions, max_input_tokens, profile_id = 'qwen/qwen3-embedding-8b', 8, 10_000, 'p' * 64


class Tok:
    def encode(self, text):
        return text.split()


def parsed_for(store, h, lease, tmp_path):
    sdk = FakeSDK(lambda kw: response(kw['model'], json.dumps(WIRE)))
    return parse(store, h, lease, client(tmp_path, sdk))


def test_the_query_embedding_is_of_the_exact_consented_text(tmp_path):
    store, emb = SessionStore(), EmbedClient(8)
    h, preview, lease = consented(store)
    parsed = parsed_for(store, h, lease, tmp_path)
    query, doc = real_cv.embed_consented_cv(store, h, lease, parsed, client=emb, spec=Spec, tokenizer=Tok())
    assert emb.calls == [([preview.text], Spec.model, real_cv.QUERY_EMBEDDING_TASK, 8)]
    assert query.profile_id == Spec.profile_id and len(query.vector) == 8 and doc.text == preview.text


def test_no_query_embedding_for_a_changed_preview_or_a_foreign_parse(tmp_path):
    store, emb = SessionStore(), EmbedClient(8)
    h, _, lease = consented(store)
    parsed = parsed_for(store, h, lease, tmp_path)
    other = parsed.model_copy(update={'profile': parsed.profile.model_copy(update={'raw_text': 'other text'})})
    with pytest.raises(ValueError):
        real_cv.embed_consented_cv(store, h, lease, other, client=emb, spec=Spec, tokenizer=Tok())
    store.set_preview(h, mask_local(CV_TEXT + '\nAirflow'))
    with pytest.raises(SessionDenied):
        real_cv.embed_consented_cv(store, h, lease, parsed, client=emb, spec=Spec, tokenizer=Tok())
    assert emb.calls == []
