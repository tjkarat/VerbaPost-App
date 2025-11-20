import streamlit as st
from gotrue.client import Client
import database

# --- LOAD SECRETS SAFELY ---
try:
    # Try different casing just in case
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    auth_client = Client(url=url, headers={"apikey": key})
    AUTH_ACTIVE = True
except Exception as e:
    print(f"⚠️ Auth Init Error: {e}")
    auth_client = None
    AUTH_ACTIVE = False

def sign_up(email, password):
    if not AUTH_ACTIVE: return None, "System Error: Supabase Secrets missing."
    
    try:
        # 1. Create Auth User
        response = auth_client.sign_up(email=email, password=password)
        
        # 2. Sync with Database (Critical for saving addresses later)
        if response:
             try:
                 database.create_or_get_user(email)
             except Exception as db_err:
                 print(f"DB Sync Error: {db_err}")
                 
        return response, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    if not AUTH_ACTIVE: return None, "System Error: Supabase Secrets missing."
    
    try:
        response = auth_client.sign_in(email=email, password=password)
        return response, None
    except Exception as e:
        return None, str(e)

def get_current_address(email):
    """
    Fetches the saved address from the SQL database for this user.
    """
    try:
        user = database.get_user_by_email(email)
        if user:
            return {
                "name": user.address_name or "",
                "street": user.address_street or "",
                "city": user.address_city or "",
                "state": user.address_state or "",
                "zip": user.address_zip or ""
            }
    except Exception as e:
        print(f"Address Load Error: {e}")
    return {}
