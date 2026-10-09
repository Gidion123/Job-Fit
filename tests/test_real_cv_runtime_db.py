"""Reserved real-CV parse and search on real PostgreSQL with a fake SDK. Opt-in; no API calls.

The parse and the query embedding run inside their D-103 reservations with the ZDR client and
leave evidence with their real phase; refusals that can be decided before a reservation reserve
nothing and call nothing; production retrieval returns only eligible production jobs.
"""
import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import lru_cache
from types import SimpleNamespace

import psycopg
import pytest

from jobfit.config import Settings
from jobfit.live import quota as quota_mod
from jobfit.live.operation import LiveRuntime
from jobfit.live.quota import BetaAllowances
from jobfit.live.runtime_client import build_public_beta_client
from jobfit.llm.public_beta_bounds import compute_public_beta_bounds
from jobfit.privacy.masking import mask_local
from jobfit.recommend import real_cv_flow as flow
from jobfit.search import production
from jobfit.search.embeddings import EmbeddingSpec
from jobfit.session.store import SessionDenied, SessionStore
from tests.test_live_db import HMAC, conn_for
from tests.test_live_runtime_db import (ADMIN, CONFIG, Conn, alembic_config, baseline, command, gate_free,
                                        intents_in, key, provision)
from tests.test_live_unit import FakeSDK, response
from tests.test_production_retrieval_db import JOBS, insert as insert_jobs

pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
SKILLS = 'Python, SQL, pandas, Airflow, dbt, Docker, Tableau, PostgreSQL, scikit-learn and FastAPI. ' * 12
CV_TEXT = ('Experience\nData Analyst, PT Contoh, 2025 - sekarang\nPython and SQL reporting for sales.\n'
           'Skills\n' + SKILLS.strip())
WIRE = {'language': 'en',
        'sections': [{'section': 'Experience', 'text': 'Data Analyst, PT Contoh, 2025 - sekarang\n'
                                                       'Python and SQL reporting for sales.'},
                     {'section': 'Skills', 'text': SKILLS.strip()}],
        'employment': [], 'skills_list': ['Python', 'SQL'],
        'evidence': [{'fact_id': 'f1', 'section': 'Experience', 'quote': 'Python and SQL reporting for sales.'}],
        'location_quote': None}
SPEC = EmbeddingSpec('qwen3-embedding-8b', 4, 'fixture-v1', 100_000, 'fixture', '1')
NOW = datetime(2026, 10, 8, 18, 30, tzinfo=timezone.utc)            # 9 Oct in Jakarta


@lru_cache(maxsize=1)
def beta():
    return compute_public_beta_bounds()


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


def runtime(db, root, sdk):
    provision(root)
    s = SimpleNamespace(usage_ledger=root / 'ledger.jsonl', database_url=db, daily_budget_usd=5.0,
                        api_hard_stop_usd=25.0)
    client_settings = Settings(openrouter_api_key='k' * 40, usage_ledger=root / 'ledger.jsonl',
                               api_budget_usd=25.0, api_hard_stop_usd=25.0)
    rt = LiveRuntime(s, beta(), pipeline_config=CONFIG, connect=lambda: Conn(db, {}),
                     client_factory=lambda op: build_public_beta_client(client_settings, CONFIG, run_id=op,
                                                                        sdk_client=sdk),
                     watchdog_interval=0.05, drain_grace=1.0)
    rt.sdk = sdk
    return rt


def fake_sdk():
    return FakeSDK(lambda kw: response(kw['model'], json.dumps(WIRE)))


def consented(store, text=CV_TEXT):
    h = store.create()
    preview = mask_local(text)
    store.set_preview(h, preview)
    store.consent(h, exact_digest=preview.digest, affirmative=True)
    return h, store.consented_lease(h)


def rows(db):
    with psycopg.connect(db) as conn:
        return conn.execute('SELECT operation_key, phase, status, reserved_usd FROM budget_reservations '
                            'ORDER BY created_at').fetchall()


def parse(rt, store, h, lease, op=None, **kw):
    return flow.reserved_parse(rt, store, h, lease, operation_key=op or key(), model='deepseek-flash',
                               envelopes=beta().envelopes, now=NOW, **kw)


def search(rt, store, h, lease, db, op=None, **kw):
    return flow.reserved_search(rt, store, h, lease, operation_key=op or key(), spec=SPEC,
                                connect=lambda: psycopg.connect(db, autocommit=True), filters=None, depth=10,
                                envelopes=beta().envelopes, tokenizer_loader=lambda spec: Tok(), **kw)


class Tok:
    def encode(self, text):
        return text.split()


def seed(db):
    with psycopg.connect(db, autocommit=True) as conn:
        insert_jobs(conn, [(*r[:7], [0.5, 0.5, 0.5, 0.5]) for r in JOBS], spec=SPEC)



# --- reserved parse ----------------------------------------------------------------------------------------

def test_the_parse_runs_in_its_reservation_with_zdr_and_the_captured_date(db, tmp_path):
    rt, store = runtime(db, tmp_path / 'root', fake_sdk()), SessionStore()
    h, lease = consented(store)
    op = key()
    parsed = parse(rt, store, h, lease, op=op)
    assert parsed.profile.is_synthetic is False and parsed.analysis_date == date(2026, 10, 9)
    assert store.read(h, lease, flow.PARSED_KEY).profile.cv_id == parsed.profile.cv_id
    (call,) = rt.sdk.calls
    assert call['extra_body']['provider']['zdr'] is True
    assert rows(db) == [(op, 'parse', 'settled', beta().parse_max.quantize(Decimal('1E-10')))]
    assert [(i['phase'], i['chain']) for i in intents_in(tmp_path / 'root', op)] == [('parse', 'parse')]
    assert gate_free(db)


def test_no_consent_or_an_oversized_cv_reserves_and_calls_nothing(db, tmp_path):
    rt, store = runtime(db, tmp_path / 'root', fake_sdk()), SessionStore()
    h = store.create()
    store.set_preview(h, mask_local(CV_TEXT))
    with pytest.raises(SessionDenied):
        store.consented_lease(h)
    big, lease = consented(store, CV_TEXT + '\n' + 'x' * beta().envelopes.cv_document_max_bytes)
    with pytest.raises(flow.RealCVRefused) as exc:
        parse(rt, store, big, lease)
    assert exc.value.code == 'input_too_large'
    assert rt.sdk.calls == [] and rows(db) == []


def test_an_edit_during_the_parse_discards_the_result(db, tmp_path):
    store = SessionStore()
    h, lease = consented(store)

    def respond(kw):
        store.set_preview(h, mask_local(CV_TEXT + '\nKubernetes'))
        return response(kw['model'], json.dumps(WIRE))
    rt = runtime(db, tmp_path / 'root', FakeSDK(respond))
    with pytest.raises(SessionDenied):
        parse(rt, store, h, lease)
    assert len(rt.sdk.calls) == 1 and rows(db)[0][2] == 'settled'     # billed and settled, never stored


# --- reserved search -----------------------------------------------------------------------------------

def test_the_search_embedding_runs_in_its_reservation_and_returns_only_production_jobs(db, tmp_path):
    seed(db)
    rt, store = runtime(db, tmp_path / 'root', fake_sdk()), SessionStore()
    h, lease = consented(store)
    parse(rt, store, h, lease)
    op = key()
    results = search(rt, store, h, lease, db, op=op)
    assert {r['job_id'] for r in results} == {'P1', 'P2', 'P3'}
    assert store.read(h, lease, flow.SEARCH_KEY) == results
    assert store.read(h, lease, flow.search_result_key(op)) == results      # the operation's own result
    embed_calls = [c for c in rt.sdk.calls if 'input' in c]
    assert len(embed_calls) == 1 and embed_calls[0]['extra_body']['provider']['zdr'] is True
    assert embed_calls[0]['input'] == [mask_local(CV_TEXT).text]
    assert rows(db)[-1] == (op, 'recommendation', 'settled', beta().search_max.quantize(Decimal('1E-10')))
    assert [(i['phase'], i['chain']) for i in intents_in(tmp_path / 'root', op)] == [('search', 'embed')]


def test_search_needs_a_parsed_cv_and_a_ready_production_corpus_before_any_reservation(db, tmp_path):
    rt, store = runtime(db, tmp_path / 'root', fake_sdk()), SessionStore()
    h, lease = consented(store)
    with pytest.raises(flow.RealCVRefused) as exc:
        search(rt, store, h, lease, db)
    assert exc.value.code == 'parse_required'
    parse(rt, store, h, lease)
    calls, reserved = len(rt.sdk.calls), len(rows(db))
    with pytest.raises(production.ProductionRetrievalUnavailable):           # no production seed yet
        search(rt, store, h, lease, db)
    with pytest.raises(production.ProductionRetrievalUnavailable):           # no tokenizer artifact
        flow.reserved_search(rt, store, h, lease, operation_key=key(), spec=SPEC,
                             connect=lambda: psycopg.connect(db, autocommit=True), filters=None, depth=10,
                             envelopes=beta().envelopes)
    assert len(rt.sdk.calls) == calls and len(rows(db)) == reserved


def test_an_edit_after_the_parse_refuses_the_search_with_no_call(db, tmp_path):
    seed(db)
    rt, store = runtime(db, tmp_path / 'root', fake_sdk()), SessionStore()
    h, lease = consented(store)
    parse(rt, store, h, lease)
    store.set_preview(h, mask_local(CV_TEXT + '\nAirbyte'))
    calls = len(rt.sdk.calls)
    with pytest.raises(SessionDenied):
        search(rt, store, h, lease, db)
    assert len(rt.sdk.calls) == calls


# --- the durable ticket opens the session allowance at the real parse ----------------------------------

@pytest.mark.parametrize('outcome', ['consumed', 'refused'])
def test_the_real_parse_consumes_the_ticket_and_only_consumed_opens_the_allowance(db, tmp_path, outcome):
    rt, store, allowances = runtime(db, tmp_path / 'root', fake_sdk()), SessionStore(), BetaAllowances()
    h, lease = consented(store)
    if outcome == 'refused':
        assert quota_mod.consume_ticket(lambda: conn_for(db), HMAC) == 'consumed'
    op = key()
    claim = allowances.claim(h.session_id, 'parse', op, lambda: quota_mod.consume_ticket(lambda: conn_for(db), HMAC))
    if outcome == 'consumed':
        parse(rt, store, h, lease, op=op, quota=claim.quota, on_first_intent=claim.on_first_intent)
        assert allowances.remaining(h.session_id) == {'parse': 0, 'search': 1, 'job_analysis': 3}
        assert len(rt.sdk.calls) == 1
    else:
        from jobfit.live.operation import LiveRefused
        with pytest.raises(LiveRefused, match='quota_refused'):
            parse(rt, store, h, lease, op=op, quota=claim.quota, on_first_intent=claim.on_first_intent)
        assert allowances.remaining(h.session_id) is None and rt.sdk.calls == []
