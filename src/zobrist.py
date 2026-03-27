import random

PIECE_INDEX = {
    ('white', 'pawn'): 0,  ('black', 'pawn'): 1,
    ('white', 'rook'): 2,  ('black', 'rook'): 3,
    ('white', 'knight'): 4, ('black', 'knight'): 5,
    ('white', 'bishop'): 6, ('black', 'bishop'): 7,
    ('white', 'queen'): 8, ('black', 'queen'): 9,
    ('white', 'king'): 10, ('black', 'king'): 11,
}
random.seed(42)

PIECEKEYS = [[random.getrandbits(64) for _ in range(64)] for _ in range(12)]

SIDEKEY = random.getrandbits(64)

CASTLEKEYS = [random.getrandbits(64) for _ in range(4)]

ENPASSANTKEYS = [random.getrandbits(64) for _ in range(8)]

def pieceZobristIndex(colour, name):
    return PIECE_INDEX[(colour, name)]

def squareIndex(row, col):
    return row * 8 + col
