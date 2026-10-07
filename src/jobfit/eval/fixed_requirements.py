"""Read-only adapter from reviewed logical gold units to matcher-only inputs.

This adapter carries requirement text and provenance, never gold CV evidence or
answers. OR alternatives remain one logical unit with explicit branches. It
does not score, relabel, or change the exported gold bundle.
"""
from __future__ import annotations

import json
from pathlib import Path

from jobfit.matching.quote_check import require_quotes
from jobfit.schemas.requirements import JDExtraction, RequirementUnit, RequirementBranch

# Exact reviewed-unit strings bind the delegated source interpretation. Shared
# qualifiers are repeated in branch descriptions, so splitting at a bare pipe
# cannot turn "Python for analysis" into unsupported generic Python. This is a
# benchmark input adapter, not a change to gold, grouping or scoring rules.
OR_BRANCHES = {
    ('F00332', 'P30-U01'): ('Fresh graduate | bachelor in quantitative/analytical or other considered discipline',
        ['Fresh graduate', "Bachelor's degree in an analytical or quantitative discipline; other disciplines considered"]),
    ('F00036', 'P09-U01'): ('Bachelor Statistics | Mathematics | CS | Informatics | DS',
        ['Bachelor in Statistics', 'Bachelor in Mathematics', 'Bachelor in Computer Science',
         'Bachelor in Informatics Engineering', 'Bachelor in Data Science']),
    ('F00036', 'P09-U03'): ('Python | R | SQL for data manipulation and analysis',
        ['Python for data manipulation and analysis', 'R for data manipulation and analysis',
         'SQL for data manipulation and analysis']),
    ('F00036', 'P09-U07'): ('pandas | scikit-learn | TensorFlow | PyTorch',
        ['Experience using pandas', 'Experience using scikit-learn',
         'Experience using TensorFlow', 'Experience using PyTorch']),
    ('F00036', 'P09-U09'): ('Tableau | Power BI | Matplotlib',
        ['Data visualization using Tableau', 'Data visualization using Power BI',
         'Data visualization using Matplotlib']),
    ('F00036', 'P09-U15'): ('Hadoop | Spark | cloud big-data experience',
        ['Big-data experience with Hadoop', 'Big-data experience with Spark',
         'Big-data experience with cloud platforms']),
    ('F00815', 'P52-U03'): ('OpenAI | LangChain | LlamaIndex LLM framework',
        ['Experience with OpenAI for LLM work', 'Experience with LangChain for LLM work',
         'Experience with LlamaIndex for LLM work']),
    ('F00815', 'P52-U09'): ('FastAPI | Flask | equivalent API deployment',
        ['Experience building and deploying APIs with FastAPI',
         'Experience building and deploying APIs with Flask',
         'Experience building and deploying APIs with an equivalent framework']),
    ('F00815', 'P52-U11'): ('Pinecone | FAISS | Weaviate vector technology',
        ['Familiarity with Pinecone vector technology', 'Familiarity with FAISS vector technology',
         'Familiarity with Weaviate vector technology']),
    ('F00815', 'P52-U12'): ('AWS | other cloud platform',
        ['Experience with AWS', 'Experience with another cloud platform']),
    ('F00018', 'P04-U11'): ('Experience with at least one of:\nNLP | LLM | Recommendation systems',
        ['Practical use-case experience with NLP', 'Practical use-case experience with LLMs',
         'Practical use-case experience with recommendation systems']),
    ('F00018', 'P04-U20'): ('Taxonomies | ontologies',
        ['Experience with taxonomies', 'Experience with ontologies']),
    ('F00018', 'P04-U22'): ('Spark | Dask distributed processing',
        ['Practical experience with Spark distributed processing',
         'Practical experience with Dask distributed processing']),
}


def fixed_reviewed_requirements(bundle: Path, job_id: str, jd_text: str) -> JDExtraction:
    bundle = Path(bundle)
    rows = [json.loads(line) for line in (bundle/'extraction_gold.jsonl').read_text().splitlines()
            if line.strip()]
    selected = [row for row in rows if row['job_id'] == job_id]
    if not selected:
        raise ValueError('No reviewed extraction reference for selected JD')
    logical = [row for row in json.loads((bundle/'logical_units.json').read_text()) if row['job_id'] == job_id]
    if len(logical) != len(selected) or {r['row_ids'][0] for r in logical if len(r['row_ids']) == 1} != {r['unit_no'] for r in selected}:
        raise ValueError('Logical-unit mapping is not one reviewed row per input unit')
    if any(r['status'] != 'ready' or r['count_as'] != 1 or len(r['row_ids']) != 1 for r in logical):
        raise ValueError('Held, composite child or duplicate logical unit cannot enter fixed input')
    if len({r['unit_no'] for r in selected}) != len(selected):
        raise ValueError('Duplicate reviewed unit identity')
    units = []
    for row in selected:
        quote = row['source_quote']
        require_quotes([quote], jd_text)
        text = row['unit_text']
        alternatives = bool(row.get('group_id')) or (' | ' in text)
        if alternatives:
            # P04-U11 says "one or more" and has no historical group_id. The
            # authored mapping retains it as one OR logical unit.
            expected, parts = OR_BRANCHES.get((job_id, row['unit_no']), (None, None))
            if text != expected:
                raise ValueError('Reviewed OR meaning changed; source-check the fixed input again')
            if len(parts) < 2 or any(not p for p in parts):
                raise ValueError('Reviewed OR text needs explicit source review')
            branches = [RequirementBranch(branch_id=f'{row["unit_no"]}/B{i:02d}', text=part,
                                          field=row['category'], min_years=row['min_years'])
                        for i, part in enumerate(parts, 1)]
            kind = 'alternative_group'
        else:
            branches = []
            kind = 'qualified' if row['min_years'] is not None else 'simple'
        units.append(RequirementUnit(unit_id=row['unit_no'], text=text, kind=kind,
                                     importance=row['importance'], field=row['category'],
                                     min_years=row['min_years'] if not branches else None,
                                     branches=branches, source_quotes=[quote],
                                     label_source='annotator'))
    return JDExtraction(job_id=job_id, units=units,
                        extractor_version='reviewed-gold-fixed-input; no CV answers')
