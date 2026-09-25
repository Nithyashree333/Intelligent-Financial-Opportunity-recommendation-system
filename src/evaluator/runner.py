"""Run labelled queries through the pipeline and compute metrics."""
from __future__ import annotations

import csv

from ..pipeline import run_query
from .metrics import hit_rate_at_k


def run_evaluation(cfg: dict, mode: str = "rules", k: int = 5):
    rows = []
    with open(cfg["paths"]["labelled"], newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            query = row["query"]
            relevant = {x.strip() for x in row["relevant_ids"].split(";") if x.strip()}
            rec = run_query(cfg, query, mode=mode)
            recs = [r.opportunity.id for r in rec.results]
            rows.append({
                "query": query,
                "relevant": relevant,
                "recommended": recs,
                "abstained": rec.abstain,
                "hit@5": hit_rate_at_k(recs, relevant, k),
                "reasons": {oid: [r.claim for r in rs] for oid, rs in rec.reasons.items()},
            })
    n = len(rows) or 1
    overall = {
        "hit@5": sum(r["hit@5"] for r in rows) / n,
    }
    return rows, overall
