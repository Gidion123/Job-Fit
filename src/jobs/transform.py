"""Rule-based feature transformation v0 (CP1.4): title, role family, seniority, experience,
location, work mode, remote eligibility.

These rules are deterministic and versioned. They are *baselines* for EDA and for the
role/eligibility gate; the LLM extractor (CP2) will be evaluated against human labels,
and these rules can be evaluated the same way.
"""

from __future__ import annotations

import re

TAXONOMY_VERSION = "role_taxonomy_v0.1_audited"

TARGET_FAMILIES = ("ai_ml_engineering", "genai_llm", "data_science", "software_ai")
ADJACENT_FAMILIES = ("data_analytics", "data_engineering", "software_general", "other_tech")
NON_TARGET_FAMILIES = ("business_product", "content_marketing", "annotation_labeling", "other")

_NOISE = re.compile(r"lowongan kerja|\(remote\)|- remote\b|remote -|\bremote\b|\bhybrid\b|\bwfh\b|\[.*?\]|\((?:mandarin|english|malaysian)[^)]*\)", re.I)


def normalize_title(title: str | None) -> str:
    t = _NOISE.sub(" ", title or "")
    t = re.sub(r"[|/–—:]+", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def _rx(p: str) -> re.Pattern:
    return re.compile(p, re.I)


# Order matters: the first matching rule wins. Documented so the gate is explainable.
_ENG_WORDS = _rx(r"engineer|developer|scientist|programmer|analyst")
_ROLE_RULES: list[tuple[str, re.Pattern, bool]] = [
    # (family, pattern, only_if_no_engineering_word)
    ("data_science", _rx(r"data scien|ilmuwan data|decision scien"), False),
    ("content_marketing", _rx(r"\b(content|creator|copywriter|marketing|social media|influencer|seo|videographer)\b|video (?:editor|content|producer)"), True),
    ("business_product", _rx(r"sales engineer|pre[- ]?sales|sales (?:executive|manager|representative|specialist)|account (?:manager|executive)|"
                             r"business development|go[- ]to[- ]market|market research|recruiter|business analyst|analis bisnis"), False),
    ("business_product", _rx(r"\b(product manager|product owner|business analyst|consultant|project manager|program manager|"
                             r"assistant director|executive assistant|personal assistant|secretary|sekretaris)\b"), True),
    ("annotation_labeling", _rx(r"annotat|labell?(?:ing|er)|ai trainer|ai tutor|rater\b"), False),
    ("other_tech", _rx(r"\b(qa|quality assurance|tester|testing|it support|helpdesk|product security|devops|sre|site reliability)\b"), False),
    ("genai_llm", _rx(r"\b(llm|genai|gen ai|generative|prompt engineer|rag|agentic|ai agent|conversational ai|chatbot)\b"), False),
    ("ai_ml_engineering", _rx(r"machine learning|\bml\b|mlops|ml ops|\bai\b|a\.i\.|artificial intelligence|computer vision|"
                              r"deep learning|\bnlp\b|natural language|research scientist"), False),
    ("data_engineering", _rx(r"data engineer|analytics engineer|big data|\betl\b|data platform"), False),
    ("data_analytics", _rx(r"data analy|data analis|business intelligence|\bbi\b|analytics|data operation|reporting|"
                           r"\bdata\b.*\b(?:analyst|analis|insights?)\b|insights? analyst|modell?ing analyst|forecasting analyst"), False),
    ("other_tech", _rx(r"\b(infrastructure|network|solutions? engineer|implementation engineer|system administrator|security)\b"), False),
    ("software_general", _rx(r"software|backend|back-end|frontend|front-end|full[- ]?stack|developer|programmer|engineer|mobile|android|ios"), False),
]


def role_family(title: str | None) -> str:
    """Title-based role family (taxonomy v0). 'software_ai' = software role whose title names AI/ML."""
    t = title or ""
    has_eng = bool(_ENG_WORDS.search(t))
    for family, rx, only_non_eng in _ROLE_RULES:
        if only_non_eng and has_eng:
            continue
        if rx.search(t):
            if family == "ai_ml_engineering" and re.search(r"software|backend|back-end|full[- ]?stack|frontend|developer|platform engineer", t, re.I) \
                    and not re.search(r"machine learning|\bml\b|mlops|ai engineer|ai developer|artificial intelligence developer", t, re.I):
                return "software_ai"
            return family
    return "other"


def role_group(family: str) -> str:
    if family in TARGET_FAMILIES:
        return "target"
    if family in ADJACENT_FAMILIES:
        return "adjacent"
    return "non_target"


_T_INTERN = _rx(r"\b(intern|internship|magang|trainee)\b")
# "Staff" alone is an entry-level word in Indonesian postings ("Data Analyst Staff"); only "Staff <x> Engineer/Scientist" is a level.
_T_LEAD = _rx(r"\b(lead|head|principal|manager|director|vp|chief|architect|section head|supervisor)\b|\bstaff\s+(?:[\w/]+\s+){0,2}(?:engineer|scientist)")
_ROLE_NOUNS = _rx(r"product manager|project manager|account manager|program manager")
_T_SENIOR = _rx(r"\b(senior|sr\.?)\b")
_T_MID = _rx(r"\b(mid|middle|intermediate)\b|\bII\b")
_T_JUNIOR = _rx(r"\b(junior|jr\.?|entry|fresh ?grad\w*|graduate|associate)\b|\bI\b(?!\w)")


def title_seniority(title: str | None) -> str:
    t = _ROLE_NOUNS.sub(" ", title or "")  # role nouns containing "manager" are not a level
    for label, rx in (("intern", _T_INTERN), ("lead_plus", _T_LEAD), ("senior", _T_SENIOR), ("mid", _T_MID), ("junior", _T_JUNIOR)):
        if rx.search(t):
            return label
    return "unspecified"


_YEARS = re.compile(
    r"(?<![\d.])(?P<a>\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to|sampai|s/d|hingga)\s*(?P<b>\d{1,2})\s*)?\+?\s*(?:years?|yrs?|tahun)", re.I)
_EXP_CONTEXT = re.compile(r"experien|pengalaman|berpengalaman|work(ing)? in|background", re.I)
_COMPANY_HISTORY = re.compile(r"since|founded|berdiri|company|perusahaan (?:telah|sudah)|over the (?:past|last)|for over|lebih dari \d+ tahun (?:ber|meng)", re.I)


def extract_years(text: str | None) -> tuple[int | None, int | None, str | None]:
    """Highest lower-bound experience mention near an experience cue, with its span.

    When a JD states several requirements ("5+ years in ML, with at least 2 years leading a team"), the bar is the
    strictest one: years_min = the highest per-mention minimum, and the span is the sentence that set it. Taking the
    smallest number would make senior jobs look beginner-friendly, which is the exact failure JobFit must avoid.

    This baseline does not distinguish required/preferred, alternatives or multi-level jobs.
    years_max is an explicit range endpoint only, not an inferred upper limit.
    Returns (years_min, years_max, span). None means not detected, not zero.
    """
    if not text:
        return None, None, None
    mentions = []
    for m in _YEARS.finditer(text):
        a = int(m.group("a"))
        b = int(m.group("b")) if m.group("b") else None
        if not 0 <= a <= 15 or (b is not None and not a <= b <= 20):
            continue
        window = text[max(0, m.start() - 80): m.end() + 80]
        if not _EXP_CONTEXT.search(window) or _COMPANY_HISTORY.search(text[max(0, m.start() - 40): m.start()]):
            continue
        mentions.append((a, b, " ".join(window.split())))
    if not mentions:
        return None, None, None
    return max(mentions, key=lambda mention: mention[0])


_ENTRY = re.compile(r"fresh ?grad\w*|lulusan baru|entry[- ]level|no (?:prior )?(?:work )?experience|tanpa pengalaman|new grad\w*|"
                    r"graduate program|management trainee|\bintern(?:ship)?\b|\bmagang\b|0\s*[-–]\s*[12]\s*(?:years?|tahun)", re.I)


def entry_level_signal(text: str | None, title: str | None = None) -> tuple[bool, str | None]:
    for source in (title or "", text or ""):
        m = _ENTRY.search(source)
        if m:
            return True, " ".join(source[max(0, m.start() - 60): m.end() + 60].split())
    return False, None


def experience_bucket(years_min: int | None, entry_signal: bool) -> str:
    """entry / 1-2y / 3-4y / 5y+ / not_stated. 'not_stated' is UNKNOWN, never treated as entry-level."""
    if years_min == 0 or (entry_signal and (years_min is None or years_min <= 1)):
        return "entry"
    if years_min is None:
        return "not_stated"
    if years_min <= 2:
        return "1-2y"
    if years_min <= 4:
        return "3-4y"
    return "5y+"


_ID_CITY_RULES = [
    ("Jakarta", r"jakarta|\bjkt\b|\bdki\b"), ("Tangerang", r"tangerang|\bbsd\b|serpong"), ("Bekasi", r"bekasi|\bbks\b"),
    ("Depok", r"depok"), ("Bogor", r"bogor"), ("Bandung", r"bandung|lembang|cimahi"), ("Surabaya", r"surabaya|sidoarjo"),
    ("Yogyakarta", r"yogyakarta|jogja|sleman|bantul"), ("Semarang", r"semarang"), ("Malang", r"malang"), ("Batam", r"batam"),
    ("Bali", r"bali|denpasar|badung|buleleng|gianyar"), ("Medan", r"medan"), ("Makassar", r"makassar"), ("Solo", r"surakarta|\bsolo\b"),
]
JABODETABEK = {"Jakarta", "Tangerang", "Bekasi", "Depok", "Bogor"}
_COUNTRY_CODES = {"id": "ID", "sg": "SG", "my": "MY", "ph": "PH", "us": "US", "gb": "GB", "vn": "VN", "th": "TH"}


def normalize_location(location_raw: str | None, country_field: str | None, query_country: str, geo_stratum: str) -> dict:
    """Publisher country/location evidence; query country is never a job-country fallback.

    Preserve geo_stratum as historical sampling metadata. Conflicts require review.
    """
    loc = (location_raw if isinstance(location_raw, str) else "").split("•")[0]
    city = None
    for name, pattern in _ID_CITY_RULES:
        if re.search(pattern, loc, re.I):
            city = name
            break
    country = country_field.upper().strip() if isinstance(country_field, str) and country_field.strip() else None
    source = "provider_country" if country else "unknown"
    if not country and city:
        country, source = "ID", "publisher_location_city"
    if not country:
        for code, pattern in [("ID", r"\bindonesia\b|jawa (?:timur|barat|tengah)|sumat(?:e|ra)ra|kalimantan|sulawesi|banten"), ("SG", r"singapore|singapura"),
                              ("MY", r"malaysia|kuala lumpur|selangor"), ("PH", r"philippines|filipina|manila"),
                              ("US", r"united states|amerika serikat"), ("GB", r"united kingdom"),
                              ("TH", r"thailand|bangkok")]:
            if re.search(pattern, loc, re.I):
                country, source = code, "publisher_location_text"
                break
    conflict = bool((city and country != "ID") or (geo_stratum == "indonesia" and country and country != "ID"))
    return {"country_code": country, "city_normalized": city if country == "ID" else None,
            "metro": ("Jabodetabek" if city in JABODETABEK else city) if country == "ID" else None,
            "location_granularity": "city" if city and country == "ID" else ("country" if country else "unknown"),
            "country_source": source, "location_conflict": conflict}


_HYBRID = _rx(r"\bhybrid\b")
_REMOTE = _rx(r"fully remote|100% remote|remote[- ]first|work from home|\bwfh\b|work from anywhere|\bremote\b(?! (?:sensing|control))")
_ONSITE = _rx(r"on[- ]?site|work from office|\bwfo\b|in[- ]office|di kantor|office[- ]based")


def work_mode(title: str | None, text: str | None, is_remote_flag: bool | None) -> str:
    """hybrid > remote > onsite > unknown, from title first, then provider flag, then JD text."""
    t = title or ""
    if _HYBRID.search(t):
        return "hybrid"
    if _REMOTE.search(t) or is_remote_flag:
        return "remote"
    body = text or ""
    if _HYBRID.search(body):
        return "hybrid"
    if _ONSITE.search(body):
        return "onsite"
    if _REMOTE.search(body):
        return "remote_mentioned"
    return "unknown"


_ELIG_ID = _rx(r"\bindonesia\b")
_ELIG_GLOBAL = _rx(r"worldwide|anywhere in the world|work from anywhere|globally remote|global(?:ly)? distributed|any country")
_ELIG_APAC = _rx(r"\bapac\b|asia[- ]pacific|southeast asia|\bsea\b region|asian time ?zones?")
_ELIG_RESTRICTED = _rx(r"(?:us|u\.s\.)[- ](?:based|only|remote)|authori[sz]ed to work in the (?:us|united states|uk|eu)|"
                       r"must (?:reside|be located|live) in|united states only|us citizens?|green card|no (?:visa )?sponsorship|"
                       r"eligible to work in the (?:us|united states|uk)")


def remote_eligibility(text: str | None) -> str:
    """For remote postings: indonesia_explicit / global_explicit / apac_explicit / restricted_other / unknown.
    Keyword evidence only: 'global_explicit' still needs verification before claiming Indonesia eligibility."""
    body = text or ""
    if _ELIG_RESTRICTED.search(body):
        return "restricted_other"
    if _ELIG_ID.search(body):
        return "indonesia_explicit"
    if _ELIG_GLOBAL.search(body):
        return "global_explicit"
    if _ELIG_APAC.search(body):
        return "apac_explicit"
    return "unknown"


# Education levels mentioned in a JD (EDA signal only; the LLM extractor decides required vs preferred).
_EDU_LEVELS = [
    ("diploma", _rx(r"\bD-?3\b(?!\.js)|\bdiploma\b")),
    ("bachelor", _rx(r"\bS-?1\b|\bbachelor|\bsarjana\b|\bundergraduate\b|\bB\.?Sc\b|\bB\.Tech\b|\bB\.?Eng\b")),
    ("master", _rx(r"\bS-?2\b|\bmaster[\u2019']?s\b|\bmaster (?:degree|of)\b|\bmagister\b|\bM\.?Sc\b|\bM\.Tech\b|\bMBA\b|\bpostgraduate\b")),
    ("phd", _rx(r"\bS-?3\b|\bPh\.?\s?D\b|\bdoctorate\b|\bdoctoral\b")),
]


def education_levels(text: str | None) -> list[str]:
    """Degree levels mentioned anywhere in the JD, e.g. ['bachelor', 'master']. Empty list = not mentioned (UNKNOWN)."""
    return [level for level, rx in _EDU_LEVELS if rx.search(text or "")]
