import pygame
from core.constants import *
from core.game_state import GameState
from core.scene_manager import SceneManager
from core.asset_manager import AssetManager
from data_base.supabase_client import Database
from auth.session import load_session
from scenes.loading_scene import LoadingScene

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT))
        pygame.display.set_caption("Cards Of Rebellion")

        self.clock = pygame.time.Clock()
        self.running = True

        self.assets = AssetManager()
        self.db = Database()
        self.state = GameState()
        self.session = load_session()   # None if not logged in

        if self.session:
            self.state.user_id = self.session["user_id"]
            self.state.username = self.session["username"]
            player = self.db.GetPlayer(self.session["user_id"])
            if player:
                self.state.load_from_db(player, self.session)

        self.scene_manager = SceneManager()
        self.scene_manager.switch_scene(LoadingScene(self))

    def set_icon(self):
        pygame.display.set_icon(self.assets.get_image("icon"))

    def Run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.scene_manager.handle_events(events)
            self.scene_manager.update()
            self.screen.fill(BACKGROUND_COLOR)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()