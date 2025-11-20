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

    # FIX: Updated URL to the correct endpoint
    url = "https://civicinfo.googleapis.com/civicinfo/v2/representatives"
    
    params = {
        'key': API_KEY,
        'address': address,
        # We need specific roles to filter out local dog catchers
        'levels': 'country',
        'roles': ['legislatorUpperBody', 'legislatorLowerBody']
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()
        
        # Case 1: Google sent an error message
        if "error" in data:
            err_msg = data['error'].get('message', 'Unknown Error')
            st.error(f"❌ Google API Error: {err_msg}")
            return []

        targets = []
        
        # Case 2: Success?
        if 'offices' not in data:
            st.warning(f"⚠️ No representatives found for this address.")
            return []

        for office in data.get('offices', []):
            # Check for keywords
            name_lower = office['name'].lower()
            if "senate" in name_lower or "senator" in name_lower or "representative" in name_lower:
                for index in office['officialIndices']:
                    official = data['officials'][index]
                    
                    # Handle Address format
                    addr_list = official.get('address', [])
                    if not addr_list:
                        # Fallback for officials with hidden addresses (Use Capitol Hill)
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
        
        if len(targets) == 0:
             st.warning("⚠️ Found data, but no Senators/Reps matched our filter.")
             
        return targets

    except Exception as e:
        st.error(f"❌ System Crash: {e}")
        return []