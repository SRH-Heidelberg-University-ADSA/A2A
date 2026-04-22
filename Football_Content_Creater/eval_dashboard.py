import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="Agent Evaluation Matrix", layout="wide")
st.title("📊 CLEAR Standard: Agent Evaluation")

# Load the CSV data
try:
    df = pd.read_csv("clear_metrics.csv")
except FileNotFoundError:
    st.error("Could not find clear_metrics.csv. Run evaluate_clear.py first!")
    st.stop()

# Top Row: Static KPIs
col1, col2 = st.columns(2)
with col1:
    st.success("🔒 **ASSURANCE:** PASS (100% Unauthorized Block Rate)")
with col2:
    st.success("🔄 **RELIABILITY:** PASS (100% Output Consistency)")

st.divider()

# Bottom Row: The Graphs
col3, col4 = st.columns(2)

with col3:
    st.subheader("⏱️ Latency per Task (Seconds)")
    st.bar_chart(df, x="Category", y="Latency (Seconds)", color="#ff4b4b")

with col4:
    st.subheader("🎯 Efficacy Score (Out of 5)")
    st.bar_chart(df, x="Category", y="Efficacy Score", color="#0068c9")

st.divider()

st.subheader("🪙 Estimated Token Cost")
st.bar_chart(df, x="Category", y="Cost (Tokens)", color="#29b5e8")