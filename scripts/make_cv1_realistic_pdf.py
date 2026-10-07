"""Render CV1 as a realistic PDF fixture: no Markdown marks, styled headings, bullet points.

Same facts and sentences as data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md,
only the layout changes (uppercase section headings, bold job lines, round bullets).
Synthetic development data only. Writes a new versioned folder and refuses to overwrite.
"""
from hashlib import sha256
import json
from pathlib import Path
import re

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
OUT = ROOT / 'evals/fixtures/cv1_realistic_pdf_v1'
HEADINGS = {'Ringkasan': 'RINGKASAN', 'Pendidikan': 'PENDIDIKAN', 'Pengalaman': 'PENGALAMAN',
            'Proyek': 'PROYEK', 'Keahlian': 'KEAHLIAN', 'Sertifikasi': 'SERTIFIKASI', 'Bahasa': 'BAHASA'}
CSS = """
body { font-family: sans-serif; font-size: 10pt; }
h1 { font-size: 18pt; margin: 0; }
p.contact { font-size: 9pt; color: #444444; margin-top: 2pt; }
h2 { font-size: 11pt; color: #1f3864; margin-top: 10pt; margin-bottom: 2pt; border-bottom: 1px solid #1f3864; }
p { margin: 1pt 0; }
li { margin: 0; }
"""


def esc(t: str) -> str:
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def to_html(md: str) -> str:
    md = re.sub(r'<!--.*?-->', '', md, flags=re.S).strip()
    html, in_list = [], False
    for line in md.splitlines():
        line = line.rstrip()
        if line.startswith('- '):
            if not in_list:
                html.append('<ul>')
                in_list = True
            html.append('<li>' + esc(line[2:]) + '</li>')
            continue
        if in_list:
            html.append('</ul>')
            in_list = False
        if not line:
            continue
        if line.startswith('# '):
            html.append('<h1>' + esc(line[2:]) + '</h1>')
        elif line.startswith('## '):
            html.append('<h2>' + HEADINGS[line[3:]] + '</h2>')
        elif ' · ' in line and '@' in line:
            html.append('<p class="contact">' + esc(line.replace(' · ', ' | ')) + '</p>')
        else:
            # "**Title**, place · dates" becomes a bold title line with the dates after a bar.
            m = re.match(r'\*\*(.+?)\*\*(.*)$', line)
            if m:
                rest = esc(m.group(2).replace(' · ', ' | '))
                html.append(f'<p><b>{esc(m.group(1))}</b>{rest}</p>')
            else:
                html.append('<p>' + esc(line) + '</p>')
    if in_list:
        html.append('</ul>')
    return '\n'.join(html)


def render(html: str, path: Path) -> None:
    story = pymupdf.Story(html=html, user_css=CSS)
    writer = pymupdf.DocumentWriter(str(path))
    rect, where = pymupdf.paper_rect('a4'), pymupdf.paper_rect('a4') + (48, 48, -48, -48)
    more = True
    while more:
        device = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
    writer.close()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    pdf = OUT / 'cv1_realistic.pdf'
    render(to_html(SOURCE.read_text()), pdf)
    (OUT / 'manifest.json').write_text(json.dumps({
        'scope': 'CV1 synthetic development only; same facts and sentences, realistic layout',
        'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': sha256(SOURCE.read_bytes()).hexdigest(),
        'rendering': 'pymupdf Story HTML: uppercase section headings, bold job lines, bullet list, no Markdown marks',
        'generator': 'scripts/make_cv1_realistic_pdf.py',
        'file': pdf.name, 'sha256': sha256(pdf.read_bytes()).hexdigest()}, indent=1) + '\n')
    print('wrote', pdf.relative_to(ROOT))


if __name__ == '__main__':
    main()
