import streamlit as st
import database
import letter_format
import os

# --- CONFIG ---
# Replace this with YOUR email to lock the door
ADMIN_EMAIL = "tjkarat@gmail.com" 

def show_admin():
    st.title("👮‍♂️ Admin Command")
    
    # Security Check
    if not st.session_state.get("user") or st.session_state.user_email != ADMIN_EMAIL:
        st.error("Access Denied. Authorized Personnel Only.")
        if st.button("Back to Safety"):
            st.session_state.current_view = "splash"
            st.rerun()
        st.stop()

    st.subheader("🗂️ Letter Queue")

    # Fetch Data
    letters = database.get_pending_heirloom_letters()
    
    if not letters:
        st.info("No letters found in database.")
        return

    # Display Metrics
    pending_count = sum(1 for l in letters if l.status != "Sent" and l.status != "Draft")
    c1, c2 = st.columns(2)
    c1.metric("Pending Fulfillment", pending_count)
    c2.metric("Total Database Rows", len(letters))

    st.divider()

    # Render the Queue
    for l in letters:
        # Filter: Show only Paid/Pending items, hide Drafts/Sent (toggle to show all)
        if l.status == "Draft": continue
        
        with st.expander(f"{l.created_at.strftime('%Y-%m-%d')} | To: {l.recipient_name} | Status: {l.status}"):
            c_info, c_action = st.columns([3, 1])
            
            with c_info:
                st.markdown(f"**From:** {l.author.email}")
                st.write(l.content[:100] + "...")
                st.caption(f"ID: {l.id}")

            with c_action:
                # 1. RE-GENERATE PDF BUTTON
                if st.button("📄 Print PDF", key=f"print_{l.id}"):
                    # Reconstruct addresses
                    r_str = f"{l.recipient_name}\n{l.recipient_street}\n{l.recipient_city}, {l.recipient_state} {l.recipient_zip}"
                    
                    # Get sender address safely
                    s_str = ""
                    if l.author:
                        s_str = f"{l.author.address_name}\n{l.author.address_street}\n{l.author.address_city}, {l.author.address_state} {l.author.address_zip}"

                    # Generate
                    # Note: We don't have the signature image, so we pass None.
                    # The formatter will just skip the image.
                    pdf_path = letter_format.create_pdf(
                        l.content, r_str, s_str, True, "English", f"admin_print_{l.id}.pdf", None
                    )
                    
                    with open(pdf_path, "rb") as f:
                        st.download_button("Download", f, f"Letter_{l.id}.pdf", "application/pdf")

                # 2. MARK SENT BUTTON
                if l.status != "Sent":
                    if st.button("✅ Mark Sent", key=f"sent_{l.id}"):
                        database.mark_as_sent(l.id)
                        st.success("Marked!")
                        st.rerun()
                else:
                    st.success("Shipped")
