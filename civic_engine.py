import requests
import streamlit as st

# Load Key
try:
    API_KEY = st.secrets["geocodio"]["api_key"]
except:
    API_KEY = None

def get_reps(address):
    if not API_KEY:
        st.error("❌ Configuration Error: Geocodio API Key is missing.")
        return []

    # Geocodio Endpoint
    url = "https://api.geocod.io/v1.7/geocode"
    
    # FIX: Changed 'congress' to 'cd' (Congressional District) which is the standard field
    params = {
        'q': address,
        'fields': 'cd',
        'api_key': API_KEY
    }

    print(f"🔍 Geocodio Lookup: {address}")

    try:
        r = requests.get(url, params=params)
        data = r.json()

        if "error" in data:
            st.error(f"❌ Geocodio Error: {data['error']}")
            return []

        if not data.get('results'):
            st.warning("⚠️ Address not found.")
            return []

        # Get the first result (best match)
        result = data['results'][0]
        
        targets = []
        
        # Parse Congressional Data
        districts = result.get('fields', {}).get('congressional_districts', [])
        
        for district in districts:
            legislators = district.get('current_legislators', [])
            
            for leg in legislators:
                role = leg['type'] # 'senator' or 'representative'
                title = "U.S. Senator" if role == 'senator' else "U.S. Representative"
                
                # Robust address extraction
                contact = leg.get('contact', {})
                addr_raw = contact.get('address', 'United States Capitol, Washington DC 20510')
                
                clean_address = {
                    'name': f"{leg['first_name']} {leg['last_name']}",
                    'street': addr_raw,
                    'city': "Washington",
                    'state': "DC",
                    'zip': "20510"
                }

                # Avoid duplicates
                is_duplicate = False
                for t in targets:
                    if t['name'] == clean_address['name']:
                        is_duplicate = True
                
                if not is_duplicate:
                    targets.append({
                        'name': f"{leg['first_name']} {leg['last_name']}",
                        'title': title,
                        'address_obj': clean_address
                    })

        if len(targets) == 0:
            st.warning("⚠️ Location found, but no legislators listed in database.")
        
        return targets

    except Exception as e:
        st.error(f"❌ Civic Engine Crash: {e}")
        return []
