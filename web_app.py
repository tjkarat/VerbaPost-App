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
import zipcodes

# --- CONFIG ---
st.set_page_config(page_title="VerbaPost", page_icon="📮")

# --- CSS HACKS FOR MOBILE UI ---
# This forces the audio button to be huge and centered
st.markdown("""
<style>
    .stAudio {
        width: 100% !important;
    }
    /* Target the container holding the custom component */
    iframe {
        width: 100% !important;
        min-height: 200px !important; 
        display: block;
        margin: 0 auto;
    }
    /* Make the status box pop */
    .status-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #f0f2f6;
        text-align: center;
        margin-bottom: 10px;
        border: 2px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "recording"
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

# --- ADDRESS VALIDATION ---
def validate_zip(zipcode, state):
    if not zipcodes.is_real(zipcode): return False, "Invalid Zip"
    details = zipcodes.matching(zipcode)
    if details and details[0]['state'] != state.upper():
         return False, f"Zip is in {details[0]['state']}"
    return True, "Valid"

# --- RESET ---
def reset_app():
    st.session_state.app_mode = "recording"
    st.session_state.audio_path = None
    st.rerun()

st.title("VerbaPost 📮")

# --- 1. ADDRESS SECTION ---
with st.expander("📍 Recipient & Sender Details", expanded=True):
    col_to, col_from = st.tabs(["👉 To (Recipient)", "👈 From (Return Address)"])
    
    with col_to:
        to_name = st.text_input("Recipient Name", placeholder="John Doe")
        to_street = st.text_input("Street Address", placeholder="123 Main St")
        c1, c2 = st.columns(2)
        to_city = c1.text_input("City", placeholder="Mt Juliet")
        to_state = c2.text_input("State", max_chars=2)
        to_zip = c2.text_input("Zip", max_chars=5)

    with col_from:
        from_name = st.text_input("Your Name")
        from_street = st.text_input("Your Street")
        c3, c4 = st.columns(2)
        from_city = c3.text_input("Your City")
        from_state = c4.text_input("Your State", max_chars=2)
        from_zip = c4.text_input("Your Zip", max_chars=5)

if not (to_name and to_street and to_city and to_state and to_zip):
    st.warning("Please fill out the Recipient Address to continue.")
    st.stop()

# --- 2. SIGNATURE ---
st.divider()
st.subheader("✍️ Signature")
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)", 
    stroke_width=2, stroke_color="#000", background_color="#fff",
    height=100, width=300, drawing_mode="freedraw", key="sig_canvas"
)

# --- 3. THE RECORDER (State Machine) ---
st.divider()
st.subheader("🎙️ Dictate")

if st.session_state.app_mode == "recording":
    # Visual Status Indicator
    st.markdown("""
    <div class="status-box">
        <h3>👇 TAP THE ICON BELOW 👇</h3>
        <p><b>Gray</b> = Ready<br>
        <b>Yellow</b> = Recording (Tap again to stop)</p>
    </div>
    """, unsafe_allow_html=True)

    # THE BIG BUTTON
    # key="recorder_component" prevents the double-click reset bug!
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e8b62c", # Yellow
        neutral_color="#b0b0b0",   # Gray (High contrast)
        icon_size="180px",         # Massive size
        pause_threshold=60.0,      # Don't auto-stop
        key="recorder_component"   # CRITICAL FIX
    )

    if audio_bytes and len(audio_bytes) > 2000:
        path = "temp_browser_recording.wav"
        with open(path, "wb") as f:
            f.write(audio_bytes)
        st.session_state.audio_path = path
        st.session_state.app_mode = "reviewing"
        st.rerun()

# === STATE: REVIEWING ===
elif st.session_state.app_mode == "reviewing":
    st.success("✅ Audio Captured!")
    st.audio(st.session_state.audio_path)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Redo", use_container_width=True):
            reset_app()
    with c2:
        if st.button("🚀 Generate Letter", type="primary", use_container_width=True):
            st.session_state.app_mode = "processing"
            st.rerun()

# === STATE: PROCESSING ===
elif st.session_state.app_mode == "processing":
    with st.status("✉️ Generating...", expanded=True):
        # 1. Transcribe
        st.write("🧠 Transcribing...")
        try:
            text_content = ai_engine.transcribe_audio(st.session_state.audio_path)
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
            
        # Check for silence/hallucinations
        if not text_content or "1 oz" in text_content or len(text_content) < 5:
            st.error("Audio was unclear. Please try again.")
            if st.button("Back"): reset_app()
            st.stop()

        # 2. PDF
        st.write("📄 Creating PDF...")
        full_recipient = f"{to_name}\n{to_street}\n{to_city}, {to_state} {to_zip}"
        full_return = f"{from_name}\n{from_street}\n{from_city}, {from_state} {from_zip}" if from_name else ""
        
        # Signature Image
        sig_path = "temp_signature.png"
        if canvas_result.image_data is not None:
            img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            img.save(sig_path)
        
        # Default to Standard tier for this logic (can add toggle back if needed)
        is_heirloom = False 
        
        pdf_path = letter_format.create_pdf(
            text_content, full_recipient, full_return, is_heirloom, "final_letter.pdf", sig_path
        )
        
        # 3. Mail
        st.write("🚀 Mailing...")
        mailer.send_letter(pdf_path)
        
        st.write("✅ Done!")

    # SUCCESS UI
    st.balloons()
    st.text_area("Message:", value=text_content)
    
    safe_name = "".join(x for x in to_name if x.isalnum())
    unique_name = f"Letter_{safe_name}_{datetime.now().strftime('%H%M')}.pdf"

    with open(pdf_path, "rb") as pdf_file:
        st.download_button("Download PDF", pdf_file, unique_name, "application/pdf", use_container_width=True)
    
    if st.button("New Letter"):
        reset_app()