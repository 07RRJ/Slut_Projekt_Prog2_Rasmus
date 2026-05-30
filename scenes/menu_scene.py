import pygame
from scenes.base_scene import BaseScene
from ui.button import Button
from core.constants import *

class MenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)

        button_rect = [
            (MIDDLE_WIDTH - 150, BASE_HEIGHT - 102, 300, 70),
            (MIDDLE_WIDTH + 200, BASE_HEIGHT - 102, 300, 70),
            (MIDDLE_WIDTH + 550, BASE_HEIGHT - 102, 300, 70)
        ]

        if game.session:
            self.mode = "main"
            self.buttons = [
                Button(button_rect[0], "PLAY", self.play),
                Button(button_rect[1], "LOG OUT", self.log_out),
                Button(button_rect[2], "QUIT", self.quit),
            ]
        else:
            self.mode = "auth"
            self.buttons = [
                Button(button_rect[0], "LOGIN", self.go_to_login),
                Button(button_rect[1], "REGISTER", self.go_to_register),
                Button(button_rect[2], "QUIT", self.quit),
            ]

        self.title_font = game.assets.get_font("title")
        self.body_font = game.assets.get_font("body")

    def play(self):
        from logic.controllers.game_controller import GameController
        ctrl = GameController(self.game)
        ctrl.start_run()
        from scenes.shop_scene import ShopScene
        self.game.scene_manager.switch_scene(ShopScene(self.game))

    def log_out(self):
        from auth.session import clear_session
        clear_session()
        self.game.session = None
        self.game.scene_manager.switch_scene(MenuScene(self.game))

    def quit(self):
        self.game.running = False

    def go_to_login(self):
        from scenes.login_scene import LoginScene
        self.game.scene_manager.switch_scene(LoginScene(self.game))

    def go_to_register(self):
        from scenes.login_scene import RegisterScene
        self.game.scene_manager.switch_scene(RegisterScene(self.game))

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                btn.handle_event(event)

    def draw(self, screen):
        bg = self.game.assets.get_image("background")
        screen.blit(pygame.transform.scale(bg, (BASE_WIDTH, BASE_HEIGHT)), (0, 0))

        if self.game.session:
            name = self.body_font.render(f"{self.game.session['username']}", True, RED)
            screen.blit(name, (32, 32))

        for btn in self.buttons:
            btn.draw(screen)
