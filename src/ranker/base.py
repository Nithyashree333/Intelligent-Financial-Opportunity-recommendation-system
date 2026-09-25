"""The seam: every ranker (rules today, RAG tomorrow) implements this contract."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import QueryIntent, RankedOpportunity


class AbstractRanker(ABC):
    @abstractmethod
    def rank(self, intent: QueryIntent, candidates: list,
             text_scores: dict[str, float] | None = None
             ) -> tuple[list[RankedOpportunity], bool]:
        """Return (ranked list, abstain). abstain MUST be True when nothing is
        supportable - never force a recommendation."""
        ...
