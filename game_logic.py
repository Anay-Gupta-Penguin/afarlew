FLEET_SPECS = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2),
]


def init_game_state(game_type):
    if game_type == "Tic-Tac-Toe":
        return {"board": [""] * 9}
    if game_type == "Connect 4":
        return {"board": [["" for _ in range(7)] for _ in range(6)]}
    if game_type == "Battleship":
        return {
            "phase": "SETUP",
            "ships": {"P1": {}, "P2": {}},
            "ready": {"P1": False, "P2": False},
            "shots": {"P1": set(), "P2": set()},
            "last_event": "",
        }
    if game_type == "Rock Paper Scissors":
        return {"picks": {"P1": None, "P2": None}}
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


def check_ttt_winner(b):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for x, y, z in wins:
        if b[x] and b[x] == b[y] == b[z]:
            return b[x]
    return "DRAW" if "" not in b else None


def check_c4_winner(b):
    for r in range(6):
        for c in range(7):
            p = b[r][c]
            if not p:
                continue
            if c + 3 < 7 and p == b[r][c+1] == b[r][c+2] == b[r][c+3]:
                return p
            if r + 3 < 6 and p == b[r+1][c] == b[r+2][c] == b[r+3][c]:
                return p
            if r + 3 < 6 and c + 3 < 7 and p == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3]:
                return p
            if r - 3 >= 0 and c + 3 < 7 and p == b[r-1][c+1] == b[r-2][c+2] == b[r-3][c+3]:
                return p
    # Check top row (row 0) for full columns
    return "DRAW" if all(b[0][c] != "" for c in range(7)) else None
