from src.ranker.rules import RulesRanker
from src.schemas import Opportunity, QueryIntent

CFG = {"ranking": {"weights": {"text_relevance": 0.25, "budget_fit": 0.25,
                               "risk_fit": 0.2, "tenure_fit": 0.2, "return_fit": 0.1},
                   "abstain_threshold": 0.25}}


def test_budget_violation_is_filtered_and_abstains():
    o = Opportunity(id="X1", min_investment_inr=5_000_000, risk="high",
                    source_document="d.txt")
    intent = QueryIntent(raw="q", budget_inr=200_000, risk="medium")
    ranked, abstain = RulesRanker(CFG).rank(intent, [o], {"X1": 0.9})
    assert ranked == [] and abstain is True


def test_infeasible_query_gets_explanation():
    o = Opportunity(id="X1", min_investment_inr=5_000_000, source_document="d.txt")
    intent = QueryIntent(raw="q", budget_inr=200_000)
    ranker = RulesRanker(CFG)
    _, abstain = ranker.rank(intent, [o], {})
    msg = ranker.abstain_message(intent, [o])
    assert abstain and "₹5,000,000" in msg and "200_000".replace("_", ",") in msg
