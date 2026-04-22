import streamlit as st
import requests
import time

# ---------------- 1. PAGE CONFIG & STYLE ----------------
st.set_page_config(page_title="Krishi-Intel Pro", page_icon="🌾", layout="wide")

st.markdown("""     # page styling how it looks 
<style>
.stApp { background: linear-gradient(135deg,#f4f8f5,#e6f0ea,#ddebe4); }
[data-testid="stChatMessageContent"] { border-radius:14px; padding:16px; border:1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ---------------- 2. CONNECTION SETTINGS ----------------
# The internal bridge to your FastAPI Backend
API_URL = "http://127.0.0.1:8001/chat"
HEALTH_URL = "http://127.0.0.1:8001/agent.json" # <-- Updated to point to a real page

def check_backend():
    try:
        # Quick ping to see if the server is alive
        response = requests.get(HEALTH_URL, timeout=2)
        return response.status_code == 200
    except:
        return False

# ---------------- 3. SIDEBAR (Health Monitor) ----------------
with st.sidebar:
    st.title("🌾 Krishi-Intel Settings")
    
    # Visual Connection Indicator
    if check_backend():
        st.success("● Backend Connected")
    else:
        st.error("○ Backend Offline")
        st.warning("Please run 'python Fast_api.py' in your terminal.")

    st.divider()
    st.info("""
    **System Info:**
    - Model: all-MiniLM-L6-v2 (Local)
    - Mode: Single-Agent Reasoning
    """)
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ---------------- 4. CHAT INTERFACE ----------------
st.title("🌾 Krishi-Intel Pro")
st.caption("Your AI Agriculture Assistant")
st.divider()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- 5. INPUT & REASONING ----------------
if prompt := st.chat_input("Ask about weather, soil, or farming techniques..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant Response Logic
    with st.chat_message("assistant"):
        with st.status("Agent Reasoning...", expanded=True) as status:
            data = None
            
            # ---> ADD YOUR SECRET PASSWORD HERE <---
            headers = {"Authorization": "Bearer krishi-secret-123"}
            
            try:
                # FIRST ATTEMPT
                res = requests.post(API_URL, json={"message": prompt}, headers=headers, timeout=15)
                data = res.json()
            except Exception:
                # RETRY LOGIC (Wait 3 seconds if the backend is still booting up)
                time.sleep(3)
                try:
                    res = requests.post(API_URL, json={"message": prompt}, headers=headers, timeout=20)
                    data = res.json()
                except Exception as e:
                    status.update(label="System Error", state="error")
                    st.error(f"Backend unreachable: {e}")
                    st.stop()
            
            # Handling reasoning steps (displaying which tools were used)
            if data and "intermediate_steps" in data and data["intermediate_steps"]:
                for step in data["intermediate_steps"]:
                    # Adjust this depending on if steps are strings or objects
                    tool_name = step[0] if isinstance(step, (list, tuple)) else step
                    st.write(f"🔍 Executing: **{tool_name}**")
                    time.sleep(0.4)
            
            status.update(label="Analysis Complete!", state="complete", expanded=False)
        
        # Show final output
        if data:
            final_response = data.get("output", "I'm sorry, I couldn't process that.")
            st.markdown(final_response) 
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": final_response})