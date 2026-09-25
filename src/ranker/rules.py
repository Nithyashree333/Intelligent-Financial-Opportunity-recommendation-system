"""Constraint-first weighted ranking (default mode).

Pipeline: HARD budget filter -> soft fits (risk/tenure/return/text) with
re-normalized weights -> abstain if empty or below threshold.
Guarantee-language is never generated; fits are explainable numbers.
"""
from __future__ import annotations

from ..schemas import Opportunity, QueryIntent, RankedOpportunity
from .base import AbstractRanker

_NEIGHBOURS = {("low", "medium"), ("medium", "high")}


class RulesRanker(AbstractRanker):
    def __init__(self, cfg: dict):
        self.weights: dict[str, float] = cfg["ranking"]["weights"]
        self.threshold: float = cfg["ranking"]["abstain_threshold"]

    # --- hard constraint -------------------------------------------------
    @staticmethod
    def _budget_ok(intent: QueryIntent, o: Opportunity) -> bool:
        return not (intent.budget_inr and o.min_investment_inr) or             intent.budget_inr >= o.min_investment_inr

    # --- soft fits (0..1, each explainable) ------------------------------
    @staticmethod
    def _risk_fit(intent: QueryIntent, o: Opportunity) -> float:
        if not (intent.risk and o.risk):
            return 0.0
        if intent.risk == o.risk:
            return 1.0
        return 0.5 if (intent.risk, o.risk) in _NEIGHBOURS else 0.0

    def _tenure_fit(self, intent: QueryIntent, o: Opportunity) -> float:
        if not (intent.tenure_months and o.tenure_min_months and o.tenure_max_months):
            return 0.0
        lo = intent.tenure_months - intent.tenure_tolerance_months
        hi = intent.tenure_months + intent.tenure_tolerance_months
        overlap = max(0, min(hi, o.tenure_max_months) - max(lo, o.tenure_min_months))
        return min(1.0, overlap / (2 * intent.tenure_tolerance_months))

    @staticmethod
    def _return_fit(o: Opportunity) -> float:
        # 0..1 over a 0-20% scale; indicative/historical treated identically,
        # the DISCLAIMER lives in the explainer, not in the score.
        if o.expected_return_min is None:
            return 0.0
        return min(1.0, o.expected_return_min / 20.0)

    # --- main -------------------------------------------------------------
    def rank(self, intent, candidates, text_scores=None):
        text_scores = text_scores or {}
        feasible = [c for c in candidates if self._budget_ok(intent, c)]
        ranked: list[RankedOpportunity] = []
        for c in feasible:
            fits = {
                "text_relevance": text_scores.get(c.id, 0.0),
                "budget_fit": 1.0 if (intent.budget_inr and c.min_investment_inr) else 0.0,
                "risk_fit": self._risk_fit(intent, c),
                "tenure_fit": self._tenure_fit(intent, c),
                "return_fit": self._return_fit(c),
            }
            w = {k: v for k, v in self.weights.items() if k != "text_relevance"
                 or text_scores.get(c.id) is not None}
            total_w = sum(w.values())
            score = sum(w[k] * fits[k] for k in w) / total_w if total_w else 0.0
            matched = [k for k, v in fits.items() if v > 0]
            ranked.append(RankedOpportunity(opportunity=c, score=round(score, 4),
                                            matched_attributes=matched, fit=fits))
        ranked.sort(key=lambda r: r.score, reverse=True)
        abstain = (not ranked) or (ranked[0].score < self.threshold)
        return ranked, abstain

    def abstain_message(self, intent: QueryIntent, candidates: list) -> str:
        if not candidates:
            return "No opportunity in the corpus matched the query terms."
        why = []
        if intent.budget_inr:
            mins = [c.min_investment_inr for c in candidates if c.min_investment_inr]
            if mins and intent.budget_inr < min(mins):
                why.append(f"minimum investments start at ₹{min(mins):,}, "
                           f"above your ₹{intent.budget_inr:,} budget")
        return ("No supported recommendation: " + "; ".join(why) +
                ". Refusing rather than recommending an unfit product.") if why else \
               ("No opportunity scored above the confidence threshold "
                f"({self.threshold}); declining to recommend.")
