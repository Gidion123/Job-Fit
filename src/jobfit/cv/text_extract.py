"""Memory-only upload extraction with explicit layout/no-text limitations."""
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import re

TEXT_VERSION = 'upload-text-v1'
MAX_BYTES = 10 * 1024 * 1024
MAX_CHARACTERS = 100_000

@dataclass
class TextResult:
    text: str = field(default='', repr=False)
    status: str = 'ok'
    warnings: list[str] = field(default_factory=list)
    pages: int = 0
    layout: str = 'text'
    preprocessing_version: str = TEXT_VERSION

def _pdf_page(page):
    # Read text blocks in column order if a clear gutter separates them. Spanning
    # headings divide vertical bands so a header/footer cannot interleave columns.
    blocks=[b for b in page.get_text('blocks',sort=False) if b[6]==0 and b[4].strip()]
    mid=page.rect.width/2
    left=[b for b in blocks if b[2] <= mid-6]
    right=[b for b in blocks if b[0] >= mid+6]
    spanning=[b for b in blocks if b not in left and b not in right]
    overlap=any(max(l[1],r[1]) < min(l[3],r[3]) for l in left for r in right)
    if len(left)<2 or len(right)<2 or not overlap:
        return '\n'.join(b[4].strip() for b in sorted(blocks,key=lambda b:(b[1],b[0]))), False
    ordered=[]; remaining=left+right
    for span in sorted(spanning,key=lambda b:b[1]):
        above=[b for b in remaining if b[1]<span[1]]
        ordered+=sorted([b for b in above if b in left],key=lambda b:b[1])+sorted([b for b in above if b in right],key=lambda b:b[1])
        remaining=[b for b in remaining if b not in above]
        ordered.append(span)
    ordered+=sorted([b for b in remaining if b in left],key=lambda b:b[1])+sorted([b for b in remaining if b in right],key=lambda b:b[1])
    return '\n'.join(b[4].strip() for b in ordered), True

def extract_text(data: bytes, filename: str) -> TextResult:
    """No disk write; caller owns source bytes. Failed extraction never reaches a model."""
    if not data or len(data)>MAX_BYTES:
        return TextResult(status='failed',warnings=['Empty input or upload exceeds 10 MB.'])
    ext=Path(filename).suffix.lower()
    try:
        if ext=='.pdf':
            import pymupdf
            with pymupdf.open(stream=data,filetype='pdf') as doc:
                if doc.needs_pass or len(doc)>30:
                    return TextResult(status='failed',warnings=['Encrypted PDF or more than 30 pages.'])
                pages=[]; columns=False
                for page in doc:
                    text,two=_pdf_page(page); pages.append(text); columns|=two
                    if not text.strip():
                        return TextResult(status='failed',pages=len(doc),layout='pdf',warnings=['A PDF page has no extractable text. Upload a text PDF or paste text; OCR is not enabled.'])
                out=TextResult(text='\n\n'.join(pages),pages=len(doc),layout='two_column' if columns else 'single_column',warnings=['Check PDF reading order and every experience/date in the parsing preview.'])
        elif ext=='.docx':
            from docx import Document
            from docx.table import Table
            from docx.text.paragraph import Paragraph
            doc=Document(BytesIO(data)); chunks=[]
            for block in doc.iter_inner_content():
                if isinstance(block,Paragraph): chunks.append(block.text)
                elif isinstance(block,Table):
                    chunks.extend(' | '.join(c.text for c in row.cells) for row in block.rows)
            out=TextResult(text='\n'.join(chunks),layout='docx',warnings=['Check tables and reading order in the parsing preview.'])
        elif ext in ['.md','.txt']:
            text=data.decode('utf-8-sig')
            # Synthetic administrative comments are not CV evidence or configuration.
            if ext=='.md': text=re.sub(r'<!--.*?-->','',text,flags=re.S)
            out=TextResult(text=text.strip())
        else: return TextResult(status='failed',warnings=['Supported inputs: PDF, DOCX, UTF-8 text or Markdown.'])
        if not out.text.strip() or len(out.text)>MAX_CHARACTERS or '\x00' in out.text:
            return TextResult(status='failed',warnings=['No readable text or text exceeds 100000 characters. Input was not truncated.'])
        return out
    except Exception:
        return TextResult(status='failed',warnings=['The document could not be read. Upload a text PDF/DOCX or paste text.'])
