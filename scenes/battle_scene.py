import pygame
import time
from scenes.base_scene import BaseScene
from logic.controllers.game_controller import GameController
from logic.battle_engine import BattleEngine
from ui.team_slot import TeamSlot
from ui.stat_box import StatBox
from core.constants import *

class BattleScene(BaseScene):
    LOG_LINE_DELAY = 0.4   # seconds between log lines

    def __init__(self, game):
        super().__init__(game)
        self.ctrl = GameController(game)
        self.font = game.assets.get_font("body")
        self.title = game.assets.get_font("title")
        self.stat_box = StatBox(game.state)

        self.ctrl.load_enemy_team()
        self.result    = self.ctrl.run_battle()

        self.log_lines    = self.result["log"]
        self.shown_lines  = 0
        self.last_advance = time.time()

        self.my_slots  = [TeamSlot(50  + i * 150, 560, i) for i in range(5)]
        self.opp_slots = [TeamSlot(900 - i * 150, 100, i) for i in range(5)]

        self.done     = False
        self.continue_btn = None

    def update(self):
        now = time.time()
        if self.shown_lines < len(self.log_lines):
            if now - self.last_advance >= self.LOG_LINE_DELAY:
                self.shown_lines += 1
                self.last_advance = now
        else:
            if not self.done:
                self.done = True
                self.continue_btn = None   # will be drawn in draw()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.done:
                # Click anywhere to continue
                from scenes.shop_scene import ShopScene
                from scenes.menu_scene import MenuScene
                player = self.game.db.GetPlayer(self.game.state.user_id)
                if player:
                    self.game.scene_manager.switch_scene(ShopScene(self.game))
                else:
                    # Run ended (health reached 0)
                    self.game.scene_manager.switch_scene(MenuScene(self.game))

    def draw(self, screen):
        screen.fill(BACKGROUND_COLOR)

        # Teams
        for slot in self.opp_slots:
            slot.draw(screen, self.game.state.enemy_team[slot.index])
        for slot in self.my_slots:
            slot.draw(screen, self.game.state.team[slot.index])

        # VS
        vs = self.title.render("VS", True, GOLD)
        screen.blit(vs, vs.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT // 2 - 30)))

        # Battle log — scrolling lines in centre
        log_x = BASE_WIDTH // 2
        log_y = BASE_HEIGHT // 2 + 40
        for i, line in enumerate(self.log_lines[:self.shown_lines]):
            surf = self.font.render(line, True, DARK_GRAY)
            screen.blit(surf, surf.get_rect(center=(log_x, log_y + i * 34)))

        # Result banner
        if self.done:
            w = self.result["winner"]
            if w == "a":
                banner_text, color = "YOU WIN!", GOLD
            elif w == "b":
                banner_text, color = "YOU LOSE", RED
            else:
                banner_text, color = "DRAW", GRAY

            banner = self.title.render(banner_text, True, color)
            screen.blit(banner, banner.get_rect(center=(BASE_WIDTH // 2, 50)))

            hint = self.font.render("Click anywhere to continue", True, GRAY)
            screen.blit(hint, hint.get_rect(center=(BASE_WIDTH // 2, BASE_HEIGHT - 50)))

        self.stat_box.draw(screen)
