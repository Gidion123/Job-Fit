"""Evaluate saved development top30 results without inference or label mutation."""
from pathlib import Path
import json
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / 'src')]
from jobfit.config import REPO_ROOT
from jobfit.eval.retrieval_evaluation import evaluate

if __name__ == '__main__':
    result = evaluate(REPO_ROOT)
    path = REPO_ROOT / 'evals/results' / (result['run_id'] + '.json')
    with path.open('x') as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
        file.write('\n')
    print(json.dumps({'status': result['status'], 'file': str(path.relative_to(REPO_ROOT)),
                      'aggregate': result['aggregate'], 'api_calls': 0, 'winner': None}, indent=2))
