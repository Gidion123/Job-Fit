"""Versioned, approved-only CP2.3 Stage-1 gold amendment; never edits a workbook."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from jobfit.eval.development_gold import validate_saved


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_hash(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def stage_approved_changes(root, base, review_packet, held_c_packet, approval_receipt,
                           *, dependent_c_receipt):
    """Return new rows after checking the exact approved case identities and source text."""
    root, base = Path(root), Path(base)
    old = validate_saved(base)
    packet = json.loads(Path(review_packet).read_text())
    held_packet = json.loads(Path(held_c_packet).read_text())
    approval = json.loads(Path(approval_receipt).read_text())
    c_recheck = json.loads(Path(dependent_c_receipt).read_text())
    if (approval['input_hashes']['base_gold_manifest'] != sha(base/'manifest.json')
            or approval['input_hashes']['six_C_draft_json'] != sha(review_packet)
            or approval['input_hashes']['three_held_C_draft_json'] != sha(held_c_packet)
            or approval['reviewer'] != 'Dion'
            or c_recheck.get('cv_id') != 'CV1' or c_recheck.get('job_id') != 'F00332'
            or c_recheck.get('relevance_0_3') != 3 or c_recheck.get('reviewer') != 'Dion'
            or c_recheck.get('decision') != 'retain_existing_C_after_B_recheck'
            or c_recheck.get('user_review_receipt_sha256') != sha(approval_receipt)
            or approval['approved']['F00332_dependent_C']['relevance_0_3'] != 3):
        raise ValueError('Approval or F00332 dependent-C receipt does not match this amendment')
    for rel, digest in old['source_hashes'].items():
        # Export-time documentation snapshots are not immutable data sources.
        if rel == 'evals/gold/README.md':
            continue
        if sha(root/rel) != digest:
            raise ValueError('Base protected source changed: '+rel)
    dev = set((root/'evals/splits/dev_job_ids.txt').read_text().splitlines())
    corpus = {row['final_cluster_id']: row for row in _read_jsonl(root/'data/processed/jobs_features.jsonl')}
    a = _read_jsonl(base/'extraction_gold.jsonl')
    b = _read_jsonl(base/'evidence_gold.jsonl')
    c = _read_jsonl(base/'relevance_gold.jsonl')
    held = json.loads((base/'held_records.json').read_text())
    bmap = {(row['cv_id'], row['job_id'], row['unit_no']): i for i, row in enumerate(b)}
    cmap = {(row['cv_id'], row['job_id']): i for i, row in enumerate(c)}
    approved_c = {(cv, job): value for cv, job, value in approval['approved']['six_C']}
    if len(approved_c) != len(packet['rows']) or len(approved_c) != 6:
        raise ValueError('Six distinct C approvals required')
    target_b = {(cv, job, unit): (before, after) for cv, job, unit, before, after in approval['approved']['F00332_B_edits']}
    if len(target_b) != 2 or set(target_b) != {('CV1', 'F00332', 'P30-U08'), ('CV1', 'F00332', 'P30-U15')}:
        raise ValueError('Only the two approved B edits are permitted')
    receipt_hash = sha(approval_receipt)
    changes = []
    for key, (before, after) in target_b.items():
        if key not in bmap or (before, after) != ('MATCH', 'PARTIAL'):
            raise ValueError('B amendment identity or value differs')
        prior = b[bmap[key]]
        if (prior['label'] != before or prior['review_status'] != 'approved'
                or prior['check_status'] != 'done' or prior['guideline_version'] != 'v1.3'):
            raise ValueError('B source is not the reviewed expected row')
        row = deepcopy(prior)
        row['label'] = after
        row['review_action'] = 'edited'
        row['review_note'] = ('Dion approved PARTIAL after source/CV review: cited evidence '
                              + ('shows learning activity, not mastery/drive across new techniques.' if key[2]=='P30-U08'
                                 else 'shows presentation of analysis, not an explicit actionable recommendation.'))
        row['historical_approval_provenance'] = prior['approval_provenance']
        row['approval_provenance'] = {'source':str(Path(approval_receipt).relative_to(root)),
            'review_kind':'case_specific_user_edit_after_model_assisted_review',
            'reviewer':'Dion','review_date':approval['review_date'],'reviewed_at':None,
            'receipt_sha256':receipt_hash,'prior_row_sha256':row_hash(prior)}
        row['amendment'] = {'before':before,'after':after,'reason':'D-054 case-specific evidence sufficiency correction'}
        b[bmap[key]] = row
        changes.append({'sheet':'B_Evidence','cv_id':key[0],'job_id':key[1],
                        'unit_no':key[2],'before':before,'after':after,'prior_row_sha256':row_hash(prior)})
    cv_targets = {row['cv_id']:row['cv_target'] for row in c if row.get('cv_target')}
    seen = set()
    for draft in packet['rows']:
        key = draft['cv_id'], draft['job_id']
        if key in seen or key not in approved_c or key in cmap or key[1] not in dev or key[0] not in {'CV1','CV2'}:
            raise ValueError('New C identity is duplicate, held, or outside the approved development scope')
        seen.add(key)
        source = corpus[key[1]]
        cv_path = root/draft['cv_source_path']
        if (draft['jd_text'] != source['description_clean'] or draft['source_record_id'] != source['record_id']
                or hashlib.sha256(draft['jd_text'].encode()).hexdigest() != draft['jd_sha256']
                or draft['exact_jd_excerpt'] not in draft['jd_text']
                or sha(cv_path) != draft['cv_source_sha256']
                or draft['exact_cv_excerpt'] not in cv_path.read_text()
                or draft['draft']['review_status'] != 'pending'
                or draft['human_review']['relevance_0_3'] is not None
                or draft['draft']['relevance_0_3'] != approved_c[key]):
            raise ValueError('Draft source, review state or approved C value differs')
        rec = {'cv_id':key[0],'cv_target':cv_targets[key[0]],'pilot_id':None,
               'job_id':key[1],'job_title':draft['job_title'],'relevance_0_3':approved_c[key],
               'main_reason':draft['draft']['main_reason'],'constraint_note':draft['draft']['constraint_note'],
               'label_source':'model_draft','review_status':'approved','review_action':'accepted',
               'review_note':'Dion explicitly approved this case after reviewing the full JD/CV; D-054.',
               'guideline_version':'v1.3','split':'development',
               'approval_provenance':{'source':str(Path(approval_receipt).relative_to(root)),
                   'review_kind':'user_review_of_model_assisted_draft','reviewer':'Dion',
                   'review_date':approval['review_date'],'reviewed_at':None,'receipt_sha256':receipt_hash,
                   'draft_row_sha256':row_hash(draft),'independent_annotation_claim':False},
               'compatibility':{'active_guideline':'v1.3','source_and_cv_checked':True,
                   'basis':'Exact source text, source ID and CV excerpt rechecked before promotion'},
               'jd_source_sha256':draft['jd_sha256'],
               'dependency_scope':'direct_ordinal_relevance_from_JD_and_CV;not_A_B_match_percentage',
               'selection_scope':'additional_original_top10_C_review;frozen_pool_unchanged'}
        c.append(rec)
        changes.append({'sheet':'C_Relevance','cv_id':key[0],'job_id':key[1],
                        'before':None,'after':approved_c[key],'draft_row_sha256':row_hash(draft)})
    if seen != set(approved_c):
        raise ValueError('Approved C values not all present in review packet')
    approved_held = {(cv, job): value for cv, job, value in approval['approved']['three_held_C']}
    if len(approved_held) != 3 or len(held_packet['rows']) != 3:
        raise ValueError('Exactly three held C case reviews required')
    resolved = []
    seen_held = set()
    for draft in held_packet['rows']:
        key = draft['cv_id'],draft['job_id']
        if key in seen_held or key not in approved_held or key in cmap or key[1] not in dev:
            raise ValueError('Held C review identity is duplicate or out of scope')
        seen_held.add(key)
        source = corpus[key[1]]
        cv_path = root/draft['cv_source_path']
        matches = [h for h in held if h['sheet']=='C_Relevance' and h['identity']==key[0]+'/'+key[1]]
        if (len(matches)!=1 or draft['jd_text']!=source['description_clean']
                or draft['source_record_id']!=source['record_id']
                or hashlib.sha256(draft['jd_text'].encode()).hexdigest()!=draft['jd_sha256']
                or draft['exact_jd_excerpt'] not in draft['jd_text']
                or sha(cv_path)!=draft['cv_source_sha256']
                or draft['exact_cv_excerpt'] not in cv_path.read_text()
                or draft['draft']['review_status']!='pending'
                or draft['human_review']['relevance_0_3'] is not None
                or draft['draft']['relevance_0_3']!=approved_held[key]
                or draft['historical_held_C_value']!=matches[0]['record']['relevance_0_3']):
            raise ValueError('Held C draft, original hold or approved value differs')
        if key==('CV1','F00369') and not draft['jd_text'].endswith('A portfolio of pro'):
            raise ValueError('F00369 source limitation changed')
        rec={'cv_id':key[0],'cv_target':cv_targets[key[0]],'pilot_id':matches[0]['record'].get('pilot_id'),
             'job_id':key[1],'job_title':draft['job_title'],'relevance_0_3':approved_held[key],
             'main_reason':draft['draft']['main_reason'],'constraint_note':draft['draft']['constraint_note'],
             'label_source':'model_draft','review_status':'approved','review_action':'accepted',
             'review_note':'Dion explicitly approved case-scoped direct JD/CV C review; A/B stay held (D-054).',
             'guideline_version':'v1.3','split':'development',
             'approval_provenance':{'source':str(Path(approval_receipt).relative_to(root)),
                 'review_kind':'case_scoped_user_review_of_model_assisted_draft','reviewer':'Dion',
                 'review_date':approval['review_date'],'reviewed_at':None,'receipt_sha256':receipt_hash,
                 'draft_row_sha256':row_hash(draft),'independent_annotation_claim':False},
             'compatibility':{'active_guideline':'v1.3','source_and_cv_checked':True,
                 'basis':'Fresh ordinal relevance from archived JD and synthetic CV; historical A/B not reused'},
             'jd_source_sha256':draft['jd_sha256'],
             'dependency_scope':'D-054_case_scoped_direct_C_only;A_B_remain_held',
             'source_limitation':draft['source_limitation'] if key==('CV1','F00369') else None,
             'historical_held_C_row_sha256':row_hash(matches[0]['record'])}
        c.append(rec)
        held.remove(matches[0])
        resolved.append({'original_held_record':matches[0],
                         'resolution':'D-054_direct_C_re_review_only;A_B_remain_held',
                         'new_C_row_sha256':row_hash(rec),'user_review_receipt_sha256':receipt_hash})
        changes.append({'sheet':'C_Relevance','cv_id':key[0],'job_id':key[1],
                        'before':'held_historical_C','after':approved_held[key],
                        'prior_held_C_row_sha256':row_hash(matches[0]['record'])})
    if seen_held!=set(approved_held):
        raise ValueError('Approved held C values not all present in review packet')
    target_c = c[cmap[('CV1','F00332')]]
    if target_c['relevance_0_3'] != 3 or 'cohort analysis' not in target_c['main_reason']:
        raise ValueError('F00332 dependent C changed or needs renewed review')
    target_c['dependency_recheck']={'source':str(Path(dependent_c_receipt).relative_to(root)),
         'receipt_sha256':sha(dependent_c_receipt),'reviewer':'Dion',
         'outcome':'relevance_3_and_original_reason_retained_after_two_B_PARTIAL_edits'}
    return {'A_Extraction':a,'B_Evidence':b,'C_Relevance':c}, changes, old, held, resolved


def promote_amendment(root, base, output, packet, held_c_packet, approval, dependent_c_receipt):
    """Write a fresh bundle atomically; historical bundle and workbook stay untouched."""
    root, base, output = Path(root), Path(base), Path(output)
    rows, changes, old, held, resolved = stage_approved_changes(root,base,packet,held_c_packet,approval,
                                                 dependent_c_receipt=dependent_c_receipt)
    if output.exists() or output.with_name(output.name+'.pending').exists():
        raise ValueError('Versioned amendment output already exists')
    tmp = output.with_name(output.name+'.pending')
    tmp.mkdir(parents=True,exist_ok=False)
    files = {}
    by_sheet = [('A_Extraction','extraction_gold.jsonl'),('B_Evidence','evidence_gold.jsonl'),
                ('C_Relevance','relevance_gold.jsonl')]
    for sheet,name in by_sheet:
        with (tmp/name).open('x') as f:
            for row in rows[sheet]: f.write(json.dumps(row,ensure_ascii=False)+'\n')
            f.flush();os.fsync(f.fileno())
        files[name]=sha(tmp/name)
    for name in ['logical_units.json','excluded_records.json',
                 'JD_coverage.json','pair_coverage.json']:
        data=(base/name).read_bytes()
        with (tmp/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        files[name]=sha(tmp/name)
    for name,value in [('held_records.json',held),('resolved_held_C_records.json',resolved)]:
        with (tmp/name).open('x') as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        files[name]=sha(tmp/name)
    receipt={'schema_version':'cp23-stage1-gold-amendment-v1','base_bundle':str(base.relative_to(root)),
             'base_manifest_sha256':sha(base/'manifest.json'),'review_packet':str(Path(packet).relative_to(root)),
             'review_packet_sha256':sha(packet),'user_review_receipt':str(Path(approval).relative_to(root)),
             'held_C_review_packet':str(Path(held_c_packet).relative_to(root)),
             'held_C_review_packet_sha256':sha(held_c_packet),
             'user_review_receipt_sha256':sha(approval),
             'dependent_C_recheck_receipt':str(Path(dependent_c_receipt).relative_to(root)),
             'dependent_C_recheck_sha256':sha(dependent_c_receipt),
             'changes':changes,'resolved_held_C_count':len(resolved),
             'A_B_holds_released':0,'workbook_changed':False,'historical_bundle_changed':False}
    with (tmp/'amendment_receipt.json').open('x') as f:
        json.dump(receipt,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    files['amendment_receipt.json']=sha(tmp/'amendment_receipt.json')
    manifest=deepcopy(old)
    manifest['files']=files
    manifest['exported_at']=datetime.now(timezone.utc).isoformat()
    manifest['source_hashes'].update({str(Path(base/'manifest.json').relative_to(root)):sha(base/'manifest.json'),
        str(Path(packet).relative_to(root)):sha(packet),
        str(Path(held_c_packet).relative_to(root)):sha(held_c_packet),
        str(Path(approval).relative_to(root)):sha(approval),
        str(Path(dependent_c_receipt).relative_to(root)):sha(dependent_c_receipt)})
    manifest['counts']['C_Relevance']['read']+=6
    manifest['counts']['C_Relevance']['approved']+=6
    manifest['counts']['C_Relevance']['approved_retained']+=6
    manifest['counts']['C_Relevance']['staged']+=9
    manifest['counts']['C_Relevance']['promoted']+=9
    manifest['counts']['C_Relevance']['held_retained']-=3
    manifest['selection_rule']='D-054 versioned amendment: six additional C, three direct C-only hold reviews, two F00332 B edits and dependent C recheck; pilot included once in base. A/B holds unchanged.'
    manifest['amendment_receipt_sha256']=files['amendment_receipt.json']
    manifest['workbook_sha256_meaning']='Hash of unchanged source workbook at base export; D-054 decisions came through a separate user-review receipt.'
    with (tmp/'manifest.json').open('x') as f:
        json.dump(manifest,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    validate_saved(tmp)
    # Recheck protected inputs immediately before the atomic rename.
    for rel,digest in manifest['source_hashes'].items():
        if rel == 'evals/gold/README.md':
            continue
        if sha(root/rel)!=digest:raise ValueError('Source changed during amendment: '+rel)
    os.rename(tmp,output)
    validate_saved(output)
    return manifest
