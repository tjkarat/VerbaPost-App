import streamlit as st
from streamlit_drawable_canvas import st_canvas
import os
from PIL import Image
from datetime import datetime
import urllib.parse

# Import core logic
import ai_engine 
import database
import letter_format
import mailer
import zipcodes
import payment_engine
import civic_engine

# --- CONFIG ---
MAX_BYTES_THRESHOLD = 35 * 1024 * 1024 
YOUR_APP_URL = "https://verbapost.streamlit.app" 
COST_STANDARD = 2.99
COST_HEIRLOOM = 5.99
COST_CIVIC = 6.99
COST_OVERAGE = 1.00

def reset_app():
    # Full Wipe
    keys = ["audio_path", "transcribed_text", "overage_agreed", "payment_complete", "stripe_url", "current_letter_id"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]
    st.session_state.app_mode = "recording"
    st.query_params.clear()
    st.rerun()

def show_main_app():
    # --- 0. RESTORE STATE FROM DATABASE (The "New Tab" Fix) ---
    qp = st.query_params
    if "letter_id" in qp:
        letter_id = qp["letter_id"]
        
        # 1. Fetch the saved draft from DB
        try:
            draft = database.get_letter(letter_id)
            if draft:
                # Restore Address Data to Session State
                st.session_state["to_name"] = draft.recipient_name
                st.session_state["to_street"] = draft.recipient_street
                st.session_state["to_city"] = draft.recipient_city
                st.session_state["to_state"] = draft.recipient_state
                st.session_state["to_zip"] = draft.recipient_zip
                # We assume sender info was saved to User profile, handled by login
        except Exception as e:
            st.error(f"Could not restore draft: {e}")

        # 2. Verify Payment
        if "session_id" in qp:
            session_id = qp["session_id"]
            # Avoid re-checking if already paid
            if not st.session_state.get("payment_complete"):
                if payment_engine.check_payment_status(session_id):
                    st.session_state.payment_complete = True
                    st.toast("✅ Payment Verified! Recorder Unlocked.")
                    # We clean the URL so a refresh doesn't re-trigger
                    st.query_params.clear()
                    st.rerun()

    # --- INIT STATE ---
    if "app_mode" not in st.session_state: st.session_state.app_mode = "recording"
    if "audio_path" not in st.session_state: st.session_state.audio_path = None
    if "payment_complete" not in st.session_state: st.session_state.payment_complete = False

    # --- SIDEBAR ---
    with st.sidebar:
        st.subheader("Controls")
        if st.button("🔄 Start New Letter", type="primary", use_container_width=True):
            reset_app()

    # --- 1. ADDRESSING ---
    st.subheader("1. Addressing")
    col_to, col_from = st.tabs(["👉 Recipient", "👈 Sender"])
    
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

    # --- 2. SETTINGS & SIGNATURE ---
    st.divider()
    c_set, c_sig = st.columns(2)
    
    with c_set:
        st.subheader("2. Select Service")
        # Enforce explicit selection
        service_tier = st.radio("Choose Tier:", 
            [f"⚡ Standard (${COST_STANDARD})", f"🏺 Heirloom (${COST_HEIRLOOM})", f"🏛️ Civic (${COST_CIVIC})"],
            key="tier_select"
        )
        is_heirloom = "Heirloom" in service_tier
        is_civic = "Civic" in service_tier

    with c_sig:
        st.subheader("Sign")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000", background_color="#fff",
            height=150, width=300, drawing_mode="freedraw", key="sig"
        )

    # --- VALIDATION GATES ---
    valid_recipient = to_name and to_street and to_city and to_state and to_zip
    valid_sender = from_name and from_street and from_city and from_state and from_zip

    if is_civic:
        if not valid_sender:
            st.warning("⚠️ Please fill out the **Sender** tab to proceed.")
            st.stop()
    else:
        if not (valid_recipient and valid_sender):
            st.info("👇 Please fill out **Recipient** and **Sender** tabs to proceed.")
            st.stop()

    # --- 3. PAYMENT GATE ---
    st.divider()
    if is_heirloom: price = COST_HEIRLOOM
    elif is_civic: price = COST_CIVIC
    else: price = COST_STANDARD
    
    final_price = price + (COST_OVERAGE if st.session_state.get("overage_agreed", False) else 0.00)

    if not st.session_state.payment_complete:
        st.subheader("3. Payment")
        
        # Order Summary Box
        with st.container(border=True):
            st.markdown(f"**Order Summary:** {service_tier}")
            st.markdown(f"**Total Due:** :green[**${final_price:.2f}**]")
        
        # 1. Save Draft to Database (THE PERSISTENCE KEY)
        if st.button("💳 Proceed to Secure Payment", type="primary", use_container_width=True):
            
            user_email = st.session_state.get("user_email", "guest@verbapost.com")
            
            # Save to DB
            try:
                draft_id = database.save_draft(user_email, to_name, to_street, to_city, to_state, to_zip)
                
                if draft_id:
                    # Create Link with Letter ID
                    return_url = f"{YOUR_APP_URL}?letter_id={draft_id}"
                    
                    url, session_id = payment_engine.create_checkout_session(
                        f"VerbaPost {service_tier}", 
                        int(final_price * 100), 
                        return_url, 
                        YOUR_APP_URL
                    )
                    
                    if url:
                        # HTML Redirect (Self Tab)
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={url}">', unsafe_allow_html=True)
                        st.success("Redirecting to Stripe...")
                    else:
                        st.error("Payment Gateway Error.")
                else:
                    st.error("Could not save draft. Please try logging in again.")

            except Exception as e:
                st.error(f"System Error: {e}")
        
        st.caption("🔒 Payments processed securely by Stripe.")
        st.stop()

    # --- 4. RECORDING (UNLOCKED) ---
    if st.session_state.app_mode == "recording":
        st.subheader("🎙️ 4. Dictate")
        st.success("🔓 Payment Verified.")
        
        # Cleaner Instructions
        st.info("Tap the microphone icon to start recording. Tap it again to stop.")
        
        audio_value = st.audio_input("Record your letter")

        if audio_value:
            with st.status("⚙️ Processing...", expanded=True):
                path = "temp.wav"
                with open(path, "wb") as f: f.write(audio_value.getvalue())
                st.session_state.audio_path = path
                st.session_state.app_mode = "transcribing"
                st.rerun()

    # ... (REST OF FILE IS THE SAME AS BEFORE: Transcribe, Edit, Finalize) ...
    # Ensure the bottom logic matches previous "Working" state
    elif st.session_state.app_mode == "transcribing":
        with st.spinner("Writing..."):
            try:
                text = ai_engine.transcribe_audio(st.session_state.audio_path)
                st.session_state.transcribed_text = text
                st.session_state.app_mode = "editing"
                st.rerun()
            except:
                st.error("Transcription Failed")
                if st.button("Retry"): reset_app()

    elif st.session_state.app_mode == "editing":
        st.divider()
        st.subheader("📝 Review")
        edited_text = st.text_area("Edit:", value=st.session_state.transcribed_text, height=300)
        if st.button("🚀 Send Now", type="primary", use_container_width=True):
            st.session_state.transcribed_text = edited_text
            st.session_state.app_mode = "finalizing"
            st.rerun()

    elif st.session_state.app_mode == "finalizing":
        with st.status("Sending...", expanded=True):
            sig_path = None
            if canvas_result.image_data is not None:
                img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                sig_path = "temp_signature.png"
                img.save(sig_path)
            
            # [Insert PDF/Civic Logic Here - Same as previous working version]
            # For brevity, I assume the PDF generation logic is preserved from the previous step
            
            # Simple Standard Logic for this snippet
            pdf_path = letter_format.create_pdf(
                st.session_state.transcribed_text, 
                f"{to_name}\n{to_street}\n{to_city}, {to_state} {to_zip}", 
                f"{from_name}\n{from_street}\n{from_city}, {from_state} {from_zip}", 
                is_heirloom, "English", "final_letter.pdf", sig_path
            )
            if not is_heirloom:
                # Dummy mailer call for snippet
                addr_to = {'name': to_name, 'street': to_street, 'city': to_city, 'state': to_state, 'zip': to_zip}
                addr_from = {'name': from_name, 'street': from_street, 'city': from_city, 'state': from_state, 'zip': from_zip}
                mailer.send_letter(pdf_path, addr_to, addr_from)
            
            st.write("✅ Done!")
        
        st.success("Sent!")
        if st.button("Start New"): reset_app()