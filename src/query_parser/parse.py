"""Parse a natural-language requirement into a QueryIntent."""
from __future__ import annotations

import re

from ..extractor.normalize import parse_money, parse_tenure_months
from ..schemas import QueryIntent

_RISK = {
    "low": r"\b(low|conservative|safe|capital[- ]protected)\b[^.]{0,20}risk\b|\brisk[- ]averse\b",
    "medium": r"\b(medium|moderate|balanced|medium[- ]risk)\b",
    "high": r"\b(high|aggressive)\b[^.]{0,20}risk\b",
}
_TENURE_SPAN = re.compile(
    r"\d+(?:\.\d+)?\s*(?:years?|yrs?|months?|mos?)"
    r"(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?\s*(?:years?|yrs?|months?|mos?))?")


_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def _words_to_digits(q: str) -> str:
    for w, n in sorted(_WORD_NUM.items(), key=lambda x: -len(x[0])):
        q = re.sub(rf"\b{w}\b", str(n), q)
    return q


def parse_query(query: str, tenure_tolerance_months: int = 3) -> QueryIntent:
    q = _words_to_digits(query.lower())
    budget = parse_money(q)

    risk = None
    for level, pat in _RISK.items():
        if re.search(pat, q):
            risk = level  # type: ignore[assignment]
            break

    tmin = tmax = None
    tspan = None
    if (m := _TENURE_SPAN.search(q)):
        tspan = m.group(0)
        tmin, tmax = parse_tenure_months(tspan)
    tenure = tmin if tmin is not None else None

    # Free text = query minus the spans we consumed as structured intent.
    text = q
    if budget:
        text = re.sub(r"(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|lac|l|crore|cr))?\b", " ", text)
        text = re.sub(r"\d+(?:\.\d+)?\s*(?:lakh|lac|l|crore|cr)\b", " ", text)
    if tspan:
        text = text.replace(tspan, " ")
    if risk:
        text = re.sub(_RISK[risk], " ", text)

    return QueryIntent(raw=query, text=" ".join(text.split()), budget_inr=budget,
                       risk=risk, tenure_months=tenure,
                       tenure_tolerance_months=tenure_tolerance_months)
