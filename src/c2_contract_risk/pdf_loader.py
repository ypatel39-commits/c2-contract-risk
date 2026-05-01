"""PDF loader: extract paragraph-preserving text from contract PDFs.

Uses pypdf for offline extraction. Also accepts plaintext fixtures for tests.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List


_PARA_SPLIT = re.compile(r"\n\s*\n+")
_WS = re.compile(r"[ \t]+")


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = _WS.sub(" ", text)
    # collapse single newlines inside a paragraph but keep blank-line breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    return text.strip()


def load_pdf_text(path: str | Path) -> str:
    """Return full text of a PDF (or .txt) file.

    Falls back to reading plaintext if extension is .txt — handy for fixtures.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8")

    try:
        from pypdf import PdfReader
    except Exception as e:  # pragma: no cover - import guard
        raise RuntimeError("pypdf not installed; run pip install -e .") from e

    reader = PdfReader(str(p))
    pages: List[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages)


def load_pdf_paragraphs(path: str | Path, min_len: int = 30) -> List[str]:
    """Split a PDF/.txt contract into paragraph-level chunks.

    Paragraph boundaries are blank lines. Empty / very short fragments are dropped.
    """
    raw = load_pdf_text(path)
    parts = _PARA_SPLIT.split(raw)
    out: List[str] = []
    for part in parts:
        cleaned = _clean(part)
        if len(cleaned) >= min_len:
            out.append(cleaned)
    return out


def chunk_paragraphs(paras: List[str], max_chars: int = 4000) -> List[str]:
    """Group paragraphs into LLM-sized chunks while preserving boundaries."""
    chunks: List[str] = []
    buf: List[str] = []
    size = 0
    for p in paras:
        if size + len(p) > max_chars and buf:
            chunks.append("\n\n".join(buf))
            buf, size = [], 0
        buf.append(p)
        size += len(p) + 2
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks
