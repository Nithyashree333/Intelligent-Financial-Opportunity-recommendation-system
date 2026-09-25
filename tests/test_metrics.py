from src.evaluator.metrics import precision_at_k, recall_at_k, hit_rate_at_k


def test_perfect_and_partial():
    rel = {"A", "B", "C"}
    assert precision_at_k(["A", "B", "X", "Y", "Z"], rel) == 0.4
    assert recall_at_k(["A", "B", "X", "Y", "Z"], rel) == 2 / 3
    assert hit_rate_at_k(["A", "B", "X", "Y", "Z"], rel) is True
    assert hit_rate_at_k(["X", "Y", "Z", "P", "Q"], rel) is False


def test_empty_inputs():
    assert precision_at_k([], {"A"}) == 0.0
    assert recall_at_k(["A"], set()) == 0.0
