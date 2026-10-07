"""Phase A tooling (D-089): leakage guard, benchmark, registry, prompts and cost cap. No model call."""
import json
from pathlib import Path

import pytest

from jobfit.eval import qa_phase_a as qa
from scripts import qa_phase_a as cli

ROOT = Path(__file__).resolve().parents[1]
CHALLENGERS = ['prompts/evidence_matching_v1_2_qa_e01.md', 'prompts/evidence_matching_v1_2_qa_e02.md',
               'prompts/evidence_matching_v1_2_qa_e03.md']


@pytest.mark.parametrize('path', [
    'evals/gold/test_v13_cp24_r1/relevance_gold.jsonl',
    'evals/gold/test_v13_cp24_r1',
    'evals/labeling/test_relevance_cp24_test_v1_v1/JobFit_Test_Relevance_Final_.xlsx',
    'evals/results/cp24/heldout_report_v1.json',
    'evals/results/cp24/test_run_v1/final_CV3.json',
    'data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md',
    'data/synthetic_cvs/cv_05_ml_engineer_3yr_en.md',
])
def test_guard_refuses_cp24_material(path):
    with pytest.raises(qa.LeakageError):
        qa.dev_path(path)
    with pytest.raises(qa.LeakageError):
        qa.dev_path(ROOT / path)


def test_guard_allows_development_gold():
    assert qa.dev_path('evals/gold/development_v13_reviewed_20261004_gap_r4/relevance_gold.jsonl').exists()


@pytest.mark.parametrize('cv', ['CV3', 'CV4', 'CV5'])
def test_heldout_cvs_cannot_be_optimization_targets(cv):
    job = sorted(qa.dev_job_ids())[0]
    with pytest.raises(qa.LeakageError):
        qa.check_pairs([(cv, job)])


def test_test_jobs_cannot_be_used():
    with pytest.raises(qa.LeakageError):
        qa.check_pairs([('CV1', sorted(qa.test_job_ids())[0])])
    qa.check_pairs([('CV1', sorted(qa.dev_job_ids())[0])])


def test_fixed_input_benchmark_is_development_only_and_answer_free():
    pairs = qa.fixed_input_pairs()
    assert len(pairs) == 42 and sum(len(v['labels']) for v in pairs.values()) == 826
    dev, test = qa.dev_job_ids(), qa.test_job_ids()
    for (cv, job), item in pairs.items():
        assert cv in qa.DEV_CVS and job in dev and job not in test
        dumped = json.dumps(item['extraction'].model_dump(mode='json'))
        assert 'cv_quote' not in dumped and 'MATCH' not in dumped  # requirement text only, never the answer
        assert {u.unit_id for u in item['extraction'].units} == set(item['labels'])


def test_split_is_deterministic_disjoint_and_complete():
    pairs = qa.fixed_input_pairs()
    a, b = qa.split_fixed_input(pairs), qa.split_fixed_input(pairs)
    assert a == b
    opt = {tuple(p) for p in a['optimization']}
    conf = {tuple(p) for p in a['confirmation']}
    assert opt.isdisjoint(conf) and opt | conf == set(pairs)
    assert {j for _, j in opt}.isdisjoint({j for _, j in conf})


def test_saved_split_matches_code():
    saved = json.loads((qa.QA_DIR / 'benchmark_v1/split.json').read_text())
    assert saved['subsets'] == qa.split_fixed_input(qa.fixed_input_pairs())


def test_perfect_predictions_score_one_and_errors_are_counted():
    pairs = qa.fixed_input_pairs()
    gold_rows = {(r['cv_id'], r['job_id'], r['unit_no']): r for r in
                 qa.read_jsonl(qa.DEV_GOLD / 'evidence_gold_gap_v2.jsonl')}
    subset = qa.split_fixed_input(pairs)['optimization'][:3]
    records = {}
    for cv, job in subset:
        rows = []
        for u, label in pairs[(cv, job)]['labels'].items():
            quote = gold_rows[(cv, job, u)]['cv_quote']
            rows.append({'unit_id': u, 'label': label, 'check_status': 'done',
                         'cv_quotes': [quote] if label != 'NO_MATCH' else [], 'branches': [], 'label_source': 'model_draft'})
        records[(cv, job)] = {'status': 'done', 'assessments': rows, 'attempts': 1, 'wall_ms': 1, 'source_flags': []}
    perfect = qa.fixed_input_metrics(records, pairs, [tuple(p) for p in subset])
    assert perfect['accuracy_all_units'] == 1.0 and perfect['unsupported_positive'] == 0
    first = tuple(subset[0])
    neg = next(r for r in records[first]['assessments'] if r['label'] == 'NO_MATCH')
    pos = next(r for r in records[first]['assessments'] if r['label'] != 'NO_MATCH')
    neg.update(label='MATCH', cv_quotes=pos['cv_quotes'])
    worse = qa.fixed_input_metrics(records, pairs, [tuple(p) for p in subset])
    assert worse['unsupported_positive'] == 1 and worse['overclaim'] == 1


def test_failed_pair_counts_against_the_prompt():
    pairs = qa.fixed_input_pairs()
    subset = [tuple(p) for p in qa.split_fixed_input(pairs)['optimization'][:2]]
    m = qa.fixed_input_metrics({subset[0]: {'status': 'failed', 'error_code': 'schema_validation'}}, pairs, subset)
    assert len(m['failed_pairs']) == 2 and m['unassessed_units'] == m['units']


def test_registry_ids_are_unique_and_statuses_checked(tmp_path):
    reg = tmp_path / 'r.csv'
    qa.upsert({'experiment_id': 'QA-X1', 'status': 'planned'}, new=True, path=reg)
    with pytest.raises(ValueError):
        qa.upsert({'experiment_id': 'QA-X1', 'status': 'planned'}, new=True, path=reg)
    with pytest.raises(ValueError):
        qa.upsert({'experiment_id': 'QA-X2', 'status': 'done'}, new=False, path=reg)
    with pytest.raises(ValueError):
        qa.upsert({'experiment_id': 'QA-X1', 'status': 'winner'}, new=False, path=reg)
    qa.upsert({'experiment_id': 'QA-X1', 'status': 'completed', 'macro_f1': 0.5}, new=False, path=reg)
    assert qa.load_registry(reg)[0]['status'] == 'completed'


def test_project_registry_is_consistent():
    rows = qa.load_registry()
    ids = [r['experiment_id'] for r in rows]
    assert len(ids) == len(set(ids)) and 'QA-E00-BASELINE' in ids
    for r in rows:
        assert r['status'] in qa.STATUSES
        assert r['prompt_sha256'] == qa.digest(ROOT / r['prompt_file'])
        assert r['model'] == 'gpt-6-sol'


@pytest.mark.parametrize('prompt', CHALLENGERS)
def test_challenger_prompts_are_new_versioned_files(prompt):
    path = ROOT / prompt
    meta = json.loads(path.with_suffix('.meta.json').read_text())
    assert meta['prompt_sha256'] == qa.digest(path)
    assert meta['parent_prompt'] == 'prompts/evidence_matching_v1_1.md'
    assert 'final' not in path.name
    base = (ROOT / meta['parent_prompt']).read_text().split('\n', 1)[1].rstrip('\n')
    assert base in path.read_text()  # v1.1 text kept word for word; one paragraph added
    for key in ('experiment_id', 'hypothesis', 'created_at', 'intended_change', 'parent_prompt'):
        assert meta[key]


def test_prompt_record_detects_edits(tmp_path, monkeypatch):
    p = tmp_path / 'p.md'
    p.write_text('a')
    p.with_suffix('.meta.json').write_text(json.dumps({'prompt_sha256': qa.digest(p)}))
    assert qa.prompt_record(p)['prompt_sha256'] == qa.digest(p)
    p.write_text('b')
    with pytest.raises(ValueError):
        qa.prompt_record(p)


def test_write_once_never_overwrites(tmp_path):
    qa.write_once(tmp_path / 'x.json', {'a': 1})
    with pytest.raises(FileExistsError):
        qa.write_once(tmp_path / 'x.json', {'a': 2})


def test_frozen_prompt_is_unchanged_and_override_restores_it():
    from jobfit.matching import evidence_matcher as em
    frozen = json.loads((ROOT / 'evals/freeze/cp23_freeze_draft_v2/freeze_receipt.json').read_text())['files_sha256']
    assert qa.digest(ROOT / 'prompts/evidence_matching_v1_1.md') == frozen['prompts/evidence_matching_v1_1.md']
    before = em.EVIDENCE_PROMPT_FILE
    p = ROOT / CHALLENGERS[0]
    with cli.prompt_override(p, qa.digest(p)):
        assert em.EVIDENCE_PROMPT_FILE == p
    assert em.EVIDENCE_PROMPT_FILE == before
    with pytest.raises(SystemExit):
        with cli.prompt_override(p, '0' * 64):
            pass


def test_cost_cap_refuses_runs_over_the_wave_cap():
    ok = {'wave1_spent_usd': 1.0, 'upper_estimate_usd': 1.0, 'ledger_total_usd': 8.0, 'project_hard_stop_usd': 18.5}
    cli.check_run_budget(ok)
    with pytest.raises(SystemExit):
        cli.check_run_budget({**ok, 'wave1_spent_usd': cli.WAVE1_CAP_USD - 0.5})
    with pytest.raises(SystemExit):
        cli.check_run_budget({**ok, 'ledger_total_usd': 18.0})


def test_experiments_never_touch_the_confirmation_subset_or_other_models():
    for exp, spec in cli.EXPERIMENTS.items():
        assert spec['subsets'] == ['optimization'] and exp.startswith('QA-E')
        assert (ROOT / spec['prompt']).exists()
    with pytest.raises(SystemExit):
        cli.plan('QA-E99')


def test_run_without_execute_makes_no_call(capsys, monkeypatch):
    monkeypatch.setattr(cli, 'estimate', lambda p: {'wave1_spent_usd': 0, 'upper_estimate_usd': 0.1})
    called = []
    monkeypatch.setattr('jobfit.matching.evidence_matcher.match_evidence', lambda *a, **k: called.append(1))
    cli.cmd_run(type('A', (), {'exp': 'QA-E01', 'execute': False})())
    assert not called and 'No call made' in capsys.readouterr().out


def test_confirmation_subset_is_sealed_without_one_finalist(tmp_path):
    reg, unseal = tmp_path / 'r.csv', tmp_path / 'u.json'
    assert not qa.confirmation_unsealed(unseal, reg)
    unseal.write_text(json.dumps({'finalist': 'QA-E01'}))
    qa.upsert({'experiment_id': 'QA-E01', 'status': 'completed'}, new=True, path=reg)
    assert not qa.confirmation_unsealed(unseal, reg)
    qa.upsert({'experiment_id': 'QA-E01', 'status': 'finalist'}, new=False, path=reg)
    assert not qa.confirmation_unsealed(unseal, reg)  # amendment 1: the repeat must pass first
    unseal.write_text(json.dumps({'finalist': 'QA-E01', 'repeat': 'QA-E01-R2', 'repeat_passed': True}))
    assert qa.confirmation_unsealed(unseal, reg)
    qa.upsert({'experiment_id': 'QA-E02', 'status': 'finalist'}, new=True, path=reg)
    assert not qa.confirmation_unsealed(unseal, reg)  # exactly one finalist


def test_project_confirmation_is_sealed_now():
    assert not qa.confirmation_unsealed()
    cli.EXPERIMENTS['QA-TMP-CONF'] = {**cli.EXPERIMENTS['QA-E01'], 'subsets': ['confirmation']}
    try:
        with pytest.raises(SystemExit, match='sealed'):
            cli.plan('QA-TMP-CONF')
    finally:
        del cli.EXPERIMENTS['QA-TMP-CONF']


def test_wave1_is_staged_and_repeat_needs_the_single_finalist():
    order = ['QA-E00-FI-R1', 'QA-E00-FI-R2', 'QA-E01', 'QA-E02', 'QA-E03']
    for prev, nxt in zip(order, order[1:]):
        assert cli.EXPERIMENTS[nxt]['requires_evaluated'] == [prev]
    assert 'QA-E03-R' not in cli.EXPERIMENTS
    for e in ('QA-E01', 'QA-E02', 'QA-E03'):
        spec = cli.EXPERIMENTS[f'{e}-R2']
        assert spec['requires_finalist'] == e and spec['replicate_of'] == e
        assert spec['prompt'] == cli.EXPERIMENTS[e]['prompt'] and spec['subsets'] == ['optimization']
    if not (qa.QA_DIR / 'QA-E03' / 'metrics.json').exists():
        with pytest.raises(SystemExit, match='runs after'):
            cli.check_stage('QA-E01-R2')


def test_rejected_units_never_enter_the_benchmark():
    rejected = {(u['job_id'], u['unit_no']) for u in qa.read_jsonl(qa.DEV_GOLD / 'extraction_gold_gap_v2.jsonl')
                if u['review_action'] == 'rejected'}
    for (cv, job), item in qa.fixed_input_pairs().items():
        assert not {(job, u.unit_id) for u in item['extraction'].units} & rejected


def test_reference_provenance_comes_from_source_metadata():
    prov = qa.reference_provenance()
    answers = prov['fixed_input_answers (evidence_gold_gap_v2.jsonl)']
    assert sum(answers.values()) == 826
    assert all(k.startswith('model_draft_assisted_human_accepted') for k in answers)
    assert 'not independent human ground truth' in prov['statement']


def test_key_limit_check_refuses_runs_the_key_cannot_finish():
    cli.check_key_limit({'limit_remaining': 2.0}, 1.61)
    cli.check_key_limit({'limit': None, 'limit_remaining': None}, 1.61)  # no numeric key limit set
    with pytest.raises(SystemExit, match='below the upper estimate'):
        cli.check_key_limit({'limit_remaining': 0.5}, 1.61)
    with pytest.raises(SystemExit, match='Cannot read'):
        cli.check_key_limit({'error': 'APIConnectionError'}, 1.61)


def test_label_transitions_counts_changes():
    pairs = qa.fixed_input_pairs()
    key = tuple(qa.split_fixed_input(pairs)['optimization'][0])
    units = list(pairs[key]['labels'])
    def rec(labels):
        return {'status': 'done', 'assessments': [{'unit_id': u, 'label': l, 'check_status': 'done',
                                                   'cv_quotes': ['x'] if l != 'NO_MATCH' else [], 'branches': [],
                                                   'label_source': 'model_draft'} for u, l in labels.items()]}
    a = {u: 'NO_MATCH' for u in units}
    b = {**a, units[0]: 'PARTIAL'}
    res = qa.label_transitions({key: rec(a)}, {key: rec(b)}, pairs, [key])
    assert res['changed'] == 1 and res['transitions'] == {'NO_MATCH->PARTIAL': 1} and res['units'] == len(units)


def test_failure_classes_keep_infrastructure_out_of_prompt_quality():
    for code in ('APITimeoutError', 'APIConnectionError', 'RateLimitError', 'PermissionDeniedError', 'RunCapReached'):
        assert qa.failure_class(code) == 'transient_operational'
    for code in ('schema_validation', 'truncated', 'assessment_coverage', 'invalid_structured_output_or_source'):
        assert qa.failure_class(code) == 'prompt_induced'
    assert qa.failure_class('SomethingNew') == 'unclassified'


def _rule():
    return json.loads(qa.RULE_FILE.read_text())


def _fake(macro, acc, up, over, under=19, unassessed=14, p5=0.7, ndcg=0.56, quotes=1.0, failed=()):
    loo = {k: acc for k in _rule()['baseline']['leave_one_pair_out_accuracy_mean']}
    fi = {'macro_f1': macro, 'accuracy_all_units': acc, 'unsupported_positive': up, 'overclaim': over, 'underclaim': under,
          'unassessed_units': unassessed, 'failed_pairs': list(failed), 'prompt_induced_failed_pairs': len(failed),
          'failure_classes': {'prompt_induced': len(failed)} if failed else {}, 'leave_one_pair_out_accuracy': loo}
    return {'fixed_input_optimization': fi, 'grounding': {'quote_validity': quotes, 'invalid_quote_items': 0 if quotes == 1.0 else 1},
            'ranking': {'macro_p_at_5': p5, 'macro_ndcg_at_10': ndcg}}


def _fails(pairs_with_up):
    return {'unit_errors': [{'unit': f'{p}/U{i}', 'gold': 'NO_MATCH', 'pred': 'PARTIAL'} for p, n in pairs_with_up.items() for i in range(n)]}


def test_rule_was_locked_before_any_challenger_result():
    rule = _rule()
    assert rule['baseline_runs'] == ['QA-E00-FI-R1', 'QA-E00-FI-R2']
    assert abs(rule['practical_improvement_reference_macro_f1'] - 0.7343) < 1e-3
    assert rule['hard_gates']['unsupported_positive_max'] == 59
    locked = rule['locked_at']
    for e in ('QA-E01', 'QA-E02', 'QA-E03'):
        plan = qa.QA_DIR / e / 'plan.json'
        if plan.exists():
            assert json.loads(plan.read_text())['created_at'] > locked


def test_scorecard_gates_and_paths():
    rule = _rule()
    base = [json.loads((qa.QA_DIR / e / 'failures.json').read_text()) for e in rule['baseline_runs']]
    spread = {'CV1/F1': 0}
    for bf in base:
        for k, v in qa.per_pair_unsupported(bf).items():
            spread[k] = v
    fewer = {k: 0 for k in spread}
    # path B: F1 below the +0.02 reference but unsupported/overclaims down materially -> eligible
    b = qa.scorecard(_fake(0.72, 0.76, 50, 58), rule, failures=_fails(fewer), baseline_failures=base)
    assert b['gates_passed'] and b['path_B'] and not b['path_A'] and b['eligible']
    # more unsupported positives than the baseline -> rejected even with a high F1 and better ranking
    worse = qa.scorecard(_fake(0.80, 0.82, 60, 50, p5=0.9, ndcg=0.7), rule, failures=_fails(fewer), baseline_failures=base)
    assert not worse['gates']['unsupported_not_worse'] and not worse['eligible']
    # a prompt-induced failure is a regression (baseline has none)
    assert not qa.scorecard(_fake(0.80, 0.82, 50, 50, failed=['CV1/F']), rule, failures=_fails(fewer), baseline_failures=base)['eligible']
    # ranking non-inferiority
    assert not qa.scorecard(_fake(0.80, 0.82, 50, 50, p5=0.6), rule, failures=_fails(fewer), baseline_failures=base)['eligible']
    # path A
    a = qa.scorecard(_fake(0.75, 0.77, 59, 66), rule, failures=_fails(spread), baseline_failures=base)
    assert a['path_A'] and a['eligible']


def test_pick_finalist_prefers_fewer_unsupported_then_f1():
    card = lambda up, f1, ok=True: {'eligible': ok, 'values': {'unsupported_positive': up, 'macro_f1': f1, 'accuracy': f1}}
    assert qa.pick_finalist({'QA-E01': card(59, 0.75), 'QA-E02': card(45, 0.72)}) == 'QA-E02'
    assert qa.pick_finalist({'QA-E01': card(46, 0.75), 'QA-E02': card(45, 0.72)}) == 'QA-E01'
    assert qa.pick_finalist({'QA-E01': card(40, 0.9, ok=False)}) is None


def test_budget_plan_stays_below_hard_stop_and_covers_need(monkeypatch):
    # Approved Phase A budget (D-070, .env.example), set here so the test does not depend on a local .env (FAIL-35).
    monkeypatch.setenv('API_BUDGET_USD', '19')
    monkeypatch.setenv('API_HARD_STOP_USD', '18.5')
    b = cli.budget_plan()
    assert b['recommended_key_limit_usd'] < b['project_hard_stop_usd']
    assert b['covered'] and b['recommended_key_limit_usd'] >= b['needed_total_usd']


def test_staged_plan_splits_fixed_input_and_ranking():
    a, b = cli.plan('QA-E02', 'A'), cli.plan('QA-E02', 'B')
    assert a['fixed_input_pairs'] and not a['ranking_pairs'] and a['ranking'] is False
    assert b['ranking_pairs'] and not b['fixed_input_pairs'] and b['run_id'].endswith('_ranking')
    assert len(a['fixed_input_pairs']) == 20 and len(b['ranking_pairs']) == 19
    assert cli.plan('QA-E02')['stage'] == 'A'  # default is Stage A
    with pytest.raises(SystemExit):
        cli.plan('QA-E01', 'A')  # E01 ran before amendment 2 and is not staged
    assert not cli.EXPERIMENTS['QA-E03']['approved']  # E03 only on Dion's request


def test_stage_b_refused_without_a_continue_decision(monkeypatch):
    monkeypatch.setattr(cli, 'estimate', lambda p: {'wave1_spent_usd': 0, 'upper_estimate_usd': 0.1,
                                                     'ledger_total_usd': 1, 'project_hard_stop_usd': 18.5})
    monkeypatch.setattr(cli, 'check_stage', lambda exp: None)
    monkeypatch.setattr(cli, 'stage_a_decision', lambda exp: 'stop')
    with pytest.raises(SystemExit, match='Stage A check'):
        cli.cmd_run(type('A', (), {'exp': 'QA-E02', 'execute': True, 'stage': 'B'})())


def test_ranking_never_rescues_a_stage_a_result():
    rule = _rule()
    base = [json.loads((qa.QA_DIR / e / 'failures.json').read_text()) for e in rule['baseline_runs']]
    card = qa.scorecard(_fake(0.70, 0.76, 47, 61, p5=1.0, ndcg=1.0), rule, failures=_fails({}), baseline_failures=base)
    assert card['gates_passed'] and not card['path_A'] and not card['path_B'] and not card['eligible']
