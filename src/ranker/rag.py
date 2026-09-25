"""Hybrid TF-IDF reranker — the RAG-mode ranker.

Architecture (per TECHNICAL_NOTE.md contract):
  1. BM25 retrieves the candidate set  (done upstream in pipeline.py)
  2. THIS class re-scores candidates with TF-IDF cosine similarity
     between the raw query text and each opportunity's raw_text.
  3. The semantic score is blended with the rules-based soft fits
     so structured constraints (budget, risk, tenure) still matter.
  4. Abstain decision is delegated to RulesRanker — never overridden
     here, keeping the rules-vs-RAG comparison fair.

No external model or API is required; only numpy (already a transitive
dependency of rank-bm25).
"""
from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np

from ..schemas import Opportunity, QueryIntent, RankedOpportunity
from .base import AbstractRanker
from .rules import RulesRanker

# Simple tokeniser reused from index.py to keep vocabularies consistent.
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


# ---------------------------------------------------------------------------
# Minimal TF-IDF implementation (no sklearn dependency)
# ---------------------------------------------------------------------------

def _build_tfidf(docs: list[list[str]]) -> tuple[dict[str, int], np.ndarray]:
    """Return (vocab, idf_vector) for a corpus of tokenised documents."""
    vocab: dict[str, int] = {}
    for tokens in docs:
        for t in set(tokens):           # set → count each term once per doc
            if t not in vocab:
                vocab[t] = len(vocab)

    n = len(docs)
    # df[i] = number of documents containing term i
    df = np.zeros(len(vocab), dtype=np.float64)
    for tokens in docs:
        for t in set(tokens):
            df[vocab[t]] += 1.0

    # Smooth IDF: log((1+n)/(1+df)) + 1  (sklearn-compatible formula)
    idf = np.log((1.0 + n) / (1.0 + df)) + 1.0
    return vocab, idf


def _tf_vector(tokens: list[str], vocab: dict[str, int],
               idf: np.ndarray) -> np.ndarray:
    """Build a normalised TF-IDF vector for a single document."""
    counts = Counter(tokens)
    total = max(len(tokens), 1)
    vec = np.zeros(len(vocab), dtype=np.float64)
    for term, cnt in counts.items():
        if term in vocab:
            vec[vocab[term]] = (cnt / total) * idf[vocab[term]]
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product of two pre-normalised vectors = cosine similarity."""
    return float(np.dot(a, b))


class RagRanker(AbstractRanker):
    """TF-IDF cross-encoder reranker blended with rules-based soft fits.

    Config keys used (fall back to sensible defaults if absent):
      ranking.rag_semantic_weight  — weight given to TF-IDF score (default 0.4)
      ranking.weights              — rules soft-fit weights (same as RulesRanker)
      ranking.abstain_threshold    — same threshold as RulesRanker
    """

    def __init__(self, cfg: dict):
        self._rules = RulesRanker(cfg)
        # How much the TF-IDF semantic score contributes vs the rules score.
        self._sem_weight: float = (
            cfg.get("ranking", {}).get("rag_semantic_weight", 0.4)
        )

    # ------------------------------------------------------------------
    # Public interface (AbstractRanker contract)
    # ------------------------------------------------------------------

    def rank(
        self,
        intent: QueryIntent,
        candidates: list[Opportunity],
        text_scores: dict[str, float] | None = None,
    ) -> tuple[list[RankedOpportunity], bool]:
        """Re-rank candidates with TF-IDF cosine similarity + rules blend."""
        if not candidates:
            return [], True

        # Step 1 — get rule-based ranked list and abstain decision.
        rules_ranked, abstain = self._rules.rank(intent, candidates, text_scores)
        if not rules_ranked:
            return [], abstain

        # Step 2 — build TF-IDF corpus over candidate raw texts.
        corpus = [_tokenize(o.raw_text) for o in candidates]
        vocab, idf = _build_tfidf(corpus)

        # Step 3 — encode the query (use raw query for richer terms).
        query_vec = _tf_vector(_tokenize(intent.raw), vocab, idf)

        # Step 4 — compute cosine similarity for every candidate.
        doc_vecs = {
            o.id: _tf_vector(_tokenize(o.raw_text), vocab, idf)
            for o in candidates
        }
        sem_scores = {oid: _cosine_sim(query_vec, v) for oid, v in doc_vecs.items()}

        # Step 5 — blend: final = (1-w)*rules_score + w*semantic_score.
        w = self._sem_weight
        blended: list[RankedOpportunity] = []
        for r in rules_ranked:
            sem = sem_scores.get(r.opportunity.id, 0.0)
            final = round((1.0 - w) * r.score + w * sem, 4)
            blended.append(
                RankedOpportunity(
                    opportunity=r.opportunity,
                    score=final,
                    matched_attributes=r.matched_attributes,
                    fit={**r.fit, "semantic_similarity": round(sem, 4)},
                )
            )

        blended.sort(key=lambda r: r.score, reverse=True)
        # Abstain threshold is re-checked against the blended scores.
        abstain = (not blended) or (blended[0].score < self._rules.threshold)
        return blended, abstain

    def abstain_message(self, intent: QueryIntent, candidates: list) -> str:
        # Delegate — abstain reasoning is rule-based in both modes.
        return self._rules.abstain_message(intent, candidates)
