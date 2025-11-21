import streamlit as st
from ui_splash import show_splash
from ui_main import show_main_app
from ui_login import show_login
from ui_admin import show_admin # <--- NEW IMPORT
import auth_engine 
import payment_engine

st.set_page_config(page_title="VerbaPost", page_icon="📮", layout="centered")

def inject_custom_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
        div.stButton > button {border-radius: 8px; font-weight: 600; border: 1px solid #e0e0e0;}
        input {border-radius: 5px !important;}
        </style>
        """, unsafe_allow_html=True)
inject_custom_css()

# --- HANDLERS ---
def handle_login(email, password):
    user, error = auth_engine.sign_in(email, password)
    if error:
        st.error(f"Login Failed: {error}")
    else:
        st.success("Welcome!")
        st.session_state.user = user
        st.session_state.user_email = email
        saved = auth_engine.get_current_address(email)
        if saved:
            st.session_state["from_name"] = saved.get("name", "")
            st.session_state["from_street"] = saved.get("street", "")
            st.session_state["from_city"] = saved.get("city", "")
            st.session_state["from_state"] = saved.get("state", "")
            st.session_state["from_zip"] = saved.get("zip", "")
        st.session_state.current_view = "main_app"
        st.rerun()

def handle_signup(email, password, name, street, city, state, zip_code):
    user, error = auth_engine.sign_up(email, password, name, street, city, state, zip_code)
    if error:
        st.error(f"Error: {error}")
    else:
        st.success("Created!")
        st.session_state.user = user
        st.session_state.user_email = email
        st.session_state.current_view = "main_app"
        st.rerun()

# --- ROUTER ---
if "session_id" in st.query_params:
    if payment_engine.check_payment_status(st.query_params["session_id"]):
        st.session_state.current_view = "main_app"
        st.session_state.payment_complete = True
        st.query_params.clear() 

if "current_view" not in st.session_state:
    st.session_state.current_view = "splash" 
if "user" not in st.session_state:
    st.session_state.user = None

# ADMIN ROUTE
if st.session_state.current_view == "admin":
    show_admin()

elif st.session_state.current_view == "splash":
    show_splash()
elif st.session_state.current_view == "login":
    show_login(handle_login, handle_signup)
elif st.session_state.current_view == "main_app":
    with st.sidebar:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_view = "splash"
            st.rerun()
        
        if st.session_state.get("user"):
            st.caption(f"User: {st.session_state.user_email}")
            
            # SECRET ADMIN BUTTON
            # Only shows if the logged in email matches
            if st.session_state.user_email == "tjkarat@gmail.com": # <--- Update this to your exact login email!
                if st.button("🔐 Admin Panel", type="primary"):
                     st.session_state.current_view = "admin"
                     st.rerun()

            if st.button("Log Out"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
    show_main_app()