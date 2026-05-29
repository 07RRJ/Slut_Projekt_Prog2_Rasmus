import pygame, time
from scenes.base_scene               import BaseScene
from logic.controllers.game_controller import GameController
from core.constants                  import *

class WaitingReadyScene(BaseScene):
    POLL_EVERY = 2

    def __init__(self, game):
        super().__init__(game)
        self.ctrl      = GameController(game)
        self.font      = game.assets.get_font("body")
        self.title     = game.assets.get_font("title")
        self.last_poll = 0
        self.dots      = 0

    def update(self):
        now = time.time()
        if now - self.last_poll > self.POLL_EVERY:
            self.last_poll = now
            if self.ctrl.poll_both_ready():
                from scenes.battle_scene import BattleScene
                self.game.scene_manager.switch_scene(BattleScene(self.game))
            self.dots = (self.dots + 1) % 4

    def handle_events(self, events):
        pass

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)
        msg = self.title.render("Waiting for opponent" + "." * self.dots, True, BLACK)
        screen.blit(msg, msg.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2)))
