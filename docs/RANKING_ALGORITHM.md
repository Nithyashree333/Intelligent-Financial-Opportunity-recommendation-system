Ranking Algorithm
=================


The system uses a hybrid ranking approach that combines two complementary
signals: textual relevance from the retrieval layer (BM25 keyword matching
and TF-IDF/dense semantic similarity) and structured attribute fits
computed directly from the extracted opportunity fields. Retrieval narrows
the corpus to the top-50 most textually relevant candidates. Ranking then
re-scores those candidates using the user's structured intent — budget, risk,
tenure, and expected return — alongside the retrieval score. This separation
ensures that semantically similar but financially unsuitable opportunities are
corrected before results are shown.


Budget is the only hard constraint in the pipeline. If a candidate's minimum
investment exceeds the user's stated budget, it is eliminated entirely before
scoring begins — it receives no score and does not appear in results. Every
other attribute is a soft fit: a partial match still contributes to the score
rather than causing elimination. Risk fit is 1.0 for an exact match (e.g.
user says medium, document is medium), 0.5 for an adjacent level (medium vs
low or medium vs high), and 0.0 for a full mismatch. Tenure fit is computed
as the proportional overlap between the user's desired horizon (±3 months
tolerance) and the opportunity's tenure range — a perfect overlap scores 1.0,
no overlap scores 0.0. Return fit scales the stated minimum return linearly
across a 0–20% reference range, capped at 1.0.


The final score for each candidate is a weighted average of the five signals:

  Signal              Weight   What it captures
  ------------------  -------  -----------------------------------------
  text_relevance      0.25     BM25 / semantic similarity from retrieval
  budget_fit          0.25     Binary: 1.0 if budget >= minimum, else 0.0
  risk_fit            0.20     Exact=1.0, adjacent=0.5, mismatch=0.0
  tenure_fit          0.20     Proportional overlap within ±3-month window
  return_fit          0.10     Linear scale of return_min over 0–20% range

  score = Σ (weight × fit) / Σ weights

Weights are re-normalised over only the signals that are available for a
given candidate. If a field is missing (e.g. risk not stated in the document),
its weight is dropped from the denominator so the remaining signals are not
penalised for someone else's incomplete data.


If the highest-scoring candidate does not clear a minimum threshold of 0.25,
the system abstains — it prints a refusal message explaining why no suitable
recommendation was made rather than surfacing a low-confidence result. In RAG
mode, a TF-IDF cosine similarity score (weight 0.40) is blended with the
rules score (weight 0.60) before this threshold check, giving more influence
to semantic language alignment while still preserving the structured
constraint logic. All weights and the abstain threshold are configurable in
config.yaml without any code changes.
