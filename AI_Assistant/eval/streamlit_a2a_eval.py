"""
A2A Coordination Evaluation Dashboard — Simple KPI View
Shows routing accuracy, latency, output completeness, and token usage
per agent/category using results from run_a2a_eval.py.
"""

import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="A2A Eval", page_icon="🔗", layout="wide")

st.title("🔗 A2A Coordination Evaluation")

# --- Load or Run ---
results_file = Path(__file__).parent / "a2a_eval_results.json"

if st.button("🚀 Run Evaluation", type="primary"):
    with st.spinner("Running evaluation..."):
        try:
            from run_a2a_eval import run_evaluation
            run_evaluation()
            st.success("Done!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")
            st.stop()

if not results_file.exists():
    st.info("No results found. Click **Run Evaluation** to generate them.")
    st.stop()

with open(results_file, "r") as f:
    data = json.load(f)

overall = data["overall"]
per_category = data["per_category"]
individual = data["individual_results"]

# --- Overall KPIs ---
st.markdown("---")
st.subheader("Overall Performance")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Routing Accuracy", f"{overall['routing_accuracy']:.1f}%")
c2.metric("Avg Latency", f"{overall['average_latency']:.2f}s")
c3.metric("Output Complete", f"{overall['output_completeness']:.1f}%")
c4.metric("Total Input Tokens", f"{overall.get('total_input_tokens', 0):,}")
c5.metric("Total Output Tokens", f"{overall.get('total_output_tokens', 0):,}")

# --- Per-Category KPIs ---
st.markdown("---")
st.subheader("Per-Agent Metrics")

for cat, stats in per_category.items():
    label = cat.replace("_", " ").title()
    with st.container():
        st.markdown(f"**{label}** ({stats['total']} tasks)")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Routing", f"{stats['routing_accuracy']:.0f}%")
        k2.metric("Latency", f"{stats['avg_latency']:.2f}s")
        k3.metric("Complete", f"{stats['output_completeness']:.0f}%")
        k4.metric("In Tokens", f"{stats.get('input_tokens', 0):,}")
        k5.metric("Out Tokens", f"{stats.get('output_tokens', 0):,}")
        st.markdown("---")

# --- Individual Results ---
st.subheader("Test Results")

for r in individual:
    icon = "✅" if r["routing_correct"] else "❌"
    with st.expander(f"{icon} {r['task_id']} — {r.get('query', '')[:70]}"):
        st.markdown(f"**Expected:** `{r.get('expected_agent') or r.get('expected_tool', 'fallback')}` | "
                    f"**Got:** `{r.get('actual_agent') or r.get('actual_tool') or 'fallback'}`")
        st.markdown(f"**Latency:** {r['latency']:.2f}s | "
                    f"**Input Tokens:** {r.get('input_tokens', 0)} | "
                    f"**Output Tokens:** {r.get('output_tokens', 0)}")
        if r.get("response_preview"):
            st.text(r["response_preview"])
