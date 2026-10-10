"""Offline observability contract. Synthetic inputs and fake SDK only."""
import hashlib
import json
import logging
from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from jobfit.api.main import AppDeps, create_app
from jobfit.live.quota import Ingress
from jobfit.observability.metrics import Telemetry, observed
from jobfit.observability.http import SafeJSONFormatter, configure_logging
from jobfit.observability.cost import CostCollector, CostSnapshot
from jobfit.session.store import SessionStore
from jobfit.llm.ledger import UsageRecord

CANARY = 'PRIVATE_CANARY@example.com-198.51.100.77-owner-token'


@contextmanager
def capture_jobfit_records():
    """Capture the private JobFit logger after production logging is configured."""
    configure_logging()
    records = []

    class Recorder(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = Recorder(level=logging.INFO)
    logger = logging.getLogger('jobfit')
    logger.addHandler(handler)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


def app(ingress=True):
    t = Telemetry()
    d = AppDeps(SessionStore(), {}, lambda: None, sweep_seconds=None, telemetry=t,
                ingress=Ingress('internal-secret', None, None) if ingress else None)
    return TestClient(create_app(d)), t


def sample(t, name, labels=None):
    return t.registry.get_sample_value(name, labels or {})


def test_metrics_keeps_internal_auth_and_dark_state():
    c, t = app()
    assert c.get('/metrics').status_code == 401
    assert c.get('/metrics', headers={'X-JobFit-Internal-Token': CANARY}).status_code == 401
    r = c.get('/metrics', headers={'X-JobFit-Internal-Token': 'internal-secret'})
    assert r.status_code == 200 and 'jobfit_http_requests_total' in r.text
    assert 'internal-secret' not in r.text and CANARY not in r.text
    assert r.headers['cache-control'] == 'no-store'
    assert c.post('/session').status_code == 401
    health = c.get('/health').json()
    assert health['live_enabled'] is False and health['real_cv_enabled'] is False
    assert sample(t, 'jobfit_llm_attempts_total') is None


def test_no_ingress_is_not_public_metrics_permission():
    c, _ = app(False)
    assert c.get('/metrics').status_code == 401


def test_http_original_status_duration_and_bounded_route():
    c, t = app(False)
    for suffix in (CANARY, 'one', 'two'):
        assert c.get('/missing/' + suffix).status_code == 404
    assert sample(t, 'jobfit_http_requests_total', {'method': 'GET', 'route': 'unmatched', 'status': '404'}) == 3
    assert sample(t, 'jobfit_http_duration_seconds_count', {'method': 'GET', 'route': 'unmatched'}) == 3
    # Existing dynamic endpoint: validation fails, but label is its route template.
    c.get('/recommendations/' + CANARY)
    assert CANARY not in t.render().decode()
    assert sample(t, 'jobfit_http_requests_total',
                  {'method': 'GET', 'route': '/recommendations/{run_id}', 'status': '422'}) == 1


def test_http_telemetry_failure_does_not_change_response(monkeypatch):
    c, t = app(False)
    monkeypatch.setattr(t, 'request', lambda *a: (_ for _ in ()).throw(ValueError(CANARY)))
    assert c.get('/health').status_code == 200
    monkeypatch.setattr(t, 'render', lambda: (_ for _ in ()).throw(ValueError(CANARY)))
    # Authentication is still checked before collection.
    assert c.get('/metrics').status_code == 401


def test_authorized_broken_exposition_is_safe_503(monkeypatch):
    c, t = app()
    monkeypatch.setattr(t, 'render', lambda: (_ for _ in ()).throw(ValueError(CANARY)))
    r = c.get('/metrics', headers={'X-JobFit-Internal-Token': 'internal-secret'})
    assert r.status_code == 503 and CANARY not in r.text


@pytest.mark.parametrize('status,expected', [('done', 'success'), ('failed', 'failure'), ('needs_review', 'failure')])
def test_actual_stage_result_and_duration(status, expected):
    t = Telemetry()
    obj = SimpleNamespace(status=status)
    assert observed(t, 'matching', lambda: obj) is obj
    assert sample(t, 'jobfit_stage_executions_total', {'stage': 'matching', 'outcome': expected}) == 1
    assert sample(t, 'jobfit_stage_duration_seconds_count', {'stage': 'matching', 'outcome': expected}) == 1


def test_hold_refusal_and_observer_failure_preserve_behavior(monkeypatch):
    from jobfit.live.operation import LiveRefused
    t = Telemetry()
    obj = SimpleNamespace(hold_reason='held')
    def refuse():
        raise LiveRefused('budget')
    with capture_jobfit_records() as records:
        assert observed(t, 'job_analysis', lambda: obj) is obj
        with pytest.raises(LiveRefused):
            observed(t, 'job_analysis', refuse)
    stage_logs = [SafeJSONFormatter().format(r) for r in records if r.name == 'jobfit.stage']
    assert any(json.loads(row).get('error_code') == 'budget' for row in stage_logs)
    assert CANARY not in '\n'.join(stage_logs)
    assert sample(t, 'jobfit_budget_rejections_total', {'reason': 'budget'}) == 1
    assert sample(t, 'jobfit_stage_executions_total', {'stage': 'job_analysis', 'outcome': 'held'}) == 1
    monkeypatch.setattr(t, 'stage', lambda *a: (_ for _ in ()).throw(ValueError(CANARY)))
    assert observed(t, 'matching', lambda: obj) is obj
    with pytest.raises(LiveRefused):
        observed(t, 'matching', refuse)
    unusual = ValueError(CANARY)
    unusual.code = [CANARY]
    with pytest.raises(ValueError) as caught:
        observed(t, 'matching', lambda: (_ for _ in ()).throw(unusual))
    assert caught.value is unusual


def test_json_formatter_never_formats_raw_messages_or_tracebacks():
    r = logging.LogRecord('jobfit.live', logging.ERROR, '', 0, CANARY + ' %s', (CANARY,),
                          (ValueError, ValueError(CANARY), None))
    r.raw_cv = CANARY
    body = SafeJSONFormatter().format(r)
    assert CANARY not in body
    assert set(json.loads(body)) == {'timestamp', 'level', 'event'}


def test_http_logs_do_not_include_query_body_header_or_path():
    with capture_jobfit_records() as records:
        c, _ = app(False)
        c.post('/not-real/' + CANARY + '?cv=' + CANARY, json={'cv': CANARY},
               headers={'Authorization': CANARY, 'X-Request-Id': CANARY})
    http_records = [r for r in records if r.name == 'jobfit.http']
    assert http_records
    for r in http_records:
        body = SafeJSONFormatter().format(r)
        assert CANARY not in body
        assert json.loads(body)['route'] == 'unmatched'


def test_attempt_usage_repair_fallback_and_unknown_cost_are_distinct():
    t = Telemetry()
    ctx = SimpleNamespace(chain='fallback', attempt_kind='initial', upper_cost=Decimal('.1'))
    r = UsageRecord(run_id=CANARY, task=CANARY, model='openai/gpt-6-luna', input_tokens=12, output_tokens=3,
                    cost_usd=.002, cost_source='reported', latency_ms=250, request_id=CANARY)
    t.attempt(r, ctx)
    ctx.attempt_kind = 'validation_repair'
    t.attempt(r.model_copy(update={'ok': False, 'cost_source': 'uncertain_upper_bound', 'cost_usd': .1}), ctx)
    assert sample(t, 'jobfit_llm_fallbacks_total', {'model': r.model}) == 1
    assert sample(t, 'jobfit_llm_tokens_total', {'model': r.model, 'direction': 'input'}) == 12
    assert sample(t, 'jobfit_llm_accounted_cost_usd_total', {'model': r.model, 'source': 'uncertain_upper_bound'}) == .1
    assert sample(t, 'jobfit_llm_attempts_total', {'model': r.model, 'chain': 'fallback',
                  'kind': 'validation_repair', 'outcome': 'failure'}) == 1
    assert CANARY not in t.render().decode()
    t.attempt(r.model_copy(update={'model': CANARY}), ctx)
    assert CANARY not in t.render().decode()


def test_real_reserved_fake_sdk_records_once_and_preserves_ledger(tmp_path):
    from tests.test_live_unit import Live, parse_call
    t = Telemetry()
    live = Live(tmp_path)
    live.client._inner.ledger.telemetry = t
    answer = parse_call(live)
    assert answer.answer == 'ok'
    assert len(live.sdk.calls) == 1
    text = t.render().decode()
    assert 'jobfit_llm_attempts_total{chain="parse",kind="initial",model="deepseek/deepseek-v4.1-flash",outcome="success"} 1.0' in text
    rows = live.client._inner.ledger.raw_lines()
    assert len(rows) == 1
    assert 'telemetry' not in rows[0]


def test_observer_exception_does_not_break_durable_ledger(tmp_path):
    from tests.test_live_unit import Live, parse_call
    live = Live(tmp_path)
    live.client._inner.ledger.telemetry = SimpleNamespace(attempt=lambda *a: (_ for _ in ()).throw(ValueError(CANARY)))
    assert parse_call(live).answer == 'ok'
    assert len(live.client._inner.ledger.raw_lines()) == 1


class FakeConnection:
    def __init__(self, *, lost=False):
        self.queries, self.lost = [], lost
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def execute(self, sql, args=None):
        from jobfit.live import budget_store as bs
        self.queries.append(sql)
        if 'SELECT ts,' in sql:
            return SimpleNamespace(fetchone=lambda: ('now', 'today', 'start'))
        if sql == bs.FOREIGN_STORAGE_SQL:
            return SimpleNamespace(fetchone=lambda: None)
        value = Decimal(0)
        if sql == bs.SETTLED_TOTAL_SQL:
            value = Decimal('99' if self.lost else '.01')
        elif sql == bs.DAY_LIABILITY_SQL:
            value = Decimal('.05')
        elif sql == bs.OPEN_LIABILITY_SQL:
            value = Decimal('.02')
        return SimpleNamespace(fetchone=lambda: (value,))


def files(tmp_path):
    import uuid
    ledger = tmp_path / 'ledger.jsonl'
    marker = {'format': 1, 'storage_id': uuid.uuid4().hex, 'ledger_name': ledger.name, 'created_at': 'synthetic'}
    (tmp_path / '.jobfit-ledger-storage.json').write_text(json.dumps(marker))
    intent = {'type': 'intent', 'operation_key': 'synthetic', 'attempt_id': 'a', 'phase': 'parse',
              'task': 'parse', 'model': 'synthetic', 'attempt_kind': 'initial', 'chain': 'parse', 'upper_cost': '.03'}
    from jobfit.live.evidence import journal_path
    journal_path(ledger).write_text(json.dumps(intent) + '\n' + json.dumps({**intent, 'attempt_id': 'b'}) + '\n')
    ledger.write_text(json.dumps({'operation_key': 'synthetic', 'attempt_id': 'a', 'cost_usd': .01,
                                 'cost_source': 'reported'}) + '\n')
    return ledger


def hashes(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()}


def test_persisted_cost_snapshot_read_only_uncertain_and_restart(tmp_path):
    ledger = files(tmp_path)
    before = hashes(tmp_path)
    conn = FakeConnection()
    s = CostSnapshot(ledger, lambda: conn, 5, 25, 25)
    a = s()
    assert a['recorded_spend_usd'] == Decimal('.04')
    assert a['reported_cost_usd'] == Decimal('.01')
    assert a['uncertain_cost_usd'] == Decimal('.03')
    assert a['lifetime_remaining_usd'] == Decimal('24.94')
    assert a['daily_remaining_usd'] == Decimal('4.95')
    assert s() == a
    assert hashes(tmp_path) == before
    assert conn.queries[0] == 'BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'
    assert not any(q.startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE')) for q in conn.queries)


@pytest.mark.parametrize('problem', ['torn', 'duplicate', 'missing_cost', 'lost', 'missing_marker', 'racing'])
def test_invalid_accounting_omits_balances_not_zero(tmp_path, problem):
    ledger = files(tmp_path)
    conn = FakeConnection(lost=problem == 'lost')
    if problem == 'torn':
        ledger.write_text('{')
    elif problem == 'duplicate':
        ledger.write_text(ledger.read_text() * 2)
    elif problem == 'missing_cost':
        row = json.loads(ledger.read_text())
        row.pop('cost_usd')
        ledger.write_text(json.dumps(row) + '\n')
    elif problem == 'missing_marker':
        (tmp_path / '.jobfit-ledger-storage.json').write_text('{}')
    def connect():
        if problem == 'racing':
            ledger.write_text(ledger.read_text() + '\n')
        return conn
    t = Telemetry()
    t.registry.register(CostCollector(CostSnapshot(ledger, connect, 5, 25, 25)))
    body = t.render().decode()
    assert 'jobfit_accounting_snapshot_available 0.0' in body
    assert 'jobfit_accounting_lifetime_remaining_usd' not in body


def test_no_snapshot_has_no_manufactured_cost():
    t = Telemetry()
    t.registry.register(CostCollector(None))
    assert sample(t, 'jobfit_accounting_snapshot_available') == 0
    assert sample(t, 'jobfit_accounting_settled_usd') is None


def test_dashboard_merge_preserves_uid_datasource_and_infra():
    from copy import deepcopy
    from scripts.prepare_observability_dashboard import merge_dashboard
    old = {'dashboard': {'uid': 'jobfit-overview', 'title': 'JobFit - Production Monitoring', 'version': 8,
                        'panels': [{'id': i, 'title': name, 'datasource': 'Prometheus',
                                    'gridPos': {'x': 0, 'y': i * 4, 'h': 4, 'w': 24}}
                                   for i, name in enumerate(('CPU', 'RAM', 'Disk', 'Node Exporter'), 1)]}}
    saved = deepcopy(old)
    from pathlib import Path
    panels = json.loads((Path(__file__).resolve().parents[1] / 'deploy/observability/panels.json').read_text())
    new = merge_dashboard(old, panels, 'Prometheus')
    assert old == saved
    assert new['dashboard']['panels'][:4] == old['dashboard']['panels']
    assert new['dashboard']['uid'] == old['dashboard']['uid']
    assert new['dashboard']['version'] == 8
    assert len({p['id'] for p in new['dashboard']['panels']}) == len(new['dashboard']['panels'])
    with pytest.raises(ValueError, match='already present'):
        merge_dashboard(new, panels, 'Prometheus')
    with pytest.raises(ValueError, match='Datasource'):
        merge_dashboard(old, panels, 'other-uid')


def test_dark_snapshot_never_uses_development_ledger():
    from jobfit.observability.cost import production_snapshot
    settings = SimpleNamespace(environment='prod', database_url='postgresql://unused')
    assert production_snapshot(settings, {}) is None
    assert production_snapshot(settings, {'JOBFIT_USAGE_LEDGER': 'reports/usage/usage_ledger.jsonl'}) is None
    env = {'JOBFIT_USAGE_LEDGER': '/var/lib/jobfit/ledger/usage_ledger.jsonl',
           'JOBFIT_DAILY_BUDGET_USD': '5', 'API_HARD_STOP_USD': '25', 'API_BUDGET_USD': '25'}
    # The production path resolves differently on macOS. Both must fail closed or validate correctly.
    s = production_snapshot(settings, env)
    if s is not None:
        assert s.daily == 5 and s.hard_stop == 25
    env['API_HARD_STOP_USD'] = 'NaN'
    assert production_snapshot(settings, env) is None


@pytest.mark.parametrize('job', ['J01', 'J04', 'J08'])
def test_matching_instrumentation_preserves_frozen_answer_and_fallback(tmp_path, job):
    from tests.test_public_beta_runtime import BetaLive, env
    from tests.test_live_recommend_equivalence import answer, extraction
    from tests.test_live_unit import CONFIG, FakeSDK
    from tests.test_cv_upload_pipeline import parsed
    from jobfit.recommend.beta_analysis import analyze_one_job
    from jobfit.recommend.service import RecommendConfig
    t = Telemetry()
    results = []
    live_runs = []
    for name, telemetry in [('old', None), ('new', t)]:
        live = BetaLive(tmp_path / name, 'job_analysis', FakeSDK(answer))
        live.client._inner.ledger.telemetry = telemetry
        r = analyze_one_job(parsed(), job, envelopes=env(), client=live.client,
                            config=RecommendConfig.from_yaml(CONFIG), cached=extraction(job), telemetry=telemetry)
        results.append(r)
        live_runs.append(live)
    assert results[0] == results[1]
    assert len(live_runs[0].sdk.calls) == len(live_runs[1].sdk.calls)
    # Cached extraction does not manufacture a timing sample.
    assert sample(t, 'jobfit_stage_executions_total', {'stage': 'extraction', 'outcome': 'success'}) is None
    if job in ('J04', 'J08'):
        assert sample(t, 'jobfit_llm_fallbacks_total', {'model': 'openai/gpt-6-luna'}) == 1
        assert sample(t, 'jobfit_stage_executions_total', {'stage': 'matching', 'outcome': 'failure'}) >= 1


def test_live_runtime_refusal_is_observed_without_provider_or_db(tmp_path):
    from jobfit.live.operation import LiveRuntime, LiveRefused
    from tests.test_live_unit import CONFIG
    from tests.test_public_beta_runtime import beta
    t = Telemetry()
    rt = LiveRuntime(SimpleNamespace(usage_ledger=tmp_path / 'ledger.jsonl'), beta(), pipeline_config=CONFIG,
                     client_factory=lambda op: pytest.fail('no provider'),
                     connect=lambda: pytest.fail('no DB'), telemetry=t)
    with pytest.raises(LiveRefused, match='phase_not_admitted'):
        rt.run('recommendation', 'synthetic', lambda c: pytest.fail('no work'))
    assert sample(t, 'jobfit_stage_executions_total', {'stage': 'recommendation', 'outcome': 'refused'}) == 1


def test_telemetry_broken_classifier_cannot_change_result(monkeypatch):
    from jobfit.observability import metrics
    value = object()
    monkeypatch.setattr(metrics, 'outcome', lambda r: (_ for _ in ()).throw(ValueError(CANARY)))
    assert observed(Telemetry(), 'matching', lambda: value) is value


def test_async_analysis_counts_real_result_duplicate_and_correlates_safe_logs():
    import uuid
    from jobfit.eval.product_order import held_score
    from jobfit.recommend.service import JobResult
    from jobfit.schemas.analysis import ScoreResult, ScoreStatus
    from tests.test_public_beta_api import make, owner, session, wait, scored, HOLD_REASON

    for expected, analyze in (
        ('completed', lambda cv, **kw: scored('A')),
        ('held', lambda cv, **kw: JobResult('A', 1, held_score(HOLD_REASON), hold_reason=HOLD_REASON)),
        ('unknown', lambda cv, **kw: JobResult('A', 1, ScoreResult(status=ScoreStatus.NO_SCORE))),
        ('failed', lambda cv, **kw: (_ for _ in ()).throw(RuntimeError(CANARY))),
    ):
        t = Telemetry()
        invocations = []
        def counted(cv, **kw):
            invocations.append(1)
            return analyze(cv, **kw)
        with capture_jobfit_records() as captured:
            c, _ = make(analyze=counted, telemetry=t)
            h = session(c)
            key = str(uuid.uuid4())
            response = c.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'},
                              headers={**owner(h, key), 'X-Request-Id': CANARY})
            assert response.status_code == 200
            run_id = response.json()['run_id']
            body = wait(c, h, run_id)
            duplicate = c.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h, key))
        assert body['status'] == ('failed' if expected == 'failed' else 'done')
        assert duplicate.json() == {'run_id': run_id, 'duplicate': True}
        assert sample(t, 'jobfit_analysis_requests_total', {'outcome': 'accepted'}) == 1
        assert sample(t, 'jobfit_analysis_requests_total', {'outcome': 'duplicate'}) == 1
        assert sample(t, 'jobfit_analysis_outcomes_total', {'outcome': expected}) == 1
        assert sample(t, 'jobfit_stage_executions_total',
                      {'stage': 'overall_analysis',
                       'outcome': {'completed': 'success', 'held': 'held', 'unknown': 'unknown', 'failed': 'failure'}[expected]}) == 1
        records = [json.loads(SafeJSONFormatter().format(r)) for r in captured
                   if r.name in {'jobfit.http', 'jobfit.analysis'}]
        admission = [r for r in records if r['event'] == 'http_completed' and
                     r.get('route') == '/jobs/{job_id}/analyze']
        execution = [r for r in records if r['event'] == 'analysis_finished']
        assert len(admission) == 2 and len(execution) == 1
        assert execution[0]['request_id'] == admission[0]['request_id']
        assert execution[0]['request_id'] != admission[1]['request_id']
        assert CANARY not in json.dumps(records)
        assert CANARY not in t.render().decode()
        assert len(invocations) == 1


def test_async_refusal_is_not_completion():
    from jobfit.live.operation import LiveRefused
    from tests.test_public_beta_api import make, owner, session, wait
    t = Telemetry()
    c, _ = make(analyze=lambda cv, **kw: (_ for _ in ()).throw(LiveRefused('budget')), telemetry=t)
    h = session(c)
    run_id = c.post('/jobs/A/analyze', json={'demo_cv_id': 'CV1'}, headers=owner(h)).json()['run_id']
    assert wait(c, h, run_id)['status'] == 'failed'
    assert sample(t, 'jobfit_analysis_outcomes_total', {'outcome': 'refused'}) == 1
    assert sample(t, 'jobfit_analysis_outcomes_total', {'outcome': 'completed'}) is None


def test_database_collector_is_independent_and_read_only():
    from jobfit.observability.cost import DatabaseCollector
    commands = []

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, sql):
            commands.append(sql)
            return self

        def fetchone(self):
            return (1,)

    t = Telemetry()
    t.registry.register(DatabaseCollector(lambda: Conn()))
    assert sample(t, 'jobfit_postgres_available') == 1
    assert commands == ['BEGIN READ ONLY', "SET LOCAL statement_timeout = '1000ms'", 'SELECT 1', 'ROLLBACK']
    down = Telemetry()
    down.registry.register(DatabaseCollector(lambda: (_ for _ in ()).throw(ValueError(CANARY))))
    assert sample(down, 'jobfit_postgres_available') == 0
    assert CANARY not in down.render().decode()


def test_dashboard_file_provisioned_merge_and_health_panels():
    from pathlib import Path
    from scripts.prepare_observability_dashboard import merge_dashboard
    panel_path = Path(__file__).resolve().parents[1] / 'deploy/observability/panels.json'
    panels = json.loads(panel_path.read_text())
    original = {'uid': 'jobfit-overview', 'panels': [
        {'id': i, 'title': name, 'datasource': {'type': 'prometheus', 'uid': 'Prometheus'},
         'gridPos': {'x': 0, 'y': i * 4, 'w': 24, 'h': 4}}
        for i, name in enumerate(('CPU', 'RAM', 'Disk', 'Node Exporter'), 1)]}
    merged = merge_dashboard(original, panels, 'Prometheus')
    assert merged['uid'] == 'jobfit-overview'
    assert merged['panels'][:4] == original['panels']
    assert all(p['datasource'] == {'type': 'prometheus', 'uid': 'Prometheus'}
               for p in merged['panels'][4:])
    assert {'API scrape and restarts', 'PostgreSQL and ledger availability'} <= {
        p['title'] for p in merged['panels']}
    health = next(p for p in merged['panels'] if p['title'] == 'API scrape and restarts')
    assert 'changes(process_start_time_seconds' in health['targets'][1]['expr']
    error = next(p for p in merged['panels'] if p['title'] == 'API server error fraction')
    assert 'or vector(0)' in error['targets'][0]['expr']
    assert '/ sum(rate(jobfit_http_requests_total' in error['targets'][0]['expr']


def test_native_process_collector_registered():
    from prometheus_client import ProcessCollector
    t = Telemetry()
    assert any(isinstance(c, ProcessCollector) for c in t.registry._collector_to_names)



def test_real_cv_async_analysis_uses_job_result_before_presentation(tmp_path):
    from tests.test_real_cv_api import (make, session, upload_and_consent, parse, search,
                                        analyze, wait)
    t = Telemetry()
    c, fake, _ = make(tmp_path, telemetry=t)
    h = session(c)
    upload_and_consent(c, h)
    parse(c, h)
    assert search(c, h).status_code == 200
    response = analyze(c, h)
    assert response.status_code == 200
    assert wait(c, h, response.json()['run_id'])['status'] == 'done'
    assert sample(t, 'jobfit_analysis_outcomes_total', {'outcome': 'completed'}) == 1
    assert sample(t, 'jobfit_stage_executions_total',
                  {'stage': 'overall_analysis', 'outcome': 'success'}) == 1
    assert len(fake.history) == 1



def test_saved_legacy_recommendation_is_http_traffic_not_analysis_admission():
    t = Telemetry()
    t.request('POST', '/recommendations', 200, .01)
    assert sample(t, 'jobfit_http_requests_total',
                  {'method': 'POST', 'route': '/recommendations', 'status': '200'}) == 1
    assert sample(t, 'jobfit_analysis_requests_total', {'outcome': 'accepted'}) is None
