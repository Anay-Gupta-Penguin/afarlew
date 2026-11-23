import streamlit as st
from game_logic import leaders_from_score_dict

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
AXIS_PAIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1)]


def _count_new_sos(board, r, c, letter):
    found = []
    if letter == "S":
        for dr, dc in DIRS:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if 0 <= r2 < 5 and 0 <= c2 < 5:
                if board[r1][c1] == "O" and board[r2][c2] == "S":
                    found.append([(r, c), (r1, c1), (r2, c2)])
    else:
        for dr, dc in AXIS_PAIRS:
            r1, c1 = r - dr, c - dc
            r2, c2 = r + dr, c + dc
            if 0 <= r1 < 5 and 0 <= c1 < 5 and 0 <= r2 < 5 and 0 <= c2 < 5:
                if board[r1][c1] == "S" and board[r2][c2] == "S":
                    found.append([(r1, c1), (r, c), (r2, c2)])
    return found


def render_sos(room, my_pid, my_turn):
    st.markdown("""
    <style>
    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"],
    div[data-testid="column"] div[data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    div[data-testid="stButton"] button {
        height: 56px !important;
        min-height: 56px !important;
        padding: 0 !important;
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    players = room["players"]
    names = room["names"]
    badges = room["badges"]
    state = room["state"]
    board = state["board"]
    sos_scores = state["sos_scores"]
    last_sos = set(state.get("last_sos", []))

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        tally = " · ".join(f"{badges[p]} {names[p]}: **{sos_scores.get(p, 0)}**" for p in players)
        st.markdown(f"**SOS Points:** {tally}")
        letter = st.radio("Choose letter to place:", ["S", "O"], horizontal=True, key="sos_letter")

        for r in range(5):
            cols = st.columns(5)
            for c in range(5):
                val = board[r][c]
                label = f"✨{val}" if (r, c) in last_sos else (val if val else " ")
                if cols[c].button(
                    label,
                    key=f"sos_{r}_{c}",
                    disabled=(not my_turn) or (val != ""),
                    use_container_width=True,
                ):
                    board[r][c] = letter
                    new_lines = _count_new_sos(board, r, c, letter)
                    if new_lines:
                        sos_scores[my_pid] = sos_scores.get(my_pid, 0) + len(new_lines)
                        state["last_sos"] = [pt for line in new_lines for pt in line]
                    else:
                        state["last_sos"] = []

                    if all(board[rr][cc] != "" for rr in range(5) for cc in range(5)):
                        room["winner"] = leaders_from_score_dict(sos_scores)
                    elif not new_lines:
                        room["turn_idx"] = (room["turn_idx"] + 1) % len(players)
                    st.rerun()
