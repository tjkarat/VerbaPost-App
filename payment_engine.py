import stripe
import streamlit as st

# --- LOAD KEYS ---
try:
    stripe.api_key = st.secrets["stripe"]["secret_key"]
except Exception as e:
    pass

def create_checkout_session(product_name, amount_in_cents, success_url, cancel_url):
    """
    Creates a Stripe Checkout Session.
    """
    try:
        if not stripe.api_key:
            return None, "Error: Stripe API Key is missing."

        # SMART JOIN: Ensure we append session_id correctly
        join_char = "&" if "?" in success_url else "?"
        final_success_url = f"{success_url}{join_char}session_id={{CHECKOUT_SESSION_ID}}"

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name,
                    },
                    'unit_amount': amount_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=final_success_url,
            cancel_url=cancel_url,
        )
        return session.url, session.id
    except Exception as e:
        return None, str(e)

def check_payment_status(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == 'paid':
            return True
    except:
        pass
    return False
