import streamlit as st
from st_audiorec import st_audiorec
import ai_engine
import database
import letter_format
import mailer
import recorder
import os

st.set_page_config(page_title="VerbaPost", page_icon="📮")

# --- INIT SESSION STATE (The Memory) ---
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None

# --- HEADER ---
st.title("VerbaPost 📮")
st.markdown("**Turn your voice into a mailed letter.**")

# --- ADDRESS INPUT ---
with st.container():
    st.subheader("📍 Recipient Details")
    col1, col2 = st.columns(2)
    with col1:
        recipient_name = st.text_input("Recipient Name", placeholder="e.g. John Doe")
        street = st.text_input("Street Address", placeholder="e.g. 123 Main St")
    with col2:
        city = st.text_input("City", placeholder="e.g. Mt Juliet")
        state_zip = st.text_input("State & Zip Code", placeholder="e.g. TN 37122")

# --- RECORDING SECTION ---
st.divider()
st.subheader("🎙️ Dictate Message")

# Mode Selection
recording_mode = st.radio("Microphone Source:", 
                          ["🖥️ Local Mac Microphone (Dev Mode)", "🌐 Browser Microphone (Deploy Mode)"])

if recording_mode == "🖥️ Local Mac Microphone (Dev Mode)":
    st.info("Uses your Mac's hardware. Reliable.")
    if st.button("🔴 Record (5 Seconds)"):
        with st.spinner("Recording... Speak Now!"):
            path = "temp_letter.wav"
            recorder.record_audio(filename=path, duration=5)
            # SAVE TO MEMORY
            st.session_state.audio_path = path
        st.success("Recording Complete! Click Generate below.")

else:
    # Browser Mode
    st.info("Uses the Browser. Required for Cloud.")
    wav_audio_data = st_audiorec()
    if wav_audio_data is not None and len(wav_audio_data) > 1000:
        path = "temp_browser_recording.wav"
        with open(path, "wb") as f:
            f.write(wav_audio_data)
        # SAVE TO MEMORY
        st.session_state.audio_path = path

# --- GENERATE SECTION ---
# Check if we have audio in memory
if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
    st.audio(st.session_state.audio_path) # Playback
    
    if st.button("📮 Generate & Mail Letter", type="primary"):
        if not recipient_name or not street or not city or not state_zip:
            st.error("⚠️ Please fill in ALL address fields first.")
        else:
            full_address = f"{recipient_name}\n{street}\n{city}, {state_zip}"
            
            with st.spinner("🤖 AI is thinking..."):
                # 1. Transcribe
                try:
                    text_content = ai_engine.transcribe_audio(st.session_state.audio_path)
                except Exception as e:
                    st.error(f"AI Error: {e}")
                    text_content = ""

                if text_content:
                    # 2. Database
                    if not os.path.exists("verbapost.db"):
                        database.init_db()
                    database.create_letter(text_content)
                    
                    # 3. PDF
                    pdf_path = letter_format.create_pdf(text_content, full_address, "final_letter.pdf")
                    
                    # 4. Success
                    st.balloons()
                    st.success("Letter Generated!")
                    st.text_area("Message Preview:", value=text_content)
                    
                    # 5. Download
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_file,
                            file_name="VerbaPost_Letter.pdf",
                            mime="application/pdf"
                        )
                    
                    # 6. Mail
                    mailer.send_letter(pdf_path)