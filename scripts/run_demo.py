"""End-to-end demo: extract clauses from 3 sample contracts and print summary.

Usage:
    python scripts/run_demo.py            # uses Ollama if reachable, else fallback
    python scripts/run_demo.py --no-llm   # forces keyword fallback
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from c2_contract_risk.clauses import RISK_TAXONOMY
from c2_contract_risk.extract import extract_from_pdf

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures"
SAMPLES = [
    FIX / "saas_master_agreement.txt",
    FIX / "consulting_services_agreement.txt",
    FIX / "equipment_lease.txt",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="Force heuristic fallback")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of pretty text")
    args = ap.parse_args()

    use_llm = False if args.no_llm else None
    output = []
    total_clauses = 0

    for path in SAMPLES:
        clauses = extract_from_pdf(path, use_llm=use_llm)
        total_clauses += len(clauses)
        output.append({"contract": path.name, "n_clauses": len(clauses),
                       "clauses": [c.to_dict() for c in clauses]})

        if not args.json:
            print(f"\n=== {path.name} ({len(clauses)} clauses) ===")
            for c in clauses:
                label = RISK_TAXONOMY[c.clause_type].label
                print(f"  [{c.risk_level.upper():6}] {label}")
                print(f"    > {c.text[:140]}{'...' if len(c.text) > 140 else ''}")
                if c.citations:
                    cite0 = c.citations[0]
                    print(f"    cite: {cite0['name']}, {cite0['cite']}")

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"\nTOTAL clauses extracted across {len(SAMPLES)} contracts: {total_clauses}")


if __name__ == "__main__":
    main()
