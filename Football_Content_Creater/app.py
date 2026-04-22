import streamlit as st
import time
import json
import os

# IMPORT YOUR AGENTS
from agents.guardrail_bot import validate_topic
from agents.rules_bot import get_official_ruling
from agents.content_bot import create_social_post

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Football AI Reporter", 
    page_icon="⚽",
    layout="wide"
)

# 2. CUSTOM CSS (Styling)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        height: 3em;
        font-weight: bold;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E1E1E;
    }
    </style>
""", unsafe_allow_html=True)

# 3. HELPER: LOAD PERSONAS
def get_personas_data():
    """Reads the JSON file to populate the sidebar."""
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ ERROR: 'personas.json' not found. Please create it!")
        return {}

# 4. SIDEBAR (Configuration)
with st.sidebar:
    st.header("⚙️ Studio Config")
    
    # Load data
    personas_data = get_personas_data()
    
    if personas_data:
        st.subheader("🎭 Choose Personality")
        
        # Create a list of names for the dropdown 
        display_names = [p['name'] for p in personas_data.values()]
        selected_name = st.selectbox("Who is reporting?", display_names)
        
        # Find the internal key (e.g. "hype_man") based on the name selected
        # We need this key to send to the Content Bot
        selected_key = next(key for key, val in personas_data.items() if val['name'] == selected_name)
        selected_persona = personas_data[selected_key]
        
        st.divider()
        # Preview the persona
        st.markdown(f"### {selected_persona.get('icon', '🤖')} {selected_name}")
        st.info(f"_{selected_persona['instructions']}_")
    else:
        st.warning("No personas loaded.")
        selected_key = "default"

# 5. MAIN INTERFACE
st.title("📱 Football Content Creator")
st.markdown("### Contextual Rules Analysis")
st.caption("Architecture: Guardrail -> Rules (Google File API) -> Content (Persona)")

# Input Section
event_input = st.text_area(
    "Describe the match event:", 
    placeholder="e.g. The goalkeeper handled the ball outside the box to stop a counter-attack...",
    height=100
)

generate_btn = st.button("🚀 Consult VAR & Post")

# 6. ORCHESTRATION LOGIC
if generate_btn:
    if not event_input.strip():
        st.warning("Please describe an event first.")
        st.stop()

    # Create a status container
    with st.status("🤖 Orchestrating Agents...", expanded=True) as status:
        
        # --- PHASE 1: SECURITY (Guardrail) ---
        st.write("🛡️ **Guardrail Agent:** Verifying topic...")
        time.sleep(0.5) # Small delay for UX
        is_allowed, reason = validate_topic(event_input)
        
        if not is_allowed:
            status.update(label="❌ Blocked by Guardrail", state="error")
            st.error(f"⛔ ACCESS DENIED: {reason}")
            st.stop()
        
        st.write("✅ Topic Verified.")
        
        # --- PHASE 2: FACTS (Rules Bot) ---
        st.write("🔍 **Rules Agent:** Searching IFAB Laws (Google File API)...")
        official_ruling = get_official_ruling(event_input)
        st.write("✅ Rules Retrieved.")

        # --- PHASE 3: CREATIVITY (Content Bot) ---
        st.write(f"✍️ **Content Agent:** {selected_name} is drafting the tweet...")
        # 👇 We pass the selected_key ("hype_man") to the bot
        social_post = create_social_post(event_input, official_ruling, selected_key)
        
        status.update(label="✨ Workflow Complete!", state="complete", expanded=False)

    # 7. DISPLAY RESULTS
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📜 Official Ruling")
        st.markdown(f"""
        <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; border-left: 5px solid #6c757d; color:black;">
        {official_ruling.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader(f"🐦 Tweet ({selected_name})")
        st.markdown(f"""
        <div style="background-color:#1DA1F2; padding:15px; border-radius:10px; color:white;">
        <span style="font-size: 1.2em;">{social_post}</span>
        </div>
        """, unsafe_allow_html=True)