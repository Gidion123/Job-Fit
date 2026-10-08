"""CP3 lean public-beta CV upload boundary (jobfit.cv.upload_guard). Offline; no provider call.

Covers the raw body limit (declared, missing and false Content-Length), the memory-only multipart
parse, the explicit file-size check, container checks before any decompression, the bounded
extraction worker (timeout, failure, busy, cleanup, scrubbed environment, Linux resource limits),
the stable error contract and zero provider or session effects for every rejection.
"""
import io
import json
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import anyio
import pytest

from jobfit.cv import upload_guard as ug
from jobfit.cv.text_extract import extract_text
from jobfit.privacy.masking import mask_local
from tests.test_api_privacy import CANARY, app, session

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'evals/fixtures/cp22_uploads'
CV_MD = ROOT / 'data/synthetic_cvs/cv_01_fresh_graduate_data_science_id.md'
MIB = 1024 * 1024


def post(client, h, name, data):
    return client.post('/cv/upload', files={'file': (name, data)}, headers=h)


def rejected(r, code):
    assert r.status_code == ug.ERRORS[code][0], (r.status_code, r.text)
    assert r.json() == {'detail': ug.ERRORS[code][1], 'code': code}
    return True


def docx_bytes(text='Experience\nData Analyst, Python and SQL, 2025', extra=None):
    from docx import Document
    d = Document()
    for line in text.split('\n'):
        d.add_paragraph(line)
    b = io.BytesIO()
    d.save(b)
    if not extra:
        return b.getvalue()
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(b.getvalue())) as src, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            dst.writestr(info, src.read(info))
        for name, payload, method in extra:
            dst.writestr(zipfile.ZipInfo(name), payload, compress_type=method)
    return out.getvalue()


def zip_bytes(entries):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, payload in entries:
            z.writestr(name, payload)
    return out.getvalue()


CONTENT_TYPES = ('<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Override PartName="/word/document.xml" ContentType="{}"/></Types>')


def pdf_bytes(pages=1, encrypt=False):
    import pymupdf
    doc = pymupdf.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f'Page {i + 1}: Data Analyst with Python and SQL experience.')
    kw = dict(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='user') if encrypt else {}
    data = doc.tobytes(**kw)
    doc.close()
    return data


# --- valid files, same preview as before --------------------------------------------------------------

@pytest.mark.parametrize('name,data', [
    ('cv.md', CV_MD.read_bytes()),
    ('cv.txt', CV_MD.read_bytes()),
    ('cv1_1_column.pdf', (FIX / 'cv1_1_column.pdf').read_bytes()),
    ('cv1_2_column.PDF', (FIX / 'cv1_2_column.pdf').read_bytes()),
    ('cv.docx', docx_bytes()),
])
def test_a_valid_file_of_each_type_gives_the_same_masked_preview(name, data):
    client, _, calls = app()
    r = post(client, session(client), name, data)
    assert r.status_code == 200, r.text
    assert r.json()['masked_text'] == mask_local(extract_text(data, name).text).text
    assert calls == []


def test_a_valid_upload_above_the_default_spool_size_never_touches_disk(monkeypatch):
    big = docx_bytes(extra=[('word/media/blob.bin', os.urandom(4 * MIB), zipfile.ZIP_STORED)])
    assert MIB < len(big) < ug.UPLOAD_FILE_MAX_BYTES

    def no_disk(self):
        raise AssertionError('the upload rolled over to a temporary file')
    monkeypatch.setattr(tempfile.SpooledTemporaryFile, 'rollover', no_disk)
    client, _, _ = app()
    assert post(client, session(client), 'cv.docx', big).status_code == 200


# --- raw body and file size limits -------------------------------------------------------------------

def asgi_post(application, headers, chunks):
    """Drive the ASGI app directly so Content-Length can be absent or false."""
    sent, consumed = [], [0]
    it = iter(chunks)

    async def receive():
        try:
            chunk = next(it)
        except StopIteration:
            return {'type': 'http.request', 'body': b'', 'more_body': False}
        consumed[0] += 1
        return {'type': 'http.request', 'body': chunk, 'more_body': True}

    async def send(message):
        sent.append(message)
    scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1', 'method': 'POST',
             'scheme': 'http', 'path': '/cv/upload', 'raw_path': b'/cv/upload', 'query_string': b'',
             'root_path': '', 'server': ('test', 80), 'client': ('client', 1),
             'headers': [(k.lower().encode(), v.encode()) for k, v in headers.items()]}
    anyio.run(application, scope, receive, send)
    start = next(m for m in sent if m['type'] == 'http.response.start')
    body = b''.join(m.get('body', b'') for m in sent if m['type'] == 'http.response.body')
    return start['status'], json.loads(body), consumed[0]


def multipart_chunks(total_bytes, chunk=64 * 1024):
    head = (b'--B\r\nContent-Disposition: form-data; name="file"; filename="cv.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n')
    yield head
    sent = len(head)
    while sent < total_bytes:
        yield b'a' * chunk
        sent += chunk


@pytest.mark.parametrize('length', ['declared_too_large', 'missing', 'false_small'])
def test_the_raw_request_cap_holds_whatever_content_length_says(length):
    client, deps, calls = app()
    h = session(client)
    application = client.app
    headers = {**h, 'content-type': 'multipart/form-data; boundary=B'}
    if length == 'declared_too_large':
        headers['content-length'] = str(ug.UPLOAD_REQUEST_MAX_BYTES + 1)
    elif length == 'false_small':
        headers['content-length'] = '100'
    total = 12 * MIB
    status, body, consumed = asgi_post(application, headers, multipart_chunks(total))
    assert status == 413 and body == ug.error_body('upload_too_large')
    chunks_in_cap = ug.UPLOAD_REQUEST_MAX_BYTES // (64 * 1024) + 2
    assert consumed <= (0 if length == 'declared_too_large' else chunks_in_cap)    # stopped early
    assert calls == []


def test_a_file_above_five_mib_inside_a_request_below_the_raw_cap_is_refused():
    client, _, calls = app()
    data = b'a' * (ug.UPLOAD_FILE_MAX_BYTES + 1)
    assert len(data) + 1024 < ug.UPLOAD_REQUEST_MAX_BYTES
    assert rejected(post(client, session(client), 'cv.txt', data), 'upload_too_large') and calls == []


def test_malformed_multipart_is_refused():
    client, _, _ = app()
    h = session(client)
    assert rejected(client.post('/cv/upload', content=b'raw', headers={**h, 'content-type': 'text/plain'}),
                    'upload_malformed')
    two = client.post('/cv/upload', files=[('file', ('a.txt', b'abc')), ('file', ('b.txt', b'abc'))], headers=h)
    assert rejected(two, 'upload_malformed')
    field = client.post('/cv/upload', data={'x': '1'}, files={'file': ('a.txt', b'abc')}, headers=h)
    assert rejected(field, 'upload_malformed')
    assert rejected(client.post('/cv/upload', files={'other': ('a.txt', b'abc')}, headers=h), 'upload_malformed')


def test_other_routes_are_not_body_limited_by_the_upload_middleware():
    client, _, _ = app()
    h = session(client)
    r = client.post('/jobs/paste', json={'jd_text': 'x' * 300}, headers=h)
    assert r.status_code == 200


# --- container checks (nothing decompressed before the limits; no worker for a parent rejection) -----

@pytest.fixture
def no_worker(monkeypatch):
    def fail(*a, **kw):
        raise AssertionError('a worker was started for a rejected container')
    monkeypatch.setattr(ug.subprocess, 'Popen', fail)


@pytest.fixture
def opened(monkeypatch):
    names = []
    real = zipfile.ZipFile.open

    def spy(self, name, *a, **kw):
        names.append(name.filename if isinstance(name, zipfile.ZipInfo) else name)
        return real(self, name, *a, **kw)
    monkeypatch.setattr(zipfile.ZipFile, 'open', spy)
    return names


@pytest.mark.parametrize('name,data,code', [
    ('cv.exe', b'MZ', 'unsupported_type'),
    ('cv', b'abc', 'unsupported_type'),
    ('cv.pdf', zip_bytes([('a.txt', 'x')]), 'content_mismatch'),
    ('cv.docx', b'%PDF-1.7\n...', 'content_mismatch'),
    ('cv.docx', b'PK\x03\x04' + b'\x00' * 200, 'docx_invalid'),
    ('cv.docx', zip_bytes([('[Content_Types].xml', CONTENT_TYPES.format(ug.DOCX_MAIN_TYPE))]), 'docx_invalid'),
])
def test_type_and_content_mismatches_are_refused_without_a_worker(no_worker, name, data, code):
    client, _, calls = app()
    assert rejected(post(client, session(client), name, data), code) and calls == []


BOMB = b'\x00' * (11 * MIB)


@pytest.mark.parametrize('label,data,code', [
    ('entry above 10 MiB', zip_bytes([('[Content_Types].xml', 'x'), ('word/document.xml', BOMB)]),
     'docx_expansion_limit'),
    ('ratio above 100', zip_bytes([('[Content_Types].xml', 'x'), ('word/document.xml', b'\x00' * (2 * MIB))]),
     'docx_expansion_limit'),
    # entries just under 1 MiB are exempt from the ratio rule, so only the total limit can refuse these
    ('total above 20 MiB', zip_bytes([('[Content_Types].xml', 'x')]
                                     + [(f'word/p{i}.bin', b'\x00' * (MIB - 1)) for i in range(21)]),
     'docx_expansion_limit'),
    ('more than 200 entries', zip_bytes([(f'e{i}.xml', 'x') for i in range(201)]), 'docx_expansion_limit'),
    ('parent path', zip_bytes([('[Content_Types].xml', 'x'), ('word/document.xml', 'x'), ('../evil.xml', 'x')]),
     'docx_invalid'),
    ('absolute path', zip_bytes([('[Content_Types].xml', 'x'), ('word/document.xml', 'x'), ('/etc/x', 'x')]),
     'docx_invalid'),
    ('vbaProject', zip_bytes([('[Content_Types].xml', 'x'), ('word/document.xml', 'x'),
                              ('word/vbaProject.bin', 'x')]), 'docx_macro_enabled'),
])
def test_hostile_docx_archives_are_refused_before_any_decompression(no_worker, opened, label, data, code):
    client, _, calls = app()
    assert rejected(post(client, session(client), 'cv.docx', data), code), label
    assert opened == [] and calls == []


def test_the_docx_content_types_are_read_only_after_the_limits_and_under_a_bound(no_worker, opened):
    client, _, _ = app()
    h = session(client)
    macro = zip_bytes([('[Content_Types].xml', CONTENT_TYPES.format(
        'application/vnd.ms-word.document.macroEnabled.main+xml')), ('word/document.xml', '<w/>')])
    huge_types = zip_bytes([('[Content_Types].xml', ' ' * (ug.DOCX_CONTENT_TYPES_MAX_BYTES + 1)),
                            ('word/document.xml', '<w/>')])
    opened.clear()                                   # building the test archives opened entries for writing
    assert rejected(post(client, h, 'cv.docx', macro), 'docx_macro_enabled')
    assert opened == ['[Content_Types].xml']
    opened.clear()
    assert rejected(post(client, h, 'cv.docx', huge_types), 'docx_invalid') and opened == []


def test_a_docx_the_parser_cannot_read_fails_closed_in_the_worker():
    client, _, calls = app()
    broken = zip_bytes([('[Content_Types].xml', CONTENT_TYPES.format(ug.DOCX_MAIN_TYPE)),
                        ('word/document.xml', 'not xml')])
    assert rejected(post(client, session(client), 'cv.docx', broken), 'document_unreadable') and calls == []


# --- PDF ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('label,data,code', [
    ('broken body after a valid header', b'%PDF-1.4 broken', 'document_unreadable'),
    ('encrypted', pdf_bytes(encrypt=True), 'pdf_encrypted'),
    ('eleven pages', pdf_bytes(pages=11), 'pdf_too_many_pages'),
    ('image only', (FIX / 'cv1_image_only.pdf').read_bytes(), 'pdf_no_text'),
])
def test_bad_pdfs_are_refused(label, data, code):
    client, _, calls = app()
    assert rejected(post(client, session(client), 'cv.pdf', data), code), label
    assert calls == []


def test_ten_pages_are_accepted():
    client, _, _ = app()
    assert post(client, session(client), 'cv.pdf', pdf_bytes(pages=10)).status_code == 200


# --- TXT / MD ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize('name,data,code', [
    ('cv.txt', b'Python\x00SQL', 'text_binary'),
    ('cv.md', b'\xff\xfe broken', 'text_not_utf8'),
    ('cv.txt', b'\x01\x02\x03\x04' * 10 + b'Python SQL', 'text_binary'),
    ('cv.txt', b'   \n\t ', 'no_text'),
])
def test_bad_text_files_are_refused(name, data, code):
    client, _, calls = app()
    assert rejected(post(client, session(client), name, data), code) and calls == []


def test_a_bom_is_accepted_and_long_text_is_refused_never_truncated():
    client, _, _ = app()
    h = session(client)
    assert post(client, h, 'cv.txt', '\ufeffData Analyst, Python 2025'.encode()).status_code == 200
    from jobfit.cv.text_extract import MAX_CHARACTERS
    assert MAX_CHARACTERS == 100_000
    assert post(client, h, 'cv.txt', b'a' * MAX_CHARACTERS).status_code == 200
    assert rejected(post(client, h, 'cv.txt', b'a' * (MAX_CHARACTERS + 1)), 'text_too_long')


# --- bounded worker: timeout, failure, busy, cleanup, environment ---------------------------------------

def probe(code: str) -> list[str]:
    return [sys.executable, '-c', 'import sys, json, os, time\nsys.stdin.buffer.read()\n' + code]


def assert_reaped(procs):
    assert len(procs) == 1
    proc = procs[0]
    assert proc.returncode is not None and proc.poll() is not None      # terminated and joined
    assert proc.stdin.closed and proc.stdout.closed                        # IPC closed


def assert_slot_free_and_service_recovers():
    assert ug._SLOT.acquire(blocking=False)
    ug._SLOT.release()
    out = ug.bounded_extract(b'Data Analyst, Python and SQL, 2025', '.txt')
    assert out.text.startswith('Data Analyst')


def test_a_timed_out_worker_is_killed_and_reaped_and_the_slot_is_released():
    procs = []
    started = time.monotonic()
    with pytest.raises(ug.UploadRejected) as exc:
        ug.bounded_extract(b'abc', '.txt', timeout=0.3, command=probe('time.sleep(60)'), on_spawn=procs.append)
    assert exc.value.code == 'upload_timeout' and time.monotonic() - started < 10
    assert_reaped(procs)
    assert procs[0].returncode != 0
    assert_slot_free_and_service_recovers()


@pytest.mark.parametrize('label,code', [
    ('exits with an error', 'sys.exit(3)'),
    ('prints garbage', 'print("not json")'),
    ('malformed result', 'print(json.dumps({"code": None, "text": 5, "pages": 1, "layout": "x", "warnings": []}))'),
    ('empty text', 'print(json.dumps({"code": None, "text": " ", "pages": 1, "layout": "x", "warnings": []}))'),
    ('unknown code', 'print(json.dumps({"code": "boom", "text": "", "pages": 0, "layout": "", "warnings": []}))'),
    ('killed', 'os.kill(os.getpid(), 9)'),
])
def test_a_failing_worker_fails_closed_and_is_cleaned_up(label, code):
    procs = []
    with pytest.raises(ug.UploadRejected) as exc:
        ug.bounded_extract(b'abc', '.txt', command=probe(code), on_spawn=procs.append)
    assert exc.value.code == 'document_unreadable', label
    assert_reaped(procs)
    assert_slot_free_and_service_recovers()


def test_one_extraction_at_a_time_per_process():
    assert ug._SLOT.acquire(blocking=False)
    try:
        with pytest.raises(ug.UploadRejected) as exc:
            ug.bounded_extract(b'Python', '.txt')
        assert exc.value.code == 'upload_busy' and ug.ERRORS['upload_busy'][0] == 503
        client, _, _ = app()
        assert rejected(post(client, session(client), 'cv.txt', b'Data Analyst, Python 2025'), 'upload_busy')
    finally:
        ug._SLOT.release()
    assert_slot_free_and_service_recovers()


def test_the_worker_gets_an_allow_listed_environment_and_isolated_mode(monkeypatch):
    secrets = {'OPENROUTER_API_KEY': 'sk-secret-1', 'DATABASE_URL': 'postgresql://u:secret-2@db/x',
               'JOBFIT_OWNER_TOKEN': 'owner-secret-3', 'JOBFIT_INTERNAL_TOKEN': 'internal-secret-4',
               'JOBFIT_IP_HMAC_KEY': 'hmac-secret-5', 'LANGFUSE_SECRET_KEY': 'lf-secret-6'}
    for k, v in secrets.items():
        monkeypatch.setenv(k, v)
    echo = probe('print(json.dumps({"code": None, "text": json.dumps(dict(os.environ)), "pages": 0, '
                 '"layout": "x", "warnings": []}))')
    env = json.loads(ug.bounded_extract(b'abc', '.txt', command=echo).text)
    assert set(env) <= set(ug.worker_environment())
    assert not any(v in json.dumps(env) for v in secrets.values())
    assert '-I' in ug.worker_command()


@pytest.mark.skipif(not sys.platform.startswith('linux'), reason='RLIMIT_AS is enforced as tested only on Linux')
def test_the_worker_limits_hold_on_linux(tmp_path):
    root = str(Path(ug.__file__).resolve().parents[2])
    code = (f'sys.path.insert(0, {root!r})\n'
            'from jobfit.cv.upload_worker import limit_resources\n'
            'limit_resources()\n'
            'out = []\n'
            'try:\n'
            '    blob = bytearray(600 * 1024 * 1024)\n'
            '    out.append("allocated")\n'
            'except MemoryError:\n'
            '    out.append("memory_refused")\n'
            'try:\n'
            f'    with open({str(tmp_path / "w.txt")!r}, "w") as f:\n'
            '        f.write("x" * 10)\n'
            '        f.flush()\n'
            '    out.append("written")\n'
            'except OSError:\n'
            '    out.append("write_refused")\n'
            'print(json.dumps({"code": None, "text": " ".join(out), "pages": 0, "layout": "x", "warnings": []}))')
    result = ug.bounded_extract(b'abc', '.txt', command=probe(code))
    assert result.text == 'memory_refused write_refused'
    assert not (tmp_path / 'w.txt').exists() or (tmp_path / 'w.txt').stat().st_size == 0


# --- stable errors, no leakage, zero provider or session effects -----------------------------------------

def test_rejections_leak_no_content_filename_or_parser_text(caplog):
    import logging
    client, _, calls = app()
    h = session(client)
    secret_name = f'{CANARY}-private-name'
    cases = [(f'{secret_name}.exe', CANARY.encode()), (f'{secret_name}.txt', CANARY.encode() + b'\x00'),
             (f'{secret_name}.pdf', b'%PDF-1.4 ' + CANARY.encode()),
             (f'{secret_name}.docx', b'PK\x03\x04' + CANARY.encode())]
    with caplog.at_level(logging.DEBUG):
        responses = [post(client, h, name, data) for name, data in cases]
    for r in responses:
        assert set(r.json()) == {'detail', 'code'} and r.json()['detail'] == ug.ERRORS[r.json()['code']][1]
        assert CANARY not in r.text and 'private-name' not in r.text
    assert CANARY not in caplog.text
    # nothing reached the session: there is no preview to consent to, and no run started
    assert client.post('/cv/consent', json={'digest': '0' * 64, 'affirmative': True}, headers=h).status_code == 409
    assert calls == []
