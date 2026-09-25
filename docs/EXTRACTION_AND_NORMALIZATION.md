Information Extraction and Normalization
=========================================


The Word-Mismatch Problem
--------------------------

Users and documents use different words for the same concept. A user types
"moderate risk"; a document says "Balanced". A user says "two years"; a
document says "24 months".

The system solves this in two layers:

  Layer 1 — Normalization (structured fields): known synonyms are mapped to
  a canonical internal value at extraction time and again at query-parse time.
  By the time a comparison happens, both sides speak the same language.

  Layer 2 — Semantic matching (unstructured text): the leftover free-text
  from the query and the full document text are compared using TF-IDF cosine
  similarity (RAG mode) or dense embeddings (hybrid mode), which measure
  meaning rather than exact words.


Fields Extracted from Each Document
-------------------------------------

  Field                   Source pattern(s)
  ----------------------  -------------------------------------------------------
  Opportunity ID          "ID: OPP001" label, or "OPP001" token, or filename stem
  Name                    "Name: / Product: / Scheme:" label
  Provider                "Provider: / Offered by: / Issued by:" label
  Category                "Category: / Type:" label
  Min investment (INR)    "minimum investment", "entry ticket", "ticket size" label
  Tenure min/max (months) "tenure / term / duration / lock-in / holding period" label
  Risk                    Keyword scan -> mapped to low | medium | high
  Return min/max (%)      % figures on lines containing "return/coupon/yield/interest"
  Return type             Keyword scan -> indicative | historical | coupon |
                            variable | illustrative | unknown
  Source document         Filename (always present)
  Evidence spans          Verbatim quote + line number for every extracted field

  Missing = None. No guessing, no defaults.


Money Normalization (-> integer rupees)
----------------------------------------

  Input expression             Stored as (INR)
  ---------------------------  ---------------
  "5 crore", "5cr"             50,000,000
  "2 lakh", "2L", "2.5 lac"   200,000 / 250,000
  "₹1,00,000" (Indian comma)  100,000
  "Rs. 75000", "INR 75000"     75,000
  "200000 rupees"              200,000

Commas are stripped before parsing. Unrecognised format -> None.


Tenure Normalization (-> integer months)
-----------------------------------------

  Input expression      tenure_min   tenure_max
  --------------------  -----------  ----------
  "18 months"           18           18
  "2 years"             24           24
  "1.5 yrs"             18           18
  "6-12 months"          6           12
  "1 year to 3 years"   12           36


Repeated units ("months months") in the corpus are collapsed before parsing.


Risk Normalization (-> low | medium | high)
--------------------------------------------

Applied in priority order (first match wins):

  Document says                       -> Stored as
  ----------------------------------  -----------
  "low to moderate"                   medium
  "moderately high", "moderate-high"  high
  "low", "conservative",
  "capital protected", "risk-averse"  low
  "medium", "moderate", "balanced"    medium
  "high", "aggressive",
  "growth oriented"                   high

The query parser applies the same mapping to the user's input before any
comparison is made. "moderate" in a query and "Balanced" in a document both
become medium, so they match.


Return Type Classification
---------------------------

Scanned across the full document text; first match wins:

  Keyword(s) found           -> Return type    Disclaimer shown to user
  -------------------------  ---------------  --------------------------------
  "coupon"                   coupon           (coupon; fixed periodic payment)
  "historical", "past
   performance"              historical       (historical; past performance
                                              is not a guarantee)
  "illustrat..."             illustrative     (illustrative only)
  "variable", "market-linked" variable        (variable; depends on market)
  "indicative", "expected",
  "target"                   indicative       (indicative, not guaranteed)
  (none of the above)        unknown          no disclaimer added


How Semantic Matching Fills the Rest
--------------------------------------

After structured fields (budget, risk, tenure) are matched via normalization,
the leftover free-text from the query is used for text search.

BM25 keyword search finds documents sharing exact tokens with the query text.
It is precise but literal — it will not match "wealth preservation" to "low
risk" because they share no words.

TF-IDF / dense vector search measures meaning-proximity rather than word
overlap. Documents are encoded into a numeric vector; query text is encoded
the same way; the closest vectors are retrieved. This catches paraphrases
and synonyms that normalization does not cover.

The two result lists are merged with Reciprocal Rank Fusion:

  score = sum of  1 / (60 + rank)  across all lists

This merges on rank position rather than raw score, which avoids the problem
of BM25 and cosine similarity being on incompatible numeric scales.


Missing Fields and Scoring
---------------------------

A blank field contributes a score of 0 for that dimension — no penalty
beyond that. 
