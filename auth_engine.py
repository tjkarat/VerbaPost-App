import streamlit as st
import database

# Try to import library safely
try:
    from supabase import create_client, Client
    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False

def get_supabase_client():
    if not LIB_AVAILABLE: return None, "Library 'supabase' not installed."
    try:
        supabase_secrets = st.secrets.get("supabase", None)
        if not supabase_secrets: return None, "Missing [supabase] section."
        url = supabase_secrets.get("url")
        key = supabase_secrets.get("key")
        if not url or not key: return None, "Missing 'url' or 'key'."
        return create_client(url, key), None
    except Exception as e: return None, f"Connection Error: {e}"

def sign_up(email, password, name, street, city, state, zip_code, language="English"):
    client, err = get_supabase_client()
    if err: return None, err
    
    try:
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user:
             try:
                 # Ensure user row exists
                 database.create_or_get_user(email)
                 # Update Profile with Language
                 database.update_user_profile(email, name, street, city, state, zip_code, language)
             except Exception as db_err:
                 print(f"DB Sync Error: {db_err}")
             return response, None
        return None, "Signup failed"
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    client, err = get_supabase_client()
    if err: return None, err
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            try: database.create_or_get_user(email)
            except: pass
            return response, None
        return None, "Login failed"
    except Exception as e: return None, str(e)

def get_current_address(email):
    try:
        user = database.get_user_by_email(email)
        if user:
            return {
                "name": user.address_name or "",
                "street": user.address_street or "",
                "city": user.address_city or "",
                "state": user.address_state or "",
                "zip": user.address_zip or "",
                "language": user.language or "English"
            }
    except: pass
    return {}
