"""Import the CP2.4 test relevance labels as test_v13_cp24_r1 (D-088).

Source of truth: sheet C_Relevance of JobFit_Test_Relevance_Final_.xlsx (Dion's choice).
Provenance: AI-assisted (ChatGPT drafts and recommendations), human-reviewed (Dion made every
final decision), blind to JobFit ranking. Not independent human annotation.

Only two corrections are applied, both approved by Dion in chat:
- T68 (CV5/F00070) becomes an unscorable source-quality hold (never 0, D-052).
- Five main_reason texts (T17, T21, T23, T43, T50) had requirement text cut with '…'. The cut
  fragment is replaced by the full unit_text of the same job in sheet A_Extraction of the same
  workbook. Text-only; scores do not change.

Change summary: 1 relevance-label change (T68 2 -> UNJUDGED), 5 text-only corrections,
0 other relevance/score changes.

Workbooks are only read. The output folder must not exist. This file is not in the D-087 freeze.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
LABEL_DIR = ROOT / 'evals/labeling/test_relevance_cp24_test_v1_v1'
FINAL = LABEL_DIR / 'JobFit_Test_Relevance_Final_.xlsx'
BLIND = LABEL_DIR / 'JobFit_Test_Relevance.xlsx'
OUT = ROOT / 'evals/gold/test_v13_cp24_r1'
VERSION = 'test_v13_cp24_r1'
MODE = 'ai_assisted_human_reviewed_blind_to_ranking'
TEXT_FIX_ITEMS = ('T17', 'T21', 'T23', 'T43', 'T50')
HOLD_ITEMS = {'T68': 'unscorable_source_quality'}
ELLIPSIS = '…'
PREVIOUS = ROOT / 'evals/gold/archive/test_v13_cp24_r1_metadata_v1/superseded_note.json'


def change_summary(diff, gold, before) -> dict:
    label = [d for d in diff if d['field'] == 'relevance_0_3']
    text = [d for d in diff if d['field'] == 'main_reason']
    old = {b['item_id']: b['relevance_0_3'] for b in before}
    other = [g['item_id'] for g in gold if g['relevance_0_3'] != old[g['item_id']]]
    if other or any(d['score_before'] != d['score_after'] for d in text):
        raise SystemExit(f'unexpected score change: {other}')
    return {
        'relevance_label_changes': {'count': len(label), 'items': [
            {'item_id': d['item_id'], 'before': d['before'], 'after': 'UNJUDGED'} for d in label]},
        'text_only_corrections': {'count': len(text), 'items': [d['item_id'] for d in text],
                                  'field': 'main_reason', 'score_changed': False},
        'other_relevance_or_score_changes': {'count': 0, 'items': []},
        'statement': f'{len(label)} relevance-label change (' + ', '.join(
            f"{d['item_id']} {d['before']} -> UNJUDGED" for d in label) + f'); {len(text)} text-only '
            'corrections (' + ', '.join(d['item_id'] for d in text) + '); 0 other relevance/score changes.',
    }


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sheet(wb, name):
    rows = list(wb[name].iter_rows(values_only=True))
    return [dict(zip(rows[0], r)) for r in rows[1:] if r and any(v is not None for v in r)]


def expand_truncated(text: str, units: list[str]) -> tuple[str, list[dict]]:
    """Replace every 'prefix…' fragment with the one unit_text that starts with that prefix."""
    out, changes = text, []
    while ELLIPSIS in out:
        cut = out.index(ELLIPSIS)
        hits = []
        for unit in units:
            for start in range(cut):
                frag = out[start:cut]
                if len(frag) >= 20 and unit.startswith(frag) and (start == 0 or out[start - 1] == ' '):
                    hits.append((start, unit))
                    break
        starts = {s for s, _ in hits}
        full = {u for _, u in hits}
        if len(full) != 1:
            raise SystemExit(f'cannot expand uniquely at {cut}: {sorted(full)}')
        start = min(starts)
        unit = full.pop()
        changes.append({'truncated': out[start:cut + 1], 'restored': unit})
        out = out[:start] + unit + out[cut + 1:]
    return out.replace('..', '.'), changes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args(argv)
    if any(p.name.startswith('~$') for p in LABEL_DIR.iterdir()):
        raise SystemExit('workbook is open (lock file found); close Excel first')
    manifest = json.loads((LABEL_DIR / 'manifest.json').read_text())
    before_hash = {'final': sha(FINAL), 'blind': sha(BLIND)}
    if before_hash['blind'] != manifest['workbook_sha256_at_creation']:
        raise SystemExit('blind workbook changed since creation')
    wb = openpyxl.load_workbook(FINAL, read_only=True)
    rows_c = sheet(wb, 'C_Relevance')
    units = {}
    for a in sheet(wb, 'A_Extraction'):
        units.setdefault(a['job_id'], []).append(a['unit_text'])
    item_of = {(i['cv_id'], i['job_id']): i['item_id'] for i in manifest['items']}
    keys = [(r['cv_id'], r['job_id']) for r in rows_c]
    if len(keys) != len(set(keys)) or set(keys) != set(item_of):
        raise SystemExit('C_Relevance pairs do not match the manifest one to one')

    before, gold, held, diff, notes = [], [], [], [], []
    for r in sorted(rows_c, key=lambda r: item_of[(r['cv_id'], r['job_id'])]):
        item = item_of[(r['cv_id'], r['job_id'])]
        before.append({'item_id': item, **r})
        if r['relevance_0_3'] not in (0, 1, 2, 3) or r['review_status'] != 'approved':
            raise SystemExit(f'{item}: unexpected score/status')
        if not r['pilot_id']:
            notes.append({'item_id': item, 'note': 'pilot_id empty in C_Relevance; pair is uniquely '
                          'identified by (cv_id, job_id) and item_id; evaluator does not read pilot_id'})
        reason = r['main_reason']
        if ELLIPSIS in reason and item not in TEXT_FIX_ITEMS:
            raise SystemExit(f'{item}: truncated reason not in the approved list')
        if item in HOLD_ITEMS:
            held.append({'record': 'C_Relevance', 'item_id': item, 'cv_id': r['cv_id'],
                         'job_id': r['job_id'], 'job_title': r['job_title'],
                         'hold_reason': HOLD_ITEMS[item], 'c_sheet_value': r['relevance_0_3'],
                         'main_reason': reason, 'draft_note': r['draft_note'],
                         'a_extraction_units': len(units.get(r['job_id'], [])),
                         'decision': 'D-088',
                         'note': 'Not a relevance judgment; never counted as 0 (D-052). Unjudged.'})
            diff.append({'item_id': item, 'cv_id': r['cv_id'], 'job_id': r['job_id'],
                         'field': 'relevance_0_3', 'before': r['relevance_0_3'],
                         'after': 'UNJUDGED (held)', 'reason': 'JD has responsibilities only and '
                         '0 A_Extraction units; no assessable qualification requirements'})
            continue
        if item in TEXT_FIX_ITEMS:
            new_reason, changes = expand_truncated(reason, units.get(r['job_id'], []))
            if not changes:
                raise SystemExit(f'{item}: no truncation found')
            diff.append({'item_id': item, 'cv_id': r['cv_id'], 'job_id': r['job_id'],
                         'field': 'main_reason', 'before': reason, 'after': new_reason,
                         'restored_fragments': changes, 'score_before': r['relevance_0_3'],
                         'score_after': r['relevance_0_3'],
                         'source': 'A_Extraction.unit_text of the same job, same workbook'})
            reason = new_reason
        gold.append({'item_id': item, 'cv_id': r['cv_id'], 'job_id': r['job_id'],
                     'job_title': r['job_title'], 'relevance_0_3': r['relevance_0_3'],
                     'main_reason': reason, 'constraint_note': r['constraint_note'],
                     'review_status': 'approved', 'review_action': r['review_action'],
                     'label_source': 'ai_assisted_human_reviewed',
                     'sheet_label_source': r['label_source'], 'labeling_mode': MODE,
                     'label_version': VERSION, 'guideline_version': r['guideline_version'],
                     'draft_note': r['draft_note']})
    missing = set(TEXT_FIX_ITEMS) - {d['item_id'] for d in diff}
    if missing:
        raise SystemExit(f'text fix items not found: {sorted(missing)}')

    per_cv = {}
    for g in gold:
        per_cv.setdefault(g['cv_id'], {'judged': 0, 'unjudged': 0})['judged'] += 1
    for h in held:
        per_cv.setdefault(h['cv_id'], {'judged': 0, 'unjudged': 0})['unjudged'] += 1
    print(json.dumps({'judged': len(gold), 'unjudged': len(held),
                      'per_cv': dict(sorted(per_cv.items())), 'diff_items': len(diff)}, indent=1))
    if not args.write:
        print('dry run; use --write')
        return 0
    if OUT.exists():
        raise SystemExit(f'{OUT} exists; never overwrite')
    OUT.mkdir(parents=True)

    def dump(name, obj, jsonl=False):
        text = (''.join(json.dumps(o, ensure_ascii=False) + '\n' for o in obj) if jsonl
                else json.dumps(obj, indent=1, ensure_ascii=False) + '\n')
        (OUT / name).write_text(text, encoding='utf-8')

    dump('relevance_before_correction.jsonl', before, jsonl=True)
    dump('relevance_gold.jsonl', gold, jsonl=True)
    dump('held_test_r1.json', held)
    summary = change_summary(diff, gold, before)
    dump('correction_diff.json', {'change_summary': summary, 'changes': diff})
    dump('provenance_manifest.json', {
        'label_version': VERSION, 'split': 'test', 'decision': 'D-088',
        'labeling_mode': MODE,
        'label_source': 'ai_assisted_human_reviewed',
        'annotator': {'name': 'Dion (Gidion Depari)', 'role': 'final decision on every label'},
        'assistant': {'tool': 'ChatGPT', 'provider_family': 'OpenAI',
                      'role': 'assessed CV-JD pairs and drafted recommendations, reasons and notes'},
        'blind_to_ranking': True,
        'hidden_during_labeling': ['JobFit rank', 'JobFit score', 'retriever method',
                                   'JobFit model suggestions', 'pool_provenance.json'],
        'independent_human_annotation': False, 'pure_human_gold': False,
        'annotators_count': 1, 'inter_annotator_agreement': 'not_measured',
        'authoritative_sheet': 'C_Relevance',
        'sheets_not_used': {'Items': 'relevance_0_3 and main_reason empty; not the label source',
                            'A_Extraction/B_Evidence': 'labeling support only; not imported'},
        'freeze': {'receipt': 'evals/freeze/cp23_freeze_draft_v2', 'decision': 'D-087',
                   'frozen_before_labeling': True},
        'test_used_for_tuning': False,
        'change_summary': summary,
        'counts': {'items': len(before), 'judged': len(gold), 'unjudged': len(held),
                   'per_cv': dict(sorted(per_cv.items()))},
        'required_disclosures': [
            'Labels are AI-assisted (ChatGPT) and human-reviewed by one reviewer; they are not '
            'independent human annotation and no inter-annotator agreement was measured.',
            'Because the labeling assistant and matcher are both OpenAI-family models, correlated '
            'model preferences may inflate apparent agreement. The direction and magnitude of this '
            'bias were not independently measured.',
            'This deviates from the D-053 wording "no model suggestions"; recorded in D-088.',
            'The headline covers three synthetic CVs (CV3-CV5); results are indicative only.',
            'Unscorable pairs are unjudged, never counted as 0 (D-052).'],
        'notes': notes,
    })
    after_hash = {'final': sha(FINAL), 'blind': sha(BLIND)}
    if after_hash != before_hash:
        raise SystemExit('source workbook changed during import')
    files = {p.name: sha(p) for p in sorted(OUT.iterdir())}
    dump('import_receipt.json', {
        'label_version': VERSION, 'decision': 'D-088', 'script': 'scripts/import_test_labels_cp24_r1.py',
        'source_workbooks': {
            'final': {'path': str(FINAL.relative_to(ROOT)), 'sha256_before': before_hash['final'],
                      'sha256_after': after_hash['final'], 'unchanged': True},
            'blind_original': {'path': str(BLIND.relative_to(ROOT)), 'sha256': after_hash['blind'],
                               'matches_manifest_at_creation': True}},
        'labeling_manifest_sha256': sha(LABEL_DIR / 'manifest.json'),
        'change_summary': summary,
        'supersedes': json.loads(PREVIOUS.read_text()) if PREVIOUS.exists() else None,
        'output_files_sha256': files})
    print('written', OUT.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
