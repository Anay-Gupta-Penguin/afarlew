import random

GAMES = {
    "1v1.LOL": {"min": 1, "max": 4, "desc": "1–4 Players · 3D Build Fight, Turbo-Build & Edits"},
    "Battle Royale": {"min": 1, "max": 8, "desc": "1–8 Players · 3D Fortnite Island, Chests & Storm"},
    "Connect 4": {"min": 2, "max": 2, "desc": "2 Players · Drop 4 in a row"},
    "Tic-Tac-Toe": {"min": 2, "max": 2, "desc": "2 Players · Classic 3×3 grid"},
    "Checkers": {"min": 2, "max": 2, "desc": "2 Players · Diagonal jumps & kings"},
    "Battleship": {"min": 2, "max": 2, "desc": "2 Players · 10×10 naval combat"},
    "Dots & Boxes": {"min": 2, "max": 4, "desc": "2–4 Players · Claim lines & capture boxes"},
    "SOS": {"min": 2, "max": 4, "desc": "2–4 Players · Form S-O-S lines on a 5×5 board"},
    "Memory Match": {"min": 2, "max": 6, "desc": "2–6 Players · Flip & match emoji pairs"},
    "Rock Paper Scissors": {"min": 2, "max": 8, "desc": "2–8 Players · Simultaneous Battle Royale"},
}

FLEET_SPECS = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]

MEMORY_EMOJIS = ["🚀", "🍕", "🐉", "🎸", "🌈", "⚡", "🦊", "💎", "🍩", "🛸"]
BR_SPAWNS = [(1, 1), (1, 6), (6, 1), (6, 6), (1, 3), (6, 4), (3, 1), (4, 6)]
BR_ITEM_POOL = ["💖", "⚡", "🌀"]


def is_in_storm(r, c, ring):
    return r < ring or r >= 8 - ring or c < ring or c >= 8 - ring


def _spawn_br_items(state, count=2):
    occupied = {p_pos for pid, p_pos in state["pos"].items() if state["hp"].get(pid, 0) > 0}
    occupied.update(state["items"].keys())
    ring = state["storm_ring"]
    candidates = [
        (r, c)
        for r in range(8)
        for c in range(8)
        if not is_in_storm(r, c, ring) and (r, c) not in occupied
    ]
    random.shuffle(candidates)
    for pt in candidates[:count]:
        state["items"][pt] = random.choice(BR_ITEM_POOL)


def init_game_state(game_type, player_ids):
    if game_type == "Battle Royale":
        spawns = BR_SPAWNS[: len(player_ids)]
        state = {
            "round": 1,
            "storm_ring": 0,
            "pos": {pid: spawns[i] for i, pid in enumerate(player_ids)},
            "hp": {pid: 3 for pid in player_ids},
            "moves": {pid: None for pid in player_ids},
            "items": {},
            "log": ["⚔️ Battle Royale started! Survive the shrinking storm!"],
        }
        _spawn_br_items(state, count=4)
        return state

    if game_type == "Tic-Tac-Toe":
        return {"board": [""] * 9, "win_line": []}

    if game_type == "Connect 4":
        return {
            "board": [["" for _ in range(7)] for _ in range(6)],
            "last_move": None,
            "win_cells": [],
        }

    if game_type == "Battleship":
        p1, p2 = player_ids[0], player_ids[1]
        return {
            "phase": "SETUP",
            "ships": {p1: {}, p2: {}},
            "ready": {p1: False, p2: False},
            "shots": {p1: set(), p2: set()},
            "last_event": "",
        }

    if game_type == "Rock Paper Scissors":
        return {"picks": {pid: None for pid in player_ids}}

    if game_type == "Checkers":
        board = [["" for _ in range(6)] for _ in range(6)]
        for r in range(2):
            for c in range(6):
                if (r + c) % 2 == 1:
                    board[r][c] = "⚫"
        for r in range(4, 6):
            for c in range(6):
                if (r + c) % 2 == 1:
                    board[r][c] = "🔴"
        return {"board": board}

    if game_type == "Dots & Boxes":
        return {
            "h_lines": [[None for _ in range(3)] for _ in range(4)],
            "v_lines": [[None for _ in range(4)] for _ in range(3)],
            "boxes": [[None for _ in range(3)] for _ in range(3)],
            "box_scores": {pid: 0 for pid in player_ids},
        }

    if game_type == "SOS":
        return {
            "board": [["" for _ in range(5)] for _ in range(5)],
            "sos_scores": {pid: 0 for pid in player_ids},
            "last_sos": [],
        }

    if game_type == "Memory Match":
        deck = MEMORY_EMOJIS * 2
        random.shuffle(deck)
        return {
            "cards": deck,
            "matched": set(),
            "flipped": [],
            "reveal_until": 0.0,
            "pairs": {pid: 0 for pid in player_ids},
        }


def resolve_br_round(room):
    state = room["state"]
    names = room["names"]
    badges = room["badges"]
    hp = state["hp"]
    pos = state["pos"]
    moves = state["moves"]
    events = []

    alive = [p for p in room["players"] if hp.get(p, 0) > 0]
    guarding = {p for p in alive if moves.get(p) == pos.get(p)}
    intended = {p: (moves.get(p) or pos[p]) for p in alive}

    # 1. Movement & collisions
    by_dest = {}
    for p, dest in intended.items():
        by_dest.setdefault(dest, []).append(p)

    for dest, contenders in by_dest.items():
        if len(contenders) == 1:
            pos[contenders[0]] = dest
        else:
            labels = " & ".join(f"{badges[p]} {names[p]}" for p in contenders)
            events.append(f"💥 {labels} collided!")
            for p in contenders:
                if p not in guarding:
                    hp[p] -= 1
                else:
                    events.append(f"🛡️ {badges[p]} {names[p]} blocked collision damage!")

    # 2. Item pickups
    for p in alive:
        if hp[p] <= 0:
            continue
        cur = pos[p]
        if cur in state["items"]:
            kind = state["items"].pop(cur)
            if kind == "💖":
                if hp[p] < 3:
                    hp[p] += 1
                    events.append(f"💖 {badges[p]} {names[p]} healed +1 Heart!")
                else:
                    events.append(f"💖 {badges[p]} {names[p]} picked up a Medkit (already full HP)!")
            elif kind == "⚡":
                events.append(f"⚡ {badges[p]} {names[p]} unleashed a Shockwave!")
                for other in alive:
                    if other != p and hp[other] > 0:
                        dr = pos[other][0] - cur[0]
                        dc = pos[other][1] - cur[1]
                        if abs(dr) <= 1 and abs(dc) <= 1:
                            nr = max(0, min(7, pos[other][0] + (1 if dr > 0 else (-1 if dr < 0 else 0))))
                            nc = max(0, min(7, pos[other][1] + (1 if dc > 0 else (-1 if dc < 0 else 0))))
                            pos[other] = (nr, nc)
                            if other not in guarding:
                                hp[other] -= 1
            elif kind == "🌀":
                ring = state["storm_ring"]
                taken = {pos[o] for o in alive if hp[o] > 0}
                safe = [
                    (r, c)
                    for r in range(8)
                    for c in range(8)
                    if not is_in_storm(r, c, ring) and (r, c) not in taken
                ]
                if safe:
                    pos[p] = random.choice(safe)
                events.append(f"🌀 {badges[p]} {names[p]} warped across the arena!")

    # 3. Shrink Storm every 2 rounds & apply Storm damage
    if state["round"] % 2 == 0 and state["storm_ring"] < 3:
        state["storm_ring"] += 1
        events.append("🌪️ The Storm shrunk! Safe zone is smaller!")

    for p in alive:
        if hp[p] > 0 and is_in_storm(pos[p][0], pos[p][1], state["storm_ring"]):
            hp[p] -= 1
            events.append(f"🔥 {badges[p]} {names[p]} took 1 Storm damage!")

    # 4. Eliminations
    for p in alive:
        if hp[p] <= 0:
            hp[p] = 0
            events.append(f"💀 {badges[p]} {names[p]} was eliminated!")

    if not events:
        events.append(f"Round {state['round']} ended quietly — everyone repositioned.")

    if len(state["items"]) < 3:
        _spawn_br_items(state, count=2)

    state["round"] += 1
    state["log"] = events[:6]

    still_alive = [p for p in room["players"] if hp.get(p, 0) > 0]
    state["moves"] = {p: None for p in still_alive}

    if len(still_alive) == 1:
        room["winner"] = still_alive[0]
    elif len(still_alive) == 0:
        room["winner"] = "DRAW"


def check_ttt_winner(b):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]
    for x, y, z in wins:
        if b[x] and b[x] == b[y] == b[z]:
            return b[x], [x, y, z]
    if "" not in b:
        return "DRAW", []
    return None, []


def check_c4_winner(b):
    for r in range(6):
        for c in range(7):
            p = b[r][c]
            if not p:
                continue
            if c + 3 < 7 and p == b[r][c+1] == b[r][c+2] == b[r][c+3]:
                return p, [(r, c+i) for i in range(4)]
            if r + 3 < 6 and p == b[r+1][c] == b[r+2][c] == b[r+3][c]:
                return p, [(r+i, c) for i in range(4)]
            if r + 3 < 6 and c + 3 < 7 and p == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]:
                return p, [(r+i, c+i) for i in range(4)]
            if r - 3 >= 0 and c + 3 < 7 and p == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3]:
                return p, [(r-i, c+i) for i in range(4)]
    if all(b[0][c] != "" for c in range(7)):
        return "DRAW", []
    return None, []


def leaders_from_score_dict(score_dict):
    if not score_dict:
        return "DRAW"
    top = max(score_dict.values())
    winners = [pid for pid, val in score_dict.items() if val == top]
    if len(winners) == len(score_dict) and len(winners) > 1:
        return "DRAW"
    return winners[0] if len(winners) == 1 else winners
