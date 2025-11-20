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
# UPDATE THIS TO YOUR EXACT APP URL
YOUR_APP_URL = "https://verbapost.streamlit.app" 

# --- PRICING ---
COST_STANDARD = 2.99
COST_HEIRLOOM = 5.99
COST_CIVIC = 6.99
COST_OVERAGE = 1.00

def reset_app():
    st.session_state.audio_path = None
    st.session_state.transcribed_text = ""
    st.session_state.app_mode = "recording"
    st.session_state.overage_agreed = False
    st.session_state.payment_complete = False
    # Clear URL params so we don't get stuck in a loop
    st.query_params.clear()
    if "stripe_url" in st.session_state:
        del st.session_state.stripe_url
    st.rerun()

def show_main_app():
    # --- 0. AUTO-DETECT RETURN FROM STRIPE ---
    if "session_id" in st.query_params:
        session_id = st.query_params["session_id"]
        if payment_engine.check_payment_status(session_id):
            st.session_state.payment_complete = True
            st.toast("✅ Payment Confirmed! Recorder Unlocked.")
            # We DO NOT clear query params immediately here to avoid a reload loop,
            # but we will rely on payment_complete state.
        else:
            st.error("Payment verification failed.")

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
    
    # --- SIDEBAR RESET ---
    with st.sidebar:
        st.subheader("Controls")
        if st.button("🔄 Start New Letter", type="primary", use_container_width=True):
            reset_app()

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
    if not (from_name and from_street and from_city and from_state and from_zip):
         st.warning("👇 Fill out the **Sender** tab.")
         return

    # --- 2. SETTINGS & SIGNATURE ---
    st.divider()
    c_set, c_sig = st.columns(2)
    with c_set:
        st.subheader("2. Settings")
        service_tier = st.radio("Service Level:", 
            [f"⚡ Standard (${COST_STANDARD})", f"🏺 Heirloom (${COST_HEIRLOOM})", f"🏛️ Civic (${COST_CIVIC})"]
        )
        is_heirloom = "Heirloom" in service_tier
        is_civic = "Civic" in service_tier
    with c_sig:
        st.subheader("3. Sign")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000", background_color="#fff",
            height=100, width=200, drawing_mode="freedraw", key="sig"
        )

    st.divider()
    
    # --- PRICE CALCULATION ---
    if is_heirloom: price = COST_HEIRLOOM
    elif is_civic: price = COST_CIVIC
    else: price = COST_STANDARD
    final_price = price + (COST_OVERAGE if st.session_state.overage_agreed else 0.00)

    # ==================================================
    #  PAYMENT GATE (One-Click Logic)
    # ==================================================
    if not st.session_state.payment_complete:
        st.subheader("4. Payment")
        st.info(f"Total: **${final_price:.2f}**")
        
        # GENERATE LINK AUTOMATICALLY IN BACKGROUND
        # We check if we already have a link for this exact price/tier to avoid re-generating on every pixel movement
        current_config = f"{service_tier}_{final_price}"
        if "last_config" not in st.session_state or st.session_state.last_config != current_config:
             url, session_id = payment_engine.create_checkout_session(
                product_name=f"VerbaPost {service_tier}",
                amount_in_cents=int(final_price * 100),
                success_url=YOUR_APP_URL, # Redirects back to app root
                cancel_url=YOUR_APP_URL
            )
             st.session_state.stripe_url = url
             st.session_state.stripe_session_id = session_id
             st.session_state.last_config = current_config
        
        if st.session_state.stripe_url:
            # SINGLE BUTTON: Takes user directly to Stripe
            st.link_button(f"💳 Pay ${final_price:.2f} & Unlock Recorder", st.session_state.stripe_url, type="primary")
            st.caption("Secure checkout via Stripe. You will be redirected back automatically.")
        else:
            st.error("Unable to connect to payment processor.")
            
        # Manual check button just in case auto-redirect fails on some browsers
        if st.button("🔄 I've already paid (Refresh Status)"):
            st.rerun()
            
        st.stop() 

    # ==================================================
    #  STATE 1: RECORDING (Unlocked)
    # ==================================================
    if st.session_state.app_mode == "recording":
        st.subheader("🎙️ 5. Dictate")
        st.success("🔓 Payment Verified.")
        
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
                        st.session_state.audio_path = None
                        st.rerun()
                    st.stop()
                else:
                    status.update(label="✅ Uploaded! Transcribing...", state="complete")
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
        edited_text = st.text_area("Edit Text:", value=st.session_state.transcribed_text, height=300)
        
        c1, c2 = st.columns([1, 3])
        if c1.button("✨ AI Polish"):
             st.session_state.transcribed_text = ai_engine.polish_text(edited_text)
             st.rerun()
        if c2.button("🗑️ Re-Record (Free)"):
             st.session_state.app_mode = "recording"
             st.rerun()

        st.markdown("---")
        if st.button("🚀 Approve & Send Now", type="primary", use_container_width=True):
            st.session_state.transcribed_text = edited_text
            st.session_state.app_mode = "finalizing"
            st.rerun()

    # ==================================================
    #  STATE 3: FINALIZING
    # ==================================================
    elif st.session_state.app_mode == "finalizing":
        st.divider()
        with st.status("✉️ Sending...", expanded=True):
            sig_path = None
            if canvas_result.image_data is not None:
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                sig_path = "temp_signature.png"
                img.save(sig_path)

            pdf_path = letter_format.create_pdf(
                st.session_state.transcribed_text, 
                f"{to_name}\n{to_street}\n{to_city}, {to_state} {to_zip}", 
                f"{from_name}\n{from_street}\n{from_city}, {from_state} {from_zip}" if from_name else "", 
                is_heirloom, 
                st.session_state.get("language", "English"),
                "final_letter.pdf", 
                sig_path
            )
            
            if not is_heirloom:
                addr_to = {'name': to_name, 'street': to_street, 'city': to_city, 'state': to_state, 'zip': to_zip}
                addr_from = {'name': from_name, 'street': from_street, 'city': from_city, 'state': from_state, 'zip': from_zip}
                mailer.send_letter(pdf_path, addr_to, addr_from)
            else:
                st.info("🏺 Added to Heirloom Queue")
            
            st.write("✅ Done!")

        st.balloons()
        st.success("Letter Sent!")
        
        safe_name = "".join(x for x in to_name if x.isalnum())
        unique_name = f"Letter_{safe_name}_{datetime.now().strftime('%H%M')}.pdf"

        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Copy", f, unique_name, "application/pdf", use_container_width=True)

        if st.button("Start New Letter"):
            reset_app()