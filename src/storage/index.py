"""Offline index builder: BM25 store + optional dense vectors."""
from __future__ import annotations

import json
import re

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def build_index(cfg: dict, db) -> None:
    opps = db.all()
    payload = {"ids": [o.id for o in opps],
               "texts": [o.raw_text for o in opps]}
    with open(cfg["paths"]["index"], "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    if cfg["retrieval"]["hybrid"]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("sentence-transformers not installed - dense index skipped (BM25 only).")
            return
        model = SentenceTransformer(cfg["retrieval"]["dense_model"])
        import numpy as np
        vecs = model.encode(payload["texts"], normalize_embeddings=True)
        np.save(cfg["paths"]["vectors"], vecs)
        print(f"Dense vectors built for {len(opps)} documents.")
