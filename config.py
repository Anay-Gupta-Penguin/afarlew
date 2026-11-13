import streamlit as st
import stripe

USE_STRIPE = False  # Set True after adding STRIPE_SECRET_KEY in Streamlit Secrets
ENTRY_FEE_CENTS = 100
APP_URL = "https://streamlit.app"

if USE_STRIPE:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]


def create_stripe_checkout():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "1 Arcade Game Credit"},
                "unit_amount": ENTRY_FEE_CENTS,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{APP_URL}?paid_session={{CHECKOUT_SESSION_ID}}",
        cancel_url=APP_URL,
    )
    return session.url


def handle_wallet_and_payments(store):
    if USE_STRIPE and "paid_session" in st.query_params:
        sid = st.query_params["paid_session"]
        if sid not in store["processed_payments"]:
            checkout = stripe.checkout.Session.retrieve(sid)
            if checkout.payment_status == "paid":
                st.session_state.credits += 1
                store["processed_payments"].add(sid)
                st.toast("Payment verified! +1 Credit", icon="✅")
        st.query_params.clear()

    with st.sidebar:
        st.header("🎟️ Arcade Wallet")
        st.metric("Available Credits", st.session_state.credits)
        st.caption("1 Credit per match.")
        if USE_STRIPE:
            if st.button("💳 Buy 1 Credit ($1.00)", use_container_width=True):
                st.link_button("Pay with Stripe", create_stripe_checkout(), use_container_width=True)
        else:
            if st.button("💳 Demo Top-Up (+1 Credit)", use_container_width=True):
                st.session_state.credits += 1
                st.rerun()
