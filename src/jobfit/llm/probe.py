"""Durable, aggregate-capped quality probe. Operational checks never approve gold."""
from decimal import Decimal
import json
import os
from pathlib import Path
from jobfit.llm.budget import BudgetExceeded
from jobfit.llm.client import strict_schema
from jobfit.llm.pricing import estimate_cost


class ProbeSession:
    MAX_CEILING = Decimal("0.20")
    def __init__(self, path: Path, *, run_id, fingerprint, jobs, ledger, ceiling='0.20'):
        self.path, self.ledger = Path(path), ledger
        cap = Decimal(str(ceiling))
        if not cap.is_finite() or not 0 < cap <= self.MAX_CEILING:
            raise ValueError(f'Probe ceiling must be positive and at most US${self.MAX_CEILING}')
        identity = dict(run_id=run_id, fingerprint=fingerprint, jobs=jobs, ceiling=str(cap))
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
            if any(self.data.get(k) != v for k, v in identity.items()):
                raise ValueError('Probe identity/configuration changed; budget cannot be reset')
        else:
            # Existing receipts with this ID must not be hidden by a missing state.
            if any(r.run_id == run_id for r in ledger.records()):
                raise ValueError('Probe receipts exist without state; reconcile before continuing')
            self.data = dict(identity, status='ready', results=[], reservations=[])
            self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        with tmp.open('w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, self.path)

    def spent(self):
        costs = [Decimal(str(r.cost_usd)) for r in self.ledger.records()
                 if r.run_id == self.data['run_id'] and not r.cached]
        if any(not x.is_finite() or x < 0 for x in costs):
            raise ValueError('Invalid probe ledger cost')
        return sum(costs, Decimal(0))

    def check_budget(self, upper):
        upper = Decimal(str(upper))
        if not upper.is_finite() or upper < 0:
            raise ValueError('Invalid probe estimate')
        if self.data['reservations']:
            raise BudgetExceeded('Unsettled attempt: stop and reconcile, never repeat it automatically')
        if self.spent() + upper > Decimal(self.data['ceiling']):
            raise BudgetExceeded('Aggregate probe ceiling includes prior attempts and repairs')

    def begin(self, job_id):
        index = len(self.data['results'])
        if self.data['status'] != 'ready' or index >= len(self.data['jobs']):
            raise ValueError('Probe stopped or waiting for semantic inspection')
        if job_id != self.data['jobs'][index]:
            raise ValueError('Probe must follow the frozen JD order')
        self.check_budget(0)
        self.data.update(status='running', active_job=job_id)
        self.save()

    def finish(self, result):
        if self.data['status'] != 'running' or result['job_id'] != self.data['active_job']:
            raise ValueError('Unexpected probe result')
        self.data['results'].append(result)
        self.data['status'] = 'awaiting_semantic_check' if result['status'] == 'done' else 'stopped_process_failure'
        self.save()

    def record_check(self, check):
        if self.data['status'] != 'awaiting_semantic_check':
            raise ValueError('Only a completed, unchecked result can receive an operational check')
        last = self.data['results'][-1]
        if check.get('job_id') != last['job_id'] or check.get('result_sha256') != last['result_sha256']:
            raise ValueError('Check must identify the exact result')
        required = {'quotes', 'coverage', 'grouping', 'qualifiers', 'importance'}
        if set(check.get('checks', {})) != required or not check.get('notes') or not check.get('checked_by'):
            raise ValueError('Record source-based inspection of every semantic dimension')
        if any(x not in {'pass', 'fail', 'uncertain'} for x in check['checks'].values()):
            raise ValueError('Invalid check outcome')
        check = dict(check, human_annotation_approval=False, alignment_status='pending')
        last['operational_check'] = check
        passed = all(x == 'pass' for x in check['checks'].values())
        self.data['status'] = ('complete' if len(self.data['results']) == len(self.data['jobs']) else 'ready') if passed else 'stopped_semantic_issue'
        self.save()


class ProbeClient:
    """Wrap the existing client, retaining its privacy, project guard and ledger."""
    def __init__(self, client, session):
        self.client, self.session = client, session
        if client.run_id != session.data['run_id']:
            raise ValueError('All probe continuations must use the same ledger run ID')

    def chat_structured(self, model, messages, output_model, task, max_tokens=2000, temperature=0):
        s, c = self.session, self.client
        if s.data['status'] != 'running':
            raise ValueError('Probe is not running')
        schema = strict_schema(output_model.model_json_schema())
        tokens = len(json.dumps(messages, ensure_ascii=False).encode()) + len(json.dumps(schema).encode()) + 512
        upper = estimate_cost(c.prices[model], tokens, max_tokens)
        s.check_budget(upper)
        c.guard.check(upper)
        before = len([r for r in c.ledger.records() if r.run_id == c.run_id])
        s.data['reservations'].append({'upper_usd': upper, 'ledger_count_before': before})
        s.save()  # Persist before network; a crash cannot release uncertain spend.
        try:
            return c.chat_structured(model, messages, output_model, task, max_tokens=max_tokens, temperature=temperature)
        finally:
            after = len([r for r in c.ledger.records() if r.run_id == c.run_id])
            if after > before:
                s.data['reservations'].clear()
            s.save()
