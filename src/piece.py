import os
import pygame
import math

class Piece:
    def __init__(self, name, colour, value, image = None, imageRect = None):
        self.name = name
        self.colour = colour
        self.value = value
        self.image = image
        self.imageRect = imageRect
        self.setImage()
        self.moves = []
        self.moved = False

    def setImage(self):
        self.image = pygame.image.load(os.path.join("..", "figureImages/" + self.colour + "-" + self.name + ".png"))

    def addMove(self, move):
        self.moves.append(move)

    def clearMoves(self):
        self.moves = []


class Pawn(Piece):
    def __init__(self, colour):
        self.direction = -1 if colour == 'white' else 1  # Pawns can only move in 1 direction depending on their colour
        super().__init__('pawn', colour, 1)

class Rook(Piece):
    def __init__(self, colour):
        super().__init__('rook', colour, 5)

class Knight(Piece):
    def __init__(self, colour):
        super().__init__('knight', colour, 3)

class Bishop(Piece):
    def __init__(self, colour):
        super().__init__('bishop', colour, 3)

class Queen(Piece):
    def __init__(self, colour):
        super().__init__('queen', colour, 9)

class King(Piece):
    def __init__(self, colour):
        super().__init__('king', colour, math.inf)