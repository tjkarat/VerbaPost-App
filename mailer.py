import requests
import streamlit as st
import os

# Load API Key
try:
    LOB_API_KEY = st.secrets["lob"]["api_key"]
    LOB_AVAILABLE = True
except:
    LOB_AVAILABLE = False
    LOB_API_KEY = ""

def send_letter(pdf_path, to_addr, from_addr):
    """
    Uploads PDF to Lob. 
    to_addr and from_addr are dictionaries: {name, street, city, state, zip}
    """
    if not LOB_AVAILABLE:
        print("⚠️ Simulation: Mail sent (No Lob API Key).")
        return True

    print(f"📮 Sending to Lob: {os.path.basename(pdf_path)}")
    
    url = "https://api.lob.com/v1/letters"
    
    try:
        with open(pdf_path, 'rb') as file:
            payload = {
                "description": "VerbaPost Letter",
                "to[name]": to_addr['name'],
                "to[address_line1]": to_addr['street'],
                "to[address_city]": to_addr['city'],
                "to[address_state]": to_addr['state'],
                "to[address_zip]": to_addr['zip'],
                "from[name]": from_addr['name'],
                "from[address_line1]": from_addr['street'],
                "from[address_city]": from_addr['city'],
                "from[address_state]": from_addr['state'],
                "from[address_zip]": from_addr['zip'],
                "color": "false"
            }
            
            response = requests.post(
                url, 
                auth=(LOB_API_KEY, ''), 
                data=payload, 
                files={'file': file}
            )
            
            if response.status_code == 200:
                st.toast(f"✅ Lob ID: {response.json()['id']}")
                print(f"✅ Lob Success: {response.json()['id']}")
                return True
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown Error')
                st.error(f"Lob Error: {error_msg}")
                return False

    except Exception as e:
        st.error(f"Connection Error: {e}")
        return False