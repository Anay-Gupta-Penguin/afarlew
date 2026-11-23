import streamlit as st
from game_logic import leaders_from_score_dict


def _claim_line_and_check(state, my_pid):
    h_lines = state["h_lines"]
    v_lines = state["v_lines"]
    boxes = state["boxes"]
    completed = 0

    for r in range(3):
        for c in range(3):
            if boxes[r][c] is None:
                if h_lines[r][c] and h_lines[r + 1][c] and v_lines[r][c] and v_lines[r][c + 1]:
                    boxes[r][c] = my_pid
                    state["box_scores"][my_pid] = state["box_scores"].get(my_pid, 0) + 1
                    completed += 1
    return completed


def render_dots(room, my_pid, my_turn):
    st.markdown("""
    <style>
    div[data-testid="stColumn"] div[data-testid="stVerticalBlock"],
    div[data-testid="column"] div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    div[data-testid="stButton"] button {
        height: 38px !important;
        min-height: 38px !important;
        padding: 0 !important;
        font-size: 1rem !important;
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    players = room["players"]
    names = room["names"]
    badges = room["badges"]
    state = room["state"]
    h_lines = state["h_lines"]
    v_lines = state["v_lines"]
    boxes = state["boxes"]
    box_scores = state["box_scores"]

    _, center, _ = st.columns([0.9, 1.5, 0.9])
    with center:
        tally = " · ".join(f"{badges[p]} {names[p]}: **{box_scores.get(p, 0)}**" for p in players)
        st.markdown(f"**Boxes Captured:** {tally}")
        st.caption("Click any `·` edge between dots to draw a line. Complete a box to score & go again!")

        col_widths = [0.35, 1.1, 0.35, 1.1, 0.35, 1.1, 0.35]

        for r in range(4):
            h_cols = st.columns(col_widths, vertical_alignment="center")
            for c in range(4):
                h_cols[c * 2].markdown(
                    "<div style='text-align:center;font-size:14px;'>⚫</div>",
                    unsafe_allow_html=True,
                )
                if c < 3:
                    owner = h_lines[r][c]
                    label = f"{badges[owner]}━━" if owner else "· · ·"
                    if h_cols[c * 2 + 1].button(
                        label,
                        key=f"dot_h_{r}_{c}",
                        disabled=(not my_turn) or (owner is not None),
                        use_container_width=True,
                    ):
                        h_lines[r][c] = my_pid
                        gained = _claim_line_and_check(state, my_pid)
                        if all(boxes[br][bc] is not None for br in range(3) for bc in range(3)):
                            room["winner"] = leaders_from_score_dict(box_scores)
                        elif gained == 0:
                            room["turn_idx"] = (room["turn_idx"] + 1) % len(players)
                        st.rerun()

            if r < 3:
                v_cols = st.columns(col_widths, vertical_alignment="center")
                for c in range(4):
                    v_owner = v_lines[r][c]
                    v_label = badges[v_owner] if v_owner else "⋮"
                    if v_cols[c * 2].button(
                        v_label,
                        key=f"dot_v_{r}_{c}",
                        disabled=(not my_turn) or (v_owner is not None),
                        use_container_width=True,
                    ):
                        v_lines[r][c] = my_pid
                        gained = _claim_line_and_check(state, my_pid)
                        if all(boxes[br][bc] is not None for br in range(3) for bc in range(3)):
                            room["winner"] = leaders_from_score_dict(box_scores)
                        elif gained == 0:
                            room["turn_idx"] = (room["turn_idx"] + 1) % len(players)
                        st.rerun()

                    if c < 3:
                        b_owner = boxes[r][c]
                        box_html = (
                            f"<div style='text-align:center;background:#1e293b;border-radius:6px;"
                            f"padding:6px 0;font-size:18px;'>{badges[b_owner]}</div>"
                            if b_owner
                            else "<div style='text-align:center;color:#475569;font-size:12px;'>□</div>"
                        )
                        v_cols[c * 2 + 1].markdown(box_html, unsafe_allow_html=True)
