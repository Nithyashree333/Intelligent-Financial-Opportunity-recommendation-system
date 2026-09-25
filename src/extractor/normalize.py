"""Normalize messy financial expressions into clean numerics.

Money: 'Rs. 5 lakh', 'INR 1.5 crore', '2,00,000', '500000 rupees' -> int INR.
Tenure: '2 years', '24 months', '18-36 months', '1.5 yrs' -> (min, max) months.
Unknown input -> None (never guess).
"""
from __future__ import annotations

import re

LAKH = 100_000
CRORE = 10_000_000

# Indian (2,00,000) first, then western (1,000,000), then a plain number.
_AMOUNT = (
    r"(\d{1,2}(?:,\d{2})*,\d{3}(?:\.\d+)?|"
    r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|"
    r"\d+(?:\.\d+)?)"
)
_UNIT = r"(years?|yrs?|months?|mos?)"


def _f(s: str) -> float:
    return float(s.replace(",", ""))


def parse_money(text: str | None) -> int | None:
    """Parse the FIRST money expression found in text -> int INR, else None."""
    if not text:
        return None
    t = text.lower()

    m = re.search(_AMOUNT + r"\s*(?:crore|cr)\b", t)
    if m:
        return int(_f(m.group(1)) * CRORE)

    # bare '5L' shows up in both the unit tests and a few docs
    m = re.search(_AMOUNT + r"\s*(?:lakh|lac|l)\b", t)
    if m:
        return int(_f(m.group(1)) * LAKH)

    m = re.search(r"(?:₹|rs\.?|inr)\s*" + _AMOUNT, t)
    if m:
        return int(_f(m.group(1)))

    m = re.search(_AMOUNT + r"\s*(?:rupees?|rs\.?)\b", t)
    if m:
        return int(_f(m.group(1)))

    return None


def parse_tenure_months(text: str | None) -> tuple[int | None, int | None]:
    """Parse a tenure expression -> (min_months, max_months); (None, None) if absent."""
    if not text:
        return None, None
    t = text.lower().strip()
    t = re.sub(r"\bto\b", "-", t)
    t = re.sub(rf"\b({_UNIT})\s+\1\b", r"\1", t)  # corpus repeats 'months months'

    def to_months(n: float, u: str) -> int:
        return int(round(n * 12)) if u.startswith(("y", "yr")) else int(round(n))

    m = re.match(rf"{_AMOUNT}\s*{_UNIT}\s*-\s*{_AMOUNT}\s*{_UNIT}$", t)
    if m:
        a, b = to_months(_f(m.group(1)), m.group(2)), to_months(_f(m.group(3)), m.group(4))
        return min(a, b), max(a, b)
    m = re.match(rf"{_AMOUNT}\s*-\s*{_AMOUNT}\s*{_UNIT}$", t)
    if m:
        a, b = to_months(_f(m.group(1)), m.group(3)), to_months(_f(m.group(2)), m.group(3))
        return min(a, b), max(a, b)
    m = re.match(rf"{_AMOUNT}\s*{_UNIT}$", t)
    if m:
        v = to_months(_f(m.group(1)), m.group(2))
        return v, v
    return None, None
