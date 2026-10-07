"""Cache-only top30 development retrieval. No workbook, labels or paid fallback."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import argparse
import json
from jobfit.config import REPO_ROOT
from jobfit.db.session import connect
from jobfit.eval.retrieval_run import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.parent != (REPO_ROOT/'evals/results').resolve() or output.suffix!='.json':
        raise ValueError('New JSON output must be directly inside evals/results')
    # Reserve an exclusive artifact before reading DB. Existing historical files refused.
    with output.open('x') as f:
        try:
            with connect() as conn:
                result=run(conn)
        except Exception as exc:
            result={'status':'failed','error_type':type(exc).__name__,'api_calls':0,
                    'cost_usd':0,'quality_metrics':None,'winner':None,
                    'next_action':'Check local DB and exact source/profile/query cache compatibility; no inference fallback'}
        f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'rankings':len(result.get('runs',[])),
                      'output':str(output),'api_calls':0}))
    return 0 if result['status']=='success' else 2


if __name__=='__main__': raise SystemExit(main())
