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
MAX_BYTES_THRESHOLD = 35 * 1024 * 1024 
YOUR_APP_URL = "https://verbapost.streamlit.app" 
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
    # Wipe session but keep login info
    keys = ["audio_path", "transcribed_text", "overage_agreed", "payment_complete", "stripe_url", "last_config", "processed_ids", "locked_tier", "sig_data"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]
    
    # Clear address keys
    addr_keys = ["to_name", "to_street", "to_city", "to_state", "to_zip", "from_name", "from_street", "from_city", "from_state", "from_zip"]
    for k in addr_keys:
        if k in st.session_state: del st.session_state[k]
        
    st.query_params.clear()
    st.rerun()

def show_main_app():
    # --- 0. SAFETY CHECK: INITIALIZE SESSION STATE ---
    defaults = {
        "app_mode": "store",
        "audio_path": None,
        "transcribed_text": "", # <--- CRITICAL: Must exist
        "overage_agreed": False,
        "payment_complete": False,
        "processed_ids": [],
        "stripe_url": None,
        "locked_tier": "Standard",
        "sig_data": None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # --- 1. AUTO-DETECT RETURN FROM STRIPE ---
    qp = st.query_params
    if "session_id" in qp:
        session_id = qp["session_id"]
        if session_id not in st.session_state.processed_ids:
            if payment_engine.check_payment_status(session_id):
                st.session_state.payment_complete = True
                st.session_state.processed_ids.append(session_id)
                st.session_state.app_mode = "workspace"
                
                if "tier" in qp: st.session_state.locked_tier = qp["tier"]
                
                st.toast("✅ Payment Verified! Welcome back.")
            else:
                st.error("Payment verification failed.")
        
        # Restore Address Data
        keys_to_restore = ["to_name", "to_street", "to_city", "to_state", "to_zip", 
                           "from_name", "from_street", "from_city", "from_state", "from_zip"]
        for key in keys_to_restore:
            if key in qp: st.session_state[key] = qp[key]
            
        st.query_params.clear() 

    # --- SIDEBAR ---
    with st.sidebar:
        st.subheader("Controls")
        if st.button("🔄 Start New Letter", type="primary"):
            reset_app()

    # ==================================================
    #  PHASE 1: THE STORE
    # ==================================================
    if st.session_state.app_mode == "store":
        st.header("1. Select Service")
        
        service_tier = st.radio("Choose your letter type:", 
            [f"⚡ Standard (${COST_STANDARD})", f"🏺 Heirloom (${COST_HEIRLOOM})", f"🏛️ Civic (${COST_CIVIC})"],
            index=0, key="tier_select"
        )
        
        if "Standard" in service_tier: price = COST_STANDARD; tier_name = "Standard"
        elif "Heirloom" in service_tier: price = COST_HEIRLOOM; tier_name = "Heirloom"
        elif "Civic" in service_tier: price = COST_CIVIC; tier_name = "Civic"
        
        st.info(f"**Total: ${price}**")
        
        # PAYMENT GENERATION
        current_config = f"{service_tier}_{price}"
        if "stripe_url" not in st.session_state or st.session_state.get("last_config") != current_config:
             success_link = f"{YOUR_APP_URL}?tier={tier_name}"
             url, session_id = payment_engine.create_checkout_session(
                f"VerbaPost {service_tier}", int(price * 100), success_link, YOUR_APP_URL
            )
             st.session_state.stripe_url = url
             st.session_state.stripe_session_id = session_id
             st.session_state.last_config = current_config
             
        if st.session_state.stripe_url:
            st.link_button(f"💳 Pay ${price} & Start Writing", st.session_state.stripe_url, type="primary")
            st.caption("Secure checkout via Stripe. A new tab will open.")
        else:
            st.error("System Error: Payment link could not be generated.")

    # ==================================================
    #  PHASE 2: THE WORKSPACE
    # ==================================================
    elif st.session_state.app_mode == "workspace":
        locked_tier = st.session_state.get("locked_tier", "Standard")
        is_civic = "Civic" in locked_tier
        is_heirloom = "Heirloom" in locked_tier

        st.success(f"🔓 **{locked_tier}** Unlocked. Ready to write.")

        # --- ADDRESSING ---
        st.subheader("2. Addressing")
        col_to, col_from = st.tabs(["👉 Recipient", "👈 Sender"])

        def get_val(key): return st.session_state.get(key, "")

        with col_to:
            if is_civic:
                st.info("🏛️ Auto-Detecting Representatives...")
                to_name, to_street, to_city, to_state, to_zip = "Civic", "Civic", "Civic", "TN", "00000"
            else:
                to_name = st.text_input("Recipient Name", value=get_val("to_name"))
                to_street = st.text_input("Street Address", value=get_val("to_street"))
                c1, c2 = st.columns(2)
                to_city = c1.text_input("City", value=get_val("to_city"))
                to_state = c2.text_input("State", value=get_val("to_state"))
                to_zip = c2.text_input("Zip", value=get_val("to_zip"))

        with col_from:
            from_name = st.text_input("Your Name", value=get_val("from_name"))
            from_street = st.text_input("Your Street", value=get_val("from_street"))
            from_city = st.text_input("Your City", value=get_val("from_city"))
            c3, c4 = st.columns(2)
            from_state = c3.text_input("Your State", value=get_val("from_state"))
            from_zip = c4.text_input("Your Zip", value=get_val("from_zip"))

        # Save to Session
        st.session_state.to_name = to_name
        st.session_state.to_street = to_street
        st.session_state.to_city = to_city
        st.session_state.to_state = to_state
        st.session_state.to_zip = to_zip
        st.session_state.from_name = from_name
        st.session_state.from_street = from_street
        st.session_state.from_city = from_city
        st.session_state.from_state = from_state
        st.session_state.from_zip = from_zip

        # --- SIGNATURE ---
        st.divider()
        st.subheader("3. Sign")
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)", stroke_width=2, stroke_color="#000", background_color="#fff",
            height=200, width=350, drawing_mode="freedraw", key="sig"
        )
        if canvas_result.image_data is not None:
            st.session_state.sig_data = canvas_result.image_data

        # --- RECORDER ---
        st.divider()
        st.subheader("4. Dictate")
        
        # INSTRUCTIONS RESTORED
        st.markdown("""
        <div style="background-color:#e8fdf5; padding:15px; border-radius:10px; border:1px solid #c3e6cb; margin-bottom:10px;">
            <h4 style="margin-top:0; color:#155724;">👇 How to Record</h4>
            <ol style="color:#155724; margin-bottom:0;">
                <li>Tap the <b>Microphone Icon</b> below.</li>
                <li>Speak your letter clearly.</li>
                <li>Tap the <b>Red Square</b> to stop.</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        audio_value = st.audio_input("Record your letter")
        
        # Gate
        valid_sender = from_name and from_street and from_city and from_state and from_zip
        valid_recipient = to_name and to_street and to_city and to_state and to_zip
        
        if is_civic and not valid_sender:
            st.warning("⚠️ Please complete **Sender** address.")
            st.stop()
        if not is_civic and not (valid_recipient and valid_sender):
            st.warning("⚠️ Please complete **Both Addresses**.")
            st.stop()

        if audio_value:
            with st.status("⚙️ Processing...", expanded=True):
                path = "temp.wav"
                with open(path, "wb") as f: f.write(audio_value.getvalue())
                st.session_state.audio_path = path
                try:
                    text = ai_engine.transcribe_audio(path)
                    st.session_state.transcribed_text = text
                    st.session_state.app_mode = "review"
                    st.rerun()
                except Exception as e:
                    st.error(f"Transcription Error: {e}")

    # ==================================================
    #  PHASE 3: REVIEW & SEND
    # ==================================================
    elif st.session_state.app_mode == "review":
        
        # SAFETY CATCH: If somehow text is missing, go back
        if not st.session_state.get("transcribed_text"):
            st.warning("No audio text found. Please record again.")
            if st.button("Back to Recorder"):
                st.session_state.app_mode = "workspace"
                st.rerun()
            st.stop()
            
        st.header("5. Review")
        
        edited_text = st.text_area("Edit your letter:", value=st.session_state.transcribed_text, height=300)
        
        if st.button("🚀 Finalize & Send", type="primary", use_container_width=True):
            st.session_state.transcribed_text = edited_text
            st.session_state.app_mode = "finalizing"
            st.rerun()

    # ==================================================
    #  PHASE 4: FINALIZE
    # ==================================================
    elif st.session_state.app_mode == "finalizing":
        # Load vars
        locked_tier = st.session_state.get("locked_tier", "Standard")
        is_civic = "Civic" in locked_tier
        is_heirloom = "Heirloom" in locked_tier
        
        to_n = st.session_state.get("to_name", "")
        to_s = st.session_state.get("to_street", "")
        to_c = st.session_state.get("to_city", "")
        to_st = st.session_state.get("to_state", "")
        to_z = st.session_state.get("to_zip", "")
        
        fr_n = st.session_state.get("from_name", "")
        fr_s = st.session_state.get("from_street", "")
        fr_c = st.session_state.get("from_city", "")
        fr_st = st.session_state.get("from_state", "")
        fr_z = st.session_state.get("from_zip", "")
        
        # Load Sig
        sig_path = None
        if st.session_state.get("sig_data") is not None:
            try:
                img = Image.fromarray(st.session_state.sig_data.astype('uint8'), 'RGBA')
                sig_path = "temp_signature.png"
                img.save(sig_path)
            except: pass

        with st.status("Sending...", expanded=True):
            if is_civic:
                full_addr = f"{fr_s}, {fr_c}, {fr_st} {fr_z}"
                try: targets = civic_engine.get_reps(full_addr)
                except: targets = []
                
                if not targets:
                    st.error("No Reps found.")
                    st.stop()
                
                files = []
                addr_from = {'name': fr_n, 'street': fr_s, 'city': fr_c, 'state': fr_st, 'zip': fr_z}
                for t in targets:
                    t_addr = t['address_obj']
                    pdf = letter_format.create_pdf(st.session_state.transcribed_text, f"{t['name']}\n{t_addr['street']}", f"{fr_n}\n{fr_s}...", False, "English", f"{t['name']}.pdf", sig_path)
                    files.append(pdf)
                    t_lob = {'name': t['name'], 'street': t_addr['street'], 'city': t_addr['city'], 'state': t_addr['state'], 'zip': t_addr['zip']}
                    mailer.send_letter(pdf, t_lob, addr_from)
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for f in files: zf.write(f, os.path.basename(f))
                st.download_button("📦 Download All", zip_buffer.getvalue(), "Civic.zip")
            
            else:
                # Standard
                pdf = letter_format.create_pdf(
                    st.session_state.transcribed_text, 
                    f"{to_n}\n{to_s}\n{to_c}, {to_st} {to_z}", 
                    f"{fr_n}\n{fr_s}\n{fr_c}, {fr_st} {fr_z}", 
                    is_heirloom, "English", "final.pdf", sig_path
                )
                
                if not is_heirloom:
                     addr_to = {'name': to_n, 'street': to_s, 'city': to_c, 'state': to_st, 'zip': to_z}
                     addr_from = {'name': fr_n, 'street': fr_s, 'city': fr_c, 'state': fr_st, 'zip': fr_z}
                     mailer.send_letter(pdf, addr_to, addr_from)
                else:
                     # Queue
                     u_email = st.session_state.get("user_email", "guest")
                     database.save_draft(u_email, to_n, to_s, to_c, to_st, to_z)

                with open(pdf, "rb") as f:
                    st.download_button("Download Copy", f, "letter.pdf")

            st.write("✅ Done!")
            st.success("Sent!")
            
            if st.session_state.get("user"):
                 database.update_user_address(st.session_state.user.user.email, fr_n, fr_s, fr_c, fr_st, fr_z)

        if st.button("Start New"): reset_app()