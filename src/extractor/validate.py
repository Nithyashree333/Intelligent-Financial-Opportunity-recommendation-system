"""Validation and return-type classification."""
from __future__ import annotations

import re

from ..schemas import Opportunity, ReturnType

_RETURN_TYPE_PATTERNS: list[tuple[ReturnType, str]] = [
    ("coupon", r"\bcoupon\b"),
    ("historical", r"\bhistorical(ly)?\b|past performance"),
    ("illustrative", r"\billustrat"),
    ("variable", r"\bvariable\b|market[- ]linked"),
    ("indicative", r"\bindicative|expected|target"),
]


def classify_return_type(text: str) -> ReturnType:
    """Classify the flavour of return the document states (first match wins;
    ordered so explicit types beat generic 'expected')."""
    for rtype, pat in _RETURN_TYPE_PATTERNS:
        if re.search(pat, text, re.I):
            return rtype
    return "unknown"


def validate(raw: dict) -> Opportunity:
    """Pydantic-parse a raw record; raises with field-level detail on failure."""
    return Opportunity(**raw)
