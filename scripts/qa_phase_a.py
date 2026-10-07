"""Phase A: controlled prompt optimization on development data only (D-089).

Subcommands
  baseline        write QA-E00-BASELINE from saved development artifacts (no model call)
  dry-run --exp   plan, pair count, expected calls and cost estimate for one experiment (no call)
  run --exp       paid run; refuses without --execute and inside the Wave 1 cap
  evaluate --exp  metrics, failures, cost and receipt from the saved run records (no call)
  status          print the experiment registry
  repeatability   offline unit-level agreement and label transitions between two runs (--a, --b)
  key-status      read-only provider key numbers (GET /key, no inference); with --exp, can that run start?
  lock-rule       write the preregistered selection rule (amendment 1) before any challenger result
  select          scorecard for E01-E03 and exactly one provisional finalist (or keep baseline)
  repeat-check    gates on <finalist>-R2; unseals the confirmation subset only if it passes
  recover --exp   one documented retry per pair for transient failures only (same prompt and settings)
  budget-plan     upper-bound money still needed and the recommended provider key limit
  run --stage A|B staged challengers (amendment 2): A = fixed-input pairs only, B = ranking pairs only
  stage-a-check   stop or continue_to_ranking after Stage A, from the locked rule
  evaluate-ranking  Stage B metrics (ranking, its quotes and cost)

CP2.4 is locked: CV3-CV5, the test labels, the test workbook and the CP2.4 results are refused
by jobfit.eval.qa_phase_a.dev_path / check_pairs. The model, retriever, K, weight, rules,
schema, validator and guardrails stay as in the D-087 freeze; only the evidence prompt changes.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.eval import qa_phase_a as qa  # noqa: E402

CONFIG = ROOT / 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'
OLD = ROOT / 'evals/results/cp23/end_to_end_dev/cp23_end_to_end_dev_20261004_v1'
V11 = ROOT / 'evals/results/cp23/pipeline_v11'
SOL_SAVED = ROOT / 'evals/results/cp23/matcher_coverage_gpt-6-sol_v1'
SWEEP = ROOT / 'evals/results/cp23/dev_eval_v2_20261004/model_sweep_stage1_v4.json'
FEATURES = ROOT / 'data/processed/jobs_features.jsonl'
BASE_PROMPT = 'prompts/evidence_matching_v1_1.md'
MODEL = 'gpt-6-sol'
WAVE1_PREFIX = 'qa_phase_a_w1_'
WAVE1_CAP_USD = 7.50
WORKERS = 6
EXPERIMENTS = {
    'QA-E00-FI-R1': {'requires_evaluated': [], 'approved': True, 'hypothesis': 'QA-E00', 'parent': 'QA-E00-BASELINE', 'prompt': BASE_PROMPT,
                     'subsets': ['optimization'], 'ranking': False, 'replicate_of': None,
                     'purpose': 'Baseline prompt v1.1 on the new fixed-input optimization subset.'},
    'QA-E00-FI-R2': {'requires_evaluated': ['QA-E00-FI-R1'], 'approved': True, 'hypothesis': 'QA-E00', 'parent': 'QA-E00-FI-R1', 'prompt': BASE_PROMPT,
                     'subsets': ['optimization'], 'ranking': False, 'replicate_of': 'QA-E00-FI-R1',
                     'purpose': 'Same as R1, run again: run-to-run noise of the baseline.'},
    'QA-E01': {'requires_evaluated': ['QA-E00-FI-R2'], 'approved': True, 'hypothesis': 'QA-H01', 'parent': 'QA-E00-FI-R1', 'prompt': 'prompts/evidence_matching_v1_2_qa_e01.md',
               'subsets': ['optimization'], 'ranking': True, 'replicate_of': None,
               'purpose': 'MATCH/PARTIAL calibration toward guideline B1/B2.'},
    'QA-E02': {'requires_evaluated': ['QA-E01'], 'approved': True, 'staged': True, 'hypothesis': 'QA-H02', 'parent': 'QA-E00-FI-R1', 'prompt': 'prompts/evidence_matching_v1_2_qa_e02.md',
               'subsets': ['optimization'], 'ranking': True, 'replicate_of': None,
               'purpose': 'Direct-evidence check against overclaiming.'},
    'QA-E03': {'requires_evaluated': ['QA-E02'], 'approved': False, 'staged': True, 'hypothesis': 'QA-H03', 'parent': 'QA-E00-FI-R1', 'prompt': 'prompts/evidence_matching_v1_2_qa_e03.md',
               'subsets': ['optimization'], 'ranking': True, 'replicate_of': None,
               'purpose': 'Ordered procedure and self-check for stability.'},
    # Amendment 1 (7 Oct 2026): the repeat is for the one provisional finalist, not fixed to E03.
    **{f'{e}-R2': {'requires_evaluated': ['QA-E01', 'QA-E02', 'QA-E03'], 'requires_finalist': e, 'approved': True,
                   'hypothesis': h, 'parent': e, 'prompt': f'prompts/evidence_matching_v1_2_{e.lower().replace("-", "_")}.md',
                   'subsets': ['optimization'], 'ranking': False, 'replicate_of': e,
                   'purpose': f'Repeat of {e} on the same optimization subset, only if {e} is the single provisional finalist.'}
       for e, h in (('QA-E01', 'QA-H01'), ('QA-E02', 'QA-H02'), ('QA-E03', 'QA-H03'))},
}
ANALYST_NOTES = {  # Claude's reading of the saved records; to be checked by Dion
    'CV1/F00020': 'Mentoring/teaching role outside the target families (relevance 0); generic tool units match, and two responsibility lines were extracted as units.',
    'CV2/F00020': 'Same mentoring role; generic tool units match.',
    'CV2/F00645': 'Required 2 years is needs_clarification and excluded under H2v2, so the score ignores the main gap.',
    'CV1/F00556': 'Internship asks for a current student; most other units are PARTIAL/MATCH, so the score stays high.',
    'CV2/F00176': '26 required units from one long list (over-splitting); many basic API units are NO_MATCH, so the score is low.',
    'CV1/F00366': 'Extraction not usable (held_extraction).',
    'CV1/F00022': 'Two required units not judged (needs_clarification), so the job is on hold.',
    'CV1/F00103': 'One required unit not judged, so the job is on hold.',
    'CV2/F00559': 'No required unit extracted (responsibilities-only JD), so no score.',
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def read(path):
    return json.loads(qa.dev_path(path).read_text())


def versions() -> dict:
    import importlib.metadata as md
    out = {'python': platform.python_version()}
    for pkg in ('pydantic', 'openai', 'numpy', 'pandas', 'matplotlib', 'pyyaml'):
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            out[pkg] = None
    return out


# ---------------------------------------------------------------- shared inputs

def dev_inputs():
    from jobfit.cv.parser import ParsedCV
    from scripts.run_cp23_luna_matching import matchable
    rankings = read(OLD / 'plan.json')['rankings']
    redo = set(read(V11 / 'plan_v1.json')['redo_jds'])
    buckets = {json.loads(l)['final_cluster_id']: json.loads(l).get('experience_bucket')
               for l in qa.dev_path(FEATURES).read_text().splitlines()}
    top = qa.ranking_pairs(rankings, buckets)
    cvs = {cv: ParsedCV.model_validate(read(OLD / f'{cv}_parse.json')['parsed']) for cv in qa.DEV_CVS}
    extractions = {(cv, j): matchable(j, redo) for cv in qa.DEV_CVS for j in top[cv]}
    labels = {cv: {} for cv in qa.DEV_CVS}
    for row in qa.read_jsonl(qa.DEV_GOLD / 'relevance_gold.jsonl'):
        if row['cv_id'] in labels and row.get('review_status') == 'approved':
            labels[row['cv_id']][row['job_id']] = int(row['relevance_0_3'])
    return {'top': top, 'cvs': cvs, 'extractions': extractions, 'labels': labels, 'eligible': sorted(qa.dev_job_ids())}


def benchmark():
    pairs = qa.fixed_input_pairs()
    split = qa.split_fixed_input(pairs)
    path = qa.QA_DIR / 'benchmark_v1/split.json'
    record = {'benchmark': 'QA-DEV-FI-v1',
              'source': 'evals/gold/development_v13_reviewed_20261004_gap_r4 (gap_v2 A units as input, B labels as answer)',
              'labeling_mode': 'model_draft_assisted_human_accepted (D-085)', 'seed': qa.SPLIT_SEED,
              'rule': 'split by job, greedy unit balance per CV after a seeded shuffle',
              'subsets': split,
              'units': {k: sum(len(pairs[tuple(p)]['labels']) for p in v) for k, v in split.items()},
              'gold_sha256': {n: qa.digest(qa.DEV_GOLD / n) for n in
                              ('extraction_gold_gap_v2.jsonl', 'evidence_gold_gap_v2.jsonl', 'held_gap_v2.json')}}
    if path.exists():
        if read(path)['subsets'] != split:
            raise SystemExit('benchmark split changed; make benchmark_v2 instead')
    else:
        qa.write_once(path, record)
    prov = qa.QA_DIR / 'benchmark_v1/provenance.json'
    if not prov.exists():
        qa.write_once(prov, qa.reference_provenance())
    return pairs, split, path


def scores_for(records: dict, inputs: dict) -> dict:
    from jobfit.eval.product_order import held_score
    from jobfit.schemas.analysis import UnitAssessment
    from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
    out = {}
    for key, ext in inputs['extractions'].items():
        rec = records.get(key)
        if ext is None:
            out[key] = held_score('held_extraction')
        elif rec is None or rec['status'] != 'done':
            out[key] = held_score((rec or {}).get('error_code') or 'not_run')
        else:
            out[key] = score_with_hold_policy(ext, [UnitAssessment.model_validate(a) for a in rec['assessments']],
                                              policy='H2v2', partial_weight=0.5)[0]
    return out


def constraints_for(inputs: dict) -> dict:
    from jobfit.matching.experience_rule import experience_conflicts
    return {key: (experience_conflicts(ext, inputs['cvs'][key[0]], history_confirmed=True) if ext else [])
            for key, ext in inputs['extractions'].items()}


def ranking_block(records: dict, inputs: dict) -> dict:
    scores = scores_for(records, inputs)
    r = qa.ranking_quality(inputs['top'], scores, inputs['labels'], inputs['eligible'], constraints_for(inputs))
    r['scores'] = {f'{k[0]}/{k[1]}': {'status': v.status.value, 'score_pct': v.score_pct} for k, v in scores.items()}
    return r


# ---------------------------------------------------------------- failure analysis (offline)

def failure_taxonomy(saved: dict, inputs: dict, ranking: dict, grounding: dict) -> dict:
    """Counts from saved development artifacts. Category rules are mechanical; notes are analyst readings."""
    from collections import Counter
    from scripts.evaluate_cp23_model_sweep import BUNDLE, SQL_KEY, pair_file, predictions
    from scripts.run_cp23_model_sweep import stages
    from scripts.run_cp23_stage2_matching import inputs as r3_inputs
    from scripts.run_cp23_luna_matching import matchable
    from jobfit.eval.matching_evaluation import reference_rows
    from jobfit.scoring.hold_policy_v11 import score_with_hold_policy
    from jobfit.schemas.analysis import UnitAssessment
    unit_errors, cats = [], Counter()
    for s in stages():
        qa.check_pairs([(s['cv_id'], s['job_id'])])
        cv, ex = r3_inputs(s)
        ref = reference_rows(BUNDLE, s, cv, ex)
        row = json.loads(pair_file(MODEL, s).read_text())
        _, guarded = predictions(s, cv, ex, row['assessments'])
        units = {u.unit_id: u for u in ex.units}
        for uid, gold in ref.items():
            key = f"{s['cv_id']}/{s['job_id']}/{uid}"
            gold = 'MATCH' if key == SQL_KEY else gold
            got = guarded[key]['label']
            if got == gold:
                continue
            soft = units[uid].field.value == 'soft_skill'
            if got is None:
                cat = 'not_assessed'
            elif qa.ORDER[got] > qa.ORDER[gold]:
                cat = 'soft_skill_inference_overclaim' if soft else 'adjacent_evidence_overclaim'
            else:
                cat = ('overly_conservative_soft_skill' if soft else
                       'partial_match_calibration_underclaim' if (got, gold) == ('PARTIAL', 'MATCH') else 'missing_evidence_underclaim')
            cats[cat] += 1
            unit_errors.append({'unit': key, 'field': units[uid].field.value, 'importance': units[uid].importance.value,
                                'gold': gold, 'sol': got, 'category': cat, 'text': units[uid].text})
    sweep = read(SWEEP)['models'][MODEL]
    proc, item_status, responsibility = Counter(), Counter(), set()
    redo = set(read(V11 / 'plan_v1.json')['redo_jds'])
    for (cv, job), rec in saved.items():
        ext = matchable(job, redo)
        if ext is None or rec['status'] == 'held_extraction':
            proc['hold_caused_by_missing_extraction'] += 1
            continue
        if rec['status'] != 'done':
            proc['matching_failure'] += 1
            continue
        units = {u.unit_id: u for u in ext.units}
        score = score_with_hold_policy(ext, [UnitAssessment.model_validate(a) for a in rec['assessments']],
                                       policy='H2v2', partial_weight=0.5)[0]
        proc[f'score_{score.status.value}'] += 1
        for a in rec['assessments']:
            u = units[a['unit_id']]
            for item in (a.get('branches') or [a]):
                st = item['check_status']
                if st == 'done':
                    continue
                if u.needs_review:
                    item_status['extraction_needs_review_unit_failed'] += 1
                elif u.field.value == 'experience_duration' or u.min_years is not None:
                    item_status['duration_needs_clarification_no_verified_years'] += 1
                elif u.field.value in ('location', 'work_authorization'):
                    item_status['location_needs_clarification'] += 1
                else:
                    item_status[f'other_{st}'] += 1
        responsibility |= {f'{job}/{u.unit_id}: {u.text}' for u in ext.units
                           if u.text.lower().startswith(('responsible for', 'you will', 'bertanggung jawab'))}
    discord = []
    for cv in qa.DEV_CVS:
        for pos, job in enumerate(ranking['per_cv'][cv]['order'], 1):
            rel = inputs['labels'][cv].get(job)
            sc = ranking['scores'][f'{cv}/{job}']
            kind = None
            if sc['status'] not in ('final', 'provisional'):
                kind = 'relevant_job_held_or_unscored' if (rel or 0) >= 2 else None
            elif pos <= 5 and rel is not None and rel <= 1:
                kind = 'low_relevance_in_top5'
            elif pos > 5 and rel is not None and rel >= 2:
                kind = 'relevant_job_below_top5'
            if kind:
                discord.append({'cv_id': cv, 'job_id': job, 'position': pos, 'relevance': rel,
                                'score_status': sc['status'], 'score_pct': sc['score_pct'], 'category': kind,
                                'analyst_note': ANALYST_NOTES.get(f'{cv}/{job}')})
    return {
        'schema_version': 'qa-failure-taxonomy-v1', 'split': 'development', 'api_calls': 0,
        'A_unit_errors_r3_anchor': {'source': 'saved GPT-6 Sol outputs (model sweep v1), 73 reviewed units in 4 pairs',
                                    'errors': len(unit_errors), 'units': 73, 'by_category': dict(cats),
                                    'run_to_run_label_agreement': sweep['run_to_run_label_agreement'],
                                    'examples': unit_errors},
        'B_process_saved_pipeline_pairs': {'source': 'saved GPT-6 Sol coverage run, 60 CV1/CV2 pairs (D-079 stage 2)',
                                           'pair_outcomes': dict(proc), 'non_done_items': dict(item_status),
                                           'responsibility_as_qualification_units': sorted(responsibility),
                                           'schema_or_repair_failures': 0,
                                           'invalid_quotes': grounding['invalid_quote_items'],
                                           'positive_items_checked': grounding['positive_items']},
        'C_ranking_discordance_top10': discord,
        'not_observed_or_not_measurable': {
            'and_or_mistake': 'not observed in the 11 anchor errors',
            'education_mismatch': 'not observed in the 11 anchor errors',
            'wrong_cv_section': 'not measurable: the matcher output has no section field',
            'schema_formatting_failure': '0 of 53 saved calls failed or needed a repair'},
        'reading': ('Unit errors are mostly MATCH/PARTIAL calibration in both directions plus soft skills. '
                    'Ranking errors are mostly holds (missing extraction, needs_review units, durations without '
                    'verified years) and job-level fit that a coverage score cannot see (role family, required '
                    'years excluded under H2v2). A matching-prompt change can only address the first group.'),
    }


# ---------------------------------------------------------------- baseline (offline)

def saved_baseline_records() -> dict:
    out = {}
    for path in qa.dev_path(SOL_SAVED).glob('*__*.json'):
        row = json.loads(path.read_text())
        if row.get('model') == MODEL:
            out[(row['cv_id'], row['job_id'])] = row
    qa.check_pairs(out)
    return out


def baseline_config(cfg, inputs, pairs, split, split_path) -> dict:
    return {
        'experiment_id': 'QA-E00-BASELINE', 'created_at': now(), 'kind': 'offline reproduction of saved development artifacts',
        'pipeline_version': cfg['pipeline_version'], 'config_file': str(CONFIG.relative_to(ROOT)), 'config_sha256': qa.digest(CONFIG),
        'freeze': 'D-087 (cp23_freeze_draft_v2)', 'model': MODEL, 'fallback_model_in_product': cfg['matching_fallback_model'],
        'phase_a_fallback': 'not used (Sol only, so the prompt is the only variable)',
        **qa.prompt_record(ROOT / BASE_PROMPT), 'prompt_version': cfg['evidence_prompt_version'],
        'guideline': cfg['guideline_file'], 'guideline_sha256': qa.digest(ROOT / cfg['guideline_file']),
        'schema': cfg['schema_version'], 'output_schema': 'EvidenceResponse (jobfit.matching.evidence_matcher)',
        'validator': cfg['evidence_validator'], 'guardrails': cfg['evidence_guardrails'],
        'retrieval': cfg['stage1_method'], 'embedding_model': cfg['embedding_model'], 'k': cfg['stage1_k'],
        'partial_weight': cfg['partial_weight'], 'seniority_rule': cfg['stage1_seniority_rule'],
        'experience_rule': cfg['experience_conflict_rule'], 'hold_policy': cfg['hold_policy'],
        'extraction': f"{cfg['extraction_model']} saved development extractions (pipeline v1.1)",
        'datasets': {
            'ranking': {'name': 'QA-DEV-RANK-v1', 'cvs': list(qa.DEV_CVS),
                        'pairs': sum(len(v) for v in inputs['top'].values()),
                        'matchable_pairs': sum(e is not None for e in inputs['extractions'].values()),
                        'labels': 'gold r4 relevance (CV1-CV2)', 'labels_sha256': qa.digest(qa.DEV_GOLD / 'relevance_gold.jsonl')},
            'fixed_input': {'name': 'QA-DEV-FI-v1', 'split_file': str(split_path.relative_to(ROOT)),
                            'split_sha256': qa.digest(split_path), 'pairs': {k: len(v) for k, v in split.items()},
                            'units': {k: sum(len(pairs[tuple(p)]['labels']) for p in v) for k, v in split.items()}},
            'anchor': {'name': 'r3 fixed-input anchor', 'pairs': 4, 'units': 73, 'source': str(SWEEP.relative_to(ROOT))}},
        'cv_count': 2, 'versions': versions()}


def cmd_baseline(_args) -> None:
    out = qa.QA_DIR / 'QA-E00-BASELINE'
    if out.exists():
        raise SystemExit(f'{out.relative_to(ROOT)} exists; baseline artifacts are written once')
    import yaml
    inputs = dev_inputs()
    saved = saved_baseline_records()
    ranking = ranking_block(saved, inputs)
    grounding = qa.quote_validity(saved, {cv: p.profile.raw_text for cv, p in inputs['cvs'].items()})
    cfg = yaml.safe_load(CONFIG.read_text())
    pairs, split, split_path = benchmark()
    sweep = read(SWEEP)['models'][MODEL]
    walls = sorted(r['wall_ms'] for r in saved.values() if r['status'] == 'done')
    summary = read(SOL_SAVED / 'summary_v1.json')
    called = [r for r in saved.values() if r['status'] != 'held_extraction']
    config = baseline_config(cfg, inputs, pairs, split, split_path)
    metrics = {
        'experiment_id': 'QA-E00-BASELINE',
        'ranking': {k: ranking[k] for k in ('macro_p_at_5', 'macro_ndcg_at_10', 'hold_rate', 'held_or_unscored', 'analyzed', 'per_cv', 'scores')},
        'grounding': grounding,
        'reliability': {'pairs': len(saved), 'called': len(called), 'done': len(walls),
                        'schema_failure_count': len(called) - len(walls), 'repair_count': 0,
                        'repair_source': 'usage ledger: 53 evidence_matching calls, no validation repair call', 'fallback_count': 0},
        'anchor_fixed_input_r3': {'macro_f1': sweep['macro_f1_all_cases_guarded'], 'per_class_f1': sweep['per_class_f1'],
                                  'error_profile': sweep['error_profile'],
                                  'run_to_run_label_agreement': sweep['run_to_run_label_agreement']},
        'fixed_input_gap_v2': {'status': 'not_available_offline',
                               'reason': 'no saved Sol outputs on gold gap_v2 units; measured by QA-E00-FI-R1/R2 (paid, Wave 1)'}}
    cost = {'source_run_id': summary['run_id'], 'run_cost_usd': summary['run_cost_usd'],
            'cost_per_called_pair': summary['run_cost_usd'] / len(walls), 'median_latency_ms': statistics.median(walls),
            'p95_latency_ms': walls[max(0, round(.95 * len(walls)) - 1)], 'note': 'historical cost of the saved run; no new call'}
    failures = failure_taxonomy(saved, inputs, ranking, grounding)
    for name, obj in (('config.json', config), ('metrics.json', metrics), ('failures.json', failures), ('cost.json', cost)):
        qa.write_once(out / name, obj)
    inputs_sha = {str(p.relative_to(ROOT)): qa.digest(p) for p in
                  [CONFIG, ROOT / BASE_PROMPT, SWEEP, SOL_SAVED / 'summary_v1.json', OLD / 'plan.json',
                   qa.DEV_GOLD / 'relevance_gold.jsonl', split_path, Path(__file__), Path(qa.__file__)]}
    qa.write_once(out / 'receipt.json', {'experiment_id': 'QA-E00-BASELINE', 'api_calls': 0, 'created_at': now(),
                                         'inputs_sha256': inputs_sha,
                                         'outputs_sha256': {p.name: qa.digest(p) for p in sorted(out.iterdir())}})
    register_wave1(cfg, config, metrics, cost, split, split_path)
    print(json.dumps({'ranking': {k: metrics['ranking'][k] for k in ('macro_p_at_5', 'macro_ndcg_at_10', 'hold_rate')},
                      'grounding': grounding, 'anchor_macro_f1': metrics['anchor_fixed_input_r3']['macro_f1'],
                      'failure_categories': failures['A_unit_errors_r3_anchor']['by_category'],
                      'process': failures['B_process_saved_pipeline_pairs']['non_done_items']}, indent=1))


def register_wave1(cfg, config, metrics, cost, split, split_path) -> None:
    rows = {r['experiment_id'] for r in qa.load_registry()}
    r, a = metrics['ranking'], metrics['anchor_fixed_input_r3']
    if 'QA-E00-BASELINE' not in rows:
        qa.upsert({'experiment_id': 'QA-E00-BASELINE', 'date': now()[:10], 'status': 'baseline', 'hypothesis_id': 'QA-E00',
                   'parent_experiment': 'D-087 freeze', 'model': MODEL, 'prompt_file': BASE_PROMPT,
                   'prompt_version': cfg['evidence_prompt_version'], 'prompt_sha256': config['prompt_sha256'],
                   'dataset': 'QA-DEV-RANK-v1 (20 pairs) + r3 anchor (73 units)',
                   'dataset_sha256': qa.digest(qa.DEV_GOLD / 'relevance_gold.jsonl'), 'sample_count': r['analyzed'],
                   'p_at_5': r['macro_p_at_5'], 'ndcg_at_10': r['macro_ndcg_at_10'], 'macro_f1': a['macro_f1'],
                   'quote_validity': metrics['grounding']['quote_validity'],
                   'hallucination_count': metrics['grounding']['invalid_quote_items'],
                   'unsupported_positive_count': a['error_profile']['positive_claim_on_gold_no_match'],
                   'schema_failure_count': metrics['reliability']['schema_failure_count'], 'repair_count': 0,
                   'hold_rate': round(r['hold_rate'], 4), 'fallback_count': 0,
                   'run_to_run_agreement': a['run_to_run_label_agreement']['rate'],
                   'total_cost_usd': cost['run_cost_usd'], 'cost_per_pair': round(cost['cost_per_called_pair'], 6),
                   'median_latency': cost['median_latency_ms'], 'p95_latency': cost['p95_latency_ms'],
                   'decision': 'baseline', 'decision_reason': 'Frozen D-087 configuration on saved development artifacts.'}, new=True)
    for exp, spec in EXPERIMENTS.items():
        if exp in rows:
            continue
        pr = qa.prompt_record(ROOT / spec['prompt'])
        qa.upsert({'experiment_id': exp, 'date': now()[:10], 'status': 'planned', 'hypothesis_id': spec['hypothesis'],
                   'parent_experiment': spec['parent'], 'model': MODEL, 'prompt_file': spec['prompt'],
                   'prompt_version': pr.get('prompt_version', cfg['evidence_prompt_version']), 'prompt_sha256': pr['prompt_sha256'],
                   'dataset': 'QA-DEV-FI-v1 optimization' + (' + QA-DEV-RANK-v1' if spec['ranking'] else ''),
                   'dataset_sha256': qa.digest(split_path),
                   'sample_count': len(split['optimization']) + (19 if spec['ranking'] else 0),
                   'decision': 'pending', 'decision_reason': spec['purpose']}, new=True)


# ---------------------------------------------------------------- plan, dry run, run

def plan(exp: str, stage: str | None = None) -> dict:
    """Amendment 2 (staged execution): a staged challenger runs Stage A (fixed-input pairs only) and,
    only if the Stage A check says so, Stage B (ranking pairs only)."""
    if exp not in EXPERIMENTS:
        raise SystemExit(f'unknown experiment {exp}; add it to EXPERIMENTS with a new ID')
    spec = dict(EXPERIMENTS[exp])
    if spec.get('staged'):
        stage = stage or 'A'
        if stage not in ('A', 'B'):
            raise SystemExit('stage must be A or B')
    elif stage:
        raise SystemExit(f'{exp} is not a staged experiment')
    if 'confirmation' in spec['subsets'] and not qa.confirmation_unsealed():
        raise SystemExit('the confirmation subset is sealed until exactly one finalist is recorded (D-089)')
    pairs, split, split_path = benchmark()
    fixed = [tuple(p) for s in spec['subsets'] for p in split[s]]
    inputs = dev_inputs()
    rank = sorted(k for k, ext in inputs['extractions'].items() if ext is not None) if spec['ranking'] else []
    run_id = WAVE1_PREFIX + exp.lower()
    if stage == 'A':
        rank, spec['ranking'] = [], False
    elif stage == 'B':
        fixed, run_id = [], run_id + '_ranking'
    qa.check_pairs(fixed + rank)
    return {'experiment_id': exp, **spec, 'stage': stage, 'prompt_record': qa.prompt_record(ROOT / spec['prompt']),
            'fixed_input_pairs': [list(p) for p in fixed], 'ranking_pairs': [list(p) for p in rank],
            'calls': len(fixed) + len(rank), 'split_sha256': qa.digest(split_path), 'run_id': run_id}


def ledger():
    from jobfit.config import get_settings
    from jobfit.llm.ledger import UsageLedger
    settings = get_settings()
    return settings, UsageLedger(settings.usage_ledger)


def estimate(p: dict) -> dict:
    settings, led = ledger()
    records = led.records()
    recs = [r for r in records if r.model == 'openai/gpt-6-sol' and r.task == 'evidence_matching' and r.ok]
    costs = sorted(r.cost_usd for r in recs)
    base_in = statistics.median(r.input_tokens for r in recs)
    extra = (len((ROOT / p['prompt']).read_text()) - len((ROOT / BASE_PROMPT).read_text())) / 4
    factor = (base_in + max(0.0, extra)) / base_in
    median, p90 = statistics.median(costs), costs[int(.9 * (len(costs) - 1))]
    spent_w1 = sum(r.cost_usd for r in records if r.run_id.startswith(WAVE1_PREFIX))
    return {'observed_sol_calls': len(costs), 'median_cost_per_call': round(median, 6), 'p90_cost_per_call': round(p90, 6),
            'prompt_input_factor': round(factor, 4), 'estimate_usd': round(p['calls'] * median * factor, 4),
            'upper_estimate_usd': round(p['calls'] * p90 * factor, 4), 'wave1_cap_usd': WAVE1_CAP_USD,
            'wave1_spent_usd': round(spent_w1, 6), 'ledger_total_usd': round(led.total_spent(), 6),
            'project_hard_stop_usd': settings.api_hard_stop_usd}


def cmd_dry_run(args) -> None:
    p = plan(args.exp, getattr(args, 'stage', None))
    e = estimate(p)
    folder = qa.QA_DIR / args.exp
    n = 1
    while (folder / f'dry_run_v{n}.json').exists():
        n += 1
    qa.write_once(folder / f'dry_run_v{n}.json', {'created_at': now(), 'plan': p, 'estimate': e, 'api_calls': 0})
    row = next((r for r in qa.load_registry() if r['experiment_id'] == args.exp), None)
    if row and row['status'] == 'planned':
        qa.upsert({'experiment_id': args.exp, 'status': 'dry_run'}, new=False)
    print(json.dumps({'experiment_id': args.exp, 'hypothesis': p['hypothesis'], 'prompt': p['prompt'],
                      'fixed_input_pairs': len(p['fixed_input_pairs']), 'ranking_pairs': len(p['ranking_pairs']),
                      'calls': p['calls'], **e}, indent=1))


@contextmanager
def prompt_override(prompt: Path, expected_sha: str):
    """Point the frozen matcher at a challenger prompt for this process only (no frozen file is edited)."""
    from jobfit.matching import evidence_matcher as em
    if qa.digest(prompt) != expected_sha:
        raise SystemExit('prompt changed since the plan')
    old = em.EVIDENCE_PROMPT_FILE
    em.EVIDENCE_PROMPT_FILE = prompt
    try:
        yield
    finally:
        em.EVIDENCE_PROMPT_FILE = old
        if qa.digest(prompt) != expected_sha:
            raise RuntimeError('prompt changed during the run')


def check_run_budget(e: dict) -> None:
    if e['wave1_spent_usd'] + e['upper_estimate_usd'] > WAVE1_CAP_USD + 1e-9:
        raise SystemExit('Upper estimate would pass the Wave 1 cap')
    if e['ledger_total_usd'] + e['upper_estimate_usd'] > e['project_hard_stop_usd'] + 1e-9:
        raise SystemExit('Project hard stop has insufficient headroom')


def check_stage(exp: str) -> None:
    """Wave 1 is staged (Dion, 7 Oct 2026): each run needs Dion's approval and the previous run evaluated."""
    spec = EXPERIMENTS[exp]
    if not spec['approved']:
        raise SystemExit(f'{exp} is not approved yet (conditional on the Wave 1 comparison)')
    missing = [x for x in spec['requires_evaluated'] if not (qa.QA_DIR / x / 'metrics.json').exists()]
    if missing:
        raise SystemExit(f'{exp} runs after {missing} is run and evaluated')
    if spec.get('requires_finalist'):
        finalists = [r['experiment_id'] for r in qa.load_registry() if r['status'] == 'finalist']
        if finalists != [spec['requires_finalist']]:
            raise SystemExit(f"{exp} runs only when {spec['requires_finalist']} is the single provisional finalist")


def stage_a_decision(exp: str) -> str | None:
    path = qa.QA_DIR / f'analysis/stage_a_check_{exp}_v1.json'
    return json.loads(path.read_text())['decision'] if path.exists() else None


def cmd_run(args) -> None:
    stage = getattr(args, 'stage', None)
    p = plan(args.exp, stage)
    e = estimate(p)
    out = qa.QA_DIR / args.exp
    plan_name, summary_name = ('plan_ranking.json', 'run_summary_ranking.json') if p['stage'] == 'B' else ('plan.json', 'run_summary.json')
    print(json.dumps({'experiment_id': args.exp, 'calls': p['calls'], **e}, indent=1))
    if not args.execute:
        print('No call made. Add --execute after Dion approves this experiment.')
        return
    check_stage(args.exp)
    if p['stage'] == 'B' and stage_a_decision(args.exp) != 'continue_to_ranking':
        raise SystemExit(f'Stage B needs a Stage A check that says continue_to_ranking (stage-a-check --exp {args.exp})')
    check_run_budget(e)
    check_key_limit(key_numeric_status(), e['upper_estimate_usd'])
    if (out / plan_name).exists():
        raise SystemExit('This experiment (stage) already ran; use a new experiment ID')
    from jobfit.llm.runtime import build_runtime_client
    from jobfit.matching.evidence_matcher import match_evidence
    from scripts.probe_openrouter_access import require_access
    from scripts.run_cp23_luna_matching import CappedClient
    settings, _ = ledger()
    if settings.api_budget_usd != 19 or settings.api_hard_stop_usd != 18.5:
        raise SystemExit('Project guard values changed; ask Dion')
    require_access([MODEL])
    base = build_runtime_client(settings, CONFIG, run_id=p['run_id'])
    w1_before = sum(r.cost_usd for r in base.ledger.records() if r.run_id.startswith(WAVE1_PREFIX))
    client = CappedClient(base, base.ledger.total_spent() - w1_before, cap=WAVE1_CAP_USD)
    qa.write_once(out / plan_name, {'created_at': now(), 'plan': p, 'estimate': e})
    inputs = dev_inputs()
    pairs = qa.fixed_input_pairs()
    jobs = [('fixed_input', tuple(k), pairs[tuple(k)]['extraction']) for k in p['fixed_input_pairs']]
    jobs += [('ranking', tuple(k), inputs['extractions'][tuple(k)]) for k in p['ranking_pairs']]

    def one(kind, key, ext):
        start = time.perf_counter()
        try:
            res = match_evidence(inputs['cvs'][key[0]], ext, client=client, model=MODEL, validator_version='quote-check-v1.1',
                                 guardrail_ids=('G1', 'G2'), dynamic_output=True)
            rec = {'status': res.status, 'error_code': res.error_code, 'attempts': res.attempts,
                   'assessments': [a.model_dump(mode='json') for a in res.assessments], 'source_flags': res.source_flags}
        except Exception as exc:  # recorded, never retried here
            rec = {'status': 'failed', 'error_code': type(exc).__name__, 'attempts': None, 'assessments': [], 'source_flags': []}
        rec = {'set': kind, 'cv_id': key[0], 'job_id': key[1], 'model': MODEL, 'experiment_id': args.exp,
               'wall_ms': round((time.perf_counter() - start) * 1000), **rec}
        qa.write_once(out / 'runs' / f'{kind}__{key[0]}_{key[1]}.json', rec)
        return rec

    stop = None
    with prompt_override(ROOT / p['prompt'], p['prompt_record']['prompt_sha256']), base.ledger.exclusive():
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for f in as_completed([pool.submit(one, *j) for j in jobs]):
                rec = f.result()
                print(json.dumps({k: rec[k] for k in ('set', 'cv_id', 'job_id', 'status', 'error_code', 'wall_ms')}), flush=True)
                if rec['error_code'] in ('RunCapReached', 'BudgetExceeded', 'AuthenticationError', 'PermissionDeniedError'):
                    stop = rec['error_code']
    cost = sum(r.cost_usd for r in base.ledger.records() if r.run_id == p['run_id'])
    qa.write_once(out / summary_name, {'finished_at': now(), 'run_cost_usd': cost, 'stop': stop,
                                       'records': len(list((out / 'runs').glob('*.json')))})
    if p['stage'] != 'B':
        qa.upsert({'experiment_id': args.exp, 'status': 'completed', 'total_cost_usd': round(cost, 6)}, new=False)
    print(json.dumps({'run_cost_usd': round(cost, 4), 'stop': stop}))
    print(f"Next: python scripts/qa_phase_a.py {'evaluate-ranking' if p['stage'] == 'B' else 'evaluate'} --exp {args.exp}")


# ---------------------------------------------------------------- evaluate (offline)

def load_records(exp: str) -> dict:
    out = {}
    for path in (qa.QA_DIR / exp / 'runs').glob('*.json'):
        rec = json.loads(path.read_text())
        out[(rec['set'], rec['cv_id'], rec['job_id'])] = rec
    return out


def unit_failures(fixed: dict, pairs: dict) -> list[dict]:
    rows = []
    for (cv, job), rec in sorted(fixed.items()):
        if rec['status'] != 'done':
            continue
        pred = qa.unit_predictions(pairs[(cv, job)]['extraction'], rec['assessments'])
        for u, gold in pairs[(cv, job)]['labels'].items():
            got = pred[u]['label']
            if got != gold:
                rows.append({'unit': f'{cv}/{job}/{u}', 'field': pairs[(cv, job)]['fields'][u],
                             'importance': pairs[(cv, job)]['importance'][u], 'gold': gold, 'pred': got,
                             'status': pred[u]['status'],
                             'direction': 'unassessed' if got is None else ('over' if qa.ORDER[got] > qa.ORDER[gold] else 'under')})
    return rows


def cmd_evaluate(args) -> None:
    exp = args.exp
    folder = qa.QA_DIR / exp
    if (folder / 'metrics.json').exists():
        raise SystemExit('metrics already written for this experiment')
    p = read(folder / 'plan.json')['plan']
    recs = load_records(exp)
    pairs = qa.fixed_input_pairs()
    inputs = dev_inputs()
    fixed = {(c, j): r for (s, c, j), r in recs.items() if s == 'fixed_input'}
    rank = {(c, j): r for (s, c, j), r in recs.items() if s == 'ranking'}
    subset = [tuple(x) for x in p['fixed_input_pairs']]
    open_failures = {f'{s}/{c}/{j}': r['error_code'] for (s, c, j), r in recs.items()
                     if r['status'] != 'done' and qa.failure_class(r['error_code']) != 'prompt_induced'}
    missing = [f'{c}/{j}' for c, j in subset if (c, j) not in fixed] + \
              [f'{c}/{j}' for c, j in map(tuple, p['ranking_pairs']) if (c, j) not in rank]
    if (open_failures or missing) and not getattr(args, 'invalidate', False):
        raise SystemExit('Not a prompt result yet: transient/unclassified failures ' + json.dumps(open_failures) +
                         f' missing {missing}. Run `recover --exp {exp}` (one documented retry per pair), or '
                         f'`evaluate --exp {exp} --invalidate` to mark the run invalid (amendment 1).')
    if getattr(args, 'invalidate', False):
        qa.upsert({'experiment_id': exp, 'status': 'invalid', 'decision': 'invalid run',
                   'decision_reason': 'Operational failures after recovery: ' + json.dumps(open_failures)}, new=False)
        print('Marked invalid; repeat later under a new experiment ID.')
        return
    fi = qa.fixed_input_metrics(fixed, pairs, subset)
    m = {'experiment_id': exp, 'fixed_input_optimization': fi,
         'grounding': qa.quote_validity({**fixed, **rank}, {cv: x.profile.raw_text for cv, x in inputs['cvs'].items()})}
    partner = p.get('replicate_of')
    if partner and (qa.QA_DIR / partner / 'runs').exists():
        other = {(c, j): r for (s, c, j), r in load_records(partner).items() if s == 'fixed_input'}
        m['run_to_run_agreement'] = qa.run_to_run_agreement(fixed, other, pairs, subset)
    if p['ranking']:
        r = ranking_block(rank, inputs)
        m['ranking'] = {k: r[k] for k in ('macro_p_at_5', 'macro_ndcg_at_10', 'hold_rate', 'held_or_unscored', 'analyzed', 'per_cv', 'scores')}
    _, led = ledger()
    calls = [x for x in led.records() if x.run_id == p['run_id']]
    walls = sorted(r['wall_ms'] for r in recs.values() if r['status'] == 'done')
    total = sum(x.cost_usd for x in calls)
    cost = {'run_id': p['run_id'], 'calls': len(calls), 'repair_calls': sum('repair' in x.task for x in calls),
            'total_cost_usd': round(total, 6), 'cost_per_pair': round(total / max(1, len(recs)), 6),
            'median_latency_ms': statistics.median(walls) if walls else None,
            'p95_latency_ms': walls[max(0, round(.95 * len(walls)) - 1)] if walls else None}
    failures = {'experiment_id': exp, 'unit_errors': unit_failures(fixed, pairs),
                'failed_pairs': fi['failed_pairs'], 'error_codes': fi['error_codes']}
    qa.write_once(folder / 'config.json', {'experiment_id': exp, 'model': MODEL, 'prompt': p['prompt_record'],
                                           'subsets': p['subsets'], 'ranking': p['ranking'], 'config_file': str(CONFIG.relative_to(ROOT)),
                                           'validator': 'quote-check-v1.1', 'guardrails': ['G1', 'G2'], 'hold_policy': 'H2v2',
                                           'partial_weight': 0.5, 'k': 10, 'fallback': 'not used',
                                           'measurement_scope': ('primary GPT-6 Sol prompt behavior; not production fallback '
                                                                 'reliability (Sol then Luna), which a later integration run checks'),
                                           'reference_provenance': 'evals/results/quality_optimization/benchmark_v1/provenance.json',
                                           'versions': versions()})
    for name, obj in (('metrics.json', m), ('failures.json', failures), ('cost.json', cost)):
        qa.write_once(folder / name, obj)
    qa.write_once(folder / 'receipt.json', {
        'experiment_id': exp, 'evaluated_at': now(), 'api_calls_in_evaluation': 0,
        'prompt_sha256': p['prompt_record']['prompt_sha256'], 'split_sha256': p['split_sha256'],
        'code_sha256': {'scripts/qa_phase_a.py': qa.digest(Path(__file__)), 'src/jobfit/eval/qa_phase_a.py': qa.digest(Path(qa.__file__))},
        'run_records_sha256': {x.name: qa.digest(x) for x in sorted((folder / 'runs').glob('*.json'))},
        'outputs_sha256': {x.name: qa.digest(x) for x in sorted(folder.glob('*.json')) if x.name != 'receipt.json'}})
    row = {'experiment_id': exp, 'macro_f1': fi['macro_f1'], 'quote_validity': m['grounding']['quote_validity'],
           'hallucination_count': m['grounding']['invalid_quote_items'], 'unsupported_positive_count': fi['unsupported_positive'],
           'schema_failure_count': len(fi['failed_pairs']), 'repair_count': cost['repair_calls'], 'fallback_count': 0,
           'total_cost_usd': cost['total_cost_usd'], 'cost_per_pair': cost['cost_per_pair'],
           'median_latency': cost['median_latency_ms'], 'p95_latency': cost['p95_latency_ms']}
    if 'ranking' in m:
        row.update({'p_at_5': m['ranking']['macro_p_at_5'], 'ndcg_at_10': m['ranking']['macro_ndcg_at_10'],
                    'hold_rate': round(m['ranking']['hold_rate'], 4)})
    if 'run_to_run_agreement' in m:
        row['run_to_run_agreement'] = m['run_to_run_agreement']['rate']
    qa.upsert(row, new=False)
    print(json.dumps({k: fi[k] for k in ('macro_f1', 'accuracy_all_units', 'overclaim', 'underclaim', 'unsupported_positive',
                                         'unassessed_units', 'failed_pairs')}, indent=1))


def cmd_repeatability(args) -> None:
    """Offline unit-level comparison of two completed runs on the same optimization pairs."""
    pa = read(qa.QA_DIR / args.a / 'plan.json')['plan']
    pb = read(qa.QA_DIR / args.b / 'plan.json')['plan']
    if pa['fixed_input_pairs'] != pb['fixed_input_pairs'] or pa['prompt_record']['prompt_sha256'] != pb['prompt_record']['prompt_sha256']:
        raise SystemExit('repeatability needs the same pairs and the same prompt')
    pairs = qa.fixed_input_pairs()
    subset = [tuple(x) for x in pa['fixed_input_pairs']]
    ra = {(c, j): r for (s, c, j), r in load_records(args.a).items() if s == 'fixed_input'}
    rb = {(c, j): r for (s, c, j), r in load_records(args.b).items() if s == 'fixed_input'}
    res = {'compared': [args.a, args.b], 'subset': 'QA-DEV-FI-v1 optimization', 'api_calls': 0, 'created_at': now(),
           'prompt_sha256': pa['prompt_record']['prompt_sha256'], **qa.label_transitions(ra, rb, pairs, subset),
           'metric_gap': {k: abs(read(qa.QA_DIR / args.a / 'metrics.json')['fixed_input_optimization'][k] -
                                 read(qa.QA_DIR / args.b / 'metrics.json')['fixed_input_optimization'][k])
                          for k in ('macro_f1', 'accuracy_all_units', 'overclaim', 'underclaim', 'unsupported_positive')}}
    name = f"repeatability_{args.a}_vs_{args.b}_v1.json"
    path = qa.QA_DIR / 'analysis' / name
    qa.write_once(path, res)
    qa.write_once(path.with_suffix('.receipt.json'), {
        'output_sha256': qa.digest(path), 'inputs_sha256': {x.name: qa.digest(x) for e in (args.a, args.b)
                                                            for x in sorted((qa.QA_DIR / e / 'runs').glob('*.json'))},
        'code_sha256': {'scripts/qa_phase_a.py': qa.digest(Path(__file__)), 'src/jobfit/eval/qa_phase_a.py': qa.digest(Path(qa.__file__))}})
    print(json.dumps({k: res[k] for k in ('units', 'same', 'changed', 'agreement', 'transitions', 'changed_by_cv', 'which_run_matches_gold')}, indent=1))


def key_numeric_status() -> dict:
    """Read-only GET /key: numeric usage and limit fields only, never the key (no inference call)."""
    from jobfit.llm.client import OpenRouterClient
    from scripts.probe_openrouter_access import key_status
    settings, _ = ledger()
    return key_status(OpenRouterClient(settings, run_id='qa_phase_a_key_check'))


def check_key_limit(status: dict, upper: float) -> None:
    """Refuse a run the provider key cannot finish: a run cut off halfway would count failed pairs against the prompt."""
    if 'error' in status:
        raise SystemExit(f"Cannot read the key limit ({status['error']}); not starting a paid run")
    remaining = status.get('limit_remaining')
    if remaining is not None and remaining < upper:
        raise SystemExit(f'Key limit_remaining US${remaining:.4f} is below the upper estimate US${upper:.4f}; '
                         'raise the key limit or credits first. The experiment design stays the same.')


def cmd_key_status(args) -> None:
    s = key_numeric_status()
    out = {'key_numeric_status': s}
    if args.exp:
        p = plan(args.exp, args.stage)
        e = estimate(p)
        out.update({'experiment_id': args.exp, 'estimate_usd': e['estimate_usd'], 'upper_estimate_usd': e['upper_estimate_usd'],
                    'jobfit_ledger_usd': e['ledger_total_usd'], 'jobfit_hard_stop_usd': e['project_hard_stop_usd'],
                    'wave1_spent_usd': e['wave1_spent_usd'], 'wave1_cap_usd': e['wave1_cap_usd']})
        try:
            check_key_limit(s, e['upper_estimate_usd'])
            check_run_budget(e)
            out['can_start'] = True
        except SystemExit as exc:
            out['can_start'] = False
            out['reason'] = str(exc)
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------- amendment 1: rule, selection, repeat, recovery, budget

def cmd_lock_rule(_args) -> None:
    """Write selection_rule_v2.json once, from the two baseline runs, before any challenger result."""
    if any((qa.QA_DIR / e / 'metrics.json').exists() for e in ('QA-E01', 'QA-E02', 'QA-E03')):
        raise SystemExit('a challenger already has results; the rule can no longer be locked')
    runs = {e: read(qa.QA_DIR / e / 'metrics.json') for e in ('QA-E00-FI-R1', 'QA-E00-FI-R2')}
    rule = qa.build_rule(runs, read(qa.QA_DIR / 'QA-E00-BASELINE' / 'metrics.json')['ranking'])
    rule['locked_at'] = now()
    qa.write_once(qa.RULE_FILE, rule)
    print(json.dumps({'rule': str(qa.RULE_FILE.relative_to(ROOT)), 'sha256': qa.digest(qa.RULE_FILE),
                      'reference_macro_f1': rule['practical_improvement_reference_macro_f1'],
                      'path_B_limits': rule['path_B_limits'], 'hard_gates': rule['hard_gates']}, indent=1))


def merged_metrics(exp: str) -> dict:
    m = read(qa.QA_DIR / exp / 'metrics.json')
    rk = qa.QA_DIR / exp / 'ranking_metrics.json'
    if rk.exists():
        r = read(rk)
        m = {**m, 'ranking': r['ranking'],
             'grounding': {'positive_items': m['grounding']['positive_items'] + r['grounding']['positive_items'],
                           'invalid_quote_items': m['grounding']['invalid_quote_items'] + r['grounding']['invalid_quote_items'],
                           'quote_validity': None}}
        g = m['grounding']
        g['quote_validity'] = (g['positive_items'] - g['invalid_quote_items']) / g['positive_items'] if g['positive_items'] else None
    return m


def cards_for(exps, *, with_ranking=True) -> dict:
    rule = read(qa.RULE_FILE)
    base_f = [read(qa.QA_DIR / e / 'failures.json') for e in rule['baseline_runs']]
    out = {}
    for e in exps:
        m = merged_metrics(e)
        rank = with_ranking and 'ranking' in m
        card = qa.scorecard(m, rule, failures=read(qa.QA_DIR / e / 'failures.json'), baseline_failures=base_f, with_ranking=rank)
        if with_ranking and not rank:  # stopped at Stage A or ranking not run: cannot be a finalist
            card['gates']['ranking_evaluated'] = False
            card['gates_passed'] = False
            card['eligible'] = False
        out[e] = card
    return out


def cmd_scorecard(args) -> None:
    """Scorecard for one evaluated challenger against the locked rule (no call, no selection)."""
    card = cards_for([args.exp])[args.exp]
    path = qa.QA_DIR / f'analysis/scorecard_{args.exp}_v1.json'
    qa.write_once(path, {'created_at': now(), 'rule_sha256': qa.digest(qa.RULE_FILE), 'experiment_id': args.exp, **card})
    qa.upsert({'experiment_id': args.exp, 'decision': 'eligible' if card['eligible'] else 'not eligible (scorecard)',
               'decision_reason': json.dumps({'gates_passed': card['gates_passed'], 'path_A': card['path_A'],
                                              'path_B': card['path_B'], 'no_other_regression': card['no_other_regression']})}, new=False)
    print(json.dumps(card, indent=1))


def cmd_stage_a_check(args) -> None:
    """Amendment 2: after Stage A is evaluated, decide stop or continue_to_ranking from the locked rule. No call.
    Every path condition is unit-level, so ranking calls can never turn a Stage A failure into an eligible result."""
    exp = args.exp
    if not EXPERIMENTS[exp].get('staged'):
        raise SystemExit(f'{exp} is not staged')
    card = cards_for([exp], with_ranking=False)[exp]
    fi = read(qa.QA_DIR / exp / 'metrics.json')['fixed_input_optimization']
    rule = read(qa.RULE_FILE)
    reasons = []
    if not card['gates']['quote_validity_1']:
        reasons.append('quote validity below 1.0')
    if not card['gates']['unsupported_not_worse']:
        reasons.append('unsupported positives above the locked limit')
    if not card['gates']['prompt_failures_not_worse']:
        reasons.append('prompt/schema-induced failure')
    if not card['gates']['no_unrecovered_transient']:
        reasons.append('unrecovered operational failure (recover or invalidate first)')
    if not card['no_other_regression']:
        reasons.append('other regression (underclaims or unassessed units)')
    if not (card['path_A'] or card['path_B']):
        reasons.append('cannot meet path A or path B (both are unit-level and final after Stage A)')
    decision = 'continue_to_ranking' if not reasons else 'stop'
    rec = {'created_at': now(), 'experiment_id': exp, 'rule_sha256': qa.digest(qa.RULE_FILE), 'decision': decision,
           'reasons': reasons, 'card': card,
           'reference': {'macro_f1_reference': rule['practical_improvement_reference_macro_f1'], **rule['path_B_limits']},
           'values': {k: fi[k] for k in ('macro_f1', 'accuracy_all_units', 'unsupported_positive', 'overclaim', 'underclaim', 'unassessed_units')}}
    qa.write_once(qa.QA_DIR / f'analysis/stage_a_check_{exp}_v1.json', rec)
    qa.upsert({'experiment_id': exp, 'decision': 'stage A: ' + decision,
               'decision_reason': '; '.join(reasons) or 'gates pass and path A or B met on the fixed-input subset'}, new=False)
    print(json.dumps({k: rec[k] for k in ('experiment_id', 'decision', 'reasons', 'values')}, indent=1))


def cmd_evaluate_ranking(args) -> None:
    """Stage B evaluation: ranking metrics and grounding of the ranking calls only (fixed-input metrics stay as written)."""
    exp = args.exp
    folder = qa.QA_DIR / exp
    if (folder / 'ranking_metrics.json').exists():
        raise SystemExit('ranking metrics already written')
    p = read(folder / 'plan_ranking.json')['plan']
    recs = {(c, j): r for (s, c, j), r in load_records(exp).items() if s == 'ranking'}
    open_failures = {f'{c}/{j}': r['error_code'] for (c, j), r in recs.items()
                     if r['status'] != 'done' and qa.failure_class(r['error_code']) != 'prompt_induced'}
    missing = [f'{c}/{j}' for c, j in map(tuple, p['ranking_pairs']) if (c, j) not in recs]
    if open_failures or missing:
        raise SystemExit(f'operational failures {open_failures} missing {missing}: recover first (amendment 1)')
    inputs = dev_inputs()
    r = ranking_block(recs, inputs)
    _, led = ledger()
    calls = [x for x in led.records() if x.run_id == p['run_id']]
    walls = sorted(x['wall_ms'] for x in recs.values() if x['status'] == 'done')
    out = {'experiment_id': exp, 'stage': 'B',
           'ranking': {k: r[k] for k in ('macro_p_at_5', 'macro_ndcg_at_10', 'hold_rate', 'held_or_unscored', 'analyzed', 'per_cv', 'scores')},
           'grounding': qa.quote_validity(recs, {cv: x.profile.raw_text for cv, x in inputs['cvs'].items()}),
           'prompt_induced_failures': sum(1 for x in recs.values() if x['status'] != 'done'),
           'cost': {'run_id': p['run_id'], 'calls': len(calls), 'repair_calls': sum('repair' in x.task for x in calls),
                    'total_cost_usd': round(sum(x.cost_usd for x in calls), 6),
                    'median_latency_ms': statistics.median(walls) if walls else None}}
    qa.write_once(folder / 'ranking_metrics.json', out)
    qa.write_once(folder / 'receipt_ranking.json', {'experiment_id': exp, 'evaluated_at': now(), 'api_calls_in_evaluation': 0,
                                                    'ranking_metrics_sha256': qa.digest(folder / 'ranking_metrics.json'),
                                                    'run_records_sha256': {x.name: qa.digest(x) for x in sorted((folder / 'runs').glob('ranking__*.json'))}})
    row = next(x for x in qa.load_registry() if x['experiment_id'] == exp)
    qa.upsert({'experiment_id': exp, 'p_at_5': r['macro_p_at_5'], 'ndcg_at_10': r['macro_ndcg_at_10'], 'hold_rate': round(r['hold_rate'], 4),
               'total_cost_usd': round(float(row['total_cost_usd'] or 0) + out['cost']['total_cost_usd'], 6)}, new=False)
    print(json.dumps({k: out['ranking'][k] for k in ('macro_p_at_5', 'macro_ndcg_at_10', 'hold_rate')} | {'grounding': out['grounding']}, indent=1))


def cmd_select(_args) -> None:
    """Preregistered Wave 1 scorecard; records exactly one provisional finalist or keep-baseline. No call."""
    # Adaptive stopping (Dion, 7 Oct 2026): E01 and E02 must be evaluated; E03 runs only if Dion asks for it.
    started = [e for e in ('QA-E01', 'QA-E02', 'QA-E03') if (qa.QA_DIR / e / 'plan.json').exists()]
    missing = [e for e in started if not (qa.QA_DIR / e / 'metrics.json').exists()]
    missing += [e for e in started if EXPERIMENTS[e].get('staged') and stage_a_decision(e) is None]
    missing += [e for e in started if stage_a_decision(e) == 'continue_to_ranking' and not (qa.QA_DIR / e / 'ranking_metrics.json').exists()]
    if missing or not {'QA-E01', 'QA-E02'} <= set(started):
        raise SystemExit(f'evaluate {missing or ["QA-E01", "QA-E02"]} first')
    exps = started
    cards = cards_for(exps)
    finalist = qa.pick_finalist(cards)
    out = qa.QA_DIR / 'analysis/wave1_selection_v1.json'
    qa.write_once(out, {'created_at': now(), 'rule_sha256': qa.digest(qa.RULE_FILE), 'cards': cards,
                        'not_run_adaptive_stopping': [e for e in ('QA-E01', 'QA-E02', 'QA-E03') if e not in exps],
                        'provisional_finalist': finalist,
                        'decision': f'{finalist} is the provisional finalist; run {finalist}-R2 next' if finalist
                        else 'no eligible challenger: keep the baseline (prompt v1.1); confirmation stays sealed'})
    for e in exps:
        qa.upsert({'experiment_id': e, 'status': 'finalist' if e == finalist else 'rejected',
                   'decision': 'provisional finalist' if e == finalist else ('eligible, not chosen' if cards[e]['eligible'] else 'not eligible'),
                   'decision_reason': json.dumps({'gates': cards[e]['gates'], 'A': cards[e]['path_A'], 'B': cards[e]['path_B']})}, new=False)
    print(json.dumps({'provisional_finalist': finalist, 'cards': {e: {k: c[k] for k in ('eligible', 'path_A', 'path_B', 'gates_passed', 'values')}
                                                                    for e, c in cards.items()}}, indent=1))


def cmd_repeat_check(_args) -> None:
    """After <finalist>-R2 is evaluated: same gates (ranking not rerun) and still eligible -> unseal confirmation."""
    finalists = [r['experiment_id'] for r in qa.load_registry() if r['status'] == 'finalist']
    if len(finalists) != 1:
        raise SystemExit('needs exactly one provisional finalist')
    rep_id = f'{finalists[0]}-R2'
    card = cards_for([rep_id], with_ranking=False)[rep_id]
    passed = card['eligible']
    qa.write_once(qa.QA_DIR / f'analysis/repeat_check_{rep_id}_v1.json', {'created_at': now(), 'card': card, 'passed': passed})
    if passed:
        qa.write_once(qa.UNSEAL_FILE, {'finalist': finalists[0], 'repeat': rep_id, 'repeat_passed': True, 'created_at': now(),
                                       'rule_sha256': qa.digest(qa.RULE_FILE)})
    else:
        qa.upsert({'experiment_id': finalists[0], 'status': 'rejected', 'decision': 'failed its repeat',
                   'decision_reason': json.dumps(card['gates'])}, new=False)
    print(json.dumps({'repeat': rep_id, 'passed': passed, 'confirmation_unsealed': qa.confirmation_unsealed()}, indent=1))


def cmd_recover(args) -> None:
    """One documented retry per pair, only for transient provider/network/budget failures. Same prompt and settings.
    The failed record is moved (never edited or deleted) to failed_attempts/ with its sha256. Prompt-induced
    failures are never retried."""
    exp = args.exp
    folder = qa.QA_DIR / exp
    p = read(folder / 'plan.json')['plan']
    todo = []
    for path in sorted((folder / 'runs').glob('*.json')):
        rec = json.loads(path.read_text())
        if rec['status'] != 'done' and qa.failure_class(rec['error_code']) == 'transient_operational':
            if (folder / 'failed_attempts' / f'{path.stem}.attempt1.json').exists():
                raise SystemExit(f'{path.name} already used its one recovery; mark the run invalid instead')
            todo.append(path)
    print(json.dumps({'experiment_id': exp, 'transient_failures': [x.name for x in todo]}, indent=1))
    if not todo or not args.execute:
        return
    e = estimate({**p, 'calls': len(todo)})
    check_run_budget(e)
    check_key_limit(key_numeric_status(), e['upper_estimate_usd'])
    from jobfit.llm.runtime import build_runtime_client
    from jobfit.matching.evidence_matcher import match_evidence
    from scripts.run_cp23_luna_matching import CappedClient
    settings, _ = ledger()
    run_id = p['run_id'] + '_recovery1'
    base = build_runtime_client(settings, CONFIG, run_id=run_id)
    w1_before = sum(r.cost_usd for r in base.ledger.records() if r.run_id.startswith(WAVE1_PREFIX))
    client = CappedClient(base, base.ledger.total_spent() - w1_before, cap=WAVE1_CAP_USD)
    inputs, pairs = dev_inputs(), qa.fixed_input_pairs()
    (folder / 'failed_attempts').mkdir(exist_ok=True)
    with prompt_override(ROOT / p['prompt'], p['prompt_record']['prompt_sha256']), base.ledger.exclusive():
        for path in todo:
            old = json.loads(path.read_text())
            target = folder / 'failed_attempts' / f'{path.stem}.attempt1.json'
            sha = qa.digest(path)
            path.rename(target)
            qa.write_once(target.with_suffix('.receipt.json'), {'moved_from': f'runs/{path.name}', 'sha256': sha,
                                                                'error_code': old['error_code'], 'class': 'transient_operational',
                                                                'moved_at': now()})
            ext = pairs[(old['cv_id'], old['job_id'])]['extraction'] if old['set'] == 'fixed_input' else \
                inputs['extractions'][(old['cv_id'], old['job_id'])]
            start = time.perf_counter()
            try:
                res = match_evidence(inputs['cvs'][old['cv_id']], ext, client=client, model=MODEL, validator_version='quote-check-v1.1',
                                     guardrail_ids=('G1', 'G2'), dynamic_output=True)
                rec = {'status': res.status, 'error_code': res.error_code, 'attempts': res.attempts,
                       'assessments': [a.model_dump(mode='json') for a in res.assessments], 'source_flags': res.source_flags}
            except Exception as exc:
                rec = {'status': 'failed', 'error_code': type(exc).__name__, 'attempts': None, 'assessments': [], 'source_flags': []}
            rec = {'set': old['set'], 'cv_id': old['cv_id'], 'job_id': old['job_id'], 'model': MODEL, 'experiment_id': exp,
                   'recovery': 'attempt 2 after a transient failure (amendment 1)',
                   'wall_ms': round((time.perf_counter() - start) * 1000), **rec}
            qa.write_once(path, rec)
            print(json.dumps({k: rec[k] for k in ('set', 'cv_id', 'job_id', 'status', 'error_code')}), flush=True)


def budget_plan() -> dict:
    """Upper-bound money still needed for Phase A, and the provider key limit that covers it."""
    settings, led = ledger()
    rows = {r['experiment_id']: r for r in qa.load_registry()}
    remaining = {}
    for exp, spec in EXPERIMENTS.items():
        if spec.get('requires_finalist') or (qa.QA_DIR / exp / 'plan.json').exists():
            continue
        if rows.get(exp, {}).get('status') in ('withdrawn', 'invalid'):
            continue
        if spec.get('staged'):
            remaining[exp] = sum(estimate(plan(exp, st))['upper_estimate_usd'] for st in ('A', 'B'))
        else:
            remaining[exp] = estimate(plan(exp))['upper_estimate_usd']
    repeats = {e: estimate(plan(e))['upper_estimate_usd'] for e, s in EXPERIMENTS.items() if s.get('requires_finalist')}
    _, split, _ = benchmark()
    base_p = {'prompt': BASE_PROMPT, 'calls': len(split['confirmation'])}
    worst_prompt = max((s['prompt'] for s in EXPERIMENTS.values()), key=lambda x: len((ROOT / x).read_text()))
    conf = estimate(base_p)['upper_estimate_usd'] + estimate({'prompt': worst_prompt, 'calls': len(split['confirmation'])})['upper_estimate_usd']
    experiments = sum(remaining.values()) + max(repeats.values()) + conf
    buffer = round(0.10 * experiments + 0.05, 4)   # one recovery retry for ~10% of calls, plus access probes
    need = led.total_spent() + experiments + buffer
    recommended = min(settings.api_hard_stop_usd - 1.0, max(16.5, -(-need * 2 // 1) / 2))
    return {'current_spend_ledger_usd': round(led.total_spent(), 4),
            'remaining_upper_usd': {**{k: round(v, 4) for k, v in remaining.items()},
                                    'finalist_repeat_max': round(max(repeats.values()), 4),
                                    'confirmation_baseline_plus_finalist': round(conf, 4)},
            'remaining_upper_total_usd': round(experiments, 4), 'safety_buffer_usd': buffer,
            'needed_total_usd': round(need, 4), 'recommended_key_limit_usd': recommended,
            'covered': recommended >= need, 'project_hard_stop_usd': settings.api_hard_stop_usd,
            'margin_to_hard_stop_usd': round(settings.api_hard_stop_usd - recommended, 4),
            'note': 'Key limit = total usage allowed on the OpenRouter key. If the key usage differs from the JobFit ledger, '
                    'add the difference (key-status shows usage). No run starts unless limit_remaining covers its upper bound.'}


def cmd_budget_plan(_args) -> None:
    print(json.dumps(budget_plan(), indent=1))


def cmd_status(_args) -> None:
    for r in qa.load_registry():
        print(f"{r['experiment_id']:16s} {r['status']:9s} {r['hypothesis_id']:7s} P5={r['p_at_5'][:5] or '-':>5} "
              f"N10={r['ndcg_at_10'][:5] or '-':>5} F1={r['macro_f1'][:5] or '-':>5} cost={r['total_cost_usd'] or '-'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('baseline')
    for name in ('dry-run', 'run', 'evaluate'):
        s = sub.add_parser(name)
        s.add_argument('--exp', required=True)
        if name in ('run', 'dry-run'):
            s.add_argument('--stage', choices=['A', 'B'], help='staged challengers (amendment 2): A fixed-input, B ranking')
        if name == 'run':
            s.add_argument('--execute', action='store_true')
        if name == 'evaluate':
            s.add_argument('--invalidate', action='store_true', help='mark a run with unrecovered operational failures invalid')
    sub.add_parser('status')
    r = sub.add_parser('repeatability')
    r.add_argument('--a', required=True)
    r.add_argument('--b', required=True)
    k = sub.add_parser('key-status')
    k.add_argument('--exp')
    k.add_argument('--stage', choices=['A', 'B'])
    for name in ('stage-a-check', 'evaluate-ranking'):
        x = sub.add_parser(name)
        x.add_argument('--exp', required=True)
    sub.add_parser('lock-rule')
    sub.add_parser('select')
    sc = sub.add_parser('scorecard')
    sc.add_argument('--exp', required=True)
    sub.add_parser('repeat-check')
    sub.add_parser('budget-plan')
    rc = sub.add_parser('recover')
    rc.add_argument('--exp', required=True)
    rc.add_argument('--execute', action='store_true')
    args = ap.parse_args(argv)
    {'baseline': cmd_baseline, 'dry-run': cmd_dry_run, 'run': cmd_run, 'evaluate': cmd_evaluate,
     'status': cmd_status, 'repeatability': cmd_repeatability, 'key-status': cmd_key_status,
     'lock-rule': cmd_lock_rule, 'select': cmd_select, 'scorecard': cmd_scorecard, 'stage-a-check': cmd_stage_a_check,
     'evaluate-ranking': cmd_evaluate_ranking, 'repeat-check': cmd_repeat_check, 'recover': cmd_recover,
     'budget-plan': cmd_budget_plan}[args.cmd](args)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
