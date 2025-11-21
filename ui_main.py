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

# --- CONFIGURATION ---
MAX_BYTES_THRESHOLD = 35 * 1024 * 1024 
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
    st.query_params.clear()
    st.rerun()

def show_main_app():
    # --- 0. RESUME STATE (THE MEMORY FIX) ---
    # If we are returning from Stripe, we will have a letter_id and session_id
    if "session_id" in st.query_params and "letter_id" in st.query_params:
        letter_id = st.query_params["letter_id"]
        session_id = st.query_params["session_id"]
        
        # Load the Draft Data from DB
        draft = database.get_letter(letter_id)
        if draft:
            # Restore the session state from the database draft
            st.session_state["to_name"] = draft.recipient_name
            st.session_state["to_street"] = draft.recipient_street
            st.session_state["to_city"] = draft.recipient_city
            st.session_state["to_state"] = draft.recipient_state
            st.session_state["to_zip"] = draft.recipient_zip
            
            # Verify Payment
            if payment_engine.check_payment_status(session_id):
                st.session_state.payment_complete = True
                st.toast("✅ Payment Confirmed! Draft Loaded.")
                # Clean URL but stay on page
                st.query_params.clear()
            else:
                st.error("Payment verification failed.")

    # --- INIT STATE ---
    if "app_mode" not in st.session_state: st.session_state.app_mode = "recording"
    if "payment_complete" not in st.session_state: st.session_state.payment_complete = False

    # --- SIDEBAR ---
    with st.sidebar:
        if st.button("🔄 Start New Letter", type="primary"): reset_app()

    # --- 1. ADDRESSING ---
    st.subheader("1. Addressing")
    col_to, col_from = st.tabs(["👉 Recipient", "👈 Sender"])
    
    # Helper to grab session state safely
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

    if not (to_name and to_street and to_city and to_state and to_zip):
        st.info("👇 Fill out Recipient to continue.")
        return

    # --- 2. SETTINGS & SIGNATURE ---
    st.divider()
    c_set, c_sig = st.columns(2)
    with c_set:
        st.subheader("2. Settings")
        service_tier = st.radio("Service Level:", 
            [f"⚡ Standard (${COST_STANDARD})", f"🏺 Heirloom (${COST_HEIRLOOM})", f"🏛️ Civic (${COST_CIVIC})"],
            key="tier_select"
        )
        is_heirloom = "Heirloom" in service_tier
        is_civic = "Civic" in service_tier
    with c_sig:
        st.subheader("3. Sign")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000", background_color="#fff",
            height=100, width=200, drawing_mode="freedraw", key="sig"
        )

    # --- 3. PAYMENT GATE ---
    st.divider()
    if is_heirloom: price = COST_HEIRLOOM
    elif is_civic: price = COST_CIVIC
    else: price = COST_STANDARD
    
    if not st.session_state.payment_complete:
        st.subheader("4. Payment")
        st.info(f"Total: **${price}**")
        
        # 1. SAVE DRAFT TO DB (This persists the address!)
        if st.button(f"💾 Save & Pay ${price}"):
            user_email = st.session_state.get("user_email", "guest@verbapost.com")
            
            # Save Draft to DB
            draft_id = database.save_draft(user_email, to_name, to_street, to_city, to_state, to_zip)
            
            if draft_id:
                # 2. Generate Link with Draft ID
                # We append letter_id so we know which draft to load on return
                return_link = f"{YOUR_APP_URL}?letter_id={draft_id}"
                
                url, session_id = payment_engine.create_checkout_session(
                    f"VerbaPost {service_tier}", 
                    int(price * 100), 
                    return_link, # Success URL
                    YOUR_APP_URL
                )
                
                if url:
                    # 3. Force Same-Tab Redirect using HTML
                    # target="_self" forces it to stay in the same window
                    st.markdown(f'''
                        <a href="{url}" target="_self">
                            <button style="
                                background-color:#FF4B4B; 
                                color:white; 
                                border:none; 
                                padding:10px 20px; 
                                border-radius:5px; 
                                font-size:16px; 
                                cursor:pointer;">
                                👉 Click to Pay Now (Secure)
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
                else:
                    st.error("Payment Error.")
            else:
                st.error("Could not save draft. Are you logged in?")
        
        st.stop()

    # --- 4. RECORDING (UNLOCKED) ---
    if st.session_state.app_mode == "recording":
        st.subheader("🎙️ 5. Dictate")
        st.success("🔓 Payment Verified.")
        audio_value = st.audio_input("Record your letter")
        
        if audio_value:
            with st.status("⚙️ Processing...", expanded=True):
                path = "temp.wav"
                with open(path, "wb") as f: f.write(audio_value.getvalue())
                st.session_state.audio_path = path
                st.session_state.app_mode = "transcribing"
                st.rerun()
                
    # ... (Rest of the transcription/editing/finalizing logic remains the same) ...
    elif st.session_state.app_mode == "transcribing":
        with st.spinner("Writing..."):
            text = ai_engine.transcribe_audio(st.session_state.audio_path)
            st.session_state.transcribed_text = text
            st.session_state.app_mode = "editing"
            st.rerun()

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

            # PDF GEN & MAIL
            pdf_path = letter_format.create_pdf(
                st.session_state.transcribed_text, 
                f"{to_name}\n{to_street}\n{to_city}, {to_state} {to_zip}", 
                f"{from_name}\n{from_street}\n{from_city}, {from_state} {from_zip}" if from_name else "", 
                is_heirloom, 
                "English",
                "final_letter.pdf", 
                sig_path
            )
            
            if not is_heirloom:
                addr_to = {'name': to_name, 'street': to_street, 'city': to_city, 'state': to_state, 'zip': to_zip}
                addr_from = {'name': from_name, 'street': from_street, 'city': from_city, 'state': from_state, 'zip': from_zip}
                mailer.send_letter(pdf_path, addr_to, addr_from)
            
            st.write("✅ Done!")
        
        st.success("Sent!")
        if st.button("Start New"): reset_app()