from src.extractor.extract import extract_document

DOC = """Opportunity: Sunrise Balanced Fund
Provider: Sunrise Capital Ltd.
Category: Debt Hybrid
Minimum investment: ₹1.5 lakh
Tenure: 24 to 36 months
Medium risk fund with an indicative return of 8% p.a.
"""

DOC_MINIMAL = """GreenHarvest Agri-Bond
High risk. Historical returns of 14% p.a. observed in backtests.
"""


def test_full_extraction_with_evidence():
    o = extract_document(DOC, "doc01.txt", "doc01")
    assert o.id == "doc01"
    assert o.provider == "Sunrise Capital Ltd."
    assert o.min_investment_inr == 150_000
    assert (o.tenure_min_months, o.tenure_max_months) == (24, 36)
    assert o.risk == "medium"
    assert o.return_type == "indicative"
    assert o.expected_return_min == 8.0
    assert "min_investment_inr" in o.evidence
    assert o.evidence["min_investment_inr"].quote != ""


def test_missing_fields_stay_none():
    o = extract_document(DOC_MINIMAL, "doc02.txt", "doc02")
    assert o.min_investment_inr is None      # never guessed
    assert o.tenure_min_months is None
    assert o.provider is None
    assert o.risk == "high"
    assert o.return_type == "historical"     # not confused with a promise
