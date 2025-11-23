import os

# 1. LIST OF FILES TO DELETE
trash_files = [
    "voice_processor.py",
    "splash_view.py",
    "main_app_view.py",
    "repair_app.py",
    "temp.wav",
    "temp_signature.png",
    "temp_browser_recording.wav"
]

# 2. SECURITY PATCH: Update ui_admin.py to use Secrets
admin_code = """import streamlit as st
import database
import letter_format
import os
import pandas as pd

def show_admin():
    st.title("👮‍♂️ Admin Command")
    
    # SECURITY: Load from Secrets
    try:
        admin_email = st.secrets["admin"]["email"]
    except:
        st.error("❌ Admin Email not configured in Secrets.")
        st.stop()
    
    # 1. Security Gate
    if not st.session_state.get("user") or st.session_state.user_email != admin_email:
        st.error("⛔ Access Denied. Authorized Personnel Only.")
        if st.button("Back to Safety"):
            st.session_state.current_view = "splash"
            st.rerun()
        st.stop()

    # 2. Fetch Data
    try:
        queue = database.get_admin_queue()
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return

    # 3. Business Stats
    col1, col2, col3 = st.columns(3)
    
    pending_count = len(queue)
    estimated_value = pending_count * 5.99 
    
    col1.metric("Pending Orders", pending_count, delta_color="inverse")
    col2.metric("Queue Value", f"${estimated_value:.2f}")
    col3.button("🔄 Refresh Data", on_click=st.rerun)

    st.divider()
    st.subheader("🗂️ Fulfillment Queue")

    if not queue:
        st.success("🎉 All caught up! No pending orders.")
        st.balloons()
        return

    # 4. The Work List
    for l in queue:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            
            with c1:
                st.markdown(f"**To:** {l.recipient_name}")
                st.caption(f"📍 {l.recipient_street}, {l.recipient_city}, {l.recipient_state} {l.recipient_zip}")
                st.text(f"Message Preview: {l.content[:75]}...")
                st.caption(f"Ordered: {l.created_at.strftime('%b %d, %I:%M %p')}")

            with c2:
                # GENERATE PDF
                s_str = f"{l.author.address_name}\n{l.author.address_street}\n{l.author.address_city}, {l.author.address_state}" if l.author else "VerbaPost User"
                r_str = f"{l.recipient_name}\n{l.recipient_street}\n{l.recipient_city}, {l.recipient_state} {l.recipient_zip}"
                
                pdf_path = letter_format.create_pdf(
                    l.content, r_str, s_str, True, "English", f"order_{l.id}.pdf", None
                )
                
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "🖨️ Print PDF", 
                        data=f, 
                        file_name=f"VerbaPost_Order_{l.id}.pdf", 
                        mime="application/pdf",
                        key=f"dl_{l.id}"
                    )
                
                # MARK AS SENT
                if st.button("✅ Mark Mailed", key=f"sent_{l.id}", type="primary"):
                    database.update_letter_status(l.id, "Sent")
                    st.toast(f"Order #{l.id} Archived!")
                    st.rerun()
"""

# 3. SECURITY PATCH: Update web_app.py to use Secrets for button visibility
web_app_code = """import streamlit as st
import importlib
import ui_splash
import auth_engine 
import payment_engine
import database

# FORCE RELOAD
importlib.reload(ui_splash)

# 1. INTERCEPT STRIPE RETURN
qp = st.query_params
if "session_id" in qp:
    if "current_view" not in st.session_state:
        st.session_state.current_view = "main_app"

# 2. IMPORTS
from ui_splash import show_splash
from ui_main import show_main_app
from ui_login import show_login
from ui_admin import show_admin

# 3. CONFIG
st.set_page_config(page_title="VerbaPost", page_icon="📮", layout="centered")

def inject_custom_css():
    st.markdown(\"\"\"
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
        div.stButton > button {border-radius: 8px; font-weight: 600; border: 1px solid #e0e0e0;}
        input {border-radius: 5px !important;}
        </style>
        \"\"\", unsafe_allow_html=True)
inject_custom_css()

# 4. HANDLERS
def handle_login(email, password):
    user, error = auth_engine.sign_in(email, password)
    if error:
        st.error(f"Login Failed: {error}")
    else:
        st.success("Welcome!")
        st.session_state.user = user
        st.session_state.user_email = email
        try:
            saved = auth_engine.get_current_address(email)
            if saved:
                st.session_state["from_name"] = saved.get("name", "")
                st.session_state["from_street"] = saved.get("street", "")
                st.session_state["from_city"] = saved.get("city", "")
                st.session_state["from_state"] = saved.get("state", "")
                st.session_state["from_zip"] = saved.get("zip", "")
                st.session_state["selected_language"] = saved.get("language", "English")
        except: pass
        st.session_state.current_view = "main_app"
        st.rerun()

def handle_signup(email, password, name, street, city, state, zip_code, language):
    user, error = auth_engine.sign_up(email, password, name, street, city, state, zip_code, language)
    if error:
        st.error(f"Error: {error}")
    else:
        st.success("Created!")
        st.session_state.user = user
        st.session_state.user_email = email
        st.session_state.selected_language = language
        st.session_state.current_view = "main_app"
        st.rerun()

# 5. STATE
if "current_view" not in st.session_state: st.session_state.current_view = "splash" 
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.current_view == "splash":
    show_splash()
elif st.session_state.current_view == "login":
    show_login(handle_login, handle_signup)
elif st.session_state.current_view == "admin":
    show_admin()
elif st.session_state.current_view == "main_app":
    with st.sidebar:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_view = "splash"
            st.rerun()
        
        if st.session_state.get("user"):
            st.caption(f"User: {st.session_state.user_email}")
            
            # SECURE ADMIN CHECK
            try:
                admin_email = st.secrets["admin"]["email"]
                if st.session_state.user.user.email == admin_email: 
                    if st.button("🔐 Admin Panel", type="primary"):
                        st.session_state.current_view = "admin"
                        st.rerun()
            except: pass

            if st.button("Log Out"):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
                
    show_main_app()

# 6. FOOTER
with st.sidebar:
    st.divider()
    st.markdown("📧 **Help:** support@verbapost.com")
"""

# EXECUTE CLEANUP
print("🧹 Starting Cleanup...")
for f in trash_files:
    if os.path.exists(f):
        os.remove(f)
        print(f"   - Deleted {f}")

# EXECUTE UPDATES
print("🔒 Securing Admin Logic...")
with open("ui_admin.py", "w") as f: f.write(admin_code)
with open("web_app.py", "w") as f: f.write(web_app_code)

print("✅ Cleanup Complete. Update Secrets now!")
