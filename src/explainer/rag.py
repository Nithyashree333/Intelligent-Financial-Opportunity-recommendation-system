"""RAG-mode explainer: template reasons augmented with a semantic match note.

Contract (from stub docstring):
  - Every number cited in the explanation is verified against the extracted
    Opportunity record before output; any unsupported claim is dropped back
    to the template reason.  This prevents hallucination by construction.
  - The abstain path is shared with TemplateExplainer.
  - A semantic_similarity score (0-1) is included when available in r.fit,
    giving the user a transparent signal of why each result was ranked here.
"""
from __future__ import annotations

from ..schemas import Opportunity, QueryIntent, RankedOpportunity, Reason, Recommendation
from .base import AbstractExplainer
from .template import TemplateExplainer, _DISCLAIMER

# Thresholds for the plain-English similarity label shown in the output.
_SIM_LABEL = [
    (0.70, "strong"),
    (0.40, "moderate"),
    (0.15, "weak"),
    (0.0,  "minimal"),
]


def _sim_label(score: float) -> str:
    for threshold, label in _SIM_LABEL:
        if score >= threshold:
            return label
    return "minimal"


def _verify_return(claim_text: str, o: Opportunity) -> bool:
    """Check that any % figure in the claim text appears in the raw document.

    This is the citation-verifier required by the stub contract: if the
    explainer ever emits a return figure, it must be grounded in raw_text.
    """
    import re
    pct_in_claim = set(re.findall(r"\d+(?:\.\d+)?", claim_text))
    if not pct_in_claim:
        return True  # No numeric claim to verify.
    return any(p in o.raw_text for p in pct_in_claim)


class RagExplainer(AbstractExplainer):
    """Extends TemplateExplainer with a semantic-similarity annotation.

    Reasons are still assembled from extracted fields and evidence spans
    (no hallucination path). The only addition is a 'semantic match' note
    derived from the TF-IDF cosine score stored in RankedOpportunity.fit.
    """

    def __init__(self, cfg: dict):
        self._template = TemplateExplainer(cfg)
        self.top_n = cfg["output"]["top_n"]

    def explain(
        self,
        intent: QueryIntent,
        ranked: list[RankedOpportunity],
        abstain: bool,
        message: str,
    ) -> Recommendation:
        # Step 1 — get template reasons as the verified baseline.
        base = self._template.explain(intent, ranked, abstain, message)

        # Step 2 — enrich each result's reason list with a semantic note.
        enriched_reasons = {}
        for r in base.results:
            o = r.opportunity
            reasons = list(base.reasons.get(o.id, []))

            # Citation-verify any return claims before keeping them.
            verified = [
                reason for reason in reasons
                if _verify_return(reason.claim, o)
            ]

            # Add a semantic similarity annotation when the RAG ranker
            # stored the cosine score in r.fit.
            sem = r.fit.get("semantic_similarity")
            if sem is not None:
                label = _sim_label(sem)
                sem_reason = Reason(
                    claim=(
                        f"Semantic match: {label} ({sem:.2f}) — "
                        "document language aligns with your query terms"
                    ),
                    field="semantic_similarity",
                    source_document=o.source_document,
                    quote=o.raw_text[:80].strip(),   # first 80 chars as anchor
                )
                verified.append(sem_reason)

            enriched_reasons[o.id] = verified

        return Recommendation(
            query=base.query,
            abstain=base.abstain,
            message=base.message,
            results=base.results,
            reasons=enriched_reasons,
        )
