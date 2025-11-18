import streamlit as st
from audio_recorder_streamlit import audio_recorder
from streamlit_drawable_canvas import st_canvas
import ai_engine
import database
import letter_format
import mailer
import os
from PIL import Image

# --- ROBUST IMPORT ---
try:
    import recorder
    local_rec_available = True
except ImportError:
    local_rec_available = False

st.set_page_config(page_title="VerbaPost", page_icon="📮")

if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

st.title("VerbaPost 📮")
st.markdown("**The Authenticity Engine.**")

# --- 1. SERVICE TIER ---
st.subheader("1. Choose Your Service")
service_tier = st.radio("Select Style:", 
    ["⚡ Standard ($2.50)", "🏺 Heirloom ($5.00)"], 
    captions=["API Fulfillment, Window Envelope", "Hand-stamped, Premium Paper, Handwritten Envelope"]
)

# --- 2. ADDRESS ---
st.divider()
st.subheader("2. Recipient")
col1, col2 = st.columns(2)
with col1:
    recipient_name = st.text_input("Name", placeholder="John Doe")
    street = st.text_input("Street", placeholder="123 Main St")
with col2:
    city = st.text_input("City", placeholder="Mt Juliet")
    state_zip = st.text_input("State/Zip", placeholder="TN 37122")

if not recipient_name or not street or not city or not state_zip:
    st.info("👇 **Please fill out the full address above to unlock the recorder.**")
    st.stop()

# --- 3. SIGNATURE ---
st.divider()
st.subheader("3. Sign Your Letter")
st.markdown("Draw your signature below:")

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=2,
    stroke_color="#000000",
    background_color="#ffffff",
    height=150,
    width=400,
    drawing_mode="freedraw",
    key="signature",
)

# --- 4. RECORDING ---
st.divider()
st.subheader("4. Dictate Message")

if local_rec_available:
    recording_mode = st.radio("Mic Source:", ["🖥️ Local Mac (Dev)", "🌐 Browser (Cloud)"])
else:
    recording_mode = "🌐 Browser (Cloud)"

if recording_mode == "🖥️ Local Mac (Dev)":
    if st.button("🔴 Record (5s)"):
        with st.spinner("Recording..."):
            path = "temp_letter.wav"
            recorder.record_audio(filename=path, duration=5)
            st.session_state.audio_path = path
        st.success("Done.")
else:
    # --- UI IMPROVEMENT FOR BROWSER RECORDER ---
    
    # Create columns to center the big button
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown("""
        <div style="text-align: center; border: 2px dashed #ccc; padding: 10px; border-radius: 10px;">
            <h4>🎙️ Instructions</h4>
            <p>1. Tap the <b>Green Mic</b> to START.</p>
            <p>2. Tap the <b>Yellow Square</b> to STOP.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # BIGGER ICON (150px) and centered layout
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e8b62c", # Yellow for Stop
            neutral_color="#6aa36f",   # Green for Start
            icon_size="150px",         # <--- MASSIVE BUTTON
        )

    if audio_bytes:
        st.success("✅ Audio Captured! Scroll down to generate.")
        path = "temp_browser_recording.wav"
        with open(path, "wb") as f:
            f.write(audio_bytes)
        st.session_state.audio_path = path

# --- 5. GENERATE ---
if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
    st.divider()
    st.audio(st.session_state.audio_path)
    
    if st.button("📮 Generate & Mail Letter", type="primary", use_container_width=True):
        full_address = f"{recipient_name}\n{street}\n{city}, {state_zip}"
        
        with st.spinner("🧠 AI Transcribing & Rendering..."):
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

                pdf_path = letter_format.create_pdf(text_content, full_address, "final_letter.pdf")
                
                st.balloons()
                if "Heirloom" in service_tier:
                    st.success("💌 Order Queued (Heirloom Tier)")
                else:
                    st.success("🚀 Sent to API (Standard Tier)")
                    mailer.send_letter(pdf_path)

                with open(pdf_path, "rb") as pdf_file:
                    st.download_button("📄 Download Preview", pdf_file, "letter.pdf", use_container_width=True)