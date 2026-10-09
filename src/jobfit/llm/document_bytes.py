"""Canonical size of one payload value, as the frozen cost guard measures it (D-103).

The frozen ``validated_call`` puts the payload into the user message as
``json.dumps({'untrusted_document_data': payload}, ensure_ascii=False)``, and the frozen
``OpenRouterClient`` guard measures ``len(json.dumps(messages, ensure_ascii=False).encode('utf-8'))``.
Every value of the payload is therefore JSON-encoded twice. JSON escaping works character by
character, so a value adds exactly the UTF-8 bytes of its twice-encoded form, wherever it sits in
the payload. ``document_bytes`` is that number. It is the one size measure shared by the public-beta
bounds calculator, runtime admission and the tests; it is not a characters-times-N heuristic.
"""
from __future__ import annotations

import json


def document_bytes(value) -> int:
    """UTF-8 bytes ``value`` adds to the guard-measured messages when it is a payload value.

    A string counts its two (escaped) quote characters as well. Text that cannot be encoded as
    UTF-8 (a lone surrogate) raises UnicodeEncodeError, like the frozen guard would.
    """
    once = json.dumps(value, ensure_ascii=False)
    return len(json.dumps(once, ensure_ascii=False).encode('utf-8')) - 2


def text_content_bytes(text: str) -> int:
    """``document_bytes`` of a string without its two escaped quotes (4 bytes)."""
    return document_bytes(text) - 4
