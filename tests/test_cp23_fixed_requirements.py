import json
import importlib.util
from pathlib import Path

import pytest

from jobfit.config import REPO_ROOT
from jobfit.eval.fixed_requirements import fixed_reviewed_requirements
from scripts.run_batch_extraction import development_sources

_spec = importlib.util.spec_from_file_location('matcher_preflight', REPO_ROOT/'scripts/prepare_cp23_stage2_matching.py')
matcher_preflight = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(matcher_preflight)

BUNDLE = REPO_ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3'
JOBS = ('F00332', 'F00036', 'F00815', 'F00018')


def source(job):
    return development_sources([job])[0]['text']


def copy_inputs(tmp_path):
    for name in ('extraction_gold.jsonl', 'logical_units.json'):
        (tmp_path/name).write_bytes((BUNDLE/name).read_bytes())
    return tmp_path


def test_all_four_fixed_inputs_retain_one_unit_per_reviewed_logical_unit():
    expected = {'F00332': (16, 1), 'F00036': (17, 5), 'F00815': (16, 4), 'F00018': (24, 3)}
    for job, (rows, groups) in expected.items():
        fixed = fixed_reviewed_requirements(BUNDLE, job, source(job))
        assert len(fixed.units) == rows
        assert sum(u.kind.value == 'alternative_group' for u in fixed.units) == groups
        assert all(u.label_source.value == 'annotator' for u in fixed.units)
        assert all(u.source_quotes for u in fixed.units)
    assert sum(x[0] for x in expected.values()) == 73


def test_and_requirements_remain_separate_and_or_qualifiers_apply_to_every_branch():
    f = fixed_reviewed_requirements(BUNDLE, 'F00332', source('F00332'))
    assert [u.unit_id for u in f.units if u.text in {'Python', 'SQL', 'Microsoft Excel'}] == ['P30-U02', 'P30-U03', 'P30-U04']
    g = fixed_reviewed_requirements(BUNDLE, 'F00036', source('F00036'))
    branches = next(u.branches for u in g.units if u.unit_id == 'P09-U03')
    assert len(branches) == 3
    assert all('data manipulation and analysis' in b.text for b in branches)
    h = fixed_reviewed_requirements(BUNDLE, 'F00815', source('F00815'))
    api = next(u.branches for u in h.units if u.unit_id == 'P52-U09')
    assert all('building and deploying APIs' in b.text for b in api)


def test_source_and_reviewed_or_mutations_fail_closed(tmp_path):
    folder = copy_inputs(tmp_path)
    with pytest.raises(ValueError):
        fixed_reviewed_requirements(folder, 'F00036', source('F00036').replace('Python, R, atau SQL', 'Python'))
    p = folder/'extraction_gold.jsonl'
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    row = next(r for r in rows if r['job_id'] == 'F00036' and r['unit_no'] == 'P09-U03')
    row['unit_text'] = 'Python | R | SQL'
    p.write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
    with pytest.raises(ValueError, match='OR meaning changed'):
        fixed_reviewed_requirements(folder, 'F00036', source('F00036'))


def test_missing_logical_or_held_reference_fails_closed(tmp_path):
    folder = copy_inputs(tmp_path)
    p = folder/'logical_units.json'
    rows = json.loads(p.read_text())
    row = next(r for r in rows if r['job_id'] == 'F00815')
    row['status'] = 'held'
    p.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='Held'):
        fixed_reviewed_requirements(folder, 'F00815', source('F00815'))


def test_matcher_preflight_uses_identical_fixed_inputs_and_no_inference():
    plan = matcher_preflight.prepare()
    assert plan['status'] == 'offline_preflight_only' and plan['model_calls'] == 0
    assert plan['stage_count'] == 16 and plan['maximum_calls_including_repairs'] == 32
    assert float(plan['conservative_upper_usd']) > 1
    for pair in {(s['cv_id'], s['job_id']) for s in plan['stages']}:
        rows = [s for s in plan['stages'] if (s['cv_id'], s['job_id']) == pair]
        assert len(rows) == 4
        assert len({s['fixed_requirements_sha256'] for s in rows}) == 1
        assert len({s['cv_sha256'] for s in rows}) == 1
        assert len({s['jd_source_sha256'] for s in rows}) == 1
    scoped = [s for s in plan['stages'] if (s['cv_id'], s['job_id']) == ('CV1', 'F00036')]
    assert all(s['duration_input'] == {'P09-U02': 0.75} for s in scoped)
    assert all('upper_bound_only' in s['duration_basis'] for s in scoped)
