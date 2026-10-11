"""Read-only collector vs real PostgreSQL accounting. Disposable server only; fake SDK."""
import os
from decimal import Decimal
import hashlib

import psycopg
import pytest

from jobfit.observability.cost import CostSnapshot
from jobfit.observability.metrics import Telemetry
from jobfit.session.store import SessionStore
from tests.test_live_runtime_db import ADMIN, baseline, command, alembic_config, key
from tests.test_public_beta_runtime_db import beta_runtime, parse_work, reservations
from tests.test_real_cv_runtime_db import runtime, fake_sdk, consented, parse, search, seed

pytestmark = pytest.mark.skipif(os.environ.get('JOBFIT_MIGRATION_TESTS') != '1' or not ADMIN,
                                reason='requires dedicated disposable PostgreSQL')


@pytest.fixture
def db():
    with baseline.scratch_database(ADMIN) as url:
        command.upgrade(alembic_config(url), 'head')
        yield url


def hashes(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}


def test_scrape_matches_settled_runtime_and_does_not_mutate_files_or_db(db, tmp_path):
    t = Telemetry()
    rt = beta_runtime(db, tmp_path / 'root', telemetry=t)
    result, report = rt.run('parse', key(), parse_work)
    assert result == 'ok' and report.outcome == 'settled'
    snapshot = CostSnapshot(rt.ledger_path, lambda: psycopg.connect(db, autocommit=True), 5, 25, 25)
    before, before_rows = hashes(rt.ledger_path.parent), reservations(db)
    a = snapshot()
    assert a['recorded_spend_usd'] == a['settled_usd'] == a['reported_cost_usd'] == Decimal('.001')
    assert a['daily_settled_usd'] == a['daily_liability_usd'] == Decimal('.001')
    assert a['uncertain_cost_usd'] == 0 and a['open_reserved_usd'] == 0
    assert a == snapshot()  # persisted values, independent of process counters
    assert before == hashes(rt.ledger_path.parent) and before_rows == reservations(db)
    assert len(rt.sdk.calls) == 1
    assert t.registry.get_sample_value('jobfit_stage_executions_total', {'stage': 'parse', 'outcome': 'success'}) == 1


def test_consented_fake_parse_embed_and_retrieval_have_real_separate_timings(db, tmp_path):
    t = Telemetry()
    rt = runtime(db, tmp_path / 'root', fake_sdk())
    rt.telemetry = t
    store = SessionStore()
    h, lease = consented(store)
    parse(rt, store, h, lease, telemetry=t)
    seed(db)
    search(rt, store, h, lease, db, telemetry=t)
    for stage in ('cv_parse', 'query_embedding', 'retrieval', 'parse', 'search'):
        assert t.registry.get_sample_value('jobfit_stage_duration_seconds_count',
                                           {'stage': stage, 'outcome': 'success'}) == 1
    assert len(rt.sdk.calls) == 2
    body = t.render().decode()
    assert 'PT Contoh' not in body and h.session_id not in body and 'Python and SQL' not in body


def test_postgres_health_collector_uses_read_only_transaction(db):
    from jobfit.observability.cost import DatabaseCollector
    t = Telemetry()
    t.registry.register(DatabaseCollector(lambda: psycopg.connect(db, autocommit=True, connect_timeout=2)))
    assert t.registry.get_sample_value('jobfit_postgres_available') == 1
    assert t.registry.get_sample_value('jobfit_postgres_available') == 1
