"""Pydantic models - the single source of truth for all data structures."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Risk = Literal["low", "medium", "high"]
ReturnType = Literal["indicative", "historical", "illustrative",
                     "coupon", "variable", "unknown"]


class Evidence(BaseModel):
    """A quoted source span backing one extracted field."""
    quote: str
    line: int


class Opportunity(BaseModel):
    id: str
    name: Optional[str] = None
    provider: Optional[str] = None
    category: Optional[str] = None
    min_investment_inr: Optional[int] = None
    tenure_min_months: Optional[int] = None
    tenure_max_months: Optional[int] = None
    risk: Optional[Risk] = None
    expected_return_min: Optional[float] = None
    expected_return_max: Optional[float] = None
    return_type: Optional[ReturnType] = None
    source_document: str
    raw_text: str = ""
    evidence: dict[str, Evidence] = Field(default_factory=dict)


class QueryIntent(BaseModel):
    raw: str
    text: str = ""                       # leftover free text for retrieval
    budget_inr: Optional[int] = None
    risk: Optional[Risk] = None
    tenure_months: Optional[int] = None
    tenure_min_months: Optional[int] = None
    tenure_max_months: Optional[int] = None
    tenure_tolerance_months: int = 3
    tenure_at_least: bool = False
    provider: Optional[str] = None
    min_return_pct: Optional[float] = None
    requires_guarantee: bool = False


class RankedOpportunity(BaseModel):
    opportunity: Opportunity
    score: float
    matched_attributes: list[str] = Field(default_factory=list)
    fit: dict[str, float] = Field(default_factory=dict)


class Reason(BaseModel):
    claim: str
    field: str
    source_document: str
    quote: str


class Recommendation(BaseModel):
    query: str
    abstain: bool = False
    message: str = ""
    results: list[RankedOpportunity] = Field(default_factory=list)
    reasons: dict[str, list[Reason]] = Field(default_factory=dict)
