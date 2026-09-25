"""The seam: every explainer implements this contract."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import QueryIntent, RankedOpportunity, Recommendation


class AbstractExplainer(ABC):
    @abstractmethod
    def explain(self, intent: QueryIntent, ranked: list[RankedOpportunity],
                abstain: bool, message: str) -> Recommendation:
        """Every Reason MUST carry claim + field + source doc + quoted span."""
        ...
