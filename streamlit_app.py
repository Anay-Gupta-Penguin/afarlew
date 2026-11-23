import random
import string
import time
import streamlit as st

from store import get_server_store, generate_room_code, PLAYER_BADGES
from game_logic import GAMES, init_game_state, resolve_br_round
from ui_ttt import render_ttt
from ui_c4 import render_c4
from ui_battleship import render_battleship
from ui_rps import render_rps
from ui_checkers import render_checkers
from ui_dots import render_dots
from ui_sos import render_sos
from ui_memory import render_memory
from ui_br import render_br

st.set_page_config(
    page_title="SHS Arcade",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {
    padding-top: 2.8rem !important;
    padding-bottom: 1.5rem !important;
}
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.3rem !important;
}
div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)

store = get_server_store()

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

my_pid = st.session_state.player_id

# --- LOBBY ---
if not st.session_state.room_code:
    st.title("🎮 Multiplayer Game Arcade")
    name_input = st.text_input(
        "Your Nickname",
        value=st.session_state.nickname,
        max_chars=16,
        placeholder="Enter your name (e.g. Anay)",
    )
    st.session_state.nickname = name_input.strip()
    prefill_code = st.query_params.get("room", "").upper()[:4]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Create a Match")
        game_choice = st.selectbox(
            "Select Game",
            list(GAMES.keys()),
            format_func=lambda g: f"{g} ({GAMES[g]['desc']})",
        )
        if st.button("Create Room", type="primary", use_container_width=True):
            code = generate_room_code(store)
            display_name = st.session_state.nickname or "Player 1"
            store["rooms"][code] = {
                "game": game_choice,
                "host": my_pid,
                "players": [my_pid],
                "names": {my_pid: display_name},
                "badges": {my_pid: PLAYER_BADGES[0]},
                "started": False,
                "starter_idx": 0,
                "turn_idx": 0,
                "winner": None,
                "counted": False,
                "last_active": time.time(),
                "scores": {my_pid: 0, "DRAW": 0},
                "state": init_game_state(game_choice, [my_pid]),
            }
            st.session_state.room_code = code
            st.query_params["room"] = code
            st.rerun()

    with col2:
        st.subheader("Join a Match")
        join_code = st.text_input(
            "4-Character Room Code",
            value=prefill_code,
            max_chars=4,
        ).upper().strip()
        if st.button("Join Room", use_container_width=True):
            room = store["rooms"].get(join_code)
            if not room:
                st.error("Room not found.")
            else:
                meta = GAMES[room["game"]]
                already_in = my_pid in room["players"]
                if not already_in and len(room["players"]) >= meta["max"]:
                    st.error(f"Room is full ({meta['max']}/{meta['max']} players).")
                elif not already_in and room["started"]:
                    st.error("Match is already in progress.")
                else:
                    if not already_in:
                        idx = len(room["players"])
                        room["players"].append(my_pid)
                        room["names"][my_pid] = st.session_state.nickname or f"Player {idx + 1}"
                        room["badges"][my_pid] = PLAYER_BADGES[idx % len(PLAYER_BADGES)]
                        room["scores"][my_pid] = 0
                        if meta["max"] == 2 and len(room["players"]) == 2:
                            room["started"] = True
                            room["state"] = init_game_state(room["game"], room["players"])
                    room["last_active"] = time.time()
                    st.session_state.room_code = join_code
                    st.query_params["room"] = join_code
                    st.rerun()

# --- ACTIVE ROOM ---
else:
    code = st.session_state.room_code
    room = store["rooms"].get(code)

    if not room or my_pid not in room["players"]:
        st.warning("This room expired or you were disconnected.")
        st.session_state.room_code = None
        if st.button("Back to Lobby"):
            st.rerun()
        st.stop()

    room["last_active"] = time.time()
    meta = GAMES[room["game"]]

    @st.fragment(run_every=2)
    def live_match():
        players = room["players"]
        names = room["names"]
        badges = room["badges"]
        scores = room["scores"]

        score_parts = [f"{badges[p]} {names[p]}: **{scores.get(p, 0)}**" for p in players]
        if scores.get("DRAW", 0) > 0:
            score_parts.append(f"Draws: **{scores['DRAW']}**")

        bar_left, bar_right = st.columns([6.5, 1], vertical_alignment="center")
        with bar_left:
            st.info(
                f"**{room['game']}** · Room `{code}` · You: **{badges[my_pid]} {names[my_pid]}** · "
                + " · ".join(score_parts)
            )
        with bar_right:
            if st.button("🚪 Leave", use_container_width=True):
                if my_pid in room["players"]:
                    room["players"].remove(my_pid)
                    if room["game"] == "Battle Royale" and room["started"] and room["winner"] is None:
                        room["state"]["hp"][my_pid] = 0
                        room["state"]["moves"].pop(my_pid, None)
                        alive = [p for p in room["players"] if room["state"]["hp"].get(p, 0) > 0]
                        if len(alive) == 1:
                            room["winner"] = alive[0]
                        elif alive and all(room["state"]["moves"].get(p) is not None for p in alive):
                            resolve_br_round(room)
                    if room["players"]:
                        room["host"] = room["players"][0]
                        room["turn_idx"] = room["turn_idx"] % len(room["players"])
                        if len(room["players"]) < meta["min"] and room["winner"] is None:
                            room["started"] = False
                    else:
                        del store["rooms"][code]
                st.session_state.room_code = None
                st.session_state.chk_sel = None
                st.query_params.clear()
                st.rerun()

        # --- WAITING ROOM / LOBBY ---
        if not room["started"]:
            st.subheader(f"⏳ Waiting Room ({len(players)}/{meta['max']} Players)")
            st.write(f"Share code **`{code}`** (or copy the page URL) so friends can join!")
            for idx, pid in enumerate(players):
                host_tag = " *(Host)*" if pid == room["host"] else ""
                st.markdown(f"**{idx + 1}.** {badges[pid]} **{names[pid]}**{host_tag}")

            if len(players) < meta["min"]:
                st.warning(f"Need at least **{meta['min']}** players to start.")
            elif my_pid == room["host"]:
                if st.button(f"🚀 Start Match ({len(players)} Players)", type="primary", use_container_width=True):
                    room["started"] = True
                    room["turn_idx"] = 0
                    room["starter_idx"] = 0
                    room["winner"] = None
                    room["counted"] = False
                    room["state"] = init_game_state(room["game"], players)
                    st.rerun()
            else:
                st.info(f"Waiting for **{names[room['host']]}** to start the match...")
            return

        # --- WINNER / REMATCH BANNER ---
        if room["winner"] is not None:
            if not room["counted"]:
                if room["winner"] == "DRAW":
                    room["scores"]["DRAW"] = room["scores"].get("DRAW", 0) + 1
                elif isinstance(room["winner"], list):
                    for w_pid in room["winner"]:
                        room["scores"][w_pid] = room["scores"].get(w_pid, 0) + 1
                else:
                    room["scores"][room["winner"]] = room["scores"].get(room["winner"], 0) + 1
                room["counted"] = True

            if room["winner"] == "DRAW":
                st.success("🤝 **It's a Draw!**")
            elif isinstance(room["winner"], list):
                win_names = " & ".join(f"{badges[p]} {names[p]}" for p in room["winner"])
                st.success(f"🏆 **{win_names} Tie for the Win!**")
            else:
                w = room["winner"]
                st.success(f"🏆 **{badges[w]} {names[w]} Wins!**")

            if st.button("🔄 Play Again (Rematch)", type="primary", use_container_width=True):
                next_starter = (room.get("starter_idx", 0) + 1) % len(players)
                room["starter_idx"] = next_starter
                room["turn_idx"] = next_starter
                room["winner"] = None
                room["counted"] = False
                room["state"] = init_game_state(room["game"], players)
                st.session_state.chk_sel = None
                st.rerun()

        # --- TURN BANNER ---
        active_pid = players[room["turn_idx"] % len(players)]
        if room["winner"] is None and room["game"] not in ("Rock Paper Scissors", "Battleship", "Battle Royale"):
            if active_pid == my_pid:
                st.success(f"🟢 **Your Turn!** ({badges[my_pid]} {names[my_pid]})")
            else:
                st.info(f"⏳ Waiting for **{badges[active_pid]} {names[active_pid]}**...")

        my_turn = (active_pid == my_pid) and (room["winner"] is None)
        g = room["game"]

        if g == "Battle Royale":
            render_br(room, my_pid)
        elif g == "Tic-Tac-Toe":
            render_ttt(room, my_pid, my_turn)
        elif g == "Connect 4":
            render_c4(room, my_pid, my_turn)
        elif g == "Battleship":
            render_battleship(room, my_pid, my_turn)
        elif g == "Rock Paper Scissors":
            render_rps(room, my_pid)
        elif g == "Checkers":
            render_checkers(room, my_pid, my_turn)
        elif g == "Dots & Boxes":
            render_dots(room, my_pid, my_turn)
        elif g == "SOS":
            render_sos(room, my_pid, my_turn)
        elif g == "Memory Match":
            render_memory(room, my_pid, my_turn)

    live_match()
