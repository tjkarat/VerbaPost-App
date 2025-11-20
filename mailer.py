import lob
import streamlit as st
import os

# Initialize Lob
try:
    lob.api_key = st.secrets["lob"]["api_key"]
    LOB_AVAILABLE = True
except:
    LOB_AVAILABLE = False
    # We don't print an error here to avoid cluttering the logs if just testing UI

def send_letter(pdf_path):
    """
    Uploads the generated PDF to Lob and sends a letter.
    """
    if not LOB_AVAILABLE:
        print("⚠️ Simulation: Mail sent (No Lob API Key found).")
        return True

    print(f"📮 Sending to Lob: {os.path.basename(pdf_path)}")
    
    try:
        # 1. Open the PDF
        with open(pdf_path, 'rb') as file:
            # 2. Create the Letter via API
            # Note: In 'Test' mode, this validates the request but doesn't actually mail it.
            response = lob.Letter.create(
                description = "VerbaPost Letter",
                to_address = {
                    'name': 'VerbaPost User', # In Day 4 we will pull real names
                    'address_line1': '185 Berry St',
                    'address_city': 'San Francisco',
                    'address_state': 'CA',
                    'address_zip': '94107'
                },
                from_address = {
                    'name': 'Tarak Robbana',
                    'address_line1': '1008 Brandon Court',
                    'address_city': 'Mt Juliet',
                    'address_state': 'TN',
                    'address_zip': '37122'
                },
                file = file,
                color = False # Black & White is cheaper ($1.00 vs $2.00)
            )
        
        print(f"✅ Lob Success! ID: {response['id']}")
        return True

    except Exception as e:
        print(f"❌ Lob Error: {e}")
        st.error(f"Mailing Failed: {e}")
        return False