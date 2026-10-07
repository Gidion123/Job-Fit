"""T03 part 2: six retrieval candidates, frozen development only, cache only."""
import csv
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import yaml
from jobfit.config import REPO_ROOT, SNAPSHOT_ID
from jobfit.db.session import connect
from jobfit.search import dense, fts, hybrid, keyword
from jobfit.search.embeddings import ModelTokenizer, cv_body, load_specs, prepare
from jobfit.search.query_cache import SyntheticQueryCache
from jobfit.search.pools import pool_rows

CVS = {'CV1': 'cv_01_fresh_graduate_data_science_id.md',
       'CV2': 'cv_02_career_switcher_ai_engineer_en.md'}


def main():
    review_books = ('dev_batch_01.xlsx', 'dev_batch_02.xlsx',
                    'JobFit_Development_Labeling_v0.1.xlsx')
    if any((REPO_ROOT / 'evals/labeling' / name).exists() for name in review_books):
        raise ValueError('review workbook exists; pool cannot be regenerated')
    splits = REPO_ROOT / 'evals/splits'
    manifest = json.loads((splits / 'split_manifest.json').read_text())
    for name, digest in manifest['output_hashes'].items():
        if hashlib.sha256((splits/name).read_bytes()).hexdigest() != digest:
            raise ValueError('frozen split changed')
    dev = set((splits/'dev_job_ids.txt').read_text().splitlines())
    test = set((splits/'test_job_ids.txt').read_text().splitlines())
    if len(dev) != 214 or len(test) != 214 or dev & test:
        raise ValueError('invalid split')
    with (REPO_ROOT/'evals/gold/relevance_gold.csv').open() as f:
        gold = list(csv.DictReader(f))
    if any(r['split'] != 'development' for r in gold):
        raise ValueError('test gold must not be read during development pooling')
    cfg = yaml.safe_load((REPO_ROOT/'config/retrieval_v1.yaml').read_text())
    cache = SyntheticQueryCache(REPO_ROOT/'reports/embedding_queries')
    specs = load_specs()
    report = dict(snapshot_id=SNAPSHOT_ID, seed=20261001, split_hashes=manifest['output_hashes'],
                  config=cfg, cv_hashes={}, profiles=[s.profile_id for s in specs], cvs={},
                  api_calls=0, session_cost_usd=0)
    all_rows = []
    with connect() as conn:
        jobs = [dict(zip(('job_id','title','skills_v0'), r)) for r in conn.execute(
            'SELECT job_id,title,skills_v0 FROM jobs WHERE snapshot_id=%s AND job_id=ANY(%s) ORDER BY job_id',
            (SNAPSHOT_ID, sorted(dev))).fetchall()]
        if len(jobs) != 214:
            raise ValueError('development database coverage mismatch')
        titles = {j['job_id']: j['title'] for j in jobs}
        for cv_id, filename in CVS.items():
            path = REPO_ROOT/'data/synthetic_cvs'/filename
            text = cv_body(path)
            report['cv_hashes'][cv_id] = hashlib.sha256(path.read_bytes()).hexdigest()
            skills = keyword.cv_skills(text)
            rankings = {'B0': keyword.rank(skills, jobs, top_k=20),
                        'B1': fts.rank(conn, skills, job_ids=dev, top_k=20)}
            for spec in specs:
                doc = prepare(cv_id, text, spec, ModelTokenizer(spec))
                query = dense.QueryEmbedding(spec.profile_id, cache.get(spec, doc))
                name = 'openai' if spec.model.startswith('openai/') else 'qwen'
                rankings['dense_'+name] = dense.rank(conn, query, spec, job_ids=dev, top_k=20)
                rankings['hybrid_'+name] = hybrid.rank(conn, skills, query, spec, job_ids=dev,
                    top_k=20, branch_depth=cfg['branch_depth'], k=cfg['rrf_k'])
            if any(not {r['job_id'] for r in rs} <= dev for rs in rankings.values()):
                raise ValueError('out of development scope')
            rows, counts = pool_rows(cv_id, rankings, titles,
                {r['job_id'] for r in gold if r['cv_id'] == cv_id})
            report['cvs'][cv_id] = dict(**counts, rankings=rankings)
            all_rows.extend(rows)
    directory = REPO_ROOT/'evals/pools'
    directory.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite a pool once human review workbooks have been created.
    if any((REPO_ROOT / 'evals/labeling' / name).exists() for name in review_books):
        raise ValueError('review workbook exists; pool cannot be regenerated')
    with (directory/'dev_pool.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    (REPO_ROOT/'evals/results/t03_dev_pool_20261001.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({cv: {k:v for k,v in r.items() if k != 'rankings'}
                      for cv, r in report['cvs'].items()}, indent=2))
    return 2 if any(r['selection_blocked'] for r in report['cvs'].values()) else 0


if __name__ == '__main__':
    raise SystemExit(main())
