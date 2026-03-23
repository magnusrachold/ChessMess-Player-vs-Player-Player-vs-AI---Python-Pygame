import os
import pygame

from sound import Sound

class Config:
    def __init__(self):
        self.moveSound = Sound(os.path.join("..", "sounds/" + "assets_sounds_move.wav"))
        self.captureSound = Sound(os.path.join("..", "sounds/" + "assets_sounds_capture.wav"))