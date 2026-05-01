# STATE - c2-contract-risk

Last updated: 2026-04-30

## Status: v0.1.0 - end-to-end working

## What works

- `src/c2_contract_risk/pdf_loader.py` - paragraph-preserving extraction
  from PDF (via `pypdf`) and `.txt` fixtures.
- `src/c2_contract_risk/clauses.py` - 5-class risk taxonomy with
  definition, risk explanation, and 2-3 Westlaw-style case citations each.
- `src/c2_contract_risk/extract.py` - Ollama (`qwen2.5:7b`,
  `format=json`, temperature=0, seed=42) clause extraction with a regex
  keyword fallback so the system degrades gracefully when Ollama is
  unreachable. Citations are auto-attached from the taxonomy.
- `src/c2_contract_risk/eval.py` - precision/recall harness; supports
  fixture eval and CUAD `master_clauses.csv` eval.
- `app.py` - Streamlit upload UI: drop PDF -> table + per-clause cards
  with color-coded risk + downloadable Markdown / JSON risk report.
- `scripts/run_demo.py` - end-to-end demo on 3 in-repo contracts.
- 8 passing pytests covering taxonomy, PDF loader, extraction (offline +
  citation attachment), and eval math.

## Demo numbers (real LLM run)

3 sample contracts, qwen2.5:7b, local Ollama:

- saas_master_agreement.txt -> 5 clauses
- consulting_services_agreement.txt -> 4 clauses
- equipment_lease.txt -> 5 clauses
- **Total: 14 clauses extracted**

## Eval numbers (3 fixtures, real LLM run)

- Micro precision: **1.00**
- Micro recall: **0.93**
- Micro F1: **0.96**
- Per-class F1: auto_renewal 1.0, jurisdiction 1.0, liability_cap 1.0,
  change_of_control 1.0, indemnification 0.80 (one fixture had two
  indemnification clauses but was labelled with one tag).

## Open / next

- CUAD download not exercised here (it's a ~500MB tarball). The code
  path is wired (`evaluate_cuad`) - drop in `master_clauses.csv` +
  `full_contract_pdf/` and re-run.
- LLM rationale strings are short. Could enrich with span-level
  highlighting in the Streamlit UI.
- Add page-number citations once we move from `.txt` fixtures to
  multi-page PDF samples.

## Conventions

- All randomness seeded `random_state = 42`.
- Files <= 300 lines.
- Local Ollama only - no cloud APIs.
- Git identity: Yash Patel <yashpatel06050@gmail.com>.
