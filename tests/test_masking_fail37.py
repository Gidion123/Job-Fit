"""FAIL-37 / D-104 commit 2: the structural sanitizer and its deterministic backstops (no API, no provider).

The sanitizer is production code built from the D-104 contract; the calibration harness only scores it.
"""
import json
import hashlib
from pathlib import Path
import pickle
import time

import pytest

from jobfit.privacy import masking, structure
from jobfit.privacy.masking import VERSION_V2, MaskedPreview, OwnerMarks, mask_local, sanitize_upload
from jobfit.privacy.structure import BOUNDARY_NOT_FOUND, MASKING_FAILED, SanitizeRefused, classify
from jobfit.session.store import SessionStore
from tests import masking_calibration as mc

ROOT = Path(__file__).resolve().parents[1]
DEV_RECEIPT = ROOT / 'evals' / 'results' / 'fail37_structural_calibration_20261009_v2_dev.json'
HOLDOUT_RECEIPT = ROOT / 'evals' / 'results' / 'fail37_structural_calibration_20261009_v2_heldout_v1_first_pass.json'
CALIBRATION = [k for k, v in mc.HARD_GATES.items() if v[0] == 'calibration']
HEADER = 'Alice Example\nalice.example@example.com | +62 800-0000-0901\n'


def refused(text, **kw):
    with pytest.raises(SanitizeRefused) as exc:
        sanitize_upload(text, **kw)
    return exc.value


# --- dev calibration (the only tuning set) -------------------------------------------------------------

def test_every_dev_hard_gate_passes_and_the_dev_receipt_is_reproducible():
    cases = mc.load_cases('dev')
    results = mc.evaluate(cases, mc.v2_adapter)
    assert all(r.correct for r in results if r.case.gated)
    table = mc.gate_table(results, v1_golden_ok=mc.v1_golden_ok(cases))
    assert all(table[g]['status'] == 'PASS' for g in CALIBRATION), table
    assert table['mask_local_v1_byte_identical']['status'] == 'PASS'
    receipt = json.loads(DEV_RECEIPT.read_text(encoding='utf-8'))
    assert receipt == mc.build_receipt('dev', 'v2', mc.v2_adapter, date=receipt['date'])
    assert receipt['sanitizer_sha256'] == mc.sanitizer_sha256()


def test_the_first_pass_holdout_receipt_matches_the_locked_holdout_and_this_sanitizer():
    """The single approved holdout run is recorded, never re-run here; a sanitizer change shows up."""
    receipt = json.loads(HOLDOUT_RECEIPT.read_text(encoding='utf-8'))
    assert receipt['holdout_run'] == 'first_pass' and receipt['adapter'] == 'v2'
    assert receipt['fixture_sha256'] == 'b892c45f6b100b352b36da2be0ba5ea78286757f6056609647c42227e97e3cf9'
    assert receipt['sanitizer_sha256'] == mc.sanitizer_sha256()


def test_the_production_sanitizer_does_not_depend_on_the_test_harness():
    for path in (ROOT / 'src' / 'jobfit' / 'privacy').glob('*.py'):
        source = path.read_text(encoding='utf-8')
        assert 'masking_calibration' not in source and 'import tests' not in source and 'from tests' not in source


# --- structural boundary ---------------------------------------------------------------------------------

@pytest.mark.parametrize('line,kind', [
    ('## Professional Summary', 'summary'), ('PERSONAL PROFILE', 'summary'), ('Profil Pribadi:', 'summary'),
    ('**About Me**', 'summary'), ('##   Work   Experience   ', 'evidence'), ('__Skills__', 'evidence'),
    ('### Skills and Tools', 'evidence'), ('Pengalaman Kerja:', 'evidence'), ('# CERTIFICATIONS', 'evidence'),
    ('Volunteering', 'evidence'), ('Interests', 'privacy'), ('Organisasi', 'privacy'), ('Kontak Darurat', 'privacy'),
    ('Contact: [EMAIL]', None), ('Experience: Data Analyst at PT Contoh', None), ('- Skills', None),
    ('Side Projects', None), ('x' * 61, None),
])
def test_heading_classification_is_exact_and_bounded(line, kind):
    assert classify(line) == kind


def test_summary_takes_precedence_and_is_itself_dropped():
    text = (HEADER + 'Senior Machine Learning Engineer\nPython | RAG | FastAPI\n## Skills\nExcel\n'
            '## Professional Summary\nML engineer specialising in RAG.\n## Experience\nML Engineer, Contoh Labs\n'
            '## Skills\nPython\n')
    preview = sanitize_upload(text)
    assert preview.text == '## Experience\nML Engineer, Contoh Labs\n## Skills\nPython\n'
    assert preview.removed['summary_sections'] == 1 and preview.removed['header_lines'] == 6


def test_without_summary_the_first_evidence_section_starts_and_privacy_sections_are_dropped():
    text = (HEADER + '## Interests\nChess\n## Projects\nRoute Planner\n## Organizations\nStudent Union\n'
            '## Hobbies Corner\nCycling\n## Education\nUniversitas Contoh\n## References\nBudi Hartono\n')
    preview = sanitize_upload(text)
    assert preview.text == '## Projects\nRoute Planner\n## Education\nUniversitas Contoh'    # trailing section dropped
    assert preview.removed['organizations'] == 1 and preview.removed['references'] == 1


@pytest.mark.parametrize('text', [
    '', '   \n', 'Just some prose about me.\nNo headings at all.\n', HEADER + '## Summary\nGreat engineer.\n',
    '## Profile\nKeen.\n## References\nOn request\n## Interests\nChess\n', '## Interests\nChess\n## Organisasi\nBEM\n',
    'Experience: Data Analyst\nSkills: SQL\n', '## Experience\n\n## Skills\n',
])
def test_no_evidence_start_fails_closed(text):
    assert refused(text).code == BOUNDARY_NOT_FOUND


# --- backstops -------------------------------------------------------------------------------------------

def test_contact_patterns_are_masked_in_retained_text():
    text = ('## Experience\nAnalyst, mail ops@example.org or +62 800-0000-0902\nNIK: 0000000000000903\n'
            'See linkedin.com/in/example-x and github.com/example-y and github.com/example-y-z/repo-name\n')
    out = sanitize_upload(text).text
    assert out == ('## Experience\nAnalyst, mail [EMAIL] or [PHONE]\nNIK: [IDENTITY_NUMBER]\n'
                   'See [PROFILE] and [PROFILE] and github.com/example-y-z/repo-name\n')


def test_v2_profile_pattern_never_stops_inside_a_hyphenated_handle():
    assert masking._PATTERNS['profile'].search('github.com/example-sari/repo').group() == 'github.com/example'
    assert masking._PATTERNS_V2['profile'].search('github.com/example-sari/repo') is None


@pytest.mark.parametrize('line,expected', [
    ('jl. melati no. 12', '[ADDRESS]'),
    ('JL. MELATI NO. 12 RT 03/RW 05', '[ADDRESS]'),
    ('Alamat: jl. mawar no. 5', 'Alamat: [ADDRESS]'),
    ('Address: Jl. Mawar No. 12, Medan', 'Address: [ADDRESS]'),
    ('- Perumahan Griya Contoh Blok C2 No. 7', '- [ADDRESS]'),
    ('Worked from Jl. Sudirman No. 1, leading the backend migration',
     'Worked from [ADDRESS], leading the backend migration'),
    ('Opened a branch at Jl. Gajah Mada No. 8 (Medan), growing sales', 'Opened a branch at [ADDRESS] (Medan), growing sales'),
    ('Relocated to 221B Baker Street; cut commute time', 'Relocated to [ADDRESS]; cut commute time'),
    ('Data Analyst, PT Contoh, Jakarta (Hybrid)', 'Data Analyst, PT Contoh, Jakarta (Hybrid)'),
    ('Mentored a gang of four interns', 'Mentored a gang of four interns'),
    ('Alamat: [ADDRESS]', 'Alamat: [ADDRESS]'),
])
def test_bounded_address_backstop_without_geography_data(line, expected):
    assert sanitize_upload(f'## Experience\n{line}\n').text == f'## Experience\n{expected}\n'


@pytest.mark.parametrize('line,expected', [
    ('Supervisor: Budi Santoso', 'Supervisor: [NAME]'),
    ('- Mentor: Rina Kartika', '- Mentor: [NAME]'),
    ('PIC: Andi Saputra (client side)', 'PIC: [NAME] (client side)'),
    ('Atasan Langsung: Hendro Wibisono', 'Atasan Langsung: [NAME]'),
    ('Supervisor: Head of Data Science', 'Supervisor: Head of Data Science'),
    ('Atasan: Kepala Divisi Data', 'Atasan: Kepala Divisi Data'),
    ('PIC: Data Engineering Team', 'PIC: Data Engineering Team'),
    ('Mentor at Dicoding for the data class', 'Mentor at Dicoding for the data class'),
    ('Supervisor: [NAME]', 'Supervisor: [NAME]'),
])
def test_strong_labels_mask_only_person_name_values(line, expected):
    assert sanitize_upload(f'## Experience\n{line}\n').text == f'## Experience\n{expected}\n'


def test_owner_repeat_is_multi_token_only_and_spares_single_token_collisions():
    text = (HEADER + '## Projects\nBuilt by Alice Example; Alice also wrote docs. EXAMPLE ALICE is not the order.\n'
            'Analyst, PT Example Pangan\n')
    preview = sanitize_upload(text)
    assert preview.owner_repeat_guard == 'active'
    assert preview.text == ('## Projects\nBuilt by [NAME]; Alice also wrote docs. EXAMPLE ALICE is not the order.\n'
                            'Analyst, PT Example Pangan\n')


def test_header_label_is_the_owner_but_an_emergency_contact_label_never_is():
    text = ('Name: Alice Example\nPhone: +62 800-0000-0904\nEmergency Contact\nName: Bob Example\n'
            '## Experience\nWorked with Alice Example and Bob Example.\n')
    assert sanitize_upload(text).text == '## Experience\nWorked with [NAME] and Bob Example.\n'
    only_emergency = 'Emergency Contact\nName: Bob Example\nbob@example.com\n## Experience\nBob Example led QA.\n'
    preview = sanitize_upload(only_emergency)
    assert preview.owner_repeat_guard == 'not_established' and 'Bob Example' in preview.text


def test_an_unlabelled_first_line_alone_is_not_enough_to_identify_the_owner():
    preview = sanitize_upload('Alice Example\n## Experience\nAlice Example built dashboards.\n')
    assert preview.owner_repeat_guard == 'not_established' and 'Alice Example' in preview.text
    assert any('could not be identified' in w for w in preview.warnings)


def test_a_reintroduced_name_or_handle_is_masked_again_with_the_upload_marks():
    upload = sanitize_upload(HEADER + 'github.com/example-alice\n## Experience\nAnalyst\n')
    edited = upload.text + 'Lead: Alice Example, repo github.com/example-alice/etl\n'
    again = sanitize_upload(edited, marks=upload.marks)
    assert again.text.endswith('Lead: [NAME], repo github.com/[PROFILE]/etl\n')
    assert 'Alice Example' in sanitize_upload(edited).text           # without marks there is no owner evidence


# --- output contract, idempotency and fail-closed --------------------------------------------------------

def test_the_preview_is_a_digest_valid_v2_preview_accepted_by_the_session_store():
    preview = sanitize_upload(HEADER + '## Experience\nAnalyst at Contoh, ops@example.org\n')
    assert isinstance(preview, MaskedPreview) and preview.version == VERSION_V2
    assert preview.digest == hashlib.sha256(preview.text.encode()).hexdigest()
    assert preview.counts == {'email': 1}
    store = SessionStore()
    store.set_preview(store.create(), preview)


def test_owner_marks_hold_no_raw_value_and_never_serialize():
    preview = sanitize_upload(HEADER + '## Experience\nAnalyst\n')
    marks = preview.marks
    assert repr(marks).startswith('OwnerMarks(<') and 'Alice' not in repr(marks) and 'Alice' not in repr(preview)
    assert not any(b'alice' in d for d in marks._digests)
    with pytest.raises(TypeError):
        pickle.dumps(marks)
    with pytest.raises(TypeError):
        json.dumps(marks)
    assert 'marks' not in repr(preview)


def test_sanitizing_the_output_again_changes_nothing():
    text = (HEADER + '## Summary\nx\n## Experience\nSupervisor: Budi Santoso\nAlamat: Jl. Mawar No. 1\n'
            'Built by Alice Example, ops@example.org\n')
    first = sanitize_upload(text)
    assert sanitize_upload(first.text, marks=first.marks).text == first.text


def test_normalization_matches_the_contract():
    preview = sanitize_upload('## Experi​ence\nCafé  pricing\r\n')
    assert preview.text == '## Experience\nCafé  pricing\n'
    assert refused('## Experience\nbad \ud800 text\n').code == MASKING_FAILED
    assert refused(None).code == MASKING_FAILED
    assert refused('## Experience\nx\n', marks='not marks').code == MASKING_FAILED


def test_an_internal_error_fails_closed_without_carrying_any_text(monkeypatch):
    def boom(text):
        raise RuntimeError('SECRET CV TEXT alice.example@example.com')
    monkeypatch.setattr(structure, 'split_structure', boom)
    exc = refused('## Experience\nAnalyst\n')
    assert exc.code == MASKING_FAILED and str(exc) == MASKING_FAILED
    assert exc.__cause__ is None and exc.__context__ is None


def test_mask_local_v1_is_unchanged_by_the_v2_additions():
    preview = mask_local('Rina Example\nrina@example.com', reviewed_identifiers={'name': ('Rina Example',)})
    assert preview.text == '[NAME]\n[EMAIL]' and preview.version == 'local-pattern-masking-v1'
    assert preview.removed == {} and preview.owner_repeat_guard is None and preview.marks is None


# --- catastrophic-backtracking guard (detects exponential/quadratic behaviour, not runner speed) ----------

N = 100_000
H = 'Sari Wulandari\nsari.wulandari@example.com\n## Experience\n'
ADVERSARIAL = {
    'street_inline': H + 'Worked at Jl. ' + 'Ab ' * (N // 3) + 'x',
    'email_domain': H + 'x@' + 'a.' * (N // 2) + '1',
    'phone_starts': H + '08 ' * (N // 3) + 'a',
    'owner_windows': H + 'Sari Wulandari ' * (N // 15),
    'url_dots': H + 'a.' * (N // 2) + '/x',
    'label_spaces': H + 'Supervisor: a' + ' ' * N + 'b',
    'address_label_spaces': H + 'Alamat: a' + ' ' * N + 'b',
    'owner_label_spaces': 'Nama: a' + ' ' * N + 'b\n## Skills\nPython',
    'intl_street': H + '1 ' + 'A' * N + ' Street',
    'rt_tokens': H + 'RT ' * (N // 3),
    'headings': '## Summary\n' * (N // 22) + '## References\n' * (N // 30) + '## Skills\nPython',
}


@pytest.mark.parametrize('name', sorted(ADVERSARIAL))
def test_100k_adversarial_inputs_finish_within_the_hard_bound(name):
    started = time.perf_counter()
    try:
        sanitize_upload(ADVERSARIAL[name])
    except SanitizeRefused:
        pass
    assert time.perf_counter() - started < 3.0
