"""Streamlit UI for C2 Contract Risk Engine.

Run:  streamlit run app.py
"""
from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from c2_contract_risk.clauses import RISK_TAXONOMY
from c2_contract_risk.extract import extract_from_pdf

st.set_page_config(page_title="C2 Contract Risk Engine", layout="wide")

st.title("C2 Contract Clause Risk Engine")
st.caption("Local Ollama (qwen2.5:7b) + pypdf - no cloud calls")

with st.sidebar:
    st.header("Settings")
    use_llm = st.checkbox("Use Ollama LLM (uncheck for keyword fallback)", value=True)
    st.markdown("**Risk taxonomy**")
    for c in RISK_TAXONOMY.values():
        with st.expander(c.label):
            st.write(c.definition)
            st.write(c.risk_explanation)

uploaded = st.file_uploader("Upload contract (PDF or .txt)", type=["pdf", "txt"])

RISK_COLOR = {"low": "#16a34a", "medium": "#f59e0b", "high": "#dc2626"}


def render_clause(c):
    color = RISK_COLOR.get(c.risk_level, "#6b7280")
    label = RISK_TAXONOMY[c.clause_type].label
    st.markdown(
        f"<div style='border-left:6px solid {color};padding:8px 12px;margin:8px 0;"
        f"background:#0f172a0d;border-radius:4px'>"
        f"<b>{label}</b> &nbsp; "
        f"<span style='color:{color};font-weight:700'>{c.risk_level.upper()}</span>"
        f"<br><i>{c.rationale}</i>"
        f"<br><pre style='white-space:pre-wrap;font-size:12px'>{c.text}</pre>"
        f"</div>",
        unsafe_allow_html=True,
    )
    with st.expander("Case-law citations"):
        for cite in c.citations:
            st.markdown(f"- **{cite['name']}**, *{cite['cite']}* — {cite['holding']}")


if uploaded is not None:
    suffix = ".pdf" if uploaded.name.lower().endswith(".pdf") else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = Path(tmp.name)

    with st.spinner("Extracting clauses with local LLM..."):
        clauses = extract_from_pdf(tmp_path, use_llm=use_llm)

    if not clauses:
        st.warning("No high-risk clauses identified.")
    else:
        st.success(f"Found {len(clauses)} clause(s) of interest.")

        df = pd.DataFrame(
            [
                {
                    "Type": RISK_TAXONOMY[c.clause_type].label,
                    "Risk": c.risk_level.upper(),
                    "Rationale": c.rationale,
                    "Excerpt": c.text[:160] + ("..." if len(c.text) > 160 else ""),
                }
                for c in clauses
            ]
        )
        st.dataframe(df, use_container_width=True)

        st.subheader("Detail")
        for c in clauses:
            render_clause(c)

        # Downloadable risk report (markdown)
        report_lines = [f"# Risk Report - {uploaded.name}", ""]
        for c in clauses:
            label = RISK_TAXONOMY[c.clause_type].label
            report_lines += [
                f"## {label} - Risk: {c.risk_level.upper()}",
                f"**Rationale**: {c.rationale}",
                "",
                f"> {c.text}",
                "",
                "**Citations**:",
            ]
            for cite in c.citations:
                report_lines.append(f"- {cite['name']}, *{cite['cite']}* - {cite['holding']}")
            report_lines.append("")
        md_blob = "\n".join(report_lines).encode()
        st.download_button("Download risk report (.md)", md_blob, file_name="risk_report.md")

        json_blob = json.dumps([c.to_dict() for c in clauses], indent=2).encode()
        st.download_button("Download raw JSON", json_blob, file_name="clauses.json")
else:
    st.info("Upload a PDF or .txt contract to begin.")
