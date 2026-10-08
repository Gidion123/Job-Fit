"""Lean public-beta CV upload boundary (CP3 upload hardening).

A bounded, memory-only, fail-closed ``POST /cv/upload`` for a single-VPS controlled beta:

1. **Raw body:** Starlette's ``RequestBodyLimitMiddleware`` (attached by ``UploadBodyLimit`` to this
   route only) counts the bytes actually received and refuses a declared ``Content-Length`` above
   the cap; a missing or false ``Content-Length`` is still capped. Every 413 on the route is
   rewritten to the JobFit error body.
2. **Memory-only multipart:** the bounded stream is parsed once, with a spool limit above the raw
   cap, so the file part never rolls over to a temporary file; then the actual file size is checked.
3. **Container checks** without decompression: PDF header; DOCX central directory (entry count,
   declared sizes, compression ratio, paths, required OOXML parts) before any entry is read; UTF-8
   and binary sanity for TXT/MD.
4. **Bounded extraction** in a separate interpreter (``upload_worker``) with an allow-listed
   environment, a wall timeout and resource limits. Resource isolation only, not a security
   sandbox. One extraction at a time per API process; the controlled beta runs ONE API
   worker process, so this is one extraction at a time for the service (no cross-process lock).

Every rejection is ``{"detail": "<fixed message>", "code": "<code>"}``: no filename, parser
exception text or CV content. A rejected file never reaches masking, the session or a provider.
``text_extract.py`` and its ``MAX_CHARACTERS`` (used by the Phase 2A and D-103 bounds) are unchanged.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path, PurePosixPath

from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.middleware.body_limit import RequestBodyLimitMiddleware
from starlette.responses import JSONResponse

UPLOAD_PATH = '/cv/upload'
UPLOAD_FILE_MAX_BYTES = 5 * 1024 * 1024                         # the actual CV file
UPLOAD_REQUEST_MAX_BYTES = UPLOAD_FILE_MAX_BYTES + 64 * 1024    # the raw multipart request
SUPPORTED_EXTENSIONS = ('.pdf', '.docx', '.txt', '.md')
PDF_HEADER_WINDOW = 1024
DOCX_MAX_ENTRIES = 200
DOCX_MAX_TOTAL_BYTES = 20 * 1024 * 1024
DOCX_MAX_ENTRY_BYTES = 10 * 1024 * 1024
DOCX_MAX_RATIO = 100
DOCX_RATIO_MIN_BYTES = 1024 * 1024
DOCX_CONTENT_TYPES_MAX_BYTES = 256 * 1024
DOCX_MAIN_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
TEXT_CONTROL_MAX_RATIO = 0.01
EXTRACT_TIMEOUT_SECONDS = 20.0
WORKER_ENV = {'LC_ALL': 'C.UTF-8'}              # allow-list: nothing from the API process environment

ERRORS = {
    'upload_too_large': (413, 'The file is too large. The limit is 5 MB.'),
    'upload_malformed': (422, 'The upload could not be read. Send one PDF, DOCX, TXT or MD file.'),
    'unsupported_type': (415, 'Supported files: PDF, DOCX, TXT or MD.'),
    'content_mismatch': (422, 'The file content does not match its file type.'),
    'pdf_encrypted': (422, 'The PDF is encrypted. Upload an unprotected PDF.'),
    'pdf_too_many_pages': (422, 'The PDF has more than 10 pages.'),
    'pdf_no_text': (422, 'A PDF page has no extractable text. Upload a text PDF or paste text; OCR is not enabled.'),
    'docx_invalid': (422, 'The DOCX file is not a valid Word document.'),
    'docx_expansion_limit': (422, 'The DOCX file expands beyond the allowed size.'),
    'docx_macro_enabled': (422, 'Macro-enabled Word documents are not accepted.'),
    'text_not_utf8': (422, 'Text files must be UTF-8 encoded.'),
    'text_binary': (422, 'The text file contains binary data.'),
    'text_too_long': (422, 'The document has more than 100,000 characters. Nothing was truncated.'),
    'no_text': (422, 'No readable text was found in the document.'),
    'document_unreadable': (422, 'The document could not be read. Upload a text PDF/DOCX or paste text.'),
    'upload_timeout': (422, 'Reading the document took too long.'),
    'upload_busy': (503, 'Another document is being read. Please try again in a moment.'),
    'upload_rate_limited': (429, 'Too many uploads. Please try again later.'),
}


class UploadRejected(Exception):
    """A safe, deterministic upload rejection; ``code`` keys ``ERRORS``."""

    def __init__(self, code: str):
        if code not in ERRORS:
            code = 'document_unreadable'
        super().__init__(code)
        self.code = code
        self.status, self.message = ERRORS[code]


def error_body(code: str) -> dict:
    return {'detail': ERRORS[code][1], 'code': code}


def rejection_response(code: str) -> JSONResponse:
    return JSONResponse(error_body(code), status_code=ERRORS[code][0])


# --- 1. raw body limit (Starlette's middleware, this route only) -----------------------------------

class UploadBodyLimit:
    """ASGI middleware: ``RequestBodyLimitMiddleware`` on ``POST /cv/upload`` with the JobFit 413 body."""

    def __init__(self, app, path: str = UPLOAD_PATH, max_body_size: int = UPLOAD_REQUEST_MAX_BYTES):
        self.app, self.path = app, path
        self.limited = RequestBodyLimitMiddleware(app, max_body_size=max_body_size)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('path') != self.path:
            return await self.app(scope, receive, send)
        replaced = False
        body = json.dumps(error_body('upload_too_large')).encode()

        async def send_contract(message):
            nonlocal replaced
            if message['type'] == 'http.response.start' and message['status'] == 413:
                replaced = True
                await send({'type': 'http.response.start', 'status': 413,
                            'headers': [(b'content-type', b'application/json'),
                                        (b'content-length', str(len(body)).encode())]})
                await send({'type': 'http.response.body', 'body': body, 'more_body': False})
                return
            if not replaced:            # the original 413 body (plain text or JSON) is dropped
                await send(message)
        await self.limited(scope, receive, send_contract)


# --- 2. memory-only multipart from the bounded stream ---------------------------------------------

class _MemoryMultiPart(MultiPartParser):
    spool_max_size = UPLOAD_REQUEST_MAX_BYTES + 1      # above the raw cap: never rolls over to disk


async def read_upload(request) -> tuple[str, bytes]:
    """(extension, file bytes) of the single ``file`` part; UploadRejected otherwise."""
    if not request.headers.get('content-type', '').lower().startswith('multipart/form-data'):
        raise UploadRejected('upload_malformed')
    try:
        form = await _MemoryMultiPart(request.headers, request.stream(), max_files=1, max_fields=0).parse()
    except StarletteHTTPException as exc:
        if exc.status_code == 413:
            raise UploadRejected('upload_too_large') from None
        raise
    except (MultiPartException, KeyError, ValueError):
        raise UploadRejected('upload_malformed') from None
    try:
        items = form.multi_items()
        if len(items) != 1 or items[0][0] != 'file' or not isinstance(items[0][1], UploadFile):
            raise UploadRejected('upload_malformed')
        upload = items[0][1]
        if upload.size is not None and upload.size > UPLOAD_FILE_MAX_BYTES:
            raise UploadRejected('upload_too_large')
        data = await upload.read(UPLOAD_FILE_MAX_BYTES + 1)
        if len(data) > UPLOAD_FILE_MAX_BYTES:
            raise UploadRejected('upload_too_large')
        if not data:
            raise UploadRejected('no_text')
        return upload_extension(upload.filename or ''), data
    finally:
        await form.close()


def upload_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UploadRejected('unsupported_type')
    return ext


# --- 3. container checks (no decompression before the limits) -------------------------------------

def check_container(data: bytes, ext: str) -> None:
    if ext == '.pdf':
        if b'%PDF-' not in data[:PDF_HEADER_WINDOW]:
            raise UploadRejected('content_mismatch')
    elif ext == '.docx':
        check_docx(data)
    elif ext in ('.txt', '.md'):
        check_text(data)
    else:
        raise UploadRejected('unsupported_type')


def _unsafe_name(name: str) -> bool:
    posix = name.replace('\\', '/')
    return (posix.startswith('/') or re.match(r'^[A-Za-z]:', posix) is not None
            or '..' in PurePosixPath(posix).parts)


def check_docx(data: bytes) -> None:
    """Central-directory checks first (ZipInfo metadata only); then one bounded metadata read."""
    if not data.startswith(b'PK\x03\x04'):
        raise UploadRejected('content_mismatch')
    try:
        archive = zipfile.ZipFile(BytesIO(data))
    except (zipfile.BadZipFile, ValueError, OSError, EOFError):
        raise UploadRejected('docx_invalid') from None
    with archive:
        infos = archive.infolist()
        if len(infos) > DOCX_MAX_ENTRIES:
            raise UploadRejected('docx_expansion_limit')
        total = 0
        for info in infos:
            if _unsafe_name(info.filename):
                raise UploadRejected('docx_invalid')
            if info.file_size > DOCX_MAX_ENTRY_BYTES:
                raise UploadRejected('docx_expansion_limit')
            if info.file_size >= DOCX_RATIO_MIN_BYTES and info.file_size > DOCX_MAX_RATIO * max(info.compress_size, 1):
                raise UploadRejected('docx_expansion_limit')
            total += info.file_size
        if total > DOCX_MAX_TOTAL_BYTES:
            raise UploadRejected('docx_expansion_limit')
        names = {info.filename for info in infos}
        if any(n.lower().endswith('vbaproject.bin') for n in names):
            raise UploadRejected('docx_macro_enabled')
        if '[Content_Types].xml' not in names or 'word/document.xml' not in names:
            raise UploadRejected('docx_invalid')
        types = archive.getinfo('[Content_Types].xml')
        if types.file_size > DOCX_CONTENT_TYPES_MAX_BYTES:
            raise UploadRejected('docx_invalid')
        try:
            content_types = archive.read(types).decode('utf-8', errors='replace')
        except (zipfile.BadZipFile, RuntimeError, ValueError, OSError, EOFError, NotImplementedError):
            raise UploadRejected('docx_invalid') from None
    if 'macroenabled' in content_types.lower():
        raise UploadRejected('docx_macro_enabled')
    if DOCX_MAIN_TYPE not in content_types:
        raise UploadRejected('docx_invalid')


def check_text(data: bytes) -> None:
    """Strict UTF-8, no NUL, almost no control characters. Plain text has no magic signature."""
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise UploadRejected('text_not_utf8') from None
    if '\x00' in text:
        raise UploadRejected('text_binary')
    controls = sum(1 for c in text if (ord(c) < 32 and c not in '\t\n\r\f') or ord(c) == 127)
    if controls > TEXT_CONTROL_MAX_RATIO * len(text):
        raise UploadRejected('text_binary')


# --- 4. bounded extraction in a separate interpreter -----------------------------------------------

_SLOT = threading.BoundedSemaphore(1)      # per API process; the beta runs one API process
_BOOT = 'import sys; sys.path.insert(0, sys.argv[1]); from jobfit.cv.upload_worker import main; main()'


@dataclass
class Extracted:
    text: str = field(repr=False)
    pages: int
    layout: str
    warnings: list[str]


def worker_command() -> list[str]:
    import jobfit
    package_root = str(Path(jobfit.__file__).resolve().parents[1])
    return [sys.executable, '-I', '-c', _BOOT, package_root]


def _parse_result(out: bytes) -> Extracted:
    try:
        result = json.loads(out.decode('utf-8'))
        code, text, pages, layout, warnings = (result['code'], result['text'], result['pages'], result['layout'],
                                               result['warnings'])
    except Exception:
        raise UploadRejected('document_unreadable') from None
    if code is not None:
        raise UploadRejected(code if isinstance(code, str) else 'document_unreadable')
    if (not isinstance(text, str) or not text.strip() or isinstance(pages, bool) or not isinstance(pages, int)
            or not isinstance(layout, str) or not isinstance(warnings, list)
            or not all(isinstance(w, str) for w in warnings)):
        raise UploadRejected('document_unreadable')
    return Extracted(text, pages, layout, list(warnings))


def bounded_extract(data: bytes, ext: str, *, timeout: float = EXTRACT_TIMEOUT_SECONDS, command=None,
                    on_spawn=None) -> Extracted:
    """Extract text in the bounded worker. ``command`` and ``on_spawn`` are test seams.

    Every path closes the pipes, reaps the worker (kill then wait on timeout or failure) and
    releases the extraction slot.
    """
    if not _SLOT.acquire(blocking=False):
        raise UploadRejected('upload_busy')
    proc = None
    try:
        try:
            proc = subprocess.Popen(command or worker_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, env=dict(WORKER_ENV), close_fds=True)
        except OSError:
            raise UploadRejected('document_unreadable') from None
        if on_spawn is not None:
            on_spawn(proc)
        try:
            out, _ = proc.communicate(ext.encode('ascii') + b'\n' + data, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise UploadRejected('upload_timeout') from None
        if proc.returncode != 0:
            raise UploadRejected('document_unreadable')
        return _parse_result(out)
    finally:
        try:
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()
                proc.wait()
                for pipe in (proc.stdin, proc.stdout):
                    if pipe is not None and not pipe.closed:
                        pipe.close()
        finally:
            _SLOT.release()


def worker_environment() -> dict:
    """What the worker process sees as its environment (for the deployment record and tests)."""
    return dict(WORKER_ENV)

