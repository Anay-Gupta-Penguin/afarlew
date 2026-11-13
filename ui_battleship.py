import streamlit as st


def render_battleship(room, role, my_turn):
    enemy = "P2" if role == "P1" else "P1"
    state = room["state"]
    my_shots, enemy_ships = state["shots"][role], state["ships"][enemy]
    my_ships, enemy_shots = state["ships"][role], state["shots"][enemy]

    st.write(f"**Enemy Ships Sunk:** {len(my_shots & enemy_ships)} / 3")
    left, right = st.columns(2)

    with left:
        st.markdown("**🎯 Target Radar**")
        for r in range(5):
            cols = st.columns(5)
            for c in range(5):
                coord = (r, c)
                icon = ("💥" if coord in enemy_ships else "💦") if coord in my_shots else "🌊"
                if cols[c].button(icon, key=f"bs_{r}_{c}", disabled=(not my_turn or coord in my_shots), use_container_width=True):
                    my_shots.add(coord)
                    if len(my_shots & enemy_ships) == 3:
                        room["winner"] = role
                    else:
                        room["turn"] = enemy
                    st.rerun()

    with right:
        st.markdown("**🚢 Your Fleet**")
        for r in range(5):
            cells = [
                "🔥" if (r, c) in my_ships and (r, c) in enemy_shots else
                "🚢" if (r, c) in my_ships else
                "💦" if (r, c) in enemy_shots else "🟦"
                for c in range(5)
            ]
            st.markdown(f"<div style='font-size:24px; letter-spacing:6px;'>{''.join(cells)}</div>", unsafe_allow_html=True)
