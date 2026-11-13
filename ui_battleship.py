import random
import streamlit as st
from game_logic import FLEET_SPECS

ROWS = "ABCDEFGHIJ"


def _occupied(ships_dict):
    return {pt for coords in ships_dict.values() for pt in coords}


def _place_random(ships_dict):
    ships_dict.clear()
    for name, size in FLEET_SPECS:
        while True:
            horiz = random.choice([True, False])
            r = random.randint(0, 9 if horiz else 10 - size)
            c = random.randint(0, 10 - size if horiz else 9)
            coords = [(r, c + i) if horiz else (r + i, c) for i in range(size)]
            if not (set(coords) & _occupied(ships_dict)):
                ships_dict[name] = coords
                break


def _draw_ocean(ships_dict, shots_taken):
    occ = _occupied(ships_dict)
    lines = ["`   1 2 3 4 5 6 7 8 9 10`"]
    for r in range(10):
        row_icons = []
        for c in range(10):
            pt = (r, c)
            if pt in occ and pt in shots_taken:
                row_icons.append("🔥")
            elif pt in occ:
                row_icons.append("🚢")
            elif pt in shots_taken:
                row_icons.append("⚪")
            else:
                row_icons.append("🟦")
        lines.append(f"`{ROWS[r]} ` " + "".join(row_icons))
    st.markdown("  \n".join(lines))


def render_battleship(room, role, my_turn):
    state = room["state"]
    enemy = "P2" if role == "P1" else "P1"
    my_ships = state["ships"][role]

    # --- PHASE 1: PLACE YOUR FLEET ---
    if state["phase"] == "SETUP":
        st.subheader("⚓ Phase 1: Position Your Fleet (10×10 Grid)")
        if state["ready"][role]:
            st.success("✅ Fleet locked in! Waiting for opponent to finish placing ships...")
            _draw_ocean(my_ships, set())
            return

        left, right = st.columns([1, 1.3])
        with left:
            ship_names = [f"{n} ({s})" for n, s in FLEET_SPECS]
            choice = st.selectbox("Select Ship to Place", ship_names)
            name, size = choice.split(" (")[0], int(choice.split("(")[1][0])
            c1, c2, c3 = st.columns(3)
            row_ch = c1.selectbox("Row", list(ROWS))
            col_num = c2.selectbox("Col", list(range(1, 11)))
            orient = c3.radio("Direction", ["Horizontal", "Vertical"])

            if st.button("📍 Place / Move Ship", use_container_width=True):
                r, c = ROWS.index(row_ch), col_num - 1
                coords = [(r, c + i) if orient == "Horizontal" else (r + i, c) for i in range(size)]
                other_cells = {pt for k, v in my_ships.items() if k != name for pt in v}
                if any(x > 9 or y > 9 for x, y in coords):
                    st.error("Ship goes off the 10×10 board!")
                elif set(coords) & other_cells:
                    st.error("Overlaps another ship!")
                else:
                    my_ships[name] = coords
                    st.rerun()

            if st.button("🎲 Randomize All Ships", use_container_width=True):
                _place_random(my_ships)
                st.rerun()

            placed = len(my_ships)
            st.write(f"**Ships Placed:** {placed} / 5")
            if st.button("🚀 Lock In Fleet & Start", disabled=(placed < 5), type="primary", use_container_width=True):
                state["ready"][role] = True
                if state["ready"]["P1"] and state["ready"]["P2"]:
                    state["phase"] = "BATTLE"
                st.rerun()

        with right:
            st.markdown("**Your Ocean Board**")
            _draw_ocean(my_ships, set())
        return

    # --- PHASE 2: BATTLE ---
    if state["last_event"]:
        st.warning(f"📢 **Last Shot:** {state['last_event']}")
    if room["winner"] is None:
        if my_turn:
            st.success("🟢 **Your Turn!** Select a coordinate to fire.")
        else:
            st.info(f"⏳ Waiting for **{enemy}** to fire...")

    my_shots = state["shots"][role]
    enemy_ships = state["ships"][enemy]
    enemy_occ = _occupied(enemy_ships)
    sunk_names = [n for n, coords in enemy_ships.items() if set(coords).issubset(my_shots)]

    left, right = st.columns([1.4, 1])
    with left:
        st.markdown(f"**🎯 Target Radar** — Enemy Ships Sunk: **{len(sunk_names)} / 5**")
        if sunk_names:
            st.caption("Sunk: " + ", ".join(sunk_names))

        # Coordinate selector + Fire button + 10x10 visual radar
        fc1, fc2, fc3 = st.columns([1, 1, 1.5])
        t_row = fc1.selectbox("Target Row", list(ROWS), key="t_row")
        t_col = fc2.selectbox("Target Col", list(range(1, 11)), key="t_col")
        target = (ROWS.index(t_row), t_col - 1)

        if fc3.button("🔥 FIRE!", disabled=(not my_turn or target in my_shots), type="primary", use_container_width=True):
            my_shots.add(target)
            coord_label = f"{t_row}{t_col}"
            if target in enemy_occ:
                hit_ship = next(n for n, coords in enemy_ships.items() if target in coords)
                if set(enemy_ships[hit_ship]).issubset(my_shots):
                    state["last_event"] = f"{role} fired at {coord_label} — 💥 HIT & SUNK {enemy}'s {hit_ship}!"
                else:
                    state["last_event"] = f"{role} fired at {coord_label} — 💥 HIT!"
            else:
                state["last_event"] = f"{role} fired at {coord_label} — 💦 MISS!"

            if enemy_occ.issubset(my_shots):
                room["winner"] = role
            else:
                room["turn"] = enemy
            st.rerun()

        # Render 10x10 Target Radar Grid
        r_lines = ["`   1 2 3 4 5 6 7 8 9 10`"]
        for r in range(10):
            icons = [
                ("💥" if (r, c) in enemy_occ else "⚪") if (r, c) in my_shots else "🌊"
                for c in range(10)
            ]
            r_lines.append(f"`{ROWS[r]} ` " + "".join(icons))
        st.markdown("  \n".join(r_lines))

    with right:
        st.markdown("**🚢 Your Fleet Status**")
        _draw_ocean(my_ships, state["shots"][enemy])
