import random
import string
import time
import streamlit as st

from store import get_server_store, generate_room_code, PLAYER_BADGES
from game_logic import GAMES, init_game_state
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

if "full_view" not in st.session_state:
    st.session_state.full_view = False

pad_top = "0.6rem" if st.session_state.full_view else "2.4rem"
header_css = "header[data-testid='stHeader'] { display: none !important; }" if st.session_state.full_view else ""

st.markdown(f"""
<style>
{header_css}
.block-container {{
    padding-top: {pad_top} !important;
    padding-bottom: 1.2rem !important;
    max-width: {"100%" if st.session_state.full_view else "1200px"} !important;
}}
div[data-testid="stHorizontalBlock"] {{
    flex-wrap: nowrap !important;
    gap: 0.35rem !important;
}}
div[data-testid="stHorizontalBlock"] > div {{
    min-width: 0 !important;
}}
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
REALTIME_3D_GAMES = ("1v1.LOL", "Battle Royale")


def _join_room(code):
    code = (code or "").upper().strip()
    if not code:
        st.error("Enter a 4-character room code.")
        return
    room = store["rooms"].get(code)
    if not room:
        st.error(f"Room `{code}` not found.")
        return

    meta = GAMES[room["game"]]
    already_in = my_pid in room["players"]
    if not already_in and len(room["players"]) >= meta["max"]:
        st.error(f"Room is full ({meta['max']}/{meta['max']} players).")
        return
    if not already_in and room["started"] and room["game"] not in REALTIME_3D_GAMES:
        st.error("Match is already in progress.")
        return

    if not already_in:
        idx = len(room["players"])
        room["players"].append(my_pid)
        room["names"][my_pid] = st.session_state.nickname or f"Player {idx + 1}"
        room["badges"][my_pid] = PLAYER_BADGES[idx % len(PLAYER_BADGES)]
        room["scores"][my_pid] = 0
        if room["game"] not in REALTIME_3D_GAMES and meta["max"] == 2 and len(room["players"]) == 2:
            room["started"] = True
            room["state"] = init_game_state(room["game"], room["players"])

    room["last_active"] = time.time()
    st.session_state.room_code = code
    st.query_params["room"] = code
    st.rerun(scope="app")


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
                "code": code,
                "game": game_choice,
                "host": my_pid,
                "players": [my_pid],
                "names": {my_pid: display_name},
                "badges": {my_pid: PLAYER_BADGES[0]},
                "started": (game_choice in REALTIME_3D_GAMES),
                "starter_idx": 0,
                "turn_idx": 0,
                "winner": None,
                "counted": False,
                "last_active": time.time(),
                "scores": {my_pid: 0, "DRAW": 0},
                "state": {},
            }
            st.session_state.room_code = code
            st.query_params["room"] = code
            st.rerun(scope="app")

    with col2:
        st.subheader("Join by Room Code")
        join_code = st.text_input(
            "4-Character Room Code",
            value=prefill_code,
            max_chars=4,
        ).upper().strip()
        if st.button("Join Room", use_container_width=True):
            _join_room(join_code)

    @st.fragment(run_every=3)
    def open_rooms_list():
        st.divider()
        st.subheader("🌐 Live Open Rooms (1-Click Join)")
        open_rooms = [
            (c, r)
            for c, r in store["rooms"].items()
            if len(r["players"]) < GAMES[r["game"]]["max"]
            and (not r["started"] or r["game"] in REALTIME_3D_GAMES)
        ]
        if not open_rooms:
            st.caption("No open rooms right now — create one above and it will appear here for your friends!")
            return

        for c, r in open_rooms:
            meta = GAMES[r["game"]]
            host_name = r["names"].get(r["host"], "Player 1")
            r_col1, r_col2 = st.columns([4, 1], vertical_alignment="center")
            r_col1.markdown(
                f"**{r['game']}** · Room `{c}` · Host: **{host_name}** · "
                f"Players: **{len(r['players'])}/{meta['max']}**"
            )
            if r_col2.button("Join ➡️", key=f"quick_join_{c}", use_container_width=True):
                _join_room(c)

    open_rooms_list()

# --- ACTIVE ROOM ---
else:
    code = st.session_state.room_code
    room = store["rooms"].get(code)

    if not room or my_pid not in room["players"]:
        st.warning("This room expired or you were disconnected.")
        st.session_state.room_code = None
        st.query_params.clear()
        if st.button("Back to Lobby"):
            st.rerun(scope="app")
        st.stop()

    room["last_active"] = time.time()
    meta = GAMES[room["game"]]

    # --- 3D 1v1.LOL & FORTNITE BATTLE ROYALE ---
    if room["game"] in REALTIME_3D_GAMES:
        mode_tag = "1v1" if room["game"] == "1v1.LOL" else "br"
        title_label = "🏗️ 1v1.LOL Build Fight" if mode_tag == "1v1" else "🪂 Fortnite Battle Royale"

        bar_left, bar_right = st.columns([6.5, 1], vertical_alignment="center")
        with bar_left:
            st.info(
                f"**{title_label}** · Room `{code}` · "
                f"You: **{room['badges'][my_pid]} {room['names'][my_pid]}** · "
                f"Share code `{code}` or join from the Home Lobby!"
            )
        with bar_right:
            if st.button("🚪 Leave", use_container_width=True):
                if my_pid in room["players"]:
                    room["players"].remove(my_pid)
                    if room["players"]:
                        room["host"] = room["players"][0]
                    else:
                        del store["rooms"][code]
                st.session_state.room_code = None
                st.query_params.clear()
                st.rerun(scope="app")

        render_br(room, my_pid, arena_mode=mode_tag)
        st.stop()

    # --- TURN-BASED / PARTY GAMES ---
    @st.fragment(run_every=2)
    def live_match():
        players = room["players"]
        names = room["names"]
        badges = room["badges"]
        scores = room["scores"]

        score_parts = [f"{badges[p]} {names[p]}: **{scores.get(p, 0)}**" for p in players]
        if scores.get("DRAW", 0) > 0:
            score_parts.append(f"Draws: **{scores['DRAW']}**")

        bar_left, bar_fs, bar_right = st.columns([5.8, 1.1, 1], vertical_alignment="center")
        with bar_left:
            st.info(
                f"**{room['game']}** · Room `{code}` · You: **{badges[my_pid]} {names[my_pid]}** · "
                + " · ".join(score_parts)
            )
        with bar_fs:
            fs_lbl = "🗗 Exit Full" if st.session_state.full_view else "⛶ Fullscreen"
            if st.button(fs_lbl, use_container_width=True):
                st.session_state.full_view = not st.session_state.full_view
                st.rerun(scope="app")
        with bar_right:
            if st.button("🚪 Leave", use_container_width=True):
                if my_pid in room["players"]:
                    room["players"].remove(my_pid)
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
                st.rerun(scope="app")

        if not room["started"]:
            st.subheader(f"⏳ Waiting Room ({len(players)}/{meta['max']} Players)")
            st.write(f"Share code **`{code}`** (or have friends click Join in Live Open Rooms)!")
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
                    st.rerun(scope="app")
            else:
                st.info(f"Waiting for **{names[room['host']]}** to start the match...")
            return

        if not room.get("state"):
            room["state"] = init_game_state(room["game"], players)

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
                st.rerun(scope="app")

        active_pid = players[room["turn_idx"] % len(players)]
        if room["winner"] is None and room["game"] not in ("Rock Paper Scissors", "Battleship"):
            if active_pid == my_pid:
                st.success(f"🟢 **Your Turn!** ({badges[my_pid]} {names[my_pid]})")
            else:
                st.info(f"⏳ Waiting for **{badges[active_pid]} {names[active_pid]}**...")

        my_turn = (active_pid == my_pid) and (room["winner"] is None)
        g = room["game"]

        if g == "Tic-Tac-Toe":
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
