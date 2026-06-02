import sys
import pygame
from pathlib import Path
from core.constants import *

_BASE = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(__file__).resolve().parent.parent

MENU_PATH = str(_BASE / "assets/menu") + "/"
CARD_PATH = str(_BASE / "assets/cards") + "/"
FONT_PATH = str(_BASE / "assets/fonts") + "/"

pygame.init()

import pygame

class AssetManager:
    def __init__(self):
        self.images = {}
        self.fonts = {}

    def load_image(self, key, path):
        full = _BASE / path
        self.images[key] = pygame.image.load(str(full)).convert_alpha()

    def load_font(self, key, path, size):
        full = _BASE / path
        self.fonts[key] = pygame.font.Font(str(full), size)

    def get_image(self, key):
        return self.images[key]

    def get_font(self, key):
        return self.fonts[key]