import os
import pygame

from sound import Sound

class Config:
    def __init__(self):
        self.moveSound = Sound(os.path.join("..", "sounds/" + "move.mp3"))
        self.captureSound = Sound(os.path.join("..", "sounds/" + "capture.mp3"))
        self.drawSound = Sound(os.path.join("..", "sounds/" + "draw.mp3"))
        self.checkmateSound = Sound(os.path.join("..", "sounds/" + "checkmate.mp3"))