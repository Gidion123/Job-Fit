"""D-103 public-beta phases on real PostgreSQL with a fake SDK. Opt-in; no API calls, no migration.

The beta runtime admits parse, search and job_analysis with the exact calculated bounds under the
US$5/day and US$25 lifetime settings. 'search' and 'job_analysis' rows carry the coarse reservation
label 'recommendation' of the unchanged 0002 schema; the real phase stays in the evidence, the
operation report and the log. The legacy 10-job recommendation phase is never admitted. The durable
ticket (live_quota) gates the in-memory session allowance.
"""
import logging
import os
from datetime import timedelta
from decimal import Decimal
from functools import lru_cache
from types import SimpleNamespace

import psycopg
import pytest

from jobfit.config import Settings
from jobfit.live import quota
from jobfit.live.common import EvidenceError
from jobfit.live.operation import LiveRefused, LiveRuntime
from jobfit.live.quota import BetaAllowances
from jobfit.llm.client import OpenRouterClient
from jobfit.llm.public_beta_bounds import compute_public_beta_bounds
from jobfit.llm.runtime import build_runtime_client
from tests.test_live_db import HMAC, _CommitFails, conn_for
from tests.test_live_runtime_db import (ADMIN, CONFIG, Conn, alembic_config, baseline, command, gate_free, intents_in,
                                        key, provision)
from tests.test_live_unit import MSGS, SOL, Answer, FakeSDK, response

pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires JOBFIT_MIGRATION_TESTS=1 and a disposable pgvector server')
MATCH_TOKENS = 55_000          # upper cost about US$0.55: room for a reported US$0.50 call


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


@lru_cache(maxsize=1)
def beta():
    return compute_public_beta_bounds()


def beta_runtime(db, root, sdk=None, cap=5.0, hard_stop=25.0, **kw):
    provision(root)
    sdk = sdk if sdk is not None else FakeSDK()
    s = SimpleNamespace(usage_ledger=root / 'ledger.jsonl', database_url=db, daily_budget_usd=cap,
                        api_hard_stop_usd=hard_stop)
    client_settings = Settings(openrouter_api_key='k' * 40, usage_ledger=root / 'ledger.jsonl',
                               api_budget_usd=25.0, api_hard_stop_usd=hard_stop)

    def factory(op):      # the frozen RuntimeClient has no embeddings endpoint; search uses the base client
        if rt.plain:
            return OpenRouterClient(client_settings, sdk_client=sdk, run_id=op)
        return build_runtime_client(client_settings, CONFIG, run_id=op, sdk_client=sdk)
    rt = LiveRuntime(s, beta(), pipeline_config=CONFIG, connect=lambda: Conn(db, {}), client_factory=factory,
                     watchdog_interval=0.05, drain_grace=1.0, **kw)
    rt.sdk, rt.plain = sdk, False
    return rt


def parse_work(client):
    return client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=16000).answer


def search_work(client):
    # long enough that the fake SDK's reported cost (US$0.00001) stays below the call's upper bound
    return client.embed(['masked cv text ' * 100], model='qwen3-embedding-8b', dimensions=4)


def job_work(client):
    return client.chat_structured(SOL, MSGS, Answer, 'evidence_matching', max_tokens=MATCH_TOKENS).answer


def cost_sdk(match_cost):
    return FakeSDK(lambda kw: response(kw['model'], cost=match_cost if kw['model'] == SOL else 0.001))


def reservations(db):
    with psycopg.connect(db) as conn:
        return conn.execute('SELECT operation_key, phase, status, reserved_usd, settled_usd FROM budget_reservations '
                            'ORDER BY created_at').fetchall()


def run_search(rt, op):
    rt.plain = True
    try:
        return rt.run('search', op, search_work)
    finally:
        rt.plain = False


# --- the compatibility label: open, settle and reconcile without migration ---------------------------

def test_search_and_job_analysis_settle_under_the_coarse_label_with_their_exact_bounds(db, tmp_path, caplog):
    rt = beta_runtime(db, tmp_path / 'root')
    p, s, j = key(), key(), key()
    with caplog.at_level(logging.INFO, logger='jobfit.live'):
        rt.run('parse', p, parse_work)
        _, s_report = run_search(rt, s)
        result, j_report = rt.run('job_analysis', j, job_work)
    assert result == 'ok' and (s_report.phase, j_report.phase) == ('search', 'job_analysis')
    assert s_report.outcome == j_report.outcome == 'settled'
    b = beta()
    q = Decimal('1E-10')
    assert reservations(db) == [
        (p, 'parse', 'settled', b.parse_max.quantize(q), Decimal('0.0010000000')),
        (s, 'recommendation', 'settled', b.search_max.quantize(q), Decimal('0.0000100000')),
        (j, 'recommendation', 'settled', b.job_analysis_max.quantize(q), Decimal('0.0010000000'))]
    # the real phase stays in the non-DB evidence and in the log
    root = tmp_path / 'root'
    assert [(i['phase'], i['chain']) for i in intents_in(root, s)] == [('search', 'embed')]
    assert [(i['phase'], i['chain']) for i in intents_in(root, j)] == [('job_analysis', 'matching')]
    logged = [r.getMessage() for r in caplog.records if 'admitted' in r.getMessage()]
    assert any(f'{j} admitted: phase=job_analysis reservation_label=recommendation' in m for m in logged)
    assert any(f'{s} admitted: phase=search reservation_label=recommendation' in m for m in logged)
    assert gate_free(db)


def test_an_interrupted_job_analysis_is_reconciled_from_evidence_under_the_coarse_label(db, tmp_path, monkeypatch):
    root = tmp_path / 'root'
    rt, op = beta_runtime(db, root), key()

    def lost(*a, **kw):
        raise EvidenceError('settlement interrupted')
    monkeypatch.setattr(rt, 'settle', lost)
    result, report = rt.run('job_analysis', op, job_work)
    assert report.outcome == 'deferred' and reservations(db)[0][1:3] == ('recommendation', 'reserved')
    with pytest.raises(LiveRefused, match='busy'):                # the open row blocks every phase
        beta_runtime(db, root).run('parse', key(), parse_work)
    fresh = beta_runtime(db, root)                                # a new process over the same storage
    with psycopg.connect(db) as conn:
        until = conn.execute('SELECT active_until FROM budget_reservations WHERE operation_key = %s',
                             (op,)).fetchone()[0]
    reports = fresh.reconcile(at=until + timedelta(seconds=1))
    assert [(r.operation_key, r.outcome) for r in reports] == [(op, 'settled')]
    assert reservations(db)[0][1:] == ('recommendation', 'settled', beta().job_analysis_max.quantize(Decimal('1E-10')),
                                       Decimal('0.0010000000'))
    assert [i['phase'] for i in intents_in(root, op)] == ['job_analysis'] and fresh.sdk.calls == []


# --- admission with the exact beta bounds under US$5/day and US$25 ------------------------------------

def test_admission_uses_the_beta_bounds_and_the_actual_settled_spend(db, tmp_path):
    rt = beta_runtime(db, tmp_path / 'root', sdk=cost_sdk(0.5))
    rt.run('parse', key(), parse_work)
    run_search(rt, key())
    for _ in range(2):                                            # 0.002 + 0.5k + 4.0012836 <= 5 for k <= 1
        assert rt.run('job_analysis', key(), job_work)[0] == 'ok'
    with pytest.raises(LiveRefused) as exc:                       # 1.002 + 4.0012836 > 5
        rt.run('job_analysis', key(), job_work)
    assert exc.value.code == 'budget' and exc.value.status == 429
    assert rt.run('parse', key(), parse_work)[0] == 'ok'          # a small bound still fits the day
    assert run_search(rt, key())[0] is not None
    assert [r[2] for r in reservations(db)] == ['settled'] * 6


def test_the_lifetime_stop_counts_recorded_spend_plus_the_beta_bound(db, tmp_path):
    rt = beta_runtime(db, tmp_path / 'root', sdk=cost_sdk(0.5), cap=10.0, hard_stop=4.5)
    assert rt.run('job_analysis', key(), job_work)[0] == 'ok'     # 0 + 4.0012836 <= 4.5
    with pytest.raises(LiveRefused, match='lifetime'):            # 0.5 + 4.0012836 > 4.5
        rt.run('job_analysis', key(), job_work)
    assert rt.run('parse', key(), parse_work)[0] == 'ok'


def test_the_legacy_recommendation_phase_is_never_admitted_by_the_beta_runtime(db, tmp_path):
    rt = beta_runtime(db, tmp_path / 'root')
    rt.run('job_analysis', key(), job_work)                       # a settled 'recommendation'-labelled row exists
    with pytest.raises(LiveRefused) as exc:
        rt.run('recommendation', key(), lambda client: pytest.fail('no pipeline may run'))
    assert exc.value.code == 'phase_not_admitted' and exc.value.status == 403
    assert len(rt.sdk.calls) == 1 and len(reservations(db)) == 1 and gate_free(db)
    # and the legacy bound itself never fits the beta day: the historical eligibility keeps its meaning
    from jobfit.llm.phase_bounds import compute_phase_bounds
    assert compute_phase_bounds().recommendation_upper_bound > Decimal(5)


# --- the durable ticket gates the session allowance (real live_quota) ---------------------------------

def consume(db, conn_factory=None):
    return lambda: quota.consume_ticket(conn_factory or (lambda: conn_for(db)), HMAC)


def test_a_proven_ticket_opens_the_allowance_and_a_restart_needs_one_of_the_ips_remaining_tickets(db, tmp_path):
    rt, allowances = beta_runtime(db, tmp_path / 'root'), BetaAllowances()
    op = key()
    c = allowances.claim('s', 'parse', op, consume(db))
    rt.run('parse', op, parse_work, quota=c.quota, on_first_intent=c.on_first_intent)
    assert allowances.remaining('s') == {'parse': 0, 'search': 1, 'job_analysis': 10}
    for _ in range(10):
        op = key()
        c = allowances.claim('s', 'job_analysis', op, consume(db))
        assert c.quota is None
        rt.run('job_analysis', op, job_work, quota=c.quota, on_first_intent=c.on_first_intent)
    assert allowances.claim('s', 'job_analysis', key(), consume(db)) == 'allowance_exhausted'
    calls = len(rt.sdk.calls)
    for _ in range(quota.TICKETS_PER_IP_PER_DAY - 1):             # other sessions use the IP's other tickets
        assert consume(db)() == 'consumed'
    restarted = BetaAllowances()                                  # process restart: the session is gone
    op = key()
    c = restarted.claim('s', 'job_analysis', op, consume(db))
    with pytest.raises(LiveRefused, match='quota_refused'):
        rt.run('job_analysis', op, job_work, quota=c.quota, on_first_intent=c.on_first_intent)
    assert restarted.remaining('s') is None and len(rt.sdk.calls) == calls


@pytest.mark.parametrize('outcome', ['refused', 'unavailable', 'unknown'])
def test_an_unproven_ticket_creates_no_allowance_and_no_provider_call(db, tmp_path, outcome):
    rt, allowances, op = beta_runtime(db, tmp_path / 'root'), BetaAllowances(), key()
    factory = lambda: conn_for(db)                                # noqa: E731
    if outcome == 'refused':
        for _ in range(quota.TICKETS_PER_IP_PER_DAY):                 # the IP already used its 24-hour tickets
            assert quota.consume_ticket(factory, HMAC) == 'consumed'
    elif outcome == 'unavailable':
        def factory():
            raise psycopg.OperationalError('database unreachable')
    else:
        factory = lambda: _CommitFails(conn_for(db), only_after='INSERT INTO live_quota')   # noqa: E731
    c = allowances.claim('s', 'job_analysis', op, consume(db, factory))
    with pytest.raises(LiveRefused) as exc:
        rt.run('job_analysis', op, job_work, quota=c.quota, on_first_intent=c.on_first_intent)
    assert exc.value.code == {'refused': 'quota_refused', 'unavailable': 'quota_unavailable',
                              'unknown': 'quota_outcome_unknown'}[outcome]
    assert rt.sdk.calls == [] and allowances.remaining('s') is None
    assert reservations(db)[0][2] == 'released'
