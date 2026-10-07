"""CP2.5 held-out figures and tables from the saved CP2.4 report (no inference, no tuning).

Inputs (read only): evals/results/cp24/heldout_report_v1.json, the test run files in
evals/results/cp24/test_run_v1/ and the labels evals/gold/test_v13_cp24_r1/.
The frozen report is first reproduced with the frozen build_report; any difference stops the script.

Outputs (new versioned names; never overwritten):
- reports/figures/cp2/fig09_cp24_heldout_primary_v1.png        (headline, CV3-CV5)
- reports/figures/cp2/fig10_cp24_supplementary_familiar_v1.png (CV1-CV2 diagnostic only)
- reports/figures/cp2/fig11_cp24_order_decomposition_v1.png    (post-hoc diagnostic, not headline)
- evals/results/cp24/cp25_tables_v1/                           (tables + receipt)
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('MPLCONFIGDIR', '/tmp/jobfit_mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from jobfit.eval.heldout_report import PRIMARY, SUPPLEMENTARY, build_report, check_contract  # noqa: E402
from jobfit.eval.metrics import ranking_metrics  # noqa: E402

REPORT = ROOT / 'evals/results/cp24/heldout_report_v1.json'
RUN_DIR = ROOT / 'evals/results/cp24/test_run_v1'
GOLD = ROOT / 'evals/gold/test_v13_cp24_r1'
FIG = ROOT / 'reports/figures/cp2'
TABLES = ROOT / 'evals/results/cp24/cp25_tables_v1'
FIGS = {'primary': 'fig09_cp24_heldout_primary_v1.png',
        'supplementary': 'fig10_cp24_supplementary_familiar_v1.png',
        'decomposition': 'fig11_cp24_order_decomposition_v1.png'}
PROVENANCE = 'Labels: AI-assisted (ChatGPT), human-reviewed (1 reviewer), blind to ranking; not independent human gold (D-088).'
BIAS = ('Labeling assistant and matcher are both OpenAI-family models: correlated preferences may inflate '
        'apparent agreement; direction and magnitude not measured.')
SIZE = 'Test: 3 synthetic held-out CVs (CV3-CV5), 68 pooled pairs over CV1-CV5, 67 judged + 1 unjudged (CV5/F00070).'
STAGE1 = '#7a8ca3'
FINAL = '#1f5f99'
DIAG = '#c47a1d'


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_labels():
    out = {}
    for line in (GOLD / 'relevance_gold.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['review_status'] == 'approved':
            out.setdefault(row['cv_id'], {})[row['job_id']] = int(row['relevance_0_3'])
    return out


def fmt(v):
    return 'n/a' if v is None else f'{v:.3f}'


def main() -> int:
    targets = [FIG / n for n in FIGS.values()] + [TABLES]
    if any(t.exists() for t in targets):
        raise SystemExit('output exists; bump the version instead of overwriting')
    report = json.loads(REPORT.read_text())
    run = json.loads((RUN_DIR / 'test_run.json').read_text())
    labels = load_labels()
    eligible = sorted((ROOT / 'evals/splits/test_job_ids.txt').read_text().split())
    again = build_report(run, labels, eligible=eligible)
    if json.loads(json.dumps(again)) != report:
        raise SystemExit('saved heldout_report_v1.json does not reproduce from the labels')
    check_contract(report)
    held = json.loads((GOLD / 'held_test_r1.json').read_text())
    unjudged = {(h['cv_id'], h['job_id']) for h in held}
    per = report['per_cv']

    # ---- per-CV table with explicit coverage
    finals = {cv: json.loads((RUN_DIR / f'final_{cv}.json').read_text()) for cv in PRIMARY + SUPPLEMENTARY}
    rows = []
    for cv in PRIMARY + SUPPLEMENTARY:
        f = finals[cv]
        statuses = [f['jobs'][j]['score']['status'] for j in f['order']]
        pooled = len(labels.get(cv, {})) + sum(1 for c, _ in unjudged if c == cv)
        rows.append({
            'cv_id': cv, 'group': per[cv]['group'], 'pooled_pairs': pooled,
            'judged_pairs': len(labels.get(cv, {})), 'unjudged_pairs': pooled - len(labels.get(cv, {})),
            'stage1_p_at_5': per[cv]['stage1']['p_at_5'], 'final_p_at_5': per[cv]['final']['p_at_5'],
            'stage1_ndcg_at_10': per[cv]['stage1']['ndcg_at_10'], 'final_ndcg_at_10': per[cv]['final']['ndcg_at_10'],
            'final_ndcg_reason': per[cv]['final']['ndcg_reason'] or '',
            'final_top10_unjudged': ' '.join(per[cv]['final']['unjudged_top10']),
            'final_top10_scored': sum(s in ('final', 'provisional') for s in statuses),
            'final_top10_held_or_no_score': sum(s not in ('final', 'provisional') for s in statuses),
        })
    groups = []
    for name in ('primary_heldout', 'supplementary_familiar'):
        g = report[name]
        for metric in ('p_at_5', 'ndcg_at_10'):
            m = g[metric]
            groups.append({'group': name, 'metric': metric, 'stage1_macro': m['stage1_macro'],
                           'final_macro': m['final_macro'], 'cvs_included': m['cv_count'],
                           'cvs_planned': m['planned_cv_count'],
                           'coverage': f"{m['cv_count']}/{m['planned_cv_count']} CV complete",
                           'cvs_in_macro': ' '.join(cv for cv in g['cvs'] if cv not in m['omitted']),
                           'omitted': '; '.join(f'{cv}: final {r["final"]}' for cv, r in m['omitted'].items())})

    # ---- post-hoc decomposition: raw stage 1 -> stage 1 + seniority rule (pre-LLM) -> final product order
    decomp = []
    for cv in PRIMARY + SUPPLEMENTARY:
        pre = finals[cv]['analyzed_ids']
        p5 = ranking_metrics(pre, labels[cv], eligible_ids=eligible, k=5)
        n10 = ranking_metrics(pre, labels[cv], eligible_ids=eligible, k=10)
        decomp.append({'cv_id': cv, 'group': per[cv]['group'],
                       'stage1_p_at_5': per[cv]['stage1']['p_at_5'],
                       'seniority_pre_llm_p_at_5': p5['precision_at_k']['value'],
                       'final_p_at_5': per[cv]['final']['p_at_5'],
                       'stage1_ndcg_at_10': per[cv]['stage1']['ndcg_at_10'],
                       'seniority_pre_llm_ndcg_at_10': n10['ndcg_at_k'],
                       'final_ndcg_at_10': per[cv]['final']['ndcg_at_10'],
                       'seniority_pre_llm_reason': n10['ndcg_reason'] or ''})

    TABLES.mkdir(parents=True)
    for name, data in (('per_cv.csv', rows), ('group_macros.csv', groups), ('order_decomposition_posthoc.csv', decomp)):
        with (TABLES / name).open('w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader(); w.writerows(data)

    # ---- figure 9: primary headline
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    for ax, metric, title in ((axes[0], 'p_at_5', 'P@5'), (axes[1], 'ndcg_at_10', 'NDCG@10')):
        x = np.arange(len(PRIMARY))
        s = [per[cv]['stage1'][metric] for cv in PRIMARY]
        f = [per[cv]['final'][metric] for cv in PRIMARY]
        ax.bar(x - .19, s, .36, color=STAGE1, label='Stage 1 (hybrid retrieval)')
        ax.bar(x + .19, [v or 0 for v in f], .36, color=FINAL, label='Final product order')
        for i, (a, b) in enumerate(zip(s, f)):
            ax.text(i - .19, a + .02, fmt(a), ha='center', fontsize=8)
            if b is None:
                ax.text(i + .19, .04, 'unavailable\nF00070\nunjudged', ha='center', fontsize=7, color='#b23b3b')
            else:
                ax.text(i + .19, b + .02, fmt(b), ha='center', fontsize=8)
        g = report['primary_heldout'][metric]
        ax.set_xticks(x, PRIMARY); ax.set_ylim(0, 1.18)
        ax.set_title(f"{title}  macro {fmt(g['stage1_macro'])} -> {fmt(g['final_macro'])}\n"
                     f"({g['cv_count']}/{g['planned_cv_count']} CV complete"
                     + (f"; macro over {' '.join(cv for cv in PRIMARY if cv not in g['omitted'])} only" if g['omitted'] else '')
                     + ')', fontsize=10)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].legend(loc='upper left', fontsize=8, frameon=False)
    fig.suptitle('CP2.4 held-out test (headline): CV3-CV5, frozen config D-087', fontsize=12)
    fig.text(.01, -.06, f'{SIZE}\n{PROVENANCE}\n{BIAS}\nMissing labels are never 0 (D-052); stage-1 NDCG macro uses the same 2 CVs.',
             fontsize=7.5, color='#425466', va='bottom')
    fig.savefig(FIG / FIGS['primary'], dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig)

    # ---- figure 10: supplementary
    fig, ax = plt.subplots(figsize=(8, 4.6))
    labels_x = [f'{cv} {m}' for cv in SUPPLEMENTARY for m in ('P@5', 'NDCG@10')]
    s = [per[cv]['stage1'][m] for cv in SUPPLEMENTARY for m in ('p_at_5', 'ndcg_at_10')]
    f = [per[cv]['final'][m] for cv in SUPPLEMENTARY for m in ('p_at_5', 'ndcg_at_10')]
    x = np.arange(len(labels_x))
    ax.bar(x - .19, s, .36, color=STAGE1, label='Stage 1'); ax.bar(x + .19, f, .36, color=FINAL, label='Final')
    for i, (a, b) in enumerate(zip(s, f)):
        ax.text(i - .19, a + .02, fmt(a), ha='center', fontsize=8); ax.text(i + .19, b + .02, fmt(b), ha='center', fontsize=8)
    ax.set_xticks(x, labels_x); ax.set_ylim(0, 1.15); ax.legend(frameon=False, fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_title('Supplementary diagnostic only: CV1-CV2 (familiar development profiles on held-out jobs)\n'
                 'Not part of the headline; never pooled with CV3-CV5', fontsize=10)
    fig.text(.01, -.08, f'{PROVENANCE}\n{BIAS}', fontsize=7.5, color='#425466', va='bottom')
    fig.savefig(FIG / FIGS['supplementary'], dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig)

    # ---- figure 11: decomposition (diagnostic)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, metric, title in ((axes[0], 'p_at_5', 'P@5'), (axes[1], 'ndcg_at_10', 'NDCG@10')):
        x = np.arange(len(PRIMARY))
        d = {r['cv_id']: r for r in decomp}
        series = [('stage1', STAGE1, 'Stage 1 raw'), ('seniority_pre_llm', DIAG, 'Stage 1 + seniority rule (pre-LLM)'),
                  ('final', FINAL, 'Final product order (LLM)')]
        for k, (key, color, lab) in enumerate(series):
            vals = [d[cv][f'{key}_{metric}'] for cv in PRIMARY]
            ax.bar(x + (k - 1) * .26, [v or 0 for v in vals], .25, color=color, label=lab)
            for i, v in enumerate(vals):
                ax.text(i + (k - 1) * .26, (v or 0) + .02, fmt(v), ha='center', fontsize=7,
                        color='#b23b3b' if v is None else 'black')
        ax.set_xticks(x, PRIMARY); ax.set_ylim(0, 1.18); ax.set_title(title, fontsize=10)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].legend(loc='upper left', fontsize=7.5, frameon=False)
    fig.suptitle('Post-hoc diagnostic (not headline, no tuning): where the CV3-CV5 change comes from', fontsize=11)
    fig.text(.01, -.06, 'Middle bar = the analyzed top 10 in seniority-rule order, before LLM scoring (same jobs as the final top 10).\n'
             f'{PROVENANCE}\n{BIAS}', fontsize=7.5, color='#425466', va='bottom')
    fig.savefig(FIG / FIGS['decomposition'], dpi=180, bbox_inches='tight', facecolor='white'); plt.close(fig)

    inputs = [REPORT, RUN_DIR / 'test_run.json', GOLD / 'relevance_gold.jsonl', GOLD / 'held_test_r1.json',
              GOLD / 'provenance_manifest.json'] + [RUN_DIR / f'final_{cv}.json' for cv in PRIMARY + SUPPLEMENTARY]
    outputs = [FIG / n for n in FIGS.values()] + sorted(TABLES.iterdir())
    (TABLES / 'receipt.json').write_text(json.dumps({
        'script': 'scripts/build_cp25_heldout_figures.py', 'report_reproduced_from_labels': True,
        'contract': report['contract'], 'label_version': 'test_v13_cp24_r1',
        'inputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in inputs},
        'outputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in outputs},
        'notes': ['Figure 11 and order_decomposition_posthoc.csv are post-hoc diagnostics, not part of the frozen '
                  'contract and not used to change anything.']}, indent=1) + '\n')
    print(json.dumps({'per_cv': rows, 'groups': groups, 'decomposition': decomp}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
