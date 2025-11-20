import streamlit as st
import database

# --- 1. SAFE LIBRARY IMPORT ---
try:
    from supabase import create_client, Client
    LIB_AVAILABLE = True
except ImportError:
    LIB_AVAILABLE = False
    auth_client = None

# --- 2. LOAD SECRETS ---
if LIB_AVAILABLE:
    try:
        url = st.secrets.get("supabase", {}).get("url", "")
        key = st.secrets.get("supabase", {}).get("key", "")
        
        if url and key:
            supabase: Client = create_client(url, key)
            AUTH_ACTIVE = True
        else:
            AUTH_ACTIVE = False
    except Exception as e:
        print(f"⚠️ Auth Init Error: {e}")
        AUTH_ACTIVE = False
else:
    AUTH_ACTIVE = False


def sign_up(email, password):
    if not LIB_AVAILABLE: return None, "Error: 'supabase' library not installed on server."
    if not AUTH_ACTIVE: return None, "System Error: Supabase secrets missing."
    
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
             # Sync with local DB
             try:
                 database.create_or_get_user(email)
             except:
                 pass
             return response, None
        return None, "Signup failed"
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    if not LIB_AVAILABLE: return None, "Error: 'supabase' library not installed on server."
    if not AUTH_ACTIVE: return None, "System Error: Supabase secrets missing."
    
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            try:
                 database.create_or_get_user(email)
            except:
                 pass
            return response, None
        return None, "Login failed"
    except Exception as e:
        return None, str(e)

def get_current_address(email):
    import database # Late import to avoid circular errors
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