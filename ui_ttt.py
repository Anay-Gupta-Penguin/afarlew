import streamlit as st
from game_logic import check_ttt_winner


def render_ttt(room, role, my_turn):
    symbol = "X" if role == "P1" else "O"
    board = room["state"]["board"]

    for r in range(3):
        cols = st.columns(3)
        for c in range(3):
            idx = r * 3 + c
            label = board[idx] if board[idx] else " "
            disabled = (not my_turn) or (board[idx] != "")
            if cols[c].button(label, key=f"ttt_{idx}", disabled=disabled, use_container_width=True):
                board[idx] = symbol
                win = check_ttt_winner(board)
                if win == "X":
                    room["winner"] = "P1"
                elif win == "O":
                    room["winner"] = "P2"
                elif win == "DRAW":
                    room["winner"] = "DRAW"
                else:
                    room["turn"] = "P2" if role == "P1" else "P1"
                st.rerun()
