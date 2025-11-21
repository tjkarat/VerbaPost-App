import requests
import streamlit as st

# Load Key
try:
    API_KEY = st.secrets["google"]["civic_key"]
except:
    API_KEY = None

def get_reps(address):
    if not API_KEY:
        st.error("❌ Configuration Error: Google Civic API Key is missing in Secrets.")
        return []

    # FIX: Back to the official, standard URL
    url = "https://www.googleapis.com/civicinfo/v2/representatives"
    
    # We ask for Country level (Federal) legislators
    params = {
        'key': API_KEY,
        'address': address,
        'levels': 'country',
        'roles': ['legislatorUpperBody', 'legislatorLowerBody']
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()
        
        # Error Handling
        if "error" in data:
            error_content = data['error']
            # Handle cases where error is a dict or string
            if isinstance(error_content, dict):
                msg = error_content.get('message', str(error_content))
                code = error_content.get('code', '')
            else:
                msg = str(error_content)
                code = ""

            st.error(f"❌ Google API Error ({code}): {msg}")
            
            if int(code) == 403:
                st.info("💡 Tip: Go to Google Cloud Console -> APIs & Services -> Enabled APIs. Make sure 'Google Civic Information API' is ENABLED for this key.")
            
            return []

        targets = []
        
        if 'offices' not in data:
            st.warning(f"⚠️ Google found the address, but returned no representatives.")
            return []

        for office in data.get('offices', []):
            name_lower = office['name'].lower()
            # Filter for Senate and House
            if "senate" in name_lower or "senator" in name_lower or "representative" in name_lower:
                for index in office['officialIndices']:
                    official = data['officials'][index]
                    
                    addr_list = official.get('address', [])
                    if not addr_list:
                        clean_address = {
                            'name': official['name'],
                            'street': 'United States Capitol',
                            'city': 'Washington',
                            'state': 'DC',
                            'zip': '20510'
                        }
                    else:
                        addr_raw = addr_list[0]
                        clean_address = {
                            'name': official['name'],
                            'street': addr_raw.get('line1', ''),
                            'city': addr_raw.get('city', ''),
                            'state': addr_raw.get('state', ''),
                            'zip': addr_raw.get('zip', '')
                        }
                    
                    targets.append({
                        'name': official['name'],
                        'title': office['name'],
                        'address_obj': clean_address
                    })
        
        return targets

    except Exception as e:
        st.error(f"❌ System Crash: {e}")
        return []