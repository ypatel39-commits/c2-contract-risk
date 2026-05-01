"""Smoke tests for the C2 contract risk engine (offline / fallback path)."""
from __future__ import annotations

from pathlib import Path

import pytest

from c2_contract_risk.clauses import CLAUSE_KEYS, RISK_TAXONOMY, get_clause_definition
from c2_contract_risk.eval import evaluate_fixture_set, score, EvalRow
from c2_contract_risk.extract import (
    ExtractedClause,
    extract_from_pdf,
    extract_from_text,
)
from c2_contract_risk.pdf_loader import load_pdf_paragraphs

FIX = Path(__file__).parent / "fixtures"


# ---------- 1. taxonomy ----------

def test_taxonomy_has_five_keys():
    assert set(CLAUSE_KEYS) == {
        "auto_renewal",
        "indemnification",
        "jurisdiction",
        "liability_cap",
        "change_of_control",
    }
    for k in CLAUSE_KEYS:
        c = get_clause_definition(k)
        assert c.definition and c.risk_explanation
        assert len(c.cases) >= 2, f"{k} needs >=2 case citations"


# ---------- 2. pdf_loader ----------

def test_pdf_loader_paragraphs():
    paras = load_pdf_paragraphs(FIX / "saas_master_agreement.txt")
    assert len(paras) >= 6
    assert all("\n\n" not in p for p in paras)


# ---------- 3. heuristic extraction (offline) ----------

def test_extract_saas_finds_all_five_categories():
    clauses = extract_from_pdf(FIX / "saas_master_agreement.txt", use_llm=False)
    found = {c.clause_type for c in clauses}
    assert found == set(CLAUSE_KEYS), f"missing: {set(CLAUSE_KEYS) - found}"


def test_extract_returns_dataclass_with_citations():
    clauses = extract_from_text(
        "The agreement is governed by the laws of the State of Delaware.",
        use_llm=False,
    )
    assert clauses
    c = clauses[0]
    assert isinstance(c, ExtractedClause)
    assert c.clause_type == "jurisdiction"
    assert c.citations and "name" in c.citations[0]


def test_extract_consulting_basic_categories():
    clauses = extract_from_pdf(
        FIX / "consulting_services_agreement.txt", use_llm=False,
    )
    types = {c.clause_type for c in clauses}
    assert "indemnification" in types
    assert "liability_cap" in types
    assert "jurisdiction" in types


# ---------- 4. eval harness ----------

def test_eval_score_math():
    rows = [
        EvalRow("a", ["auto_renewal", "indemnification"], ["auto_renewal"]),
        EvalRow("b", ["liability_cap"], ["liability_cap", "jurisdiction"]),
    ]
    rep = score(rows)
    assert 0.0 < rep.micro_precision <= 1.0
    assert 0.0 < rep.micro_recall <= 1.0


def test_eval_fixture_set_runs_offline():
    rep = evaluate_fixture_set(FIX, use_llm=False)
    assert rep.rows, "no fixtures evaluated"
    assert rep.micro_recall >= 0.6, f"recall too low: {rep.micro_recall}"


# ---------- 5. data integrity ----------

def test_each_taxonomy_case_has_required_fields():
    for key, info in RISK_TAXONOMY.items():
        for case in info.cases:
            assert case.name and case.cite and case.holding, key
