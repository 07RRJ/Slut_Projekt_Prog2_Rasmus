import pygame
from scenes.base_scene import BaseScene
from core.constants import *

class LoadingScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)
        self.done = False
        self.font = pygame.font.SysFont("arial", 36)
        self.load_assets()

    def load_assets(self): # wish i had the time to make actual cards....
        assets = self.game.assets
        assets.load_image("icon", "assets/icon/icon.png")
        assets.load_image("background", "assets/menu/mainMenu.png")
        assets.load_image("card1", "assets/cards/card_1.png")
        assets.load_font("title", "assets/fonts/COPRGTB.TTF", 64)
        assets.load_font("body", "assets/fonts/CORBEL.TTF", 28)
        assets.load_font("bold", "assets/fonts/CORBELB.TTF", 28)
        self.done = True

    def update(self):
        if self.done:
            self.game.set_icon()
            from scenes.menu_scene import MenuScene
            self.game.scene_manager.switch_scene(MenuScene(self.game))

    def draw(self, screen):
        screen.fill((20, 20, 20))
        text = self.font.render("Loading…", True, WHITE)
        screen.blit(text, text.get_rect(center=(MIDDLE_WIDTH, MIDDLE_HEIGHT)))