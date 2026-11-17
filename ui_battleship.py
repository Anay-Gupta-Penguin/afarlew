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


def _draw_aligned_ocean(ships_dict, shots_taken):
    occ = _occupied(ships_dict)
    cells = ['<div style="display:grid;grid-template-columns:24px repeat(10,1fr);gap:3px;text-align:center;font-family:monospace;font-size:13px;align-items:center;">']
    cells.append("<div></div>" + "".join(f"<div><b>{c}</b></div>" for c in range(1, 11)))
    for r in range(10):
        cells.append(f"<div><b>{ROWS[r]}</b></div>")
        for c in range(10):
            pt = (r, c)
            if pt in occ and pt in shots_taken:
                icon, bg = "🔥", "#7f1d1d"
            elif pt in occ:
                icon, bg = "🚢", "#1e3a8a"
            elif pt in shots_taken:
                icon, bg = "⚪", "#334155"
            else:
                icon, bg = "🟦", "#0f172a"
            cells.append(f'<div style="background:{bg};border-radius:4px;padding:3px 0;font-size:15px;">{icon}</div>')
    cells.append("</div>")
    st.markdown("".join(cells), unsafe_allow_html=True)


def render_battleship(room, role, my_turn):
    # Compact button styling so 10x10 clickable grids fit cleanly without scrolling
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        padding: 0.15rem 0 !important;
        min-height: 2rem !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    state = room["state"]
    enemy = "P2" if role == "P1" else "P1"
    my_ships = state["ships"][role]

    # --- PHASE 1: PLACE YOUR FLEET ---
    if state["phase"] == "SETUP":
        st.subheader("⚓ Phase 1: Position Your Fleet")
        if state["ready"][role]:
            st.success("✅ Fleet locked in! Waiting for opponent to finish placing ships...")
            _draw_aligned_ocean(my_ships, set())
            return

        left, right = st.columns([1, 1.45])
        with left:
            unplaced = [n for n, _ in FLEET_SPECS if n not in my_ships]
            default_idx = next((i for i, (n, _) in enumerate(FLEET_SPECS) if unplaced and n == unplaced[0]), 0)
            ship_labels = [f"{'✅' if n in my_ships else '⬜'} {n} ({s})" for n, s in FLEET_SPECS]
            choice = st.selectbox("1. Select Ship", ship_labels, index=default_idx)
            sel_idx = ship_labels.index(choice)
            name, size = FLEET_SPECS[sel_idx]

            orient = st.radio("2. Direction", ["Horizontal", "Vertical"], horizontal=True)
            st.caption("3. Click any square on the grid to place or move the selected ship.")

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
            st.markdown("**Your Ocean Board** *(Click a square to place)*")
            occ = _occupied(my_ships)
            hdr = st.columns([0.6] + [1] * 10)
            hdr[0].markdown("")
            for c in range(10):
                hdr[c + 1].markdown(f"<div style='text-align:center;font-weight:700;font-size:12px;'>{c+1}</div>", unsafe_allow_html=True)

            for r in range(10):
                row_cols = st.columns([0.6] + [1] * 10)
                row_cols[0].markdown(f"<div style='text-align:center;font-weight:700;font-size:12px;padding-top:6px;'>{ROWS[r]}</div>", unsafe_allow_html=True)
                for c in range(10):
                    icon = "🚢" if (r, c) in occ else "🟦"
                    if row_cols[c + 1].button(icon, key=f"setup_{role}_{r}_{c}", use_container_width=True):
                        coords = [(r, c + i) if orient == "Horizontal" else (r + i, c) for i in range(size)]
                        other_cells = {pt for k, v in my_ships.items() if k != name for pt in v}
                        if any(x > 9 or y > 9 for x, y in coords):
                            st.toast(f"{name} goes off the edge from {ROWS[r]}{c+1}!", icon="⚠️")
                        elif set(coords) & other_cells:
                            st.toast("That overlaps another ship!", icon="⚠️")
                        else:
                            my_ships[name] = coords
                            st.rerun()
        return

    # --- PHASE 2: BATTLE ---
    if state["last_event"]:
        st.warning(f"📢 **Last Shot:** {state['last_event']}")
    if room["winner"] is None:
        if my_turn:
            st.success("🟢 **Your Turn!** Click any `🌊` square on the Target Radar to fire.")
        else:
            st.info(f"⏳ Waiting for **{enemy}** to fire...")

    my_shots = state["shots"][role]
    enemy_ships = state["ships"][enemy]
    enemy_occ = _occupied(enemy_ships)
    sunk_names = [n for n, coords in enemy_ships.items() if set(coords).issubset(my_shots)]

    left, right = st.columns([1.45, 1])
    with left:
        st.markdown(f"**🎯 Target Radar** — Enemy Ships Sunk: **{len(sunk_names)} / 5**")
        if sunk_names:
            st.caption("Sunk: " + ", ".join(sunk_names))

        hdr = st.columns([0.6] + [1] * 10)
        hdr[0].markdown("")
        for c in range(10):
            hdr[c + 1].markdown(f"<div style='text-align:center;font-weight:700;font-size:12px;'>{c+1}</div>", unsafe_allow_html=True)

        for r in range(10):
            row_cols = st.columns([0.6] + [1] * 10)
            row_cols[0].markdown(f"<div style='text-align:center;font-weight:700;font-size:12px;padding-top:6px;'>{ROWS[r]}</div>", unsafe_allow_html=True)
            for c in range(10):
                target = (r, c)
                already_shot = target in my_shots
                icon = ("💥" if target in enemy_occ else "⚪") if already_shot else "🌊"
                if row_cols[c + 1].button(
                    icon,
                    key=f"fire_{role}_{r}_{c}",
                    disabled=(not my_turn or already_shot),
                    use_container_width=True,
                ):
                    my_shots.add(target)
                    coord_label = f"{ROWS[r]}{c+1}"
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

    with right:
        st.markdown("**🚢 Your Fleet Status**")
        _draw_aligned_ocean(my_ships, state["shots"][enemy])
