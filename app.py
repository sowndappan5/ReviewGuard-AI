import json
import os
from pathlib import Path
import streamlit as st
from reviewguard.core import review
from reviewguard.llm import llm_review

st.set_page_config(page_title="ReviewGuard AI", page_icon="🛡️", layout="wide")
st.title("🛡️ ReviewGuard AI")
st.caption("Evidence-first pull-request risk triage · Cynbit BitElevate opportunity PoC")
st.info("Static review runs offline. Optional LLM review requires OPENAI_API_KEY. Findings are advisory and require human verification.")

mode = st.radio("Diff source", ["Built-in demo", "Paste unified diff"], horizontal=True)
if mode == "Built-in demo":
    diff = Path(__file__).parent.joinpath("samples", "risky.diff").read_text()
    st.code(diff, language="diff")
else:
    diff = st.text_area("Unified diff", height=260, placeholder="diff --git a/example.py b/example.py\n...")

use_llm = st.checkbox("Add optional LLM semantic review", value=False)
if st.button("Analyze changes", type="primary", disabled=not bool(diff.strip())):
    try:
        with st.spinner("Reviewing changed lines..."):
            extras = llm_review(diff) if use_llm else []
            if use_llm and not os.getenv("OPENAI_API_KEY"):
                st.warning("No OPENAI_API_KEY configured; showing static checks only.")
            report = review(diff, extras)
        st.session_state["report"] = report
    except Exception as exc:
        st.error(f"Analysis failed: {exc}")

if "report" in st.session_state:
    report = st.session_state["report"]
    a, b, c = st.columns(3)
    a.metric("Total findings", report["summary"]["total"])
    b.metric("High / critical", report["summary"]["high_or_critical"])
    c.metric("LLM findings", report["summary"]["llm"])

    st.subheader(report["summary"]["risk_label"].capitalize())
    for finding in report["findings"]:
        with st.expander(f"{finding['severity'].upper()} · {finding['rule_id']} · {finding['file']}:{finding['line']}", expanded=True):
            st.code(finding["evidence"])
            st.write(finding["explanation"])
            st.write("**Suggested action:**", finding["suggestion"])
            st.caption(f"Evidence source: {finding['source']}")

    st.caption(report["limitations"])
    st.download_button(
        "Download JSON review",
        json.dumps(report, indent=2),
        file_name="reviewguard_report.json",
        mime="application/json",
    )