"""D-097 acceptance: the full frozen recommendation pipeline gives the same Recommendation serially
(the frozen client, whose whole-call lock serializes every provider call) and concurrently (the Phase 2B
ReservedClient). Fake SDK only; no frozen file is touched.

Frozen code exercised: recommend(), analyze_job() (Sol, then the Luna fallback), match_evidence() with
the quote-check v1.1 validator and the G1/G2 guardrails, validated_call() (repair and continuation),
the hold policy, scoring, the experience rule and the product order.
"""
import json
import re
import threading
from collections import Counter

from jobfit.config import Settings
from jobfit.llm.runtime import build_runtime_client
from jobfit.recommend.service import RecommendConfig, recommend
from jobfit.schemas.requirements import JDExtraction
from tests.test_cv_upload_pipeline import parsed
from tests.test_live_unit import CONFIG, LUNA, SOL, FakeSDK, Live, response

UNITS = {
    'python': {'unit_id': 'python', 'text': 'Python', 'field': 'skill_tool', 'importance': 'required',
               'source_quotes': ['Python']},
    'git': {'unit_id': 'git', 'text': 'Git', 'field': 'skill_tool', 'importance': 'required', 'source_quotes': ['Git']},
    'sql': {'unit_id': 'sql', 'text': 'SQL', 'field': 'skill_tool', 'importance': 'preferred', 'source_quotes': ['SQL']},
    'docker': {'unit_id': 'docker', 'text': 'Docker', 'field': 'skill_tool', 'importance': 'required',
               'source_quotes': ['Docker']},
}
JOBS = {   # job -> units (None: no extraction, held before matching)
    'J01': ['python', 'git'], 'J02': ['python'], 'J03': ['git'], 'J04': ['python', 'sql'],
    'J05': ['docker'], 'J06': ['python', 'docker'], 'J07': None, 'J08': ['git', 'sql'],
    'J09': ['python', 'git', 'docker'], 'J10': ['sql'], 'J11': ['python'], 'J12': ['git'],
}
SOL_FAILS = {'J04'}               # Sol answers fail validation twice (repair), Luna answers validly
BOTH_FAIL = {'J08'}               # both chains fail: held


def extraction(job):
    units = JOBS[job]
    if units is None:
        return None, 'not_extracted'
    return JDExtraction.model_validate({'job_id': job, 'units': [UNITS[u] for u in units]}), None


def answer(kw):
    """Deterministic evidence answer from the request payload (job id, units, model)."""
    data = json.loads(kw['messages'][1]['content'])['untrusted_document_data']
    job, units = data['extraction']['job_id'], [u['unit_id'] for u in data['extraction']['units']]
    if job in BOTH_FAIL or (job in SOL_FAILS and kw['model'] == SOL):
        return response(kw['model'], json.dumps({'assessments': []}))              # coverage failure
    python_quote = re.search(r'- Membersihkan dan menggabungkan.*?PostgreSQL\)\.', data['cv_text'], re.S)[0]
    rows = []
    for u in units:
        if u == 'python':
            rows.append({'unit_id': u, 'label': 'MATCH', 'cv_quotes': [python_quote]})
        elif u == 'git':
            rows.append({'unit_id': u, 'label': 'PARTIAL', 'cv_quotes': ['Git']})
        elif u == 'sql':
            rows.append({'unit_id': u, 'label': 'MATCH', 'cv_quotes': [python_quote]})
        else:
            rows.append({'unit_id': u, 'label': 'NO_MATCH', 'cv_quotes': []})
    return response(kw['model'], json.dumps({'assessments': rows}))


def run(client):
    ids = list(JOBS)
    return recommend(parsed(), retrieve=lambda depth: ids[:depth], buckets={}, extraction_for=extraction,
                     client=client, config=RecommendConfig.from_yaml(CONFIG))


def semantic(rec):
    """Every deterministic, user-visible field of a Recommendation (no latency, no attempt ids)."""
    def dump(x):
        return x.model_dump(mode='json') if hasattr(x, 'model_dump') else x
    return {'cv_id': rec.cv_id, 'order': rec.order, 'stage1': rec.stage1_ids, 'analyzed': rec.analyzed_ids,
            'demoted': rec.demoted_ids, 'held': rec.held_ids, 'fallback': rec.fallback_ids,
            'versions': rec.versions, 'filter_states': rec.filter_states, 'empty': rec.empty_message,
            'jobs': {j: {'rank': r.stage1_rank, 'score': dump(r.score), 'assessments': [dump(a) for a in r.assessments],
                         'hold': r.hold_reason, 'fallback': r.used_fallback, 'matcher': r.matcher_model,
                         'attempts': r.attempts, 'excluded': r.excluded_units,
                         'constraints': [dump(c) for c in r.constraints],
                         'extraction': dump(r.extraction) if r.extraction else None}
                     for j, r in sorted(rec.jobs.items())}}


def calls(sdk):
    return Counter((kw['model'], kw['messages'][1]['content']) for kw in sdk.calls)


def test_serial_and_concurrent_recommendations_are_identical(tmp_path):
    serial_sdk = FakeSDK(answer, delay=0.05)
    serial_client = build_runtime_client(Settings(openrouter_api_key='k' * 40, usage_ledger=tmp_path / 's.jsonl',
                                                  api_budget_usd=5.0, api_hard_stop_usd=4.5),
                                         CONFIG, sdk_client=serial_sdk)
    serial = run(serial_client)
    assert serial_sdk.max_active == 1                     # the frozen whole-call lock serializes

    live = Live(tmp_path / 'c', phase='recommendation', sdk=FakeSDK(answer, delay=0.05))
    concurrent = run(live.client)
    assert live.sdk.max_active > 1                         # matching calls really overlap (FAIL-36)
    assert live.op.fatal_refusal is None

    assert semantic(concurrent) == semantic(serial)
    assert concurrent == serial
    # the scenario is not trivial: scored, held (no extraction, both chains failed) and fallback jobs
    assert set(serial.held_ids) == {'J07', 'J08'} and serial.fallback_ids == ['J04', 'J08']
    assert len({r.score.score_pct for r in serial.jobs.values() if r.score.score_pct is not None}) > 2
    # the same provider requests, one correlated ledger line and one intent per call
    assert calls(live.sdk) == calls(serial_sdk)
    lines, intents = live.ledger_rows(), live.intents()
    assert len(lines) == len(intents) == len(live.sdk.calls)
    assert {r['attempt_id'] for r in lines} == {i['attempt_id'] for i in intents}
    models = Counter(kw['model'] for kw in live.sdk.calls)
    assert models[LUNA] == 2 * len(BOTH_FAIL) + len(SOL_FAILS) and models[SOL] > models[LUNA]
    assert not live.op.inflight and threading.active_count() >= 1
