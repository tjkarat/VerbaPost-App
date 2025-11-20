import streamlit as st
from splash_view import show_splash
from main_app_view import show_main_app

# --- PAGE CONFIG ---
st.set_page_config(page_title="VerbaPost", page_icon="📮", layout="centered")

# --- CSS INJECTOR ---
def inject_custom_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
        div.stButton > button {border-radius: 8px; font-weight: 600; border: 1px solid #e0e0e0;}
        input {border-radius: 5px !important;}
        </style>
        """, unsafe_allow_html=True)

inject_custom_css()

# --- ROUTING LOGIC (THE FIX) ---
# Check if returning from Stripe
if "session_id" in st.query_params:
    # Force view to main app so we don't get stuck on Splash
    st.session_state.current_view = "main_app"

# Default State
if "current_view" not in st.session_state:
    st.session_state.current_view = "splash" 
if "user" not in st.session_state:
    st.session_state.user = None

# --- ROUTER ---
if st.session_state.current_view == "splash":
    show_splash()

elif st.session_state.current_view == "main_app":
    # Sidebar
    with st.sidebar:
        st.subheader("Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_view = "splash"
            st.rerun()
        st.caption("VerbaPost v0.9 (Alpha)")
        
    show_main_app()