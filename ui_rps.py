import streamlit as st

BEATS = {"🪨 Rock": "✂️ Scissors", "📄 Paper": "🪨 Rock", "✂️ Scissors": "📄 Paper"}


def render_rps(room, my_pid):
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        height: 76px !important;
        min-height: 76px !important;
        font-size: 1.25rem !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    players = room["players"]
    names = room["names"]
    badges = room["badges"]
    picks = room["state"]["picks"]

    for p in players:
        picks.setdefault(p, None)

    status_cols = st.columns(len(players))
    for idx, p in enumerate(players):
        locked = picks[p] is not None
        status_cols[idx].markdown(
            f"<div style='text-align:center;padding:8px;border-radius:8px;background:#1e293b;'>"
            f"<b>{badges[p]} {names[p]}</b><br>{'✅ Locked In' if locked else '⏳ Picking...'}</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    if picks[my_pid] is None and room["winner"] is None:
        st.markdown("**Pick your move (hidden until everyone locks in):**")
        cols = st.columns(3)
        for idx, move in enumerate(["🪨 Rock", "📄 Paper", "✂️ Scissors"]):
            if cols[idx].button(move, key=f"rps_{my_pid}_{move}", use_container_width=True):
                picks[my_pid] = move
                if all(picks[p] is not None for p in players):
                    unique_moves = list({picks[p] for p in players})
                    if len(unique_moves) != 2:
                        room["winner"] = "DRAW"
                    else:
                        m1, m2 = unique_moves[0], unique_moves[1]
                        win_move = m1 if BEATS[m1] == m2 else m2
                        winners = [p for p in players if picks[p] == win_move]
                        room["winner"] = winners[0] if len(winners) == 1 else winners
                st.rerun()
    elif room["winner"] is None:
        st.info(f"You locked in **{picks[my_pid]}**. Waiting for the remaining players...")
    else:
        st.subheader("🃏 Round Reveal")
        rev_cols = st.columns(len(players))
        for idx, p in enumerate(players):
            is_win = (room["winner"] == p) or (
                isinstance(room["winner"], list) and p in room["winner"]
            )
            border = "2px solid #22c55e" if is_win else "1px solid #334155"
            rev_cols[idx].markdown(
                f"<div style='text-align:center;padding:14px;border-radius:10px;background:#0f172a;border:{border};'>"
                f"<div style='font-size:14px;'><b>{badges[p]} {names[p]}</b></div>"
                f"<div style='font-size:26px;margin-top:6px;'>{picks[p]}</div>"
                f"{'<div style=\"color:#4ade80;font-weight:700;margin-top:4px;\">🏆 WINNER</div>' if is_win else ''}"
                f"</div>",
                unsafe_allow_html=True,
            )
