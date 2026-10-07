"""Offline quote-compatibility receipt for synthetic CV1/CV2 masking.

The receipt has identities and hashes, never raw CV text or quote contents.
It does not approve gold labels or prove semantic equivalence.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1]/'src')]

from jobfit.config import REPO_ROOT
from jobfit.privacy.masking import VERSION, mask_local

CVS = {
    'CV1': ('data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md', 'Rina'),
    'CV2': ('data/synthetic_cvs/cv_02_career_switcher_ai_engineer_en.md', 'Bima'),
}
GOLD = REPO_ROOT/'evals/gold/development_v13_reviewed_20261003_stage1_r3/evidence_gold.jsonl'
OUTPUT = REPO_ROOT/'evals/results/cp23_masking_quote_compatibility_20261004_v1.json'


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def check() -> dict:
    rows = [json.loads(line) for line in GOLD.read_text().splitlines() if line]
    results = {}
    for cv_id, (relative, name) in CVS.items():
        source = REPO_ROOT/relative
        raw = source.read_text()
        hints = {'name': (name,)}
        masked = mask_local(raw, reviewed_identifiers=hints)
        quoted = [row for row in rows if row['cv_id'] == cv_id and row.get('cv_quote')]
        changed = []
        for row in quoted:
            quote = row['cv_quote']
            if quote not in raw:
                raise ValueError(f'Saved gold quote missing from synthetic source: {cv_id}/{row["job_id"]}/{row["unit_no"]}')
            if quote in masked.text:
                continue
            mapped = mask_local(quote, reviewed_identifiers=hints).text
            changed.append({
                'cv_id': cv_id, 'job_id': row['job_id'], 'unit_no': row['unit_no'],
                'review_status': row['review_status'],
                'raw_quote_sha256': sha256(quote.encode()).hexdigest(),
                'masked_quote_sha256': sha256(mapped.encode()).hexdigest(),
                'mapped_quote_exact_in_masked_cv': mapped in masked.text,
                'semantic_label_review': 'not_performed',
            })
        results[cv_id] = {
            'source_file': relative, 'source_sha256': digest(source),
            'masked_sha256': masked.digest,
            'quoted_gold_rows': len(quoted),
            'unchanged_exact_quote_rows': len(quoted) - len(changed),
            'changed_quote_rows': len(changed),
            'changed_unique_source_quotes': len({item['raw_quote_sha256'] for item in changed}),
            'changed_rows': changed,
            'masking_entity_counts': masked.counts,
        }
    return {
        'schema_version': 'cp23-masking-quote-compatibility-v1',
        'scope': 'development_synthetic_CV1_CV2_only',
        'masking_version': VERSION,
        'gold_file': str(GOLD.relative_to(REPO_ROOT)),
        'gold_sha256': digest(GOLD),
        'results': results,
        'all_changed_quotes_mapped_exactly': all(
            item['mapped_quote_exact_in_masked_cv']
            for result in results.values() for item in result['changed_rows']
        ),
        'semantic_equivalence_approved': False,
        'limitation': 'Text mapping is mechanical. It does not validate the evidence meaning or a model response.',
        'api_calls': 0,
    }


if __name__ == '__main__':
    if OUTPUT.exists():
        raise SystemExit('Versioned receipt already exists; preserve it')
    receipt = check()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open('x') as file:
        json.dump(receipt, file, indent=2)
    print(json.dumps({cv: {'quotes': result['quoted_gold_rows'], 'changed': result['changed_quote_rows']}
                      for cv, result in receipt['results'].items()}))
