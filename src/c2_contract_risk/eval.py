"""Evaluation harness: precision / recall vs. labelled ground truth.

CUAD (Contract Understanding Atticus Dataset) is large (~500MB) — by default
we evaluate against the smaller in-repo fixture set. Pass --cuad <path> to
evaluate against a CUAD master_clauses.csv subset if you have one locally.
"""
from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .clauses import CLAUSE_KEYS
from .extract import extract_from_text, extract_from_pdf

random.seed(42)

# Map CUAD column header substrings -> our taxonomy keys
_CUAD_MAP = {
    "renewal term": "auto_renewal",
    "auto-renewal": "auto_renewal",
    "auto renewal": "auto_renewal",
    "indemnification": "indemnification",
    "governing law": "jurisdiction",
    "venue": "jurisdiction",
    "cap on liability": "liability_cap",
    "limitation of liability": "liability_cap",
    "change of control": "change_of_control",
    "anti-assignment": "change_of_control",
}


@dataclass
class EvalRow:
    contract: str
    expected: List[str]
    predicted: List[str]


@dataclass
class EvalReport:
    rows: List[EvalRow]
    precision: Dict[str, float]
    recall: Dict[str, float]
    f1: Dict[str, float]
    micro_precision: float
    micro_recall: float
    micro_f1: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_contracts": len(self.rows),
            "per_class": {
                k: {"precision": self.precision[k], "recall": self.recall[k], "f1": self.f1[k]}
                for k in CLAUSE_KEYS
            },
            "micro": {
                "precision": self.micro_precision,
                "recall": self.micro_recall,
                "f1": self.micro_f1,
            },
        }


# -------------------- Metric math --------------------

def _prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def score(rows: Iterable[EvalRow]) -> EvalReport:
    rows = list(rows)
    per: Dict[str, Dict[str, int]] = {k: {"tp": 0, "fp": 0, "fn": 0} for k in CLAUSE_KEYS}
    for row in rows:
        exp = set(row.expected) & set(CLAUSE_KEYS)
        pred = set(row.predicted) & set(CLAUSE_KEYS)
        for k in CLAUSE_KEYS:
            if k in exp and k in pred:
                per[k]["tp"] += 1
            elif k in pred and k not in exp:
                per[k]["fp"] += 1
            elif k in exp and k not in pred:
                per[k]["fn"] += 1
    precision, recall, f1 = {}, {}, {}
    micro_tp = micro_fp = micro_fn = 0
    for k, v in per.items():
        p, r, f = _prf(v["tp"], v["fp"], v["fn"])
        precision[k], recall[k], f1[k] = p, r, f
        micro_tp += v["tp"]; micro_fp += v["fp"]; micro_fn += v["fn"]
    mp, mr, mf = _prf(micro_tp, micro_fp, micro_fn)
    return EvalReport(rows, precision, recall, f1, mp, mr, mf)


# -------------------- Fixture-based eval --------------------

def evaluate_fixture_set(
    fixtures_dir: str | Path,
    *,
    use_llm: bool | None = None,
) -> EvalReport:
    """Evaluate against tests/fixtures/*.txt with sibling *.labels.json files."""
    d = Path(fixtures_dir)
    rows: List[EvalRow] = []
    for txt in sorted(d.glob("*.txt")):
        labels_path = txt.with_suffix(".labels.json")
        if not labels_path.exists():
            continue
        expected = json.loads(labels_path.read_text())
        clauses = extract_from_pdf(txt, use_llm=use_llm)
        predicted = sorted({c.clause_type for c in clauses})
        rows.append(EvalRow(txt.name, sorted(expected), predicted))
    return score(rows)


# -------------------- CUAD eval --------------------

def _cuad_expected_for_row(headers: List[str], row: List[str]) -> List[str]:
    """Translate a CUAD master_clauses.csv row into our taxonomy keys."""
    found = set()
    for h, val in zip(headers, row):
        if not val or val.strip() in {"", "[]"}:
            continue
        h_lower = h.lower()
        for needle, ckey in _CUAD_MAP.items():
            if needle in h_lower:
                found.add(ckey)
    return sorted(found)


def evaluate_cuad(
    master_csv: str | Path,
    contracts_dir: str | Path,
    *,
    sample_size: int = 100,
    use_llm: bool | None = None,
) -> EvalReport:
    """Evaluate against CUAD master_clauses.csv + contracts/CUAD_v1/full_contract_pdf/."""
    csv_path = Path(master_csv)
    cdir = Path(contracts_dir)
    rows: List[EvalRow] = []

    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        headers = next(reader)
        all_rows = list(reader)

    rng = random.Random(42)
    sample = rng.sample(all_rows, min(sample_size, len(all_rows)))
    for r in sample:
        contract_name = r[0]
        expected = _cuad_expected_for_row(headers, r)
        # CUAD organizes contracts in nested subfolders; fall back to glob
        candidates = list(cdir.rglob(f"{Path(contract_name).stem}*"))
        candidates = [c for c in candidates if c.suffix.lower() in {".pdf", ".txt"}]
        if not candidates:
            continue
        try:
            clauses = extract_from_pdf(candidates[0], use_llm=use_llm)
        except Exception:
            continue
        predicted = sorted({c.clause_type for c in clauses})
        rows.append(EvalRow(contract_name, expected, predicted))
    return score(rows)


# -------------------- CLI --------------------

def main() -> None:
    import click

    @click.command()
    @click.option("--fixtures", default="tests/fixtures", help="Fixture dir")
    @click.option("--cuad-csv", default=None, help="CUAD master_clauses.csv path")
    @click.option("--cuad-dir", default=None, help="CUAD contracts dir")
    @click.option("--no-llm", is_flag=True, help="Force heuristic fallback")
    def cli(fixtures, cuad_csv, cuad_dir, no_llm):
        use_llm = False if no_llm else None
        if cuad_csv and cuad_dir:
            rep = evaluate_cuad(cuad_csv, cuad_dir, use_llm=use_llm)
        else:
            rep = evaluate_fixture_set(fixtures, use_llm=use_llm)
        print(json.dumps(rep.to_dict(), indent=2))

    cli()


if __name__ == "__main__":
    main()
