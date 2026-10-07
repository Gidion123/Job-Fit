"""Closure gates keep partial paid runs and new alignments out of publication."""
import json
import pytest
from scripts import prepare_cp23_followup_alignment as alignment
from scripts import evaluate_cp23_followup_matching as matching
from scripts import evaluate_cp23_followup_extraction as extraction

def test_new_alignment_refuses_incomplete_original_scope(tmp_path,monkeypatch):
    state=tmp_path/'state.json';state.write_text(json.dumps({'status':'ready','results':[]}))
    plan=tmp_path/'plan.json';plan.write_text('{}')
    monkeypatch.setattr(alignment,'STATE',state);monkeypatch.setattr(alignment,'PLAN',plan)
    with pytest.raises(ValueError,match='Entire D-064 original extraction scope'):alignment.prepare()

def test_fixed_evidence_refuses_incomplete_followup_even_with_adapter_acceptance(tmp_path,monkeypatch):
    state=tmp_path/'state.json';state.write_text(json.dumps({'status':'running','results':[]}))
    plan=tmp_path/'plan.json';plan.write_text('{}')
    monkeypatch.setattr(matching,'STATE',state);monkeypatch.setattr(matching,'PLAN',plan)
    monkeypatch.setattr(matching,'accepted_packet',lambda:(None,{'verification_method':'accepted assisted QA'}))
    with pytest.raises(ValueError,match='D-064 collection incomplete'):matching.evaluate()

def test_payment_approval_is_not_new_alignment_acceptance(tmp_path,monkeypatch):
    approval=tmp_path/'approval.json';approval.write_text(json.dumps({'approved_by':'Dion','decision_id':'D-064','ceiling_usd':'6.40'}))
    monkeypatch.setattr(extraction,'APPROVAL',approval)
    monkeypatch.setattr(extraction,'accepted_packet',lambda:(None,{}))
    with pytest.raises(ValueError,match='Exact new candidate alignment acceptance'):extraction.evaluate()

def test_common_scope_rejects_missing_failed_reference_units():
    with pytest.raises(ValueError,match='Reference denominator changed'):
        extraction.aggregate([{'tp':57,'fp':2,'fn':0}],73)
