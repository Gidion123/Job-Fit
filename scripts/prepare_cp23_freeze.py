"""Draft the D-053 configuration/protocol freeze receipt. No model call, no DB.

Default is a dry run that prints the receipt summary and every blocker.
`--write` saves a new versioned DRAFT folder under evals/freeze/. The draft is not
an approval: Dion approves the freeze in docs/decisions.md, and only then the test
run may start. `--verify FOLDER` re-hashes every listed file and reports drift.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

import yaml

from jobfit.eval.heldout_report import CONTRACT_VERSION as HELDOUT_CONTRACT, PRIMARY as HELDOUT_PRIMARY, SUPPLEMENTARY as HELDOUT_SUPP
from jobfit.eval.test_pool import DEPTH, MINUTES_PER_LABEL, POOL_RULE
from jobfit.recommend.service import SERVICE_VERSION, RecommendConfig

CONFIG = 'config/versions/pipeline_cp23_freeze_candidate_v4_20261006.yaml'
FREEZE_DIR = ROOT / 'evals/freeze'
CVS = {'CV1': 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md',
       'CV2': 'data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md',
       'CV3': 'data/synthetic_cvs/cv_03_junior_ml_engineer_1yr_en.md',
       'CV4': 'data/synthetic_cvs/cv_04_data_analyst_to_ds_id.md',
       'CV5': 'data/synthetic_cvs/cv_05_ml_engineer_3yr_en.md'}
CODE = ['src/jobfit/recommend/service.py', 'src/jobfit/llm/runtime.py', 'src/jobfit/llm/client.py', 'src/jobfit/search/hybrid.py', 'src/jobfit/search/fts.py',
        'src/jobfit/search/dense.py', 'src/jobfit/search/keyword.py', 'src/jobfit/search/embeddings.py',
        'src/jobfit/search/seniority.py', 'src/jobfit/eval/retrieval_run.py',
        'src/jobfit/extraction/jd_extractor.py', 'src/jobfit/extraction/cache.py',
        'src/jobfit/matching/evidence_matcher.py', 'src/jobfit/matching/quote_check_v11.py',
        'src/jobfit/matching/guardrails.py', 'src/jobfit/scoring/hold_policy_v11.py',
        'src/jobfit/scoring/score.py', 'src/jobfit/scoring/ranking.py', 'src/jobfit/eval/product_order.py',
        'src/jobfit/eval/metrics.py', 'src/jobfit/eval/test_pool.py', 'src/jobfit/llm/output_policy.py',
        'src/jobfit/llm/structured.py', 'src/jobfit/schemas/requirements.py', 'src/jobfit/schemas/analysis.py',
        'src/jobfit/cv/parser.py', 'src/jobfit/matching/experience_rule.py',
        'src/jobfit/extraction/saved_records.py', 'src/jobfit/search/filters.py', 'src/jobfit/eval/d078.py',
        'src/jobfit/eval/heldout_report.py', 'scripts/evaluate_cp24_test.py', 'scripts/run_cp24_test.py',
        'scripts/build_cp23_test_workbook.py']
PROTOCOL = ['docs/evaluation.md', 'evals/annotation_guideline_v1_3.md',
            'evals/results/cp23_metric_contract_D052_D054_20261003_v1.json',
            'evals/splits/dev_job_ids.txt', 'evals/splits/test_job_ids.txt', 'evals/splits/split_manifest.json',
            'evals/gold/development_v13_reviewed_20261004_gap_r4/manifest.json',
            'evals/gold/development_v13_reviewed_20261004_gap_r4/relevance_gold.jsonl',
            'evals/results/cp23/post_labeling_development_v13_reviewed_20261004_gap_r4_v1/summary.json']
RUNTIME = ['config/versions/route_rules_cp23_v1.json', 'config/models_v1.yaml', 'config/retrieval_v1.yaml', 'config/tokenizers_v1.json',
           'config/pipeline_v1.yaml', 'config/skill_aliases_v0.yaml']
# Values D-078 still has to set from the complete development judgments (gold r4).
PENDING = {'stage1_k': 'D-078 rule on complete top-20/30 judgments after the r4 import',
           'partial_weight': 'D-078 rule on complete judgments after the r4 import'}


def digest(rel: str) -> str:
    return sha256((ROOT / rel).read_bytes()).hexdigest()


def blockers(cfg: dict) -> tuple[list[str], list[str]]:
    """Return (blockers, notes). Blockers must be cleared before approval."""
    provisional = str(cfg.get('freeze_status', '')).startswith('provisional')
    out = [f'{k} is provisional: {why}' for k, why in PENDING.items()] if provisional else []
    notes = []
    runtime = yaml.safe_load((ROOT / 'config/pipeline_v1.yaml').read_text())
    if runtime['evidence_prompt_file'] != cfg['evidence_prompt_file']:
        out.append('runtime evidence prompt differs from the frozen config')
    if runtime['guideline_file'] != cfg['guideline_file']:
        out.append('runtime guideline differs from the frozen config')
    if runtime['jd_prompt_file'] != cfg['jd_prompt_file']:
        notes.append(f"runtime config/pipeline_v1.yaml uses {runtime['jd_prompt_file']}; the test extraction "
                   f"script must pass ExtractionSpec({cfg['jd_prompt_file']}) explicitly (recorded, not a code change)")
    if not (ROOT / 'evals/gold/development_v13_reviewed_20261004_gap_r4').exists():
        out.append('development gold r4 (46 gap labels) not imported yet')
    return out, notes


def build(config: str = CONFIG) -> dict:
    cfg = yaml.safe_load((ROOT / config).read_text())
    RecommendConfig.from_yaml(ROOT / config)  # same validation as the service
    split = json.loads((ROOT / 'evals/splits/split_manifest.json').read_text())
    for name, value in split['output_hashes'].items():
        if digest('evals/splits/' + name) != value:
            raise ValueError(f'frozen split file changed: {name}')
    files = {rel: digest(rel) for rel in [config, cfg['jd_prompt_file'], cfg['evidence_prompt_file'],
                                          *PROTOCOL, *RUNTIME, *CODE, *CVS.values()]}
    return {
        'receipt': 'cp23-freeze-receipt', 'status': 'DRAFT_NOT_APPROVED', 'decision': 'D-053',
        'pipeline_version': cfg['pipeline_version'], 'service_version': SERVICE_VERSION,
        'config_file': config, 'config': cfg, 'pending_values': PENDING if str(cfg.get('freeze_status', '')).startswith('provisional') else {},
        'stage1_call': {'function': 'hybrid.rank', 'top_k': cfg['stage1_candidate_depth'],
                        'branch_depth': f"max(top_k, 20) = {max(cfg['stage1_candidate_depth'], 20)}",
                        'seniority_rule': cfg.get('stage1_seniority_rule'), 'analyzed_k': cfg['stage1_k'],
                        'rrf_k': cfg['rrf_k'], 'embedding_model': cfg['embedding_model'],
                        'eligible_jobs': 'evals/splits/test_job_ids.txt (214)'},
        'extraction_call': {'model': cfg['extraction_model'], 'prompt_file': cfg['jd_prompt_file'],
                            'scope': 'corpus_jd', 'dynamic_output': True,
                            'matchable_rule': 'status done, extraction present, jd_quality ok'},
        'matching_call': {'model': cfg['matching_model'], 'fallback': cfg['matching_fallback_model'],
                          'fallback_rule': 'processing failure only, once, model recorded per job',
                          'validator': cfg['evidence_validator'], 'guardrails': cfg['evidence_guardrails'],
                          'dynamic_output': True, 'timeout_s': cfg['request_timeout_seconds'],
                          'concurrency': cfg['matching_concurrency_limit']},
        'experience_block': {'rule': cfg.get('experience_conflict_rule'),
                             'history': 'synthetic test CVs have complete dated histories by design (T07): confirmed'},
        'test_pool': {'rule': POOL_RULE, 'depth': DEPTH, 'cvs': list(CVS),
                      'stage1_order': 'original stage-1 order before the seniority rule',
                      'final_order': 'product order of the analyzed top K (D-073)',
                      'effort_minutes_per_label': MINUTES_PER_LABEL, 'blind': True,
                      'hidden': ['rank', 'score', 'method', 'model suggestion', 'experience bucket'],
                      'reporting': 'CV1/CV2 familiar profiles and CV3-CV5 held-out profiles reported separately'},
        'report_contract': {'version': HELDOUT_CONTRACT, 'headline': 'CV3-CV5 only (held-out profiles and jobs)',
                            'primary_cvs': list(HELDOUT_PRIMARY), 'supplementary_cvs': list(HELDOUT_SUPP),
                            'supplementary_role': 'familiar-profile diagnostic, never in the headline',
                            'pooled_cv1_cv5_metric': 'not produced; rejected by check_contract',
                            'module': 'src/jobfit/eval/heldout_report.py'},
        'metrics': {'primary': ['P@5 original positions', 'NDCG@10 original positions'],
                    'contract': 'D-052 carried over; unjudged never zero; holds stay in the last block'},
        'no_tuning_rule': 'No model, prompt, K, weight or rule change after test exposure (D-046, D-053).',
        'files_sha256': files,
        'blockers': blockers(cfg)[0],
        'notes': blockers(cfg)[1],
        'approval': None,
    }


def next_folder() -> Path:
    n = 1
    while (FREEZE_DIR / f'cp23_freeze_draft_v{n}').exists():
        n += 1
    return FREEZE_DIR / f'cp23_freeze_draft_v{n}'


def verify(folder: Path) -> list[str]:
    saved = json.loads((folder / 'freeze_receipt.json').read_text())
    return [rel for rel, h in saved['files_sha256'].items()
            if not (ROOT / rel).exists() or digest(rel) != h]


def approve(folder: Path, decision: str | None) -> int:
    """Write an approved copy next to the draft. Refuses drift, blockers or a missing decision id."""
    if not decision or not decision.startswith('D-'):
        raise SystemExit('Approval needs the decision id that records it in docs/decisions.md')
    if decision not in (ROOT / 'docs/decisions.md').read_text():
        raise SystemExit(f'{decision} is not in docs/decisions.md yet')
    saved = json.loads((folder / 'freeze_receipt.json').read_text())
    drift = verify(folder)
    if drift or saved['blockers']:
        raise SystemExit(json.dumps({'changed_files': drift, 'blockers': saved['blockers']}, indent=1))
    target = folder / 'freeze_receipt_APPROVED.json'
    if target.exists():
        raise SystemExit('already approved')
    saved.update(status='APPROVED', approval={'decision': decision})
    target.write_text(json.dumps(saved, indent=1) + '\n')
    print('approved', target.relative_to(ROOT))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--config', default=CONFIG, help='version file, relative to the repo root')
    ap.add_argument('--verify', type=Path)
    ap.add_argument('--approve', type=Path, help='draft folder Dion approves; run by Dion only')
    ap.add_argument('--decision', help='decision id recording the approval, for example D-084')
    args = ap.parse_args(argv)
    if args.verify:
        drift = verify(args.verify)
        print(json.dumps({'folder': str(args.verify), 'changed_files': drift, 'ok': not drift}, indent=1))
        return 0 if not drift else 2
    if args.approve:
        return approve(args.approve, args.decision)
    receipt = build(args.config)
    print(json.dumps({'status': receipt['status'], 'files': len(receipt['files_sha256']),
                      'blockers': receipt['blockers'], 'notes': receipt['notes']}, indent=1))
    if args.write:
        folder = next_folder()
        folder.mkdir(parents=True)
        (folder / 'freeze_receipt.json').write_text(json.dumps(receipt, indent=1) + '\n')
        print('wrote', folder.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
