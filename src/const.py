import pygame
import os

# screen dimensions
WIDTH = 800
HEIGHT = 800

# board dimensions
COLS = 8
ROWS = 8
SquareSize = WIDTH // COLS

# move directions
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
UP_LEFT = (-1, -1)
UP_RIGHT = (-1, 1)
DOWN_LEFT = (1, -1)
DOWN_RIGHT = (1, 1)

ROOK_DIRECTIONS = [UP, DOWN, LEFT, RIGHT]
BISHOP_DIRECTIONS = [UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT]
QUEEN_DIRECTIONS = ROOK_DIRECTIONS + BISHOP_DIRECTIONS
KING_DIRECTIONS = QUEEN_DIRECTIONS
KNIGHT_DIRECTIONS = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]

# image paths for promotion
IMAGES = {}
pieces = ['white-queen', 'white-rook', 'white-bishop', 'white-knight', 'black-queen', 'black-rook', 'black-bishop', 'black-knight']
for piece in pieces:
    IMAGES[piece] = pygame.image.load(os.path.join("..", "figureImages/" + piece + ".png"))
