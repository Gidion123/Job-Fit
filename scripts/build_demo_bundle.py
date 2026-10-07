"""Build the D-022 saved demo bundle for synthetic CV1/CV2 (development jobs only). No model call.

It runs recommend() with the saved stage-1 top 30, the saved extractions and a
replay of the saved Sol answers (Luna v2 answers for the fallback), with the v3
configuration, for the seniority rule on and off. Before writing, every replayed
score is checked against a direct H2v2 rescoring of the same saved answers.
Writes a new versioned folder under evals/demo/.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

from jobfit.api.presenter import recommendation
from jobfit.api.wiring import CONFIG, CV_FILES, DEMO_HISTORY_CONFIRMED, PARSES, _extraction_record, _features
from jobfit.cv.parser import ParsedCV
from jobfit.llm.runtime import RULES_FILE
from jobfit.recommend.saved_demo import DEMO_VERSION, ReplayMatcher, demo_key
from jobfit.recommend.service import RecommendConfig, extraction_from_record, recommend
from jobfit.scoring.hold_policy_v11 import score_with_hold_policy

RANKINGS = PARSES / 'plan.json'
SOURCES = {'gpt-6-sol': ROOT / 'evals/results/cp23/matcher_coverage_gpt-6-sol_v1',
           'gpt-6-luna': ROOT / 'evals/results/cp23/luna_matching_v2'}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def records() -> dict:
    out = {}
    for model, folder in SOURCES.items():
        for path in folder.glob('*__*.json'):
            row = json.loads(path.read_text())
            if row.get('model') == model:
                out[(row['cv_id'], row['job_id'], model)] = row
    return out


def build() -> dict:
    config = RecommendConfig.from_yaml(CONFIG)
    rankings = json.loads(RANKINGS.read_text())['rankings']
    features = _features()
    buckets = {j: r.get('experience_bucket') for j, r in features.items()}
    meta = {j: {'title': r['title'], 'company': r['company'], 'location': r.get('location_raw'),
                'url': r.get('apply_url')} for j, r in features.items()}
    saved = records()
    entries, checks = {}, 0
    for cv_id, name in CV_FILES.items():
        cv = ParsedCV.model_validate(json.loads((PARSES / f'{cv_id}_parse.json').read_text())['parsed'])
        for seniority in (True, False):
            replay = ReplayMatcher(saved)
            rec = recommend(cv, retrieve=lambda d, r=rankings[cv_id]: r[:d], buckets=buckets,
                            extraction_for=lambda j: extraction_from_record(_extraction_record(j)),
                            client=None, config=config, seniority_enabled=seniority, matcher=replay,
                            history_confirmed=DEMO_HISTORY_CONFIRMED)
            for job, res in rec.jobs.items():
                row = saved.get((cv_id, job, res.matcher_model)) if res.matcher_model else None
                if row and res.extraction is not None:
                    direct = score_with_hold_policy(res.extraction, res.assessments, policy=config.hold_policy,
                                                    partial_weight=config.partial_weight)[0]
                    if direct.score_pct != res.score.score_pct or direct.status != res.score.status:
                        raise ValueError(f'Replay score differs for {cv_id}/{job}')
                    checks += 1
            key = demo_key(cv_id=cv_id, cv_sha256=digest(ROOT / 'data/synthetic_cvs' / name),
                           config_sha256=digest(CONFIG), rules_sha256=digest(RULES_FILE), seniority=seniority)
            entries[key] = {'cv_id': cv_id, 'seniority_rule': seniority, 'result': recommendation(rec, meta),
                            'replayed_answers': len(replay.used),
                            'fallback_jobs': rec.fallback_ids}
    return {'version': DEMO_VERSION, 'built': date.today().isoformat(), 'split': 'development',
            'label': 'Demo with saved results', 'entries': entries, 'score_checks': checks,
            'provenance': {'config': str(CONFIG.relative_to(ROOT)), 'config_sha256': digest(CONFIG),
                           'rules_sha256': digest(RULES_FILE), 'rankings_sha256': digest(RANKINGS),
                           'sol_summary_sha256': digest(SOURCES['gpt-6-sol'] / 'summary_v1.json'),
                           'luna_summary_sha256': digest(SOURCES['gpt-6-luna'] / 'summary_v1.json')}}


def main() -> int:
    bundle = build()
    # Version numbers continue after archived bundles (evals/demo/archive/), never reused.
    taken = [int(p.name.split('_v', 1)[1].split('_')[0]) for p in (ROOT / 'evals/demo').rglob('saved_demo_v*') if p.is_dir()]
    n = max(taken, default=0) + 1
    folder = ROOT / f'evals/demo/saved_demo_v{n}'
    folder.mkdir(parents=True)
    (folder / 'bundle.json').write_text(json.dumps(bundle, indent=1, ensure_ascii=False) + '\n')
    for e in bundle['entries'].values():
        b = e['result']['blocks'][0]['groups']
        print(e['cv_id'], 'rule' if e['seniority_rule'] else 'no rule',
              {k: len(v) for k, v in b.items()}, 'fallback', e['fallback_jobs'])
    print('score checks', bundle['score_checks'], 'wrote', folder.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
