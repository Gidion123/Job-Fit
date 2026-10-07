from collections import Counter
import pytest
from scripts.prepare_cp23_extraction_alignment import prepare, render
from jobfit.eval.metrics import extraction_metrics

def test_every_original_case_and_unit_has_pending_inventory():
    packet=prepare()
    assert len(packet['cases'])==28 and len({r['stage_id'] for r in packet['cases']})==28
    failures=[c for c in packet['cases'] if c['status']=='retained_process_failure']
    assert len(failures)==1 and failures[0]['stage_id']=='gemini-3.5-flash-lite/F00815'
    for case in packet['cases']:
        if 'rows' not in case:continue
        assert not case['unmapped_gold'] and not case['unmapped_model']
        assert case['human_verified'] is False and case['metrics'] is None
        g=[i for r in case['rows'] for i in r['gold_ids']]
        m=[i for r in case['rows'] for i in r['model_ids']]
        assert len(g)==len(set(g))==len(case['gold_unit_ids'])
        assert len(m)==len(set(m))==len(case['model_unit_ids'])
        for row in case['rows']:
            for ref in row['gold']:assert ref['source_quote'] in case['full_jd']
            for out in row['model']:assert all(q in case['full_jd'] for q in out['source_quotes'])
        with pytest.raises(ValueError):extraction_metrics(case,reference_complete=True)

def test_complex_and_omitted_preferred_units_cannot_disappear():
    packet=prepare();cases={c['stage_id']:c for c in packet['cases']}
    complex_rows=[r for c in packet['cases'] for r in c.get('rows',[]) if r['relation']=='complex_pending']
    assert len(complex_rows)==1 and len(complex_rows[0]['gold_ids'])==2 and len(complex_rows[0]['model_ids'])==3
    for model in ['gemini-3.5-flash-lite','claude-haiku-4.5']:
        c=cases[model+'/F00018']
        omitted={i for r in c['rows'] if r['relation']=='model_omission' for i in r['gold_ids']}
        assert {'P04-U18','P04-U18-AWS','P04-U19','P04-U20','P04-U21','P04-U22','P04-U23'}<=omitted

def test_historical_branch_qualifier_warning_is_not_silently_equivalence():
    packet=prepare();text=render(packet)
    assert 'inherited' in text and 'ordinary' in text.lower()
    assert 'no candidate-specific human approval' in text.lower()
    assert all(r['status']=='proposed_pending_alignment_review' for c in packet['cases'] for r in c.get('rows',[]))
