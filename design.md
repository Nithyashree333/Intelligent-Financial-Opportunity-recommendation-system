# System Design — Intelligent Financial Opportunity Analysis & Recommendation Engine

1. Overview
Converts unstructured opportunity documents into structured records, matches natural-language
requirements against them, and returns ranked, evidence-backed recommendations with explicit
abstention when no match is supported.

2. Design Principles
- Groundedness over fluency: every claim traces to a source document span.
- Determinism where money is involved: constraints and abstention are rule-based, never model-based.
- Variant seam: rules engine and RAG engine share one pipeline behind two interfaces for fair A/B evaluation.
- Reproducibility: runs fully offline; zero required API keys; pinned dependencies.

3. Architecture

```
Documents ──▶ Extractor ──▶ Normalizer ──▶ Validator ──▶ Storage (SQLite + Vector Index)
                                                            │
NL Query ──▶ Query Parser ──▶ Retriever (BM25 + Dense + RRF)│
                                    │                       │
                                    ▼                       ▼
                              Ranker [rules | rag] ◀── Candidates
                                    │
                                    ▼
                              Explainer [template | rag] ──▶ Recommendation (with evidence)
                                    │
                                    ▼
                              Evaluator ──▶ P@5 / R@5 / Hit@5 + comparison report
```

## 4. Module Map (what sits where)

| Path | Role |
|---|---|
| `main.py` | CLI entry: `--query`, `--eval`, `--mode rules\|rag`; routes to pipeline |
| `config.yaml` | All thresholds, ranking weights, fusion params, model names — no magic numbers in code |
| `src/schemas.py` | Pydantic models: Opportunity, QueryIntent, RankedOpportunity, Recommendation — single source of truth |
| `src/extractor/extract.py` | Rule/regex extraction of schema fields from raw text; missing stays None |
| `src/extractor/llm_backend.py` | Optional LLM extraction adapter behind same contract; system runs without it |
| `src/extractor/normalize.py` | ₹/Rs/lakh/crore → INR ints; years/months/ranges → tenure_min/tenure_max |
| `src/extractor/validate.py` | Pydantic validation; return-type classification (indicative/historical/coupon/variable) |
| `src/storage/db.py` | SQLite persistence of validated records; rebuildable from documents |
| `src/storage/index.py` | Offline build of BM25 index + embedding store (one command) |
| `src/query_parser/parse.py` | NL query → QueryIntent: budget, risk, tenure ± tolerance, free-text |
| `src/retriever/bm25.py` | Sparse retrieval — exact values, product names, numbers |
| `src/retriever/dense.py` | Embedding cosine — paraphrases, intent language |
| `src/retriever/fusion.py` | RRF fusion of both rankings → top-k candidates |
| `src/ranker/base.py` | AbstractRanker interface — the seam |
| `src/ranker/rules.py` | Hard-constraint filter → weighted score → abstain flag; weights justified in config |
| `src/ranker/rag.py` | [VARIANT STUB] LLM reranking behind the same interface |
| `src/explainer/base.py` | AbstractExplainer interface — the seam |
| `src/explainer/template.py` | Reasons built from extracted fields + source spans; guarantee-language blocked |
| `src/explainer/rag.py` | [VARIANT STUB] LLM draft + citation verifier behind same interface |
| `src/evaluator/metrics.py` | Precision@5, Recall@5, HitRate@5 |
| `src/evaluator/runner.py` | Runs labelled queries through both modes on identical retrieval |
| `src/evaluator/report.py` | Per-query tables, overall scores, failure analysis, side-by-side comparison |
| `tests/` | Unit tests: normalization, extraction fidelity, abstention, metrics correctness |
| `docs/TECHNICAL_NOTE.md` | Architecture, assumptions, failure modes, 10M-doc scaling, production safeguards |

5. Data Flow
- Offline (once): documents → extraction → normalization → validation → SQLite → indexes.
- Online (per query): parse → hybrid retrieve → rank → explain → (eval mode) score against labels.

6. Key Interfaces
- `AbstractRanker.rank(intent, candidates) -&gt; list[RankedOpportunity]` — must set abstain when unsupported.
- `AbstractExplainer.explain(intent, ranked) -&gt; Recommendation` — every reason carries claim + field + source doc + span.

7. Scoring (rules mode)
score = w₁·text_relevance + w₂·budget_fit + w₃·risk_fit + w₄·tenure_fit + w₅·return_fit;
hard constraints filter first; abstain if no survivors or score &lt; threshold. Weights live in config.yaml.

8. Evaluation
Labelled queries → both modes → P@5/R@5/Hit@5 per query + overall + one failure analysis;
RAG mode additionally audited for groundedness (claims vs. extracted records).

9. Safeguards
No invented providers/returns; indicative/historical never rendered as guarantees;
missing evidence → explicit statement; no-match → explicit refusal with reason.

 10. Scaling Path (10M docs)
Sharded inverted index (OpenSearch) + ANN vector index (FAISS/HNSW);
batched distributed extraction; two-stage ranking (retrieve 100 → cross-encoder rerank 5).