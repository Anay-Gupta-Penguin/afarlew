import random
import string
import time
import streamlit as st

from store import get_server_store, generate_room_code
from game_logic import init_game_state
from ui_ttt import render_ttt
from ui_c4 import render_c4
from ui_battleship import render_battleship
from ui_rps import render_rps
from ui_checkers import render_checkers

st.set_page_config(page_title="SHS Arcade", page_icon="🎮", layout="wide")

# Prevent game grids from stacking vertically on mobile screens
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.25rem !important;
}
div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)

store = get_server_store()

# Prune inactive rooms older than 2 hours
now = time.time()
expired = [k for k, v in store["rooms"].items() if now - v.get("last_active", now) > 7200]
for k in expired:
    del store["rooms"][k]

if "player_id" not in st.session_state:
    st.session_state.player_id = "".join(random.choices(string.ascii_uppercase, k=8))
if "room_code" not in st.session_state:
    st.session_state.room_code = None
if "nickname" not in st.session_state:
    st.session_state.nickname = ""

st.title("🎮 Multiplayer Game Arcade")
GAMES = ["Tic-Tac-Toe", "Connect 4", "Battleship", "Rock Paper Scissors", "Checkers"]

if not st.session_state.room_code:
    name_input = st.text_input("Your Nickname (optional)", value=st.session_state.nickname, max_chars=16, placeholder="e.g. Alex")
    st.session_state.nickname = name_input.strip()

    prefill_code = st.query_params.get("room", "").upper()[:4]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Create a Match")
        game = st.selectbox("Select Game", GAMES)
        if st.button("Create Room", type="primary", use_container_width=True):
            code = generate_room_code(store)
            store["rooms"][code] = {
                "game": game,
                "p1": st.session_state.player_id,
                "p2": None,
                "names": {"P1": st.session_state.nickname or "Player 1", "P2": "Player 2"},
                "starter": "P1",
                "turn": "P1",
                "winner": None,
                "counted": False,
                "last_active": time.time(),
                "scores": {"P1": 0, "P2": 0, "DRAW": 0},
                "state": init_game_state(game),
            }
            st.session_state.room_code = code
            st.query_params["room"] = code
            st.rerun()

    with col2:
        st.subheader("Join a Match")
        join_code = st.text_input("4-Character Room Code", value=prefill_code, max_chars=4).upper().strip()
        if st.button("Join Room", use_container_width=True):
            room = store["rooms"].get(join_code)
            if not room or (room["p2"] and room["p1"] != st.session_state.player_id and room["p2"] != st.session_state.player_id):
                st.error("Room not found or already full.")
            else:
                if room["p1"] != st.session_state.player_id:
                    room["p2"] = st.session_state.player_id
                    room["names"]["P2"] = st.session_state.nickname or "Player 2"
                room["last_active"] = time.time()
                st.session_state.room_code = join_code
                st.query_params["room"] = join_code
                st.rerun()
else:
    if st.sidebar.button("🚪 Leave Room", use_container_width=True):
        st.session_state.room_code = None
        st.session_state.chk_sel = None
        st.query_params.clear()
        st.rerun()

    code = st.session_state.room_code
    room = store["rooms"].get(code)

    # Guard against expired rooms or server restarts
    if not room:
        st.warning("This room expired or the server restarted.")
        st.session_state.room_code = None
        if st.button("Back to Lobby"):
            st.rerun()
        st.stop()

    room["last_active"] = time.time()
    role = "P1" if room["p1"] == st.session_state.player_id else "P2"
    names = room["names"]

    @st.fragment(run_every=2)
    def live_match():
        s = room["scores"]
        st.info(
            f"**{room['game']}** | Room: `{code}` | You: **{names[role]} ({role})** | "
            f"Score — {names['P1']}: **{s['P1']}** · {names['P2']}: **{s['P2']}** · Draws: **{s['DRAW']}**"
        )

        if not room["p2"]:
            st.warning(f"Share code **{code}** (or copy the page URL) with Player 2 to start!")
            return

        if room["winner"]:
            if not room["counted"] and room["game"] != "Rock Paper Scissors":
                room["scores"][room["winner"]] += 1
                room["counted"] = True
            winner_label = "🤝 Draw!" if room["winner"] == "DRAW" else f"🏆 **{names[room['winner']]} Wins!**"
            st.success(winner_label)
            if st.button("🔄 Play Again (Rematch)", type="primary", use_container_width=True):
                next_starter = "P2" if room.get("starter", "P1") == "P1" else "P1"
                room["state"] = init_game_state(room["game"])
                room["winner"], room["counted"] = None, False
                room["starter"], room["turn"] = next_starter, next_starter
                st.session_state.chk_sel = None
                st.rerun()
        elif room["game"] not in ("Rock Paper Scissors", "Battleship"):
            if room["turn"] == role:
                st.success("🟢 Your Turn!")
            else:
                st.info(f"⏳ Waiting for **{names[room['turn']]}**...")

        my_turn = (room["turn"] == role) and (room["winner"] is None)
        g = room["game"]
        if g == "Tic-Tac-Toe":
            render_ttt(room, role, my_turn)
        elif g == "Connect 4":
            render_c4(room, role, my_turn)
        elif g == "Battleship":
            render_battleship(room, role, my_turn)
        elif g == "Rock Paper Scissors":
            render_rps(room, role)
        elif g == "Checkers":
            render_checkers(room, role, my_turn)

    live_match()
