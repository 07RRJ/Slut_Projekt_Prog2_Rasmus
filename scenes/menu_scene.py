import pygame
from scenes.base_scene  import BaseScene
from ui.button          import Button
from core.constants     import *

class MenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)

        cx = BASE_WIDTH  // 2
        cy = BASE_HEIGHT // 2

        if game.session:
            # Logged in — show main menu
            self.mode = "main"
            self.buttons = [
                Button((cx - 150, cy - 80,  300, 70), "PLAY",     self._play),
                Button((cx - 150, cy + 10,  300, 70), "LOG OUT",  self._logout),
                Button((cx - 150, cy + 100, 300, 70), "QUIT",     self._quit),
            ]
        else:
            # Not logged in — show login/register
            self.mode = "auth"
            self.buttons = [
                Button((cx - 150, cy - 80,  300, 70), "LOGIN",    self._goto_login),
                Button((cx - 150, cy + 10,  300, 70), "REGISTER", self._goto_register),
                Button((cx - 150, cy + 100, 300, 70), "QUIT",     self._quit),
            ]

        self.title_font = game.assets.get_font("title")
        self.body_font  = game.assets.get_font("body")

    # ── Button callbacks ─────────────────────────────────────

    def _play(self):
        from logic.controllers.game_controller import GameController
        ctrl = GameController(self.game)
        ctrl.start_run()
        from scenes.shop_scene import ShopScene
        self.game.scene_manager.switch_scene(ShopScene(self.game))

    def _logout(self):
        from auth.session import clear_session
        clear_session()
        self.game.session = None
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def _quit(self):
        self.game.running = False

    def _goto_login(self):
        from scenes.login_scene import LoginScene
        self.game.scene_manager.switch_scene(LoginScene(self.game))

    def _goto_register(self):
        from scenes.login_scene import RegisterScene
        self.game.scene_manager.switch_scene(RegisterScene(self.game))

    # ── Scene interface ──────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def draw(self, screen):
        bg = self.game.assets.get_image("background")
        screen.blit(pygame.transform.scale(bg, (BASE_WIDTH, BASE_HEIGHT)), (0, 0))

        if self.game.session:
            name = self.body_font.render(
                f"Welcome, {self.game.session['username']}", True, RED
            )
            screen.blit(name, name.get_rect(center=(BASE_WIDTH // 2, 280)))

        for btn in self.buttons:
            btn.draw(screen)
