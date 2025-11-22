import streamlit as st
from streamlit_drawable_canvas import st_canvas
import os
from PIL import Image
from datetime import datetime
import urllib.parse
import io
import zipfile

# Import core logic
import ai_engine 
import database
import letter_format
import mailer
import zipcodes
import payment_engine
import civic_engine

# --- CONFIG ---
YOUR_APP_URL = "https://verbapost.streamlit.app" 
COST_STANDARD = 2.99
COST_HEIRLOOM = 5.99
COST_CIVIC = 6.99
COST_OVERAGE = 1.00

def reset_app():
    # Clear session but keep login
    keys = ["audio_path", "transcribed_text", "overage_agreed", "payment_complete", "stripe_url", "processed_ids", "locked_tier"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]
    
    # Clear address fields from session
    addr_keys = ["to_name", "to_street", "to_city", "to_state", "to_zip", "from_name", "from_street", "from_city", "from_state", "from_zip"]
    for k in addr_keys:
        if k in st.session_state: del st.session_state[k]
        
    st.query_params.clear()
    st.rerun()

def show_main_app():
    # --- 0. URL HYDRATION (Runs First) ---
    qp = st.query_params
    if "session_id" in qp:
        session_id = qp["session_id"]
        # Verify Payment if not already done
        if session_id not in st.session_state.get("processed_ids", []):
            if payment_engine.check_payment_status(session_id):
                st.session_state.payment_complete = True
                if "processed_ids" not in st.session_state: st.session_state.processed_ids = []
                st.session_state.processed_ids.append(session_id)
                st.toast("✅ Payment Verified! Welcome back.")
            
            # Restore Address from URL to Session State
            keys = ["to_name", "to_street", "to_city", "to_state", "to_zip", 
                    "from_name", "from_street", "from_city", "from_state", "from_zip"]
            for k in keys:
                if k in qp: st.session_state[k] = qp[k]
            
            # Restore Tier
            if "tier" in qp: st.session_state.locked_tier = qp["tier"]

            # Force Recording Mode
            st.session_state.app_mode = "recording"
            
            # Clear URL to look clean (but data is now in Session State)
            st.query_params.clear()

    # --- INIT DEFAULTS ---
    if "app_mode" not in st.session_state: st.session_state.app_mode = "recording"
    if "payment_complete" not in st.session_state: st.session_state.payment_complete = False

    # --- SIDEBAR ---
    with st.sidebar:
        st.subheader("Controls")
        if st.button("🔄 Start New Letter", type="primary"): reset_app()

    # ==========================================
    #  SECTION 1: INPUTS (ALWAYS RENDERED)
    # ==========================================
    st.subheader("1. Addressing")
    col_to, col_from = st.tabs(["👉 Recipient", "👈 Sender"])

    # Data Binding: Priority is Session State -> Empty
    def get(k): return st.session_state.get(k, "")

    with col_to:
        to_name = st.text_input("Recipient Name", value=get("to_name"), key="to_name")
        to_street = st.text_input("Street Address", value=get("to_street"), key="to_street")
        c1, c2 = st.columns(2)
        to_city = c1.text_input("City", value=get("to_city"), key="to_city")
        to_state = c2.text_input("State", value=get("to_state"), max_chars=2, key="to_state")
        to_zip = c2.text_input("Zip", value=get("to_zip"), max_chars=5, key="to_zip")

    with col_from:
        from_name = st.text_input("Your Name", value=get("from_name"), key="from_name")
        from_street = st.text_input("Your Street", value=get("from_street"), key="from_street")
        from_city = st.text_input("Your City", value=get("from_city"), key="from_city")
        c3, c4 = st.columns(2)
        from_state = c3.text_input("Your State", value=get("from_state"), max_chars=2, key="from_state")
        from_zip = c4.text_input("Your Zip", value=get("from_zip"), max_chars=5, key="from_zip")

    # Service Tier Logic
    if st.session_state.payment_complete:
        service_tier = st.session_state.get("locked_tier", "Standard")
        st.success(f"✅ Order Active: **{service_tier}**")
    else:
        st.divider()
        st.subheader("2. Service")
        service_tier = st.radio("Choose Tier:", 
            [f"⚡ Standard (${COST_STANDARD})", f"🏺 Heirloom (${COST_HEIRLOOM})", f"🏛️ Civic (${COST_CIVIC})"],
            key="tier_select"
        )

    is_heirloom = "Heirloom" in service_tier
    is_civic = "Civic" in service_tier

    # Validation Check
    valid_sender = from_name and from_street and from_city and from_state and from_zip
    valid_recipient = to_name and to_street and to_city and to_state and to_zip

    if is_civic:
        if not valid_sender:
            st.warning("⚠️ Please fill