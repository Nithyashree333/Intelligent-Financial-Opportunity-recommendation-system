"""Dense retrieval: embedding cosine similarity (paraphrases, intent language).

Requires: pip install sentence-transformers && python main.py --index
"""
from __future__ import annotations

import json

import numpy as np


class DenseIndex:
    def __init__(self, cfg: dict):
        from sentence_transformers import SentenceTransformer
        with open(cfg["paths"]["index"], encoding="utf-8") as fh:
            payload = json.load(fh)
        self.ids = payload["ids"]
        self.model = SentenceTransformer(cfg["retrieval"]["dense_model"])
        self.vecs = np.load(cfg["paths"]["vectors"])


    def search(self, query_text: str, k: int) -> list[str]:
        q = self.model.encode([query_text], normalize_embeddings=True)[0]
        sims = self.vecs @ q
        order = np.argsort(-sims)[:k]
        return [self.ids[i] for i in order if sims[i] > 0]
