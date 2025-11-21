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
    
    # We ask for 'congress' fields to get federal reps
    params = {
        'q': address,
        'fields': 'congress',
        'api_key': API_KEY
    }

    print(f"🔍 Geocodio Lookup: {address}")

    try:
        r = requests.get(url, params=params)
        data = r.json()

        if "error" in data:
            st.error(f"❌ Geocodio Error: {data['error']}")
            return []

        # Geocodio returns a list of results (we take the first/best match)
        if not data.get('results'):
            st.warning("⚠️ Address not found in database.")
            return []

        result = data['results'][0]
        
        targets = []
        
        # Parse Congress Data
        congress_data = result.get('fields', {}).get('congressional_districts', [])
        
        for district in congress_data:
            # Geocodio returns "current_legislators" list for each district
            legislators = district.get('current_legislators', [])
            
            for leg in legislators:
                # Filter for Senator and Representative
                role = leg['type'] # 'senator' or 'representative'
                
                # Map Geocodio format to our App format
                title = "U.S. Senator" if role == 'senator' else "U.S. Representative"
                
                # Address extraction (Geocodio provides contact info)
                contact = leg.get('contact', {})
                addr_raw = contact.get('address', 'United States Capitol, Washington DC 20510')
                
                # Simple parsing of the address string returned by Geocodio
                # Example: "317 Russell Senate Office Building Washington DC 20510"
                # We use a generic DC address if parsing gets too messy, ensuring delivery to the hill.
                clean_address = {
                    'name': f"{leg['first_name']} {leg['last_name']}",
                    'street': addr_raw, # Use the full string for line 1
                    'city': "Washington",
                    'state': "DC",
                    'zip': "20510" 
                }

                targets.append({
                    'name': f"{leg['first_name']} {leg['last_name']}",
                    'title': title,
                    'address_obj': clean_address
                })

        if len(targets) == 0:
            st.warning("⚠️ Address located, but no current legislators found.")
        
        return targets

    except Exception as e:
        st.error(f"❌ Civic Engine Crash: {e}")
        return []
