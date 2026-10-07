"""Offline CP2.3 readiness report. No inference, gold export, or test evaluation.

Exit 2 means expected prerequisites are not ready; the report explains why.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import argparse
import json
from jobfit.eval.run_eval import prepare_development

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--split',choices=['development'],default='development')
    p.add_argument('--reviewed-bundle',type=Path,help='Explicit versioned reviewed-record gold bundle')
    p.add_argument('--retrieval',type=Path,help='Saved comparable top30 retrieval artifact for bundle readiness')
    p.add_argument('--acceptance-probe',type=Path,help='Explicit completed, operationally reviewed development probe; not a model selection')
    p.add_argument('--historical-pilot',action='store_true',help='Explicitly inspect the legacy pilot export with its historical readiness rules')
    args=p.parse_args()
    if args.reviewed_bundle:
        if not args.retrieval:p.error('--reviewed-bundle requires --retrieval')
        from jobfit.config import REPO_ROOT
        from jobfit.eval.bundle_readiness import prepare_reviewed_bundle
        report=prepare_reviewed_bundle(REPO_ROOT,args.reviewed_bundle.resolve(),args.retrieval.resolve(),
            args.acceptance_probe.resolve() if args.acceptance_probe else None)
    else:
        if args.acceptance_probe:p.error('--acceptance-probe requires --reviewed-bundle')
        if not args.historical_pilot:p.error('Specify --reviewed-bundle and --retrieval; the legacy pilot path requires --historical-pilot')
        report=prepare_development()
    with args.output.open('x') as f:json.dump(report,f,indent=2,ensure_ascii=False)
    print(json.dumps({k:report[k] for k in ['status','purpose','gold_inventory','blockers','api_calls']},indent=2))
    return 2 if report['status']=='blocked' else 0

if __name__=='__main__':raise SystemExit(main())
