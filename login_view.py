import streamlit as st
import auth_engine
import time

def show_login():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("VerbaPost 📮")
        st.markdown("### Member Access")

        tab_login, tab_signup = st.tabs(["Log In", "Create Account"])

        # --- LOGIN ---
        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Log In", type="primary", use_container_width=True):
                with st.spinner("Verifying..."):
                    user, error = auth_engine.sign_in(email, password)
                    if error:
                        st.error(f"Failed: {error}")
                    else:
                        st.success("Success!")
                        # Save critical user info to session
                        st.session_state.user = user
                        st.session_state.user_email = email # Easier access
                        st.session_state.current_view = "main_app"
                        st.rerun()

        # --- SIGN UP ---
        with tab_signup:
            new_email = st.text_input("Email", key="new_email")
            new_pass = st.text_input("Password", type="password", key="new_pass")
            
            if st.button("Create Account", use_container_width=True):
                with st.spinner("Creating account..."):
                    user, error = auth_engine.sign_up(new_email, new_pass)
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.success("Account created! You are logged in.")
                        st.session_state.user = user
                        st.session_state.user_email = new_email
                        st.session_state.current_view = "main_app"
                        st.rerun()
        
        st.divider()
        if st.button("⬅️ Back to Home"):
            st.session_state.current_view = "splash"
            st.rerun()