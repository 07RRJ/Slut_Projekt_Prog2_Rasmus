from scenes.base_scene import BaseScene
from scenes.shop_scene import ShopScene

from ui.button import Button

class MenuScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)

        self.play_button = Button(
            (500, 300, 300, 100),
            "PLAY",
            self.start_game
        )

    def start_game(self):
        self.game.scene_manager.switch_scene(
            ShopScene(self.game)
        )

    def handle_events(self, events):
        for event in events:
            self.play_button.handle_event(event)

    def draw(self, screen):
        self.play_button.draw(screen)