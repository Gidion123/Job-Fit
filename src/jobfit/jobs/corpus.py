"""Build a provenance-preserving, deduplicated JSearch corpus snapshot.

This is a *collection-steering* tool for CP1.1F, not the final cleaning pipeline:
- every raw slot becomes one record with provenance (file, batch, query, retrieval time);
- exact-key clusters (job_id / job_uid / apply URL / JD content hash / company+title+place)
  give an upper bound of distinct vacancies;
- probable cross-publisher duplicates are *listed for review*, not silently merged,
  giving a lower-bound estimate;
- role / seniority / geography labels here are provisional title/query rules used only to
  see which strata are under-covered. Final labels come from JD review (CP1.3-1.4).

Standard library only. Raw JSON files are read, never modified.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
import zlib
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Heuristic thresholds (documented, adjustable; not ground truth).
JD_INSUFFICIENT_MAX = 200     # characters: vacancy mention only
JD_SUMMARY_MAX = 700          # characters: aggregator summary without requirement list
TITLE_JACCARD_PROBABLE = 0.6  # probable duplicate when same company key and similar title
CONTENT_JACCARD_PROBABLE = 0.5  # probable duplicate when JD 5-gram shingles overlap strongly
GENERIC_FORM_MARKERS = ("globaljob.sbs",)
BATCH_ORDER = {"BENCHMARK": 0, "COL": 1, "B01": 2, "B02": 3, "B03": 4, "B04": 5, "B05A": 6, "B05": 7, "B06": 8, "B07": 9, "B08": 10, "B09": 11, "B10": 12}
LOW_PROVENANCE_PUBLISHER_MARKERS = ("blogspot",)

TARGET_TITLE = re.compile(
    r"\b(ai|a\.i\.|artificial intelligence|machine learning|ml|mlops|llm|genai|generative|"
    r"data scien\w*|deep learning|computer vision|nlp|natural language|rag|agentic)\b", re.I)
ADJACENT_TITLE = re.compile(
    r"\b(data analy\w*|data analis|data engineer\w*|analytics|business intelligence|bi|"
    r"software|backend|back-end|frontend|front-end|full[- ]?stack|developer|engineer\w*|programmer)\b", re.I)
CONTENT_TITLE = re.compile(r"\b(content|creator|copywriter|marketing|sales|social media|video|editor|design\w*)\b", re.I)
INTERN = re.compile(r"\b(intern\w*|magang|trainee|internship)\b", re.I)
JUNIOR = re.compile(r"\b(junior|jr\.?|entry|fresh ?grad\w*|graduate|associate|i)\b", re.I)
SENIOR = re.compile(r"\b(senior|sr\.?|lead|head|principal|staff|manager|director|vp|chief|architect|ii|iii)\b", re.I)
ID_PLACES = re.compile(
    r"indonesia|jakarta|jawa|bandung|surabaya|yogyakarta|sleman|tangerang|bekasi|depok|bogor|bali|"
    r"denpasar|buleleng|semarang|medan|malang|makassar|batam|banten|sumatera|kalimantan|sulawesi", re.I)


def norm(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def company_key(name: object) -> str:
    """Normalize employer names: drop legal forms so 'PT Dot Indonesia' ~ 'DOT Indonesia'."""
    tokens = [t for t in norm(name).split() if t not in {"pt", "tbk", "cv", "sdn", "bhd", "inc", "ltd", "llc", "co", "the"}]
    return " ".join(tokens)


def title_tokens(title: object) -> set[str]:
    stop = {"and", "the", "for", "with", "of", "in", "to", "a", "an", "remote", "hybrid"}
    return {t for t in norm(title).split() if t not in stop and len(t) > 1}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


@dataclass
class Record:
    record_id: str
    source_file: str
    batch: str
    query_id: str
    bucket: str
    query: str
    query_country: str
    query_language: str
    page: int
    retrieved_at_utc: str | None
    source_provider: str
    source_platform: str | None
    source_job_id: str | None
    job_uid: str | None
    apply_url: str | None
    google_url: str | None
    apply_is_direct: bool | None
    company: str | None
    title: str | None
    location_raw: str | None
    city: str | None
    country: str | None
    is_remote_flag: bool | None
    employment_type: str | None
    provider_posted_text: str | None
    posted_at: str | None
    salary_present: bool
    description_length: int
    content_hash: str | None
    jd_quality: str
    provenance_flags: list[str] = field(default_factory=list)
    geo_stratum: str = "unknown"
    role_stratum_provisional: str = "unknown"
    seniority_stratum_provisional: str = "unspecified"
    cluster_id: str = ""            # exact-key cluster
    is_canonical: bool = False      # canonical within the FINAL cluster (after reviewed merges)
    final_cluster_id: str = ""      # exact clusters merged by reviewed SAME decisions
    description: str = ""
    highlights: dict = field(default_factory=dict)


def _batch_of(path: Path) -> str:
    name = path.name
    if "provider_benchmark" in str(path):
        return "BENCHMARK"
    if name.startswith("CP1_JSearch_COL"):
        return "COL"
    m = re.match(r"(B\d{2}[A-Z]?)_", name)
    return m.group(1) if m else "B01"


def iter_sources(root: Path) -> list[tuple[Path, dict]]:
    """Return (response_path, metadata) for every archived JSearch response."""
    out: list[tuple[Path, dict]] = []
    bench = root / "evidence/checkpoint_1/provider_benchmark/jsearch"
    coll = root / "evidence/checkpoint_1/corpus_collection"
    for p in sorted(bench.glob("*.json")) + sorted(coll.glob("*Response.json")):
        params = json.loads(p.read_text(encoding="utf-8")).get("parameters", {})
        country = str(params.get("country", ""))
        out.append((p, {"query_id": p.stem.replace("_Response", "").replace("_Screenshot", ""),
                        "bucket": "indonesia" if country == "id" else "unknown",
                        "parameters_without_cursor": params, "page_in_probe": 1, "retrieved_at_utc": None}))
    raw = root / "data/raw/jsearch"
    for p in sorted(raw.glob("*.json")):
        if p.name.endswith(".meta.json"):
            continue
        meta_path = p.with_name(p.stem + ".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        out.append((p, meta))
    return out


def classify_role(title: str | None) -> str:
    t = title or ""
    if TARGET_TITLE.search(t):
        return "target_family"
    if CONTENT_TITLE.search(t):
        return "wrong_role_content"
    if ADJACENT_TITLE.search(t):
        return "adjacent"
    return "other"


def classify_seniority(title: str | None) -> str:
    t = title or ""
    if INTERN.search(t):
        return "intern"
    if SENIOR.search(t):
        return "senior_lead"
    if JUNIOR.search(t):
        return "junior_entry"
    return "unspecified"


def classify_geo(meta_bucket: str, query_country: str, job: dict) -> str:
    if meta_bucket == "remote_candidate":
        return "remote_unverified"
    loc = " ".join(str(job.get(k) or "") for k in ("job_location", "job_city", "job_state", "job_country"))
    if query_country == "id" or ID_PLACES.search(loc):
        return "indonesia" if ID_PLACES.search(loc) or query_country == "id" else "unknown"
    return "foreign"


def to_records(root: Path) -> list[Record]:
    records: list[Record] = []
    for path, meta in iter_sources(root):
        payload = json.loads(path.read_text(encoding="utf-8"))
        jobs = payload.get("data", {}).get("jobs", []) if isinstance(payload.get("data"), dict) else []
        params = meta.get("parameters_without_cursor") or payload.get("parameters", {})
        rel = str(path.relative_to(root))
        for i, job in enumerate(jobs, start=1):
            desc = job.get("job_description") or ""
            n = len(desc.strip())
            quality = "insufficient" if n < JD_INSUFFICIENT_MAX else "summary_only" if n < JD_SUMMARY_MAX else "full"
            flags = []
            publisher = str(job.get("job_publisher") or "")
            if any(m in publisher.casefold() for m in LOW_PROVENANCE_PUBLISHER_MARKERS):
                flags.append("low_provenance_publisher")
            if any(m in desc.casefold() or m in str(job.get("job_apply_link") or "").casefold() for m in GENERIC_FORM_MARKERS):
                flags.append("generic_external_form")
            if job.get("job_apply_is_direct") is False:
                flags.append("apply_not_direct_per_provider")
            q_country = str(params.get("country", ""))
            records.append(Record(
                record_id=f"{path.stem}#{i}", source_file=rel, batch=_batch_of(path),
                query_id=str(meta.get("query_id") or path.stem), bucket=str(meta.get("bucket") or "unknown"),
                query=str(params.get("query", "")), query_country=q_country, query_language=str(params.get("language", "")),
                page=int(meta.get("page_in_probe") or 1), retrieved_at_utc=meta.get("retrieved_at_utc"),
                source_provider="jsearch", source_platform=job.get("job_publisher"), source_job_id=job.get("job_id"),
                job_uid=job.get("job_uid"), apply_url=job.get("job_apply_link"), google_url=job.get("job_google_link"),
                apply_is_direct=job.get("job_apply_is_direct"), company=job.get("employer_name"), title=job.get("job_title"),
                location_raw=job.get("job_location"), city=job.get("job_city"), country=job.get("job_country"),
                is_remote_flag=job.get("job_is_remote"), employment_type=job.get("job_employment_type"),
                provider_posted_text=job.get("job_posted_at"),
                posted_at=job.get("job_posted_at_datetime_utc") or None,  # never substituted by retrieval time
                salary_present=any(job.get(k) for k in ("job_min_salary", "job_max_salary", "job_salary")),
                description_length=n,
                content_hash=hashlib.sha256(norm(desc).encode()).hexdigest() if n >= JD_INSUFFICIENT_MAX else None,
                jd_quality=quality, provenance_flags=flags,
                geo_stratum=classify_geo(str(meta.get("bucket") or ""), q_country, job),
                role_stratum_provisional=classify_role(job.get("job_title")),
                seniority_stratum_provisional=classify_seniority(job.get("job_title")),
                description=desc, highlights=job.get("job_highlights") or {},
            ))
    return records


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def cluster_exact(records: list[Record]) -> None:
    """Assign cluster_id using exact keys; choose the most complete record as canonical."""
    uf = _UnionFind(len(records))
    seen: dict[tuple[str, str], int] = {}
    for i, r in enumerate(records):
        place = norm(r.city or r.location_raw)
        keys = [("id", r.source_job_id or ""), ("uid", r.job_uid or ""), ("url", norm(r.apply_url)),
                ("hash", r.content_hash or ""),
                ("ctp", "|".join((company_key(r.company), norm(r.title), place)) if r.company and r.title else "")]
        for kind, key in keys:
            if not key:
                continue
            if (kind, key) in seen:
                uf.union(seen[(kind, key)], i)
            else:
                seen[(kind, key)] = i
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(records)):
        groups[uf.find(i)].append(i)
    rank = {"full": 2, "summary_only": 1, "insufficient": 0}
    for n, members in enumerate(sorted(groups.values(), key=min), start=1):
        cid = f"C{n:05d}"
        best = max(members, key=lambda i: (rank[records[i].jd_quality], records[i].description_length, -i))
        for i in members:
            records[i].cluster_id = cid
            records[i].is_canonical = i == best


def _shingles(text: str, k: int = 5) -> set[int]:
    toks = norm(text).split()
    # zlib.crc32 is stable across processes (built-in hash() is randomized per run).
    return {zlib.crc32(" ".join(toks[j:j + k]).encode()) for j in range(max(0, len(toks) - k + 1))}


def probable_duplicates(records: list[Record]) -> list[dict]:
    """Candidate same-vacancy pairs between exact clusters, for manual review (never auto-merged).

    Detector A (company_title): same normalized employer key and title-token Jaccard >= TITLE_JACCARD_PROBABLE.
    Detector B (content): JD 5-gram shingle Jaccard >= CONTENT_JACCARD_PROBABLE, catching syndicated copies
    posted under a recruiter or a differently spelled employer name.
    """
    best_by_cluster = _cluster_best(records)
    canon = [r for r in records if r.cluster_id and r.record_id == best_by_cluster[r.cluster_id]]
    found: dict[tuple[str, str], dict] = {}

    def add(a: Record, b: Record, reason: str, tj: float, cj: float | None) -> None:
        key = tuple(sorted((a.record_id, b.record_id)))
        item = found.setdefault(key, {"record_a": key[0], "record_b": key[1], "reasons": set(), "title_jaccard": round(tj, 2),
                                      "content_jaccard": None if cj is None else round(cj, 2)})
        item["reasons"].add(reason)
        if cj is not None:
            item["content_jaccard"] = round(cj, 2)

    by_company: dict[str, list[Record]] = defaultdict(list)
    for r in canon:
        if r.company:
            by_company[company_key(r.company)].append(r)
    shingles = {r.record_id: _shingles(r.description) for r in canon if r.description_length >= JD_INSUFFICIENT_MAX}

    def cj_of(a: Record, b: Record) -> float | None:
        sa, sb = shingles.get(a.record_id), shingles.get(b.record_id)
        return (len(sa & sb) / len(sa | sb)) if sa and sb else None

    for items in by_company.values():
        for x in range(len(items)):
            for y in range(x + 1, len(items)):
                a, b = items[x], items[y]
                tj = jaccard(title_tokens(a.title), title_tokens(b.title))
                if tj >= TITLE_JACCARD_PROBABLE and a.geo_stratum == b.geo_stratum:
                    add(a, b, "company_title", tj, cj_of(a, b))
    # Detector B via an inverted index on a sample of shingles (hash % 4 == 0) to avoid all-pairs work.
    index: dict[int, list[str]] = defaultdict(list)
    for rid, sh in shingles.items():
        for h in sh:
            if h % 4 == 0:
                index[h].append(rid)
    by_id = {r.record_id: r for r in canon}
    candidates: set[tuple[str, str]] = set()
    for rids in index.values():
        if 1 < len(rids) <= 50:  # very common shingles are boilerplate, skip
            for x in range(len(rids)):
                for y in range(x + 1, len(rids)):
                    candidates.add(tuple(sorted((rids[x], rids[y]))))
    for ra, rb in candidates:
        a, b = by_id[ra], by_id[rb]
        cj = cj_of(a, b)
        if cj is not None and cj >= CONTENT_JACCARD_PROBABLE:
            add(a, b, "content", jaccard(title_tokens(a.title), title_tokens(b.title)), cj)
    pairs = []
    for item in found.values():
        a, b = by_id[item["record_a"]], by_id[item["record_b"]]
        pairs.append({**item, "reasons": "+".join(sorted(item["reasons"])),
                      "company_a": a.company, "company_b": b.company, "title_a": a.title, "title_b": b.title,
                      "location_a": a.location_raw, "location_b": b.location_raw,
                      "publisher_a": a.source_platform, "publisher_b": b.source_platform,
                      "jd_len_a": a.description_length, "jd_len_b": b.description_length})
    return sorted(pairs, key=lambda p: (p["record_a"], p["record_b"]))


def _cluster_best(records: list[Record]) -> dict[str, str]:
    """record_id of the most complete record in each exact cluster."""
    rank = {"full": 2, "summary_only": 1, "insufficient": 0}
    best: dict[str, Record] = {}
    for r in records:
        cur = best.get(r.cluster_id)
        if cur is None or (rank[r.jd_quality], r.description_length) > (rank[cur.jd_quality], cur.description_length):
            best[r.cluster_id] = r
    return {cid: r.record_id for cid, r in best.items()}


def load_decisions(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {tuple(sorted((row["record_a"], row["record_b"]))): row for row in csv.DictReader(fh)}


def apply_decisions(records: list[Record], decisions: dict[tuple[str, str], dict]) -> int:
    """Merge exact clusters joined by reviewed SAME decisions; set final_cluster_id and final canonical record."""
    by_id = {r.record_id: r for r in records}
    cids = sorted({r.cluster_id for r in records})
    idx = {c: i for i, c in enumerate(cids)}
    uf = _UnionFind(len(cids))
    merged = 0
    for (ra, rb), row in decisions.items():
        if row.get("decision", "").strip().upper() == "SAME" and ra in by_id and rb in by_id:
            uf.union(idx[by_id[ra].cluster_id], idx[by_id[rb].cluster_id])
            merged += 1
    groups: dict[int, list[Record]] = defaultdict(list)
    for r in records:
        groups[uf.find(idx[r.cluster_id])].append(r)
    rank = {"full": 2, "summary_only": 1, "insufficient": 0}
    for members in groups.values():
        fid = min(m.cluster_id for m in members).replace("C", "F", 1)
        best = max(members, key=lambda m: (rank[m.jd_quality], m.description_length, m.record_id))
        for m in members:
            m.final_cluster_id = fid
            m.is_canonical = m is best
    return merged


def build(root: Path) -> dict:
    records = to_records(root)
    cluster_exact(records)
    n_exact = len({r.cluster_id for r in records})
    pairs = probable_duplicates(records)
    decisions_path = root / "data/interim/dedup_decisions.csv"
    decisions = load_decisions(decisions_path)
    merged_pairs = apply_decisions(records, decisions)
    canon = [r for r in records if r.is_canonical]
    auditable = [r for r in canon if r.jd_quality == "full" and "generic_external_form" not in r.provenance_flags]

    interim = root / "data/interim"
    interim.mkdir(parents=True, exist_ok=True)
    with (interim / "jsearch_records.jsonl").open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    cols = ["final_cluster_id", "cluster_id", "record_id", "batch", "query", "geo_stratum", "role_stratum_provisional",
            "seniority_stratum_provisional", "jd_quality", "description_length", "company", "title",
            "location_raw", "source_platform", "provider_posted_text", "posted_at", "apply_url", "provenance_flags"]
    with (interim / "jsearch_canonical.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in canon:
            row = {c: getattr(r, c) for c in cols}
            row["provenance_flags"] = ";".join(r.provenance_flags)
            w.writerow(row)
    review_fields = ["record_a", "record_b", "reasons", "title_jaccard", "content_jaccard", "company_a", "company_b",
                     "title_a", "title_b", "location_a", "location_b", "publisher_a", "publisher_b", "jd_len_a", "jd_len_b",
                     "decision", "rationale"]
    undecided = 0
    with (interim / "jsearch_probable_duplicates_review.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=review_fields)
        w.writeheader()
        for p in pairs:
            d = decisions.get((p["record_a"], p["record_b"]), {})
            p = {**p, "decision": d.get("decision", ""), "rationale": d.get("rationale", "")}
            undecided += not p["decision"]
            w.writerow({k: p.get(k) for k in review_fields})

    def dist(rs: list[Record], attr: str) -> dict:
        return dict(Counter(getattr(r, attr) for r in rs).most_common())

    batches = defaultdict(lambda: {"responses": set(), "slots": 0, "new_clusters": 0})
    for path, _ in iter_sources(root):  # include empty responses in the response count
        batches[_batch_of(path)]["responses"].add(str(path.relative_to(root)))
    first_batch: dict[str, str] = {}
    chronological = sorted(records, key=lambda r: (BATCH_ORDER.get(r.batch, 99), r.retrieved_at_utc or "", r.record_id))
    for r in chronological:
        b = batches[r.batch]
        b["responses"].add(r.source_file)
        b["slots"] += 1
        if r.final_cluster_id not in first_batch:
            first_batch[r.final_cluster_id] = r.batch
            b["new_clusters"] += 1
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counting_rule": "distinct_exact = exact-key clusters; distinct_final = exact clusters after merging reviewed SAME pairs "
                         "(UNSURE/undecided pairs stay separate). auditable_candidates = final canonical record with full JD "
                         "(>= %d chars) and no generic external form. Strata are provisional title/query rules, not final labels." % JD_SUMMARY_MAX,
        "raw_slots": len(records),
        "distinct_exact_clusters": n_exact,
        "probable_duplicate_pairs": len(pairs),
        "pairs_reviewed": len(pairs) - undecided,
        "pairs_merged_same": merged_pairs,
        "distinct_final": len(canon),
        "auditable_candidates_full_jd": len(auditable),
        "jd_quality_canonical": dist(canon, "jd_quality"),
        "geo_canonical": dist(canon, "geo_stratum"),
        "role_canonical_provisional": dist(canon, "role_stratum_provisional"),
        "seniority_canonical_provisional": dist(canon, "seniority_stratum_provisional"),
        "auditable_by_geo": dist(auditable, "geo_stratum"),
        "auditable_by_role_provisional": dist(auditable, "role_stratum_provisional"),
        "auditable_by_seniority_provisional": dist(auditable, "seniority_stratum_provisional"),
        "structured_posted_at_present_canonical": sum(1 for r in canon if r.posted_at),
        "by_batch_first_seen": {k: {"responses": len(v["responses"]), "slots": v["slots"], "new_clusters": v["new_clusters"]}
                                for k, v in sorted(batches.items(), key=lambda kv: BATCH_ORDER.get(kv[0], 99))},
    }
    (root / "data/research/CP1_Corpus_Progress.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
