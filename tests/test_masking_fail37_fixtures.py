"""FAIL-37 / D-104 commit 1: locked holdout, fixture integrity, harness semantics, v1 golden, v1 baseline.

No sanitizer exists yet. The annotation oracle checks the harness itself; no detector runs on the
locked holdout. See tests/masking_calibration.py for the expected-output contract.
"""
import json
from pathlib import Path
import re
import unicodedata

import pytest

from scripts import report_fail37_masking as report
from tests import masking_calibration as mc

HELDOUT_V1_SHA256 = 'b892c45f6b100b352b36da2be0ba5ea78286757f6056609647c42227e97e3cf9'
BASELINE = Path(__file__).resolve().parents[1] / 'evals' / 'results' / \
    'fail37_structural_calibration_20261009_v1_baseline.json'
MANIFEST = mc.FIXTURES / 'manifest.json'
CALIBRATION_GATES = [k for k, v in mc.HARD_GATES.items() if v[0] == 'calibration']


def manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def all_cases():
    return {name: mc.load_cases(name) for name in mc.SETS}


# --- the locked holdout ----------------------------------------------------------------------------------

def test_the_holdout_is_locked_by_a_double_pin():
    actual = mc.sha256_file(mc.fixture_path('heldout'))
    assert actual == HELDOUT_V1_SHA256 == manifest()['sets']['heldout_v1']['sha256']


def test_the_manifest_matches_the_fixtures_and_the_contract():
    m, cases = manifest(), all_cases()
    assert m['schema'] == mc.SCHEMA and m['harness'] == mc.HARNESS_VERSION and m['normalization'] == mc.NORMALIZATION
    assert m['sets']['dev']['sha256'] == mc.sha256_file(mc.fixture_path('dev'))
    for key, name in (('dev', 'dev'), ('heldout_v1', 'heldout')):
        assert m['sets'][key]['cases'] == len(cases[name])
        assert m['sets'][key]['families'] == len({c.family for c in cases[name]})
    assert 'not a truly blind' in m['sets']['heldout_v1']['role']


# --- fixture integrity -----------------------------------------------------------------------------------

SYNTHETIC_EMAIL = re.compile(r'[\w.+-]+@example\.(?:com|org|net)')
SYNTHETIC_ID = re.compile(r'[A-Z]?0{4,}\d{0,4}')


def _synthetic(ann, span):
    text = mc.span_text(ann, span).strip()
    digits = re.sub(r'\D', '', text)
    return {'email': lambda: SYNTHETIC_EMAIL.fullmatch(text),
            'phone': lambda: digits.startswith(('628000000', '08000000')),
            'id': lambda: SYNTHETIC_ID.fullmatch(text),
            'profile': lambda: 'example' in text}.get(span.kind, lambda: True)()


@pytest.mark.parametrize('set_name', sorted(mc.SETS))
def test_every_case_is_well_formed_and_its_expected_output_is_consistent(set_name):
    cases = mc.load_cases(set_name)
    assert len({c.id for c in cases}) == len(cases)
    for c in cases:
        assert c.category in mc.CATEGORIES and c.lang in mc.LANGS, c.id
        assert c.expect in ('ok', mc.BOUNDARY_CODE), c.id
        assert (c.category in mc.FAIL_CLOSED_CATEGORIES) == (c.expect != 'ok'), c.id
        assert c.gated or c.note, f'{c.id}: a residual case needs a note'
        parts = [p for p in (c.upload, c.prepend, c.append) if p]
        for ann in parts:
            for span in ann.of('PII'):
                assert _synthetic(ann, span), f'{c.id}: non-synthetic {span.kind}'
        if c.expect != 'ok':
            assert c.expect_start is None and not (c.prepend or c.append), c.id
            continue
        expected = c.expected_edit() if (c.prepend or c.append) else c.expected()
        lines = {line.strip() for line in mc.compare_canon(expected).split('\n')}
        assert mc.compare_canon(c.expected()).split('\n')[0] == c.expect_start, c.id
        for ann in parts:
            for kind, variants in mc.drop_line_variants(ann).items():
                assert not variants & lines, f'{c.id}: a {kind} DROP line also appears in the expected output'
            for span in ann.of('PII'):
                assert mc.span_text(ann, span).strip() not in expected, f'{c.id}: PII text in expected output'
            for span in ann.of('KEEP'):
                if not span.in_drop:
                    assert mc.span_text(ann, span) in expected, f'{c.id}: KEEP text missing from expected'


def test_dev_and_holdout_are_independent_compositions_covering_every_category():
    dev, held = mc.load_cases('dev'), mc.load_cases('heldout')
    assert not {c.id for c in dev} & {c.id for c in held}
    assert not {c.family for c in dev} & {c.family for c in held}
    for cases in (dev, held):
        assert len({c.family for c in cases}) == len(cases)
        assert {c.category for c in cases} == mc.CATEGORIES
        assert {c.lang for c in cases} == mc.LANGS
    for name in CALIBRATION_GATES:
        _, _, select, _ = mc.HARD_GATES[name]
        for cases in (dev, held):
            results = mc.evaluate(cases, mc.OracleAdapter(cases))
            assert any(select(r) for r in results if r.case.gated), f'{name} has no cases'


# --- annotation isolation --------------------------------------------------------------------------------

def test_no_annotation_marker_ever_reaches_an_adapter():
    seen = []

    def recording(text, marks=None):
        seen.append(text)
        return mc.OracleAdapter(cases)(text, marks)

    for cases in all_cases().values():
        for c in cases:
            for ann in (c.upload, c.prepend, c.append):
                if ann:
                    assert not any(m in ann.source for m in ('[[', ']]', 'DROP:', 'PII:', 'KEEP:', '[[/'))
        mc.evaluate(cases, recording)
    assert seen and not any('[[' in t or ']]' in t for t in seen)
    with pytest.raises(mc.AnnotationLeak):
        mc.call(mc.identity_adapter, 'x [[PII:email]]a@example.com[[/PII]]')


@pytest.mark.parametrize('text', [
    '[[PII:mystery]]x[[/PII]]',                                   # unknown kind
    '[[DROP:header]]x\n',                                          # unclosed
    'a[[DROP:header]]x\n[[/DROP]]',                                # DROP not at a line start
    '[[DROP:header]]x[[/DROP]]y\n',                                # DROP not at a line end
    '[[DROP:header]][[DROP:summary]]x\n[[/DROP]][[/DROP]]',        # nested DROP
    '[[PII:name]][[KEEP:title]]x[[/KEEP]][[/PII]]',                # nested PII/KEEP
    '[[KEEP:title]]e[[/KEEP]]́',                               # combining mark at a boundary
    'stray ]] marker',                                             # annotation syntax left in source
])
def test_the_parser_rejects_malformed_annotations(text):
    with pytest.raises(mc.FixtureError):
        mc.parse_annotated(text)


# --- expected-output semantics and the DROP false-pass regression -----------------------------------------

def test_drop_has_precedence_over_nested_pii_and_keep():
    ann = mc.parse_annotated('[[DROP:summary]]AI Engineer - [[PII:email]]john@example.com[[/PII]] '
                             '[[KEEP:skill]]RAG[[/KEEP]]\n[[/DROP]]## Experience\nMail [[PII:email]]a@example.com'
                             '[[/PII]], [[KEEP:tech]]FastAPI[[/KEEP]]\n')
    assert mc.expected_text(ann) == '## Experience\nMail [EMAIL], FastAPI\n'


def _keep_drops_render(ann):
    """A broken sanitizer: masks every PII (also inside DROP) but keeps the DROP text."""
    pii = {s.start: s for s in ann.of('PII')}
    out, i = [], 0
    while i < len(ann.source):
        if i in pii:
            out.append(mc.PLACEHOLDER[pii[i].kind])
            i = pii[i].end
        else:
            out.append(ann.source[i])
            i += 1
    return mc.source_normalize(''.join(out))


def test_masking_nested_pii_while_keeping_the_rest_of_a_drop_block_fails():
    case = mc.Case(id='regression', family='regression', category='summary_delimiter', lang='en', expect='ok',
                   expect_start='## Experience', upload=mc.parse_annotated(
                       '[[DROP:summary]]## Summary\nAI Engineer - [[PII:email]]john@example.com[[/PII]]\n'
                       '[[/DROP]]## Experience\nData Analyst\n'))
    broken = lambda text, marks=None: (_keep_drops_render(case.upload), marks)   # noqa: E731
    assert 'AI Engineer - [EMAIL]' in broken(case.upload.source)[0]
    result = mc.evaluate_case(case, broken)
    assert not result.correct and result.drop_leaks['summary'] >= 1 and not result.pii_leaks
    for cases in all_cases().values():
        table = {c.upload.source: _keep_drops_render(c.upload) for c in cases}
        results = mc.evaluate([c for c in cases if c.expect == 'ok' and not (c.prepend or c.append)],
                              lambda text, marks=None: (table.get(text, text), marks))
        nested = [r for r in results if any(s.in_drop for s in r.case.upload.of('PII'))]
        assert nested and not any(r.correct for r in nested)
        assert all(sum(r.drop_leaks.values()) for r in nested)


@pytest.mark.parametrize('set_name', sorted(mc.SETS))
def test_the_annotation_oracle_passes_every_calibration_gate(set_name):
    cases = mc.load_cases(set_name)
    results = mc.evaluate(cases, mc.OracleAdapter(cases))
    assert all(r.correct for r in results)
    table = mc.gate_table(results)
    assert all(table[g]['status'] == 'PASS' for g in CALIBRATION_GATES), table
    assert {k for k, v in table.items() if v['status'] == 'NOT_APPLICABLE_YET'} == \
        {'no_summary_in_provider_payload', 'raw_canary_sinks_zero'}
    assert table['mask_local_v1_byte_identical']['status'] == 'NOT_EVALUATED'


def test_identity_and_keep_dropping_sanitizers_fail():
    cases = mc.load_cases('dev')
    table = mc.gate_table(mc.evaluate(cases, mc.identity_adapter))
    for gate in ('exact_expected_output', 'header_removed', 'summary_content_removed', 'privacy_sections_removed',
                 'contact_pattern_leakage_zero', 'no_start_fails_closed'):
        assert table[gate]['status'] == 'FAIL', gate
    oracle = mc.OracleAdapter(cases)
    victim = next(c for c in cases if c.id == 'dev-ev-01')
    lost = mc.span_text(victim.upload, victim.upload.of('KEEP')[0])

    def drops_keep(text, marks=None):
        out = oracle.table.get(text, text)              # unknown input (its own output): pass through
        return out.replace(lost, ''), marks
    result = mc.evaluate_case(victim, drops_keep)
    assert not result.correct and result.keep_destroyed >= 1


# --- the expected-output normalization contract -----------------------------------------------------------

def test_source_normalization_contract():
    assert mc.source_normalize('Da​ta﻿') == 'Data'                       # category Cf removed
    assert mc.source_normalize('Café') == 'Café'                         # decomposed -> NFC
    assert mc.source_normalize('a\r\nb\rc') == 'a\nb\nc'
    with pytest.raises(ValueError):
        mc.source_normalize('bad \ud800 text')
    assert mc.compare_canon('\n\nA  b  \n\n\n\nC\t\n\n') == 'A  b\n\nC'            # inner spaces and case kept


def test_the_unicode_fixture_expects_the_normalized_form_and_rejects_other_forms():
    case = next(c for c in mc.load_cases('dev') if c.id == 'dev-ad-02')
    expected = case.expected()
    assert '​' not in expected and 'Café Contoh' in expected and 'Data Analyst' in expected
    assert 'a  dashboard' in expected and 'menu  pricing' in expected                 # KEEP otherwise unchanged
    assert mc.evaluate_case(case, mc.OracleAdapter([case])).correct
    rendered = mc.annotation_render(case.upload)                                      # before normalization
    wrong = {
        'keeps_cf': rendered,
        'nfd': unicodedata.normalize('NFD', expected),
        'casefolded': expected.casefold(),
        'inner_whitespace_collapsed': re.sub(r'[ \t]+', ' ', expected),
    }
    for name, output in wrong.items():
        assert output != expected, name
        result = mc.evaluate_case(case, lambda text, marks=None, o=output: (o, marks))
        assert not result.correct, name


# --- mask_local v1 golden and the reproducible v1 baseline (dev only) ------------------------------------

def test_mask_local_v1_output_is_byte_identical_to_the_pinned_golden():
    pinned = manifest()['v1_golden']
    assert {'CV1_with_cp2_hint', 'CV2_with_cp2_hint', 'CV1_no_hint', 'CV2_no_hint'} <= set(pinned)
    current = mc.v1_golden_digests(mc.load_cases('dev'))
    assert {k: current.get(k) for k in pinned} == pinned
    assert mc.v1_golden_ok(mc.load_cases('dev'))


def test_the_v1_baseline_receipt_is_reproducible_and_shows_the_gap():
    receipt = json.loads(BASELINE.read_text(encoding='utf-8'))
    assert receipt == mc.build_receipt('dev', 'v1', mc.v1_adapter, date=receipt['date'])
    assert receipt['set'] == 'dev' and receipt['adapter'] == 'v1'
    gates = receipt['gates']
    assert gates['mask_local_v1_byte_identical']['status'] == 'PASS'
    for gate in ('exact_expected_output', 'header_removed', 'summary_delimiter_detected', 'summary_content_removed',
                 'privacy_sections_removed', 'interests_removed', 'organizations_removed', 'no_start_fails_closed',
                 'owner_repeat_masked', 'supported_address_masked', 'labelled_person_masked'):
        assert gates[gate]['status'] == 'FAIL', gate
    assert gates['no_summary_in_provider_payload']['status'] == 'NOT_APPLICABLE_YET'
    text = BASELINE.read_text(encoding='utf-8')
    assert '@example' not in text and 'Wulandari' not in text                         # counts and ids only


# --- holdout discipline -----------------------------------------------------------------------------------

@pytest.mark.parametrize('adapter', sorted(report.ADAPTERS))
def test_the_holdout_execution_gate_is_closed_for_every_adapter(adapter, capsys):
    """The single first-pass D-104 run happened at 8257f17; no detector may run on the holdout again."""
    assert mc.HOLDOUT_RUN_ALLOWED == frozenset()
    for single_run in (False, True):
        with pytest.raises(PermissionError):
            mc.build_receipt('heldout', adapter, report.ADAPTERS[adapter], date='2026-10-09', single_run=single_run)
    for flags in ([], ['--single-holdout-run']):
        assert report.main(['--adapter', adapter, '--set', 'heldout', '--date', '2026-10-09', *flags]) == 2
        assert 'refused' in capsys.readouterr().err
