import streamlit as st
from game_logic import check_c4_winner


def render_c4(room, my_pid, my_turn):
    st.markdown("""
    <style>
    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"],
    div[data-testid="column"] div[data-testid="stVerticalBlock"] {
        gap: 0.25rem !important;
    }
    div[data-testid="stButton"] button {
        height: 48px !important;
        min-height: 48px !important;
        padding: 0 !important;
        font-size: 1.45rem !important;
        background-color: #172554 !important;
        border: 1px solid #1d4ed8 !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    p1_id, p2_id = room["players"][0], room["players"][1]
    names = room["names"]
    my_piece = "🔴" if my_pid == p1_id else "🟡"
    state = room["state"]
    board = state["board"]
    last_move = state.get("last_move")
    win_cells = set(state.get("win_cells", []))

    _, center, _ = st.columns([0.85, 1.6, 0.85])
    with center:
        st.caption(f"🔴 = **{names[p1_id]}** · 🟡 = **{names[p2_id]}** · Click any square in a column to drop your disc.")

        hdr = st.columns(7)
        for c in range(7):
            hdr[c].markdown(
                f"<div style='text-align:center;font-weight:700;font-size:13px;padding-bottom:12px;'>{c+1}</div>",
                unsafe_allow_html=True,
            )

        for r in range(6):
            cols = st.columns(7)
            for c in range(7):
                cell = board[r][c]
                if (r, c) in win_cells:
                    label = "🌟" if cell == "🟡" else "💥"
                elif (r, c) == last_move:
                    label = f"[{cell}]"
                elif cell:
                    label = cell
                else:
                    label = "⚫"

                col_full = board[0][c] != ""
                if cols[c].button(
                    label,
                    key=f"c4_{r}_{c}",
                    disabled=(not my_turn) or col_full,
                    use_container_width=True,
                ):
                    for drop_r in range(5, -1, -1):
                        if board[drop_r][c] == "":
                            board[drop_r][c] = my_piece
                            state["last_move"] = (drop_r, c)
                            break
                    win_piece, w_cells = check_c4_winner(board)
                    state["win_cells"] = w_cells
                    if win_piece == "🔴":
                        room["winner"] = p1_id
                    elif win_piece == "🟡":
                        room["winner"] = p2_id
                    elif win_piece == "DRAW":
                        room["winner"] = "DRAW"
                    else:
                        room["turn_idx"] = 1 - room["turn_idx"]
                    st.rerun()
