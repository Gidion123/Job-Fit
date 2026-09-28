#!/usr/bin/env python3
"""Build a varied JSearch query plan, collect capped raw responses, and inventory evidence.

Only Python's standard library is required. The API key is read from JSEARCH_API_KEY
at request time and is never written to disk or printed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/research/CP1_JSearch_Query_Plan.csv"
RAW = ROOT / "data/raw/jsearch"
INVENTORY = ROOT / "data/research/CP1_JSearch_Seed_Inventory.json"
FIELDS = ("query_id", "bucket", "role_probe", "seniority_probe", "query", "country", "language", "work_from_home")
PILOT_IDS = (
    "ID_MLE_JAK_JUNIOR", "ID_DAS_SUR_MID", "ID_AIE_BAN_SENIOR",
    "ID_GEN_YOG_JUNIOR", "ID_BAI_JAK_MID", "REMOTE_MLE_JUNIOR",
    "REMOTE_DAS_MID", "REMOTE_GEN_SENIOR", "GLOBAL_US_AIE_JUNIOR",
    "GLOBAL_SG_BAI_SENIOR", "CONTROL_ANL_BAN", "CONTROL_CNT_JAK",
)


def norm(value: object) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_plan(_: argparse.Namespace) -> None:
    if PLAN.exists():
        raise SystemExit(f"Plan already exists; preserved: {PLAN}")
    roles = (
        ("MLE", "Machine Learning Engineer"),
        ("DAS", "Data Scientist"),
        ("AIE", "AI Engineer"),
        ("GEN", "Generative AI Engineer"),
        ("BAI", "Backend Engineer AI"),
    )
    seniority = (("junior", "Junior"), ("mid", "Mid Level"), ("senior", "Senior"))
    id_cities = ("Jakarta", "Bandung", "Surabaya", "Yogyakarta")
    abroad = (("us", "United States"), ("sg", "Singapore"))
    rows: list[dict[str, str]] = []
    for code, role in roles:
        for city in id_cities:
            for level, prefix in seniority:
                rows.append(dict(query_id=f"ID_{code}_{city[:3].upper()}_{level.upper()}", bucket="indonesia", role_probe=role, seniority_probe=level, query=f"{prefix} {role} in {city}", country="id", language="id", work_from_home=""))
        for level, prefix in seniority:
            rows.append(dict(query_id=f"REMOTE_{code}_{level.upper()}", bucket="remote_candidate", role_probe=role, seniority_probe=level, query=f"Remote {prefix} {role} in Indonesia", country="id", language="en", work_from_home="true"))
        for country, place in abroad:
            for level, prefix in seniority:
                rows.append(dict(query_id=f"GLOBAL_{country.upper()}_{code}_{level.upper()}", bucket="foreign_comparison", role_probe=role, seniority_probe=level, query=f"{prefix} {role} in {place}", country=country, language="en", work_from_home=""))
    for city in id_cities:
        for code, role in (("ANL", "Data Analyst"), ("CNT", "AI Content Creator")):
            rows.append(dict(query_id=f"CONTROL_{code}_{city[:3].upper()}", bucket="role_contrast", role_probe=role, seniority_probe="unspecified", query=f"{role} in {city}", country="id", language="id", work_from_home=""))
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    with PLAN.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} distinct query probes to {PLAN}")
    print("These are sampling probes, not job labels or evidence of work eligibility.")


def read_plan(path: Path = PLAN) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit("Query plan is missing. Run: python3 scripts/jsearch_collection.py make-plan")
    if path.suffix == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))["queries"]
    else:
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    if not rows or any(set(FIELDS) - set(row) for row in rows):
        raise SystemExit("Query plan is empty or missing required fields")
    ids = [r["query_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("Query plan has duplicate query IDs")
    return rows


def get_usage(key: str) -> tuple[str, bool, int | None]:
    """Read the provider's quota endpoint without storing or displaying the key."""
    request = urllib.request.Request(
        "https://api.openwebninja.com/usage?api_id=jsearch",
        headers={"x-api-key": key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(
            f"Could not verify current JSearch quota ({type(exc).__name__}); no collection requests sent."
        ) from None
    data = payload.get("data", {})
    plan = data.get("plan", {})
    is_free = plan.get("is_free") is True
    name = str(plan.get("nickname") or plan.get("key") or "unknown")
    quotas = data.get("quotas") or []
    request_quota = next((q for q in quotas if str(q.get("name", "")).casefold() == "requests"), None)
    remaining = request_quota.get("remaining") if request_quota else None
    if isinstance(remaining, bool) or not isinstance(remaining, int):
        remaining = None
    if is_free and remaining is None:
        raise SystemExit("Free plan detected but remaining quota is unavailable; no collection requests sent.")
    if data.get("status") in ("exceeded", "inactive", "canceled", "past_due"):
        raise SystemExit(f"JSearch subscription status is {data['status']}; no collection requests sent.")
    return name, is_free, remaining


def collect(args: argparse.Namespace) -> None:
    rows = read_plan(args.plan)
    if args.pilot:
        rows_by_id = {row["query_id"]: row for row in rows}
        rows = [rows_by_id[query_id] for query_id in PILOT_IDS]
    if args.query_id:
        rows = [r for r in rows if r["query_id"] in args.query_id]
        unknown = set(args.query_id) - {r["query_id"] for r in rows}
        if unknown:
            raise SystemExit(f"Unknown query ID(s): {', '.join(sorted(unknown))}")
    if args.bucket:
        rows = [r for r in rows if r["bucket"] == args.bucket]
    if args.max_requests < 1 or args.pages_per_query < 1:
        raise SystemExit("Request cap and pages per query must be positive")
    if not args.execute:
        print(f"Dry run: {len(rows)} matching probes; at most {args.max_requests} requests this run")
        for row in rows[: args.max_requests]:
            print(row["query_id"], row["query"])
        print("Add --execute to send requests. Set JSEARCH_API_KEY in the environment first.")
        return
    key = os.environ.get("JSEARCH_API_KEY")
    if not key:
        raise SystemExit("JSEARCH_API_KEY is not set. No requests were sent.")
    plan_name, is_free, remaining = get_usage(key)
    print(f"Verified JSearch plan: {plan_name}; remaining request quota: {remaining if remaining is not None else 'not reported'}")
    if args.free_only and not is_free:
        raise SystemExit("This batch is Free/Basic only; no collection requests sent on a paid or unverified plan.")
    effective_cap = min(args.max_requests, remaining) if is_free else args.max_requests
    if effective_cap < 1:
        print("No verified Free-plan requests remain; no collection requests sent.")
        return
    RAW.mkdir(parents=True, exist_ok=True)
    sent = 0
    reserved_units = 0
    try:
        for row in rows:
            cursor = None
            first_page = 1
            cursor_source = None
            # Optional continuation: resume a probe from the cursor saved in an earlier archived response.
            if row.get("start_cursor_file"):
                source = ROOT / row["start_cursor_file"]
                try:
                    cursor = json.loads(source.read_text(encoding="utf-8"))["data"].get("cursor")
                except (OSError, KeyError, ValueError, AttributeError):
                    cursor = None
                if not cursor:
                    print(f"Skipping {row['query_id']}: no saved cursor in {row['start_cursor_file']}")
                    continue
                first_page = int(row.get("start_page") or 2)
                cursor_source = row["start_cursor_file"]
            pages_this_probe = int(row.get("max_pages") or args.pages_per_query)
            last_page = first_page + pages_this_probe - 1
            for page in range(first_page, last_page + 1):
                if sent >= effective_cap:
                    print(f"Reached per-run cap: {sent} requests")
                    return
                prefix = RAW / f"{row['query_id']}_P{page:02d}"
                response_path = prefix.with_suffix(".json")
                if response_path.exists():
                    print("Skipping existing raw response:", response_path.name)
                    if page < last_page:
                        try:
                            cursor = json.loads(response_path.read_text(encoding="utf-8"))["data"].get("cursor")
                        except (KeyError, ValueError):
                            cursor = None
                    if page > 1 and not cursor:
                        break
                    continue
                if page > 1 and not cursor:
                    break
                params = {"query": row["query"], "country": row["country"], "language": row["language"], "num_pages": str(row.get("num_pages") or "1")}
                page_units = int(params["num_pages"])
                if page_units < 1:
                    raise SystemExit("num_pages must be positive; no request sent for this probe.")
                if is_free and reserved_units + page_units > remaining:
                    print(f"Stopping before request: {page_units} page units exceed remaining verified free budget.")
                    return
                if row["work_from_home"]:
                    params["work_from_home"] = row["work_from_home"]
                if cursor:
                    params["cursor"] = cursor
                url = "https://api.openwebninja.com/jsearch/search-v2?" + urllib.parse.urlencode(params)
                request = urllib.request.Request(url, headers={"x-api-key": key, "Accept": "application/json"})
                # Multi-page calls are fetched server-side sequentially and need a longer timeout.
                timeout_s = min(180, max(45, 50 * int(params['num_pages'])))
                sent += 1
                reserved_units += page_units  # Reserve before sending, including failed attempts.
                started = time.monotonic()
                try:
                    with urllib.request.urlopen(request, timeout=timeout_s) as response:
                        body = response.read()
                        code = response.status
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                    print(f"Request {row['query_id']} page {page} failed: {type(exc).__name__} / HTTP {getattr(exc, 'code', 'unknown')}; stopped. No automatic retry.", file=sys.stderr)
                    raise SystemExit(1)
                elapsed = round(time.monotonic() - started, 3)
                try:
                    parsed = json.loads(body)
                except ValueError:
                    print(f"Non-JSON response for {row['query_id']} page {page}; stopped", file=sys.stderr)
                    raise SystemExit(1)
                if code != 200 or parsed.get("status") != "OK" or not isinstance(parsed.get("data", {}).get("jobs"), list):
                    print(f"Unexpected response for {row['query_id']} page {page}; stopped", file=sys.stderr)
                    raise SystemExit(1)
                response_path.write_bytes(body)
                metadata = {
                    "query_id": row["query_id"], "bucket": row["bucket"], "role_probe": row["role_probe"],
                    "seniority_probe": row["seniority_probe"], "parameters_without_cursor": {k: v for k, v in params.items() if k != "cursor"},
                    "page_in_probe": page, "retrieved_at_utc": utc_now(), "http_status": code,
                    "elapsed_seconds": elapsed, "timeout_seconds": timeout_s, "response_sha256": hashlib.sha256(body).hexdigest(),
                    "job_slots": len(parsed["data"]["jobs"]), "provider_request_id": parsed.get("request_id"),
                    "cursor_used": bool(params.get("cursor")),
                    "cursor_source": (cursor_source if page == first_page else "previous page in this probe") if params.get("cursor") else None,
                }
                prefix.with_suffix(".meta.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"Saved {row['query_id']} page {page}: {metadata['job_slots']} slots, {elapsed}s")
                cursor = parsed["data"].get("cursor")
                if not parsed["data"]["jobs"]:
                    break
                if sent < effective_cap:
                    time.sleep(1)
        print(f"Completed {sent} requests; raw files in {RAW}")
    finally:
        if sent:
            try:
                _, _, remaining_after = get_usage(key)
            except SystemExit:
                remaining_after = None
            if remaining is not None and remaining_after is not None:
                print(f"Quota check: requests sent {sent}; quota consumed {remaining - remaining_after} "
                      f"(before {remaining}, after {remaining_after}). Provider usage may lag a few seconds.")
            else:
                print(f"Quota check: requests sent {sent}; remaining quota not reported after run.")


def inventory(_: argparse.Namespace) -> None:
    benchmark = ROOT / "evidence/checkpoint_1/provider_benchmark/jsearch"
    collection = ROOT / "evidence/checkpoint_1/corpus_collection"
    # JS02's historical JSON has a Screenshot.json suffix; include it without renaming evidence.
    sources = list(benchmark.glob("*.json")) + list(collection.glob("*Response.json"))
    sources += [p for p in RAW.glob("*.json") if not p.name.endswith(".meta.json")]
    seen_ids: dict[str, str] = {}
    seen_urls: dict[str, str] = {}
    seen_heuristic: dict[str, str] = {}
    exact_collisions = []
    jobs_total = 0
    quality = Counter()
    by_source = []
    for path in sorted(sources):
        data = json.loads(path.read_text(encoding="utf-8"))
        jobs = data.get("data", {}).get("jobs", [])
        if not isinstance(jobs, list):
            raise SystemExit(f"Invalid jobs array: {path}")
        by_source.append({"file": str(path.relative_to(ROOT)), "slots": len(jobs), "query": data.get("parameters", {}).get("query")})
        for index, job in enumerate(jobs, start=1):
            jobs_total += 1
            label = f"{path.name}#{index}"
            desc = job.get("job_description") or ""
            if len(desc.strip()) < 500:
                quality["descriptions_under_500_chars"] += 1
            if not job.get("job_posted_at_datetime_utc") and not job.get("job_posted_at_timestamp"):
                quality["structured_posted_time_missing"] += 1
            if not job.get("job_apply_link"):
                quality["apply_url_missing"] += 1
            if not job.get("job_city") or not job.get("job_country"):
                quality["city_or_country_missing"] += 1
            key_sets = (
                ("provider_job_id", str(job.get("job_id") or ""), seen_ids),
                ("normalized_apply_url", norm(job.get("job_apply_link")), seen_urls),
                ("company_title_city", "|".join((norm(job.get("employer_name")), norm(job.get("job_title")), norm(job.get("job_city")))), seen_heuristic),
            )
            for key_type, key, seen in key_sets:
                if not key or key == "||":
                    continue
                if key in seen:
                    exact_collisions.append({"type": key_type, "first": seen[key], "again": label})
                else:
                    seen[key] = label
    report = {
        "generated_at_utc": utc_now(), "input_files": len(sources), "raw_result_slots": jobs_total,
        "unique_provider_job_ids": len(seen_ids), "unique_normalized_apply_urls": len(seen_urls),
        "unique_company_title_city_keys": len(seen_heuristic), "quality_flags": dict(quality),
        "exact_key_collisions": exact_collisions, "files": by_source,
        "caveat": "Inventory only. Distinct keys are not confirmed distinct usable vacancies; fuzzy cross-source duplicates, role, seniority, provenance, and JD quality still require review.",
    }
    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Inventory: {len(sources)} files; {jobs_total} raw slots; {len(seen_heuristic)} company/title/city keys")
    print("Quality flags:", dict(quality))
    print("Written:", INVENTORY)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("make-plan")
    commands.add_parser("inventory")
    collector = commands.add_parser("collect")
    collector.add_argument("--plan", type=Path, default=PLAN, help="CSV or JSON query manifest")
    collector.add_argument("--free-only", action="store_true", help="Refuse collection on a paid or unverified plan")
    collector.add_argument("--execute", action="store_true", help="Send API requests; default is dry run")
    collector.add_argument("--max-requests", type=int, default=5, help="Hard per-run request cap (default: 5)")
    collector.add_argument("--pages-per-query", type=int, default=1, help="Maximum cursor pages per query (default: 1)")
    collector.add_argument("--query-id", action="append", help="Select one query ID; repeatable")
    collector.add_argument("--bucket", choices=("indonesia", "remote_candidate", "foreign_comparison", "role_contrast"))
    collector.add_argument("--pilot", action="store_true", help="Run the 12-query balanced first pilot")
    args = parser.parse_args()
    if args.command == "make-plan":
        make_plan(args)
    elif args.command == "collect":
        collect(args)
    else:
        inventory(args)


if __name__ == "__main__":
    main()
