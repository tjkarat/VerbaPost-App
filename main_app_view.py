import streamlit as st
from streamlit_drawable_canvas import st_canvas
import os
from PIL import Image
from datetime import datetime

# Import core logic
import ai_engine
import database
import letter_format
import mailer
import zipcodes
import payment_engine

# --- CONFIGURATION ---
MAX_BYTES_THRESHOLD = 35 * 1024 * 1024 

# --- PRICING ---
COST_STANDARD = 2.99
COST_HEIRLOOM = 5.99
COST_CIVIC = 6.99
COST_OVERAGE = 1.00

def validate_zip(zipcode, state):
    if not zipcodes.is_real(zipcode): return False, "Invalid Zip Code"
    details = zipcodes.matching(zipcode)
    if details and details[0]['state'] != state.upper():
         return False, f"Zip is in {details[0]['state']}, not {state}"
    return True, "Valid"

def reset_app():
    st.session_state.audio_path = None
    st.session_state.transcribed_text = ""
    st.session_state.app_mode = "recording"
    st.session_state.overage_agreed = False
    st.session_state.payment_complete = False
    st.rerun()

def show_main_app():
    # --- INIT STATE ---
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "recording"
    if "audio_path" not in st.session_state:
        st.session_state.audio_path = None
    if "transcribed_text" not in st.session_state:
        st.session_state.transcribed_text = ""
    if "overage_agreed" not in st.session_state:
        st.session_state.overage_agreed = False
    if "payment_complete" not in st.session_state:
        st.session_state.payment_complete = False
    
    # --- 1. ADDRESSING ---
    st.subheader("1. Addressing")
    col_to, col_from = st.tabs(["👉 Recipient", "👈 Sender"])

    with col_to:
        to_name = st.text_input("Recipient Name", placeholder="John Doe")
        to_street = st.text_input("Street Address", placeholder="123 Main St")
        c1, c2 = st.columns(2)
        to_city = c1.text_input("City", placeholder="Mt Juliet")
        to_state = c2.text_input("State", max_chars=2, placeholder="TN")
        to_zip = c2.text_input("Zip", max_chars=5, placeholder="37122")

    with col_from:
        from_name = st.text_input("Your Name")
        from_street = st.text_input("Your Street")
        from_city = st.text_input("Your City")
        c3, c4 = st.columns(2)
        from_state = c3.text_input("Your State", max_chars=2)
        from_zip = c4.text_input("Your Zip", max_chars=5)

    if not (to_name and to_street and to_city and to_state and to_zip):
        st.info("👇 Fill out the **Recipient** tab to unlock the tools.")
        return

    # --- 2. SETTINGS & SIGNATURE ---
    st.divider()
    c_set, c_sig = st.columns(2)
    with c_set:
        st.subheader("Settings")
        service_tier = st.radio("Service Level:", 
            [
                f"⚡ Standard (${COST_STANDARD})", 
                f"🏺 Heirloom (${COST_HEIRLOOM})", 
                f"🏛️ Civic (${COST_CIVIC})"
            ]
        )
        is_heirloom = "Heirloom" in service_tier
        is_civic = "Civic" in service_tier

    with c_sig:
        st.subheader("Sign")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2, stroke_color="#000", background_color="#fff",
            height=100, width=200, drawing_mode="freedraw", key="sig"
        )

    # ==================================================
    #  STATE 1: RECORDING
    # ==================================================
    if st.session_state.app_mode == "recording":
        st.divider()
        st.subheader("🎙️ Dictate")
        st.warning(f"⏱️ **Time Limit:** 3 Minutes (+${COST_OVERAGE} fee for overage).")

        audio_value = st.audio_input("Record your letter")

        if audio_value:
            with st.status("⚙️ Processing Audio...", expanded=True) as status:
                path = "temp_browser_recording.wav"
                with open(path, "wb") as f:
                    f.write(audio_value.getvalue())
                st.session_state.audio_path = path
                
                file_size = audio_value.getbuffer().nbytes
                if file_size > MAX_BYTES_THRESHOLD:
                    status.update(label="⚠️ Recording too long!", state="error")
                    st.error("Recording exceeds 3 minutes.")
                    if st.button(f"💳 Agree to +${COST_OVERAGE} Charge"):
                        st.session_state.overage_agreed = True
                        st.session_state.app_mode = "transcribing"
                        st.rerun()
                    if st.button("🗑️ Delete & Retry"):
                        reset_app()
                    st.stop()
                else:
                    status.update(label="✅ Uploaded! Starting Transcription...", state="complete")
                    st.session_state.app_mode = "transcribing"
                    st.rerun()

    # ==================================================
    #  STATE 1.5: TRANSCRIBING
    # ==================================================
    elif st.session_state.app_mode == "transcribing":
        with st.spinner("🧠 AI is writing your letter..."):
            try:
                text = ai_engine.transcribe_audio(st.session_state.audio_path)
                st.session_state.transcribed_text = text
                st.session_state.app_mode = "editing"
                st.rerun()
            except Exception as e:
                st.error(f"Transcription Error: {e}")
                if st.button("Try Again"): reset_app()

    # ==================================================
    #  STATE 2: EDITING
    # ==================================================
    elif st.session_state.app_mode == "editing":
        st.divider()
        st.subheader("📝 Review")
        
        st.audio(st.session_state.audio_path)
        if st.session_state.overage_agreed:
            st.caption(f"💲 Overage Fee Applied: +${COST_OVERAGE}")

        edited_text = st.text_area("Edit Text:", value=st.session_state.transcribed_text, height=300)
        
        c_ai, c_reset = st.columns([1, 3])
        with c_ai:
            if st.button("✨ AI Polish"):
                polished = ai_engine.polish_text(edited_text)