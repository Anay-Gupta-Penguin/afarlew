import time
import streamlit as st
from game_logic import leaders_from_score_dict


def render_memory(room, my_pid, my_turn):
    st.markdown("""
    <style>
    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"],
    div[data-testid="column"] div[data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    div[data-testid="stButton"] button {
        height: 60px !important;
        min-height: 60px !important;
        padding: 0 !important;
        font-size: 1.5rem !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    players = room["players"]
    names = room["names"]
    badges = room["badges"]
    state = room["state"]
    cards = state["cards"]
    matched = state["matched"]
    flipped = state["flipped"]
    pairs = state["pairs"]

    waiting_flip_back = False
    if state["reveal_until"] > 0:
        if time.time() >= state["reveal_until"]:
            state["flipped"] = []
            state["reveal_until"] = 0.0
            room["turn_idx"] = (room["turn_idx"] + 1) % len(players)
            st.rerun()
        else:
            waiting_flip_back = True

    _, center, _ = st.columns([0.95, 1.5, 0.95])
    with center:
        tally = " · ".join(f"{badges[p]} {names[p]}: **{pairs.get(p, 0)}**" for p in players)
        st.markdown(f"**Pairs Found:** {tally}")
        if waiting_flip_back:
            st.warning("❌ Not a match! Flipping cards back...")

        for r in range(4):
            cols = st.columns(5)
            for c in range(5):
                idx = r * 5 + c
                is_open = (idx in matched) or (idx in flipped)
                label = cards[idx] if is_open else "❓"
                disabled = (not my_turn) or is_open or waiting_flip_back

                if cols[c].button(label, key=f"mem_{idx}", disabled=disabled, use_container_width=True):
                    flipped.append(idx)
                    if len(flipped) == 2:
                        a, b = flipped
                        if cards[a] == cards[b]:
                            matched.update([a, b])
                            state["flipped"] = []
                            pairs[my_pid] = pairs.get(my_pid, 0) + 1
                            if len(matched) == len(cards):
                                room["winner"] = leaders_from_score_dict(pairs)
                        else:
                            state["reveal_until"] = time.time() + 2.0
                    st.rerun()
