"""Versioned continuation after rejected GPT request; old runners stay frozen.

Reuse the reviewed dispatch/repair/source-check runner with explicit v6 globals.
The new session counts predecessor costs against the same cumulative USD3.16.
"""
from pathlib import Path
import sys
sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / 'src')]
from scripts import run_cp23_stage2_continuation as runner
from jobfit.config import REPO_ROOT
from jobfit.eval.stage2_route_repair import RUN_ID, RouteClient, RouteSession, build_route_plan

if __name__ == '__main__':
    runner.RUN_ID = RUN_ID
    runner.PLAN = REPO_ROOT / 'evals/results' / (RUN_ID + '_preflight.json')
    runner.STATE = REPO_ROOT / 'reports/quality_probe' / (RUN_ID + '.json')
    runner.build_continuation_plan = build_route_plan
    runner.OpenRouterClient = RouteClient
    runner.Stage2ComparisonSession = RouteSession
    runner.main()
