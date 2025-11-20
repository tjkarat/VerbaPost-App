import streamlit as st

# Version 2.0 - Force Pricing Update
def show_splash():
    # --- CONFIG ---
    P_STANDARD = ".99"
    P_HEIRLOOM = ".99"
    P_CIVIC = ".99"

    # --- HERO ---
    st.title("VerbaPost 📮")
    
    st.markdown(
        """
        ### Texts are trivial. Emails are ignored.
        # Real letters get read.
        """
    )
    
    st.divider()

    # --- HOW IT WORKS ---
    st.subheader("How it Works")
    step1, step2, step3 = st.columns(3)
    
    with step1:
        st.markdown("### 🎙️ 1. Dictate")
        st.write("Tap the mic and speak your mind. Our AI transcribes and polishes your message.")
    
    with step2:
        st.markdown("### ✍️ 2. Sign")
        st.write("Review the text, sign your name on the screen, and choose your style.")
    
    with step3:
        st.markdown("### 📮 3. We Mail")
        st.write("We print, fold, stamp, and mail a physical letter to your recipient.")

    st.divider()

    # --- PRICING TIERS ---
    st.subheader("Simple Pricing")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.info(f"**Standard**\n\n# {P_STANDARD}")
        st.caption("API Fulfillment • Window Envelope • Mailed via Lob")

    with c2:
        st.success(f"**Heirloom**\n\n# {P_HEIRLOOM}")
        st.caption("Hand-Stamped • Premium Paper • Mailed from Nashville, TN")

    with c3:
        st.warning(f"**Civic Blast**\n\n# {P_CIVIC}")
        st.caption("Activism Mode • Auto-Find Reps • Mails Senate + House")

    st.divider()

    # --- CTA ---
    col_spacer, col_btn, col_spacer2 = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🚀 Start Writing Now", type="primary", use_container_width=True):
            st.session_state.current_view = "main_app"
            st.rerun()

    st.markdown("<div style='text-align: center'><a href='#'>Already have an account? Log In</a></div>", unsafe_allow_html=True)
