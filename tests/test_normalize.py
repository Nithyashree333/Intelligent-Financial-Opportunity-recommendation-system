from src.extractor.normalize import parse_money, parse_tenure_months


def test_money_lakh_crore_inr():
    assert parse_money("₹5 lakh") == 500_000
    assert parse_money("Rs. 1.5 crore") == 15_000_000
    assert parse_money("INR 2,00,000") == 200_000
    assert parse_money("minimum investment of 5L") == 500_000


def test_money_missing_is_none():
    assert parse_money("no money here") is None
    assert parse_money(None) is None


def test_tenure_units_and_ranges():
    assert parse_tenure_months("2 years") == (24, 24)
    assert parse_tenure_months("24 months") == (24, 24)
    assert parse_tenure_months("18-36 months") == (18, 36)
    assert parse_tenure_months("1.5 years") == (18, 18)
    assert parse_tenure_months("3 to 5 years") == (36, 60)
    assert parse_tenure_months("unclear") == (None, None)
