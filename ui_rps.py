import streamlit as st

BEATS = {"🪨 Rock": "✂️ Scissors", "📄 Paper": "🪨 Rock", "✂️ Scissors": "📄 Paper"}


def render_rps(room, role):
    picks = room["state"]["picks"]
    enemy = "P2" if role == "P1" else "P1"

    if picks[role] is None:
        st.write("**Pick your move (hidden from opponent):**")
        cols = st.columns(3)
        for idx, move in enumerate(["🪨 Rock", "📄 Paper", "✂️ Scissors"]):
            if cols[idx].button(move, key=f"rps_{move}", use_container_width=True):
                picks[role] = move
                if picks["P1"] and picks["P2"]:
                    p1_m, p2_m = picks["P1"], picks["P2"]
                    if p1_m == p2_m:
                        room["winner"] = "DRAW"
                    elif BEATS[p1_m] == p2_m:
                        room["winner"] = "P1"
                    else:
                        room["winner"] = "P2"
                    room["scores"][room["winner"]] = room["scores"].get(room["winner"], 0) + 1
                st.rerun()
    elif room["winner"] is None:
        st.info(f"You locked in **{picks[role]}**. Waiting for **{enemy}** to pick...")
    else:
        st.write(f"**P1 picked:** {picks['P1']}  |  **P2 picked:** {picks['P2']}")
