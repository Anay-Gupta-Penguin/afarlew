import random
import string
import streamlit as st


@st.cache_resource
def get_server_store():
    return {
        "rooms": {},
        "processed_payments": set(),
    }


def generate_room_code(store):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choices(chars, k=4))
        if code not in store["rooms"]:
            return code
