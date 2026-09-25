"""Human-readable rendering of recommendations and evaluation tables."""


def print_recommendation(rec, top_n: int = 5) -> None:
    if rec.abstain:
        print(f"ABSTAINED: {rec.message}")
        return
    print(f"Query: {rec.query}\n{'-' * 72}")
    for i, r in enumerate(rec.results[:top_n], 1):
        o = r.opportunity
        print(f"{i}. [{o.id}] {o.name or '(unnamed)'} - {o.provider or 'provider unknown'}"
              f" | score {r.score:.3f} | source: {o.source_document}")
        print(f"   matched: {', '.join(r.matched_attributes) or 'none'}")
        for reason in rec.reasons.get(o.id, []):
            print(
                f"   - {reason.claim}\n"
                f'     evidence: "{reason.quote}" ({reason.source_document})'
            )
        print()


def print_eval_report(rows, overall) -> None:
    print(f"{'Query':<55} {'Hit@5':>5}  {'Abstain':>7}")
    print("-" * 72)
    for r in rows:
        q = (r["query"][:52] + "...") if len(r["query"]) > 55 else r["query"]
        print(f"{q:<55} {int(r['hit@5']):>5}  {str(r['abstained']):>7}")
    print("-" * 72)
    print(f"{'OVERALL Hit@5':<55} {overall['hit@5']:>5.2f}")
