import streamlit as st


def _valid_moves_for(board, sr, sc, is_p1):
    piece = board[sr][sc]
    if not piece:
        return {}
    is_king = piece in ("🟥", "⬛")
    enemy_pieces = ("⚫", "⬛") if is_p1 else ("🔴", "🟥")
    forward = -1 if is_p1 else 1
    row_dirs = [-1, 1] if is_king else [forward]

    moves = {}
    for dr in row_dirs:
        for dc in (-1, 1):
            nr, nc = sr + dr, sc + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == "":
                moves[(nr, nc)] = None
            jr, jc = sr + 2 * dr, sc + 2 * dc
            if (
                0 <= jr < 6
                and 0 <= jc < 6
                and board[jr][jc] == ""
                and board[nr][nc] in enemy_pieces
            ):
                moves[(jr, jc)] = (nr, nc)
    return moves


def render_checkers(room, my_pid, my_turn):
    st.markdown("""
    <style>
    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"],
    div[data-testid="column"] div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    div[data-testid="stButton"] button {
        height: 54px !important;
        min-height: 54px !important;
        padding: 0 !important;
        font-size: 1.35rem !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    p1_id, p2_id = room["players"][0], room["players"][1]
    is_p1 = my_pid == p1_id
    names = room["names"]
    board = room["state"]["board"]
    my_pieces = ("🔴", "🟥") if is_p1 else ("⚫", "⬛")
    enemy_pieces = ("⚫", "⬛") if is_p1 else ("🔴", "🟥")

    if "chk_sel" not in st.session_state:
        st.session_state.chk_sel = None

    sel = st.session_state.chk_sel
    if sel and board[sel[0]][sel[1]] not in my_pieces:
        st.session_state.chk_sel = None
        sel = None

    valid_targets = _valid_moves_for(board, sel[0], sel[1], is_p1) if (sel and my_turn) else {}

    _, center, _ = st.columns([0.9, 1.5, 0.9])
    with center:
        st.caption(
            f"🔴 = **{names[p1_id]}** · ⚫ = **{names[p2_id]}** · Click your piece, then click a `🟢` or `🎯` square."
        )

        for r in range(6):
            cols = st.columns(6)
            for c in range(6):
                cell = board[r][c]
                dark_sq = (r + c) % 2 == 1
                is_sel = sel == (r, c)

                if not dark_sq:
                    cols[c].button(" ", key=f"chk_{r}_{c}", disabled=True, use_container_width=True)
                    continue

                if is_sel:
                    label = f"[{cell}]"
                elif (r, c) in valid_targets:
                    label = "🎯" if valid_targets[(r, c)] else "🟢"
                elif cell:
                    label = cell
                else:
                    label = "▪️"

                clickable = my_turn and (cell in my_pieces or (r, c) in valid_targets)
                if cols[c].button(label, key=f"chk_{r}_{c}", disabled=not clickable, use_container_width=True):
                    if cell in my_pieces:
                        st.session_state.chk_sel = None if is_sel else (r, c)
                        st.rerun()
                    elif (r, c) in valid_targets:
                        sr, sc = sel
                        jumped = valid_targets[(r, c)]
                        board[r][c], board[sr][sc] = board[sr][sc], ""
                        if jumped:
                            board[jumped[0]][jumped[1]] = ""
                        if is_p1 and r == 0:
                            board[r][c] = "🟥"
                        elif (not is_p1) and r == 5:
                            board[r][c] = "⬛"

                        st.session_state.chk_sel = None
                        flat = [x for row in board for x in row]
                        if not any(x in enemy_pieces for x in flat):
                            room["winner"] = my_pid
                        else:
                            room["turn_idx"] = 1 - room["turn_idx"]
                        st.rerun()
