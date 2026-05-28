from scenes.base_scene import BaseScene
from scenes.menu_scene import MenuScene

class LoadingScene(BaseScene):
    def __init__(self, game):
        super().__init__(game)

        self.finished_loading = False

        self.load_assets()

    def load_assets(self):
        assets = self.game.assets

        assets.load_image(
            "icon",
            "assets/icon/icon.png"
        )

        assets.load_image(
            "background",
            "assets/menu/mainMenu.png"
        )

        assets.load_image(
            "card1",
            "assets/cards/card_1.png"
        )

        self.finished_loading = True

    def update(self):
        if self.finished_loading:
            self.game.set_icon()
            self.game.scene_manager.switch_scene(
                MenuScene(self.game)
            )