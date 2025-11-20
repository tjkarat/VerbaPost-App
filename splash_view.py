import streamlit as st

def show_splash():
    P_STANDARD = ".99"
    P_HEIRLOOM = ".99"
    P_CIVIC = ".99"

    st.title("VerbaPost 📮")
    st.subheader("The Authenticity Engine.")
    
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Standard**\n\n# {P_STANDARD}")
        st.caption("API Fulfillment")
    with c2:
        st.success(f"**Heirloom**\n\n# {P_HEIRLOOM}")
        st.caption("Hand-Stamped")
    with c3:
        st.warning(f"**Civic**\n\n# {P_CIVIC}")
        st.caption("Activism")

    st.divider()

    if st.button("🚀 Start Writing Now", type="primary", use_container_width=True):
        st.session_state.current_view = "main_app"
        st.rerun()

    st.markdown("Already a member? [Log In](#)")
