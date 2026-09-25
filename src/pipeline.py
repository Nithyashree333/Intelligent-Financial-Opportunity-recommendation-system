"""Shared online pipeline used by both `--query` and `--eval`.

Retrieval is identical for every mode so the rules-vs-RAG comparison is fair;
only the ranker/explainer pair swaps at the seams.
"""
from __future__ import annotations

from .query_parser.parse import parse_query
from .retriever.bm25 import BM25Index
from .retriever.dense import DenseIndex
from .retriever.fusion import rrf_fuse
from .ranker.rules import RulesRanker
from .explainer.template import TemplateExplainer
from .schemas import Recommendation
from .storage.db import OpportunityDB


def _retrieve(cfg: dict, intent) -> tuple[list, dict[str, float]]:
    k = cfg["retrieval"]["top_k"]
    qtext = intent.text or intent.raw
    rankings = []
    bm25_hits = BM25Index(cfg).search(qtext, k)
    if bm25_hits:
        rankings.append(bm25_hits)
    if cfg["retrieval"]["hybrid"]:
        dense_hits = DenseIndex(cfg).search(qtext, k)
        if dense_hits:
            rankings.append(dense_hits)
    if not rankings:
        return [], {}
    fused = rrf_fuse(rankings, k=cfg["retrieval"]["fusion_k"])
    peak = max(fused.values()) or 1.0
    return OpportunityDB(cfg).get_many(list(fused)), {i: v / peak for i, v in fused.items()}


def run_query(cfg: dict, query: str, mode: str = "rules") -> Recommendation:
    intent = parse_query(query, cfg["query"]["tenure_tolerance_months"])
    candidates, text_scores = _retrieve(cfg, intent)
    if mode == "rag":
        from .ranker.rag import RagRanker
        from .explainer.rag import RagExplainer
        ranker = RagRanker(cfg)
        explainer = RagExplainer(cfg)
    else:
        ranker = RulesRanker(cfg)
        explainer = TemplateExplainer(cfg)
    ranked, abstain = ranker.rank(intent, candidates, text_scores)
    message = ranker.abstain_message(intent, candidates) if abstain else ""
    return explainer.explain(intent, ranked, abstain, message)

