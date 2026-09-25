"""Template-based grounded explanations.

Reasons are assembled ONLY from validated extracted fields and their stored
evidence spans - this class cannot hallucinate by construction.
Indicative/historical/illustrative returns always carry a disclaimer.
"""
from __future__ import annotations

from ..schemas import Opportunity, QueryIntent, RankedOpportunity, Reason, Recommendation
from .base import AbstractExplainer

_DISCLAIMER = {
    "indicative": " (indicative, not guaranteed)",
    "historical": " (historical; past performance is not a guarantee)",
    "illustrative": " (illustrative only)",
    "variable": " (variable; depends on market conditions)",
}


class TemplateExplainer(AbstractExplainer):
    def __init__(self, cfg: dict):
        self.top_n = cfg["output"]["top_n"]

    @staticmethod
    def _ev(o: Opportunity, field: str) -> Reason | None:
        if field not in o.evidence:
            return None
        e = o.evidence[field]
        return Reason(claim="", field=field, source_document=o.source_document, quote=e.quote)

    def explain(self, intent, ranked, abstain, message):
        reasons: dict[str, list[Reason]] = {}
        results = ranked[: self.top_n]
        for r in results:
            o, rs = r.opportunity, []
            if (e := self._ev(o, "min_investment_inr")) and intent.budget_inr:
                e.claim = (f"Fits your budget: minimum ₹{o.min_investment_inr:,} "
                           f"≤ your ₹{intent.budget_inr:,}")
                rs.append(e)
            if (e := self._ev(o, "tenure")) and intent.tenure_months:
                e.claim = (f"Tenure {o.tenure_min_months}–{o.tenure_max_months} months "
                           f"matches your ~{intent.tenure_months}-month horizon")
                rs.append(e)
            if (e := self._ev(o, "risk")) and intent.risk:
                e.claim = f"Risk level '{o.risk}' vs your preference '{intent.risk}'"
                rs.append(e)
            if (e := self._ev(o, "expected_return")) and o.expected_return_min is not None:
                d = _DISCLAIMER.get(o.return_type or "unknown", "")
                e.claim = (f"Stated return {o.expected_return_min}–{o.expected_return_max}%"
                           f"{d}")
                rs.append(e)
            reasons[o.id] = rs
        return Recommendation(query=intent.raw, abstain=abstain, message=message,
                              results=results, reasons=reasons)
