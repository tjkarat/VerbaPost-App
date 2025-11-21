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

    # FIX: The definitive, correct endpoint for v2
    url = "https://civicinfo.googleapis.com/civicinfo/v2/representatives"
    
    params = {
        'key': API_KEY,
        'address': address,
        'levels': 'country',
        'roles': ['legislatorUpperBody', 'legislatorLowerBody']
    }

    try:
        r = requests.get(url, params=params)
        
        # Specific handling for 404 vs other errors
        if r.status_code == 404:
            st.error(f"❌ Google API Error (404): The API endpoint URL is wrong or the address format is invalid.")
            return []
            
        data = r.json()
        
        if "error" in data:
            err_content = data['error']
            msg = err_content.get('message', str(err_content)) if isinstance(err_content, dict) else str(err_content)
            st.error(f"❌ Google API Error: {msg}")
            return []

        targets = []
        
        if 'offices' not in data:
            st.warning(f"⚠️ No representatives found. Google couldn't match this address to a district.")
            return []

        for office in data.get('offices', []):
            name_lower = office['name'].lower()
            if "senate" in name_lower or "senator" in name_lower or "representative" in name_lower:
                for index in office['officialIndices']:
                    official = data['officials'][index]
                    
                    # Parse Address
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
