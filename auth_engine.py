import streamlit as st
from gotrue.client import Client
import database

# Load Supabase Config
url = st.secrets.get("supabase", {}).get("url", "")
key = st.secrets.get("supabase", {}).get("key", "")

try:
    auth_client = Client(url=url, headers={"apikey": key})
except:
    auth_client = None

def sign_up(email, password):
    if not auth_client: return None, "Supabase credentials missing"
    try:
        response = auth_client.sign_up(email=email, password=password)
        # Ensure they exist in our SQL DB immediately
        if response:
            database.create_or_get_user(email)
        return response, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    if not auth_client: return None, "Supabase credentials missing"
    try:
        response = auth_client.sign_in(email=email, password=password)
        # Ensure syncing
        if response:
            database.create_or_get_user(email)
        return response, None
    except Exception as e:
        return None, str(e)

def get_current_address(email):
    """Retrieves the saved address for the logged-in user."""
    user = database.get_user_by_email(email)
    if user:
        return {
            "name": user.address_name or "",
            "street": user.address_street or "",
            "city": user.address_city or "",
            "state": user.address_state or "",
            "zip": user.address_zip or ""
        }
    return {}