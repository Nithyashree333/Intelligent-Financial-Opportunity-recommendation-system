Technical Note
==============


Architecture and Data Flow
---------------------------

The pipeline has two phases: offline preparation and online query serving.

Offline (run once):
  Documents are parsed field-by-field into a SQLite database. Two indexes
  are built — a BM25 keyword index (good at exact values like "₹1 lakh")
  and an dense vector index (good at paraphrased intent).

Online (per query):
  1. Query is parsed into structured intent: budget, risk, tenure, free text.
  2. Both indexes are queried; results are merged with Reciprocal Rank Fusion.
  3. Ranker applies a hard budget filter, then scores remaining candidates on
     risk, tenure, and return fit.
  4. Explainer builds reasons from stored evidence spans — no inference.
  5. Top-N results print. If no candidate clears the confidence threshold,
     the system abstains instead of guessing.

  Two ranking modes are supported: the default `rules` mode strictly scores
  candidates using hard mathematical fits for financial constraints, ensuring
  absolute predictability and safety. Alternatively, the `rag` mode blends those
  strict financial scores with a TF-IDF semantic language score (cosine similarity)
  computed on the fly, offering fuzzier matching at the cost of additional compute.


Modelling Choices
------------------

Two-index hybrid retrieval: BM25 handles exact numbers and named entities;
dense vectors handle semantic paraphrases. Neither alone is sufficient.

Budget is a hard constraint, not a soft preference. An opportunity requiring
more than the user's budget is removed before scoring, not just downranked.

Risk and tenure are soft fits scored 0–1. Adjacent risk levels (e.g. low vs
medium) score 0.5, not 0. Tenure uses a ±3-month tolerance window.

Return type (indicative / historical / coupon / variable / illustrative) is
stored separately from the return figure and drives the disclaimer shown to
the user. A 9% indicative return and a 9% coupon are not the same thing.

Missing fields stay None. The system never guesses or fills in a default.

This hybrid architecture is the result of direct iteration on retrieval methods.
Initial versions relying purely on BM25 keyword search struggled with paraphrased
user intent (e.g., matching "around 18 months" to "1.5 years"), yielding an
overall Hit@5 of 0.75 (6 out of 8 queries). By mandating dense embeddings to
form a hybrid retrieval layer, the system successfully bridged these semantic
gaps, improving the Hit@5 score to a perfect 1.00 (8 out of 8) and justifying
the inclusion of the heavier machine learning dependency.


Failure Modes
--------------

Unusual document phrasing -> fields not extracted. Mitigated by expanding
regex patterns or plugging in an LLM extractor.

Tenure tolerance too tight -> boundary cases ranked low despite being a
reasonable match. Tolerance is a tunable config value.

Semantic index sometimes surfaces constraint-violating documents (wrong budget
or risk) because it only sees meaning, not numbers. The hard budget filter
downstream corrects this before results are shown.

No suitable match exists -> without an abstain path, any system returns
something. This system refuses if no candidate clears the threshold.


Scaling to 10 Million Documents
---------------------------------

SQLite -> PostgreSQL. In-memory BM25 -> OpenSearch (sharded inverted index).
Dense vector search -> FAISS/HNSW approximate nearest-neighbour index.
Extraction becomes a parallelised batch job; only new or changed documents
need reprocessing. Ranking becomes two-stage: retrieve 100 candidates fast,
rerank top 5 with a cross-encoder for precision.


Evaluation with More Labelled Data
------------------------------------

Current: 8 labelled queries, Hit@5 only. Enough to catch obvious failures.

With ~50 queries: split into tune/test sets; grid-search the config weights
(risk_fit, tenure_fit, etc.) on the tune set; report unbiased Hit@5 on test.

With ~100+ queries: we need to add nDCG@5 (rewards showing the best match first, not
just any match). Stratify failures by attribute to see where the system
specifically loses. Replace hand-set weights with learned weights
(LambdaRank or similar).


Safeguards Before Production
------------------------------

1. Numeric traceability. Every number rendered in an explanation must match
   the stored evidence span verbatim. An automated check runs before display;
   any mismatch suppresses the result and raises a flag for human review.

2. Return-type compliance filter. Words like "guaranteed" or "assured" must
   never appear alongside figures classified as indicative or variable.
   Any change to scoring weights or the abstain threshold requires explicit
   human sign-off — not just a code change.