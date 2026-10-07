"""Versioned offline quote and OR-group validation for D-066.

The model quote is retained in the audit record. The evaluated quote is an
actual contiguous span of the CV. This module does not change the v1 runtime.
"""
from __future__ import annotations

from copy import deepcopy
import re
import unicodedata


class QuoteResolutionError(ValueError):
    pass


def _tokens(text: str) -> list[tuple[str, int, int]]:
    chars: list[str] = []
    positions: list[int] = []
    for pos, original in enumerate(text):
        for char in unicodedata.normalize("NFKC", original):
            # Keep C++, C# and similar tool names distinct from a bare letter.
            chars.append(char if char.isalnum() or char in "+#" else " ")
            positions.append(pos)
    normalized = "".join(chars)
    return [(m.group(), positions[m.start()], positions[m.end() - 1] + 1)
            for m in re.finditer(r"[^\W_]+(?:\+\+|#)?", normalized, re.UNICODE)]


def resolve_quote(model_quote: str, cv_text: str) -> dict:
    """Return one actual CV span; reject changed words and ambiguous spans."""
    if not model_quote.strip():
        raise QuoteResolutionError("empty_quote")
    def boundary(start: int, end: int) -> bool:
        lexical = lambda char: char.isalnum() or char in "+#_"
        return (start == 0 or not lexical(cv_text[start - 1])) and (end == len(cv_text) or not lexical(cv_text[end]))
    exact = [m for m in re.finditer(re.escape(model_quote), cv_text) if boundary(m.start(), m.end())]
    if len(exact) == 1:
        m = exact[0]
        return {"model_quote": model_quote, "cv_span": cv_text[m.start():m.end()],
                "start": m.start(), "end": m.end(), "flags": []}
    if len(exact) > 1:
        raise QuoteResolutionError("ambiguous_source_span")
    source = _tokens(cv_text)
    wanted = [t[0] for t in _tokens(model_quote)]
    if not wanted:
        raise QuoteResolutionError("empty_quote_tokens")
    for insensitive in (False, True):
        target = [s.casefold() for s in wanted] if insensitive else wanted
        hits = []
        for i in range(len(source) - len(target) + 1):
            words = [t[0].casefold() for t in source[i:i + len(target)]] if insensitive else [t[0] for t in source[i:i + len(target)]]
            if words == target:
                start, end = source[i][1], source[i + len(target) - 1][2]
                hits.append((start, end))
        if hits:
            if len(hits) != 1:
                raise QuoteResolutionError("ambiguous_source_span")
            start, end = hits[0]
            return {"model_quote": model_quote, "cv_span": cv_text[start:end],
                    "start": start, "end": end,
                    "flags": ["normalized_separators"] + (["casefold_fallback"] if insensitive else [])}
    raise QuoteResolutionError("changed_or_invented_word")


_BRANCH_ALIASES = {
    "statistics": {"statistics", "statistika"},
    "mathematics": {"mathematics", "matematika"},
    "computer science": {"computer science", "ilmu komputer"},
    "informatics engineering": {"informatics engineering", "teknik informatika"},
    "data science": {"data science"},
}
_TOOL_ANCHORS = {"python", "sql", "pandas", "scikit-learn", "tensorflow", "pytorch",
                 "tableau", "power bi", "matplotlib", "hadoop", "spark", "aws", "gcp"}


def _supported_branch_ids(branches: list[dict], spans: list[str]) -> list[str]:
    quoted = " ".join(spans).casefold()
    found = []
    for branch in branches:
        description = branch["text"].casefold()
        anchors = set()
        for key, names in _BRANCH_ALIASES.items():
            if key in description:
                anchors.update(names)
        anchors.update(t for t in _TOOL_ANCHORS if t in description)
        if anchors and any(re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", quoted) for a in anchors):
            found.append(branch["branch_id"])
    return found


def normalize_assessments_v11(assessments: list[dict], units: list[dict], cv_text: str) -> tuple[list[dict], list[dict]]:
    """Return source-grounded copies and explicit change records, or fail closed."""
    revised = deepcopy(assessments)
    by_id = {u["unit_id"]: u for u in units}
    flags: list[dict] = []
    if len(revised) != len(by_id) or {a["unit_id"] for a in revised} != set(by_id):
        raise ValueError("assessment_coverage")
    for assessment in revised:
        unit_id = assessment["unit_id"]
        unit = by_id[unit_id]
        branches = assessment.get("branches", [])
        if branches and any(b.get("label") is not None for b in branches):
            if assessment.get("label") is not None or assessment.get("cv_quotes"):
                assessment["label"] = None
                assessment["cv_quotes"] = []
                flags.append({"unit_id": unit_id, "kind": "parent_ignored_branch_labels_present"})
        for item in [assessment, *assessment.get("branches", [])]:
            resolved = []
            for quote in item.get("cv_quotes", []):
                result = resolve_quote(quote, cv_text)
                resolved.append(result)
                flags.append({"unit_id": unit_id, "branch_id": item.get("branch_id"),
                              "kind": "quote_normalized" if result["flags"] else "quote_exact", **result})
            item["cv_quotes"] = [r["cv_span"] for r in resolved]
        if not branches:
            continue
        parent_has_content = assessment.get("label") is not None or bool(assessment.get("cv_quotes"))
        if not parent_has_content:
            continue
        if any(b.get("label") is not None for b in branches):
            raise ValueError("unresolved_parent_with_labeled_branches")
        if assessment.get("label") != "MATCH" or not assessment.get("cv_quotes"):
            raise ValueError("ambiguous_parent_group_label")
        supported = _supported_branch_ids(unit.get("branches", []), assessment["cv_quotes"])
        if len(supported) != 1:
            raise ValueError("ambiguous_parent_group_label")
        selected = supported[0]
        for branch in branches:
            if branch["branch_id"] == selected:
                branch["label"] = assessment["label"]
                branch["cv_quotes"] = assessment["cv_quotes"]
                branch["check_status"] = "done"
            else:
                branch["label"] = None
                branch["cv_quotes"] = []
                branch["check_status"] = "failed"
        assessment["label"] = None
        assessment["cv_quotes"] = []
        flags.append({"unit_id": unit_id, "kind": "parent_moved_unique_branch", "branch_id": selected})
    return revised, flags
