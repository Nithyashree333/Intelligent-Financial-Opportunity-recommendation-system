<<<<<<< HEAD
# Intelligent-Financial-Opportunity-recommendation-system
This is system designed for analysing the in house opprtunities available for investing based on user preferences and Constraints. I involves text extraction, normalization. It uses hybrid fusion search model. Evaluate on hit@5
=======
# Financial Opportunity Analysis & Recommendation Engine

Grounded, abstaining recommendation engine over unstructured opportunity
documents. Rules mode is complete; RAG mode is a stub behind the same
interfaces (see docs/TECHNICAL_NOTE.md).

## Setup
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    # optional, for dense/hybrid retrieval:
    pip install sentence-transformers

## Run
Place the supplied dataset under `data/` (opportunities/*.txt,
labelled_examples.csv), then:

    python main.py --extract          # documents -> SQLite
    python main.py --index            # BM25 (+ dense vectors if installed)
    python main.py --query "I have ₹2 lakh available, prefer medium risk, and want something for around two years."
    python main.py --eval             # P@5 / R@5 / Hit@5 + failure table
    pytest                            # validation checks

## Layout
See DESIGN.md / docs/TECHNICAL_NOTE.md. One module per pipeline stage;
`ranker/base.py` + `explainer/base.py` are the seams for the RAG variant.
>>>>>>> 6c51c0b (Pushed)
