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

def validate_zip(zipcode, state):
    if not zipcodes.is_real(zipcode): return False, "Invalid Zip Code"
    details = zipcodes.matching(zipcode)
    if details and details[0]['state'] != state.upper():
         return False, f"Zip is in {details[0]['state']}, not {state}"
    return True, "Valid"

def reset_app():
    # Full wipe
    keys = ["audio_path", "transcribed_text", "overage_agreed", "payment_complete", "stripe_url", "last_config", "processed_ids", "locked_tier"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]
    
    # Clear address keys too? Optional. Let's keep them for convenience.
    st.query_params.clear()
    st.rerun()

def show_main_app():
    # --- 0. AUTO-DETECT RETURN FROM STRIPE ---
    qp = st.query_params
    if "session_id" in qp:
        session_id = qp["session_id"]
        if session_id not in st.session_state.get("processed_ids", []):
            if payment_engine.check_payment_status(session_id):
                st.session_state.payment_complete = True
                if "processed_ids" not in st.session_state: st.session_state.processed_ids = []
                st.session_state.processed_ids.append(session_id)
                
                # Set mode
                st.session_state.app_mode = "recording"
                st.toast("✅ Payment Confirmed! Recorder Unlocked.")
            else:
                st.error("Payment verification failed.")
        
        # Restore Data
        keys_to_restore = ["to_name", "to_street", "to_city", "to_state", "to_zip", 
                           "from_name", "from_street", "from_city", "from_state", "from_zip", "locked_tier"]
        for key in keys_to_restore:
            if key in qp:
                st.session_state[key] = qp[key]
        
        st.query_params.clear() 

    # --- INIT STATE ---
    if "app_mode" not in st.session_state: st.session_state.app_mode = "recording"
    if "audio_path" not in st.session_state: st.session_state.audio_path = None
    if "payment_complete" not in st.session_state: st.session_state.payment_complete = False
    
    # --- SIDEBAR RESET ---
    with st.sidebar:
        st.subheader("Controls")
        if st.button("🔄 Start New Letter", type="primary", use_container_width=True):
            reset_app()
    
    # --- 1. ADDRESSING ---
    st.subheader("1. Addressing")
    col_to, col_from = st.tabs(["👉 Recipient", "👈 Sender"])

    def get_val(key): return st.session_state.get(key, "")

    with col_to:
        to_name = st.text_input("Recipient Name", value=get_val("to_name"), key="to_name")
        to_street = st.text_input("Street Address", value=get_val("to_street"), key="to_street")
        c1, c2 = st.columns(2)
        to_city = c1.text_input("City", value=get_val("to_city"), key="to_city")
        to_state = c2.text_input("State", value=get_val("to_state"), max_chars=2, key="to_state")
        to_zip = c2.text_input("Zip", value=get_val("to_zip"), max_chars=5, key="to_zip")

    with col_from:
        from_name = st.text_input("Your Name", value=get_val("from_name"), key="from_name")
        from_street = st.text_input("Your Street", value=get_val("from_street"), key="from_street")
        from_city = st.text_input("Your City", value=get_val("from_city"), key="from_city")
        c3, c4 = st.columns(2)
        from_state = c3.text_input("Your State", value=get_val("from_state"), max_chars=2, key="from_state")
        from_zip = c4.text_input("Your Zip", value=get_val("from_zip"), max_chars=5, key="from_zip")

    # --- 2. SETTINGS & SIGNATURE ---
    st.divider()
    c_set, c_sig = st.columns(2)
    
    with c_set:
        st.subheader("2. Service")
        
        # LOGIC: If paid, show fixed badge. If not paid, show selector.
        if st.session_state.payment_complete:
            # Retrieve what they bought
            locked_tier = st.session_state.get("locked_tier", "Standard")
            
            st.markdown(f"""
            <div style="background-color:#d4edda; padding:15px; border-radius:8px; border:1px solid #c3e6cb; color:#155724;">
                <strong>✅ Order Confirmed:</strong><br>
                {locked_tier}
            </div>
            """, unsafe_allow_html=True)
            
            # Set variable for downstream logic
            service_tier = locked_tier
            
        else:
            # Show Radio Buttons
            service_tier_raw = st.radio("Choose Tier:", 
                [f"⚡ Standard (${COST_STANDARD})", f"🏺 Heirloom (${COST_HEIRLOOM})", f"🏛️ Civic (${COST_CIVIC})"],
                key="tier_select"
            )
            service_tier = service_tier_raw # Store for logic
            st.session_state["locked_tier"] = service_tier_raw # Prepare to lock

    is_heirloom = "Heirloom" in service_tier
    is_civic = "Civic" in service_tier

    with c_sig:
        st.subheader("Sign")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000", background_color="#fff",
            height=150, width=300, drawing_mode="freedraw", key="sig"
        )

    # Validation Gates
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
        st.info(f"Total: **${final_price:.2f}**")
        
        # 1. Save Draft & URL Prep
        user_email = st.session_state.get("user_email", "guest@verbapost.com")
        
        if st.button("💳 Proceed to Secure Payment", type="primary", use_container_width=True):
            try:
                draft_id = database.save_draft(user_email, to_name, to_street, to_city, to_state, to_zip)
                
                if draft_id:
                    # Pass the locked tier in URL so we remember what they bought
                    return_url = f"{YOUR_APP_URL}?letter_id={draft_id}&locked_tier={urllib.parse.quote(service_tier)}"
                    
                    url, session_id = payment_engine.create_checkout_session(
                        f"VerbaPost {service_tier}", 
                        int(final_price * 100), 
                        return_url, 
                        YOUR_APP_URL
                    )
                    
                    if url:
                        st.markdown(f'''
                        <a href="{url}" target="_self" style="text-decoration:none;">
                            <div style="background-color:#FF4B4B;color:white;padding:12px 24px;text-align:center;border-radius:8px;font-weight:bold;">
                                👉 Click to Pay Now
                            </div>
                        </a>
                        ''', unsafe_allow_html=True)
                    else:
                        st.error("Payment Gateway Error.")
            except Exception as e:
                st.error(f"System Error: {e}")
        
        st.caption("Secure payment via Stripe.")
        st.stop()

    # --- 4. RECORDING (UNLOCKED) ---
    if st.session_state.app_mode == "recording":
        st.subheader("🎙️ 4. Dictate")
        
        # INSTRUCTIONS (The Fix)
        st.markdown("""
        <div style="background-color:#e8fdf5; padding:15px; border-radius:10px; border:1px solid #c3e6cb; margin-bottom:10px;">
            <h4 style="margin-top:0; color:#155724;">👇 How to Record</h4>
            <ol style="color:#155724; margin-bottom:0;">
                <li>Tap the <b>Microphone Icon</b> in the box below.</li>
                <li>Speak your letter clearly.</li>
                <li>Tap the <b>Red Square</b> to stop.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        audio_value = st.audio_input("Record your letter")

        if audio_value:
            with st.status("⚙️ Processing...", expanded=True):
                path = "temp.wav"
                with open(path, "wb") as f: f.write(audio_value.getvalue())
                st.session_state.audio_path = path
                st.session_state.app_mode = "transcribing"
                st.rerun()

    # ... (Rest of Transcribe/Edit/Finalize logic) ...
    # RE-INSERTING LOGIC TO ENSURE FILE IS COMPLETE
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

            if is_civic:
                 # CIVIC LOGIC
                 full_addr = f"{from_street}, {from_city}, {from_state} {from_zip}"
                 try: targets = civic_engine.get_reps(full_addr)
                 except: targets = []
                 if not targets: 
                     st.error("No Reps Found.")
                     st.stop()
                 
                 files = []
                 addr_from = {'name': from_name, 'street': from_street, 'city': from_city, 'state': from_state, 'zip': from_zip}
                 for t in targets:
                     t_addr = t['address_obj']
                     fname = f"Letter_to_{t['name'].replace(' ', '')}.pdf"
                     pdf = letter_format.create_pdf(st.session_state.transcribed_text, f"{t['name']}\n{t_addr['street']}", f"{from_name}\n{from_street}...", False, "English", fname, sig_path)
                     files.append(pdf)
                     # Add Lob Send here...
                 
                 zip_buffer = io.BytesIO()
                 with zipfile.ZipFile(zip_buffer, "w") as zf:
                     for f in files: zf.write(f, os.path.basename(f))
                 st.download_button("📦 Download All", zip_buffer.getvalue(), "Civic.zip")

            else:
                # STANDARD LOGIC
                full_to = f"{to_name}\n{to_street}\n{to_city}, {to_state} {to_zip}"
                full_from = f"{from_name}\n{from_street}\n{from_city}, {from_state} {from_zip}"
                pdf = letter_format.create_pdf(
                    st.session_state.transcribed_text, full_to, full_from, is_heirloom, "English", "final.pdf", sig_path
                )
                
                if not is_heirloom:
                    addr_to = {'name': to_name, 'street': to_street, 'city': to_city, 'state': to_state, 'zip': to_zip}
                    addr_from = {'name': from_name, 'street': from_street, 'city': from_city, 'state': from_state, 'zip': from_zip}
                    mailer.send_letter(pdf, addr_to, addr_from)
                
                with open(pdf, "rb") as f:
                    st.download_button("Download PDF", f, "letter.pdf")
            
            st.write("✅ Done!")
            
            if st.session_state.get("user"):
                try:
                    database.update_user_address(st.session_state.user.user.email, from_name, from_street, from_city, from_state, from_zip)
                except: pass

        st.success("Sent!")
        if st.button("Start New"): reset_app()