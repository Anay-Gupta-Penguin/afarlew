import random


def init_game_state(game_type):
    if game_type == "Tic-Tac-Toe":
        return {"board": [""] * 9}
    if game_type == "Connect 4":
        return {"board": [["" for _ in range(7)] for _ in range(6)]}
    if game_type == "Battleship":
        grid = [(r, c) for r in range(5) for c in range(5)]
        return {
            "ships": {"P1": set(random.sample(grid, 3)), "P2": set(random.sample(grid, 3))},
            "shots": {"P1": set(), "P2": set()},
        }
    if game_type == "Rock Paper Scissors":
        return {"picks": {"P1": None, "P2": None}}
    if game_type == "Checkers":
        board = [["" for _ in range(6)] for _ in range(6)]
        for r in range(2):
            for c in range(6):
                if (r + c) % 2 == 1:
                    board[r][c] = "⚫"  # P2 pieces at top
        for r in range(4, 6):
            for c in range(6):
                if (r + c) % 2 == 1:
                    board[r][c] = "🔴"  # P1 pieces at bottom
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
    return "DRAW" if all(b[c] != "" for c in range(7)) else None
