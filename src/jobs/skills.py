"""Deterministic skill extraction from JD text using the versioned alias file (config/skill_aliases_v0.yaml).

This is a transparent keyword baseline for EDA and market counts. It detects *mentions*, not whether a
skill is required or preferred — that distinction is the LLM extractor's job (CP2).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_ALIAS_FILE = Path(__file__).resolve().parents[2] / "config/skill_aliases_v0.yaml"


@lru_cache(maxsize=4)
def load_skill_patterns(path: str = str(DEFAULT_ALIAS_FILE)) -> tuple[str, dict[str, tuple[str, re.Pattern]]]:
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    patterns: dict[str, tuple[str, re.Pattern]] = {}
    for name, item in spec["skills"].items():
        flags = 0 if item.get("case_sensitive") else re.I
        if item.get("regex"):
            rx = item["regex"]
        else:
            alts = sorted((re.escape(a) for a in item["aliases"]), key=len, reverse=True)
            rx = r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])"
        patterns[name] = (item["category"], re.compile(rx, flags))
    return spec["version"], patterns


def extract_skills(text: str | None, path: str = str(DEFAULT_ALIAS_FILE)) -> list[str]:
    """Canonical skill names mentioned in the text, sorted. Empty list when nothing matches."""
    if not text:
        return []
    _, patterns = load_skill_patterns(path)
    return sorted(name for name, (_, rx) in patterns.items() if rx.search(text))


def skill_category(name: str, path: str = str(DEFAULT_ALIAS_FILE)) -> str:
    return load_skill_patterns(path)[1][name][0]
