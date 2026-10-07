"""Development CV1 upload fixtures. No source changes, test CVs or model calls."""
from pathlib import Path
import hashlib, json, re
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evals/fixtures/cp22_uploads'

def markdown_body():
    p=ROOT/'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
    return p,re.sub(r'<!--.*?-->','',p.read_text(),flags=re.S).strip()

def make_pdf(text,columns):
    doc=pymupdf.open(); page=doc.new_page(width=595,height=842)
    paragraphs=text.split('\n\n')
    # Preserve literal source text including Markdown markers; only wrap lines.
    if columns==1:
        y=30
        for para in paragraphs:
            box=pymupdf.Rect(30,y,565,812)
            left=page.insert_textbox(box,para,fontsize=8.5,fontname='helv')
            if left<0: raise ValueError('fixture overflow; do not truncate facts')
            y=812-left+5
    else:
        # Two narrow independent columns, flowing left then right.
        split=(len(paragraphs)+1)//2
        for x,items in [(25,paragraphs[:split]),(310,paragraphs[split:])]:
            y=25
            for para in items:
                left=page.insert_textbox(pymupdf.Rect(x,y,x+260,815),para,fontsize=8.0,fontname='helv')
                if left<0: raise ValueError('fixture overflow; do not truncate facts')
                y=815-left+6
    return doc

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source,body=markdown_body();rows=[]
    for columns in [1,2]:
        doc=make_pdf(body,columns);p=OUT/f'cv1_{columns}_column.pdf'
        if p.exists(): raise FileExistsError('Preserve existing fixture; use a new version')
        doc.save(p);doc.close()
        rows.append({'file':p.name,'columns':columns,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    with pymupdf.open(OUT/'cv1_1_column.pdf') as src:
        pix=src[0].get_pixmap(matrix=pymupdf.Matrix(1,1));scan=pymupdf.open();page=scan.new_page(width=595,height=842)
        page.insert_image(page.rect,stream=pix.tobytes('png'))
        p=OUT/'cv1_image_only.pdf'
        if p.exists():raise FileExistsError(p)
        scan.save(p);scan.close()
        rows.append({'file':p.name,'columns':None,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'expected':'no extractable text, no OCR'})
    manifest={'scope':'CV1 synthetic development only; not new candidate facts or labels','source':str(source.relative_to(ROOT)),
              'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'body_sha256':hashlib.sha256(body.encode()).hexdigest(),
              'rendering':'Literal Markdown body, Helvetica, whitespace-only line wrapping. No content omitted.','fixtures':rows}
    with (OUT/'manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    print(json.dumps({'created':len(rows),'source':'CV1'},indent=2))

if __name__=='__main__':main()
