import streamlit as st
from game_logic import check_ttt_winner


def render_ttt(room, my_pid, my_turn):
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        height: 82px !important;
        min-height: 82px !important;
        font-size: 2rem !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    p1_id, p2_id = room["players"][0], room["players"][1]
    names = room["names"]
    my_symbol = "❌" if my_pid == p1_id else "⭕"
    state = room["state"]
    board = state["board"]
    win_line = state.get("win_line", [])

    _, center, _ = st.columns([1.3, 1, 1.3])
    with center:
        st.caption(f"❌ = **{names[p1_id]}** · ⭕ = **{names[p2_id]}**")
        for r in range(3):
            cols = st.columns(3)
            for c in range(3):
                idx = r * 3 + c
                cell = board[idx]
                label = f"✅{cell}" if idx in win_line else (cell if cell else " ")
                disabled = (not my_turn) or (cell != "")
                if cols[c].button(label, key=f"ttt_{idx}", disabled=disabled, use_container_width=True):
                    board[idx] = my_symbol
                    win_sym, line = check_ttt_winner(board)
                    state["win_line"] = line
                    if win_sym == "❌":
                        room["winner"] = p1_id
                    elif win_sym == "⭕":
                        room["winner"] = p2_id
                    elif win_sym == "DRAW":
                        room["winner"] = "DRAW"
                    else:
                        room["turn_idx"] = 1 - room["turn_idx"]
                    st.rerun()
