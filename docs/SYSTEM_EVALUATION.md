Evaluation against `labelled_examples.csv` using the full hybrid pipeline yields a perfect overall Hit@5 of 1.00, meaning at least one relevant opportunity was successfully retrieved for every query.

| Query snippet | Hit@5 | Abstain |
|---|---|---|
| I have ₹2 lakh, want medium risk and around 2 years... | 1 | False |
| I only need to park ₹50,000 for about 1 year and I want low risk. | 1 | False |
| Budget is ₹1 lakh, high risk is acceptable... | 1 | False |
| I have ₹80,000 and want moderate risk for roughly 18 months. | 1 | False |
| Looking for something around 6 to 12 months, under ₹1 lakh... | 1 | False |
| I can invest ₹3 lakh, accept high risk and want at least 3 years. | 1 | False |
| I have ₹2.5 lakh and prefer moderate risk for 2 to 3 years. | 1 | False |
| I need a conservative option for 3 to 6 months with only ₹10,000. | 1 | False |
| **OVERALL** | **1.00** | — |

To control hallucinations, the system relies strictly on verbatim evidence spans, never inventing any fields or returns. It leaves missing data safely blank, classifies returns to enforce strict disclaimers against false guarantees, and explicitly abstains if no match clears the confidence threshold.

The codebase is written in readable, modular Python that enforces a strict architectural separation between the extraction, retrieval, ranking, and evaluation components. It includes a complete `requirements.txt` alongside reproducible run instructions, and is backed by basic tests and pydantic validation checks to ensure reliable execution.
