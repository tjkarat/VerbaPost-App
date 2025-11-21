import streamlit as st
import auth_engine
import time

def show_login(handle_login, handle_signup): 
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.title("VerbaPost 📮")
        st.subheader("Member Access")
        
        # Check connection safely
        client, err = auth_engine.get_supabase_client()
        if err:
            st.error(f"System Error: {err}")
            st.stop()

        # Use defaults to prevent index errors
        default_idx = 1 if st.session_state.get('initial_mode', 'login') == 'signup' else 0
        try:
            tab_login, tab_signup = st.tabs(["Log In", "Create Account"])
        except:
            # Fallback if tabs fail on older streamlit versions
            st.warning("Please select a mode below:")
            mode = st.radio("Mode", ["Log In", "Create Account"])
            tab_login = st.container() if mode == "Log In" else None
            tab_signup = st.container() if mode == "Create Account" else None

        # LOGIN FORM
        if tab_login:
            with tab_login:
                email = st.text_input("Email", key="l_email")
                password = st.text_input("Password", type="password", key="l_pass")
                if st.button("Log In", type="primary", use_container_width=True):
                    with st.spinner("Verifying..."):
                        handle_login(email, password)

        # SIGNUP FORM
        if tab_signup:
            with tab_signup:
                new_email = st.text_input("Email", key="s_email")
                new_pass = st.text_input("Password", type="password", key="s_pass")
                st.markdown("---")
                st.caption("Return Address (Required)")
                new_name = st.text_input("Full Name", key="s_name")
                new_street = st.text_input("Street", key="s_street")
                c_a, c_b = st.columns(2)
                new_city = c_a.text_input("City", key="s_city")
                new_state = c_b.text_input("State", max_chars=2, key="s_state")
                new_zip = st.text_input("Zip", max_chars=5, key="s_zip")
                
                if st.button("Create Account", type="primary", use_container_width=True):
                    if not (new_name and new_street and new_city and new_state and new_zip):
                        st.error("Please fill all address fields.")
                    else:
                        with st.spinner("Creating..."):
                            handle_signup(new_email, new_pass, new_name, new_street, new_city, new_state, new_zip)
        
        st.divider()
        if st.button("⬅️ Back"):
            st.session_state.current_view = "splash"
            st.rerun()
