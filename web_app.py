import streamlit as st
from audio_recorder_streamlit import audio_recorder
from streamlit_drawable_canvas import st_canvas
import ai_engine
import database
import letter_format
import mailer
import os
from PIL import Image
from datetime import datetime
from uszipcode import SearchEngine

# --- ROBUST IMPORT (The Fix) ---
# We wrap this in a try/except block. 
# If 'sounddevice' is missing (Cloud), we just disable local mode.
try:
    import recorder
    local_rec_available = True
except (ImportError, OSError):
    local_rec_available = False

# --- CONFIG & SETUP ---
st.set_page_config(page_title="VerbaPost", page_icon="📮")
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

# Validation Engine (Lightweight)
search = SearchEngine()

def validate_zip(city, state, zipcode):
    # Quick check: Is it 5 digits?
    if len(zipcode) != 5 or not zipcode.isdigit():
        return False, "Zip code must be 5 digits."
    
    # Database check
    result = search.by_zipcode(zipcode)
    if not result:
        return False, "Zip code does not exist."
    
    # State Match Check (Basic)
    if result.state and state.upper() not in result.state:
         return False, f"Zip {zipcode} belongs to {result.state}, not {state}."
         
    return True, "Valid"

# --- HEADER ---
st.title("VerbaPost 📮")
st.markdown("**The Authenticity Engine.**")

# --- 1. ADDRESS SECTION ---
st.subheader("1. Addressing")

col_to, col_from = st.tabs(["👉 To (Recipient)", "👈 From (Return Address)"])

with col_to:
    to_name = st.text_input("Recipient Name", placeholder="John Doe")
    to_street = st.text_input("Street Address", placeholder="123 Main St")
    c1, c2 = st.columns(2)
    to_city = c1.text_input("City", placeholder="Mt Juliet")
    to_state = c2.text_input("State (e.g. TN)", max_chars=2)
    to_zip = c2.text_input("Zip Code", max_chars=5)

with col_from:
    st.info("Required for the post office to return undelivered mail.")
    from_name = st.text_input("Your Name")
    from_street = st.text_input("Your Street")
    c3, c4 = st.columns(2)
    from_city = c3.text_input("Your City")
    from_state = c4.text_input("Your State", max_chars=2)
    from_zip = c4.text_input("Your Zip", max_chars=5)

# --- VALIDATION GATE ---
address_valid = False
if to_name and to_street and to_city and to_state and to_zip:
    is_valid, msg = validate_zip(to_city, to_state, to_zip)
    if is_valid:
        st.success("✅ Destination Address Verified")
        address_valid = True
    else:
        st.error(f"⚠️ Address Error: {msg}")
else:
    st.info("👇 Fill out the **Recipient** tab to unlock the recorder.")

if not address_valid:
    st.stop()

# --- 2. SERVICE TIER ---
st.divider()
service_tier = st.radio("Service Level:", ["⚡ Standard ($2.50)", "🏺 Heirloom ($5.00)"], horizontal=True)

# --- 3. SIGNATURE ---
st.divider()
st.write("Sign Below:")
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)", 
    stroke_width=2, stroke_color="#000", background_color="#fff",
    height=120, width=300, drawing_mode="freedraw", key="sig"
)

# --- 4. RECORDER (Optimized) ---
st.divider()
st.subheader("🎙️ Dictate")

# UI Layout
c_rec, c_inst = st.columns([1, 2])
with c_inst:
    st.caption("Tap the Mic. Speak. Tap again to Stop.")
    st.caption("⚠️ **Wait 2 seconds** after speaking before stopping.")

with c_rec:
    # Check availability
    if local_rec_available:
        # If local is available, user sees both options
        mode = st.toggle("Dev Mode (Local Mic)", value=False)
        if mode:
            if st.button("🔴 Record Local"):
                path = "temp_letter.wav"
                recorder.record_audio(filename=path, duration=5)
                st.session_state.audio_path = path
            audio_bytes = None
        else:
            audio_bytes = audio_recorder(text="", icon_size="80px", pause_threshold=2.0)
    else:
        # Cloud mode only
        audio_bytes = audio_recorder(text="", icon_size="80px", pause_threshold=2.0)

if audio_bytes:
    if len(audio_bytes) > 500: 
        path = "temp_browser_recording.wav"
        with open(path, "wb") as f:
            f.write(audio_bytes)
        st.session_state.audio_path = path
        st.success("Audio Captured!")

# --- 5. GENERATE ---
if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
    st.audio(st.session_state.audio_path)
    
    if st.button("📮 Generate Letter", type="primary", use_container_width=True):
        # Format Address Blocks
        full_recipient = f"{to_name}\n{to_street}\n{to_city}, {to_state} {to_zip}"
        # (Logic to include Return Address in PDF would go here in Day 3)
        
        with st.spinner("Processing..."):
            try:
                text_content = ai_engine.transcribe_audio(st.session_state.audio_path)
            except Exception as e:
                st.error(f"AI Error: {e}")
                text_content = ""

            if text_content:
                sig_path = None
                if canvas_result.image_data is not None:
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    sig_path = "temp_signature.png"
                    img.save(sig_path)

                pdf_path = letter_format.create_pdf(text_content, full_recipient, "final_letter.pdf", sig_path)
                
                st.balloons()
                st.success("Letter Ready!")
                
                safe_name = "".join(x for x in to_name if x.isalnum())
                unique_name = f"Letter_{safe_name}_{datetime.now().strftime('%H%M')}.pdf"

                with open(pdf_path, "rb") as pdf_file:
                    st.download_button("📄 Download PDF", pdf_file, unique_name, "application/pdf", use_container_width=True)