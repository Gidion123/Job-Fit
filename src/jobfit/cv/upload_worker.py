"""Bounded CV text-extraction worker, run as a separate interpreter by ``upload_guard.bounded_extract``.

Resource isolation only, not a security sandbox: the worker runs with an allow-listed environment
(no provider, database, owner or observability secrets), in isolated mode (``python -I``), and it
sets its own resource limits before it reads any untrusted byte or imports a parser:

- ``RLIMIT_AS`` (Linux only; other platforms do not enforce it the same way);
- ``RLIMIT_CPU``;
- ``RLIMIT_FSIZE`` 0, with SIGXFSZ ignored and no bytecode writes, so the parsers cannot write a file.

Protocol: stdin is ``<extension>\\n<file bytes>``; stdout is one JSON object
``{"code": null | "<rejection code>", "text": str, "pages": int, "layout": str, "warnings": [str]}``.
Nothing is written to stderr on purpose; the parent discards it.
"""
from __future__ import annotations

import json
import sys

ADDRESS_SPACE_BYTES = 512 * 1024 * 1024
CPU_SECONDS = 20
PDF_MAX_PAGES = 10
STDIN_MAX_BYTES = 5 * 1024 * 1024 + 1024


def limit_resources() -> None:
    import resource
    import signal
    sys.dont_write_bytecode = True
    if hasattr(signal, 'SIGXFSZ'):
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)       # a write fails with EFBIG instead of killing
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    if sys.platform.startswith('linux'):
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_BYTES, ADDRESS_SPACE_BYTES))


def _rejected(code: str) -> dict:
    return {'code': code, 'text': '', 'pages': 0, 'layout': '', 'warnings': []}


def extract(data: bytes, ext: str) -> dict:
    """The existing ``extract_text`` (unchanged), plus the stricter upload checks around it."""
    from jobfit.cv import text_extract
    if ext == '.pdf':
        import pymupdf
        with pymupdf.open(stream=data, filetype='pdf') as doc:
            if doc.needs_pass or doc.is_encrypted:
                return _rejected('pdf_encrypted')
            if len(doc) > PDF_MAX_PAGES:
                return _rejected('pdf_too_many_pages')
    # extract_text fails one combined way for "no text" and "too long"; in this throwaway process its
    # length check is lifted so the same two checks can be reported separately below, with the
    # unchanged MAX_CHARACTERS. Nothing is ever truncated.
    limit = text_extract.MAX_CHARACTERS
    text_extract.MAX_CHARACTERS = sys.maxsize
    out = text_extract.extract_text(data, 'upload' + ext)
    if out.status != 'ok':
        joined = ' '.join(out.warnings)
        if 'OCR is not enabled' in joined:
            return _rejected('pdf_no_text')
        if 'Encrypted PDF' in joined:
            return _rejected('pdf_encrypted')
        if 'No readable text' in joined:       # empty, or NUL characters in the extracted text
            return _rejected('no_text')
        return _rejected('document_unreadable')
    if len(out.text) > limit:
        return _rejected('text_too_long')
    return {'code': None, 'text': out.text, 'pages': int(out.pages), 'layout': str(out.layout),
            'warnings': [str(w) for w in out.warnings]}


def main() -> None:
    limit_resources()
    try:
        raw = sys.stdin.buffer.read(STDIN_MAX_BYTES + 1)
        head, sep, data = raw.partition(b'\n')
        ext = head.decode('ascii')
        if not sep or len(raw) > STDIN_MAX_BYTES or ext not in ('.pdf', '.docx', '.txt', '.md'):
            result = _rejected('document_unreadable')
        else:
            result = extract(data, ext)
    except BaseException:          # MemoryError, parser crashes: fail closed with no detail
        result = _rejected('document_unreadable')
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
