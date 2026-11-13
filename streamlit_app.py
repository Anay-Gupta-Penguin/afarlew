import random
import string
import streamlit as st

from store import get_server_store, generate_room_code
from config import handle_wallet_and_payments
from game_logic import init_game_state
from ui_ttt import render_ttt
from ui_c4 import render_c4
from ui_battleship import render_battleship

st.set_page_config(page_title="Streamlit Arcade", page_icon="🎮", layout="centered")
store = get_server_store()

for key, default in [("player_id", "".join(random.choices(string.ascii_uppercase, k=8))), ("credits", 0), ("room_code", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

handle_wallet_and_payments(store)
st.title("🎮 Pay-to-Play Multiplayer Arcade")

if not st.session_state.room_code:
    if st.session_state.credits < 1:
        st.warning("Top up at least **1 Credit** in the sidebar to create or join a room.")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Create a Match")
        game = st.selectbox("Select Game", ["Tic-Tac-Toe", "Connect 4", "Battleship"])
        if st.button("Create Room (1 Credit)", disabled=st.session_state.credits < 1, use_container_width=True):
            st.session_state.credits -= 1
            code = generate_room_code(store)
            store["rooms"][code] = {"game": game, "p1": st.session_state.player_id, "p2": None, "turn": "P1", "winner": None, "state": init_game_state(game)}
            st.session_state.room_code = code
            st.rerun()
    with col2:
        st.subheader("Join a Match")
        join_code = st.text_input("4-Letter Room Code", max_chars=4).upper().strip()
        if st.button("Join Room (1 Credit)", disabled=st.session_state.credits < 1, use_container_width=True):
            room = store["rooms"].get(join_code)
            if not room or (room["p2"] and room["p1"] != st.session_state.player_id):
                st.error("Room unavailable or full.")
            else:
                st.session_state.credits -= 1
                if room["p1"] != st.session_state.player_id:
                    room["p2"] = st.session_state.player_id
                st.session_state.room_code = join_code
                st.rerun()
else:
    if st.sidebar.button("🚪 Leave Room", use_container_width=True):
        st.session_state.room_code = None
        st.rerun()

    code = st.session_state.room_code
    room = store["rooms"].get(code)
    role = "P1" if room["p1"] == st.session_state.player_id else "P2"

    @st.fragment(run_every=2)
    def live_match():
        st.info(f"**{room['game']}** | Room: `{code}` | You: **{role}**")
        if not room["p2"]:
            st.warning(f"Share code **{code}** with Player 2 to start.")
            return
        if room["winner"]:
            st.success("🤝 Draw!" if room["winner"] == "DRAW" else f"🏆 **{room['winner']} Wins!**")
        else:
            st.success("🟢 Your Turn!") if room["turn"] == role else st.info(f"⏳ Waiting for {room['turn']}...")

        my_turn = (room["turn"] == role) and (room["winner"] is None)
        if room["game"] == "Tic-Tac-Toe":
            render_ttt(room, role, my_turn)
        elif room["game"] == "Connect 4":
            render_c4(room, role, my_turn)
        elif room["game"] == "Battleship":
            render_battleship(room, role, my_turn)

    live_match()
