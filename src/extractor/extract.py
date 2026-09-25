"""Rule-based field extraction from opportunity documents.

Patterns cover the labelled-line style used in unit tests and the phrasing
in data/opportunities/*.txt (entry ticket, holding period, 'risk Moderate').
Missing values stay None — never guessed.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..schemas import Evidence, Opportunity, Risk
from .normalize import parse_money, parse_tenure_months
from .validate import classify_return_type

# first match wins; compound labels before the shorter ones they contain
RISK_PATTERNS: list[tuple[Risk, str]] = [
    ("medium", r"low\s+to\s+moderate"),
    ("high", r"moderately\s+high|moderate[- ]high"),
    ("low", r"\blow(?:[- ]risk)?\b|conservative|capital[- ]protected|risk[- ]averse"),
    ("medium", r"\b(medium|moderate|balanced)\b"),
    ("high", r"\b(high|aggressive|growth[- ]oriented)\b"),
]
RETURN_CONTEXT = re.compile(r"return|coupon|yield|interest|market[- ]linked", re.I)
_PCT_RANGE = re.compile(
    r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(?:%|percent|p\.a\.|per annum)", re.I
)
_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent|p\.a\.|per annum)", re.I)

_LABELED_ID = re.compile(
    r"^(?:opportunity\s+)?id\s*[:#]\s*([A-Za-z0-9][A-Za-z0-9\-]{1,20})\b",
    re.I | re.M,
)
_DOC_ID = re.compile(r"\b(OPP\d{3,})\b", re.I)
_PROVIDER = r"(?:Provider|Offered by|Issued by)\s*:\s*([^\n]+)"
_NAME_LABELED = re.compile(
    r"^(?:Opportunity|Product|Scheme|Name)\s*:\s*(.+)$", re.I | re.M
)
_CATEGORY = r"(?:Category|Type)\s*:\s*([^\n]+)"
_MIN_INV = re.compile(
    r"(?:minimum investment(?:\s+is)?|entry ticket|ticket size starts at|"
    r"investors may participate from)\s*:?\s*"
    r"((?:₹|rs\.?|inr)?\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakh|lac|l|crore|cr))?)",
    re.I,
)
_TENURE = re.compile(
    r"(?:tenure|term|duration|lock[- ]?in|(?:intended\s+)?holding period|"
    r"maturity(?:/holding period)?|suggested duration(?:\s+is)?)\s*:?\s*"
    r"(\d+(?:\.\d+)?\s*(?:years?|yrs?|months?|mos?)?"
    r"(?:\s*(?:to|-|–)\s*\d+(?:\.\d+)?\s*(?:years?|yrs?|months?|mos?))?"
    r"(?:\s*months?)?)",
    re.I,
)


def _ev_at(text: str, start: int, quote: str) -> Evidence:
    return Evidence(quote=quote.strip(), line=text[:start].count("\n") + 1)


def _field(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.I)
    return m.group(1).strip() if m else None


def _opportunity_id(text: str, fallback_id: str) -> tuple[str, Evidence | None]:
    m = _LABELED_ID.search(text)
    if m:
        return m.group(1), _ev_at(text, m.start(1), m.group(1))
    m = _DOC_ID.search(text)
    if m:
        return m.group(1).upper(), _ev_at(text, m.start(1), m.group(1))
    return fallback_id, None


def _name(text: str, fallback_id: str) -> tuple[str | None, Evidence | None]:
    m = _NAME_LABELED.search(text)
    if m:
        return m.group(1).strip(), _ev_at(text, m.start(1), m.group(1))
    lines = [(i, ln.strip()) for i, ln in enumerate(text.splitlines(), 1) if ln.strip()]
    if len(lines) >= 2 and lines[0][1].upper() in {fallback_id.upper(), fallback_id.upper().replace(".TXT", "")}:
        _, quote = lines[1]
        return quote, Evidence(quote=quote, line=lines[1][0])
    if len(lines) >= 2 and _DOC_ID.fullmatch(lines[0][1]):
        _, quote = lines[1]
        return quote, Evidence(quote=quote, line=lines[1][0])
    return None, None


def _return_percents(line: str) -> list[float]:
    found: list[float] = []
    used: list[tuple[int, int]] = []
    for m in _PCT_RANGE.finditer(line):
        found.extend([float(m.group(1)), float(m.group(2))])
        used.append(m.span())
    for m in _PCT.finditer(line):
        if any(s <= m.start() and m.end() <= e for s, e in used):
            continue
        found.append(float(m.group(1)))
    return found


def extract_document(text: str, source_document: str, fallback_id: str) -> Opportunity:
    evidence: dict[str, Evidence] = {}

    oid, id_ev = _opportunity_id(text, fallback_id)
    if id_ev:
        evidence["id"] = id_ev

    name, name_ev = _name(text, fallback_id)
    if name_ev:
        evidence["name"] = name_ev

    min_inv = None
    m = _MIN_INV.search(text)
    if m:
        min_inv = parse_money(m.group(1)) or parse_money(m.group(0))
        if min_inv is not None:
            evidence["min_investment_inr"] = _ev_at(text, m.start(1), m.group(1))

    tmin = tmax = None
    m = _TENURE.search(text)
    if m:
        tmin, tmax = parse_tenure_months(m.group(1))
        if tmin is not None:
            evidence["tenure"] = _ev_at(text, m.start(1), m.group(1))

    risk = None
    for level, pat in RISK_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            risk = level
            evidence["risk"] = _ev_at(text, m.start(), m.group(0))
            break

    percents: list[float] = []
    ret_line = None
    ret_line_no = None
    for i, line in enumerate(text.splitlines(), 1):
        if not RETURN_CONTEXT.search(line):
            continue
        got = _return_percents(line)
        if got and ret_line is None:
            ret_line, ret_line_no = line.strip(), i
        percents.extend(got)
        if ret_line is None and re.search(r"variable|market[- ]linked", line, re.I):
            ret_line, ret_line_no = line.strip(), i
    ret_min = min(percents) if percents else None
    ret_max = max(percents) if percents else None
    if ret_line:
        evidence["expected_return"] = Evidence(quote=ret_line, line=ret_line_no or 1)

    return Opportunity(
        id=oid, name=name, provider=_field(text, _PROVIDER),
        category=_field(text, _CATEGORY), min_investment_inr=min_inv,
        tenure_min_months=tmin, tenure_max_months=tmax, risk=risk,
        expected_return_min=ret_min, expected_return_max=ret_max,
        return_type=classify_return_type(text), source_document=source_document,
        raw_text=text, evidence=evidence,
    )


def extract_all(opportunities_dir: Path, db) -> int:
    docs = sorted(Path(opportunities_dir).glob("*.txt"))
    if not docs:
        raise SystemExit(f"No .txt documents found in {opportunities_dir}")
    db.clear()
    for path in docs:
        db.upsert(extract_document(path.read_text(encoding="utf-8", errors="replace"),
                                   path.name, path.stem))
    return len(docs)
