import streamlit as st


def render_checkers(room, role, my_turn):
    board = room["state"]["board"]
    my_pieces = ("🔴", "🟥") if role == "P1" else ("⚫", "⬛")
    enemy_pieces = ("⚫", "⬛") if role == "P1" else ("🔴", "🟥")

    if "chk_sel" not in st.session_state:
        st.session_state.chk_sel = None

    st.caption("🔴 = P1 | ⚫ = P2 | Click your piece, then click a diagonal square to move or jump.")

    for r in range(6):
        cols = st.columns(6)
        for c in range(6):
            cell = board[r][c]
            is_sel = st.session_state.chk_sel == (r, c)
            label = f"[{cell}]" if is_sel else (cell if cell else ("▪️" if (r + c) % 2 == 1 else "▫️"))

            if cols[c].button(label, key=f"chk_{r}_{c}", disabled=not my_turn, use_container_width=True):
                if cell in my_pieces:
                    st.session_state.chk_sel = (r, c)
                    st.rerun()
                elif st.session_state.chk_sel and cell == "" and (r + c) % 2 == 1:
                    sr, sc = st.session_state.chk_sel
                    dr, dc = r - sr, c - sc
                    forward = -1 if role == "P1" else 1
                    is_king = board[sr][sc] in ("🟥", "⬛")
                    valid_dir = is_king or (dr * forward > 0)

                    moved = False
                    if abs(dr) == 1 and abs(dc) == 1 and valid_dir:
                        board[r][c], board[sr][sc] = board[sr][sc], ""
                        moved = True
                    elif abs(dr) == 2 and abs(dc) == 2 and valid_dir:
                        mr, mc = sr + dr // 2, sc + dc // 2
                        if board[mr][mc] in enemy_pieces:
                            board[r][c], board[sr][sc], board[mr][mc] = board[sr][sc], "", ""
                            moved = True

                    if moved:
                        if role == "P1" and r == 0:
                            board[r][c] = "🟥"
                        elif role == "P2" and r == 5:
                            board[r][c] = "⬛"
                        st.session_state.chk_sel = None
                        flat = [x for row in board for x in row]
                        if not any(x in enemy_pieces for x in flat):
                            room["winner"] = role
                            room["scores"][role] += 1
                        else:
                            room["turn"] = "P2" if role == "P1" else "P1"
                        st.rerun()
