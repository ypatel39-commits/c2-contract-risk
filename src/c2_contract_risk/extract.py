"""LLM-based clause extraction via local Ollama (qwen2.5:7b, format=json).

Falls back to a regex/keyword scanner when Ollama is unreachable so tests
and demos still produce results offline.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .clauses import CLAUSE_KEYS, RISK_TAXONOMY, taxonomy_summary
from .pdf_loader import chunk_paragraphs, load_pdf_paragraphs

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:7b"
RANDOM_SEED = 42

RISK_LEVELS = ("low", "medium", "high")


@dataclass
class ExtractedClause:
    clause_type: str          # one of CLAUSE_KEYS
    text: str                 # verbatim excerpt
    risk_level: str           # low / medium / high
    rationale: str            # 1-2 sentence why
    citations: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ------------------------------ Prompts ------------------------------

SYSTEM_PROMPT = (
    "You are a senior contracts attorney. From the contract excerpt, identify "
    "any of the following high-risk clause types and extract them verbatim:\n"
    f"{taxonomy_summary()}\n\n"
    "Return STRICT JSON with shape:\n"
    "{\"clauses\": [{\"clause_type\": one of "
    f"{CLAUSE_KEYS}, "
    "\"text\": verbatim excerpt (<=400 chars), "
    "\"risk_level\": one of [\"low\",\"medium\",\"high\"], "
    "\"rationale\": 1-2 sentences}]}\n"
    "If none are present, return {\"clauses\": []}. No commentary outside JSON."
)


# ------------------------------ Ollama call ---------------------------

def _ollama_available(timeout: float = 1.5) -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _call_ollama(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 120) -> Dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.0, "seed": RANDOM_SEED},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    body = r.json()
    raw = body.get("response", "{}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # last-ditch: pull first {...} block
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {"clauses": []}


# ------------------------------ Heuristic fallback ---------------------

_KEYWORDS = {
    "auto_renewal": [
        r"automatic(ally)?\s+renew", r"evergreen", r"renewal\s+term",
        r"unless\s+(either|a)\s+party.*notice",
    ],
    "indemnification": [
        r"indemnif", r"hold\s+harmless", r"defend\s+and\s+indemnify",
    ],
    "jurisdiction": [
        r"governed\s+by\s+the\s+laws", r"exclusive\s+(jurisdiction|venue)",
        r"forum\s+selection", r"courts\s+of\s+the\s+state",
    ],
    "liability_cap": [
        r"limitation\s+of\s+liability", r"in\s+no\s+event\s+shall",
        r"aggregate\s+liability", r"consequential\s+damages",
    ],
    "change_of_control": [
        r"change\s+of\s+control", r"merger\s+or\s+acquisition",
        r"assignment", r"successor\s+in\s+interest",
    ],
}


def _heuristic_scan(paragraphs: List[str]) -> List[ExtractedClause]:
    out: List[ExtractedClause] = []
    for para in paragraphs:
        for ckey, patterns in _KEYWORDS.items():
            if any(re.search(p, para, re.IGNORECASE) for p in patterns):
                risk = "high" if re.search(
                    r"(uncapped|unlimited|sole\s+discretion|in\s+no\s+event)",
                    para, re.IGNORECASE,
                ) else "medium"
                out.append(
                    _attach_citations(
                        ExtractedClause(
                            clause_type=ckey,
                            text=para[:400],
                            risk_level=risk,
                            rationale="Keyword-match fallback (Ollama unavailable).",
                        )
                    )
                )
                # allow multiple clause types per paragraph (e.g., "limitation
                # of liability... indemnification" header)
    return _dedupe(out)


# ------------------------------ Public API ----------------------------

def _attach_citations(c: ExtractedClause) -> ExtractedClause:
    info = RISK_TAXONOMY.get(c.clause_type)
    if info:
        c.citations = [
            {"name": cs.name, "cite": cs.cite, "holding": cs.holding}
            for cs in info.cases
        ]
    return c


def _validate(raw: Dict[str, Any]) -> List[ExtractedClause]:
    out: List[ExtractedClause] = []
    for item in raw.get("clauses", []) or []:
        ctype = str(item.get("clause_type", "")).strip()
        if ctype not in CLAUSE_KEYS:
            continue
        text = str(item.get("text", "")).strip()[:400]
        risk = str(item.get("risk_level", "medium")).lower()
        if risk not in RISK_LEVELS:
            risk = "medium"
        rationale = str(item.get("rationale", "")).strip()[:500]
        if not text:
            continue
        out.append(_attach_citations(ExtractedClause(ctype, text, risk, rationale)))
    return out


def extract_from_text(
    contract_text: str,
    *,
    model: str = DEFAULT_MODEL,
    use_llm: Optional[bool] = None,
) -> List[ExtractedClause]:
    """Run extraction over an in-memory contract string."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", contract_text) if p.strip()]
    return _extract_from_paragraphs(paragraphs, model=model, use_llm=use_llm)


def extract_from_pdf(
    path: str | Path,
    *,
    model: str = DEFAULT_MODEL,
    use_llm: Optional[bool] = None,
) -> List[ExtractedClause]:
    """Run extraction over a contract PDF (or .txt fixture)."""
    paragraphs = load_pdf_paragraphs(path)
    return _extract_from_paragraphs(paragraphs, model=model, use_llm=use_llm)


def _extract_from_paragraphs(
    paragraphs: List[str],
    *,
    model: str,
    use_llm: Optional[bool],
) -> List[ExtractedClause]:
    if use_llm is None:
        use_llm = _ollama_available()

    if not use_llm:
        return _heuristic_scan(paragraphs)

    chunks = chunk_paragraphs(paragraphs, max_chars=3500)
    results: List[ExtractedClause] = []
    for chunk in chunks:
        try:
            raw = _call_ollama(
                f"Contract excerpt:\n\n{chunk}\n\nReturn JSON now.",
                model=model,
            )
            results.extend(_validate(raw))
        except Exception:
            # graceful degradation per chunk
            results.extend(_heuristic_scan([chunk]))
    return _dedupe(results)


def _dedupe(items: List[ExtractedClause]) -> List[ExtractedClause]:
    seen = set()
    out = []
    for c in items:
        key = (c.clause_type, c.text[:120].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out
