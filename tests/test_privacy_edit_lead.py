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


# --- an edited first section with any reworded heading is kept when it still holds approved lines ----------

@pytest.mark.parametrize('heading', ['TECH SKILLS', 'Keahlian Teknis', 'TECHINCAL SKILLS', 'Technical Skill',
                                     'TECHNICAL SKILLS (Python, SQL)', 'TOOLS & TECHNOLOGIES'])
def test_an_edited_first_section_with_a_reworded_heading_is_kept(preview, heading):
    edited = preview.text.replace('TECHNICAL SKILLS', heading).replace('Python, SQL, Docker',
                                                                      'Python, SQL, Docker, FastAPI')
    out = sanitize_upload(edited, marks=preview.marks, edited=True, approved=preview.text)
    assert out.text.startswith(heading + '\nPython, SQL, Docker, FastAPI')
    assert 'Machine Learning: Regression' in out.text and 'Co-Founder' in out.text
    assert out.removed['header_lines'] == 0


def test_without_the_approved_preview_the_strict_boundary_still_applies(preview):
    edited = preview.text.replace('TECHNICAL SKILLS', 'TECH SKILLS')
    assert sanitize_upload(edited, marks=preview.marks, edited=True).text.startswith('WORK EXPERIENCE')


def test_new_private_text_is_still_dropped_with_the_approved_preview(preview):
    for lead in ('Gidion Contoh Depari', 'Private note that must not leave the preview',
                 'Date of Birth: 01 January 1990\nPersonal Details: Other Example'):
        out = sanitize_upload(lead + '\n' + preview.text, marks=preview.marks, edited=True, approved=preview.text)
        assert out.text.startswith('TECHNICAL SKILLS\nPython, SQL, Docker')
        for value in ('Gidion', 'Private note', '1990', 'Other Example'):
            assert value not in out.text


def test_a_name_typed_into_the_kept_first_block_is_dropped_and_contacts_are_masked(preview):
    edited = preview.text.replace('TECHNICAL SKILLS', 'TECH SKILLS').replace(
        'Python, SQL, Docker', 'Python, SQL, Docker\nRaka Pratama\ncontact gidion.contoh@example.com')
    out = sanitize_upload(edited, marks=preview.marks, edited=True, approved=preview.text)
    assert out.text.startswith('TECH SKILLS\nPython, SQL, Docker')
    assert 'Raka Pratama' not in out.text and 'example.com' not in out.text


def test_interests_and_a_strict_summary_still_apply_with_the_approved_preview(preview):
    edited = preview.text.replace('TECHNICAL SKILLS', 'TECH SKILLS') + '\nINTERESTS\nHiking and photography.'
    out = sanitize_upload(edited, marks=preview.marks, edited=True, approved=preview.text)
    assert 'Hiking' not in out.text and out.text.startswith('TECH SKILLS')
    with_summary = edited.replace('WORK EXPERIENCE', 'PROFILE\nA private self-description.\nWORK EXPERIENCE')
    out = sanitize_upload(with_summary, marks=preview.marks, edited=True, approved=preview.text)
    assert out.text.startswith('WORK EXPERIENCE') and 'private self-description' not in out.text


def test_the_preview_edit_endpoint_passes_the_approved_preview():
    from tests.test_api import make
    client, headers = make()
    up = client.post('/cv/upload', headers=headers, files={'file': ('cv.txt', CV.encode(), 'text/plain')})
    assert up.status_code == 200 and up.json()['masked_text'].startswith('TECHNICAL SKILLS')
    edited = up.json()['masked_text'].replace('TECHNICAL SKILLS', 'TECH SKILLS').replace(
        'Python, SQL, Docker', 'Python, SQL, Docker, FastAPI')
    out = client.post('/cv/preview', headers=headers, json={'text': edited})
    assert out.status_code == 200
    assert out.json()['masked_text'].startswith('TECH SKILLS\nPython, SQL, Docker, FastAPI')
    assert 'Gidion' not in out.json()['masked_text'] and 'example.com' not in out.json()['masked_text']
