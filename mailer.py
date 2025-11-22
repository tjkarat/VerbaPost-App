import streamlit as st
import lob

# Load API Key
try:
    lob.api_key = st.secrets["lob"]["api_key"]
except:
    pass

def send_letter(pdf_path, to_address, from_address):
    """
    Sends a physical letter via Lob.
    Handles key mapping (street -> address_line1) automatically.
    """
    try:
        # Helper to map keys safely
        def map_address(addr):
            return {
                'name': addr.get('name'),
                'address_line1': addr.get('address_line1') or addr.get('street'),
                'address_city': addr.get('address_city') or addr.get('city'),
                'address_state': addr.get('address_state') or addr.get('state'),
                'address_zip': addr.get('address_zip') or addr.get('zip')
            }

        clean_to = map_address(to_address)
        clean_from = map_address(from_address)

        # Validation
        if not clean_to['address_line1']:
            return {"error": "Missing address line for recipient"}

        with open(pdf_path, 'rb') as file:
            response = lob.Letter.create(
                description="VerbaPost Letter",
                to_address=clean_to,
                from_address=clean_from,
                file=file,
                color=True
            )
            return response

    except Exception as e:
        st.error(f"Mailer Error: {e}")
        return None
