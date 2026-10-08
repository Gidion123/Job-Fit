"""Subprocess worker for the crash/restart tests (tests/test_live_restart_db.py). Not collected by pytest.

It is one "API process": a LiveRuntime over an existing, provisioned ledger storage root and a scratch
database, with a fake SDK (no provider, no network). It runs one parse operation and prints exact
handshake markers (flushed) so the parent can kill it at a proven boundary:

- complete:          runs the operation to the end, prints ``DONE <op> <outcome>``;
- stop_after_admit:  work() prints ``ADMITTED <op>`` and blocks BEFORE touching the client (no intent);
- stop_in_call:      the fake SDK, reached only after the durable intent, prints ``IN_CALL <attempt_id>``
                     and blocks until the parent kills the process.
"""
from __future__ import annotations

import argparse
import sys
import threading
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import psycopg
from pydantic import BaseModel

from jobfit.config import REPO_ROOT, Settings
from jobfit.live.common import CURRENT_ATTEMPT
from jobfit.live.operation import LiveRuntime
from jobfit.llm.phase_bounds import compute_phase_bounds
from jobfit.llm.runtime import build_runtime_client

CONFIG = REPO_ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'
MSGS = [{'role': 'user', 'content': 'synthetic text'}]


class Answer(BaseModel):
    answer: str


class WorkerSDK:
    def __init__(self, scenario: str, cost: float):
        self.scenario, self.cost = scenario, cost
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **kw):
        return self

    def create(self, **kw):
        if self.scenario == 'stop_in_call':
            print(f'IN_CALL {CURRENT_ATTEMPT.get().attempt_id}', flush=True)
            threading.Event().wait()                     # until SIGKILL
        return SimpleNamespace(id='req', model=kw['model'],
                               usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, cost=self.cost),
                               choices=[SimpleNamespace(finish_reason='stop',
                                                        message=SimpleNamespace(content='{"answer":"ok"}'))])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', required=True)
    parser.add_argument('--root', required=True)
    parser.add_argument('--op', required=True)
    parser.add_argument('--scenario', required=True, choices=('complete', 'stop_after_admit', 'stop_in_call'))
    parser.add_argument('--cost', type=float, default=0.01)
    args = parser.parse_args()
    ledger = Path(args.root) / 'ledger.jsonl'
    sdk = WorkerSDK(args.scenario, args.cost)
    settings = SimpleNamespace(usage_ledger=ledger, database_url=args.db, daily_budget_usd=2.0, api_hard_stop_usd=4.5)
    client_settings = Settings(openrouter_api_key='k' * 40, usage_ledger=ledger, api_budget_usd=5.0,
                               api_hard_stop_usd=4.5)
    rt = LiveRuntime(settings, compute_phase_bounds(), pipeline_config=CONFIG,
                     connect=lambda: psycopg.connect(args.db, autocommit=True),
                     client_factory=lambda op: build_runtime_client(client_settings, CONFIG, run_id=op, sdk_client=sdk),
                     watchdog_interval=0.05, drain_grace=1.0)

    def work(client):
        if args.scenario == 'stop_after_admit':
            print(f'ADMITTED {args.op}', flush=True)
            threading.Event().wait()                     # never reaches the ReservedClient
        return client.chat_structured('deepseek-flash', MSGS, Answer, 'cv_parsing', max_tokens=16000).answer
    _, report = rt.run('parse', args.op, work)
    print(f'DONE {args.op} {report.outcome} {report.spend if report.spend is not None else Decimal(0)}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
