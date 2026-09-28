"""Deterministic cleaning rules for job descriptions and provider metadata (CP1.3).

Every function is pure and returns what it changed, so notebooks can show before/after
and count rule hits. Raw text is never overwritten; cleaned values live in new fields.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timedelta

CLEANING_VERSION = "cleaning_v0.1_audited"

_TAG = re.compile(r"<[^>]+>")
_TRACKING = re.compile(r"#[A-Z]-\d{4,}-\w+")                       # e.g. aggregator code "#J-18808-Ljbffr"
_BLOG_INTRO = re.compile(r"^(Info Terbaru Lowongan Kerja[^.]*\.|Selamat (Pagi|Siang|Sore|Malam) untuk sobat[^.]*\.)\s*", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"(?:\+62|\b0)8\d{2}[\s-]?\d{3,4}[\s-]?\d{3,5}\b")
_MD_HEADER = re.compile(r"^#{1,6}\s*", re.M)
_SPACES = re.compile(r"[ \t   ]+")
_BLANKS = re.compile(r"\n{3,}")


def clean_description(text: str | None) -> tuple[str, list[str]]:
    """Return (clean_text, applied_rules). Keeps list structure (bullets and line breaks).

    Masks emails and Indonesian mobile numbers. This is not complete PII anonymization.
    """
    if not isinstance(text, str) or not text:
        return "", ["empty"]
    rules: list[str] = []
    out = text
    unescaped = html.unescape(out)
    if unescaped != out:
        rules.append("html_entities")
        out = unescaped
    if _TAG.search(out):
        rules.append("html_tags")
        out = _TAG.sub(" ", out)
    if _TRACKING.search(out):
        rules.append("aggregator_tracking_code")
        out = _TRACKING.sub("", out)
    if _BLOG_INTRO.search(out.strip()):
        rules.append("job_blog_intro")
        out = _BLOG_INTRO.sub("", out.strip())
    if _EMAIL.search(out):
        rules.append("email_masked")
        out = _EMAIL.sub("[EMAIL]", out)
    if _PHONE.search(out):
        rules.append("phone_masked")
        out = _PHONE.sub("[PHONE]", out)
    if _MD_HEADER.search(out):
        rules.append("markdown_headers")
        out = _MD_HEADER.sub("", out)
    if " " in out or " " in out:
        rules.append("nonbreaking_spaces")
    out = _SPACES.sub(" ", out)
    out = "\n".join(line.strip() for line in out.splitlines())
    out = _BLANKS.sub("\n\n", out).strip()
    return out, rules


_ID_WORDS = set("dan yang dengan untuk kami anda pengalaman memiliki dalam atau minimal kemampuan bekerja".split())
_EN_WORDS = set("and the with for you experience our will your ability work of to".split())


def detect_language(text: str) -> str:
    """Rough 'en' / 'id' / 'mixed' from common function words (heuristic, not a classifier)."""
    words = re.findall(r"[a-z]+", (text or "").lower())
    if not words:
        return "unknown"
    if len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", text or "")) > len("".join(words)):
        return "other_script"
    i = sum(w in _ID_WORDS for w in words)
    e = sum(w in _EN_WORDS for w in words)
    if i > e * 1.2:
        return "id"
    if e > i * 1.2:
        return "en"
    return "mixed" if i + e else "unknown"


_EMPLOYMENT_MAP = [
    ("internship", re.compile(r"magang|intern", re.I)),
    ("contract", re.compile(r"kontrak|contract", re.I)),
    ("part_time", re.compile(r"paruh waktu|part[\s–-]?time", re.I)),
    ("full_time", re.compile(r"pekerjaan tetap|full[\s–-]?time", re.I)),
]


def normalize_employment_type(raw: str | None) -> str:
    """Map provider values in EN/ID to one label; multi-valued strings keep the first listed type."""
    if not isinstance(raw, str) or not raw:
        return "unknown"
    first = re.split(r"\s+(?:and|dan)\s+", raw.strip(), maxsplit=1)[0]
    for label, rx in _EMPLOYMENT_MAP:
        if rx.search(first):
            return label
    return "unknown"


_REL = re.compile(r"(\d+)\s*(hari|days?|jam|hours?|menit|minutes?|minggu|weeks?|bulan|months?)\s*(?:yang\s+)?(?:ago|lalu)\b", re.I)
_UNIT_DAYS = {"hari": 1, "day": 1, "days": 1, "jam": 1 / 24, "hour": 1 / 24, "hours": 1 / 24,
              "menit": 1 / 1440, "minute": 1 / 1440, "minutes": 1 / 1440, "minggu": 7, "week": 7, "weeks": 7,
              "bulan": 30, "month": 30, "months": 30}


def derive_posted_at(posted_at: str | None, relative_text: str | None, retrieved_at: str | None) -> tuple[str | None, str]:
    """Return (date ISO or None, source). Never uses retrieval time as the posting date itself.

    source: provider_structured | relative_text (approximate, 'bulan' = 30 days) | unknown
    """
    posted_at = posted_at if isinstance(posted_at, str) and posted_at else None      # pandas may pass NaN
    relative_text = relative_text if isinstance(relative_text, str) else None
    retrieved_at = retrieved_at if isinstance(retrieved_at, str) and retrieved_at else None
    if posted_at:
        try:
            return datetime.fromisoformat(posted_at.replace("Z", "+00:00")).date().isoformat(), "provider_structured"
        except ValueError:
            pass
    if relative_text and retrieved_at:
        m = _REL.search(relative_text)
        if m:
            days = int(m.group(1)) * _UNIT_DAYS[m.group(2).lower()]
            try:
                base = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            except ValueError:
                return None, "unknown"
            return (base - timedelta(days=days)).date().isoformat(), "relative_text"
    return None, "unknown"
