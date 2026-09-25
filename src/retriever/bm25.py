"""Sparse retrieval: BM25 over raw document text (exact values, names, numbers)."""
from __future__ import annotations

import json

from ..storage.index import tokenize


class BM25Index:
    def __init__(self, cfg: dict):
        from rank_bm25 import BM25Okapi
        # Load the pre-built index; encoding must be explicit on Windows.
        with open(cfg["paths"]["index"], encoding="utf-8") as fh:
            payload = json.load(fh)
        self.ids = payload["ids"]
        self._bm25 = BM25Okapi([tokenize(t) for t in payload["texts"]])


    def search(self, query_text: str, k: int) -> list[str]:
        scores = self._bm25.get_scores(tokenize(query_text))
        order = sorted(range(len(self.ids)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.ids[i] for i in order if scores[i] > 0]
