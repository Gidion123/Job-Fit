"""An edit of a sanitized preview keeps its first section when its heading is reworded (D-104 edit path).

Regression: the first section of the preview was TECHNICAL SKILLS; rewording its heading ("TECHNICAL
SKILLS & TOOLS", a typo, or text on the heading line) made the whole section look like an identity
header, so it was silently removed. Identity data before the first heading is still removed.
"""
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
    assert 'TECHNICAL SKILLS' in out.text and 'Co-Founder' in out.text


def test_an_edit_without_any_section_heading_is_still_refused(preview):
    with pytest.raises(SanitizeRefused) as exc:
        sanitize_upload('Just some text without sections.\nMore text here.', marks=preview.marks, edited=True)
    assert exc.value.code == BOUNDARY_NOT_FOUND
