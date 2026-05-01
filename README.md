# C2 - LLM Contract Clause Risk Engine

Local-only legal-tech tool. Drop a contract PDF in, get back the risky clauses
(auto-renewal, indemnification, jurisdiction, liability cap, change-of-control)
flagged with a `low/medium/high` risk level, a 1-2 sentence rationale, and 2-3
seminal case-law citations per clause.

**Stack:** 100% local — Ollama (`qwen2.5:7b`, `format=json`) + `pypdf` +
Streamlit. No cloud API. No API keys.

## Quickstart

```bash
# 1. Make sure Ollama is running and the model is pulled
ollama serve &
ollama pull qwen2.5:7b

# 2. Install
pip install -e .

# 3. Demo on 3 sample contracts
python scripts/run_demo.py

# 4. Streamlit UI (drop-PDF -> risk report)
streamlit run app.py

# 5. Tests
pytest -q

# 6. Eval (precision / recall vs. labelled fixtures)
python -m c2_contract_risk.eval
# Or against a local CUAD copy:
python -m c2_contract_risk.eval \
    --cuad-csv /path/to/CUAD_v1/master_clauses.csv \
    --cuad-dir /path/to/CUAD_v1/full_contract_pdf
```

If Ollama is unreachable, the engine transparently falls back to a regex
keyword scanner so tests, demo, and CI all still produce results offline.

## Risk taxonomy

| Key                  | Label                              | Why we flag it |
|----------------------|------------------------------------|----------------|
| `auto_renewal`       | Auto-Renewal / Evergreen           | Vendor lock-in if a narrow notice window is missed |
| `indemnification`    | Indemnification / Hold-Harmless    | Uncapped liability for third-party claims |
| `jurisdiction`       | Governing Law / Forum Selection    | Adverse forum kills remedies |
| `liability_cap`      | Limitation of Liability            | Caps that negate the contract's essential purpose |
| `change_of_control`  | Change of Control / Assignment     | Transaction-killer or consent gate |

Each entry ships with seminal case-law (e.g., *Hadley v. Baxendale*,
*M/S Bremen v. Zapata*, *Hooper v. AGS Computers*) — see
`src/c2_contract_risk/clauses.py`.

## Layout

```
src/c2_contract_risk/
    pdf_loader.py    # paragraph-preserving PDF/text extraction
    clauses.py       # 5-class risk taxonomy + case-law lookup
    extract.py       # Ollama JSON extraction + heuristic fallback
    eval.py          # precision/recall harness (fixtures + CUAD)
app.py               # Streamlit upload UI
scripts/run_demo.py  # 3-contract end-to-end demo
tests/fixtures/      # 3 self-generated sample contracts + label JSON
docs/sample-report.md
```

## Eval result (3 self-generated fixtures, qwen2.5:7b)

| Metric             | Value |
|--------------------|-------|
| Micro precision    | 1.00  |
| Micro recall       | 0.93  |
| Micro F1           | 0.96  |

Seed: `random_state = 42` everywhere.

## Author

Yash Patel | Tempe, AZ | yashpatel06050@gmail.com
GitHub: github.com/ypatel39-commits
