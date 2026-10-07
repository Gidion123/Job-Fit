"""Realistic CV1 PDF (no Markdown marks): text, parser plumbing, G1 headings and quotes.

The fixture has the same facts as CV1. Fixture responses are fixed adapters, not a
semantic oracle, and no model is called.
"""
from datetime import date
import json
from hashlib import sha256
from pathlib import Path
import re

import pytest

from jobfit.cv.parser import parse_cv
from jobfit.cv.text_extract import extract_text
from jobfit.eval.fixture_client import FixtureClient
from jobfit.matching.constraints import experience_years
from jobfit.matching.guardrails import SKILL_HEADINGS, _headings, skills_only
from jobfit.matching.quote_check_v11 import _tokens, resolve_quote

pytest.importorskip('fitz')
ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evals/fixtures/cv1_realistic_pdf_v1'
SOURCE = ROOT / 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
REF = date(2026, 9, 30)
MAP = {'RINGKASAN': 'Summary', 'PENDIDIKAN': 'Education', 'PENGALAMAN': 'Experience', 'PROYEK': 'Projects',
       'KEAHLIAN': 'Skills', 'SERTIFIKASI': 'Certifications', 'BAHASA': 'Other'}


@pytest.fixture(scope='module')
def text():
    data = (FOLDER / 'cv1_realistic.pdf').read_bytes()
    manifest = json.loads((FOLDER / 'manifest.json').read_text())
    assert sha256(data).hexdigest() == manifest['sha256']
    assert manifest['source_sha256'] == sha256(SOURCE.read_bytes()).hexdigest()
    return extract_text(data, 'cv1_realistic.pdf')


def plain_response(cv_text):
    """CV1-only adapter for the plain layout (headings in capitals, bullets)."""
    hits = list(re.finditer(r'^(' + '|'.join(MAP) + r')$', cv_text, re.M))
    sections = [{'section': MAP[m[1]], 'text': cv_text[m.end():hits[i + 1].start() if i + 1 < len(hits) else len(cv_text)].strip()}
                for i, m in enumerate(hits)]
    exp = next(s['text'] for s in sections if s['section'] == 'Experience')
    a, b = exp.index('Data Analyst Intern'), exp.index('Asisten Praktikum Analisis Regresi')
    work = [{'title': 'Data Analyst Intern', 'organization': 'PT Contoh Retail Nusantara', 'source_quote': exp[a:b].strip(),
             'start_text': 'Februari 2026', 'end_text': 'Mei 2026', 'is_present': False},
            {'title': 'Asisten Praktikum Analisis Regresi', 'organization': 'Universitas Negeri Contoh',
             'source_quote': exp[b:].strip(), 'start_text': 'Februari 2025', 'end_text': 'Juni 2025', 'is_present': False}]
    return {'language': 'id', 'sections': sections, 'employment': work,
            'skills_list': ['Python', 'SQL', 'R', 'Looker Studio', 'Excel', 'Git'],
            'evidence': [{'fact_id': f'f{i + 1}', 'section': s['section'], 'quote': s['text']} for i, s in enumerate(sections)],
            'location_quote': 'Jakarta Selatan, Indonesia'}


def test_pdf_has_no_markdown_and_keeps_every_word(text):
    assert text.status == 'ok' and text.layout == 'single_column' and text.pages == 1
    assert '#' not in text.text and '**' not in text.text and not re.search(r'(?m)^- ', text.text)
    assert '•' in text.text
    md = extract_text(SOURCE.read_bytes(), SOURCE.name).text
    # Only headings change case; every other word keeps its exact spelling.
    headings = {m.casefold() for m in MAP}
    norm = lambda s: [t[0].casefold() if t[0].casefold() in headings else t[0] for t in _tokens(s)]
    assert norm(text.text) == norm(md)


def test_pdf_ligatures_are_real_and_quote_check_handles_them(text):
    # PDF text keeps the fi ligature (U+FB01), as many real CV exports do.
    assert 'ﬁtur penting' in text.text
    out = resolve_quote('menjelaskan fitur penting dengan SHAP', text.text)
    assert out['flags'] == ['normalized_separators'] and 'ﬁ' in out['cv_span']


def test_quote_across_line_wrap_resolves_to_one_span(text):
    out = resolve_quote('dengan Python (pandas) dan SQL (PostgreSQL).', text.text)
    assert 'PostgreSQL' in out['cv_span'] and '\n' in out['cv_span']


def test_g1_finds_plain_headings_and_skills_only_quotes(text):
    names = [n for _, _, n in _headings(text.text)]
    assert [n for n in names if n in {m.lower() for m in MAP}] == [m.lower() for m in MAP]
    assert 'keahlian' in SKILL_HEADINGS
    assert skills_only('Excel', text.text) and skills_only('Git', text.text)
    assert skills_only('Python (pandas, NumPy', text.text)
    assert not skills_only('Looker Studio', text.text)      # also used in the internship
    assert not skills_only('scikit-learn', text.text)       # also used in the thesis project


def test_parser_plumbing_on_plain_layout(text):
    cv = parse_cv(text, cv_id='CV1', analysis_date=REF, is_synthetic=True,
                  client=FixtureClient([lambda p: plain_response(p['cv_text'])]), model='deepseek-flash')
    assert cv.profile.parse_status.value == 'ok'
    assert [e.title for e in cv.profile.experience] == ['Data Analyst Intern', 'Asisten Praktikum Analisis Regresi']
    assert experience_years(cv.profile.experience, REF) == .75
    assert {'Education', 'Projects', 'Skills', 'Experience'} <= set(cv.summary()['sections_found'])
    assert cv.summary()['review_required'] and cv.profile.confirmed_location is None
