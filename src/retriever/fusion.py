"""Reciprocal Rank Fusion: merge ranked lists on ranks, not raw scores
(BM25 and cosine live on different scales and cannot be mixed directly)."""
from __future__ import annotations


def rrf_fuse(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores
