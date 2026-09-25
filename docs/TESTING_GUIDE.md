Testing Guide — NL Retrieval System

Platform: Windows (PowerShell) — macOS/Linux equivalents shown where different

---

1. Prerequisites
You need Python 3.10+ and pip 23+. Check these with python --version and pip --version.
All commands in this guide must be run from the project root directory:
c:\Users\SHREE\OneDrive\Desktop\Nithyashree_aiml\

2. Environment Setup
Create and activate a Python virtual environment.

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
If you see an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first.

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install Dependencies
Install all required packages into your virtual environment:
```powershell
pip install -r requirements.txt
```
This installs pydantic, PyYAML, rank-bm25, pytest, and sentence-transformers. 
Verify the installation by running `pip show rank-bm25 pydantic PyYAML pytest sentence-transformers`.

4. Verify the Data Pipeline
Before querying, confirm the data files are present by running `ls data\`.
You should see opportunities.db, index.json, labelled_examples.csv, and the opportunities/ folder.
If any file is missing, rebuild them:
```powershell
python main.py --extract
python main.py --index
```

5. Running Query Retrieval
The core command for testing is:
```powershell
python main.py --query "<your natural-language requirement>"
```
A well-formed query should mention a budget (e.g. ₹2 lakh), a risk preference (e.g. low risk), or a tenure (e.g. two years).

Mode Selection:
Use `--mode rules` (default) to rank candidates strictly by how well their numbers match the financial constraints.
Use `--mode rag` to blend those strict rules with a semantic meaning score, allowing for fuzzier text-based matches.

Use `--k 5` to change the number of results.

6. Test Scenarios
Run these commands and compare with the expected output format at the bottom.

Sample 1 — Standard Query
```powershell
python main.py --query "I have ₹2 lakh available, prefer medium risk, and want something for around two years."
```
Verify it returns 5 results, showing the ID, score, matched attributes, and at least 2 grounded reasons with quotes.

Sample 2 — Low Budget + Low Risk
```powershell
python main.py --query "I only need to park ₹50,000 for about 1 year and I want low risk."
```
Verify budget_fit appears, risk_fit matches conservative, and all results have a minimum investment ≤ 50000.

Sample 3 — Smoke Test
```powershell
python main.py --query "Find a product with guaranteed 15% return from Zenith AMC."
```
Verify the system abstains or returns results with explicit disclaimers (e.g. "indicative, not guaranteed"). It should never invent a guarantee.

7. Automated Evaluation
Run the built-in evaluation suite:
```powershell
python main.py --eval
```
Look at the OVERALL Hit@5 metric. It should be 1.00. If it is lower, your index may be stale and you should rebuild it.

8. Expected Output Reference
A successful result looks like this:
```
1. [OPP029] Cobalt Multi Asset Strategy - Cobalt Wealth | score 0.801 | source: OPP029.txt
   matched: text_relevance, budget_fit, risk_fit, tenure_fit, return_fit
   - Fits your budget: minimum ₹100,000 ≤ your ₹200,000
     evidence: "1 lakh" (OPP029.txt)
```
An abstain result looks like this:
```
ABSTAINED: No supported recommendation: minimum investments start at ₹100,000, above your ₹25,000 budget.
```

9. Troubleshooting
If you see ModuleNotFoundError, you forgot to activate the virtual environment.
If you see FileNotFoundError for index.json, run the extract and index commands from step 4.
If you see garbled ₹ symbols, run `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`.
If tests fail, run `pytest tests/ -v` to investigate.
