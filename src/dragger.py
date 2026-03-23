import pygame
from const import *

class Dragger:
    def __init__(self):
        self.mouseXCoord = 0
        self.mouseYCoord = 0
        self.initialRow = 0
        self.initialCol = 0
        self.piece = None
        self.isActive = False

    def updateMousePos(self, position):
        self.mouseXCoord, self.mouseYCoord = position

    def savePos(self, position):
        self.initialCol = position[0] // SquareSize
        self.initialRow = position[1] // SquareSize

    def savePiece(self, piece):
        self.piece = piece
        self.isActive = True

    def clearPiece(self):
        self.piece = None
        self.isActive = False

    def updateImage(self, screen):
        self.piece.setImage()
        img = self.piece.image
        self.piece.imageRect = img.get_rect(center = (self.mouseXCoord, self.mouseYCoord))
        screen.blit(img, self.piece.imageRect)
