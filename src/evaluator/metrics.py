"""Ranking quality metric: Hit@5."""


def hit_rate_at_k(recommended: list[str], relevant: set[str], k: int = 5) -> bool:
    """Return True if at least one relevant ID appears in the top-k results."""
    return any(r in relevant for r in recommended[:k])
