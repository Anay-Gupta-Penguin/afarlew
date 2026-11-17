import streamlit as st
from game_logic import check_c4_winner


def render_c4(room, role, my_turn):
    piece = "🔴" if role == "P1" else "🟡"
    board = room["state"]["board"]

    drop_cols = st.columns(7)
    for c in range(7):
        # Check top cell of column c (board[0][c]), not board[c]
        disabled = (not my_turn) or (board[0][c] != "")
        if drop_cols[c].button(f"⬇️ {c+1}", key=f"c4_{c}", disabled=disabled, use_container_width=True):
            for r in range(5, -1, -1):
                if board[r][c] == "":
                    board[r][c] = piece
                    break
            win = check_c4_winner(board)
            if win == "🔴":
                room["winner"] = "P1"
            elif win == "🟡":
                room["winner"] = "P2"
            elif win == "DRAW":
                room["winner"] = "DRAW"
            else:
                room["turn"] = "P2" if role == "P1" else "P1"
            st.rerun()

    for r in range(6):
        row_str = " ".join(board[r][c] if board[r][c] else "⚪" for c in range(7))
        st.markdown(f"<h3 style='text-align:center; margin:0; letter-spacing:4px;'>{row_str}</h3>", unsafe_allow_html=True)
