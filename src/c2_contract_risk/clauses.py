"""Risk clause taxonomy + in-repo legal lookup table.

Five risk types we flag, each with a definition, a risk explanation,
and a small set of well-known case-law citations (Westlaw-style).

Citations are intentionally seminal / well-established cases. Use as
analogical authority — pair with current jurisdiction-specific research.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class CaseCitation:
    name: str          # e.g., "Hadley v. Baxendale"
    cite: str          # e.g., "9 Ex. 341 (1854)" / "550 U.S. 544 (2007)"
    holding: str       # one-line holding relevant to the clause type


@dataclass(frozen=True)
class ClauseRisk:
    key: str
    label: str
    definition: str
    risk_explanation: str
    cases: List[CaseCitation] = field(default_factory=list)


# ------------------------------ Taxonomy ------------------------------

RISK_TAXONOMY: Dict[str, ClauseRisk] = {
    "auto_renewal": ClauseRisk(
        key="auto_renewal",
        label="Auto-Renewal / Evergreen",
        definition=(
            "A clause that automatically extends the contract term unless a party "
            "affirmatively opts out within a notice window."
        ),
        risk_explanation=(
            "Evergreen clauses can lock a counterparty into another full term if a "
            "narrow notice window is missed, resulting in unanticipated cost and "
            "vendor lock-in. Several state statutes (e.g., Cal. Bus. & Prof. Code "
            "§ 17600 et seq.) further regulate consumer auto-renewals; commercial "
            "courts routinely enforce them when notice terms are clear."
        ),
        cases=[
            CaseCitation(
                "ProCD, Inc. v. Zeidenberg",
                "86 F.3d 1447 (7th Cir. 1996)",
                "Standardized renewal/assent terms enforceable absent unconscionability.",
            ),
            CaseCitation(
                "Schnabel v. Trilegiant Corp.",
                "697 F.3d 110 (2d Cir. 2012)",
                "Auto-renewal terms unenforceable where notice was inconspicuous.",
            ),
            CaseCitation(
                "Williams v. Walker-Thomas Furniture Co.",
                "350 F.2d 445 (D.C. Cir. 1965)",
                "Unconscionable adhesion terms (incl. renewal) may be voided.",
            ),
        ],
    ),
    "indemnification": ClauseRisk(
        key="indemnification",
        label="Indemnification / Hold-Harmless",
        definition=(
            "A clause requiring one party to defend, indemnify, and hold harmless "
            "the other against specified third-party claims or losses."
        ),
        risk_explanation=(
            "Broad indemnities can shift liability for the indemnitee's own "
            "negligence and uncapped third-party claims, materially expanding "
            "balance-sheet exposure beyond the contract value. Courts generally "
            "require clear, unambiguous language to indemnify a party against its "
            "own negligence."
        ),
        cases=[
            CaseCitation(
                "Hooper Assocs., Ltd. v. AGS Computers, Inc.",
                "74 N.Y.2d 487 (1989)",
                "Indemnity for first-party claims requires unmistakably clear language.",
            ),
            CaseCitation(
                "Ethyl Corp. v. Daniel Constr. Co.",
                "725 S.W.2d 705 (Tex. 1987)",
                "Express-negligence rule: indemnity for own negligence must be express.",
            ),
            CaseCitation(
                "Heat & Power Corp. v. Air Prods. & Chems., Inc.",
                "320 Md. 584 (1990)",
                "Strictly construes broad hold-harmless language against drafter.",
            ),
        ],
    ),
    "jurisdiction": ClauseRisk(
        key="jurisdiction",
        label="Governing Law / Forum Selection",
        definition=(
            "A clause designating the governing law and/or exclusive forum for "
            "disputes arising under the contract."
        ),
        risk_explanation=(
            "An adverse forum or governing-law choice can dramatically raise "
            "litigation cost, alter substantive rights, and effectively foreclose "
            "remedies (e.g., class-action waivers, fee-shifting). Forum-selection "
            "clauses are presumptively enforceable absent fraud, overreach, or "
            "strong public policy."
        ),
        cases=[
            CaseCitation(
                "M/S Bremen v. Zapata Off-Shore Co.",
                "407 U.S. 1 (1972)",
                "Forum-selection clauses are prima facie valid and enforceable.",
            ),
            CaseCitation(
                "Carnival Cruise Lines, Inc. v. Shute",
                "499 U.S. 585 (1991)",
                "Form-contract forum clauses enforceable if reasonable and noticed.",
            ),
            CaseCitation(
                "Atl. Marine Constr. Co. v. U.S. Dist. Court",
                "571 U.S. 49 (2013)",
                "Valid forum clauses enforced via § 1404(a) absent extraordinary cause.",
            ),
        ],
    ),
    "liability_cap": ClauseRisk(
        key="liability_cap",
        label="Limitation of Liability / Damages Cap",
        definition=(
            "A clause limiting the type or dollar amount of damages recoverable "
            "(e.g., excludes consequential damages; caps at fees paid)."
        ),
        risk_explanation=(
            "An aggressive cap (e.g., 3 months of fees) can leave the injured "
            "party with no meaningful remedy for material breach or data-loss "
            "events. Courts often enforce caps between sophisticated parties but "
            "scrutinize them where they negate the contract's essential purpose "
            "or violate public policy."
        ),
        cases=[
            CaseCitation(
                "Hadley v. Baxendale",
                "9 Ex. 341 (1854)",
                "Foreseeability rule for consequential damages — backdrop for caps.",
            ),
            CaseCitation(
                "Metro. Life Ins. Co. v. Noble Lowndes Int'l, Inc.",
                "84 N.Y.2d 430 (1994)",
                "Liability caps enforceable absent gross negligence / willful misconduct.",
            ),
            CaseCitation(
                "Kalisch-Jarcho, Inc. v. City of New York",
                "58 N.Y.2d 377 (1983)",
                "Exculpatory clauses unenforceable for intentional or grossly negligent acts.",
            ),
        ],
    ),
    "change_of_control": ClauseRisk(
        key="change_of_control",
        label="Change of Control / Assignment",
        definition=(
            "A clause that triggers consent, termination, or other rights upon a "
            "merger, acquisition, or change in beneficial ownership of a party."
        ),
        risk_explanation=(
            "CoC triggers can let a counterparty unilaterally terminate or "
            "renegotiate on a transaction, destroying deal value or creating "
            "consent gating that delays close. They also frequently interact "
            "with anti-assignment provisions to capture indirect transfers."
        ),
        cases=[
            CaseCitation(
                "SQL Solutions, Inc. v. Oracle Corp.",
                "1991 WL 626458 (N.D. Cal. 1991)",
                "Reverse triangular merger treated as assignment of non-exclusive license.",
            ),
            CaseCitation(
                "Meso Scale Diagnostics, LLC v. Roche Diagnostics GmbH",
                "62 A.3d 62 (Del. Ch. 2013)",
                "Whether merger = assignment depends on contractual language and context.",
            ),
            CaseCitation(
                "Cincom Sys., Inc. v. Novelis Corp.",
                "581 F.3d 431 (6th Cir. 2009)",
                "Statutory merger transferred software license; no consent obtained = breach.",
            ),
        ],
    ),
}


CLAUSE_KEYS: List[str] = list(RISK_TAXONOMY.keys())


def get_clause_definition(key: str) -> ClauseRisk:
    if key not in RISK_TAXONOMY:
        raise KeyError(f"Unknown clause key: {key}. Valid: {CLAUSE_KEYS}")
    return RISK_TAXONOMY[key]


def taxonomy_summary() -> str:
    """Compact human-readable summary used in LLM system prompts."""
    lines = []
    for c in RISK_TAXONOMY.values():
        lines.append(f"- {c.key} ({c.label}): {c.definition}")
    return "\n".join(lines)
