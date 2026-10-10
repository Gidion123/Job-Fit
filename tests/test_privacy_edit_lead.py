"""D-104 edited previews: bounded professional headings and a strict first-Summary boundary."""
import pytest

from jobfit.privacy.masking import sanitize_upload
from jobfit.privacy.structure import BOUNDARY_NOT_FOUND, SanitizeRefused

CV = """Gidion Contoh Depari
gidion.contoh@example.com | +62 812 0000 0000
SUMMARY
AI engineer moving from marketing analytics.
TECHNICAL SKILLS
Python, SQL, Docker
Machine Learning: Regression, Classification
WORK EXPERIENCE
Co-Founder, Contoh Studio, 2020 - 2026
Increased revenue by 80%.
EDUCATION
Bachelor of Information Systems, 2025"""


@pytest.fixture
def preview():
    p = sanitize_upload(CV)
    assert p.text.startswith('TECHNICAL SKILLS') and 'Gidion' not in p.text and 'example.com' not in p.text
    return p


@pytest.mark.parametrize('heading', ['TECHNICAL SKILLS & TOOLS', 'TECHNICALS SKILLS', 'TECHNICAL SKILLS: Python',
                                     'Tech Stack'])
def test_a_reworded_first_heading_keeps_its_section(preview, heading):
    edited = preview.text.replace('TECHNICAL SKILLS', heading).replace('Python, SQL, Docker', 'Python, SQL, Docker, GCP')
    out = sanitize_upload(edited, marks=preview.marks, edited=True)
    assert out.text.split('\n')[0] == heading
    assert 'Python, SQL, Docker, GCP' in out.text and 'Machine Learning: Regression' in out.text
    assert out.removed['header_lines'] == 0


def test_private_lead_is_dropped_before_a_reworded_professional_heading(preview):
    edited = ('Date of Birth: 01 January 1990\nPersonal Details: Other Example\n' +
              preview.text.replace('TECHNICAL SKILLS', 'TECHNICAL SKILLS & TOOLS'))
    out = sanitize_upload(edited, marks=preview.marks, edited=True)
    assert out.text.startswith('TECHNICAL SKILLS & TOOLS\nPython, SQL, Docker')
    assert 'Machine Learning: Regression' in out.text and 'Co-Founder' in out.text
    assert 'Date of Birth' not in out.text and '01 January 1990' not in out.text
    assert 'Personal Details' not in out.text and 'Other Example' not in out.text


def test_unclassified_lead_is_dropped_before_a_reworded_professional_heading(preview):
    edited = 'Private note that must not leave the preview\n' + preview.text.replace(
        'TECHNICAL SKILLS', 'TECHNICAL SKILLS & TOOLS')
    out = sanitize_upload(edited, marks=preview.marks, edited=True)
    assert out.text.startswith('TECHNICAL SKILLS & TOOLS\nPython, SQL, Docker')
    assert 'Private note' not in out.text


def test_private_inline_section_is_dropped_after_a_reworded_heading(preview):
    edited = preview.text.replace('TECHNICAL SKILLS', 'TECHNICAL SKILLS & TOOLS')
    edited = edited.replace('WORK EXPERIENCE', 'Personal Details: Other Example\n'
                            'Date of Birth: 01 January 1990\nWORK EXPERIENCE')
    out = sanitize_upload(edited, marks=preview.marks, edited=True)
    assert 'Python, SQL, Docker' in out.text and 'Co-Founder' in out.text
    assert 'Personal Details' not in out.text and 'Other Example' not in out.text
    assert 'Date of Birth' not in out.text and '01 January 1990' not in out.text


def test_private_only_edit_is_refused(preview):
    with pytest.raises(SanitizeRefused) as exc:
        sanitize_upload('Date of Birth: 01 January 1990\nPersonal Details: Other Example',
                        marks=preview.marks, edited=True)
    assert exc.value.code == BOUNDARY_NOT_FOUND


def test_an_upload_still_removes_everything_before_the_first_section():
    out = sanitize_upload(CV.replace('TECHNICAL SKILLS', 'TECHNICAL SKILLS & TOOLS'))
    assert out.text.startswith('WORK EXPERIENCE') and 'Gidion' not in out.text      # unchanged upload boundary


@pytest.mark.parametrize('lead', ['Gidion Contoh Depari\ngidion.contoh@example.com',
                                  'Phone: +62 812 0000 0000', 'github.com/gidion-contoh',
                                  'Alamat: Jl. Contoh No. 5, Medan'])
def test_identity_data_typed_before_the_first_heading_is_still_removed(preview, lead):
    out = sanitize_upload(lead + '\n' + preview.text, marks=preview.marks, edited=True)
    assert out.text.startswith('TECHNICAL SKILLS')
    for value in ('Gidion', 'example.com', '812 0000', 'gidion-contoh', 'Jl. Contoh'):
        assert value not in out.text


def test_a_pasted_full_cv_in_the_edit_box_is_sanitized_like_an_upload(preview):
    out = sanitize_upload(CV, marks=preview.marks, edited=True)
    assert out.text == preview.text


def test_summary_and_privacy_sections_are_still_dropped_in_an_edit(preview):
    edited = preview.text + '\nINTERESTS\nHiking and photography.'
    edited = edited.replace('WORK EXPERIENCE', 'PROFILE\nA private self-description.\nWORK EXPERIENCE')
    out = sanitize_upload(edited, marks=preview.marks, edited=True)
    assert 'Hiking' not in out.text and 'private self-description' not in out.text
    assert out.text.startswith('WORK EXPERIENCE') and 'Co-Founder' in out.text
    assert 'TECHNICAL SKILLS' not in out.text and 'Python, SQL, Docker' not in out.text


def test_an_edit_without_any_section_heading_is_still_refused(preview):
    with pytest.raises(SanitizeRefused) as exc:
        sanitize_upload('Just some text without sections.\nMore text here.', marks=preview.marks, edited=True)
    assert exc.value.code == BOUNDARY_NOT_FOUND
